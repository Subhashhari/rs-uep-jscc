# cifar10/val erasure sweep

- commit `79b295eeee917b210fe71782134c259f1b8b23d9` (dirty: False), 2026-11-06T10:24:47+00:00
- checkpoint `results/g1/smoke_train/best_val.pth` sha256 `b015079d564ecf7fc824bf9393d3ed7d9c3c4bcae1be36d86a50b639e12b7d1b`
- images_per_seed: 200
- is_full_test_set: False
- quality_metric: per-image PSNR (dB)
- channels: 16
- packet_size: 16
- overhead: 0.5
- clean_psnr_mean: 22.052576065063477
- side_info_rule: 0 B for uniform/no_rs, one byte per channel for sorted methods
- channel_seeds: [0, 1]
- mask_protocol: one master mask per (batch, seed, rate) shared by all methods; smaller schemes use its first columns
- PSNR: mean ± sample std over channel seeds (95% t-interval half-width in brackets)

| Method | erasure_rate | PSNR (dB) | median | p5 | SSIM | block-fail | Coding OH | Side-info B | Total OH |
|---|---|---|---|---|---|---|---|---|---|
| no_rs | 0 | 22.05 ± 0.00 (CI ±0.00) | 22.13 | 19.28 | 0.7869 | 0.000 | 0.00% | 0 | 0.00% |
| three_tier_25_50_25@energy | 0 | 22.05 ± 0.00 (CI ±0.00) | 22.13 | 19.28 | 0.7869 | 0.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@oracle | 0 | 22.05 ± 0.00 (CI ±0.00) | 22.13 | 19.28 | 0.7869 | 0.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@random | 0 | 22.05 ± 0.00 (CI ±0.00) | 22.13 | 19.28 | 0.7869 | 0.000 | 50.00% | 16 | 51.56% |
| uniform | 0 | 22.05 ± 0.00 (CI ±0.00) | 22.13 | 19.28 | 0.7869 | 0.000 | 50.00% | 0 | 50.00% |
| no_rs | 0.4 | 17.97 ± 0.09 (CI ±0.78) | 17.82 | 15.35 | 0.6592 | 1.000 | 0.00% | 0 | 0.00% |
| three_tier_25_50_25@energy | 0.4 | 19.07 ± 0.03 (CI ±0.24) | 18.75 | 15.77 | 0.6934 | 1.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@oracle | 0.4 | 19.92 ± 0.06 (CI ±0.58) | 19.77 | 17.08 | 0.7296 | 1.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@random | 0.4 | 19.19 ± 0.03 (CI ±0.28) | 19.17 | 16.14 | 0.7057 | 1.000 | 50.00% | 16 | 51.56% |
| uniform | 0.4 | 18.35 ± 0.04 (CI ±0.34) | 17.99 | 15.37 | 0.6703 | 0.895 | 50.00% | 0 | 50.00% |

# Paired difference to `uniform` (same loss mask per seed)

| Method | erasure_rate | mean gain (dB) | std over seeds | 95% CI ± | wins | significant |
|---|---|---|---|---|---|---|
| no_rs | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@energy | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@oracle | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@random | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| no_rs | 0.4 | -0.38 | 0.05 | 0.44 | 0% | no |
| three_tier_25_50_25@energy | 0.4 | +0.72 | 0.06 | 0.57 | 100% | yes |
| three_tier_25_50_25@oracle | 0.4 | +1.57 | 0.10 | 0.92 | 100% | yes |
| three_tier_25_50_25@random | 0.4 | +0.85 | 0.07 | 0.61 | 100% | yes |

# Insights

- Based on 2 channel seed(s); 200 images per seed. All gains below are paired per seed against the baseline (same packet losses), so they carry no luck-of-the-draw advantage.
- No low-loss penalty: the best method is never more than 0.05 dB below `uniform` at any erasure_rate in this sweep.
- Peak gain: +1.57 dB at erasure_rate = 0.4 by three_tier_25_50_25@oracle (95% CI ±0.92, significant).
- Importance sources ranked by their best scheme's mean gain over erasure_rate >= 0.35: oracle +1.57 dB, random +0.85 dB, energy +0.72 dB.
- Share of the reference ranking's gain captured: random 54%, energy 46%. A share above 100% means that source allocated protection better than the reference.
- Random-order control gains +0.85 dB versus oracle +1.57 dB, so the benefit comes from *which* channels are protected, not merely from tiering.
- Worst-case images at erasure_rate = 0.4: 5th-percentile PSNR 17.08 dB (three_tier_25_50_25@oracle) vs 15.37 dB (uniform).
- Seed sensitivity: std across channel seeds stays below 0.3 dB everywhere.
