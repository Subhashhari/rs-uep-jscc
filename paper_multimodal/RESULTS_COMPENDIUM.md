# Results compendium for the multimodal paper, tiered by usefulness

Every result the project has produced (images, speech, text), with its numbers, its source file and
where it belongs in the paper. Compiled 2026-11-24 from `results/` (speech, text, image DeepJSCC-Q,
early image sweeps) and `published_results/` + `paper/generated_numbers.tex` (image ADJSCC-Q main
study, coding controls, baselines). Nothing was re-run; every number below is copied from a result file.

**Tiers**

| Tier | Meaning | Where in the paper |
|---|---|---|
| **1** | Headline evidence. The paper's claims fail without it. | Main text, with a figure or table |
| **2** | Strong support: replication, fair baselines, mechanisms. | Main text |
| **3** | Context and robustness. Useful, not decisive. | Short paragraph in main text, details in appendix |
| **4** | Diagnostics and per-seed detail. | Appendix / supplementary only |
| **5** | Do not use as is: superseded, not converged, broken metric, or inconsistent. | Nowhere (or a footnote) until fixed |

**Units.** Gains are paired differences against uniform RS(96,64) under identical loss masks (5
channel seeds; 95% CI over seeds is ≤ 0.05 dB for images unless stated). Images: PSNR (dB). Speech:
per-segment SNR (dB), the result files store it in `psnr_db_*`. Text: per-window character accuracy
(%), stored in `psnr_db_*` and labelled "dB" in every auto-generated table; a "dB" for text means
**percentage points (pp)**. Hand-tiered = `three_tier_25_50_25` = RS(32,16) / RS(48,32) / (16,16).

---

## 0. Before writing: conflicts and gaps (fix these first)

| # | Issue | Evidence | Action |
|---|---|---|---|
| G1 | **Two definitions of "top-4 share".** | GLOBECOM macros: share of LOO **MSE** damage (66–84% ADJSCC-Q, 69–72% DeepJSCC-Q). All `multiseed.md`: share of LOO **dB** damage (45–53% images, 43–46% speech, 29% text). | Pick one for all modalities. The dB share exists for every modality now; the MSE share would need recomputation for speech and text. |
| G2 | **Two sets of image DeepJSCC-Q models.** | `paper/generated_tables.tex`: seeds 100/21/7, clean 31.79/32.73/32.17. `results/g1/deepjsccq/`: seeds 42/100/13/7, clean 32.38/31.54/32.40/31.66. | Decide which set is "the" DeepJSCC-Q image family; report the other as replication or drop it. |
| G3 | **Truncation / optimal allocation only exists for images.** | `published_results/coding/seed42/coding_controls_test.md` (images). Speech and text sweeps contain hand-designed tiers only. | Run `opt_trunc`, `opt_grouped`, `opt_pet`, selector on speech and text before claiming "truncation is optimal" across modalities. Highest-value missing experiment. |
| G4 | **No converged attention model for text.** | All three `adjsccq_text` seeds stopped improving at epoch 14–20 (< 50); clean char. acc. 42.6–44.0%. | Either retrain (wider model, shorter windows) or state that the text attention ablation is incomplete. |
| G5 | **Text proxy table came from a non-converged model.** | `results/text/adjsccq_text/seed42/saliency` (energy +0.80) vs converged `deepjsccq_text/seed42/saliency` (energy **+0.42**). | Use the converged model's numbers (done in the draft). Attention on text is only measurable on the non-converged ADJSCC-Q-text. |
| G6 | **PESQ-WB / STOI are empty.** | `results/speech/*/seed42/perceptual/perceptual.md`: all "-". | Install `pesq`/`pystoi` and re-run, or drop the claim and report SNR + SI-SDR only. |
| G7 | **Speech and text absolute quality is low.** | Clean speech SNR 6.4–6.7 dB; clean text char. acc. 64.6–69.2% (word acc. ≈ 32%). | Frame all claims as protection of a given latent, not JSCC quality. Reviewers will ask. |
| G8 | **Text at ≥ 40% loss is near chance.** | Uniform at 40%: 23.4% / 25.7% char. acc.; no RS: 17.9% / 21.2%; the most-frequent-symbol guess gives ≈ 18%. | Report text gains at 40% with this caveat; the useful regime (≤ 30%) is where uniform RS wins by 8–17 pp. |
| G9 | **Burst, Kodak, bandwidth, robust-training and codec studies are image-only.** | `published_results/gpu/final/burst`, `phase3`, `phase2`, `digital`. | Fine for this draft; list as limitations for speech/text. |
| G10 | **SSIM computed with zero-padded windows.** | Noted in the GLOBECOM draft. | Report PSNR only, or fix SSIM and recompute. |

---

## Tier 1: headline evidence

