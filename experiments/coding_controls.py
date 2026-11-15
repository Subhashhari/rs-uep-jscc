"""Coding-theory controls reviewers ask for, evaluated exactly and fast.

Questions answered (one model per run):

1. **Block length vs importance.** ``two_tier_50_50`` *unsorted* (two RS(48,32) blocks, the uniform code
   rate) isolates the pure block-length effect; random-order tiers isolate "splitting into tiers";
   ranked tiers add importance. The per-image leave-one-out ranking is the upper bound.
2. **Grouped tiers vs PET.** Every grouped scheme has a PET twin with the same per-tier code rate in
   which every tier spans all 96 packets (Albanese et al., 1996); ``coding/outcome.py``.
3. **Optimal allocation.** For every design loss rate, the surrogate-optimal grouped and PET
   allocations (``experiments/allocation.py``, dropping data allowed, which contains Grad-FEC's
   drop-and-protect) are refined by local search on the *validation* split with the exact simulator.
   A design for a whole loss-rate range (``robust``), a loss-aware selector (uniform vs optimised,
   chosen per rate on validation) and a design/actual mismatch matrix follow.
4. **Grad-FEC-style baselines** (Uyanik et al., ICIP 2023): drop the least important channels and
   spend their packets on parity for the most important ones.

Exactness: the receiver's outcome is computed by ``coding.outcome`` (bit-exact with real RS decoding,
``tests/test_outcome.py``) and the decoder is the trained model, so the numbers are the same as
``experiments/eval_rs_uep.py`` would give. Loss masks and random orders use the same generator seeds
and the same 250-image batches as that evaluator, so ``--reference_json`` can check overlapping
methods against a published sweep to the last digit.

Stages
------
``--stage val``   optimise allocations on validation (default 5,000 images x seeds 0,1,2) and write
                  ``allocations.json``.
``--stage test``  evaluate every method on the test split (all 10,000 images x seeds 0-4) with the
                  allocations fixed on validation. Every test access is logged.

    python -m experiments.coding_controls --stage val --checkpoint results/gpu/models/seed42/best_val.pth \\
        --oracle_ranking_file results/gpu/models/seed42/oracle_ranking.json --output_dir results/coding/seed42
    python -m experiments.coding_controls --stage test --checkpoint ... --oracle_ranking_file ... \\
        --head_checkpoint results/gpu/phase1/head/sensitivity_head.pt --output_dir results/coding/seed42 \\
        --reference_json results/gpu/final/final_test.json
"""
import argparse
import json
import os
import time
from types import SimpleNamespace
from typing import Dict, List, Optional, Sequence

import numpy as np
import torch

from coding.outcome import (
    Layout,
    grouped_layout,
    layout_from_scheme,
    lost_latent_symbols,
    pet_layout,
    pet_twin,
    stream_loss_probability,
)
from coding.rs_pipeline import SCHEME_CANDIDATES, random_channel_order
from experiments.allocation import (
    grouped_neighbours,
    hill_climb,
    loss_weighting,
    optimal_grouped,
    optimal_pet,
    pet_neighbours,
    surrogate_cost,
    symbol_weights_from_channels,
)
from experiments.eval_rs_uep import parse_csv, prepare_data
from experiments.metrics import per_item_mse, quality_db_per_item
from experiments.model_io import reconstruct
from experiments.reproducibility import build_provenance, seed_everything, seed_statistics, write_json
from experiments.stats_utils import paired_difference, spearman

MASTER_PACKETS = 96
TEST_RATES = (0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5)
DESIGN_RATES = (0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5)
GRADFEC = {  # name: (protected top channels, dropped bottom channels); the rest is sent without parity
    "gradfec_top4_drop4": (4, 4), "gradfec_top8_drop4": (8, 4), "gradfec_top4_drop8": (4, 8),
}


