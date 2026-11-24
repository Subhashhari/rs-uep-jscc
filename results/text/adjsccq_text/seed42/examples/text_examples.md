# Text check (character / word accuracy, bits per character)

500 test windows of 2048 characters, channel seed 0.

| method | loss | char acc (%) | word acc (%) | bits/char |
|---|---|---|---|---|
| no_rs | 0 | 44.12 | 13.33 | 2.589 |
| uniform | 0 | 44.12 | 13.33 | 2.589 |
| three_tier_25_50_25@oracle | 0 | 44.12 | 13.33 | 2.589 |
| three_tier_25_50_25@energy | 0 | 44.12 | 13.33 | 2.589 |
| three_tier_25_50_25@attention | 0 | 44.12 | 13.33 | 2.589 |
| no_rs | 0.3 | 21.05 | 3.02 | 8.164 |
| uniform | 0.3 | 39.46 | 11.30 | 3.777 |
| three_tier_25_50_25@oracle | 0.3 | 31.92 | 7.33 | 4.906 |
| three_tier_25_50_25@energy | 0.3 | 32.07 | 7.46 | 4.798 |
| three_tier_25_50_25@attention | 0.3 | 30.73 | 6.88 | 5.148 |
| no_rs | 0.35 | 19.80 | 2.60 | 8.663 |
| uniform | 0.35 | 29.59 | 6.99 | 6.302 |
| three_tier_25_50_25@oracle | 0.35 | 27.41 | 5.51 | 6.243 |
| three_tier_25_50_25@energy | 0.35 | 27.51 | 5.58 | 6.138 |
| three_tier_25_50_25@attention | 0.35 | 26.16 | 4.99 | 6.513 |
| no_rs | 0.4 | 18.68 | 2.22 | 9.101 |
| uniform | 0.4 | 21.16 | 3.35 | 8.501 |
| three_tier_25_50_25@oracle | 0.4 | 23.30 | 3.87 | 7.584 |
| three_tier_25_50_25@energy | 0.4 | 23.24 | 3.89 | 7.512 |
| three_tier_25_50_25@attention | 0.4 | 22.15 | 3.48 | 7.832 |
| no_rs | 0.5 | 16.88 | 1.71 | 9.683 |
| uniform | 0.5 | 16.88 | 1.71 | 9.683 |
| three_tier_25_50_25@oracle | 0.5 | 18.52 | 2.20 | 9.247 |
| three_tier_25_50_25@energy | 0.5 | 18.53 | 2.20 | 9.199 |
| three_tier_25_50_25@attention | 0.5 | 17.85 | 1.99 | 9.355 |
