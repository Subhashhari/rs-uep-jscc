"""Separation baseline with the SAME freedom as the optimised Deep JSCC allocation: rate-adaptive RS.

``experiments/eval_digital_baseline.py`` gives every codec the full 1,024-byte data budget and one
RS(96, 64) block, so it collapses beyond ~33% loss by construction. Once the Deep JSCC transmitter may
trade source bytes for parity at a known loss rate (``experiments/coding_controls.py``), a fair digital
baseline must be allowed the same trade: compress to ``16 k - 2`` bytes (2-byte length header) and send
RS(96, k) over the same 96 sixteen-byte packets, with ``k`` chosen per loss rate **on validation**.

Exactness and fairness:
* identical loss masks to every other evaluator (same seeds, same 250-image batches, ``coding.outcome``);
* a failed RS block keeps the systematic packets that arrived; lost ones are zero-filled and the codec
  decodes whatever it can (truncated streams allowed), otherwise mid-grey -- the most favourable choice
  for the baseline, as in ``eval_digital_baseline``;
* the rate search picks the highest quality that fits the budget.

    python -m experiments.eval_digital_adaptive --split val --output_dir results/coding/digital
    python -m experiments.eval_digital_adaptive --split test --selection results/coding/digital/digital_adaptive_val.json \\
        --output_dir results/coding/digital
"""
import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import torch

from coding.outcome import grouped_layout, lost_stream_symbols
from data.datasets import is_official_test, load_image_tensor
from experiments.eval_digital_baseline import GREY, decode_stream, fit_to_budget, pack, unpack
from experiments.eval_rs_uep import parse_csv
from experiments.reproducibility import build_provenance, log_test_access, seed_everything, seed_statistics, write_json

PACKETS, PACKET_SIZE = 96, 16
DEFAULT_K = (8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64)
RATES = (0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5)


def _psnr(a: np.ndarray, b: np.ndarray) -> float:
    return float(10 * np.log10(1.0 / max(float(np.mean((a - b) ** 2)), 1e-10)))


def _encode_one(job):
    image, codec, ks = job
    out = {}
    for k in ks:
        budget = PACKET_SIZE * k - 2
        stream = fit_to_budget(image, codec, budget)
        if stream is None:
            out[k] = (None, 10 * np.log10(1.0 / float(np.mean((image - GREY) ** 2))))
            continue
        decoded = decode_stream(stream, codec, image.shape)
        out[k] = (stream, _psnr(decoded, image) if decoded is not None else _psnr(np.full_like(image, GREY), image))
    return out


