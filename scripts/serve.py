"""Launch the Encrypted-Chaos web app.

    python scripts/serve.py                 # http://localhost:8000
    python scripts/serve.py --port 9000 --reload
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--reload", action="store_true")
    args = ap.parse_args()

    import uvicorn
    print(f"\n  Encrypted-Chaos  ->  http://localhost:{args.port}\n")
    uvicorn.run("app.server:app", host=args.host, port=args.port,
                reload=args.reload, app_dir=str(ROOT))


if __name__ == "__main__":
    main()
