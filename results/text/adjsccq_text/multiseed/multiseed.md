# Multi-seed oracle comparison

| model | clean val PSNR | top-4 channels | worst (dB) | least (dB) | top-4 share | bands |
|---|---|---|---|---|---|---|
| seed42 | 44.37 | [0, 12, 11, 9] | 14.94 | 7.72 | 29% | {'catastrophic (>10 dB)': 13, 'high (5-10 dB)': 3, 'medium (2-5 dB)': 0, 'low (<2 dB)': 0} |
| seed100 | 43.76 | [6, 0, 11, 7] | 13.45 | 8.20 | 29% | {'catastrophic (>10 dB)': 13, 'high (5-10 dB)': 3, 'medium (2-5 dB)': 0, 'low (<2 dB)': 0} |
| seed7 | 42.95 | [9, 13, 14, 15] | 15.75 | 8.08 | 32% | {'catastrophic (>10 dB)': 12, 'high (5-10 dB)': 4, 'medium (2-5 dB)': 0, 'low (<2 dB)': 0} |

## Insights

- Most damaging channel per model: seed42 14.9 dB (channel 0), seed100 13.5 dB (channel 6), seed7 15.7 dB (channel 9).
- Index-aligned Spearman between models averages +0.19: channel labels do permute between initialisations, as expected.
- Sorted damage profiles agree: mean Pearson 0.936, mean absolute difference 0.89 dB per channel.
- Every model has a catastrophic (>10 dB) channel.
- Share of total damage carried by the top-4 channels: seed42 29%, seed100 29%, seed7 32%.
