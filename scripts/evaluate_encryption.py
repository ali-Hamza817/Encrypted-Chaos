"""Profile a cipher with the traditional cryptographic metrics.

    python scripts/evaluate_encryption.py --source cifar10 --map logistic --rounds 2
    python scripts/evaluate_encryption.py --source synthetic --cipher aes

Prints a table averaged over N sample images and saves histogram + correlation
scatter plots under experiments/enc_profile/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chaoscrypt.crypto_metrics import (adjacent_correlation, correlation_report,
                                       histogram_uniformity_chi2, key_sensitivity,
                                       npcr, shannon_entropy, uaci)
from chaoscrypt.dataset import load_source_images
from chaoscrypt.encryption import build_cipher
from chaoscrypt.utils import ensure_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="synthetic")
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--image-size", type=int, default=64)
    ap.add_argument("--channels", type=int, default=1)
    ap.add_argument("--cipher", default="chaos", choices=["chaos", "aes"])
    ap.add_argument("--map", dest="map_type", default="logistic")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--no-permute", action="store_true")
    ap.add_argument("--no-diffuse", action="store_true")
    ap.add_argument("--key-mode", default="static")
    ap.add_argument("--seed", default="profile-key")
    args = ap.parse_args()

    spec = {"cipher": args.cipher, "seed": args.seed, "key_mode": args.key_mode,
            "map_type": args.map_type, "rounds": args.rounds,
            "permute": not args.no_permute, "diffuse": not args.no_diffuse}

    def factory(seed):
        s = dict(spec); s["seed"] = seed
        return build_cipher(s)

    cipher = build_cipher(spec)
    imgs = load_source_images(args.source, args.n, args.image_size, args.channels, split="test")

    ent, chi2, cor_h, cor_v, cor_d, ks_npcr, ks_uaci = ([] for _ in range(7))
    plain_ent = []
    ct0 = None
    for i, img in enumerate(imgs):
        ct = cipher.encrypt(img)
        if ct0 is None:
            ct0, plain0 = ct, img
        ent.append(shannon_entropy(ct))
        plain_ent.append(shannon_entropy(img))
        chi2.append(histogram_uniformity_chi2(ct))
        c = correlation_report(ct)
        cor_h.append(c["horizontal"]); cor_v.append(c["vertical"]); cor_d.append(c["diagonal"])
        kr = key_sensitivity(factory, img, args.seed)
        ks_npcr.append(kr["npcr"]); ks_uaci.append(kr["uaci"])

    def line(k, v, ideal):
        print(f"  {k:<26} {v:>10.4f}    (ideal ~ {ideal})")

    print(f"\n=== Encryption profile: {spec} ===")
    print(f"  images: {args.n} x {args.image_size}x{args.image_size}x{args.channels} "
          f"from {args.source}\n")
    line("plaintext entropy", float(np.mean(plain_ent)), "varies")
    line("cipher entropy (bpp)", float(np.mean(ent)), "7.99")
    line("histogram chi-square", float(np.mean(chi2)), "low / ~255")
    line("correlation H", float(np.mean(cor_h)), "0.00")
    line("correlation V", float(np.mean(cor_v)), "0.00")
    line("correlation D", float(np.mean(cor_d)), "0.00")
    line("key sensitivity NPCR %", float(np.mean(ks_npcr)), "99.60")
    line("key sensitivity UACI %", float(np.mean(ks_uaci)), "33.46")

    out = ensure_dir(ROOT / "experiments" / "enc_profile")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 3, figsize=(12, 3.4))
        ax[0].hist(np.asarray(plain0).ravel(), bins=64, color="#4C78A8")
        ax[0].set_title("plaintext histogram")
        ax[1].hist(np.asarray(ct0).ravel(), bins=64, color="#E45756")
        ax[1].set_title("ciphertext histogram")
        g = np.asarray(ct0).astype(float)
        g = g.mean(2) if g.ndim == 3 else g
        rng = np.random.default_rng(0)
        r = rng.integers(0, g.shape[0], 3000); cc = rng.integers(0, g.shape[1] - 1, 3000)
        ax[2].scatter(g[r, cc], g[r, cc + 1], s=3, alpha=0.3, color="#54A24B")
        ax[2].set_title("adjacent-pixel correlation (H)")
        ax[2].set_xlabel("pixel (x,y)"); ax[2].set_ylabel("pixel (x+1,y)")
        fig.tight_layout()
        fig.savefig(out / "profile.png", dpi=120)
        print(f"\n  saved plots -> {out/'profile.png'}")
    except Exception as e:  # noqa
        print(f"  (plot skipped: {e})")


if __name__ == "__main__":
    main()
