# The paper, as a story

**What this file is.** Everything we will write in the paper, in the order the paper presents it. Each
section says what the reader must learn there, what we did, what we got and where the number comes from,
and how the section hands over to the next one. Read it top to bottom and you have read the paper.

**Model for the story.** Bourtsoulatze, Kurka and Gündüz, *Deep Joint Source-Channel Coding for Wireless
Image Transmission* (2019), the PDF in `docs/06_literature_review/reference_papers/`. Their arc: the
separation theorem is optimal only in the limit; practical systems fall off a cliff; a learned joint code
avoids the cliff; then each experiment answers the next obvious question ("We start by…", "More
interestingly…"), then larger images and visual examples, then complexity, then a conclusion that
recaps and looks ahead. We follow the same arc. Their Section II, "Background and Problem
Formulation", explains the conventional pipeline and its cliff before the method; we do the same.

**Status marks.** ✅ checked against the result file named next to it (24 Nov 2026). ⚠️ needs an action
before submission. All image numbers are on the CIFAR-10 test split (10,000 images × 5 channel seeds)
unless stated. Speech: LibriSpeech test, 4,000 segments × 5 channel seeds. Text: text8 test, 2,441
windows × 5 channel seeds. "Gain" always means the paired difference to equal protection (uniform
RS(96,64)) on the same lost packets.

---

## The story in one paragraph

Deep JSCC removed the cliff of separate source and channel coding: its quality falls slowly as the
channel gets worse. But many real links are packet networks. There the latent must travel as bytes, the
bytes need Reed–Solomon parity, and the parity brings the cliff back. With a fixed parity budget, an old
question returns: which bytes deserve the parity? The classical answer needs a known order of
importance, and a learned latent hides its order. We measure that order for image, speech and text
models that share one byte format. For images and speech it is strong, and the attention gates of the
network do not see it; simple statistics do. Once the order is known, the best use of the parity is not
many protection levels. It is to drop the few least important channels and protect the rest with one
strong code. That gains 6.5 dB at 40% packet loss on our main image model, and the order is almost the
whole gain. For text the order is flat, and the same measurement tells us to keep equal protection.

## The story in seven sentences (every section serves one of them)

1. Deep JSCC removed the cliff of separate coding, but packet networks bring it back.
2. To cross a packet network, a latent becomes bytes, and the bytes need Reed–Solomon parity.
3. With a fixed parity budget, a classical question returns: which bytes deserve the parity?
4. The classical answer needs a known order of importance; a learned latent hides its order.
5. We measure the order: it is strong for images and speech, and attention does not see it.
6. With the order, the best use of the parity is simple: drop the least important channels and protect
   the rest with one strong code.
7. The same measurement tells us when not to bother: for text the order is flat.

---

# Title

**Which Latent Bytes Need Parity? Importance-Aware Reed–Solomon Protection of Deep JSCC Latents for
Images, Speech and Text**

# Abstract (six beats, about 200 words)

1. **Context.** Deep JSCC degrades gracefully when the channel worsens.
2. **Tension.** Packet networks lose whole packets, so the latent must travel as bytes with packet-level
   RS parity, and the cliff returns.
3. **Question.** With a fixed parity budget, which latent bytes should get the parity?
4. **Method.** One byte format (16 channels × 64 bytes, 96 packets) for image, speech and text models,
   each with and without attention; we measure the damage when each latent channel is lost.
5. **Findings.** Four of 16 channels cause 45–53% of the damage for images and 38–48% for speech; text is
   almost flat (28–30%; 25% is perfectly flat). Attention does not find the important channels; energy
   and a static table do. The best design drops the least important channels and protects the rest with
   one strong code: +6.5 dB at 40% loss for images. For speech, ordered tiers give +1.5 to +3.4 dB. For
   text, equal protection stays best.
6. **Message.** Measure what "important" means before you protect it.

---

# I. Introduction

The introduction moves from a principle, to its practical limit, to a new setting where the limit
returns, to our question, to why the obvious answer is not enough, to what we did and found.

**P1. The promise of deep JSCC.** Shannon's separation theorem says that compression and error
correction can be designed apart without loss, but only for infinitely long blocks. Real systems pay for
the separation with the *cliff effect*: when the channel is worse than the code was designed for, the
decoder fails all at once, and when it is better, the quality does not improve. Deep JSCC replaces both
steps with one neural network that maps the source straight to channel symbols, and its quality falls
slowly as the channel worsens. Later work made it adapt to the SNR (ADJSCC, with attention modules) and
made it digital by quantizing the latent (DeepJSCC-Q).

**P2. Where the cliff comes back.** Most deep JSCC papers assume a noisy physical channel. Many real
links are different: an application hands bytes to the network, the network sends them in packets, and
congestion or interference removes whole packets. The receiver knows which packets are missing from
their sequence numbers, so a lost packet is an *erasure*, not an error. To use such a link, the latent
must become bytes, and the bytes need packet-level forward error correction. Reed–Solomon codes are the
natural choice because they are optimal for erasures. But an RS code has its own cliff. The graceful
behaviour that made deep JSCC attractive is lost again one layer up.

**P3. The question.** A fixed parity budget does not have to protect every byte equally. Some bytes can
get more protection than others. This is the old question of unequal error protection in a new form:
which latent bytes deserve the parity? For layered image and video codecs this question was answered
decades ago (priority encoding transmission, unequal loss protection). Those answers rely on one
property: the bit stream has a known order of importance, because it is built that way.

**P4. Why the old answer does not transfer, and the tempting shortcut.** A learned latent has no known
order. Training never asks the network to put the important information in a particular channel. Recent
work therefore takes importance from attention weights or saliency maps. The shortcut is attractive:
ADJSCC already computes one attention weight per channel for free. But nobody has checked whether these
weights say which channel hurts most when it is lost.

**P5. What we do.** We study the question with one byte format for three sources: images, speech and
text. Each model turns a sample into 16 channels of 64 one-byte values, and the same RS packetizer sends
them in 96 packets. For every source we train the model with and without attention modules, so every
experiment also tests whether attention matters. We erase one channel at a time, measure the damage, and
use that measurement to decide where the parity goes.

**P6. What we find, in the order the paper shows it.** (i) The damage is very unequal for images and
speech and almost equal for text. (ii) Attention does not find the important channels; simple statistics
of the latent do. (iii) Once the order is known, the best allocation is not many protection levels: it
drops the least important channels and protects the rest with one strong code. (iv) The order is almost
the whole gain; a random order gets little of it.

**P7. Contributions.**
1. A byte-level JSCC pipeline with importance-aware RS protection that works the same way for images,
   speech and text (Fig. 2).
2. A measurement of erasure sensitivity in three modalities, with and without attention.
3. Evidence that attention gates do not predict erasure damage, and cheap predictors that do.
4. An exact model of the RS receiver and the optimal parity allocation it leads to.
5. Criteria fixed before the test that tell when unequal protection pays, and one modality where it
   does not.

**P8. Road map.** One paragraph naming Sections II–VI.

> **Hand-over:** the reader now wants to know exactly how packets, RS codes and unequal protection work.

---

# II. Background and Problem Formulation

Like Section II of the Deep JSCC paper, this section explains the conventional tools and their limits
before our method, so the method reads as the natural answer.

## A. Packets, erasures and Reed–Solomon codes

**What to explain.** An RS(n, k) code adds n − k parity symbols to k data symbols. RS codes are
**MDS (maximum distance separable)**: *any* k of the n symbols rebuild the data. So RS(96,64) survives
any 32 lost symbols and fails at 33. Our codes are **systematic**: the data bytes are sent as they are,
so when decoding fails, the data bytes that did arrive are still usable. Over erasures the receiver
knows where the holes are, which is why it can fill up to n − k of them.

**Interleaving.** We place codewords so that each packet carries one symbol of every codeword. A lost
packet then costs every codeword exactly one symbol. Our first layout put each codeword in consecutive
packets; at 20% loss the chance that some codeword fails was 81%, against 0.07% interleaved.
✅ `archive/superseded_documentation_2026-09_to_2026-10/2026-09-27_phase4_status_…md`, table at line 182.

**The cliff, in our numbers.** Uniform RS(96,64) is lossless up to 20% loss, loses 2.2 dB at 30%, drops
4.27 dB between 30% and 35%, and reaches 20.73 dB at 40% (clean 30.88 dB). ✅ `published_results/gpu/report/headline.md`, `INSIGHTS.md`.

## B. Unequal protection: tiers and PET

**Grouped tiers** (what we tried first). The channels are sorted by importance and split into groups;
each group gets its own packets and its own code. Our hand design "25/50/25": the top 4 channels in
RS(32,16), the next 8 in RS(48,32), the last 4 with no parity; 96 packets in total.

**PET** (priority encoding transmission, Albanese et al. 1996), the classical alternative. Think of the
96 packets as rows of a grid with 16 byte columns. In PET each *column* is one RS code that runs through
all 96 packets, and important data sits in columns with fewer data symbols (more parity). Every class is
spread over every packet, and every code has full length 96. The PET version of our 25/50/25 scheme is
5 columns of RS(96,47), 8 of RS(96,63) and 3 of RS(96,95) (computed by `pet_twin`,
`coding/outcome.py:193`). Uniform RS(96,64) is itself a PET layout with every column at K = 64.

**Why both need an order.** Both put the strong protection on "the important data". Neither says which
data that is.

## C. Importance in learned latents

Grad-FEC ranks feature packets with Grad-CAM; ISFR uses the leave-one-out drop and imposes an order with
nested dropout; Kim et al. learn per-bit protection. In machine learning, attention weights often fail
to predict what happens when a feature is removed. ADJSCC's attention gate is the obvious free signal for
a JSCC latent, and it is the one we test.

## D. Problem formulation

The network (encoder, quantizer, decoder) is fixed. The budget is fixed: 96 packets of 16 bytes = 1,536
bytes per sample, i.e. 64 data packets + 32 parity packets for equal protection. We may choose two
things: the **order** of the channels and the **code layout** (how many packets and how much parity each
group gets). The goal is the best expected quality over the packet losses.

> **Hand-over:** to choose well we need four tools: a way to measure importance, a way to predict it
> cheaply, a way to compute what any layout does, and a way to pick the best layout.

---

# III. Importance-Aware Reed–Solomon Protection (the method)

Opens with the one architecture figure, as Section III of the Deep JSCC paper does.

**Fig. 2 (full page width): the pipeline.** Grey blocks are a standard quantized deep JSCC: source →
encoder → byte quantizer → … → RS decoder → decoder → output. Orange blocks are new: the **importance
sort** (fed by an offline measurement or an online predictor), the **parity allocator** (designed with
an exact simulator), and the ranking passed to the receiver (0 bytes with a static table). The attention
gate is drawn crossed out. The TikZ code is in `main_narrative.tex`.

## A. Models and the byte format

- **Sources** (Table I): CIFAR-10 images 32×32 (bandwidth ratio k/n = 1/6); LibriSpeech segments of
  1.024 s (8 kbit/s); text8 windows of 2,048 characters (4 bits per character). All three give the same
  latent: 16 channels × 64 bytes = 1,024 bytes. ✅ rate arithmetic: 1,024 B × 8 / 1.024 s = 8 kbit/s;
  1,024 B × 8 / 2,048 chars = 4 bits/char.
- **Two families per source:** ADJSCC-Q (attention module after every layer) and DeepJSCC-Q (same network,
  attention removed). Images use 2-D convolutions; speech and text use 1-D convolutions (text after a
  character embedding).
- **Quantizer:** 256 learned scalar levels, so one latent value = one byte = one RS symbol. Trained soft
  to hard (straight-through), temperature annealed from 1.0 to 0.05.
  The speech model uses 252 of 256 levels on the test split. ✅ `results/speech/deepjsccq1d/seed42/metrics.json`.
  ⚠️ The image numbers on the slides (0.5 dB quantization cost, 31.04 → 30.53 dB; 179/256 levels) come
  from an early model; recheck them on the final primary model before quoting.
- **Training:** Adam, learning rate 10⁻³, 60 epochs (✅ `metrics.json`, `recipe`); images and speech
  with MSE, text with cross-entropy (✅ text recipe; ⚠️ confirm the speech loss in the training code).
- **Sanity check:** unquantized ADJSCC on CIFAR-10 over AWGN gives 22.01 / 25.23 / 27.85 / 29.32 /
  29.92 dB at 0 / 5 / 10 / 15 / 20 dB SNR, in line with the ADJSCC paper.
  ✅ `archive/…/2026-10-16_project_chronology_report…md` (early run; one sentence in setup).

## B. Tool 1: measuring importance (leave-one-out damage)

We define importance by its effect. Erase one channel (set its 64 bytes to zero), decode, and record
the quality drop. Repeat for all 16 channels over the training split. The result is a damage profile
w₁…w₁₆ for each trained model; sorted, it is a **static table** that the decoder can store, so the
order needs no side information. This measurement is the reference for everything after.

Summary numbers per profile: the **top-4 share** (fraction of the total damage carried by the four
worst channels; 25% means flat) and the worst-channel damage.
⚠️ Two definitions exist: share of the dB drops (all `multiseed.md` files, used in this document) and
share of the MSE increase (GLOBECOM macros, 66–84%). Pick one for the whole paper.

## C. Tool 2: predicting importance cheaply

The measurement costs 16 decoder passes. Cheaper signals: the static table; per-sample channel
**energy**, ℓ1 norm, variance, Taylor saliency; a small learned **head** (two-layer network, 2,048
multiply-accumulates); and the **attention gate** of the bottleneck module, the shortcut that prior work
suggests. Each signal is scored against the true per-sample damage by (a) Spearman rank correlation
within a sample, (b) overlap of its top 4 with the true top 4 (0.25 by chance), (c) protection regret.

## D. Tool 3: the exact RS outcome

Because RS is MDS and systematic, a data byte is lost **if and only if** its packet is lost **and** its
codeword lost more than n − k symbols. So the set of lost bytes is a fixed function of which packets
were lost: no decoding is needed in simulation, and the simulation is exact.

**Lemma.** With independent losses at rate p, a data byte of an RS(n, k) codeword is lost with
probability q(n, k, p) = p · Pr[Bin(n − 1, p) ≥ n − k].
(First factor: its own packet is lost. Second: too many others are lost for the code to recover it.)

Worked values (✅ computed from the formula):

| Code | Used for | p = 20% | p = 30% | p = 40% |
|---|---|---|---|---|
| RS(96,64) | equal protection | 0.0002 | 0.075 | 0.37 |
| RS(32,16) | top tier, hand design | 0.000 | 0.003 | 0.05 |
| RS(48,32) | middle tier, hand design | 0.003 | 0.10 | 0.33 |
| RS(96,52) | truncation to 13 channels | 0.000 | 0.0002 | 0.05 |

The simulator reproduces the RS-decoded sweep of the primary model to 0.000 dB on 56 cells.
✅ `paper/generated_numbers.tex` (ReferenceMaxDiff, ReferenceCells).

## E. Tool 4: choosing the layout, and truncation

Combine Tool 1 and Tool 3: the expected damage of a layout ≈ Σ (weight of each byte × its loss
probability) + damage of the channels not sent. Dynamic programming finds the layout that minimises
this sum for 96 packets; the exact simulator then re-checks the best candidates on validation data and
refines them by local search. The additive sum predicts the simulated MSE with Spearman 0.994 on
validation and 0.997 on test (median relative error 7.3% and 5.4%). ✅ `published_results/coding/seed42/allocations.json`
(`surrogate_fidelity`), `paper/generated_numbers.tex`.

**Truncation** is the extreme layout: send only the top m channels in one RS(96, 4m) code, and do not
send the other 16 − m. With m = 16 it is plain equal protection. Code: `truncation_layout`,
`experiments/coding_controls.py:168`; per-model evaluation: `experiments/eval_truncation.py`.

**Proposition.** Truncation beats equal protection if the damage of the channels left out is smaller
than the protection that their freed packets buy for the channels kept. The left side is small only if
the dropped channels really are the unimportant ones. So, before any experiment, the method predicts
that **truncation works only with a correct order**.

> **Hand-over:** we have the tools. Now we test them, one question at a time, starting with images.

---

# IV. Evaluation

Images are the main test bed: most models, all baselines. Speech and text then show how far the story
goes. Each subsection answers one question, and its answer raises the next.

## A. Setup and protocol

- **Splits.** CIFAR-10 40k train / 10k validation / 10k test. Models and damage tables use train; every
  design choice (tier shape, truncation depth) is made on validation; test is used once, and each access
  is logged. CIFAR-100 tests transfer; Kodak tests larger images.
- **Models kept.** A convergence rule fixed before evaluation (best validation epoch ≥ 50 of 60) keeps:
  images, ADJSCC-Q seeds 42, 100, 13, 21, 7 (seed 2024 excluded, clean 26.52 dB ✅
  `published_results/gpu/multiseed/seed2024`) and DeepJSCC-Q seeds 100, 21, 7 for the truncation study
  ✅ `published_results/coding/trunc/` (seeds 42 and 13 of that run did not converge: clean 29.03 and 29.69 dB);
  speech, ADJSCC-Q-1D seeds 42, 100, 7 and DeepJSCC-Q-1D seeds 42, 7, 13 (seed 100 excluded);
  text, DeepJSCC-Q-text seeds 42 and 7 only (all ADJSCC-Q-text and DeepJSCC-Q-text seed 100 excluded).
  ✅ `results/{speech,text}/compare/compare.md`.
  ⚠️ A second DeepJSCC-Q image run exists in `results/g1/deepjsccq/` (seeds 42/100/13/7, all converged,
  clean 31.5–32.4 dB) with hand-tier results but **no truncation results**. Decide which run is "the"
  DeepJSCC-Q image family.
- **Paired protocol.** One master loss mask per batch, channel seed and loss rate, shared by every
  method. Five channel seeds; 95% intervals; gains are paired. Every result file stores the commit and
  checkpoint hash.
- **Criteria fixed before the speech and text tests** (✅ `compare.md`): C1 family top-4 share ≥ 40%;
  C2 every model's measured-order gain at 40% loss ≥ +1.5 dB (speech) / +2.0 pp (text) with its interval
  above zero; C3 a random order gets less than half the measured-order gain. FLAT: top-4 share < 30% and
  the measured-minus-random gap ≤ 0.5.
- **Metrics.** Images PSNR; speech segment SNR and SI-SDR; text character and word accuracy (gains in
  percentage points, pp). ⚠️ SSIM is not reported (the implementation uses zero-padded windows).
  ⚠️ PESQ-WB and STOI were never computed (empty columns in `perceptual.md`).

## B. Images

### B1. Is importance unequal? — Yes.
"We start by asking whether the latent channels matter equally."
In the five ADJSCC-Q models, the top 4 of 16 channels carry **50, 45, 47, 53, 52%** of the damage
(seeds 42, 100, 7, 13, 21). The worst channel costs 8.7–17.1 dB, the least 0.9–2.2 dB. The sorted
profiles look alike across seeds (mean Pearson 0.922), but the channel numbers change (index-aligned
Spearman −0.13): **each model has its own order, and every model has one.**
✅ `published_results/gpu/phase1/multiseed/multiseed.md`.
Without attention the inequality stays: DeepJSCC-Q top-4 share 33–40%, every seed has a channel above
10 dB, profile Pearson 0.930. ✅ `results/g1/deepjsccq/multiseed/multiseed.md`. So the attention modules
do not create it.
**Fig. 4:** sorted damage per channel, both families (`paper/figures/fig_profiles.pdf`).

> An order exists. Can a transmitter find it without running the measurement?

### B2. Can the transmitter see the order? — Not through attention; simple statistics see it.
Within an image the attention gate has **no correlation** with the damage: Spearman −0.015 (95% CI
−0.020 to −0.011). Its top 4 match the true top 4 in 0.23 of cases; random guessing gives 0.25.
(Pooled over images the Pearson is +0.118, but within an image the gate does not order the channels.)
The gate scales channels against noise; it does not measure what losing a channel costs.
Cheap signals do much better (Table II):

| Predictor (image ADJSCC-Q) | Spearman | top-4 overlap | regret (dB) |
|---|---|---|---|
| static table | +0.89 | 0.88 | 0.60 |
| energy | +0.84 | 0.67 | 3.45 |
| ℓ1 norm | +0.84 | 0.68 | — |
| Taylor | +0.63 | 0.64 | — |
| variance | +0.44 | 0.46 | — |
| random | 0.00 | 0.25 | 15.87 |
| attention | −0.015 | 0.23 | 16.76 |
| head (2,048 MACs) | +0.95 | **0.92** | **0.21** |

✅ `published_results/gpu/phase1/{saliency,head}/*.md`.
The table transfers: the CIFAR-10 table on CIFAR-100 has Spearman +0.997 and the same top 4, so it can be
hard-coded. ✅ `published_results/gpu/phase1/transfer/transfer.md`.
**Fig. 5:** attention value vs damage (`results/eval/oracle_attention_correlation.png`).

> We have a good order. How should the parity use it?

### B3. First answer: tiers — and the order is the gain.
The hand design (25/50/25) protects the top quarter strongly and leaves the bottom quarter unprotected.
"Same tiers, same packets, only the order changes" (✅ `headline.md`, `coding_controls_test.md`):

| Loss | uniform (dB) | tiers, measured order | tiers, head | tiers, per-image order | tiers, random | tiers, attention |
|---|---|---|---|---|---|---|
| 30% | 28.67 | −0.95 | −0.87 | −0.77 | −3.33 | −3.10 |
| 35% | 24.40 | +1.31 | +1.42 | +1.52 | −0.93 | −0.93 |
| **40%** | **20.73** | **+2.86** | +3.00 | +3.08 | **+0.94** | **+0.74** |
| 50% | 18.31 | +1.89 | +2.00 | +2.05 | +0.81 | +0.55 |

Averaged over loss ≥ 35%: head +2.31, energy +2.24, ℓ1 +2.22, measured order +2.19, random +0.50,
attention +0.31 dB. A random order recovers 23% of the gain; attention 14%. ✅ `INSIGHTS.md`.
Two weaknesses remain: the tiers win only above about 32% loss, and they **lose about 1 dB below it**,
because the bottom tier never has parity.
Also tested (✅ `coding_controls_test.md`): two RS(48,32) blocks without any order (pure block-length
control): −0.05 dB at 40% — short codes alone do not help. The PET version of the same tiers: +2.78 dB at
40%, better at 30% (−0.41) and 50% (+2.37) because its codes are full length.

> The tiers leave a gap and pay at low loss. Is there a better design?

### B4. Better answer: truncation.
"More interestingly, when the allocation search may choose any layout, it does not choose many levels."
At each loss rate the search (on validation) compares every truncation depth, every multi-tier layout and
every PET layout (✅ `published_results/coding/seed42/allocations.json`, validation PSNR):

| Loss | uniform | best truncation (channels kept) | best multi-tier | best PET |
|---|---|---|---|---|
| 10% | 30.86 | 30.86 (16 = uniform) | 30.86 | 30.86 |
| 30% | 28.62 | 29.48 (15) | 29.48 | 29.39 |
| 35% | 24.38 | 28.52 (14) | 28.54 | 28.41 |
| 40% | 20.73 | **27.26 (13)** | 27.26 | 27.01 |
| 50% | 18.30 | 24.48 (10) | 24.63 | 24.58 |

Test split (✅ `coding_controls_test.md`): truncation in the measured order gives **27.25 dB at 40%
against 20.73 dB (+6.52 dB)**, +6.68 at 45%, +6.21 at 50%, and it never loses at low loss, because there
it *is* equal protection. The 25 best genuine multi-tier designs add at most **0.15 dB**
(✅ macro MultiTierMaxGain). Optimized PET reaches +6.30 dB at 40%.

**Why it wins, explained with the lemma (40% loss):**

| | hand tiers | truncation (13 kept) |
|---|---|---|
| top 4 channels | 5% of bytes lost | 5% |
| next 8 channels | 33% lost (barely better than uniform's 37%) | 5% |
| next 1 channel | 40% lost (no parity) | 5% |
| last 3 channels | 40% lost | 100% (not sent) |

The tiers protect 4 channels well; truncation protects 13 and sacrifices the 3 least important. It also
uses one long code instead of short ones, and it adapts the depth to the loss rate (16, 15, 14, 13, 12,
10 channels kept at ≤20, 30, 35, 40, 45, 50% loss ✅ macros TruncKeep*).

**The order decides it, as the proposition predicted** (✅ `coding_controls_test.md`, 40% loss):
truncation with measured order +6.52, head +6.37, energy +6.00, attention +4.80, **random +1.58 dB**.
Attention order is erratic: +4.12 at 35% but +1.92 at 45% and −0.19 at 50%, as the cut reaches channels
it ranks wrongly.
**Fig. 6** (main result): quality vs loss for uniform, tiers and truncation (`paper/figures/fig_main.pdf`).
**Table III:** gain of each design × each order at 40%.

**Replication over every converged image model** (✅ `published_results/coding/trunc/*/truncation.json`,
test PSNR at 40% loss):

| Models | uniform | tiers (measured order) | **truncation, measured** | truncation, energy | truncation, random |
|---|---|---|---|---|---|
| ADJSCC-Q s42/100/13/21/7 | 20.6–21.0 | 23.4–23.9 | **25.0–27.3** | 25.3–26.7 | 22.1–22.7 |
| DeepJSCC-Q s100/21/7 | 17.8–19.5 | 21.9–22.7 | **25.6–28.0** | 26.0–27.9 | 19.6–21.5 |

Truncation gains +4.0 to +9.4 dB over uniform on all 8 models and beats the tiers on every one
(+1.7 to +5.8 dB). Energy order is within 0.9 dB of the measured order on every model. Attention order
falls below random on ADJSCC-Q seed 21 (20.78 vs 22.24 dB). ✅

> If the order is worth this much, can we build it into the model?

### B5. Making the order explicit (nested dropout).
Train with nested ("tail") dropout: half of the images keep only a random prefix of the channels, so
the model learns to put its information first. Its measured order equals the channel index; the last
five channels each cost at most 0.02 dB. Clean cost 0.24 dB (30.64 dB). Truncation then barely depends
on the loss: 30.64 / 30.63 / 30.62 / **30.60** / 30.45 / 30.26 dB at 20 / 30 / 35 / 40 / 45 / 50% loss,
while uniform RS on the same model falls to 17.96 dB at 40%. DeepJSCC-Q version: 31.32 dB at 40%.
✅ macros Ordered*, `published_results/coding/trunc/adjsccq_td05`, `deepjsccq_td05`.
A model trained for 8 channels behind RS(96,32) holds 30.06 dB at every loss up to 50% (its code never
fails); the ordered 16-channel model is above it with one network. ✅ macros KnTwelve*.

> Truncation is strong inside our system. How does it compare with other ways to use the same bytes?

### B6. Comparison with other systems — stated honestly.
Same 1,536 bytes (✅ `published_results/gpu/final/digital/digital.md`, macros):

| Loss | WebP fixed RS | JPEG fixed RS | JPEG2000 fixed RS | WebP adaptive RS | JSCC uniform | JSCC best design (selector) |
|---|---|---|---|---|---|---|
| 0% | 38.14 | 36.76 | 32.91 | 38.14 | 30.88 | 30.88 |
| 35% | 23.04 | 21.64 | 20.57 | 37.28 | 24.40 | 28.54 |
| 40% | 15.32 | 14.06 | 14.36 | **36.84** | 20.73 | 27.25 |
| 50% | 12.52 | 11.75 | 12.33 | 35.35 | 18.31 | 24.66 |

⚠️ JPEG2000 with fixed RS differs slightly between `digital.md` (20.74 / 14.56 / 12.42 dB at 35 / 40 /
50%) and the macros used above (20.57 / 14.36 / 12.33); the other codecs match. Check which run is final.
Without any RS the codecs collapse to 9.8–12.9 dB at only 10% loss. With a fixed RS(96,64) they fall off
the same cliff as our uniform scheme. But **when the codec may also choose fewer source bytes and a
stronger code, WebP beats every JSCC system here.** We say this plainly: our claim is how to protect a
learned latent once it is the transmitted representation, not that JSCC beats codecs.
A JSCC model that spends all 1,536 bytes on latent data, with no RS, erasure-fine-tuned (DeepJSCC-Q,
24 channels): 24.36 dB at 40%, against 26.03 dB for RS + truncation and 27.05 dB for RS + truncation
after the same fine-tuning. RS with truncation wins up to 45% loss. (The 24-channel ADJSCC-Q never
converged: best clean 27.83 dB.) ✅ macros NoRs*, RsDeep*.
Grad-FEC-style drop-and-protect (top 8 coded, 4 dropped): +4.52 dB at 40% but −3.80 dB on a clean
channel. ✅
**Fig. 8:** reconstructed images at 40% loss (⚠️ to make, Deep JSCC paper style).

> All of this is images. Is the order a property of images, or of learned latents in general?

## C. Speech — the story transfers.

"We next repeat the study on speech."
**Unequal?** Yes. Top-4 share 46, 45, 38% for ADJSCC-Q-1D (family 43 ± 4%) and 48, 46, 46% for
DeepJSCC-Q-1D (46 ± 1%). Worst channel 5.2–9.8 dB / 9.4–11.7 dB of segment SNR. Profiles repeat across
seeds (Pearson 0.973 / 0.828); channel numbers change. ✅ `results/speech/*/multiseed/multiseed.md`.
**Visible to attention?** No — even negative: Spearman −0.217 (CI −0.226 to −0.208), top-4 overlap
0.14, below chance. Energy +0.87 (ADJSCC-Q-1D) and +0.94 (DeepJSCC-Q-1D). Here the static table is
weaker for ADJSCC-Q-1D (+0.42) and the head helps more (top-4 0.68 vs 0.55; regret 0.71 vs 1.41 dB).
✅ `results/speech/*/seed42/{saliency,head,attention}`.
**Does the order pay?** Yes (✅ `results/speech/compare/compare.md`, validation-selected tiers, 40% loss):

| Family | measured order | energy | random | criteria |
|---|---|---|---|---|
| ADJSCC-Q-1D | +1.76 ± 0.24 dB (per model +2.01, +1.76, +1.52) | +1.78 | +0.81 | met |
| DeepJSCC-Q-1D | +2.96 ± 0.36 dB (+3.36, +2.90, +2.64) | +2.98 | +0.63 | met |

Attention order with the hand tiers: +0.37 to +0.88 dB. Below about 33% the tiers lose 0.7–1.0 dB, as
for images. ✅ `results/speech/*/seed*/test_sweep/test_sweep.md`.
**An observation worth a paragraph:** without any RS, ADJSCC-Q-1D keeps 4.1–4.3 dB at 10% loss (from
6.4–6.7 clean), DeepJSCC-Q-1D only 0.2–1.8 dB. Attention modules make the raw latent robust to random
erasures, even though they do not point to the important channels.
**SI-SDR** agrees (500 segments): ADJSCC-Q-1D at 40% loss: uniform −3.04, measured-order tiers −1.03,
energy tiers −0.56 dB. ✅ `perceptual.md`.
**Fig. 9:** speech damage profiles (`results/speech/compare/sorted_profiles.png`); Table V per model.
⚠️ **Truncation has not been run on speech.** `experiments/eval_truncation.py` hard-codes CIFAR-10
(line 40). Run it on the 6 converged speech models; until then, section B4's claim is image-only.
⚠️ Speech quality is low in absolute terms (clean SNR 6.4–6.7 dB). Say so; the claims are relative.

> Speech confirms the story. Text tests its limit.

## D. Text — the measurement says "don't bother", and that is useful.

"Finally, we apply the same measurement to text."
**Training was hard.** Only 2 of 6 models converged (DeepJSCC-Q-text seeds 42 and 7: clean character
accuracy 69.2% and 64.6%, word accuracy about 32%, 1.34 bits/char). ✅ `metrics.json`, `compare.md`.
**Unequal?** No: the top 4 carry 28 and 30% (25% is flat), and *every* channel is costly, 12.4–31.1
points of character accuracy. ✅ `results/text/deepjsccq_text/multiseed/multiseed.md`.
**Visible?** Energy stops working on text (+0.42); only the static table works (+0.77), and the head
adds nothing beyond it. ✅ `results/text/deepjsccq_text/seed42/{saliency,head}`.
**Does the order pay?** At 40% loss the tiers gain +2.57 ± 0.85 pp with the measured order, +2.69 with
energy, and **+1.74 with a random order** (68% of the gain). The family is labelled FLAT. ✅ `compare.md`.
But at 40% loss every method gives 23–26% character accuracy (no RS 18–21%), close to always guessing the
most common character; the text is unreadable either way. Where text is still readable, at 30% loss
(uniform 58.8% / 55.9%), the tiers **lose** 17.0 / 11.8 points. ✅ `test_sweep.md`.
**Conclusion for text:** equal protection is right at every useful operating point, and the measurement
tells us so before we design anything.
**Fig. 10:** text damage profiles (flat); **Table VI:** a text example at 40% loss
(`results/text/deepjsccq_text/seed42/examples/`).
⚠️ No attention model converged for text; the attention value −0.12 is from a non-converged model and is
reported only for completeness.

## E. All sources together — the climax

"One figure summarises the paper": gain over equal protection at 40% loss against the top-4 share, for
every model; measured order filled, random order open; colour by source. The more unequal the damage,
the more the order is worth. Share of the gain that a random order already gets: about 0.2–0.3 for images
and DeepJSCC speech, 0.46 for ADJSCC speech, 0.68 for text.
**Table VII:** summary across sources (top-4 share, attention and energy correlation, measured and random
gain, criteria).
⚠️ **Fig. 11 must be made** (one plot, all three sources; per-source versions exist in
`results/{speech,text}/compare/gain_vs_concentration.png`).

## F. Robustness — short answers to the reader's doubts

- **Bursts** (Gilbert–Elliott, 1% loss in the good state, 85% in the bad). At 35% average loss and mean
  burst 16, tiers sent in order lose 0.56 dB (one burst wipes out a tier); interleaved round-robin they
  gain 0.80 dB. At 45% average loss, truncation gains +6.65 dB with independent losses and +2.05 dB at
  burst 16. ✅ `published_results/gpu/final/burst/*`, macros Burst*.
- **Wrong loss rate.** A truncation designed for 40% costs 2.59 dB on a clean channel. So the transmitter
  selects the design from the loss rate (one byte of signalling per change). The only case where a
  multi-level design wins: one allocation for 10–50% loss chooses four tiers (−2.47 dB at 10%, +5.43 dB
  at 40%). ✅ `coding_controls_test.md` (design*, robust*), macros.
- **Larger images.** Kodak (24 images, 768×512, coded with the CIFAR model in 128-byte packets; clean
  24.31 dB, so relative results only): tiers +1.43 dB at 40%, +1.46 at 45%; attention +0.27; no
  low-loss penalty. ✅ `published_results/gpu/phase3/kodak/kodak.md`.
- **Erasure-aware training.** Fine-tuning with channel drops, packet drops or an inpainter narrows the
  low-loss penalty (−0.87 → −0.41 dB at best) but lifts uniform RS more than UEP; peak gain falls to
  +1.17…+2.51 dB. After channel-drop fine-tuning, energy order beats the old static table (+2.49 vs
  +1.46): a table goes stale when the model changes. ✅ `published_results/gpu/phase2/*`, `INSIGHTS.md`.
- **Bandwidth ratio.** Tier gain at 40% loss: k/n = 1/3: +2.51; 1/6: +2.86; 1/12: +1.49; 1/16: +1.00 dB;
  positive everywhere at high loss. ✅ `published_results/gpu/phase3/kn_*/test_sweep`.

## G. Complexity — almost nothing

Static table: 16 bytes in the decoder, no side information. Head: 2,048 MACs, 0.039% of the image encoder
and 0.024% of the speech encoder. ✅ `head_metrics.md`. Measuring the table: 16 decoder passes per training
sample, once per model. The receiver runs the same RS decoder as for equal protection.

> The evidence is in. What does it mean, and where does it stop?

---

# V. Discussion and limitations

- **What to protect.** At a known loss rate the answer is not "several levels" but "which channels to
  send at all". The order decides the quality.
- **When not to.** A flat profile (text) leaves nothing to exploit, and the measurement says so first.
- **Limits.** Low absolute quality for speech (6.4–6.7 dB SNR) and text (65–69% characters); codecs with
  adaptive RS stay ahead on images; 32×32 images (Kodak only with the CIFAR model); truncation, bursts,
  Kodak, codecs and bandwidth studies are image-only; the selector needs the loss rate; PSNR only for
  images, no perceptual speech metric yet; several models did not converge and were excluded by a rule
  fixed in advance (for text this leaves no attention model).

# VI. Conclusions and future work

Close the loop, as the Deep JSCC paper does (recap, then the insight, then what comes next):
**C1.** Deep JSCC removed the cliff; packet networks bring it back; much of the lost quality returns when
the parity follows the latent's hidden order.
**C2.** For images and speech, a few channels carry most of the damage; attention does not find them, a
simple measurement does; with that order, the best design drops the least important channels and
protects the rest with one strong code. For text the order is flat and equal protection is right.
**C3.** Do not protect everything equally, but measure what "important" means first. Next steps:
truncation for speech and text, entropy-coded latents, larger images, unknown loss rates.

# Appendices

A. Proofs (lemma, proposition, dynamic program). B. Architectures and hyperparameters per source.
C. Additional results: per-seed sweeps, all tier shapes, 5th-percentile curves, CDFs, block-failure
rates, head training curves.

---

# Writing order (how we draft it, not how it reads)

1. **Figures and tables first** — the story is the figures. Make Fig. 11 (all sources), Fig. 8 (images),
   Fig. 3 (packet layouts); everything else exists.
2. **Section IV (Evaluation)**, in the order above: B1 → B6, then C, D, E, F, G.
3. **Section III (Method)**: now we know exactly which tools the results use.
4. **Section II (Background)**: only what Section III needs.
5. **Discussion and Conclusions.**
6. **Introduction** — written once the results are fixed, so P6 promises exactly what IV delivers.
7. **Abstract and title** last.

# Figures and tables

| # | Content | Status |
|---|---|---|
| Fig. 1 | System model | TikZ in `main_narrative.tex` |
| Fig. 2 | Pipeline, new blocks in orange | TikZ in `main_narrative.tex` |
| Fig. 3 | Packet layouts: uniform / tiers / PET / truncation | ⚠️ to draw |
| Fig. 4 | Image damage profiles | `paper/figures/fig_profiles.pdf` |
| Fig. 5 | Attention vs damage (images) | `results/eval/oracle_attention_correlation.png` |
| Fig. 6 | Quality vs loss: uniform, tiers, truncation | `paper/figures/fig_main.pdf` |
| Fig. 7 | Design-rate mismatch (optional) | `paper/figures/fig_mismatch.pdf` |
| Fig. 8 | Reconstructed images at 40% loss | ⚠️ to make |
| Fig. 9 | Speech damage profiles | `results/speech/compare/sorted_profiles.png` |
| Fig. 10 | Text damage profiles | `results/text/compare/sorted_profiles.png` |
| Fig. 11 | Gain vs concentration, all sources | ⚠️ to make |
| Table I | Sources and byte format | in this file, §III.A |
| Table II | Predictors vs damage (all sources) | numbers in `RESULTS_COMPENDIUM.md` §2.3 |
| Table III | Designs × orders at 40% | §IV.B3–B4 above |
| Table IV | Codecs vs JSCC | §IV.B6 above |
| Table V | Speech per model | `RESULTS_COMPENDIUM.md` §3.5 |
| Table VI | Text example | `results/text/deepjsccq_text/seed42/examples/` |
| Table VII | Summary across sources | `RESULTS_COMPENDIUM.md` §1.8 |

# Before we submit (open items, in order of importance)

1. ⚠️ Run truncation and the allocation search on speech (and text, for completeness). Needs a small
   change to `experiments/eval_truncation.py` (dataset hard-coded to CIFAR-10).
2. ⚠️ Choose one DeepJSCC-Q image run (`results/g1t4`, used for truncation, vs `results/g1`, all seeds
   converged, no truncation) and one definition of top-4 share (dB vs MSE).
3. ⚠️ Make Fig. 11, Fig. 8, Fig. 3.
4. ⚠️ PESQ-WB / STOI for speech, or drop the mention.
5. ⚠️ Recheck the quantizer numbers (0.5 dB cost, 179/256 levels) on the final primary model.
6. ⚠️ Confirm the speech training loss; verify the extra bibliography entries.

# Verification log (24 Nov 2026)

Every ✅ number above was read from the file named next to it during this session. Checks that found
problems, and how they are handled here:
- The image DeepJSCC-Q models in the truncation study (`results/g1t4`) are not the ones in
  `results/g1/`; seeds 42 and 13 of the first run did not converge. → open item 2.
- Text predictor numbers from the non-converged ADJSCC-Q-text (energy +0.80) contradict the converged
  model (+0.42). → this file uses the converged model.
- The progress-review slides quote "≈ 32%" as the break-even point and "+3.00 dB" at 40%; both match
  `INSIGHTS.md` (+3.00 is the head order; the static table gives +2.86).
- The interleaving claim (81% vs 0.07%) is the probability that *some* codeword fails at 20% loss, not
  the fraction of codewords that fail. → worded accordingly in §II.A.
- JPEG2000 with fixed RS: two result files disagree by up to 0.2 dB (`digital.md` vs macros). → flagged
  in §IV.B6.
- "Send only the important channels" overstates truncation: at 40% it keeps 13 of 16. → worded as "drop
  the least important channels" throughout.
