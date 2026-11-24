# Multi-seed oracle comparison

| model | clean val PSNR | top-4 channels | worst (dB) | least (dB) | top-4 share | bands |
|---|---|---|---|---|---|---|
| seed42 | 7.06 | [0, 5, 15, 14] | 11.70 | 1.36 | 48% | {'catastrophic (>10 dB)': 1, 'high (5-10 dB)': 7, 'medium (2-5 dB)': 0, 'low (<2 dB)': 8} |
| seed100 | 7.13 | [12, 6, 3, 13] | 5.75 | 1.37 | 37% | {'catastrophic (>10 dB)': 0, 'high (5-10 dB)': 1, 'medium (2-5 dB)': 1, 'low (<2 dB)': 14} |
| seed7 | 7.01 | [8, 15, 0, 10] | 9.42 | 1.42 | 46% | {'catastrophic (>10 dB)': 0, 'high (5-10 dB)': 5, 'medium (2-5 dB)': 6, 'low (<2 dB)': 5} |
| seed13 | 7.09 | [4, 9, 0, 13] | 9.54 | 1.61 | 46% | {'catastrophic (>10 dB)': 0, 'high (5-10 dB)': 2, 'medium (2-5 dB)': 11, 'low (<2 dB)': 3} |

## Insights

- Most damaging channel per model: seed42 11.7 dB (channel 0), seed100 5.7 dB (channel 12), seed7 9.4 dB (channel 8), seed13 9.5 dB (channel 4).
- Index-aligned Spearman between models averages +0.06: channel labels do permute between initialisations, as expected.
- Sorted damage profiles agree: mean Pearson 0.828, mean absolute difference 1.62 dB per channel.
- NOT every model has a >10 dB channel: the 'one catastrophic channel' claim needs softening.
- Share of total damage carried by the top-4 channels: seed42 48%, seed100 37%, seed7 46%, seed13 46%.
