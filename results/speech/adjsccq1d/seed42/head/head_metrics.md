# Sensitivity head (validation split)

| ranking | top-4 overlap | top-1 hit | within-image Spearman | regret (dB) |
|---|---|---|---|---|
| head (mean over seeds) | 0.677 | 0.989 | +0.639 | 0.71 |
| random | 0.254 | 0.062 | -0.001 | 8.43 |
| static_train_ranking | 0.559 | 0.988 | +0.422 | 1.41 |
| energy | 0.774 | 0.691 | +0.867 | 0.89 |
| variance | 0.477 | 0.024 | +0.482 | 7.90 |
| attention | 0.143 | 0.000 | -0.216 | 10.78 |

## Insights

- Head top-4 overlap on validation: 0.677 ± 0.002 over 5 head seeds (random 0.25, static table 0.56).
- Protection regret: head 0.71 dB vs static table 1.41 dB vs random 8.43 dB per image.
- The head costs 2048 MACs = 0.024% of the encoder.
- The head beats the static table on top-4 overlap (+0.119); if images share one ranking the online predictor is unnecessary.
