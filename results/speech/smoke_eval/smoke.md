# librispeech/val erasure sweep

- commit `79b295eeee917b210fe71782134c259f1b8b23d9` (dirty: False), 2026-11-09T13:19:11+00:00
- checkpoint `results/speech/smoke_train/best_val.pth` sha256 `dc03e3fdbef9699e978bea60949556526eed6a4c52265dfe37630385f3175f5f`
- images_per_seed: 200
- is_full_test_set: False
- quality_metric: per-segment SNR (dB), stored in the psnr_db_* fields
- channels: 16
- packet_size: 16
- overhead: 0.5
- clean_psnr_mean: -0.001009436440654099
- side_info_rule: 0 B for uniform/no_rs, one byte per channel for sorted methods
- channel_seeds: [0, 1]
- mask_protocol: one master mask per (batch, seed, rate) shared by all methods; smaller schemes use its first columns
- PSNR: mean ± sample std over channel seeds (95% t-interval half-width in brackets)

| Method | erasure_rate | SNR (dB) | median | p5 | SI-SDR (dB) | block-fail | Coding OH | Side-info B | Total OH |
|---|---|---|---|---|---|---|---|---|---|
| no_rs | 0 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.56 | 0.000 | 0.00% | 0 | 0.00% |
| three_tier_25_50_25@attention | 0 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.56 | 0.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@energy | 0 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.56 | 0.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@oracle | 0 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.56 | 0.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@random | 0 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.56 | 0.000 | 50.00% | 16 | 51.56% |
| uniform | 0 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.56 | 0.000 | 50.00% | 0 | 50.00% |
| no_rs | 0.4 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.51 | 1.000 | 0.00% | 0 | 0.00% |
| three_tier_25_50_25@attention | 0.4 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.35 | 1.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@energy | 0.4 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.41 | 1.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@oracle | 0.4 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.46 | 1.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@random | 0.4 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.55 | 1.000 | 50.00% | 16 | 51.56% |
| uniform | 0.4 | -0.00 ± 0.00 (CI ±0.00) | -0.00 | -0.01 | -50.44 | 0.895 | 50.00% | 0 | 50.00% |

# Paired difference to `uniform` (same loss mask per seed)

| Method | erasure_rate | mean gain (dB) | std over seeds | 95% CI ± | wins | significant |
|---|---|---|---|---|---|---|
| no_rs | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@attention | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@energy | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@oracle | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@random | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| no_rs | 0.4 | +0.00 | 0.00 | 0.00 | 100% | no |
| three_tier_25_50_25@attention | 0.4 | +0.00 | 0.00 | 0.00 | 100% | no |
| three_tier_25_50_25@energy | 0.4 | +0.00 | 0.00 | 0.00 | 50% | no |
| three_tier_25_50_25@oracle | 0.4 | +0.00 | 0.00 | 0.00 | 100% | no |
| three_tier_25_50_25@random | 0.4 | +0.00 | 0.00 | 0.00 | 100% | no |

# Insights

- Based on 2 channel seed(s); 200 images per seed. All gains below are paired per seed against the baseline (same packet losses), so they carry no luck-of-the-draw advantage.
- No low-loss penalty: the best method is never more than 0.05 dB below `uniform` at any erasure_rate in this sweep.
- Peak gain: +0.00 dB at erasure_rate = 0.4 by three_tier_25_50_25@attention (95% CI ±0.00, not significant).
- Importance sources ranked by their best scheme's mean gain over erasure_rate >= 0.35: attention +0.00 dB, random +0.00 dB, oracle +0.00 dB, energy +0.00 dB.
- Random-order control gains +0.00 dB versus oracle +0.00 dB, so the benefit comes from *which* channels are protected, not merely from tiering.
- Worst-case images at erasure_rate = 0.4: 5th-percentile PSNR -0.01 dB (three_tier_25_50_25@attention) vs -0.01 dB (uniform).
- Seed sensitivity: std across channel seeds stays below 0.3 dB everywhere.
