"""Importance-ordered truncation under Gilbert-Elliott burst losses (same mean loss, growing burst length).

One RS(96, 4m) codeword spans all 96 packets, so the packet order inside it is irrelevant. Bursts act only
through the per-image number of lost packets, whose spread grows with the burst length, so the code fails
more often at the same mean loss. Compared, on identical timeline masks:

* uniform RS(96,64);
* the hand-tiered 25/50/25 scheme with round-robin interleaving (the best burst layout of the earlier study);
* truncation with the depth chosen for i.i.d. loss at the same mean (burst-agnostic);
* truncation with the depth chosen on validation for the burst channel itself (burst-aware).

    python -m experiments.eval_burst_truncation --checkpoint results/gpu/models/seed42/best_val.pth \\
        --oracle_ranking_file results/gpu/models/seed42/oracle_ranking.json \\
        --allocations results/coding/seed42/allocations.json --output_dir results/coding/burst_seed42
"""
import argparse
import json
import os
from types import SimpleNamespace

import numpy as np
import torch

from coding.erasure_channel import GilbertElliottChannel
from coding.interleave import transmission_slots
from coding.outcome import layout_from_scheme
from coding.rs_pipeline import SCHEME_CANDIDATES
from experiments.coding_controls import MASTER_PACKETS, Simulator, truncation_layout
from experiments.eval_rs_uep import parse_csv, prepare_data
from experiments.reproducibility import build_provenance, seed_everything, seed_statistics, write_json


def timeline_masks(n: int, avg_loss: float, burst: float, seed: int, batch_size: int = 250) -> torch.Tensor:
    """(N, 96) timeline masks; burst <= 1 is i.i.d. Bernoulli. Seeded per (seed, batch) like the other sweeps."""
    parts = []
    channel = None if burst <= 1 else GilbertElliottChannel.from_average_loss(avg_loss, burst)
    for b, start in enumerate(range(0, n, batch_size)):
        stop = min(start + batch_size, n)
        generator = torch.Generator().manual_seed(seed * 100000 + b + 7_000_000)
        if channel is None:
            parts.append(torch.rand(stop - start, MASTER_PACKETS, generator=generator) < avg_loss)
        else:
            parts.append(channel.sample_mask(stop - start, MASTER_PACKETS, generator))
    return torch.cat(parts)


def load_sim(args, split):
    data_args = SimpleNamespace(
        device="cpu", checkpoint=args.checkpoint, split_seed=None, dataset="cifar10", split=split,
        name=f"eval_burst_truncation_{split}", oracle_ranking_file=args.oracle_ranking_file, rankings=None,
        importance="static:oracle", data_dir=args.data_dir, max_images=(5000 if split == "val" else None),
        head_checkpoint=None, batch_size=250)
    data = prepare_data(data_args, sources=["static:oracle"], note="eval_burst_truncation")
    return Simulator(data["bundle"], data["images"], data["prep"], 250)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--oracle_ranking_file", required=True)
    parser.add_argument("--allocations", required=True, help="allocations.json of coding_controls (i.i.d. depths)")
    parser.add_argument("--avg_losses", default="0.35,0.45")
    parser.add_argument("--bursts", default="1,2,4,8,16")
    parser.add_argument("--data_dir", default="./data")
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)
    seed_everything(42)
    os.makedirs(args.output_dir, exist_ok=True)
    losses, bursts = parse_csv(args.avg_losses, float), parse_csv(args.bursts, float)
    with open(args.allocations, "r", encoding="utf-8") as handle:
        designs = json.load(handle)["designs"]
    iid_keep = {loss: designs[f"{loss:g}"]["trunc_keep"] for loss in losses}

    val = load_sim(args, "val")
    burst_keep = {}
    for loss in losses:
        for burst in bursts:
            scores = {}
            for keep in range(1, 17):
                layout = truncation_layout(keep)
                scores[keep] = np.mean([val.run(layout, "static:oracle", s, 0, mask=timeline_masks(val.n, loss, burst, s))[0].mean()
                                        for s in (0, 1, 2)])
            burst_keep[(loss, burst)] = max(scores, key=scores.get)
            print(f"[val] loss {loss} burst {burst}: keep {burst_keep[(loss, burst)]} (iid design {iid_keep[loss]})",
                  flush=True)

    test = load_sim(args, "test")
    tiered = layout_from_scheme(SCHEME_CANDIDATES["three_tier_25_50_25"])
    slots = transmission_slots(SCHEME_CANDIDATES["three_tier_25_50_25"], "round_robin")
    rows = []
    for loss in losses:
        for burst in bursts:
            values = {"uniform": [], "three_tier_25_50_25_rr@oracle": [], "trunc_iid_depth@oracle": [],
                      "trunc_burst_depth@oracle": []}
            for seed in range(5):
                timeline = timeline_masks(test.n, loss, burst, seed)
                values["uniform"].append(test.run(layout_from_scheme(SCHEME_CANDIDATES["uniform"]), None, seed, 0,
                                                  mask=timeline)[0].mean())
                values["three_tier_25_50_25_rr@oracle"].append(
                    test.run(tiered, "static:oracle", seed, 0, mask=timeline[:, slots])[0].mean())
                values["trunc_iid_depth@oracle"].append(
                    test.run(truncation_layout(iid_keep[loss]), "static:oracle", seed, 0, mask=timeline)[0].mean())
                values["trunc_burst_depth@oracle"].append(
                    test.run(truncation_layout(burst_keep[(loss, burst)]), "static:oracle", seed, 0,
                             mask=timeline)[0].mean())
            for method, vals in values.items():
                stats = seed_statistics([float(v) for v in vals])
                rows.append({"avg_loss": loss, "burst": burst, "method": method, "psnr_db_mean": stats["mean"],
                             "ci95_seeds": stats["ci95_half_width"],
                             "keep": {"trunc_iid_depth@oracle": iid_keep[loss],
                                      "trunc_burst_depth@oracle": burst_keep[(loss, burst)]}.get(method)})
                print(f"[test] loss {loss} burst {burst} {method}: {stats['mean']:.2f}", flush=True)
    out = {"rows": rows, "burst_keep_val": {f"{k[0]:g}/{k[1]:g}": v for k, v in burst_keep.items()},
           "iid_keep": {f"{k:g}": v for k, v in iid_keep.items()},
           "metadata": build_provenance(args=args, checkpoint_path=args.checkpoint, global_seed=42,
                                        device=torch.device("cpu"), split_info={"dataset": "cifar10",
                                                                                "split": "val->test"})}
    write_json(os.path.join(args.output_dir, "burst_truncation.json"), out)
    print("saved", args.output_dir)


if __name__ == "__main__":
    main()
