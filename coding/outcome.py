"""Exact erasure outcome of systematic MDS (Reed-Solomon) packet layouts, without GF(256) arithmetic.

Why this is exact
-----------------
Every code in this project is a systematic Reed-Solomon code used for erasure decoding only. RS codes
are MDS, so a codeword with ``n`` symbols and ``k`` data symbols is recovered *if and only if* at most
``n - k`` of its symbols are erased; when it is not recovered, the data symbols that arrived are kept
(systematic) and the erased ones are lost. Which latent bytes reach the decoder is therefore a
deterministic function of the packet-loss mask and the layout. ``coding/rs_pipeline.py`` computes the
same thing by actually decoding; ``tests/test_outcome.py`` checks the two agree symbol for symbol on
every scheme in ``SCHEME_CANDIDATES``. Decoding cost then drops from pure-numpy RS to one matrix product,
which is what makes the allocation searches in ``experiments/coding_controls.py`` affordable.

Layouts
-------
A :class:`Layout` describes, for every position ``t`` of the importance-sorted data stream (most
important first), the packet that carries it and the codeword it belongs to, plus ``(n, k)`` and the
packet set of every codeword. Two families are built here:

* :func:`grouped_layout` -- the project's tiered layout (``rs_pipeline.encode_blocks``): tier ``i`` owns
  ``n_i`` consecutive packets; its data fill ``k_i`` packets row by row; every column is one
  RS(n_i, k_i) codeword. A tier with ``n_i == 0`` is *dropped* (its data are never sent; the
  Grad-FEC "drop and protect" idea). Tier failures are independent events.
* :func:`pet_layout` -- Priority Encoding Transmission (Albanese et al., 1996): every byte column ``j``
  of all ``N`` packets is one RS(N, K_j) codeword, so every tier spans every packet and whether column
  ``j`` is recovered depends only on the *total* number of lost packets ``L`` (recovered iff
  ``L <= N - K_j``). Data are filled column by column, strongest column first. ``placement="diagonal"``
  cyclically shifts each column's rows so that one lost packet does not hit the same spatial position
  of every channel.
"""
from dataclasses import dataclass, field
from functools import lru_cache
from math import comb
from typing import Optional, Sequence, Tuple

import numpy as np
import torch

from coding.importance import permutation_from_channel_order
from coding.rs_pipeline import CodingScheme


@dataclass(frozen=True)
class Layout:
    """Where every sorted data symbol travels, and the codewords protecting it."""

    name: str
    total_packets: int                 # packets on the air (<= the master mask width)
    packet_size: int
    sym_packet: Tuple[int, ...]        # packet index of stream symbol t; -1 = never sent (dropped)
    sym_word: Tuple[int, ...]          # codeword index of stream symbol t (ignored when dropped)
    word_n: Tuple[int, ...]            # codeword length in packets
    word_k: Tuple[int, ...]            # data packets of the codeword
    word_packets: Tuple[Tuple[int, ...], ...]  # packets carrying a symbol of the codeword
    family: str = "grouped"
    params: Tuple = field(default=())

    @property
    def data_symbols(self) -> int:
        return len(self.sym_packet)

    @property
    def dropped_symbols(self) -> int:
        return sum(1 for p in self.sym_packet if p < 0)

    @property
    def transmitted_symbols(self) -> int:
        return self.total_packets * self.packet_size


@dataclass
class _Tensors:
    sym_packet: torch.Tensor   # (L,) long, dropped symbols point at a sentinel column that is always erased
    sym_word: torch.Tensor     # (L,) long
    incidence: torch.Tensor    # (P + 1, W) float, 1 where packet p carries a symbol of codeword w
    capacity: torch.Tensor     # (W,) float, n - k


@lru_cache(maxsize=256)
def _tensors(layout: Layout) -> _Tensors:
    packets = layout.total_packets
    sentinel = packets
    sym_packet = torch.tensor([p if p >= 0 else sentinel for p in layout.sym_packet], dtype=torch.long)
    words = len(layout.word_n)
    # Codeword ``words`` is a sentinel for dropped symbols: capacity -1, so it always "fails".
    incidence = torch.zeros(packets + 1, words + 1)
    for w, members in enumerate(layout.word_packets):
        if members:
            incidence[list(members), w] = 1.0
    capacity = torch.tensor([n - k for n, k in zip(layout.word_n, layout.word_k)] + [-1], dtype=torch.float32)
    sym_word = torch.tensor([w if p >= 0 else words for p, w in zip(layout.sym_packet, layout.sym_word)],
                            dtype=torch.long)
    return _Tensors(sym_packet, sym_word, incidence, capacity)


