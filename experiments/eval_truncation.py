"""Importance-ordered truncation + one RS block, for any model and channel count, on a fixed 96-packet budget.

For a model with ``C`` latent channels (4 sixteen-byte packets each) the transmitter sends the ``m`` most
important channels in one systematic RS(96, 4m) block and drops the rest (``m = 24`` on a 24-channel model
is "no RS at all": 96 data packets). ``m`` is chosen per loss rate on the validation split, separately for
every ranking source; the test split is then evaluated once with the frozen choice. Masks and outcome model
are those of ``experiments/coding_controls.py`` (exact, shared with every other evaluator).

This puts very different systems on one axis at the same 1,536 transmitted bytes:
* the 1,024-byte model with RS (clean-trained or erasure-fine-tuned),
* a 1,536-byte (24-channel) model with no RS, clean-trained or erasure-fine-tuned,
* models trained with nested (tail) dropout, whose channel index is the importance order,
* smaller-bandwidth models (k/n = 1/12, 1/16) whose whole latent fits a stronger code.

    python -m experiments.eval_truncation --checkpoint results/nors/adjsccq_kn14_seed42_robust/adjsccq_erasure_robust.pth \\
        --oracle_ranking_file results/nors/adjsccq_kn14_seed42_robust/oracle_ranking.json --output_dir results/coding/trunc/x
"""
import argparse
import json
import os
from types import SimpleNamespace

import numpy as np
import torch

from experiments.coding_controls import MASTER_PACKETS, TEST_RATES, Simulator, truncation_layout
from experiments.eval_rs_uep import parse_csv, prepare_data
from experiments.model_io import load_model_bundle
from experiments.reproducibility import build_provenance, seed_everything, seed_statistics, write_json


def run_split(args, split: str, sources, seeds, rates, keep_choice=None):
    bundle = load_model_bundle(args.checkpoint, "cpu")
    channels = bundle.channels
    packets_per_channel = bundle.symbols_per_channel // 16
    rankings = [f"oracle={args.oracle_ranking_file}"] + ([f"index={args.index_ranking}"] if args.index_ranking else [])
    data_args = SimpleNamespace(
        device="cpu", checkpoint=args.checkpoint, split_seed=None, dataset="cifar10", split=split,
        name=f"eval_truncation_{split}", oracle_ranking_file=None, rankings=",".join(rankings),
        importance=",".join(sources), data_dir=args.data_dir,
        max_images=(args.val_images if split == "val" else None), head_checkpoint=None, batch_size=250)
    data = prepare_data(data_args, sources=list(sources), note="eval_truncation")
    sim = Simulator(data["bundle"], data["images"], data["prep"], 250)
    max_keep = min(channels, MASTER_PACKETS // packets_per_channel)
    results = {}
    for source in sources:
        for rate in rates:
            keeps = range(1, max_keep + 1) if keep_choice is None else [keep_choice[source][f"{rate:g}"]]
            for keep in keeps:
                layout = truncation_layout(keep, channels, packets_per_channel)
                values = [float(sim.run(layout, source, seed, rate)[0].mean()) for seed in seeds]
                results[(source, rate, keep)] = values
    return results, data, channels


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--oracle_ranking_file", required=True)
    parser.add_argument("--index_ranking", default=None, help="ranking file 0,1,..,C-1 (tail-drop models); "
                                                               "written automatically with --index_order")
    parser.add_argument("--index_order", action="store_true", help="also rank channels by index (ordered models)")
    parser.add_argument("--sources", default="static:oracle,energy")
    parser.add_argument("--data_dir", default="./data")
    parser.add_argument("--val_images", type=int, default=5000)
    parser.add_argument("--rates", default=",".join(map(str, TEST_RATES)))
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)
    seed_everything(42)
    os.makedirs(args.output_dir, exist_ok=True)
    sources = list(parse_csv(args.sources))
    if args.index_order:
        channels = load_model_bundle(args.checkpoint, "cpu").channels
        args.index_ranking = os.path.join(args.output_dir, "index_ranking.json")
        write_json(args.index_ranking, {"ranking_channels_most_to_least_important": list(range(channels)),
                                        "source_split": "train", "note": "channel index order (tail-drop training)"})
        sources.append("static:index")
    rates = parse_csv(args.rates, float)

    val, _, channels = run_split(args, "val", sources, (0, 1, 2), rates)
    choice = {}
    for source in sources:
        choice[source] = {}
        for rate in rates:
            options = {keep: np.mean(v) for (s, r, keep), v in val.items() if s == source and r == rate}
            choice[source][f"{rate:g}"] = int(max(options, key=options.get))
    test, data, _ = run_split(args, "test", sources, (0, 1, 2, 3, 4), rates, choice)
    summary = []
    for (source, rate, keep), values in sorted(test.items()):
        stats = seed_statistics(values)
        summary.append({"source": source, "erasure_rate": rate, "keep_channels": keep,
                        "psnr_db_mean": stats["mean"], "ci95_seeds": stats["ci95_half_width"]})
    out = {
        "checkpoint": args.checkpoint, "channels": channels, "clean_psnr_test": float(np.mean(data["prep"]["clean_psnr"])),
        "selected_keep_on_val": choice, "summary": summary,
        "val_curves": [{"source": s, "erasure_rate": r, "keep_channels": k, "psnr_db_mean": float(np.mean(v))}
                       for (s, r, k), v in sorted(val.items())],
        "metadata": build_provenance(args=args, checkpoint_path=args.checkpoint, global_seed=42,
                                     device=torch.device("cpu"),
                                     split_info={"dataset": "cifar10", "split": "val->test"}),
    }
    path = os.path.join(args.output_dir, "truncation.json")
    write_json(path, out)
    for row in summary:
        print(f"{row['source']:>14} p={row['erasure_rate']:<5g} keep={row['keep_channels']:>2}  {row['psnr_db_mean']:.2f} dB")
    print(f"saved {path}")


if __name__ == "__main__":
    main()
