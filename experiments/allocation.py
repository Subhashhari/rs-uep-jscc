"""Optimal parity allocation for importance-sorted latents over i.i.d. packet erasures.

The surrogate
-------------
Let ``w_r`` be the mean-squared-error increase when the channel at rank ``r`` is erased (the
leave-one-out profile, ``mse_increase_by_channel`` in a ranking file, sorted most damaging first) and
let every symbol of that channel carry ``w_r / S`` (``S`` symbols per channel). If damage adds up over
erased symbols, the expected MSE increase of a layout is

    E[dMSE] = sum_t  (w_{r(t)} / S) * P(stream symbol t is lost),

and ``P(lost)`` has a closed form for systematic MDS codes (``coding.outcome.symbol_loss_probability``):
a data symbol of an RS(n, k) block is lost iff its own packet is lost *and* at least ``n - k`` of the
other ``n - 1`` packets are lost. Both layout families make the objective separable over consecutive
segments of the sorted stream, so the surrogate optimum is found exactly by dynamic programming:

* grouped tiers: segments are whole channels; a tier of ``c`` channels uses ``4c`` data packets and
  any ``n >= 4c`` packets in total, or ``n = 0`` (not sent). Packets sum to the budget.
* PET: 16 byte columns, each an RS(N, K_j) codeword over all ``N`` packets, filled in order; a
  trailing part of the stream may be left unsent.

The additivity assumption is only a surrogate: allocations are always re-scored by exact simulation
(``coding.outcome`` + the real decoder) and refined by a local search on the validation split
(:func:`hill_climb`). ``experiments/coding_controls.py`` reports how well the surrogate predicts
the simulated PSNR.
"""
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from coding.outcome import Layout, grouped_layout, pet_layout, symbol_loss_probability


@lru_cache(maxsize=None)
def _f(n: int, k: int, p: float) -> float:
    return symbol_loss_probability(n, k, p)


def loss_weighting(rates: Sequence[float], weights: Optional[Sequence[float]] = None):
    """``[(rate, weight), ...]`` normalised to sum 1 (a design point or a loss-rate prior)."""
    rates = list(rates)
    weights = list(weights) if weights is not None else [1.0] * len(rates)
    total = float(sum(weights))
    return tuple((float(r), float(w) / total) for r, w in zip(rates, weights))


def _expected_f(n: int, k: int, prior) -> float:
    return sum(w * _f(n, k, p) for p, w in prior)


# ----------------------------------------------------------------------------------------------
# Grouped tiers
# ----------------------------------------------------------------------------------------------
def optimal_grouped(channel_weights: Sequence[float], prior, total_packets: int = 96,
                    packets_per_channel: int = 4, allow_drop: bool = True, max_tiers: int = 16):
    """Exact surrogate optimum over channel-aligned tiers. Returns ``(tiers, expected_cost)``."""
    weights = np.asarray(channel_weights, dtype=np.float64)
    channels = len(weights)
    prefix = np.concatenate([[0.0], np.cumsum(weights)])
    inf = float("inf")
    # best[i][P] = (cost, back-pointer) for channels [0, i) using P packets
    best = [[(inf, None)] * (total_packets + 1) for _ in range(channels + 1)]
    best[0][0] = (0.0, None)
    for i in range(channels):
        for used in range(total_packets + 1):
            cost_here = best[i][used][0]
            if cost_here == inf:
                continue
            for j in range(i + 1, channels + 1):
                k = packets_per_channel * (j - i)
                segment = prefix[j] - prefix[i]
                options = ([0] if allow_drop else []) + list(range(k, min(255, total_packets - used) + 1))
                for n in options:
                    cost = cost_here + segment * (1.0 if n == 0 else _expected_f(n, k, prior))
                    if cost < best[j][used + n][0]:
                        best[j][used + n] = (cost, (i, used, n, k))
    cost, pointer = best[channels][total_packets]
    tiers, j, used = [], channels, total_packets
    while pointer is not None:
        i, previous_used, n, k = pointer
        tiers.append((n, k))
        j, used = i, previous_used
        pointer = best[j][used][1]
    return tuple(reversed(tiers)), cost


def surrogate_cost(layout: Layout, symbol_weights: np.ndarray, prior) -> float:
    """Expected MSE increase of any layout under the additive surrogate."""
    per_word = [_expected_f(n, k, prior) for n, k in zip(layout.word_n, layout.word_k)]
    loss = np.array([1.0 if p < 0 else per_word[w] for p, w in zip(layout.sym_packet, layout.sym_word)])
    return float(np.dot(loss, symbol_weights))


def symbol_weights_from_channels(channel_weights: Sequence[float], symbols_per_channel: int) -> np.ndarray:
    return np.repeat(np.asarray(channel_weights, dtype=np.float64) / symbols_per_channel, symbols_per_channel)


