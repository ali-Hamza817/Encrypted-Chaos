"""One-command sanity check: runs the tiny `smoke` config end to end on synthetic
data (no downloads, ~1 min CPU) and prints the Attack Risk verdict.

    python scripts/quickstart.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    cmd = [sys.executable, str(ROOT / "scripts" / "run_experiment.py"),
           str(ROOT / "configs" / "smoke.yaml"), "--outdir", str(ROOT / "experiments")]
    print("running:", " ".join(cmd), "\n")
    raise SystemExit(subprocess.call(cmd))
