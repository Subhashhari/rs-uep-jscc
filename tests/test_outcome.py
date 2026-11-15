"""The fast outcome simulator (coding/outcome.py) must agree exactly with real RS decoding."""
import numpy as np
import pytest
import torch

from coding.erasure_channel import apply_erasure_mask
from coding.outcome import (
    block_failure_probability,
    grouped_layout,
    layout_from_scheme,
    lost_latent_symbols,
    lost_stream_symbols,
    pet_layout,
    pet_twin,
    stream_loss_probability,
    symbol_loss_probability,
)
from coding.reed_solomon import decode_block, encode_block
from coding.rs_pipeline import SCHEME_CANDIDATES, decode_blocks, encode_blocks


@pytest.mark.parametrize("name", sorted(SCHEME_CANDIDATES))
@pytest.mark.parametrize("rate", [0.1, 0.35, 0.5])
def test_grouped_matches_rs_pipeline(name, rate):
    scheme = SCHEME_CANDIDATES[name]
    generator = torch.Generator().manual_seed(7)
    batch = 12
    idx = torch.randint(0, 256, (batch, scheme.data_symbols), generator=generator)
    order = torch.stack([torch.randperm(16, generator=generator) for _ in range(batch)])
    mask = torch.rand(batch, scheme.total_packets, generator=generator) < rate
    received = apply_erasure_mask(encode_blocks(idx, scheme, order), mask).received
    decoded = decode_blocks(received, scheme, order)
    simulated = lost_latent_symbols(layout_from_scheme(scheme), mask, order, 64)
    assert torch.equal(simulated, decoded.failed.cpu())
    # recovered symbols are exactly right, which is what makes "lost" the only thing that matters
    assert torch.equal(decoded.indices[~decoded.failed], idx[~decoded.failed])


def test_unsorted_matches_rs_pipeline():
    scheme = SCHEME_CANDIDATES["uniform"]
    generator = torch.Generator().manual_seed(3)
    idx = torch.randint(0, 256, (8, 1024), generator=generator)
    mask = torch.rand(8, 96, generator=generator) < 0.4
    decoded = decode_blocks(apply_erasure_mask(encode_blocks(idx, scheme, None), mask).received, scheme, None)
    assert torch.equal(lost_latent_symbols(layout_from_scheme(scheme), mask, None, 64), decoded.failed.cpu())


def _pet_decode_reference(layout, stream, mask_row):
    """Real RS: encode every column as its own systematic RS(N, K_j) codeword, erase, decode."""
    packets, size = layout.total_packets, layout.packet_size
    lost = np.zeros(len(stream), dtype=bool)
    for j, k in enumerate(layout.word_k):
        positions = [t for t, w in enumerate(layout.sym_word) if w == j and layout.sym_packet[t] >= 0]
        if not positions:
            continue
        rows = [layout.sym_packet[t] for t in positions]
        data = np.zeros((k, 1), dtype=np.uint8)
        for t, r in zip(positions, rows):
            data[r, 0] = stream[t]
        codeword = encode_block(data, packets)
        erased = np.flatnonzero(mask_row)
        recovered, success = decode_block(codeword.copy(), erased, packets, k)
        for t, r in zip(positions, rows):
            if success:
                assert recovered[r, 0] == stream[t]
            else:
                lost[t] = bool(mask_row[r])
                if not mask_row[r]:
                    assert recovered[r, 0] == stream[t]
    lost[[t for t, p in enumerate(layout.sym_packet) if p < 0]] = True
    return lost


@pytest.mark.parametrize("placement", ["column", "diagonal"])
def test_pet_matches_real_rs(placement):
    rng = np.random.default_rng(0)
    column_k = [40, 40, 48, 56, 56, 60, 64, 64, 64, 64, 68, 72, 76, 80, 80, 92]
    dropped = 1024 - sum(column_k)
    layout = pet_layout(column_k, 96, 16, dropped=max(dropped, 0), placement=placement)
    stream = rng.integers(0, 256, layout.data_symbols, dtype=np.uint8)
    for rate in (0.2, 0.3, 0.4, 0.5):
        mask = rng.random((4, 96)) < rate
        simulated = lost_stream_symbols(layout, torch.from_numpy(mask)).numpy()
        for b in range(4):
            assert np.array_equal(simulated[b], _pet_decode_reference(layout, stream, mask[b]))


def test_dropped_tier_is_always_lost_and_layout_counts():
    layout = grouped_layout([(40, 16), (56, 32), (0, 16)])
    assert layout.total_packets == 96 and layout.data_symbols == 1024 and layout.dropped_symbols == 256
    lost = lost_stream_symbols(layout, torch.zeros(3, 96, dtype=torch.bool))
    assert lost[:, -256:].all() and not lost[:, :-256].any()


def test_pet_twin_sizes():
    for name, scheme in SCHEME_CANDIDATES.items():
        twin = pet_twin(scheme.tiers)
        assert sum(twin.word_k) == scheme.data_symbols, name
        assert list(twin.word_k) == sorted(twin.word_k)
    assert pet_twin(SCHEME_CANDIDATES["uniform"].tiers).word_k == tuple([64] * 16)


def test_closed_form_matches_monte_carlo():
    layout = grouped_layout([(32, 16), (48, 32), (16, 16)])
    rate = 0.4
    mask = torch.rand(40000, 96, generator=torch.Generator().manual_seed(1)) < rate
    empirical = lost_stream_symbols(layout, mask).float().mean(0).numpy()
    expected = stream_loss_probability(layout, rate)
    assert np.allclose(empirical, expected, atol=0.01)
    assert abs(block_failure_probability(96, 64, 0.4) - 0.891) < 2e-3      # table in the literature review
    assert abs(block_failure_probability(48, 32, 0.2) - 0.0093) < 3e-4
    assert symbol_loss_probability(16, 16, 0.3) == pytest.approx(0.3)
