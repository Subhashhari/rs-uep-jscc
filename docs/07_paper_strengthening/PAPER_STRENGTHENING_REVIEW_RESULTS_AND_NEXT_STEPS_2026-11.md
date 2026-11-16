# Paper strengthening (branch `paper-strengthening`, 2026-11-16/17): review, new results, next steps

This document records a pre-submission review of the project, what was changed and run in response, what
the new results say, and what the authors still need to decide. To continue the work (running jobs,
resuming queues, finishing the paper), see [`HANDOFF_2026-11-16.md`](HANDOFF_2026-11-16.md). Every number below comes from a result
file in `results/coding/` (local, git-ignored; small copies in `published_results/coding/`) and is
regenerated into the paper by `python -m experiments.paper_figures`.

## 1. Verdict in one paragraph

Before this branch, the paper rested on a hand-picked three-tier RS scheme that gained about +3 dB at 40%
loss and lost about 1 dB below 32% loss. It also rested on a claim that Deep JSCC beats JPEG/WebP + RS at
high loss. A reviewer from the coding or JSCC community would have rejected both. The three-tier scheme
is far from optimal. Under the same budget, the validation-optimised allocation gains **+6.52 dB** at 40%
loss and has **no low-loss penalty**. The digital comparison was a straw man: the codecs were held to a
fixed RS(96,64) that collapses by construction, and with the same rate-adaptation freedom WebP stays at
**36.8 dB** at 40% loss. The defensible paper is different and stronger than the planned one. Its subject
is how a learned latent should be protected by packet-level FEC, and its answer is that importance-ordered
truncation with one strong code is optimal at a known loss rate. That makes the importance ranking
decisive: random order gives +1.58 dB, attention +4.80 dB, energy +6.00 dB, the 2,048-MAC head +6.37 dB
and LOO +6.52 dB.

## 2. What a GLOBECOM reviewer would have objected to, and what was done

| # | Objection | Status before | Done on this branch | Outcome |
|---|---|---|---|---|
| 1 | "Tiered RS over packets is PET/ULP (1996/2000)" | Not addressed | PET layouts and PET twins (`coding/outcome.py`), PET in the optimiser | PET twin of 25/50/25: +2.78 dB vs +2.86 grouped; optimised PET within 0.25 dB of optimised grouped |
| 2 | "Is the hand-picked allocation any good?" | 7 hand-made candidates | Exact DP on a closed-form surrogate + exhaustive multi-tier check + simulated local search on validation (`experiments/allocation.py`, `coding_controls.py`) | No: optimum is truncation, +6.52 vs +2.86 dB at 40% |
| 3 | "The low-loss penalty makes UEP useless below 32%" | Real: -0.9 to -1.8 dB | Loss-aware selector (validation-chosen per rate) | Penalty gone (selector = uniform RS up to 20%) |
| 4 | "Is the gain block length, tiering, or importance?" | Partly (random +0.50) | Unsorted two-tier control, random tiers, per-image LOO upper bound | Block length alone: -0.05 dB at 40%; ranking is everything |
| 5 | "Digital baseline unfair" | Fixed RS(96,64) | Rate-adaptive JPEG/JPEG2000/WebP + RS, k chosen on validation (`eval_digital_adaptive.py`) | Digital wins at every loss rate on CIFAR-10. **The paper must not claim JSCC beats separation.** |
| 6 | "Why RS at all? Train JSCC over erasures" | Not run | 24-channel (1,536-byte) model, no RS, erasure fine-tuned; best of 3 runs by validation (`nors2_*` Kaggle jobs) | *pending; filled in Section 4.4* |
| 7 | "Attention artefact? (G1 ran on a Mac, ADJSCC-Q on T4)" | Hardware confound | DeepJSCC-Q retrained on Kaggle T4, 5 seeds | 3/5 converged (seeds 42, 13 diverged); concentration persists without attention |
| 8 | "Why not train an ordered latent (nested dropout)?" | Not run | `--tail_drop` option; ordered ADJSCC-Q/DeepJSCC-Q trained | *pending; Section 4.5* |
| 9 | "Why not a smaller model + strong code?" | Not asked | Truncation evaluator on the k/n = 1/12 and 1/16 models | **8-channel model + RS(96,32): 30.06 dB at every loss up to 50%**, which beats truncating one model |
| 10 | "Error bars cover channel randomness only" | True | Image bootstrap of every gain + multi-seed table | Seed CI and image CI both about +-0.02-0.06 dB |
| 11 | "Oracle" naming | Static table called oracle | Paper says "static LOO ranking (training split)"; per-image LOO reported as an upper bound | -- |
| 12 | Report text took the best method per rate on test, with a wrong "block-length" explanation | Present | `reporting.py` / `make_report.py` text corrected; paper numbers use validation selection only | -- |
| 13 | G1 report errors (head architecture, train+val, RS capacity) | Present | Corrected in the G1 results document | -- |
| 14 | "Removing attention improved training stability" (G1 report) | Claimed from Mac runs | Same-hardware runs contradict it (3/5 vs 5/6) | Claim must be dropped |
| 15 | Anonymity (public repo + fork, W&B, title) | Open | New work kept off GitHub: Kaggle jobs read a **private** code dataset (`kaggle/upload_code.py`); branch not pushed | Authors must act, see Section 6 |

