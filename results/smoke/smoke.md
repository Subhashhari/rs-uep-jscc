# cifar10/val erasure sweep

- commit `6954220a0f9da6f973557c1f544028ef6fdfd3e8` (dirty: True), 2026-10-17T14:01:01+00:00
- checkpoint `results/train_split_adjsccq/best_val.pth` sha256 `b07b868ade0abd3cbf5fda59b250ccdebf439b8681bc622055a2fd1f1f1a3fc3`
- images_per_seed: 200
- is_full_test_set: False
- channels: 16
- packet_size: 16
- overhead: 0.5
- clean_psnr_mean: 30.977144241333008
- side_info_rule: 0 B for uniform/no_rs, one byte per channel for sorted methods
- channel_seeds: [0, 1]
- mask_protocol: one master mask per (batch, seed, rate) shared by all methods; smaller schemes use its first columns
- PSNR: mean ± sample std over channel seeds (95% t-interval half-width in brackets)

| Method | erasure_rate | PSNR (dB) | median | p5 | SSIM | block-fail | Coding OH | Side-info B | Total OH |
|---|---|---|---|---|---|---|---|---|---|
| no_rs | 0 | 30.98 ± 0.00 (CI ±0.00) | 30.96 | 27.23 | 0.9650 | 0.000 | 0.00% | 0 | 0.00% |
| three_tier_25_50_25@attention | 0 | 30.98 ± 0.00 (CI ±0.00) | 30.96 | 27.23 | 0.9650 | 0.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@oracle | 0 | 30.98 ± 0.00 (CI ±0.00) | 30.96 | 27.23 | 0.9650 | 0.000 | 50.00% | 16 | 51.56% |
| uniform | 0 | 30.98 ± 0.00 (CI ±0.00) | 30.96 | 27.23 | 0.9650 | 0.000 | 50.00% | 0 | 50.00% |
| no_rs | 0.4 | 19.92 ± 0.01 (CI ±0.05) | 19.84 | 16.91 | 0.7788 | 1.000 | 0.00% | 0 | 0.00% |
| three_tier_25_50_25@attention | 0.4 | 22.41 ± 0.20 (CI ±1.79) | 21.86 | 17.70 | 0.8512 | 1.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@oracle | 0.4 | 23.21 ± 0.41 (CI ±3.71) | 22.66 | 18.25 | 0.8644 | 1.000 | 50.00% | 16 | 51.56% |
| uniform | 0.4 | 20.94 ± 0.24 (CI ±2.18) | 20.02 | 16.91 | 0.7947 | 0.895 | 50.00% | 0 | 50.00% |
| no_rs | 0.5 | 18.50 ± 0.13 (CI ±1.12) | 18.39 | 15.85 | 0.7279 | 1.000 | 0.00% | 0 | 0.00% |
| three_tier_25_50_25@attention | 0.5 | 19.47 ± 0.15 (CI ±1.35) | 19.31 | 16.14 | 0.7677 | 1.000 | 50.00% | 16 | 51.56% |
| three_tier_25_50_25@oracle | 0.5 | 19.87 ± 0.26 (CI ±2.30) | 19.86 | 15.98 | 0.7759 | 1.000 | 50.00% | 16 | 51.56% |
| uniform | 0.5 | 18.50 ± 0.13 (CI ±1.12) | 18.39 | 15.85 | 0.7279 | 1.000 | 50.00% | 0 | 50.00% |

# Paired difference to `uniform` (same loss mask per seed)

| Method | erasure_rate | mean gain (dB) | std over seeds | 95% CI ± | wins | significant |
|---|---|---|---|---|---|---|
| no_rs | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@attention | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@oracle | 0 | +0.00 | 0.00 | 0.00 | 0% | no |
| no_rs | 0.4 | -1.03 | 0.25 | 2.23 | 0% | no |
| three_tier_25_50_25@attention | 0.4 | +1.47 | 0.04 | 0.39 | 100% | yes |
| three_tier_25_50_25@oracle | 0.4 | +2.27 | 0.17 | 1.53 | 100% | yes |
| no_rs | 0.5 | +0.00 | 0.00 | 0.00 | 0% | no |
| three_tier_25_50_25@attention | 0.5 | +0.97 | 0.28 | 2.48 | 100% | no |
| three_tier_25_50_25@oracle | 0.5 | +1.36 | 0.38 | 3.43 | 100% | no |

# Insights

- Based on 2 channel seed(s); 200 images per seed. All gains below are paired per seed against the baseline (same packet losses), so they carry no luck-of-the-draw advantage.
- Break-even: the best protected method overtakes `uniform` from about erasure_rate = 0.00.
- Peak gain: +2.27 dB at erasure_rate = 0.4 by three_tier_25_50_25@oracle (95% CI ±1.53, significant).
- Importance sources ranked by their best scheme's mean gain over erasure_rate >= 0.35: oracle +1.82 dB, attention +1.22 dB.
- Share of the oracle gain captured: attention 67%.
- Worst-case images at erasure_rate = 0.4: 5th-percentile PSNR 18.25 dB (three_tier_25_50_25@oracle) vs 16.91 dB (uniform).
- Worst-case images at erasure_rate = 0.5: 5th-percentile PSNR 15.98 dB (three_tier_25_50_25@oracle) vs 15.85 dB (uniform).
- Seed sensitivity: largest std across channel seeds is 0.41 dB (three_tier_25_50_25@oracle, erasure_rate = 0.4); gains smaller than that are not reliable.
- `uniform` shows its steepest fall (-10.04 dB) between erasure_rate = 0 and 0.4 -- its cliff.
