# Sensitivity head (validation split)

| ranking | top-4 overlap | top-1 hit | within-image Spearman | regret (dB) |
|---|---|---|---|---|
| head (mean over seeds) | 0.657 | 0.269 | +0.769 | 3.12 |
| random | 0.247 | 0.059 | -0.013 | 18.16 |
| static_train_ranking | 0.657 | 0.273 | +0.768 | 3.13 |
| energy | 0.481 | 0.252 | +0.418 | 9.75 |
| variance | 0.480 | 0.247 | +0.417 | 9.66 |

## Insights

- Head top-4 overlap on validation: 0.657 ± 0.000 over 5 head seeds (random 0.25, static table 0.66).
- Protection regret: head 3.12 dB vs static table 3.13 dB vs random 18.16 dB per image.
- The head costs 2048 MACs = 0.018% of the encoder.
- The head does NOT clearly beat the static table on top-4 overlap (+0.000); if images share one ranking the online predictor is unnecessary.