def _damaged_one(job):
    image, codec, data, lost = job
    decoded = decode_stream(unpack(data, lost), codec, image.shape)
    return _psnr(decoded if decoded is not None else np.full_like(image, GREY), image)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", choices=["val", "test"], required=True)
    parser.add_argument("--data_dir", default="./data")
    parser.add_argument("--split_seed", type=int, default=42)
    parser.add_argument("--max_images", type=int, default=None, help="default: 5000 for val, all for test")
    parser.add_argument("--codecs", default="jpeg,webp,jpeg2000")
    parser.add_argument("--k_values", default=",".join(map(str, DEFAULT_K)))
    parser.add_argument("--rates", default=",".join(map(str, RATES)))
    parser.add_argument("--seeds", default=None, help="default: 0,1,2 for val, 0,1,2,3,4 for test")
    parser.add_argument("--selection", default=None, help="test: the validation result whose k per rate is used")
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    parser.add_argument("--batch_size", type=int, default=250)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    seed_everything(42)
    os.makedirs(args.output_dir, exist_ok=True)
    codecs, rates = parse_csv(args.codecs), parse_csv(args.rates, float)
    seeds = parse_csv(args.seeds or ("0,1,2" if args.split == "val" else "0,1,2,3,4"), int)
    max_images = args.max_images if args.max_images is not None else (5000 if args.split == "val" else None)
    selection = None
    if args.split == "test":
        if not args.selection:
            raise SystemExit("--split test needs --selection (the validation result)")
        with open(args.selection, "r", encoding="utf-8") as handle:
            selection = json.load(handle)["selected_k"]
        log_test_access("experiments.eval_digital_adaptive", None, note="rate-adaptive digital baseline")
    ks = parse_csv(args.k_values, int)
    if selection is not None:   # only the selected k (plus the fixed RS(96,64) reference) are needed on test
        ks = tuple(sorted({64} | {int(k) for per_codec in selection.values() for k in per_codec.values()}))
    images = load_image_tensor("cifar10", args.split, args.data_dir, max_images, args.split_seed).numpy()
    n = len(images)
    print(f"{n} images ({args.split}); codecs {codecs}; k {ks}; rates {rates}; seeds {seeds}", flush=True)

    # loss masks identical to eval_rs_uep / coding_controls
    def draws(seed):
        parts = []
        for b, start in enumerate(range(0, n, args.batch_size)):
            stop = min(start + args.batch_size, n)
            parts.append(torch.rand(stop - start, PACKETS, generator=torch.Generator().manual_seed(seed * 100000 + b)))
        return torch.cat(parts)

    uniforms = {seed: draws(seed) for seed in seeds}
    results, clean = {}, {}
    started = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for codec in codecs:
            encoded = list(pool.map(_encode_one, [(images[i], codec, ks) for i in range(n)], chunksize=64))
            print(f"[{codec}] encoded at {len(ks)} budgets ({time.time() - started:.0f} s)", flush=True)
            for k in ks:
                clean_psnr = np.array([encoded[i][k][1] for i in range(n)])
                clean[(codec, k)] = float(clean_psnr.mean())
                data = np.stack([pack(encoded[i][k][0] or b"", PACKET_SIZE * k) for i in range(n)])
                layout = grouped_layout([(PACKETS, k)])
                for rate in rates:
                    if selection is not None and int(selection[codec].get(f"{rate:g}", -1)) != k and k != 64:
                        continue
                    for seed in seeds:
                        lost = lost_stream_symbols(layout, uniforms[seed] < rate).numpy()
                        psnr = clean_psnr.copy()
                        damaged = np.flatnonzero(lost.any(axis=1))
                        if len(damaged):
                            jobs = [(images[i], codec, data[i], lost[i]) for i in damaged]
                            psnr[damaged] = list(pool.map(_damaged_one, jobs, chunksize=32))
                        results[(codec, k, rate, seed)] = float(psnr.mean())
                print(f"[{codec}] k={k}: clean {clean[(codec, k)]:.2f} dB ({time.time() - started:.0f} s)", flush=True)

    summary = []
    for (codec, k, rate) in sorted({key[:3] for key in results}):
        values = [results[(codec, k, rate, s)] for s in seeds]
        stats = seed_statistics(values)
        summary.append({"codec": codec, "k_data_packets": k, "payload_bytes": PACKET_SIZE * k - 2,
                        "erasure_rate": rate, "psnr_db_mean": stats["mean"], "ci95_seeds": stats["ci95_half_width"],
                        "clean_psnr_db": clean[(codec, k)]})
    out = {"summary": summary, "seeds": list(seeds), "images": n, "split": args.split}
    if args.split == "val":
        selected = {}
        for codec in codecs:
            selected[codec] = {}
            for rate in rates:
                options = [r for r in summary if r["codec"] == codec and r["erasure_rate"] == rate]
                selected[codec][f"{rate:g}"] = max(options, key=lambda r: r["psnr_db_mean"])["k_data_packets"]
        out["selected_k"] = selected
    out["metadata"] = build_provenance(args=args, global_seed=42, split_info={"dataset": "cifar10", "split": args.split,
                                                                               "split_seed": args.split_seed})
    path = os.path.join(args.output_dir, f"digital_adaptive_{args.split}.json")
    write_json(path, out)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
