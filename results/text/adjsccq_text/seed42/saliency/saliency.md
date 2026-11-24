# Feature-saliency proxies vs true leave-one-out damage

| proxy | within-image Spearman (95% CI) | top-1 hit | top-4 overlap | verdict |
|---|---|---|---|---|
| attention | -0.119 (-0.13..-0.11) | 0.00 | 0.15 | no better than chance |
| energy | +0.798 (+0.79..+0.80) | 0.36 | 0.63 | useful |
| variance | +0.795 (+0.79..+0.80) | 0.33 | 0.61 | useful |
| l1 | +0.794 (+0.79..+0.80) | 0.38 | 0.64 | useful |
| taylor | +0.195 (+0.18..+0.21) | 0.15 | 0.37 | no better than chance |
| random | -0.002 (-0.01..+0.01) | 0.06 | 0.25 | no better than chance |
| static_train_ranking | +0.783 (+0.78..+0.79) | 0.40 | 0.59 | useful |

## Insights

- Proxies ranked by within-image Spearman with the true damage: energy +0.80, variance +0.79, l1 +0.79, static_train_ranking +0.78, taylor +0.20, random -0.00, attention -0.12.
- Static train ranking reaches +0.78: how much of the per-image structure a single global table already explains.
- Best proxy beyond the static table: energy (top-4 overlap 0.64 vs chance 0.25).
