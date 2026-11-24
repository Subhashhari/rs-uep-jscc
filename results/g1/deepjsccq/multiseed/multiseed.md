# Multi-seed oracle comparison

| model | clean val PSNR | top-4 channels | worst (dB) | least (dB) | top-4 share | bands |
|---|---|---|---|---|---|---|
| seed42 | 32.35 | [8, 7, 5, 14] | 11.68 | 4.35 | 35% | {'catastrophic (>10 dB)': 1, 'high (5-10 dB)': 12, 'medium (2-5 dB)': 3, 'low (<2 dB)': 0} |
| seed100 | 31.51 | [3, 4, 2, 13] | 11.22 | 3.21 | 33% | {'catastrophic (>10 dB)': 1, 'high (5-10 dB)': 13, 'medium (2-5 dB)': 2, 'low (<2 dB)': 0} |
| seed7 | 31.62 | [1, 6, 15, 11] | 11.43 | 0.26 | 40% | {'catastrophic (>10 dB)': 2, 'high (5-10 dB)': 8, 'medium (2-5 dB)': 5, 'low (<2 dB)': 1} |
| seed13 | 32.36 | [12, 11, 13, 2] | 10.49 | 3.39 | 40% | {'catastrophic (>10 dB)': 2, 'high (5-10 dB)': 6, 'medium (2-5 dB)': 8, 'low (<2 dB)': 0} |

## Insights

- Most damaging channel per model: seed42 11.7 dB (channel 8), seed100 11.2 dB (channel 3), seed7 11.4 dB (channel 1), seed13 10.5 dB (channel 12).
- Index-aligned Spearman between models averages -0.19: channel labels do permute between initialisations, as expected.
- Sorted damage profiles agree: mean Pearson 0.930, mean absolute difference 1.01 dB per channel.
- Every model has a catastrophic (>10 dB) channel.
- Share of total damage carried by the top-4 channels: seed42 35%, seed100 33%, seed7 40%, seed13 40%.