# ----------------------------------------------------------------------------------------------
# PET (shared packets)
# ----------------------------------------------------------------------------------------------
def optimal_pet(symbol_weights: Sequence[float], prior, total_packets: int = 96, columns: int = 16,
                allow_drop: bool = True):
    """Exact surrogate optimum of ``K_1..K_columns`` (stream filled in order). Returns ``(K, dropped, cost)``."""
    weights = np.asarray(symbol_weights, dtype=np.float64)
    length = len(weights)
    prefix = np.concatenate([[0.0], np.cumsum(weights)])
    f = np.array([_expected_f(total_packets, k, prior) for k in range(total_packets + 1)])
    inf = float("inf")
    cost = np.full((columns + 1, length + 1), inf)
    choice = np.zeros((columns + 1, length + 1), dtype=np.int64)
    cost[0, 0] = 0.0
    ks = np.arange(total_packets + 1)
    for j in range(columns):
        for s in np.flatnonzero(np.isfinite(cost[j])):
            ends = np.minimum(s + ks, length)
            valid = (s + ks) <= length
            candidate = cost[j, s] + (prefix[ends] - prefix[s]) * f
            for k in ks[valid]:
                e = s + k
                if candidate[k] < cost[j + 1, e]:
                    cost[j + 1, e] = candidate[k]
                    choice[j + 1, e] = k
    finals = cost[columns] + (prefix[length] - prefix) if allow_drop else np.where(
        np.arange(length + 1) == length, cost[columns], inf)
    end = int(np.argmin(finals))
    column_k, s = [], end
    for j in range(columns, 0, -1):
        k = int(choice[j, s])
        column_k.append(k)
        s -= k
    column_k.reverse()
    return tuple(column_k), length - end, float(finals[end])


# ----------------------------------------------------------------------------------------------
# Local search with an exact (simulated) objective
# ----------------------------------------------------------------------------------------------
def grouped_neighbours(tiers: Sequence[Tuple[int, int]], total_packets: int = 96, step_channels: int = 4):
    """Move parity packets between tiers, split or merge tiers, shift a tier boundary by one channel."""
    tiers = [tuple(t) for t in tiers]
    out = set()
    m = len(tiers)
    for a in range(m):
        for b in range(m):
            if a == b:
                continue
            for d in (1, 2, 4):
                t = list(tiers)
                na, ka = t[a]
                nb, kb = t[b]
                if na == 0 or nb == 0:
                    continue
                if na - d >= ka and nb + d <= 255:
                    t[a], t[b] = (na - d, ka), (nb + d, kb)
                    out.add(tuple(t))
    for a in range(m - 1):  # move one channel across the boundary a | a+1 (keep each tier's parity)
        (na, ka), (nb, kb) = tiers[a], tiers[a + 1]
        pa, pb = (na - ka if na else None), (nb - kb if nb else None)
        for delta in (step_channels, -step_channels):
            ka2, kb2 = ka + delta, kb - delta
            if ka2 <= 0 or kb2 <= 0:
                continue
            na2 = 0 if na == 0 else ka2 + pa
            nb2 = 0 if nb == 0 else kb2 + pb
            if na2 and na2 < ka2 or nb2 and nb2 < kb2:
                continue
            total_new = sum(n for n, _ in tiers) - na - nb + na2 + nb2
            if total_new != total_packets:  # a dropped tier changes the packet count; fix with the other tier
                spare = total_packets - (total_new - (nb2 if nb2 else na2))
                if nb2:
                    nb2 = spare
                elif na2:
                    na2 = spare
                if (na2 and na2 < ka2) or (nb2 and nb2 < kb2):
                    continue
            t = list(tiers)
            t[a], t[a + 1] = (na2, ka2), (nb2, kb2)
            if sum(n for n, _ in t) == total_packets:
                out.add(tuple(t))
    for a in range(m - 1):  # merge two adjacent sent tiers
        (na, ka), (nb, kb) = tiers[a], tiers[a + 1]
        if na and nb:
            out.add(tuple(tiers[:a] + [(na + nb, ka + kb)] + tiers[a + 2:]))
    for a in range(m):  # split a tier into two equal-rate halves at a channel boundary
        n, k = tiers[a]
        if n and k >= 2 * step_channels:
            k1 = (k // (2 * step_channels)) * step_channels
            n1 = round(n * k1 / k)
            if n1 >= k1 and n - n1 >= k - k1:
                out.add(tuple(tiers[:a] + [(n1, k1), (n - n1, k - k1)] + tiers[a + 1:]))
    out.discard(tuple(tiers))
    return [t for t in out if sum(n for n, _ in t) == total_packets]


def pet_neighbours(column_k: Sequence[int], dropped: int, total_packets: int = 96):
    """Move capacity between columns (keeping order), or between the last column and the unsent tail."""
    base = list(column_k)
    out = set()
    columns = len(base)
    for a in range(columns):
        for b in range(columns):
            if a == b:
                continue
            for d in (1, 4, 16):
                t = list(base)
                if t[a] - d >= 0 and t[b] + d <= total_packets:
                    t[a] -= d
                    t[b] += d
                    out.add((tuple(sorted(t)), dropped))
    for d in (4, 16, 64):  # send less (drop more) or send more
        t = list(base)
        if t[-1] + d <= total_packets and dropped - d >= 0:
            t[-1] += d
            out.add((tuple(sorted(t)), dropped - d))
        t = list(base)
        if t[-1] - d >= 0:
            t[-1] -= d
            out.add((tuple(sorted(t)), dropped + d))
    out.discard((tuple(sorted(base)), dropped))
    return sorted(out)


def hill_climb(start, neighbours: Callable, score: Callable, max_evaluations: int = 200,
               log: Optional[Callable] = None):
    """First-improvement local search maximising ``score(candidate)`` (exact simulated PSNR)."""
    cache: Dict = {}

    def value(candidate):
        if candidate not in cache:
            cache[candidate] = score(candidate)
        return cache[candidate]

    current, current_value = start, value(start)
    improved = True
    while improved and len(cache) < max_evaluations:
        improved = False
        for candidate in neighbours(current):
            if len(cache) >= max_evaluations:
                break
            if value(candidate) > current_value + 1e-6:
                current, current_value = candidate, value(candidate)
                improved = True
                if log:
                    log(current, current_value, len(cache))
                break
    return current, current_value, cache
