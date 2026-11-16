"""Figures, tables and number macros for the paper draft, generated only from result files.

Writes ``paper/figures/*.pdf|png``, ``paper/generated_numbers.tex`` (``\\newcommand`` macros used in the
text, so no number is typed by hand) and ``paper/generated_tables.tex``. Missing inputs are skipped and
reported; their macros expand to a visible ``\\TBD{...}`` marker.

    python -m experiments.paper_figures
"""
import glob
import json
import os
from typing import Dict, List, Optional

import numpy as np

from experiments import plotting  # noqa: F401  (rcParams)
import matplotlib.pyplot as plt  # noqa: E402

from coding.outcome import Layout, grouped_layout, pet_layout  # noqa: E402
from experiments.allocation import loss_weighting, surrogate_cost, symbol_weights_from_channels  # noqa: E402

PAPER = "paper"
FIG = os.path.join(PAPER, "figures")
# Validated categorical palette (dataviz reference instance, light mode); gray = the uniform-RS reference.
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GRAY = "#6b6a66"
COLUMN = 3.5

macros: Dict[str, str] = {}
missing: List[str] = []


def macro(name: str, value, fmt: str = "{:.2f}"):
    text = fmt.format(value) if isinstance(value, (int, float, np.floating)) else str(value)
    if text.startswith("-"):
        text = "$-$" + text[1:]   # a real minus sign that cannot break across lines
    macros[name] = text