### 1.1 Erasure sensitivity of image latents is concentrated, and not because of attention
- **ADJSCC-Q, CIFAR-10, 5 converged seeds** (`published_results/gpu/phase1/multiseed/multiseed.md`):
  top-4 of 16 channels carry **45, 47, 50, 52, 53 %** of LOO dB damage (even split: 25%). Worst
  channel 8.7–17.1 dB, least 0.9–2.2 dB. Sorted profiles agree across seeds (mean Pearson **0.922**,
  mean abs. diff. 0.83 dB/channel), channel indices permute (index-aligned Spearman −0.13).
- **DeepJSCC-Q (all attention removed), 4 seeds** (`results/g1/deepjsccq/multiseed/multiseed.md`):
  top-4 share **33–40 %** (dB); every seed has a > 10 dB channel (10.5–11.7 dB); profile Pearson 0.930;
  aligned Spearman −0.19. Less concentrated than ADJSCC-Q in dB share, but clearly above 25%.
- MSE-share version (GLOBECOM macros): ADJSCC-Q 66–84%, DeepJSCC-Q 69–72%.
- **Use:** Fig. (sorted profiles; `paper/figures/fig_profiles.pdf`, `results/g1/deepjsccq/multiseed/damage_profiles.png`).

### 1.2 Attention gates do not rank erasure damage, in any modality
| Modality / model | Within-sample Spearman (attention vs LOO) | Top-4 overlap (chance 0.25) | Pooled Pearson | Source |
|---|---|---|---|---|
| Image, ADJSCC-Q s42 | **−0.015** (CI −0.020…−0.011) | 0.23 | +0.118 | `published_results/gpu/phase1/saliency/saliency.md`, INSIGHTS |
| Speech, ADJSCC-Q-1D s42 | **−0.217** (CI −0.226…−0.208) | 0.14 | −0.260 | `results/speech/adjsccq1d/seed42/attention/attention_vs_damage.json` |
| Text, ADJSCC-Q-text s42 (not converged) | **−0.119** (CI −0.125…−0.111) | 0.15 | −0.167 | `results/text/adjsccq_text/seed42/attention/attention_vs_damage.json` |

Consequence for protection (25/50/25 tiers, 40% loss): attention order gains **+0.74 dB** (image s42)
vs +2.86 dB LOO order; on four other image seeds −0.33…+0.54 dB. Speech ADJSCC-Q-1D: **+0.37 / +0.39 /
+0.88 dB** vs +2.01 / +1.76 / +1.52 dB LOO. Under optimal truncation, attention order loses 1.7 dB to LOO
order on s42 (25.52 vs 27.25 dB) and on seed 21 falls below random order (20.78 vs 22.24 dB).
- **Use:** one figure (image scatter `results/eval/oracle_attention_correlation.png` + speech scatter
  `results/speech/adjsccq1d/seed42/attention/fig2_left_attention_scatter.png`) and a row in the proxy table.

### 1.3 The ranking is the gain, not the tiering (images)
Primary ADJSCC-Q (s42), CIFAR-10 test, 10,000 images × 5 channel seeds, 25/50/25 tiers
(`published_results/gpu/report/headline.md`, `coding_controls_test.md`):

| Loss | uniform | no RS | LOO | energy | L1 | head | per-image LOO | random | attention |
|---|---|---|---|---|---|---|---|---|---|
| 0.30 | 28.67 | 21.16 | −0.95 | −0.92 | −0.95 | −0.87 | −0.77 | −3.33 | −3.10 |
| 0.35 | 24.40 | 20.36 | +1.31 | +1.36 | +1.33 | +1.42 | +1.52 | −0.93 | −0.93 |
| **0.40** | **20.73** | 19.62 | **+2.86** | +2.92 | +2.89 | **+3.00** | +3.08 | **+0.94** | **+0.74** |
| 0.45 | 19.07 | 18.94 | +2.69 | +2.76 | +2.73 | +2.83 | +2.90 | +1.17 | +0.88 |
| 0.50 | 18.31 | 18.31 | +1.89 | +1.94 | +1.92 | +2.00 | +2.05 | +0.81 | +0.55 |

(uniform and no-RS columns are PSNR in dB; the others are gains in dB.) Mean over loss ≥ 35%, best scheme
per ranking: head +2.31, energy +2.24, L1 +2.22, LOO +2.19, random +0.50, attention +0.31 dB. Share of LOO
gain: head 106%, energy 102%, L1 101%, random 23%, attention 14%.
- **Use:** main results figure (`paper/figures/fig_main.pdf` or `published_results` sweep plot) + bar chart.

### 1.4 The optimal allocation at a known loss rate is importance-ordered truncation (images)
`published_results/coding/seed42/coding_controls_test.md`, macros in `paper/generated_numbers.tex`.

