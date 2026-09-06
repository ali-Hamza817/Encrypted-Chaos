"""Bake measured demo results (numbers + sample PNGs as base64) into the
frontend HTML so it renders them with zero network calls.

    python scripts/inject_results.py
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web" / "chaoscrypt-analyzer.html"
SUMMARY = ROOT / "experiments" / "demo_summary.json"

ORDER = ["demo_weak_chaos", "demo_full_chaos", "demo_dynamic_chaos", "demo_aes"]
LABELS = {
    "demo_weak_chaos": "Chaos - diffusion only, static key",
    "demo_full_chaos": "Chaos - permutation + diffusion x2, static key",
    "demo_dynamic_chaos": "Chaos - permutation + diffusion x2, per-image key",
    "demo_aes": "AES-256-CTR, per-image nonce",
}

MARK_A = "<!-- RESULTS:BEGIN -->"
MARK_B = "<!-- RESULTS:END -->"


def main() -> None:
    if not SUMMARY.exists():
        sys.exit(f"no {SUMMARY} yet -- run scripts/run_demo_suite.py first")
    summary = json.loads(SUMMARY.read_text())
    runs = summary.get("runs", {})

    present = [k for k in ORDER if k in runs] + [k for k in runs if k not in ORDER]
    for k in present:
        runs[k]["label"] = LABELS.get(k, k)

    samples = {}
    for k in present:
        p = ROOT / "experiments" / k / "samples.png"
        if p.exists():
            samples[k] = base64.b64encode(p.read_bytes()).decode("ascii")

    payload = {**summary, "order": present, "runs": runs, "samples": samples}
    block = (f"{MARK_A}\n<script>window.__CHAOSCRYPT_RESULTS__ = "
             f"{json.dumps(payload)};</script>\n{MARK_B}")

    html = HTML.read_text(encoding="utf-8")
    if MARK_A in html and MARK_B in html:
        html = html.split(MARK_A)[0] + block + html.split(MARK_B)[1]
    else:
        anchor = "<script>\n(function () {"
        html = html.replace(anchor, block + "\n" + anchor, 1)
    HTML.write_text(html, encoding="utf-8")

    print(f"injected {len(present)} runs, {len(samples)} sample strips "
          f"({len(block)/1024:.0f} KB)  ->  {HTML}")
    for k in present:
        sc = runs[k].get("scores", {})
        print(f"  {k:22s} SSIM {sc.get('ssim_mean', float('nan')):.3f}  "
              f"floor {sc.get('ssim_baseline', float('nan')):.3f}  "
              f"gain {sc.get('ssim_gain', float('nan')):+.3f}  {sc.get('risk', '?')}")


if __name__ == "__main__":
    main()
