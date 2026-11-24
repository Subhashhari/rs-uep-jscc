# Feature-saliency proxies vs true leave-one-out damage

| proxy | within-image Spearman (95% CI) | top-1 hit | top-4 overlap | verdict |
|---|---|---|---|---|
| energy | +0.936 (+0.93..+0.94) | 0.98 | 0.78 | useful |
| variance | +0.429 (+0.42..+0.44) | 0.03 | 0.38 | weak |
| l1 | +0.906 (+0.90..+0.91) | 0.98 | 0.77 | useful |
| taylor | +0.528 (+0.52..+0.54) | 0.27 | 0.50 | useful |
| random | +0.001 (-0.01..+0.01) | 0.05 | 0.25 | no better than chance |
| static_train_ranking | +0.859 (+0.85..+0.86) | 0.98 | 0.82 | useful |

## Insights

- Proxies ranked by within-image Spearman with the true damage: energy +0.94, l1 +0.91, static_train_ranking +0.86, taylor +0.53, variance +0.43, random +0.00.
- Static train ranking reaches +0.86: how much of the per-image structure a single global table already explains.
- Best proxy beyond the static table: energy (top-4 overlap 0.78 vs chance 0.25).