## 3. New tools (all tested; 268 unit tests pass)

* `coding/outcome.py`: exact receiver outcome for any systematic MDS layout (grouped tiers, dropped
  tiers, PET with column or diagonal placement), plus closed-form loss probabilities. It is verified bit
  for bit against real GF(256) RS decoding (`tests/test_outcome.py`). It replaces RS decoding in
  simulation, so a full test sweep that took 1.5-3 h per model on Kaggle CPUs now takes minutes, with
  identical numbers: the published seed-42 sweep is reproduced in all 56 overlapping cells with
  **max |difference| = 0.000 dB**.
* `experiments/allocation.py`: additive expected-MSE surrogate, exact DP optimum for grouped and PET
  layouts, exhaustive 2-3-tier enumeration, local search.
* `experiments/coding_controls.py`: validation optimisation (`--stage val`, `--stage multitier`) and the
  one-shot test evaluation (`--stage test`), with paired gains, seed CIs, image-bootstrap CIs and the
  reference check.
* `experiments/eval_truncation.py`: importance-ordered truncation for any model / channel count, with
  validation-chosen depth (used for multi-seed, DeepJSCC-Q, ordered, smaller and no-RS models).
* `experiments/eval_digital_adaptive.py`: rate-adaptive digital baselines on the same masks.
* `experiments/train_adjsccq_train_split.py --tail_drop`: nested-dropout ordered training.
* `experiments/paper_figures.py`: every figure, table and number macro of the paper from result files.
* `kaggle/upload_code.py`, `CODE_SOURCE = "dataset"`: Kaggle jobs without pushing to public GitHub.
  `kaggle/compile_paper` compiles the LaTeX on Kaggle (no local TeX).
* `experiments/queue_paper_evals.sh`: the detached CPU queue behind the multi-model table.

## 4. Results

### 4.1 Primary model (ADJSCC-Q seed 42), test split, 10,000 images x 5 channel seeds

Gain over uniform RS(96,64) in dB (paired, same losses). Allocations, truncation depths and the selector
were chosen on 5,000 validation images x 3 seeds.

| method | 0.2 | 0.3 | 0.35 | 0.4 | 0.45 | 0.5 |
|---|---|---|---|---|---|---|
| uniform RS(96,64), absolute PSNR | 30.88 | 28.67 | 24.40 | 20.73 | 19.07 | 18.31 |
| hand-tiered 25/50/25, LOO order (published scheme) | -1.19 | -0.95 | +1.31 | +2.86 | +2.69 | +1.89 |
| same, per-image LOO order (upper bound) | -1.06 | -0.77 | +1.52 | +3.08 | +2.90 | +2.05 |
| same, attention order | -2.77 | -3.10 | -0.93 | +0.74 | +0.88 | +0.55 |
| two RS(48,32), unsorted (block length only) | -0.14 | -1.69 | -1.00 | -0.05 | +0.13 | +0.04 |
| PET twin of 25/50/25 | -1.25 | -0.41 | +1.53 | +2.78 | +2.93 | +2.37 |
| uniform RS, diagonal placement (failure dispersal only) | 0.00 | +0.28 | +0.78 | +1.18 | +1.28 | +1.25 |
| Grad-FEC style: top 8 coded, 4 sent bare, 4 dropped | -4.80 | -3.03 | +1.04 | +4.52 | +5.97 | +6.35 |
| **optimised truncation, LOO order** | 0.00 | +0.80 | +4.12 | **+6.52** | +6.68 | +6.21 |
| optimised truncation, 2,048-MAC head | 0.00 | +0.92 | +3.92 | +6.37 | +6.57 | +6.40 |
| optimised truncation, energy | 0.00 | +0.90 | +3.74 | +6.00 | +6.27 | +5.90 |
| optimised truncation, attention | 0.00 | +0.80 | +4.12 | +4.80 | +1.92 | -0.19 |
| optimised truncation, random order | 0.00 | -2.02 | -0.26 | +1.58 | +1.77 | +1.05 |
| optimised grouped (multi-tier allowed) | 0.00 | +0.80 | +4.14 | +6.52 | +6.68 | +6.35 |
| optimised PET | -0.00 | +0.73 | +4.01 | +6.30 | +6.79 | +6.29 |
| selector (uniform / grouped / PET / truncation per rate) | -0.00 | +0.80 | +4.14 | +6.52 | +6.79 | +6.35 |
| one allocation for all p in [0.1, 0.5] (grouped) | -3.25 | -1.79 | +2.13 | +5.43 | +6.41 | +5.58 |

