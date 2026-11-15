"""Upload the working tree's code (not docs, paper or results) as a PRIVATE Kaggle dataset.

Kaggle jobs generated with ``CODE_SOURCE = "dataset"`` unpack this archive instead of cloning the
public GitHub repository, so an unpublished branch never has to be pushed (double-blind review).

    python kaggle/upload_code.py                 # create or version vaishakprasadbhat/rs-uep-jscc-code

Only the code folders below are packed: files git tracks plus new, not-ignored files, as they are on
disk now. ``CODE_VERSION.json`` records the commit, branch and whether the tree was dirty; result
files read it for their provenance when there is no ``.git`` (experiments/reproducibility.py).
"""
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OWNER = "vaishakprasadbhat"
SLUG = "rs-uep-jscc-code"
CODE_PATHS = ("coding", "models", "data", "experiments", "configs", "tests", "run_pipeline.py",
              "requirements-local.txt")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def code_files():
    listed = git("ls-files", "--cached", "--others", "--exclude-standard", "--", *CODE_PATHS).splitlines()
    return sorted({name for name in listed if (REPO / name).is_file()})


def main() -> int:
    stamp = {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=no", "--", *CODE_PATHS)),
        "packed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    files = code_files()
    with tempfile.TemporaryDirectory() as folder:
        archive = Path(folder) / "rs-uep-jscc-code.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for name in files:
                tar.add(REPO / name, arcname=name)
            stamp_path = Path(folder) / "CODE_VERSION.json"
            stamp_path.write_text(json.dumps(stamp, indent=2), encoding="utf-8")
            tar.add(stamp_path, arcname="CODE_VERSION.json")
        stamp_path.unlink()
        meta = {"title": SLUG, "id": f"{OWNER}/{SLUG}", "licenses": [{"name": "other"}]}
        (Path(folder) / "dataset-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"packed {len(files)} files ({archive.stat().st_size / 1e6:.2f} MB): {stamp}")
        kg = [sys.executable, str(REPO / "kaggle" / "kg.py")]
        status = subprocess.call(kg + ["datasets", "status", f"{OWNER}/{SLUG}"], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        if status == 0:
            command = kg + ["datasets", "version", "-p", folder, "-m", f"{stamp['branch']}@{stamp['commit'][:10]}"]
        else:  # first upload; datasets are private unless --public is passed
            command = kg + ["datasets", "create", "-p", folder]
        return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
