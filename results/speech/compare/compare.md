# Architecture comparison (G1): is sensitivity-aware UEP specific to ADJSCC-Q?

Decision rate: loss 0.4. Gains are paired differences to uniform RS of the best (validation-selected) tiered scheme per source; families use converged models only.

## Per model

| model | arch | clean test PSNR | best epoch | converged | worst ch. (dB) | top-4 share | oracle gain @0.4 (CI) | random gain @0.4 | energy gain @0.4 | oracle mean ≥0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| adjsccq1d/seed42 | adjsccq1d | 6.73 | 59 | yes | 9.82 | 46% | +2.01 (±0.02) | +0.84 | +2.10 | +1.62 |
| adjsccq1d/seed100 | adjsccq1d | 6.42 | 58 | yes | 9.26 | 45% | +1.76 (±0.04) | +0.77 | +1.66 | +1.40 |
| adjsccq1d/seed7 | adjsccq1d | 6.71 | 57 | yes | 5.15 | 38% | +1.52 (±0.03) | +0.80 | +1.59 | +1.19 |
| deepjsccq1d/seed42 | deepjsccq1d | 6.53 | 53 | yes | 11.70 | 48% | +3.36 (±0.09) | +0.53 | +3.19 | +2.64 |
| deepjsccq1d/seed100 | deepjsccq1d | 6.56 | 37 | **no** | 5.75 | 37% | +1.55 (±0.01) | +0.67 | +1.77 | +1.20 |
| deepjsccq1d/seed7 | deepjsccq1d | 6.46 | 60 | yes | 9.42 | 46% | +2.90 (±0.07) | +0.66 | +2.94 | +2.30 |
| deepjsccq1d/seed13 | deepjsccq1d | 6.52 | 54 | yes | 9.54 | 46% | +2.64 (±0.05) | +0.71 | +2.82 | +2.06 |

## Per family (mean ± sample std over converged models)

| family | models | top-4 share | worst ch. (dB) | clean test PSNR | oracle @0.4 | energy @0.4 | random @0.4 | energy share of oracle | verdict |
|---|---|---|---|---|---|---|---|---|---|
| adjsccq1d | 3 | 43 ± 4% | 8.08 ± 2.55 | 6.62 ± 0.17 | 1.76 ± 0.24 | 1.78 ± 0.27 | 0.81 ± 0.04 | 101 ± 7% | **criteria met** |
| deepjsccq1d | 3 | 46 ± 1% | 10.22 ± 1.29 | 6.50 ± 0.04 | 2.96 ± 0.36 | 2.98 ± 0.19 | 0.63 ± 0.09 | 102 ± 6% | **criteria met** |

## Decision rule (pre-registered, AD-09)

- C1 concentration: family mean top-4 share ≥ 0.40
- C2 UEP gain: every model's oracle gain at loss 0.4 ≥ +1.50 dB, CI above 0
- C3 identity matters: random gain < 0.50 × oracle gain (loss ≥ 0.35)
- FLAT: top-4 share < 0.30 and oracle − random ≤ 0.50 dB

- **adjsccq1d**: criteria met (C1_concentration=True, C2_uep_gain=True, C3_identity_matters=True, FLAT_no_structure=False)
- **deepjsccq1d**: criteria met (C1_concentration=True, C2_uep_gain=True, C3_identity_matters=True, FLAT_no_structure=False)

## Differences between family means

| comparison | quantity | value | reference | difference |
|---|---|---|---|---|
| deepjsccq1d - adjsccq1d | top4_share | 0.463 | 0.430 | +0.032 |
| deepjsccq1d - adjsccq1d | worst_channel_damage_db | 10.221 | 8.079 | +2.142 |
| deepjsccq1d - adjsccq1d | clean_test_psnr_db | 6.503 | 6.622 | -0.119 |
| deepjsccq1d - adjsccq1d | gain_at_decision_rate_db@oracle | 2.964 | 1.764 | +1.201 |
| deepjsccq1d - adjsccq1d | high_loss_mean_gain_db@oracle | 2.331 | 1.403 | +0.928 |
| deepjsccq1d - adjsccq1d | gain_at_decision_rate_db@energy | 2.982 | 1.782 | +1.200 |
| deepjsccq1d - adjsccq1d | high_loss_mean_gain_db@energy | 2.356 | 1.421 | +0.935 |
| deepjsccq1d - adjsccq1d | gain_at_decision_rate_db@random | 0.634 | 0.805 | -0.171 |
| deepjsccq1d - adjsccq1d | high_loss_mean_gain_db@random | 0.351 | 0.541 | -0.189 |

## Insights

- adjsccq1d: 3 converged model(s), top-4 channels carry 43% of the damage (even split 25% at 16 channels), oracle UEP gain at loss 0.4 +1.76 dB -> criteria met.
- deepjsccq1d: 3 converged model(s), top-4 channels carry 46% of the damage (even split 25% at 16 channels), oracle UEP gain at loss 0.4 +2.96 dB -> criteria met.
- deepjsccq1d: excluded as not converged (best epoch < 50): deepjsccq1d/seed100.
- deepjsccq1d - adjsccq1d: top-4 share +3.2 points, oracle gain at loss 0.4 +1.20 dB.
