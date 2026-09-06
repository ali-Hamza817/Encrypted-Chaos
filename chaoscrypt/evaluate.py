"""Attack-side evaluation: run the model over a test set, score reconstructions,
and turn the numbers into an Attack Risk verdict."""
from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import DataLoader

from .image_metrics import batch_scores

# Risk is judged on the GAIN over the trivial "predict the dataset mean image"
# baseline, not on raw SSIM -- a homogeneous test set can score high SSIM for a
# constant prediction, which would make a failed attack look successful.
RISK_RULES = [
    ("HIGH", lambda s: s.get("ssim_gain", s["ssim_mean"]) >= 0.30
             or s.get("psnr_gain", 0.0) >= 6.0),
    ("MEDIUM", lambda s: s.get("ssim_gain", s["ssim_mean"]) >= 0.12),
    ("LOW", lambda s: True),
]


def attack_risk(scores: dict) -> str:
    for label, rule in RISK_RULES:
        if rule(scores):
            return label
    return "LOW"


def mean_image_baseline(targets) -> dict:
    """Scores for predicting the per-pixel mean of `targets` for every sample --
    the best possible constant predictor, i.e. the 'no information recovered' floor."""
    t = np.asarray(targets, dtype=np.float32)
    mu = t.mean(axis=0, keepdims=True)
    pred = np.repeat(mu, len(t), axis=0)
    return batch_scores(pred, t, data_range=1.0)


@torch.no_grad()
def predict(model, ds, device: str | None = None, batch_size: int = 128):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    preds, targets = [], []
    for x, y in DataLoader(ds, batch_size=batch_size):
        preds.append(model(x.to(device)).clamp(0, 1).cpu().numpy())
        targets.append(y.numpy())
    return np.concatenate(preds), np.concatenate(targets)


def evaluate_attack(model, ds, device: str | None = None) -> dict:
    pred, target = predict(model, ds, device)
    scores = batch_scores(pred, target, data_range=1.0)
    base = mean_image_baseline(target)
    scores["ssim_baseline"] = base["ssim_mean"]
    scores["psnr_baseline"] = base["psnr_mean"]
    scores["ssim_gain"] = scores["ssim_mean"] - base["ssim_mean"]
    scores["psnr_gain"] = scores["psnr_mean"] - base["psnr_mean"]
    scores["risk"] = attack_risk(scores)
    return scores


def sample_grid(model, ds, path: str, n: int = 8, device: str | None = None) -> str:
    """Save a [cipher | prediction | ground-truth] comparison strip as PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    n = min(n, len(ds))
    xs = torch.stack([ds[i][0] for i in range(n)])
    ys = torch.stack([ds[i][1] for i in range(n)])
    with torch.no_grad():
        ps = model(xs.to(device)).clamp(0, 1).cpu()

    def show(ax, t):
        img = t.numpy()
        if img.shape[0] == 1:
            ax.imshow(img[0], cmap="gray", vmin=0, vmax=1)
        else:
            ax.imshow(np.moveaxis(img, 0, -1))
        ax.set_xticks([]); ax.set_yticks([])

    fig, axes = plt.subplots(3, n, figsize=(1.6 * n, 5))
    for i in range(n):
        show(axes[0, i], xs[i]); show(axes[1, i], ps[i]); show(axes[2, i], ys[i])
    axes[0, 0].set_ylabel("cipher", fontsize=9)
    axes[1, 0].set_ylabel("recovered", fontsize=9)
    axes[2, 0].set_ylabel("plaintext", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