| Method (primary model) | 0.30 | 0.35 | **0.40** | 0.45 | 0.50 |
|---|---|---|---|---|---|
| uniform RS(96,64) | 28.67 | 24.40 | **20.73** | 19.07 | 18.31 |
| hand-tiered 25/50/25, LOO | −0.95 | +1.31 | +2.86 | +2.69 | +1.89 |
| PET twin of 25/50/25 | −0.41 | +1.53 | +2.78 | +2.93 | +2.37 |
| Grad-FEC style (top 8 coded, 4 dropped) | −3.03 | +1.04 | +4.52 | +5.97 | +6.35 |
| opt. truncation, random order | −2.02 | −0.26 | +1.58 | +1.77 | +1.05 |
| opt. truncation, attention order | +0.80 | +4.12 | +4.80 | +1.92 | −0.19 |
| opt. truncation, energy order | +0.90 | +3.74 | +6.00 | +6.27 | +5.90 |
| opt. truncation, 2,048-MAC head | +0.92 | +3.92 | +6.37 | +6.57 | +6.40 |
| **opt. truncation, LOO order** | +0.80 | +4.12 | **+6.52** | +6.68 | +6.21 |
| opt. grouped (multi-tier allowed) | +0.80 | +4.14 | +6.52 | +6.68 | +6.35 |
| opt. PET | +0.73 | +4.01 | +6.30 | +6.79 | +6.29 |
| selector (one byte of signalling per rate change) | +0.80 | +4.14 | +6.52 | +6.79 | +6.35 |

At 0–20% loss every optimized design equals uniform RS (gain 0.00): **no low-loss penalty**. Truncation
depth chosen on validation: keep 16 channels at 10–20% loss, 15 at 30%, 14 at 35%, 13 at 40%,
12 at 45% and 10 at 50%. 25 surrogate-best multi-tier allocations improve on truncation by at most **0.15 dB**;
PET designs are within **0.25 dB**. 40% loss PSNR: truncation 27.25 dB vs uniform 20.73 dB.
Across all **8 converged image models**: LOO truncation +4.0 to +9.4 dB at 40% (ADJSCC-Q +4.02…+6.52,
DeepJSCC-Q +6.10…+9.45), beating the hand-tiered scheme by +1.7…+5.8 dB on every model.
- **Use:** allocation table + per-model table (`paper/generated_tables.tex`).

### 1.5 Exact MDS outcome and a closed-form surrogate
- Lemma: data byte lost iff its packet is erased and its codeword has > n−k erasures;
  q(n,k,p) = p·Pr[Bin(n−1,p) ≥ n−k]. Verified symbol by symbol against a GF(256) RS decoder.
- Simulator reproduces the published RS-decoded sweep to **0.000 dB** on **56** overlapping cells.
- Additive surrogate vs simulated mean MSE: Spearman **0.997**, median relative error **5.4%** over 77 cells.
- **Use:** method section; surrogate scatter `paper/figures/fig_surrogate.pdf`.

### 1.6 Speech: the same structure, the same conclusion
`results/speech/compare/compare.md` (decision rate 40%, validation-selected tiered scheme, converged models).

| Model | clean SNR | top-4 share | worst ch. | LOO gain @40% (CI) | energy | random | verdict |
|---|---|---|---|---|---|---|---|
| ADJSCC-Q-1D s42 | 6.73 | 46% | 9.82 | +2.01 (±0.02) | +2.10 | +0.84 | |
| ADJSCC-Q-1D s100 | 6.42 | 45% | 9.26 | +1.76 (±0.04) | +1.66 | +0.77 | |
| ADJSCC-Q-1D s7 | 6.71 | 38% | 5.15 | +1.52 (±0.03) | +1.59 | +0.80 | |
| **family** | 6.62 ± 0.17 | **43 ± 4%** | 8.08 ± 2.55 | **+1.76 ± 0.24** | +1.78 | +0.81 | **criteria met** |
| DeepJSCC-Q-1D s42 | 6.53 | 48% | 11.70 | +3.36 (±0.09) | +3.19 | +0.53 | |
| DeepJSCC-Q-1D s7 | 6.46 | 46% | 9.42 | +2.90 (±0.07) | +2.94 | +0.66 | |
| DeepJSCC-Q-1D s13 | 6.52 | 46% | 9.54 | +2.64 (±0.05) | +2.82 | +0.71 | |
| **family** | 6.50 ± 0.04 | **46 ± 1%** | 10.22 ± 1.29 | **+2.96 ± 0.36** | +2.98 | +0.63 | **criteria met** |

