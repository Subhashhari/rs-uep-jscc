# Text check (character / word accuracy, bits per character)

500 test windows of 2048 characters, channel seed 0.

| method | loss | char acc (%) | word acc (%) | bits/char |
|---|---|---|---|---|
| no_rs | 0 | 69.36 | 32.22 | 1.347 |
| uniform | 0 | 69.36 | 32.22 | 1.347 |
| three_tier_25_50_25@oracle | 0 | 69.36 | 32.22 | 1.347 |
| three_tier_25_50_25@energy | 0 | 69.36 | 32.22 | 1.347 |
| no_rs | 0.3 | 22.18 | 2.96 | 24.194 |
| uniform | 0.3 | 59.96 | 26.56 | 6.383 |
| three_tier_25_50_25@oracle | 0.3 | 42.26 | 13.71 | 11.162 |
| three_tier_25_50_25@energy | 0.3 | 41.00 | 12.70 | 10.606 |
| no_rs | 0.35 | 20.01 | 2.31 | 26.921 |
| uniform | 0.35 | 40.10 | 14.78 | 17.090 |
| three_tier_25_50_25@oracle | 0.35 | 33.18 | 8.67 | 16.676 |
| three_tier_25_50_25@energy | 0.35 | 32.53 | 8.11 | 15.940 |
| no_rs | 0.4 | 18.06 | 1.76 | 29.469 |
| uniform | 0.4 | 23.20 | 4.91 | 26.916 |
| three_tier_25_50_25@oracle | 0.4 | 25.35 | 4.76 | 22.436 |
| three_tier_25_50_25@energy | 0.4 | 25.36 | 4.60 | 21.553 |
| no_rs | 0.5 | 14.91 | 1.17 | 34.031 |
| uniform | 0.5 | 14.91 | 1.17 | 34.031 |
| three_tier_25_50_25@oracle | 0.5 | 16.98 | 1.61 | 31.079 |
| three_tier_25_50_25@energy | 0.5 | 17.33 | 1.66 | 30.267 |
