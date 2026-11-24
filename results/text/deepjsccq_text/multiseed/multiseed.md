# Multi-seed oracle comparison

| model | clean val PSNR | top-4 channels | worst (dB) | least (dB) | top-4 share | bands |
|---|---|---|---|---|---|---|
| seed42 | 69.53 | [11, 2, 0, 8] | 31.10 | 15.94 | 28% | {'catastrophic (>10 dB)': 16, 'high (5-10 dB)': 0, 'medium (2-5 dB)': 0, 'low (<2 dB)': 0} |
| seed100 | 44.16 | [12, 6, 1, 2] | 17.01 | 8.53 | 31% | {'catastrophic (>10 dB)': 15, 'high (5-10 dB)': 1, 'medium (2-5 dB)': 0, 'low (<2 dB)': 0} |
| seed7 | 65.00 | [7, 15, 6, 10] | 24.61 | 12.36 | 30% | {'catastrophic (>10 dB)': 16, 'high (5-10 dB)': 0, 'medium (2-5 dB)': 0, 'low (<2 dB)': 0} |

## Insights

- Most damaging channel per model: seed42 31.1 dB (channel 11), seed100 17.0 dB (channel 12), seed7 24.6 dB (channel 7).
- Index-aligned Spearman between models averages -0.05: channel labels do permute between initialisations, as expected.
- Sorted damage profiles agree: mean Pearson 0.904, mean absolute difference 9.46 dB per channel.
- Every model has a catastrophic (>10 dB) channel.
- Share of total damage carried by the top-4 channels: seed42 28%, seed100 31%, seed7 30%.