Pre-registered criteria (AD-09): C1 top-4 share ≥ 40%; C2 every model's LOO gain at 40% ≥ +1.5 dB with
CI > 0; C3 random gain < ½ LOO gain. Energy recovers 101 ± 7% / 102 ± 6% of the LOO gain. Sorted profiles
agree across seeds (Pearson 0.973 ADJSCC-Q-1D, 0.828 DeepJSCC-Q-1D); indices permute.
- **Use:** speech results subsection, sorted-profile figure, SNR-vs-loss figure, gain-by-family figure
  (`results/speech/compare/{sorted_profiles,oracle_gain_by_family,gain_vs_concentration}.png`).

### 1.7 Text: the boundary case, flat sensitivity and little to exploit
`results/text/compare/compare.md`, `results/text/*/multiseed/multiseed.md`.
- Only **2 of 6** text models converged (DeepJSCC-Q-text s42, s7; clean char. acc. 69.2 / 64.6%, word
  acc. ≈ 32%, 1.34 bits/char). All three ADJSCC-Q-text and DeepJSCC-Q-text s100 stopped at epoch 14–20
  (clean 42.6–44.0%).
- Converged models: top-4 share **28–30 %** (25% = flat); **every** channel costs > 10 pp when lost
  (worst 24.6–31.1 pp, least 12.4–15.9 pp). Profile Pearson 0.904, aligned Spearman −0.05.
- Gain at 40% (validation-selected): LOO **+2.57 ± 0.85 pp**, energy +2.69, random **+1.74** → verdict
  **FLAT, "no exploitable structure"** (C1, C2, C3 all fail).
- Context: at 40% loss uniform gives 23.4% (s42) / 25.7% (s7) char. acc. and no RS 17.9% / 21.2%, close
  to the ≈ 18% most-frequent-symbol floor. At 30% loss, where text is still readable, uniform RS gives
  58.8% / 55.9% and the hand-tiered scheme loses **17.0 / 11.8 pp** to it.
- **Use:** text results subsection, flat-profile figure (`results/text/compare/sorted_profiles.png`),
  examples table. The message is "measure first: the measurement can say *don't*".

### 1.8 Cross-modal synthesis
| Modality / family | converged | top-4 share (dB) | attention ρs | energy ρs | static ρs | LOO gain @40% | random gain @40% | random/LOO |
|---|---|---|---|---|---|---|---|---|
| Image ADJSCC-Q | 5 | 45–53% | −0.015 | +0.84 | +0.89 | +2.86 (s42, hand) / +6.52 (trunc.) | +0.94 / +1.58 | 0.33 / 0.24 |
| Image DeepJSCC-Q (results/g1) | 4 | 33–40% | – | +0.84 | +0.74 | +2.11…+2.76 (hand) | +0.56…+0.64 | ≈ 0.26 |
| Speech ADJSCC-Q-1D | 3 | 43 ± 4% | −0.22 | +0.87 | +0.42 | +1.76 ± 0.24 | +0.81 | 0.46 |
| Speech DeepJSCC-Q-1D | 3 | 46 ± 1% | – | +0.94 | +0.86 | +2.96 ± 0.36 | +0.63 | 0.21 |
| Text DeepJSCC-Q-text | 2 | 29 ± 1% | – | +0.42 | +0.77 | +2.57 ± 0.85 pp | +1.74 pp | 0.68 |

The share of the gain that a random order already gets rises as concentration falls: ≈ 0.2–0.3 for
images and DeepJSCC speech, 0.46 for ADJSCC speech, 0.68 for text. **Main new figure:** one scatter of
LOO and random gain against top-4 share, all models, coloured by modality (exists per modality in
`results/{speech,text}/compare/gain_vs_concentration.png`; needs one combined version).

---

## Tier 2: strong support (main text)

### 2.1 Replication across image seeds (ADJSCC-Q)
Hand-tiered 25/50/25, paired gain vs uniform at 40% (`published_results/gpu/multiseed/*/test_sweep.md`):

| Seed | clean | uniform @40 | LOO | energy | attention | gain @30 (LOO) |
|---|---|---|---|---|---|---|
| 42 (primary) | 30.88 | 20.73 | +2.86 | +2.92 | +0.74 | −0.95 |
| 100 | 31.34 | 20.77 | +2.83 | +2.76 | +0.54 | −1.52 |
| 13 | 31.76 | 20.64 | +2.90 | +3.23 | −0.33 | −1.55 |
| 21 | 31.09 | 20.79 | +3.11 | +2.07 | −0.05 | −1.09 |
| 7 | 31.45 | 21.02 | +2.35 | +2.59 | +0.42 | −1.82 |

Peak (best ranking) +2.6…+3.2 dB at 40%; penalty −0.9…−1.8 dB at 20–30%. Optimal truncation per model
(`paper/generated_tables.tex`, PSNR at 40%): LOO 25.04–27.25, energy 25.27–26.72, attention
20.78–25.72, random 22.13–22.70 vs uniform 20.64–21.02.

