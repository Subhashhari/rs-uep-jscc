# Sensitivity head (validation split)

| ranking | top-4 overlap | top-1 hit | within-image Spearman | regret (dB) |
|---|---|---|---|---|
| head (mean over seeds) | 0.910 | 0.982 | +0.903 | 0.14 |
| random | 0.249 | 0.054 | +0.003 | 16.17 |
| static_train_ranking | 0.828 | 0.982 | +0.861 | 0.48 |
| energy | 0.781 | 0.985 | +0.936 | 0.80 |
| variance | 0.383 | 0.032 | +0.432 | 10.74 |

## Insights

- Head top-4 overlap on validation: 0.910 ± 0.001 over 5 head seeds (random 0.25, static table 0.83).
- Protection regret: head 0.14 dB vs static table 0.48 dB vs random 16.17 dB per image.
- The head costs 2048 MACs = 0.024% of the encoder.
- The head beats the static table on top-4 overlap (+0.082); if images share one ranking the online predictor is unnecessary.