def lost_stream_symbols(layout: Layout, packet_mask: torch.Tensor) -> torch.Tensor:
    """``(B, L)`` bool: ``True`` where sorted stream symbol ``t`` is not available after decoding.

    ``packet_mask`` is ``(B, >= total_packets)``, ``True`` = packet erased; only the first
    ``total_packets`` columns are used (the master-mask prefix convention of the main evaluator).
    """
    tensors = _tensors(layout)
    mask = packet_mask[:, : layout.total_packets].to(torch.bool).cpu()
    batch = mask.shape[0]
    # Sentinel column (dropped data) is always erased.
    extended = torch.cat([mask, torch.ones(batch, 1, dtype=torch.bool)], dim=1)
    erasures = extended.float() @ tensors.incidence           # (B, W) erased symbols per codeword
    failed_word = erasures > tensors.capacity                  # MDS: recovered iff erasures <= n - k
    symbol_erased = extended[:, tensors.sym_packet]           # (B, L)
    return symbol_erased & failed_word[:, tensors.sym_word]


def lost_latent_symbols(layout: Layout, packet_mask: torch.Tensor, channel_order: Optional[torch.Tensor],
                        symbols_per_channel: int) -> torch.Tensor:
    """Same as :func:`lost_stream_symbols` but in the original (unsorted, channel-major) latent order."""
    lost = lost_stream_symbols(layout, packet_mask)
    if channel_order is None:
        return lost
    permutation = permutation_from_channel_order(channel_order.cpu(), symbols_per_channel)
    out = torch.zeros_like(lost)
    out.scatter_(1, permutation, lost)
    return out


# ----------------------------------------------------------------------------------------------
# Layout families
# ----------------------------------------------------------------------------------------------
def grouped_layout(tiers: Sequence[Tuple[int, int]], packet_size: int = 16, name: str = "") -> Layout:
    """The tiered layout of ``coding/rs_pipeline.py``; ``(0, k)`` = tier of ``k`` data packets not sent."""
    sym_packet, sym_word, word_n, word_k, word_packets = [], [], [], [], []
    packet = 0
    for n, k in tiers:
        if k <= 0:
            raise ValueError("every tier needs k > 0 data packets")
        if n == 0:                       # dropped tier
            sym_packet.extend([-1] * (k * packet_size))
            sym_word.extend([-1] * (k * packet_size))
            continue
        if n < k or n > 255:
            raise ValueError(f"invalid tier ({n}, {k})")
        word = len(word_n)
        word_n.append(n)
        word_k.append(k)
        word_packets.append(tuple(range(packet, packet + n)))
        for row in range(k):
            sym_packet.extend([packet + row] * packet_size)
            sym_word.extend([word] * packet_size)
        packet += n
    label = name or "grouped[" + ",".join(f"{n}/{k}" for n, k in tiers) + "]"
    return Layout(label, packet, packet_size, tuple(sym_packet), tuple(sym_word), tuple(word_n), tuple(word_k),
                  tuple(word_packets), "grouped", tuple(tuple(t) for t in tiers))


def layout_from_scheme(scheme: CodingScheme, name: str = "") -> Layout:
    return grouped_layout(scheme.tiers, scheme.packet_size, name)


