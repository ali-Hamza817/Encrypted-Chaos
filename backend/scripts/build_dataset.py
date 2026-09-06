"""Pre-generate a plaintext/ciphertext pair dataset and save it as .npz
(so training runs don't re-encrypt every time).

    python scripts/build_dataset.py --config configs/rq1_same_key.yaml --split train
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chaoscrypt.dataset import build_pair_arrays, load_source_images
from chaoscrypt.utils import ensure_dir, load_yaml


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--split", choices=["train", "test"], default="train")
    ap.add_argument("--outdir", default="datasets")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    d = cfg["data"]
    n = d["n_train"] if args.split == "train" else d["n_test"]
    role = "train_cipher" if args.split == "train" else "test_cipher"
    base = dict(cfg.get(role) or cfg["cipher"])

    if args.split == "train":
        specs = [{**base, "seed": k} for k in cfg["keys"]["train_keys"]]
    else:
        specs = {**base, "seed": cfg["keys"]["test_key"]}

    imgs = load_source_images(d["source"], n, d["image_size"], d["channels"], split=args.split)
    x, y = build_pair_arrays(specs, imgs, dynamic_nonce=d.get("dynamic_nonce", False),
                             seed=1 if args.split == "train" else 2)

    out = ensure_dir(Path(args.outdir))
    path = out / f"{cfg.get('name','ds')}_{args.split}.npz"
    np.savez_compressed(path, x=x, y=y)
    print(f"saved {path}  x={x.shape} y={y.shape}")


if __name__ == "__main__":
    main()