Readings:

1. **Truncation is the optimum.** The exhaustive check of the 25 surrogate-best two- and three-tier
   layouts per loss rate improves on truncation by at most 0.15 dB on validation (at 50% loss).
   Multi-level UEP is not where the gain is.
2. **The ranking decides.** With truncation, LOO, the head and energy are within 0.5 dB of each other,
   attention collapses beyond 40% loss, and random order is no better than the hand-tiered scheme.
   Proposition 1 in the paper gives the closed-form condition.
3. **Placement matters on failure.** Spreading uniform RS's failure losses diagonally over channels
   (no ranking, no side information) gains +1.2 dB at 40% on its own.
4. **Mismatch is expensive.** A design for 40% loss costs 2.6 dB on a clean channel. One design for all
   rates costs 3.3 dB at 20%. Loss-rate feedback (one byte per change) is assumed for the selector.
5. **The surrogate works.** It predicts simulated MSE with Spearman 0.994 on validation and 0.99+ on test.
   It underestimates high distortion (mild superadditivity).

### 4.2 Digital baselines with the same freedom (test split)

| loss | WebP + fixed RS(96,64) | WebP + adaptive RS (k chosen on val) | JPEG adaptive | JPEG2000 adaptive | best JSCC (selector) |
|---|---|---|---|---|---|
| 0.0 | 38.14 | 38.14 | 36.76 | 32.91 | 30.88 |
| 0.3 | 32.88 | 37.73 | 35.08 | 30.96 | 29.47 |
| 0.4 | 15.32 | 36.84 | 32.98 | 28.55 | 27.25 |
| 0.5 | 12.52 | 35.35 | 30.39 | 26.01 | 24.66 |

The byte-quantised JSCC latent has no entropy coding and spends 1 byte per latent value (8 bits per
pixel), so on CIFAR-10 it is about 7 dB behind WebP at equal bytes. **Recommendation:** state this
plainly in the paper and position the work as protecting a learned latent that is the given transmitted
representation (digital semantic communication, split inference, neural codecs). Do not claim JSCC beats
separation.

### 4.3 Smaller models (model switching) vs truncating one model

| model (same 96 packets) | clean | 0.3 | 0.4 | 0.5 |
|---|---|---|---|---|
| 16-channel ADJSCC-Q, optimised truncation | 30.88 | 29.47 | 27.25 | 24.52 |
| 8-channel ADJSCC-Q (k/n = 1/12) + RS(96,32) | 30.06 | 30.06 | 30.06 | 30.06 |
| 6-channel ADJSCC-Q (k/n = 1/16) + RS(96,24) | 28.28 | 28.28 | 28.28 | 28.28 |

The JSCC rate-distortion curve is flat (half the latent costs 0.8 dB), so spending the budget on code
strength wins. This is the strongest reviewer question for the paper. The honest framing: truncation is
the single-model approximation of model switching, it needs a good ranking, and ordered training
(Section 4.5) is the way to close the gap.

### 4.4 No RS at all: 1,536-byte JSCC trained over packet erasures

*Pending (Kaggle `nors2_adjsccq` / `nors2_deepjsccq`). The first 24-channel runs diverged under recipe v1
(best epoch 18, 26.4 dB), so the baseline is retrained as the best of three runs by validation PSNR before
erasure fine-tuning.*

### 4.5 Ordered (tail-drop) training

Ordered models converged (ADJSCC-Q 30.64 dB, DeepJSCC-Q 31.63 dB clean test; 0.24 dB below the plain
ADJSCC-Q). *Truncation results pending (evaluation queue).*

### 4.6 Across seeds and architectures

DeepJSCC-Q on the same T4 hardware: seeds 100 / 7 / 21 converged (31.79 / 32.17 / 32.73 dB test). Seeds
42 and 13 did not (best epochs 29 and 20). Top-4 share of LOO MSE damage: 66-84% (ADJSCC-Q, 5 seeds),
69-72% (DeepJSCC-Q, 3 seeds).

Test PSNR (dB) at 40% loss. Each model uses its own ranking and a truncation depth chosen on validation
(`paper/generated_tables.tex`, `results/coding/trunc/*/truncation.json`):