def load(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        missing.append(path)
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def table(summary, method, key="psnr_db_mean"):
    return {r["erasure_rate"]: r[key] for r in summary if r["method"] == method}


def word(rate: float) -> str:
    return {0.0: "Zero", 0.1: "Ten", 0.2: "Twenty", 0.3: "Thirty", 0.35: "ThirtyFive", 0.4: "Forty",
            0.45: "FortyFive", 0.5: "Fifty"}[round(rate, 2)]


# ----------------------------------------------------------------------------------------------
def fig_profiles():
    """Sorted per-channel share of total LOO damage, every converged seed, both architectures."""
    families = {
        "ADJSCC-Q (with attention)": sorted(glob.glob("results/gpu/models/seed*/oracle_ranking.json")),
        "DeepJSCC-Q (no attention)": sorted(glob.glob("results/g1t4/models/deepjsccq_seed*/oracle_ranking.json")),
    }
    # did not converge (best epoch < 50): ADJSCC-Q seed 2024 (published ledger), DeepJSCC-Q T4 seeds 42 and 13
    excluded = {"models/seed2024", "deepjsccq_seed42", "deepjsccq_seed13"}
    fig, ax = plt.subplots(figsize=(COLUMN, 2.3))
    stats = {}
    for (label, files), color, marker in zip(families.items(), C, ("o", "s")):
        shares = []
        for path in files:
            if any(tag in path.replace("\\", "/") for tag in excluded):
                continue
            data = load(path)
            damage = np.sort(np.asarray(data["mse_increase_by_channel"]))[::-1]
            share = damage / damage.sum()
            shares.append(share)
            ax.plot(np.arange(1, len(share) + 1), share, color=color, lw=0.8, alpha=0.35)
        if not shares:
            missing.append(f"profiles for {label}")
            continue
        mean = np.mean(shares, axis=0)
        ax.plot(np.arange(1, len(mean) + 1), mean, color=color, lw=2, marker=marker, ms=4,
                label=f"{label}, {len(shares)} seeds")
        top4 = [s[:4].sum() for s in shares]
        stats[label] = (len(shares), min(top4), max(top4))
    ax.axhline(1 / 16, color=GRAY, lw=1, ls=":", label="equal share (1/16)")
    ax.set_xticks([1, 4, 8, 12, 16])
    ax.set_xlabel("channel rank (most damaging first)")
    ax.set_ylabel("share of LOO MSE damage")
    ax.legend(frameon=False, loc="upper right")
    plotting.save_figure(fig, os.path.join(FIG, "fig_profiles"))
    for label, (n, lo, hi) in stats.items():
        key = "Adj" if label.startswith("ADJ") else "Deep"
        macro(f"TopFourShareMin{key}", 100 * lo, "{:.0f}")
        macro(f"TopFourShareMax{key}", 100 * hi, "{:.0f}")
        macro(f"Seeds{key}", n, "{:d}")


# ----------------------------------------------------------------------------------------------
def fig_main(controls: dict, digital: Optional[dict], digital_sel: Optional[dict]):
    summary = controls["summary"]
    rates = sorted({r["erasure_rate"] for r in summary})
    series = [
        ("uniform", "uniform RS(96,64)", GRAY, "o", "-"),
        ("three_tier_25_50_25@oracle", "hand-tiered UEP 25/50/25", C[0], "s", "--"),
        ("opt_trunc@random", "opt. truncation, random order", C[2], "v", "-."),
        ("opt_trunc@attention", "opt. truncation, attention order", C[3], "D", "-."),
        ("opt_trunc@oracle", "opt. truncation, LOO order", C[1], "^", "-"),
    ]
    fig, ax = plt.subplots(figsize=(COLUMN, 2.7))
    for method, label, color, marker, ls in series:
        values = table(summary, method)
        if not values:
            continue
        ax.plot(rates, [values[r] for r in rates], color=color, marker=marker, ms=4, lw=1.6, ls=ls, label=label)
    switching = load("results/coding/trunc/kn_1_12/truncation.json")
    if switching:
        points = {r["erasure_rate"]: r["psnr_db_mean"] for r in switching["summary"] if r["source"] == "static:oracle"}
        xs = sorted(points)
        ax.plot(xs, [points[x] for x in xs], color=C[5], marker="x", ms=4, lw=1.4, ls="--",
                label="8-channel model + RS(96,32)")
    if digital and digital_sel:
        sel = digital_sel["selected_k"]["webp"]
        points = {(r["erasure_rate"]): r["psnr_db_mean"] for r in digital["summary"]
                  if r["codec"] == "webp" and r["k_data_packets"] == sel.get(f"{r['erasure_rate']:g}")}
        if points:
            xs = sorted(points)
            ax.plot(xs, [points[x] for x in xs], color=C[6], marker="P", ms=4, lw=1.6, ls=":",
                    label="WebP + rate-adaptive RS")
    ax.set_xlabel("packet loss rate $p$")
    ax.set_ylabel("PSNR (dB)")
    ax.legend(frameon=False, fontsize=6.5, loc="lower left")
    plotting.save_figure(fig, os.path.join(FIG, "fig_main"))


def numbers_main(controls: dict, prefix: str = ""):
    summary = controls["summary"]
    for method, name in [("uniform", "Uniform"), ("three_tier_25_50_25@oracle", "HandTier"),
                         ("three_tier_25_50_25@random", "HandTierRandom"),
                         ("three_tier_25_50_25@attention", "HandTierAttention"),
                         ("three_tier_25_50_25@oracle_perimage", "HandTierPerImage"),
                         ("two_tier_50_50@unsorted", "TwoTierUnsorted"),
                         ("opt_trunc@oracle", "TruncOracle"), ("opt_trunc@energy", "TruncEnergy"),
                         ("opt_trunc@predicted", "TruncHead"), ("opt_trunc@attention", "TruncAttention"),
                         ("opt_trunc@random", "TruncRandom"), ("opt_grouped@oracle", "OptGrouped"),
                         ("opt_pet@oracle", "OptPet"), ("opt_selector@oracle", "Selector"),
                         ("robust_grouped@oracle", "RobustGrouped"), ("robust_pet@oracle", "RobustPet"),
                         ("pet_twin_three_tier_25_50_25@oracle", "PetTwin"),
                         ("uniform_pet_diag@unsorted", "UniformDiag"), ("no_rs", "NoRS"),
                         ("gradfec_top8_drop4@oracle", "GradFec")]:
        psnr, gain = table(summary, method), table(summary, method, "gain_vs_uniform_db")
        for rate, value in psnr.items():
            macro(f"{prefix}{name}{word(rate)}", value)
            if method != "uniform":
                macro(f"{prefix}{name}Gain{word(rate)}", gain[rate], "{:+.2f}")


def fig_mismatch(controls: dict):
    summary = controls["summary"]
    rates = sorted({r["erasure_rate"] for r in summary})
    fig, ax = plt.subplots(figsize=(COLUMN, 2.4))
    base = table(summary, "uniform")
    plotted = 0
    for (design, color, marker) in zip(("0.3", "0.4", "0.5"), (C[0], C[1], C[2]), ("s", "^", "v")):
        values = table(summary, f"design{design}_grouped@oracle")
        if values:
            ax.plot(rates, [values[r] - base[r] for r in rates], color=color, marker=marker, ms=4, lw=1.4,
                    label=f"designed for $p={design}$")
            plotted += 1
    for method, label, color, ls in (("opt_selector@oracle", "designed for the true $p$", C[6], "-"),
                                     ("robust_grouped@oracle", "one design for $p\\in[0.1,0.5]$", C[3], "--")):
        values = table(summary, method)
        if values:
            ax.plot(rates, [values[r] - base[r] for r in rates], color=color, lw=2, ls=ls, label=label)
    ax.axhline(0, color=GRAY, lw=1)
    ax.set_xlabel("actual packet loss rate $p$")
    ax.set_ylabel("gain over uniform RS (dB)")
    ax.legend(frameon=False, fontsize=6.5)
    if plotted:
        plotting.save_figure(fig, os.path.join(FIG, "fig_mismatch"))
    else:
        plt.close(fig)


def layout_from_name(name: str) -> Optional[Layout]:
    """Rebuild a layout from its printed name (grouped[96/52,0/12], trunc[13], pet[...]-dropD-diag)."""
    if name.startswith("trunc["):
        keep = int(name[6:-1])
        return grouped_layout([(96, 4 * keep)] + ([(0, 4 * (16 - keep))] if keep < 16 else []))
    if name.startswith("grouped["):
        tiers = [tuple(int(v) for v in t.split("/")) for t in name[8:-1].split(",")]
        return grouped_layout(tiers)
    if name.startswith("pet["):
        body, _, rest = name[4:].partition("]")
        dropped = 0
        placement = "diagonal" if rest.endswith("-diag") else "column"
        if "-drop" in rest:
            dropped = int(rest.split("-drop")[1].split("-")[0])
        return pet_layout([int(v) for v in body.split(",")], 96, 16, dropped, placement)
    return None


def fig_surrogate(controls: dict, ranking_file: str):
    """Additive-MSE surrogate vs simulated mean MSE, every static-ranked test cell."""
    ranking = load(ranking_file)
    if ranking is None:
        return
    weights = np.asarray(ranking["mse_increase_by_channel"])[ranking["ranking_channels_most_to_least_important"]]
    sym_w = symbol_weights_from_channels(weights, 64)
    clean = np.mean([r["mse_mean"] for r in controls["rows"] if r["method"] == "uniform" and r["erasure_rate"] == 0.0])
    cells: Dict = {}
    for row in controls["rows"]:
        if row["source"] != "static:oracle" or row["erasure_rate"] == 0.0:
            continue
        cells.setdefault((row["layout"], row["erasure_rate"]), []).append(row["mse_mean"])
    pred, sim = [], []
    for (name, rate), values in cells.items():
        layout = layout_from_name(name)
        if layout is None:
            continue
        pred.append(clean + surrogate_cost(layout, sym_w, loss_weighting([rate])))
        sim.append(float(np.mean(values)))
    if not pred:
        return
    pred, sim = np.array(pred), np.array(sim)
    fig, ax = plt.subplots(figsize=(COLUMN, 2.4))
    ax.scatter(1e3 * pred, 1e3 * sim, s=14, color=C[0], edgecolor="white", linewidth=0.5, zorder=3)
    lim = [0, 1e3 * max(pred.max(), sim.max()) * 1.05]
    ax.plot(lim, lim, color=GRAY, lw=1, ls="--", label="$y=x$")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("predicted MSE ($\\times 10^{-3}$), eq. (2)")
    ax.set_ylabel("simulated MSE ($\\times 10^{-3}$)")
    ax.legend(frameon=False)
    plotting.save_figure(fig, os.path.join(FIG, "fig_surrogate"))
    rel = np.abs(pred / sim - 1)
    from experiments.stats_utils import spearman
    macro("SurrogateSpearman", spearman(pred.tolist(), sim.tolist()), "{:.3f}")
    macro("SurrogateMedianRelErr", 100 * float(np.median(rel)), "{:.1f}")
    macro("SurrogateCells", len(pred), "{:d}")


CONVERGED = {"adjsccq_seed42", "adjsccq_seed100", "adjsccq_seed7", "adjsccq_seed13", "adjsccq_seed21",
             "deepjsccq_seed100", "deepjsccq_seed7", "deepjsccq_seed21"}
MODEL_LABEL = {"adjsccq": "ADJSCC-Q", "deepjsccq": "DeepJSCC-Q"}


def multiseed_numbers():
    """Table: every model at 40% loss (truncation evaluator; depth chosen on validation per ranking)."""
    lines = [r"\begin{tabular}{lrrrrrrr}", r"\toprule",
             r"model & clean & uniform & hand-tiered & \multicolumn{4}{c}{opt.\ truncation, order:} \\",
             r" & & & LOO & LOO & energy & attention & random \\", r"\midrule"]
    gaps = {"adjsccq": [], "deepjsccq": []}
    for path in sorted(glob.glob("results/coding/trunc/*_seed*/truncation.json")):
        name = os.path.basename(os.path.dirname(path))
        if name not in CONVERGED:
            continue
        data = load(path)
        rows = {(r["source"], r["erasure_rate"]): r["psnr_db_mean"] for r in data["summary"]}
        cell = lambda key: rows.get((key, 0.4))  # noqa: E731
        values = [cell("fixed:uniform"), cell("fixed:three_tier_25_50_25@oracle"), cell("static:oracle"),
                  cell("energy"), cell("attention"), cell("random")]
        arch, _, seed = name.partition("_seed")
        if values[2] is not None and values[0] is not None:
            gaps[arch].append(values[2] - values[0])
        text = ["--" if v is None else f"{v:.2f}" for v in values]
        lines.append(f"{MODEL_LABEL[arch]} s{seed} & {data['clean_psnr_test']:.2f} & " + " & ".join(text) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(PAPER, "generated_tables.tex"), "w", encoding="utf-8") as handle:
        handle.write("% generated by experiments/paper_figures.py -- do not edit\n" + "\n".join(lines) + "\n")
    for arch, key in (("adjsccq", "Adj"), ("deepjsccq", "Deep")):
        if gaps[arch]:
            macro(f"TruncGainMin{key}", min(gaps[arch]), "{:+.2f}")
            macro(f"TruncGainMax{key}", max(gaps[arch]), "{:+.2f}")


def digital_numbers(digital, digital_sel):
    if not digital or not digital_sel:
        return
    for codec, name in (("webp", "Webp"), ("jpeg", "Jpeg"), ("jpeg2000", "Jtwok")):
        sel = digital_sel["selected_k"][codec]
        for r in digital["summary"]:
            if r["codec"] != codec:
                continue
            if r["k_data_packets"] == sel.get(f"{r['erasure_rate']:g}"):
                macro(f"{name}Adaptive{word(r['erasure_rate'])}", r["psnr_db_mean"])
            if r["k_data_packets"] == 64:
                macro(f"{name}Fixed{word(r['erasure_rate'])}", r["psnr_db_mean"])


def extra_numbers(controls: Optional[dict]):
    """Macros that combine several result files (reference check, multi-tier, mismatch, other models)."""
    if controls:
        check = controls.get("reference_check") or {}
        if check.get("max_abs_diff_db") is not None:
            macro("ReferenceMaxDiff", check["max_abs_diff_db"], "{:.3f}")
            macro("ReferenceCells", check["compared"], "{:d}")
        s = controls["summary"]
        hand, trunc = table(s, "three_tier_25_50_25@oracle"), table(s, "opt_trunc@oracle")
        if 0.4 in hand and 0.4 in trunc:
            macro("TruncOverHandForty", trunc[0.4] - hand[0.4])
        design = table(s, "design0.4_grouped@oracle", "gain_vs_uniform_db")
        if design:
            macro("DesignFortyAtZeroLoss", -design[0.0])
            macro("DesignFortyAtFifty", design[0.5], "{:+.2f}")
    allocations = load("results/coding/seed42/allocations.json")
    if allocations:
        gains, pet_gaps = [], []
        for label, entry in allocations["designs"].items():
            check = entry.get("multitier_check")
            if check:
                gains.append(check["best_val_psnr"] - entry["trunc_val_psnr"])
            pet_gaps.append(abs(entry["pet_val_psnr"] - entry["trunc_val_psnr"]))
        if gains:
            macro("MultiTierMaxGain", max(gains))
        macro("PetVsTruncMax", max(pet_gaps))
    for folder, name in (("kn_1_12", "KnTwelve"), ("kn_1_16", "KnSixteen")):
        data = load(f"results/coding/trunc/{folder}/truncation.json")
        if data:
            rows = {r["erasure_rate"]: r["psnr_db_mean"] for r in data["summary"] if r["source"] == "static:oracle"}
            for rate, value in rows.items():
                macro(f"{name}{word(rate)}", value)
            macro(f"{name}Clean", data["clean_psnr_test"])
    ordered = load("results/coding/trunc/adjsccq_td05/truncation.json")
    plain = load("results/coding/trunc/adjsccq_seed42/truncation.json")
    if ordered:
        rows = {r["erasure_rate"]: r["psnr_db_mean"] for r in ordered["summary"] if r["source"] == "static:index"}
        for rate, value in rows.items():
            macro(f"OrderedTrunc{word(rate)}", value)
        if plain:
            macro("OrderedCleanCost", plain["clean_psnr_test"] - ordered["clean_psnr_test"])
    status = load("results/kaggle/rs-uep-jscc-nors2-adjsccq/outputs/status.json")
    if status and status.get("nors2_selected"):
        macro("NoRsBestValClean", max(c[0] for c in status["nors2_selected"]["candidates"]))
    nors = load("results/coding/trunc/kn14_best_robust_adjsccq/truncation.json")
    if nors:
        rows = {r["erasure_rate"]: r for r in nors["summary"] if r["source"] == "static:oracle"}
        for rate, row in rows.items():
            macro(f"NoRsJscc{word(rate)}", row["psnr_db_mean"])
        macro("NoRsJsccClean", nors["clean_psnr_test"])


def write_macros():
    lines = ["% generated by experiments/paper_figures.py -- do not edit",
             r"\providecommand{\TBD}[1]{\textbf{\color{red}[#1]}}"]
    for name, value in sorted(macros.items()):
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    with open(os.path.join(PAPER, "generated_numbers.tex"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    os.makedirs(FIG, exist_ok=True)
    fig_profiles()
    controls = load("results/coding/seed42/coding_controls_test.json")
    digital = load("results/coding/digital/digital_adaptive_test.json")
    digital_sel = load("results/coding/digital/digital_adaptive_val.json")
    if controls:
        fig_main(controls, digital, digital_sel)
        numbers_main(controls)
        fig_mismatch(controls)
        fig_surrogate(controls, "results/gpu/models/seed42/oracle_ranking.json")
        macro("CleanPsnr", controls["clean_psnr_mean"])
        allocations = load("results/coding/seed42/allocations.json")
        if allocations:
            for label, entry in allocations["designs"].items():
                if label != "robust":
                    macro(f"TruncKeep{word(float(label))}", entry["trunc_keep"], "{:d}")
    digital_numbers(digital, digital_sel)
    extra_numbers(controls)
    multiseed_numbers()
    write_macros()
    print(f"{len(macros)} macros; missing inputs: {missing or 'none'}")


if __name__ == "__main__":
    main()
