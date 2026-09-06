"""Run the three frontend-demo experiments back to back and write a combined
summary (experiments/demo_summary.json) the frontend reads.

    python scripts/run_demo_suite.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chaoscrypt.utils import load_json, save_json

CONFIGS = ["demo_weak_chaos", "demo_full_chaos", "demo_dynamic_chaos", "demo_aes"]


def main() -> None:
    out = ROOT / "experiments"
    results = {}
    t0 = time.time()
    force = "--force" in sys.argv
    for name in CONFIGS:
        cfg = ROOT / "configs" / f"{name}.yaml"
        done = (out / name / "report.json").exists()
        if done and not force:
            print(f"\n{'='*60}\n SKIP {name} (report.json exists; pass --force to rerun)\n{'='*60}",
                  flush=True)
        else:
            print(f"\n{'='*60}\n RUN {name}\n{'='*60}", flush=True)
            rc = subprocess.call([sys.executable, str(ROOT / "scripts" / "run_experiment.py"),
                                  str(cfg), "--outdir", str(out)])
            if rc != 0:
                print(f"!! {name} exited {rc}")
                continue
        rep = load_json(out / name / "report.json")
        results[name] = {
            "scores": rep["scores"],
            "cipher": rep["config"]["cipher"],
            "n_train": rep["config"]["data"]["n_train"],
            "n_test": rep["config"]["data"]["n_test"],
            "epochs": rep["config"]["train"]["epochs"],
            "model": rep["config"]["model"]["name"],
            "n_params": rep["n_params"],
        }
    save_json({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
               "elapsed_sec": round(time.time() - t0, 1),
               "runs": results}, out / "demo_summary.json")
    print(f"\nDONE in {time.time()-t0:.0f}s -> {out/'demo_summary.json'}")


if __name__ == "__main__":
    main()