| model | clean | uniform | hand-tiered (LOO) | trunc. LOO | trunc. energy | trunc. attention | trunc. random |
|---|---|---|---|---|---|---|---|
| ADJSCC-Q s100 | 31.34 | 20.77 | 23.60 | 25.77 | 25.75 | 23.15 | 22.28 |
| ADJSCC-Q s13 | 31.76 | 20.64 | 23.54 | 26.18 | 26.36 | 22.41 | 22.13 |
| ADJSCC-Q s21 | 31.09 | 20.79 | 23.90 | 26.14 | 25.27 | 20.78 | 22.24 |
| ADJSCC-Q s42 | 30.88 | 20.73 | 23.59 | 27.25 | 26.72 | 25.72 | 22.42 |
| ADJSCC-Q s7 | 31.45 | 21.02 | 23.37 | 25.04 | 25.74 | 23.25 | 22.70 |
| DeepJSCC-Q s100 | 31.79 | 18.56 | 22.19 | 28.00 | 27.89 | -- | 20.54 |
| DeepJSCC-Q s21 | 32.73 | 19.52 | 22.70 | 25.63 | 26.03 | -- | 21.51 |
| DeepJSCC-Q s7 | 32.17 | 17.81 | 21.86 | 26.03 | 26.08 | -- | 19.64 |

* **The finding holds on every model.**
  * LOO truncation gains +4.0 to +6.5 dB over uniform for ADJSCC-Q and +6.1 to +9.5 dB for DeepJSCC-Q.
  * It beats the hand-tiered scheme by +1.7 to +5.8 dB.
* **Seed 42 is the most favourable ADJSCC-Q seed.** The abstract now quotes the cross-model range.
* **Energy order is a near-free substitute.** It is within 0.9 dB of LOO on every model, and better on 4 of 8.
* **Attention order is unreliable.** On seed 21 it is worse than random order.

## 5. Recommended paper

* **Working title (anonymous, differs from the README):** "Which Latent Bytes Deserve Parity? Erasure
  Sensitivity and Packet-Level FEC for Quantized Deep JSCC". The draft is in `paper/main.tex`; numbers come
  from `paper/generated_numbers.tex`.
* **Contributions, in order:** (1) measured erasure sensitivity: concentrated, seed-stable, present without
  attention, transferable; (2) attention gates do not predict it while energy and a 2,048-MAC head do;
  (3) exact outcome lemma, closed-form surrogate and DP-optimal allocation; (4) the optimum is
  importance-ordered truncation, and multi-level UEP adds at most about 0.15 dB at a known loss rate;
  (5) honest baselines: PET, Grad-FEC style, block-length control, model switching, rate-adaptive codecs.
* **Drop from the conference paper:** speech (S1) and text (T1). They are unrun, or run on another
  platform, and dilute the message. Also drop Kodak with a CIFAR-trained model and the erasure-aware
  decoder track (its peak-gain trade-off is superseded by truncation).

## 6. What the authors must do or decide

1. **Anonymity (blocking for double-blind).** The public repository and its public fork carry the
   project. Ask the fork owner to delete or privatise the fork, make the repository private for the review
   window, provide code through an anonymised mirror, and keep the W&B project private. This branch was
   pushed to the authors' GitHub fork on request (2026-11-16) so that others can continue. It must be
   included in that privatisation step.
2. **Venue and deadline.** Confirm the GLOBECOM 2027 CFP (dates and double-blind policy were not
   findable online on 2026-11-16).
3. **Positioning decision.** Accept the reframing in Section 5, or invest in a JSCC model that is
   competitive with codecs (entropy-coded latents or a higher-resolution model) before submission.
4. **Citations marked CHECK** in `paper/references.bib` need verification against publisher pages.
5. **Compile and proofread** the draft (`kaggle/compile_paper` builds it on Kaggle; Overleaf works too).

## 7. Reproduce

```bash
# primary model: optimise on validation, then test once (about 4 h + 30 min on 16 CPU cores)
python -m experiments.coding_controls --stage val  --checkpoint results/gpu/models/seed42/best_val.pth \
    --oracle_ranking_file results/gpu/models/seed42/oracle_ranking.json --hill_evals 40 --output_dir results/coding/seed42
python -m experiments.coding_controls --stage multitier --checkpoint ... --oracle_ranking_file ... --output_dir results/coding/seed42
python -m experiments.coding_controls --stage test --checkpoint ... --oracle_ranking_file ... \
    --head_checkpoint results/gpu/phase1/head/sensitivity_head.pt --reference_json results/gpu/final/final_test.json \
    --save_per_image --output_dir results/coding/seed42
python -m experiments.eval_digital_adaptive --split val  --output_dir results/coding/digital
python -m experiments.eval_digital_adaptive --split test --selection results/coding/digital/digital_adaptive_val.json --output_dir results/coding/digital
bash experiments/queue_paper_evals.sh          # truncation for every other model
python -m experiments.paper_figures            # figures, tables, number macros
```
