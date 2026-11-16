"""Wait for the Kaggle nors2_* jobs, fetch their outputs into results/nors2 and write results/nors2/READY.

READY lists ``name checkpoint ranking sources`` lines for experiments/queue_paper_evals_2.sh. The 24-channel
model chosen by each job (best of three by clean validation PSNR, recorded in status.json) is evaluated both
as trained (clean) and after the erasure fine-tune.

    python kaggle/fetch_nors2.py
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JOBS = {"adjsccq": "rs-uep-jscc-nors2-adjsccq", "deepjsccq": "rs-uep-jscc-nors2-deepjsccq"}


def kg(*args: str) -> str:
    return subprocess.run([sys.executable, str(REPO / "kaggle" / "kg.py"), *args], capture_output=True, text=True,
                          cwd=REPO).stdout


def main() -> int:
    pending = dict(JOBS)
    while pending:
        for arch, slug in list(pending.items()):
            status = kg("kernels", "status", f"vaishakprasadbhat/{slug}")
            if "RUNNING" in status or "QUEUED" in status:
                continue
            print(f"{slug}: {status.strip()}", flush=True)
            target = REPO / "results" / "kaggle" / slug
            target.mkdir(parents=True, exist_ok=True)
            kg("kernels", "output", f"vaishakprasadbhat/{slug}", "-p", str(target))
            source = target / "outputs" / "results" / "nors2"
            if source.is_dir():
                shutil.copytree(source, REPO / "results" / "nors2", dirs_exist_ok=True)
            del pending[arch]
        if pending:
            time.sleep(120)
    lines = []
    for arch, slug in JOBS.items():
        status_file = REPO / "results" / "kaggle" / slug / "outputs" / "status.json"
        if not status_file.exists():
            continue
        status = json.loads(status_file.read_text(encoding="utf-8"))
        selected = status.get("nors2_selected", {}).get("selected")
        sources = "static:oracle,energy,random" + (",attention" if arch == "adjsccq" else "")
        if selected:
            folder = f"results/{selected}"
            lines.append(f"kn14_best_clean_{arch} {folder}/best_val.pth {folder}/oracle_ranking.json {sources}")
        robust = f"results/nors2/{arch}_kn14_best_robust"
        lines.append(f"kn14_best_robust_{arch} {robust}/adjsccq_erasure_robust.pth {robust}/oracle_ranking.json "
                     "static:oracle,energy,random")
        if arch == "deepjsccq":
            folder = "results/nors2/deepjsccq_kn16_seed7_robust"
            lines.append(f"deepjsccq_kn16_seed7_robust {folder}/adjsccq_erasure_robust.pth {folder}/oracle_ranking.json "
                         "static:oracle,energy,random")
    (REPO / "results" / "nors2").mkdir(parents=True, exist_ok=True)
    (REPO / "results" / "nors2" / "READY").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("READY:\n" + "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
