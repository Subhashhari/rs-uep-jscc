# Feature-saliency proxies vs true leave-one-out damage

| proxy | within-image Spearman (95% CI) | top-1 hit | top-4 overlap | verdict |
|---|---|---|---|---|
| attention | -0.217 (-0.23..-0.21) | 0.00 | 0.14 | no better than chance |
| energy | +0.868 (+0.86..+0.87) | 0.68 | 0.77 | useful |
| variance | +0.487 (+0.48..+0.50) | 0.03 | 0.48 | weak |
| l1 | +0.752 (+0.74..+0.76) | 0.91 | 0.69 | useful |
| taylor | +0.335 (+0.33..+0.35) | 0.51 | 0.47 | weak |
| random | -0.002 (-0.01..+0.01) | 0.06 | 0.25 | no better than chance |
| static_train_ranking | +0.422 (+0.41..+0.43) | 0.99 | 0.55 | weak |

## Insights

- Proxies ranked by within-image Spearman with the true damage: energy +0.87, l1 +0.75, variance +0.49, static_train_ranking +0.42, taylor +0.34, random -0.00, attention -0.22.
- Static train ranking reaches +0.42: how much of the per-image structure a single global table already explains.
- Best proxy beyond the static table: energy (top-4 overlap 0.77 vs chance 0.25).
