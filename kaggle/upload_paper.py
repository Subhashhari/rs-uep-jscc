"""Upload paper/ (tex, bib, generated numbers/tables, figures) as the PRIVATE dataset rs-uep-jscc-paper."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SLUG = "vaishakprasadbhat/rs-uep-jscc-paper"


def main() -> int:
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "paper"
        shutil.copytree(REPO / "paper", target, ignore=shutil.ignore_patterns("*.png", "*.aux", "*.pdf.tmp"))
        (Path(folder) / "dataset-metadata.json").write_text(
            json.dumps({"title": "rs-uep-jscc-paper", "id": SLUG, "licenses": [{"name": "other"}]}), encoding="utf-8")
        shutil.make_archive(str(Path(folder) / "paper"), "zip", target)
        shutil.rmtree(target)
        kg = [sys.executable, str(REPO / "kaggle" / "kg.py")]
        exists = subprocess.call(kg + ["datasets", "status", SLUG], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        command = kg + (["datasets", "version", "-p", folder, "-m", "update"] if exists else ["datasets", "create", "-p", folder])
        return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