# ----------------------------------------------------------------------------------------------
# Exact fast simulator
# ----------------------------------------------------------------------------------------------
class Simulator:
    """Per-image quality of a layout + channel order under the evaluator's exact loss masks."""

    def __init__(self, bundle, images: torch.Tensor, prep: dict, batch_size: int = 250, chunk: int = 2500):
        self.bundle, self.images, self.prep = bundle, images, prep
        self.batch_size, self.chunk = batch_size, chunk
        self.n = len(images)
        self.channels = bundle.channels
        self.spc = bundle.symbols_per_channel
        with torch.no_grad():
            self.latent = bundle.encoder.quantizer.dequantize_indices(prep["idx"].long()).cpu()
        self._uniform: Dict[int, torch.Tensor] = {}
        self._random: Dict[int, torch.Tensor] = {}
        self.evaluations = 0

    def _batches(self):
        for b, start in enumerate(range(0, self.n, self.batch_size)):
            yield b, start, min(start + self.batch_size, self.n)

    def uniform_draws(self, seed: int) -> torch.Tensor:
        """The uniforms behind ``sample_master_mask``: mask = draws < rate (nested across rates)."""
        if seed not in self._uniform:
            parts = [torch.rand(stop - start, MASTER_PACKETS, generator=torch.Generator().manual_seed(seed * 100000 + b))
                     for b, start, stop in self._batches()]
            self._uniform[seed] = torch.cat(parts)
        return self._uniform[seed]

    def random_order(self, seed: int) -> torch.Tensor:
        if seed not in self._random:
            parts = [random_channel_order(stop - start, self.channels,
                                          torch.Generator().manual_seed(seed * 100000 + b + 50000))
                     for b, start, stop in self._batches()]
            self._random[seed] = torch.cat(parts)
        return self._random[seed]

    def order(self, source: Optional[str], seed: int) -> Optional[torch.Tensor]:
        if source is None:
            return None
        if source == "random":
            return self.random_order(seed)
        return self.prep["orders"][source]

    @torch.no_grad()
    def run(self, layout: Layout, source: Optional[str], seed: int, rate: float, index=None):
        """``(quality_db, mse, lost_fraction)`` per image (``index`` restricts to a subset of images)."""
        self.evaluations += 1
        mask = self.uniform_draws(seed) < rate
        order = self.order(source, seed)
        if index is not None:
            mask = mask[index]
            order = None if order is None else order[index]
        lost = lost_latent_symbols(layout, mask, order, self.spc)
        latent = self.latent if index is None else self.latent[index]
        images = self.images if index is None else self.images[index]
        quality, mse = [], []
        for start in range(0, len(latent), self.chunk):
            stop = start + self.chunk
            z = latent[start:stop].masked_fill(lost[start:stop], 0.0).to(self.bundle.device)
            recon = reconstruct(self.bundle, z, lost[start:stop].to(self.bundle.device), self.bundle.snr_db)
            x = images[start:stop].to(self.bundle.device)
            quality.append(quality_db_per_item(recon, x).cpu())
            mse.append(per_item_mse(recon, x).cpu())
        return torch.cat(quality).numpy(), torch.cat(mse).numpy(), float(lost.float().mean())


# ----------------------------------------------------------------------------------------------
# Method catalogue
# ----------------------------------------------------------------------------------------------
def gradfec_layout(protect: int, drop: int, channels: int = 16, packets_per_channel: int = 4) -> Layout:
    middle = channels - protect - drop
    tiers = [(MASTER_PACKETS - packets_per_channel * middle, packets_per_channel * protect)]
    if middle:
        tiers.append((packets_per_channel * middle, packets_per_channel * middle))
    if drop:
        tiers.append((0, packets_per_channel * drop))
    return grouped_layout(tiers, name=f"gradfec[{protect}+{middle}u+{drop}x]")


def truncation_layout(keep: int, channels: int = 16, packets_per_channel: int = 4) -> Layout:
    """Importance-ordered truncation + equal protection: one RS(96, 4*keep) block over the ``keep`` most
    important channels; the other channels are not sent. ``keep = channels`` is uniform RS(96, 64)."""
    tiers = [(MASTER_PACKETS, packets_per_channel * keep)]
    if keep < channels:
        tiers.append((0, packets_per_channel * (channels - keep)))
    return grouped_layout(tiers, name=f"trunc[{keep}]")


def layout_from_record(record: dict) -> Layout:
    if record["family"] == "grouped":
        return grouped_layout([tuple(t) for t in record["tiers"]])
    return pet_layout(record["column_k"], MASTER_PACKETS, 16, record["dropped"], record.get("placement", "column"))