### 2.2 Replication without attention, images (DeepJSCC-Q, `results/g1/deepjsccq/seed*/test_sweep`)

| Seed | clean | uniform @40 | no RS @10 | LOO (25/50/25) | energy | head | random | LOO @30 |
|---|---|---|---|---|---|---|---|---|
| 42 | 32.38 | 19.00 | 23.97 | +2.11 | +2.05 | +2.28 | +0.62 | −3.82 |
| 100 | 31.54 | 18.34 | 23.16 | +2.05 | +1.77 | – | +0.56 | −3.67 |
| 13 | 32.40 | 18.96 | 23.94 | +2.43 | +2.54 | – | +0.64 | −2.93 |
| 7 | 31.66 | 18.58 | 23.51 | +2.76 | +2.78 | – | +0.62 | −1.96 |

The low-loss penalty of fixed tiering is larger without attention (−2 to −4 dB at 30%).

### 2.3 Cheap rankings: proxies, a learned head, and a transferable table
Within-sample Spearman with LOO damage (validation; top-4 overlap in brackets):

| Proxy | Image ADJSCC-Q | Image DeepJSCC-Q | Speech ADJSCC-Q-1D | Speech DeepJSCC-Q-1D | Text DeepJSCC-Q-text |
|---|---|---|---|---|---|
| static train table | +0.89 (0.88) | +0.74 (0.71) | +0.42 (0.55) | +0.86 (0.82) | **+0.77 (0.65)** |
| energy ‖z_c‖² | +0.84 (0.67) | +0.84 (0.67) | **+0.87 (0.77)** | **+0.94 (0.78)** | +0.42 (0.49) |
| L1 | +0.84 (0.68) | +0.81 (0.66) | +0.75 (0.69) | +0.91 (0.77) | +0.43 (0.49) |
| Taylor | +0.63 (0.64) | +0.47 (0.56) | +0.34 (0.47) | +0.53 (0.50) | +0.05 (0.30) |
| variance | +0.44 (0.46) | +0.35 (0.43) | +0.49 (0.48) | +0.43 (0.38) | +0.42 (0.48) |
| random | 0.00 (0.25) | 0.00 (0.25) | 0.00 (0.25) | 0.00 (0.25) | −0.01 (0.25) |
| attention | −0.015 (0.23) | – | −0.22 (0.14) | – | (−0.12, non-conv. model) |
| **2,048-MAC head** | +0.95 (**0.92**) | +0.92 (0.88) | +0.64 (0.68) | +0.90 (**0.91**) | +0.77 (0.66) |
| head regret (dB / pp) | 0.21 | 0.34 | 0.71 | 0.14 | 3.12 |
| static regret | 0.60 | 2.30 | 1.41 | 0.48 | 3.13 |
| random regret | 15.87 | 12.65 | 8.43 | 16.17 | 18.16 |

Sources: `published_results/gpu/phase1/{saliency,head}`, `results/g1/deepjsccq/seed42/{saliency,head}`,
`results/speech/*/seed42/{saliency,head}`, `results/text/deepjsccq_text/seed42/{saliency,head}`.
Head cost: 2,048 MACs = 0.039% (image) / 0.024% (speech) of the encoder.
- **Transfer:** the CIFAR-10 ranking on CIFAR-100: Spearman **+0.997**, Kendall 0.983, top-4 overlap
  1.00 → hard-code the table, **0 B side information** (`published_results/gpu/phase1/transfer`).
- **Finding:** energy is the best cheap proxy for images and speech, but **fails on converged text**
  (+0.42), where only the static table works and the learned head adds nothing over it (0.657 vs 0.657).

### 2.4 Nested-dropout ordered models (images)
(`paper/generated_numbers.tex`, Ordered*): clean cost **0.24 dB** (30.64 dB). Truncation in index order
holds 30.64 / 30.63 / 30.62 / **30.60** / 30.45 / 30.26 dB at 20/30/35/40/45/50% loss. On the same model,
uniform RS: 30.63 / 27.84 / 22.46 / **17.96** / 16.12 / 15.47; random-order truncation 23.09 dB at 40%.
DeepJSCC-Q ordered: clean 31.63, truncation **31.32 dB at 40%**, 30.42 at 50%. Last five channels of the
ordered ADJSCC-Q carry ≤ 0.02 dB each.

### 2.5 Smaller dedicated models (images)
With the same 96 packets, the 8-channel model (k/n 1/12) behind RS(96,32) gives **30.06 dB at every
loss rate up to 50%**; the 6-channel model behind RS(96,24) gives 28.28 dB flat. Switching between such
models dominates truncating an unordered model; the ordered model is above the 8-channel model at every
loss rate.

