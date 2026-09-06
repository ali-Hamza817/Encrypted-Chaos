"""Run one experiment end to end from a YAML config.

    python scripts/run_experiment.py configs/rq1_same_key.yaml
    python scripts/run_experiment.py configs/rq2_cross_key.yaml --outdir experiments

Outputs (experiments/<name>/): report.json, history.json, samples.png, model.pt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chaoscrypt.dataset import PairDataset, build_pair_arrays, load_source_images
from chaoscrypt.evaluate import evaluate_attack, sample_grid
from chaoscrypt.models import build_model
from chaoscrypt.train import train_model
from chaoscrypt.utils import ensure_dir, load_yaml, save_json, set_seed, timer


def _cipher_spec(cfg: dict, role: str) -> dict:
    """role: 'train' or 'test'. Falls back to cfg['cipher']."""
    key = f"{role}_cipher"
    base = dict(cfg.get(key) or cfg["cipher"])
    return base


def _with_seed(spec: dict, seed: str) -> dict:
    s = dict(spec)
    s["seed"] = seed
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=str)
    ap.add_argument("--outdir", type=str, default="experiments")
    ap.add_argument("--device", type=str, default=None)
    ap.add_argument("--epochs", type=int, default=None, help="override config epochs")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    name = cfg.get("name", Path(args.config).stem)
    out = ensure_dir(Path(args.outdir) / name)
    set_seed(cfg["train"].get("seed", 1234))

    d = cfg["data"]
    train_specs = [_with_seed(_cipher_spec(cfg, "train"), k) for k in cfg["keys"]["train_keys"]]
    test_spec = _with_seed(_cipher_spec(cfg, "test"), cfg["keys"]["test_key"])

    print(f"[{name}] loading {d['n_train']} train / {d['n_test']} test images "
          f"from {d['source']} ...")
    train_imgs = load_source_images(d["source"], d["n_train"], d["image_size"],
                                    d["channels"], split="train")
    test_imgs = load_source_images(d["source"], d["n_test"], d["image_size"],
                                   d["channels"], split="test")

    with timer("encrypt"):
        xtr, ytr = build_pair_arrays(train_specs, train_imgs,
                                     dynamic_nonce=d.get("dynamic_nonce", False), seed=1)
        xte, yte = build_pair_arrays(test_spec, test_imgs,
                                     dynamic_nonce=d.get("dynamic_nonce", False), seed=2)

    # hold out a validation slice from training pairs
    n_val = max(1, int(0.1 * len(xtr)))
    train_ds = PairDataset(xtr[n_val:], ytr[n_val:])
    val_ds = PairDataset(xtr[:n_val], ytr[:n_val])
    test_ds = PairDataset(xte, yte)

    model = build_model(cfg["model"])
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[{name}] model {cfg['model']['name']}  params={n_params/1e6:.2f}M")

    tcfg = cfg["train"]
    model, history = train_model(
        model, train_ds, val_ds,
        epochs=args.epochs or tcfg["epochs"],
        batch_size=tcfg["batch_size"], lr=tcfg["lr"], device=args.device,
    )

    scores = evaluate_attack(model, test_ds, device=args.device)
    print(f"\n[{name}] TEST  PSNR {scores['psnr_mean']:.2f} dB   "
          f"SSIM {scores['ssim_mean']:.3f}   ->  Attack Risk: {scores['risk']}")

    import torch
    torch.save({"state_dict": model.state_dict(), "model_cfg": cfg["model"]}, out / "model.pt")
    save_json(history, out / "history.json")
    save_json({
        "name": name, "config": cfg, "n_params": n_params,
        "train_cipher": train_specs, "test_cipher": test_spec,
        "scores": scores,
    }, out / "report.json")
    sample_grid(model, test_ds, str(out / "samples.png"), n=8, device=args.device)
    print(f"[{name}] wrote {out}/report.json, samples.png, model.pt")


if __name__ == "__main__":
    main()
