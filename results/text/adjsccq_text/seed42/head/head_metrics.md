# Sensitivity head (validation split)

| ranking | top-4 overlap | top-1 hit | within-image Spearman | regret (dB) |
|---|---|---|---|---|
| head (mean over seeds) | 0.605 | 0.433 | +0.801 | 2.47 |
| random | 0.247 | 0.058 | +0.000 | 10.74 |
| static_train_ranking | 0.591 | 0.397 | +0.784 | 2.64 |
| energy | 0.633 | 0.357 | +0.797 | 2.13 |
| variance | 0.613 | 0.327 | +0.795 | 2.35 |
| attention | 0.150 | 0.000 | -0.119 | 14.18 |

## Insights

- Head top-4 overlap on validation: 0.605 ± 0.001 over 5 head seeds (random 0.25, static table 0.59).
- Protection regret: head 2.47 dB vs static table 2.64 dB vs random 10.74 dB per image.
- The head costs 2048 MACs = 0.018% of the encoder.
- The head does NOT clearly beat the static table on top-4 overlap (+0.014); if images share one ranking the online predictor is unnecessary.