### 2.6 Conventional codecs with RS (images): honest baseline
`published_results/gpu/final/digital/digital.md` (fixed RS(96,64)) and macros (rate-adaptive).

| Loss | WebP fixed | JPEG fixed | J2K fixed | WebP adaptive | JPEG adaptive | J2K adaptive | JSCC uniform | JSCC best (trunc./selector) |
|---|---|---|---|---|---|---|---|---|
| 0 | 38.14 | 36.76 | 32.91 | 38.14 | 36.76 | 32.91 | 30.88 | 30.88 |
| 0.30 | 32.88 | 31.48 | 28.60 | 37.73 | 35.08 | 30.96 | 28.67 | 29.47 |
| 0.35 | 23.04 | 21.64 | 20.57 | 37.28 | 33.52 | 29.72 | 24.40 | 28.54 |
| 0.40 | 15.32 | 14.06 | 14.36 | **36.84** | 32.98 | 28.55 | 20.73 | 27.25 |
| 0.50 | 12.52 | 11.75 | 12.33 | 35.35 | 30.39 | 26.01 | 18.31 | 24.66 |

Codecs without RS collapse to 9.8–12.9 dB at 10% loss. With a **fixed** code, JSCC tiers win from 35%
(25.72 vs 20.6–23.0 dB). With the **same rate adaptation** the JSCC gets, WebP stays ahead everywhere.
State this plainly: the paper is about protecting a learned latent, not JSCC vs separation.

### 2.7 Spending the whole budget on latent bytes without RS
24-channel (k/n 1/4, `kn14`) ADJSCC-Q: none of 3 runs converged (best clean val 27.83 dB; after
erasure fine-tuning 27.92 clean, 24.07 dB at 40%, macros NoRsJscc*). Within DeepJSCC-Q (macros
NoRsDeep*, RsDeep*): no-RS 24 ch., erasure-fine-tuned: 30.00 clean, 25.51 / **24.36** / 23.18 dB at
30/40/50%; RS + LOO truncation, 16 ch.: 32.17 clean, 30.13 / **26.03** / 22.71; same after fine-tuning:
29.31 clean, 28.61 / **27.05** / 24.91. RS + truncation wins up to 45%; at 50% the fine-tuned no-RS model
passes truncation of the plain model but not of the fine-tuned one.

### 2.8 Bursty losses need interleaved tiers (images)
Gilbert–Elliott, 1% loss in good state, 85% in bad (`published_results/gpu/final/burst`).

| Avg. loss | Burst | 25/50/25 in order | 25/50/25 round-robin | 25/25/50 in order | 25/25/50 rr | no RS |
|---|---|---|---|---|---|---|
| 35% | 1 | +1.31 | +1.31 | +0.52 | +0.51 | −4.04 |
| 35% | 4 | +0.46 | +1.17 | −0.23 | +0.48 | −4.28 |
| 35% | 16 | **−0.56** | **+0.80** | −1.07 | +0.55 | −3.70 |
| 45% | 1 | +2.69 | +2.70 | +2.81 | +2.80 | −0.13 |
| 45% | 4 | +2.13 | +2.45 | +2.06 | +2.41 | −0.70 |
| 45% | 16 | +0.42 | +1.32 | +0.11 | +1.13 | −2.13 |

LOO truncation under bursts (45% avg.): **+6.65 dB** (burst 1), **+2.05 dB** (burst 16); burst-tuned
depth adds ≤ 0.28 dB. Original target (> 3 dB at burst ≥ 4 for hand tiers): not met.

### 2.9 Loss-rate mismatch
A truncation designed for 40% gives up **2.59 dB** on a clean channel and gains +1.88 dB at 50%. Design
for 35%: −1.59 dB clean, +5.87 at 40%. A robust allocation optimized over p ∈ [0.1, 0.5]: grouped
−2.47 dB at 10%, +5.43 at 40%; PET −2.49 / +5.52. Only regime where a multi-level structure is selected.
Source: `coding_controls_test.md` (design0.x, robust_*), `paper/figures/fig_mismatch.pdf`.

---

## Tier 3: context and robustness (short in main text, details in appendix)

### 3.1 Coding controls that isolate the mechanism (images, s42, at 40%)
- Unsorted two tiers, two RS(48,32) at the uniform rate (block-length control): **−0.05 dB** at 40%,
  −1.69 at 30%. Shorter blocks alone do not help.
- Uniform PET with diagonal layout: +1.18 dB at 40% (+0.28 at 30%).
- PET twin of 25/50/25 (and diagonal variant): +2.78 / +2.89 dB, about the hand-tiered value.
- Per-image LOO order (unattainable upper bound for a ranking): +3.08 dB vs +2.86 static.
- Grad-FEC-style drop-and-protect: top8/drop4 +4.52 at 40% but −3.80 dB clean; top4/drop4 +1.32;
  top4/drop8 +0.17.