def record_from_layout(layout: Layout) -> dict:
    if layout.family == "grouped":
        return {"family": "grouped", "tiers": [list(t) for t in layout.params], "name": layout.name}
    column_k, dropped, placement = layout.params
    return {"family": "pet", "column_k": list(column_k), "dropped": dropped, "placement": placement,
            "name": layout.name}


# ----------------------------------------------------------------------------------------------
# Validation stage: optimise allocations
# ----------------------------------------------------------------------------------------------
def channel_weights(ranking_info: dict) -> np.ndarray:
    """LOO MSE increase sorted most damaging first (the surrogate's per-rank weights)."""
    with open(ranking_info["path"], "r", encoding="utf-8") as handle:
        data = json.load(handle)
    mse = np.asarray(data["mse_increase_by_channel"], dtype=np.float64)
    return mse[[int(c) for c in data["ranking_channels_most_to_least_important"]]]


def stage_val(args, sim: Simulator, weights: np.ndarray, seeds: Sequence[int]) -> dict:
    spc = sim.spc
    sym_w = symbol_weights_from_channels(weights, spc)
    source = "static:oracle"
    trace: List[dict] = []
    clean_mse = None

    def mean_quality(layout: Layout, rates) -> float:
        values = []
        for rate in rates:
            for seed in seeds:
                quality, mse, _ = sim.run(layout, source, seed, rate)
                values.append(float(quality.mean()))
                trace.append({"layout": layout.name, "rate": rate, "seed": seed, "psnr": float(quality.mean()),
                              "mse": float(mse.mean())})
        return float(np.mean(values))

    def climb(start: Layout, family: str, rates):
        if family == "grouped":
            to_layout = lambda c: grouped_layout(list(c))  # noqa: E731
            neighbours = lambda c: grouped_neighbours(c, MASTER_PACKETS)  # noqa: E731
            start_key = tuple(tuple(t) for t in start.params)
        else:
            placement = start.params[2]
            to_layout = lambda c: pet_layout(c[0], MASTER_PACKETS, 16, c[1], placement)  # noqa: E731
            neighbours = lambda c: pet_neighbours(c[0], c[1], MASTER_PACKETS)  # noqa: E731
            start_key = (tuple(start.params[0]), start.params[1])
        best, value, cache = hill_climb(start_key, neighbours, lambda c: mean_quality(to_layout(c), rates),
                                        max_evaluations=args.hill_evals)
        return to_layout(best), value, len(cache)

    designs: Dict[str, dict] = {}
    targets = [(f"{rate:g}", (rate,)) for rate in args.design_rates] + [("robust", tuple(args.design_rates))]
    for label, rates in targets:
        prior = loss_weighting(rates)
        tiers, g_cost = optimal_grouped(weights, prior, MASTER_PACKETS, spc // 16)
        column_k, dropped, p_cost = optimal_pet(sym_w, prior, MASTER_PACKETS, 16)
        entry = {"rates": list(rates)}
        started = time.time()
        trunc_values = {keep: mean_quality(truncation_layout(keep, sim.channels), rates)
                        for keep in range(1, sim.channels + 1)}
        keep = max(trunc_values, key=trunc_values.get)
        g0 = grouped_layout(tiers)
        # start the grouped search from the better of the surrogate optimum and the best truncation
        g_start = g0 if mean_quality(g0, rates) >= trunc_values[keep] else truncation_layout(keep, sim.channels)
        g_best, g_val, g_n = climb(g_start, "grouped", rates)
        start_values = {placement: mean_quality(pet_layout(column_k, MASTER_PACKETS, 16, dropped, placement), rates)
                        for placement in ("column", "diagonal")}
        placement = max(start_values, key=start_values.get)
        p_best, p_val, p_n = climb(pet_layout(column_k, MASTER_PACKETS, 16, dropped, placement), "pet", rates)
        pet_options = {key: (None, value) for key, value in start_values.items()}
        entry.update({
            "grouped_surrogate_start": record_from_layout(g0), "grouped_surrogate_cost": g_cost,
            "grouped": record_from_layout(g_best), "grouped_val_psnr": g_val, "grouped_evaluations": g_n,
            "pet_surrogate_start": {"column_k": list(column_k), "dropped": dropped}, "pet_surrogate_cost": p_cost,
            "pet": record_from_layout(p_best), "pet_val_psnr": p_val, "pet_evaluations": p_n,
            "pet_placement_val_psnr_at_surrogate_start": {key: value[1] for key, value in pet_options.items()},
            "trunc_keep": keep, "trunc_val_psnr": trunc_values[keep],
            "trunc_val_psnr_by_keep": {str(k): v for k, v in trunc_values.items()},
            "seconds": round(time.time() - started, 1),
        })
        if len(rates) == 1:   # loss-aware selector: uniform vs the two optimised layouts, chosen on validation
            uniform_val = trunc_values[sim.channels]   # trunc[16] is uniform RS(96,64)
            candidates = {"uniform": uniform_val, "grouped": g_val, "pet": p_val, "trunc": trunc_values[keep]}
            entry["uniform_val_psnr"] = uniform_val
            entry["selector_choice"] = max(candidates, key=candidates.get)
        designs[label] = entry
        print(f"[val] design {label}: grouped {g_best.name} {g_val:.3f} dB ({g_n} evals) | "
              f"pet {p_best.name} {p_val:.3f} dB ({p_n} evals) | trunc[{keep}] {trunc_values[keep]:.3f} | "
              f"selector {entry.get('selector_choice', '-')}", flush=True)

    # Surrogate fidelity: additive-MSE prediction vs simulated mean MSE over every layout evaluated.
    clean = float(np.mean(sim.run(layout_from_scheme(SCHEME_CANDIDATES["uniform"]), None, 0, 0.0)[1]))
    predicted, simulated = [], []
    seen = {}
    for item in trace:
        seen.setdefault((item["layout"], item["rate"]), []).append(item["mse"])
    layouts_by_name = {}
    for label, entry in designs.items():
        for key in ("grouped", "pet"):
            layout = layout_from_record(entry[key])
            layouts_by_name[layout.name] = layout
    for (name, rate), values in seen.items():
        layout = layouts_by_name.get(name)
        if layout is None:
            continue
        predicted.append(clean + surrogate_cost(layout, sym_w, loss_weighting([rate])))
        simulated.append(float(np.mean(values)))
    fidelity = {
        "clean_mse": clean, "n_points": len(predicted),
        "spearman_predicted_vs_simulated_mse": spearman(predicted, simulated) if len(predicted) > 2 else None,
        "median_relative_error": float(np.median(np.abs(np.array(predicted) / np.array(simulated) - 1)))
        if predicted else None,
    }
    return {"designs": designs, "surrogate_fidelity": fidelity, "source": source,
            "channel_weights_mse_sorted": weights.tolist(), "evaluations": sim.evaluations,
            "trace": trace if args.keep_trace else None}


# ----------------------------------------------------------------------------------------------
# Test stage
# ----------------------------------------------------------------------------------------------
def build_methods(args, allocations: dict, sources_available: Sequence[str], has_attention: bool, profile: str):
    """``{name: (layout or {rate: layout}, source)}``."""
    s = {k: SCHEME_CANDIDATES[k] for k in SCHEME_CANDIDATES}
    m: Dict[str, tuple] = {
        "uniform": (layout_from_scheme(s["uniform"]), None),
        "no_rs": (grouped_layout([(64, 64)]), None),
        "two_tier_50_50@unsorted": (layout_from_scheme(s["two_tier_50_50"]), None),
        "uniform_pet_diag@unsorted": (pet_layout([64] * 16, MASTER_PACKETS, 16, 0, "diagonal"), None),
    }
    primary = layout_from_scheme(s["three_tier_25_50_25"])
    for source in ["static:oracle", "energy", "predicted", "attention", "random", "oracle_perimage"]:
        if source == "attention" and not has_attention:
            continue
        if source not in ("random",) and source not in sources_available:
            continue
        m[f"three_tier_25_50_25@{short(source)}"] = (primary, source)
    m["pet_twin_three_tier_25_50_25@oracle"] = (pet_twin(s["three_tier_25_50_25"].tiers), "static:oracle")
    m["pet_twin_three_tier_25_50_25_diag@oracle"] = (
        pet_twin(s["three_tier_25_50_25"].tiers, placement="diagonal"), "static:oracle")
    for name, (protect, drop) in GRADFEC.items():
        m[f"{name}@oracle"] = (gradfec_layout(protect, drop), "static:oracle")

    designs = allocations["designs"]
    per_rate_g = {float(k): layout_from_record(v["grouped"]) for k, v in designs.items() if k != "robust"}
    per_rate_p = {float(k): layout_from_record(v["pet"]) for k, v in designs.items() if k != "robust"}

    per_rate_t = {float(k): truncation_layout(v["trunc_keep"]) for k, v in designs.items() if k != "robust"}

    def selector_layout(rate):
        entry = designs[f"{rate:g}"]
        choice = entry["selector_choice"]
        if choice == "uniform":
            return layout_from_scheme(s["uniform"])
        if choice == "trunc":
            return truncation_layout(entry["trunc_keep"])
        return layout_from_record(entry[choice])

    selector = {float(k): selector_layout(float(k)) for k in designs if k != "robust"}
    for source in ["static:oracle", "energy", "predicted"]:
        if source in sources_available:
            m[f"opt_grouped@{short(source)}"] = (per_rate_g, source)
            m[f"opt_pet@{short(source)}"] = (per_rate_p, source)
    for source in ["static:oracle", "energy", "predicted", "attention", "random"]:
        if source == "attention" and not has_attention:
            continue
        if source == "random" or source in sources_available:
            m[f"opt_trunc@{short(source)}"] = (per_rate_t, source)
    m["opt_selector@oracle"] = (selector, "static:oracle")
    m["robust_grouped@oracle"] = (layout_from_record(designs["robust"]["grouped"]), "static:oracle")
    m["robust_pet@oracle"] = (layout_from_record(designs["robust"]["pet"]), "static:oracle")
    if profile == "full":   # mismatch: a layout designed for p_d used at every p
        for design_rate, layout in per_rate_g.items():
            m[f"design{design_rate:g}_grouped@oracle"] = (layout, "static:oracle")
    return m


def short(source: str) -> str:
    return "oracle" if source == "static:oracle" else source


def layout_for(spec, rate: float) -> Layout:
    if isinstance(spec, dict):
        nearest = min(spec, key=lambda r: (abs(r - rate), -r)) if rate > 0 else min(spec)
        return spec[nearest]
    return spec


def stage_test(args, sim: Simulator, methods: dict, seeds: Sequence[int], rates: Sequence[float]):
    rows, per_image = [], {}
    started = time.time()
    for name, (spec, source) in methods.items():
        for rate in rates:
            layout = layout_for(spec, rate)
            per_seed = []
            for seed in seeds:
                quality, mse, lost = sim.run(layout, source, seed, rate)
                per_seed.append(float(quality.mean()))
                per_image[(name, seed, rate)] = quality.astype(np.float32)
                rows.append({"method": name, "seed": seed, "erasure_rate": rate, "psnr_db_mean": float(quality.mean()),
                             "mse_mean": float(mse.mean()), "psnr_db_p5": float(np.percentile(quality, 5)),
                             "lost_symbol_fraction": lost, "layout": layout.name, "source": source,
                             "dropped_symbols": layout.dropped_symbols,
                             "side_info_bytes": 0 if source in (None, "static:oracle") else sim.channels})
        print(f"[test] {name} done ({time.time() - started:.0f} s)", flush=True)
    return rows, per_image


def summarise(rows: List[dict], per_image: dict, seeds, rates, baseline: str = "uniform", n_boot: int = 1000):
    by = {}
    for r in rows:
        by.setdefault((r["method"], r["erasure_rate"]), []).append(r)
    summary = []
    rng = np.random.default_rng(0)
    for (method, rate), items in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        items = sorted(items, key=lambda r: r["seed"])
        values = [r["psnr_db_mean"] for r in items]
        stats = seed_statistics(values)
        entry = {"method": method, "erasure_rate": rate, "psnr_db_mean": stats["mean"],
                 "psnr_db_ci95_seeds": stats["ci95_half_width"], "layout": items[0]["layout"],
                 "source": items[0]["source"], "side_info_bytes": items[0]["side_info_bytes"],
                 "dropped_symbols": items[0]["dropped_symbols"],
                 "lost_symbol_fraction": float(np.mean([r["lost_symbol_fraction"] for r in items])),
                 "psnr_db_p5": float(np.mean([r["psnr_db_p5"] for r in items]))}
        base = [r["psnr_db_mean"] for r in sorted(by[(baseline, rate)], key=lambda r: r["seed"])]
        paired = paired_difference(values, base)
        entry.update({"gain_vs_uniform_db": paired["mean"], "gain_ci95_seeds": paired["ci95_half_width"]})
        # image-level bootstrap of the seed-averaged per-image gain (covers image sampling)
        gain = np.mean([per_image[(method, s, rate)] - per_image[(baseline, s, rate)] for s in seeds], axis=0)
        if method != baseline:
            boot = np.array([gain[rng.integers(0, len(gain), len(gain))].mean() for _ in range(n_boot)])
            entry["gain_ci95_images"] = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
        summary.append(entry)
    return summary


def reference_check(summary: List[dict], reference_path: str) -> dict:
    """Compare methods that also appear in a published ``eval_rs_uep`` sweep (same masks -> same numbers)."""
    with open(reference_path, "r", encoding="utf-8") as handle:
        reference = json.load(handle)
    ref = {(r["method"], r["erasure_rate"]): r["psnr_db_mean_per_image__mean"] for r in reference["seed_summary"]}
    names = {"uniform": "uniform", "no_rs": "no_rs"}
    for source in ("oracle", "energy", "predicted", "attention", "random"):
        names[f"three_tier_25_50_25@{source}"] = f"three_tier_25_50_25@{source}"
    diffs = []
    for item in summary:
        key = (names.get(item["method"]), item["erasure_rate"])
        if key in ref:
            diffs.append({"method": item["method"], "rate": item["erasure_rate"], "ours": item["psnr_db_mean"],
                          "published": ref[key], "abs_diff": abs(item["psnr_db_mean"] - ref[key])})
    worst = max((d["abs_diff"] for d in diffs), default=None)
    return {"reference": reference_path, "compared": len(diffs), "max_abs_diff_db": worst, "rows": diffs}


def write_markdown(path: str, summary: List[dict], title: str, rates):
    methods = list(dict.fromkeys(r["method"] for r in summary))
    table = {(r["method"], r["erasure_rate"]): r for r in summary}
    lines = [f"# {title}", "", "Mean per-image PSNR (dB); in brackets the paired gain over uniform RS(96,64) "
             "(mean over channel seeds).", "",
             "| method | " + " | ".join(f"{r:g}" for r in rates) + " |", "|---|" + "---|" * len(rates)]
    for method in methods:
        cells = []
        for rate in rates:
            r = table.get((method, rate))
            cells.append("" if r is None else (f"{r['psnr_db_mean']:.2f}" if method == "uniform"
                                               else f"{r['psnr_db_mean']:.2f} ({r['gain_vs_uniform_db']:+.2f})"))
        lines.append(f"| {method} | " + " | ".join(cells) + " |")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=["val", "test"], required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--oracle_ranking_file", required=True)
    parser.add_argument("--head_checkpoint", default=None)
    parser.add_argument("--data_dir", default="./data")
    parser.add_argument("--dataset", default="cifar10")
    parser.add_argument("--split_seed", type=int, default=None)
    parser.add_argument("--max_images", type=int, default=None, help="default: 5000 for val, all for test")
    parser.add_argument("--seeds", default=None, help="default: 0,1,2 for val, 0,1,2,3,4 for test")
    parser.add_argument("--rates", default=",".join(map(str, TEST_RATES)))
    parser.add_argument("--design_rates", default=",".join(map(str, DESIGN_RATES)))
    parser.add_argument("--hill_evals", type=int, default=60, help="distinct layouts per local search")
    parser.add_argument("--profile", choices=["full", "multiseed"], default="full")
    parser.add_argument("--allocations", default=None, help="test stage: allocations.json (default: output_dir)")
    parser.add_argument("--reference_json", default=None)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--batch_size", type=int, default=250, help="must match the reference sweep (mask seeds)")
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--keep_trace", action="store_true")
    parser.add_argument("--save_per_image", action="store_true")
    args = parser.parse_args()
    args.design_rates = parse_csv(args.design_rates, float)
    if args.threads:
        torch.set_num_threads(args.threads)
    seed_everything(42)
    os.makedirs(args.output_dir, exist_ok=True)

    split = "val" if args.stage == "val" else "test"
    seeds = parse_csv(args.seeds or ("0,1,2" if split == "val" else "0,1,2,3,4"), int)
    max_images = args.max_images if args.max_images is not None else (5000 if split == "val" else None)
    from experiments.model_io import load_model_bundle
    has_attention = load_model_bundle(args.checkpoint, "cpu").has_attention
    sources = ["static:oracle", "energy"]
    if args.head_checkpoint:
        sources.append("predicted")
    if split == "test":
        sources += (["attention"] if has_attention else []) + ["oracle_perimage"]
    data_args = SimpleNamespace(
        device="cpu", checkpoint=args.checkpoint, split_seed=args.split_seed, dataset=args.dataset, split=split,
        name=f"coding_controls_{split}", oracle_ranking_file=args.oracle_ranking_file, rankings=None,
        importance=",".join(sources), data_dir=args.data_dir, max_images=max_images,
        head_checkpoint=args.head_checkpoint, batch_size=args.batch_size)
    data = prepare_data(data_args, sources=sources, note="coding_controls")
    sim = Simulator(data["bundle"], data["images"], data["prep"], args.batch_size)
    provenance = build_provenance(
        args=args, checkpoint_path=args.checkpoint, global_seed=42, device=torch.device("cpu"),
        extra_files={"ranking_oracle": args.oracle_ranking_file, **({"head": args.head_checkpoint}
                                                                     if args.head_checkpoint else {})},
        split_info={"dataset": args.dataset, "split": split, "split_seed": data["split_seed"]},
        extra={"images": len(data["images"]), "channel_seeds": list(seeds),
               "mask_protocol": "identical to experiments.eval_rs_uep (seed*100000+batch, 250-image batches)",
               "outcome_model": "coding.outcome (exact for systematic MDS erasure decoding)"})

    if args.stage == "val":
        weights = channel_weights(data["rankings"]["oracle"]["info"])
        result = stage_val(args, sim, weights, seeds)
        result["metadata"] = provenance
        path = os.path.join(args.output_dir, "allocations.json")
        write_json(path, result)
        print(f"saved {path}; surrogate fidelity {result['surrogate_fidelity']}")
        return

    allocation_path = args.allocations or os.path.join(args.output_dir, "allocations.json")
    with open(allocation_path, "r", encoding="utf-8") as handle:
        allocations = json.load(handle)
    rates = parse_csv(args.rates, float)
    methods = build_methods(args, allocations, sources, has_attention, args.profile)
    print(f"{len(data['images'])} test images, {len(methods)} methods x {len(seeds)} seeds x {len(rates)} rates")
    rows, per_image = stage_test(args, sim, methods, seeds, rates)
    summary = summarise(rows, per_image, seeds, rates)
    result = {"metadata": provenance, "allocations_file": allocation_path, "summary": summary, "rows": rows,
              "clean_psnr_mean": float(np.mean(data["prep"]["clean_psnr"]))}
    if args.reference_json:
        result["reference_check"] = reference_check(summary, args.reference_json)
        print(f"reference check: {result['reference_check']['compared']} cells, "
              f"max |diff| = {result['reference_check']['max_abs_diff_db']}")
    write_json(os.path.join(args.output_dir, "coding_controls_test.json"), result)
    write_markdown(os.path.join(args.output_dir, "coding_controls_test.md"), summary,
                   f"Coding controls, test split ({os.path.basename(os.path.dirname(args.checkpoint))})", rates)
    if args.save_per_image:
        np.savez_compressed(os.path.join(args.output_dir, "coding_controls_test.per_image.npz"),
                            **{f"{m}__s{s}__r{r:.3f}": v for (m, s, r), v in per_image.items()})
    print(f"saved {args.output_dir}")


if __name__ == "__main__":
    main()
