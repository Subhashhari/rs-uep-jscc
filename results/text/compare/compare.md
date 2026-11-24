# Architecture comparison (G1): is sensitivity-aware UEP specific to ADJSCC-Q?

Decision rate: loss 0.4. Gains are paired differences to uniform RS of the best (validation-selected) tiered scheme per source; families use converged models only.

## Per model

| model | arch | clean test PSNR | best epoch | converged | worst ch. (dB) | top-4 share | oracle gain @0.4 (CI) | random gain @0.4 | energy gain @0.4 | oracle mean ≥0.35 |
|---|---|---|---|---|---|---|---|---|---|---|
| adjsccq_text/seed42 | adjsccq_text | 44.02 | 17 | **no** | 14.94 | 29% | +2.06 (±0.11) | +1.02 | +2.13 | +1.10 |
| adjsccq_text/seed100 | adjsccq_text | 43.45 | 20 | **no** | 13.45 | 29% | +2.03 (±0.16) | +1.04 | +2.02 | +1.10 |
| adjsccq_text/seed7 | adjsccq_text | 42.64 | 14 | **no** | 15.75 | 32% | +2.12 (±0.10) | +0.88 | +1.96 | +1.17 |
| deepjsccq_text/seed42 | deepjsccq_text | 69.20 | 60 | yes | 31.10 | 28% | +1.98 (±0.25) | +1.13 | +1.95 | +0.60 |
| deepjsccq_text/seed100 | deepjsccq_text | 43.79 | 14 | **no** | 17.01 | 31% | +1.99 (±0.12) | +0.86 | +2.10 | +1.01 |
| deepjsccq_text/seed7 | deepjsccq_text | 64.63 | 60 | yes | 24.61 | 30% | +3.17 (±0.23) | +2.35 | +3.42 | +1.58 |

## Per family (mean ± sample std over converged models)

| family | models | top-4 share | worst ch. (dB) | clean test PSNR | oracle @0.4 | energy @0.4 | random @0.4 | energy share of oracle | verdict |
|---|---|---|---|---|---|---|---|---|---|
| adjsccq_text | 0 | - | - | - | - | - | - | - | **incomplete** |
| deepjsccq_text | 2 | 29 ± 1% | 27.86 ± 4.59 | 66.91 ± 3.23 | 2.57 ± 0.85 | 2.69 ± 1.04 | 1.74 ± 0.86 | 125 ± 1% | **no exploitable structure** |

## Decision rule (pre-registered, AD-09)

- C1 concentration: family mean top-4 share ≥ 0.40
- C2 UEP gain: every model's oracle gain at loss 0.4 ≥ +2.00 dB, CI above 0
- C3 identity matters: random gain < 0.50 × oracle gain (loss ≥ 0.35)
- FLAT: top-4 share < 0.30 and oracle − random ≤ 0.50 dB

- **adjsccq_text**: incomplete (C1_concentration=None, C2_uep_gain=None, C3_identity_matters=None, FLAT_no_structure=None)
- **deepjsccq_text**: no exploitable structure (C1_concentration=False, C2_uep_gain=False, C3_identity_matters=False, FLAT_no_structure=True)

## Differences between family means

| comparison | quantity | value | reference | difference |
|---|---|---|---|---|

## Insights

- adjsccq_text: 0 converged model(s) -> incomplete.
- adjsccq_text: excluded as not converged (best epoch < 50): adjsccq_text/seed100, adjsccq_text/seed42, adjsccq_text/seed7.
- deepjsccq_text: 2 converged model(s), top-4 channels carry 29% of the damage (even split 25% at 16 channels), oracle UEP gain at loss 0.4 +2.57 dB -> no exploitable structure.
- deepjsccq_text: excluded as not converged (best epoch < 50): deepjsccq_text/seed100.
