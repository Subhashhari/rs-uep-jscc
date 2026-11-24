# Multi-seed oracle comparison

| model | clean val PSNR | top-4 channels | worst (dB) | least (dB) | top-4 share | bands |
|---|---|---|---|---|---|---|
| seed42 | 7.21 | [4, 6, 13, 7] | 9.82 | 1.43 | 46% | {'catastrophic (>10 dB)': 0, 'high (5-10 dB)': 1, 'medium (2-5 dB)': 2, 'low (<2 dB)': 13} |
| seed100 | 7.05 | [14, 12, 2, 13] | 9.26 | 1.44 | 45% | {'catastrophic (>10 dB)': 0, 'high (5-10 dB)': 1, 'medium (2-5 dB)': 4, 'low (<2 dB)': 11} |
| seed7 | 7.30 | [15, 11, 9, 12] | 5.15 | 1.44 | 38% | {'catastrophic (>10 dB)': 0, 'high (5-10 dB)': 1, 'medium (2-5 dB)': 2, 'low (<2 dB)': 13} |

## Insights

- Most damaging channel per model: seed42 9.8 dB (channel 4), seed100 9.3 dB (channel 14), seed7 5.2 dB (channel 15).
- Index-aligned Spearman between models averages -0.01: channel labels do permute between initialisations, as expected.
- Sorted damage profiles agree: mean Pearson 0.973, mean absolute difference 0.30 dB per channel.
- NOT every model has a >10 dB channel: the 'one catastrophic channel' claim needs softening.
- Share of total damage carried by the top-4 channels: seed42 46%, seed100 45%, seed7 38%.
