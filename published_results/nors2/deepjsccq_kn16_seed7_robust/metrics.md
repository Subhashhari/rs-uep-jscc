# Erasure-robust fine-tuning

- Clean validation PSNR: 32.18 -> 29.34 dB (-2.84 dB; roadmap budget: lose < 0.3 dB).
- Channel-drop PSNR at 40%: 16.30 -> 23.38 dB; packet-drop at 40%: 16.19 -> 23.43 dB.
- Best epoch 16 of 40; robust score 21.89 -> 26.18 dB.
- Clean PSNR collapsed (> 2 dB): over-regularised. Lower --p_max to 0.3 or use --curriculum_epochs 20.