### 3.2 Kodak (CIFAR model on 768×512, `published_results/gpu/phase3/kodak/kodak.md`)
24 images × 5 seeds, packet size 128 B, clean 24.31 dB (model trained on 32×32, so relative only).
25/50/25 LOO **+1.43 dB** at 40%, peak +1.46 at 45% (CI ±0.15); attention +0.27 at 40%; mean ≥ 35%:
LOO +1.14 vs attention +0.14 dB (12%). **No low-loss penalty** for the best scheme (≤ 0.05 dB at all
rates: bigger blocks). 5th-percentile PSNR at 40%: 20.06 vs 18.93 dB.

### 3.3 Erasure-aware training (Track B, `published_results/gpu/phase2`)

| Model | clean | worst gain (low loss) | peak gain | break-even | uniform @40 | best tier @40 |
|---|---|---|---|---|---|---|
| base | 30.88 | −0.87 | +3.00 | 0.32 | 20.73 | 23.72 |
| channel-drop fine-tune | 29.51 (−1.37) | −0.73 | +2.51 | 0.32 | 21.84 | 24.33 |
| packet-drop fine-tune | 29.50 (−1.38) | −0.64 | +1.17 | 0.34 | 23.39 | 24.51 |
| inpainter | 30.31 (−0.59) | −0.41 | +1.22 | 0.32 | 25.09 | 26.26 |

Robust training lifts uniform RS more than UEP; the margin shrinks. Target (≥ 2.5 dB at 20% loss): not met.
Energy order beats LOO order after channel-drop fine-tuning (+2.49 vs +1.46): the training-set LOO
table goes stale when the model changes.

### 3.4 Bandwidth ratio (`published_results/gpu/phase3/kn_*`)
| k/n | channels | clean | uniform @40 | 25/50/25 LOO @40 | best LOO tier @40 | LOO @30 |
|---|---|---|---|---|---|---|
| 1/3 | 32 | 31.65 | 22.14 | +2.51 | +2.51 | −1.69 |
| 1/6 (primary) | 16 | 30.88 | 20.73 | +2.86 | +2.86 | −0.95 |
| 1/12 | 8 | 30.06 | 20.01 | +1.49 | +1.49 | −1.74 |
| 1/16 | 6 | 28.28 | 19.93 | +1.00 | +1.00 | −0.85 |
Gain is positive at every ratio in the high-loss region; largest at 1/6.

### 3.5 Speech: what the gain looks like per seed, and the penalty
Hand-tiered 25/50/25, SNR (dB), paired gain vs uniform:

| Model | uniform @30 | LOO @30 | uniform @35 | LOO @35 | uniform @40 | LOO @40 | random @40 | attention @40 | no RS @10 |
|---|---|---|---|---|---|---|---|---|---|
| ADJSCC-Q-1D s42 | 5.38 | −0.77 | 2.83 | +0.83 | 0.59 | +2.01 | +0.84 | +0.37 | 4.29 |
| ADJSCC-Q-1D s100 | 5.14 | −0.87 | 2.67 | +0.64 | 0.51 | +1.76 | +0.77 | +0.39 | 4.06 |
| ADJSCC-Q-1D s7 | 5.44 | −0.94 | 3.05 | +0.48 | 0.96 | +1.52 | +0.80 | +0.88 | 4.34 |
| DeepJSCC-Q-1D s42 | 4.21 | −0.74 | −0.15 | +1.67 | −3.73 | +3.24 | +0.53 | – | 0.23 |
| DeepJSCC-Q-1D s7 | 4.44 | −0.82 | 0.63 | +1.41 | −2.51 | +2.90 | +0.66 | – | 1.40 |
| DeepJSCC-Q-1D s13 | 4.59 | −1.01 | 0.93 | +1.17 | −2.10 | +2.64 | +0.71 | – | 1.79 |

Validation selected 25/50/25 or 25/25/50 for loss ≥ 35% on every speech model (`val_sweep/selected_schemes.json`).

### 3.6 Speech SI-SDR (500 test segments, seed 0, `results/speech/*/seed42/perceptual/perceptual.md`)
ADJSCC-Q-1D s42, SI-SDR (dB): clean 5.34; at 35% uniform 0.23 vs LOO tiers 0.81 vs energy tiers 1.22;
at 40% −3.04 vs −1.03 vs −0.56; attention-tiered (two-tier 75/25) −1.81. DeepJSCC-Q-1D s42: clean 5.01;
at 40% uniform −11.15 vs LOO −6.92 vs energy −6.71. SI-SDR moves in the same direction as SNR.

