# Feature-saliency proxies vs true leave-one-out damage

| proxy | within-image Spearman (95% CI) | top-1 hit | top-4 overlap | verdict |
|---|---|---|---|---|
| energy | +0.420 (+0.41..+0.43) | 0.26 | 0.49 | weak |
| variance | +0.418 (+0.41..+0.43) | 0.25 | 0.48 | weak |
| l1 | +0.430 (+0.42..+0.44) | 0.27 | 0.49 | weak |
| taylor | +0.049 (+0.04..+0.06) | 0.10 | 0.30 | no better than chance |
| random | -0.010 (-0.02..+0.00) | 0.06 | 0.25 | no better than chance |
| static_train_ranking | +0.767 (+0.76..+0.77) | 0.28 | 0.65 | useful |

## Insights

- Proxies ranked by within-image Spearman with the true damage: static_train_ranking +0.77, l1 +0.43, energy +0.42, variance +0.42, taylor +0.05, random -0.01.
- Static train ranking reaches +0.77: how much of the per-image structure a single global table already explains.
- Best proxy beyond the static table: l1 (top-4 overlap 0.49 vs chance 0.25).