def pet_layout(column_k: Sequence[int], total_packets: int = 96, packet_size: int = 16,
               dropped: int = 0, placement: str = "column", name: str = "") -> Layout:
    """PET: byte column ``j`` of all ``total_packets`` packets is one RS(total_packets, K_j) codeword.

    ``column_k`` lists ``K_j`` for the ``packet_size`` columns, strongest (smallest) first; the data
    stream fills column 0 first. ``dropped`` trailing stream symbols (least important) are not sent;
    ``sum(column_k) + dropped`` is the stream length. ``K_j = 0`` is an all-parity column (allowed, but
    useless). ``placement``: ``column`` puts stream symbol ``s`` of column ``j`` in packet ``s``;
    ``diagonal`` uses packet ``(s + 5 j) mod K_j``, so a lost packet erases different spatial positions
    in different columns.
    """
    if len(column_k) != packet_size:
        raise ValueError(f"need {packet_size} column sizes, got {len(column_k)}")
    if any(k < 0 or k > total_packets for k in column_k):
        raise ValueError("every K_j must lie in [0, total_packets]")
    if total_packets > 255:
        raise ValueError("an RS codeword over GF(256) has at most 255 symbols")
    if placement not in ("column", "diagonal"):
        raise ValueError(f"unknown placement {placement!r}")
    sym_packet, sym_word = [], []
    for j, k in enumerate(column_k):
        for s in range(k):
            row = s if placement == "column" or k == 0 else (s + 5 * j) % k
            sym_packet.append(row)
            sym_word.append(j)
    sym_packet.extend([-1] * dropped)
    sym_word.extend([-1] * dropped)
    word_n = tuple(total_packets for _ in column_k)
    word_packets = tuple(tuple(range(total_packets)) for _ in column_k)
    label = name or f"pet[{','.join(map(str, column_k))}]" + (f"-drop{dropped}" if dropped else "") + (
        "-diag" if placement == "diagonal" else "")
    return Layout(label, total_packets, packet_size, tuple(sym_packet), tuple(sym_word), word_n,
                  tuple(column_k), word_packets, "pet", (tuple(column_k), dropped, placement))


def pet_twin(tiers: Sequence[Tuple[int, int]], total_packets: int = 96, packet_size: int = 16,
             placement: str = "column") -> Layout:
    """PET layout with (as nearly as integers allow) the same per-tier code rate as a grouped scheme.

    Tier ``i`` of rate ``k_i / n_i`` needs ``k_i * packet_size / K_i`` columns of
    ``K_i = round(total_packets * k_i / n_i)`` data symbols each (fractional in general); the column
    counts are rounded with the largest-remainder rule so they sum to ``packet_size``, and the weakest
    columns' ``K`` are then moved by one at a time until the columns hold exactly the data. With the
    16-channel templates the twin differs from the exact rates by at most a few symbols per column.
    """
    from coding.scaling import largest_remainder

    data = sum(k for _, k in tiers) * packet_size
    rates = [total_packets if n == 0 else int(round(total_packets * k / n)) for n, k in tiers]
    shares = [k * packet_size / rate for (_, k), rate in zip(tiers, rates)]
    counts = largest_remainder(packet_size, shares)
    columns = sorted(rate for rate, count in zip(rates, counts) for _ in range(count))
    diff, j = data - sum(columns), 0
    while diff != 0:
        idx = packet_size - 1 - (j % packet_size)        # adjust the weakest columns first
        if diff > 0 and columns[idx] < total_packets:
            columns[idx] += 1
            diff -= 1
        elif diff < 0 and columns[idx] > 1:
            columns[idx] -= 1
            diff += 1
        j += 1
    return pet_layout(sorted(columns), total_packets, packet_size, 0, placement,
                      name="pet_twin[" + ",".join(f"{n}/{k}" for n, k in tiers) + "]")


# ----------------------------------------------------------------------------------------------
# Closed-form probabilities under i.i.d. packet loss
# ----------------------------------------------------------------------------------------------
def binom_tail(n: int, p: float, at_least: int) -> float:
    """P(Bin(n, p) >= at_least)."""
    if at_least <= 0:
        return 1.0
    if at_least > n:
        return 0.0
    return float(sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(at_least, n + 1)))


def block_failure_probability(n: int, k: int, p: float) -> float:
    """P(an RS(n, k) block is not recovered) = P(more than n - k of its n packets are lost)."""
    return binom_tail(n, p, n - k + 1)


def symbol_loss_probability(n: int, k: int, p: float) -> float:
    """P(a given data symbol of a systematic RS(n, k) block is lost) = p * P(>= n-k of the other n-1 lost)."""
    if n == 0:
        return 1.0
    return p * binom_tail(n - 1, p, n - k)


def stream_loss_probability(layout: Layout, p: float) -> np.ndarray:
    """``(L,)`` probability that each sorted stream symbol is lost under i.i.d. loss rate ``p``."""
    per_word = [symbol_loss_probability(n, k, p) for n, k in zip(layout.word_n, layout.word_k)]
    return np.array([1.0 if packet < 0 else per_word[word] for packet, word in zip(layout.sym_packet,
                                                                                    layout.sym_word)])
