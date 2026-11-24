# Sensitivity head (validation split)

| ranking | top-4 overlap | top-1 hit | within-image Spearman | regret (dB) |
|---|---|---|---|---|
| head (mean over seeds) | 0.881 | 0.933 | +0.916 | 0.34 |
| random | 0.248 | 0.064 | +0.004 | 12.65 |
| static_train_ranking | 0.712 | 0.804 | +0.735 | 2.30 |
| energy | 0.668 | 0.381 | +0.839 | 2.35 |
| variance | 0.436 | 0.267 | +0.348 | 7.88 |

## Insights

- Head top-4 overlap on validation: 0.881 ± 0.001 over 5 head seeds (random 0.25, static table 0.71).
- Protection regret: head 0.34 dB vs static table 2.30 dB vs random 12.65 dB per image.
- The head costs 2048 MACs = 0.039% of the encoder.
- The head beats the static table on top-4 overlap (+0.169); if images share one ranking the online predictor is unnecessary.