### 3.7 Attention models degrade more gracefully *without* any code (cross-modal observation)
No-RS quality at 10% loss relative to clean: image ADJSCC-Q 25.80/30.88 dB vs DeepJSCC-Q 23.16–23.97/
31.5–32.4; speech ADJSCC-Q-1D 4.06–4.34/6.4–6.7 vs DeepJSCC-Q-1D 0.23–1.79/6.5. The attention modules
buy erasure robustness of the raw latent even though they do not identify important channels. Worth a
paragraph: it explains why DeepJSCC-Q models show larger UEP gains and larger low-loss penalties.

### 3.8 Text qualitative examples
`results/text/deepjsccq_text/seed42/examples/` (500 windows, seed 0): clean char. acc. 69.36%, word acc.
32.22%, 1.347 bits/char; at 40% loss uniform and no RS decode identically garbled text; LOO- and
energy-tiered outputs are differently garbled. Good as a short qualitative table that makes G8 visible.

### 3.9 Tail behaviour (images)
5th-percentile PSNR at 40%: 18.74 dB (25/50/25 head order) vs 16.66 dB (uniform); at 50%: 15.90 vs
15.40. Std over channel seeds < 0.3 dB everywhere. Uniform's cliff: −4.27 dB between 30% and 35%.

---

## Tier 4: appendix / supplementary only
- Full per-seed sweeps for every model and modality, all schemes (two_tier_25_75, two_tier_50_50,
  two_tier_75_25, three_tier_25_25_50, three_tier_50_25_25): `*/test_sweep/test_sweep.md`.
- Per-model figures: `test_sweep_{psnr_curves,psnr_p5_curves,gain_vs_uniform,gain_heatmap,block_failure,psnr_cdf_r0.4}.png`.
- Validation sweeps and scheme selection plots: `*/val_sweep/scheme_selection_*.png`, `selected_schemes.json`.
- Head diagnostics: `head/{training_loss,val_top4_overlap,top4_selection_frequency,predicted_vs_true,protection_regret_comparison}.png`.
- Saliency diagnostics: `saliency/{within_image_spearman,top4_overlap}.png`; image saliency sweep
  `published_results/gpu/phase1/saliency_sweep`; energy validation sweep `phase1/val_sweep_energy`.
- Multi-seed diagnostics: `multiseed/{aligned_spearman,profile_pearson,damage_bars}.png`.
- Robust-model validation sweeps (`phase2/*/val_sweep`), bandwidth-ratio validation sweeps (`phase3/kn_*/val_sweep`).
- Per-image result arrays (`*.per_image.npz`): source for visual-example figures and CDFs.
- AWGN sanity check of unquantized ADJSCC (22.01 / 25.23 / 27.85 / 29.32 / 29.92 dB at 0–20 dB SNR):
  one sentence in the setup, values in an appendix table.
- Quantizer facts: 31.04 → 30.53 dB on the first model, 179/256 levels used, σ_q 1.0 → 0.05.
- Interleaving sanity: consecutive layout fails 81% of codewords at 20% loss vs 0.07% interleaved.

## Tier 5: do not use as is
| Item | Why | Source |
|---|---|---|
| ADJSCC-Q image seed 2024 | Not converged (clean 26.52 dB); excluded by the pre-fixed rule | `published_results/gpu/multiseed/seed2024` |
| DeepJSCC-Q-1D seed 100 | Not converged (best epoch 37) | `results/speech/deepjsccq1d/seed100` |
| ADJSCC-Q-text seeds 42/100/7 | Not converged (best epoch 14–20; clean 42.6–44.0%) | `results/text/adjsccq_text` |
| DeepJSCC-Q-text seed 100 | Not converged (clean 43.8%) | `results/text/deepjsccq_text/seed100` |
| Text proxy numbers from ADJSCC-Q-text | Non-converged model; contradict the converged one (energy +0.80 vs +0.42) | `results/text/adjsccq_text/seed42/saliency` |
| `results/eval/rs_uep_sweep.*`, `rs_uep_oracle_sweep.*` | Pre-protocol sweeps of the first model (clean 30.50 dB), no train/val/test discipline; superseded by `published_results/gpu/final` | `results/eval` |
| `results/train_split_adjsccq/*` | Early split-training sweep, superseded | |
| First attention-UEP sweep (19.35 vs random 19.45 dB at 50%) | Pre-protocol; superseded by 1.2/1.3 (same conclusion) | slides, archive |
| Smoke runs | Tiny, for pipeline checks | `results/*/smoke_*` |
| PESQ-WB / STOI | Not computed (empty columns) | perceptual.md |
| SSIM | Zero-padded windows | all image sweeps |
| 24-channel ADJSCC-Q no-RS | Never converged; only usable as a footnote | `published_results/nors*` |
| Robust no-RS fine-tune deepjsccq_kn16_seed7 | Clean collapsed −2.84 dB (over-regularised) | `published_results/nors2` |
