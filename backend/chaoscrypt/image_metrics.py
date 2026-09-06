"""Reconstruction-quality metrics for the attack side (MSE / PSNR / SSIM).

Accepts either uint8 [0,255] arrays or float [0,1] arrays; pass `data_range`
accordingly (default 1.0 for the float tensors used in training).
"""
from __future__ import annotations

import numpy as np


def mse(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return float(np.mean((a - b) ** 2))


def psnr(a: np.ndarray, b: np.ndarray, data_range: float = 1.0) -> float:
    m = mse(a, b)
    if m <= 1e-12:
        return 99.0
    return float(10.0 * np.log10((data_range ** 2) / m))


def ssim(a: np.ndarray, b: np.ndarray, data_range: float = 1.0) -> float:
    from skimage.metrics import structural_similarity as sk_ssim
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.ndim == 3 and a.shape[-1] in (3, 4):
        return float(sk_ssim(a, b, data_range=data_range, channel_axis=-1))
    if a.ndim == 3 and a.shape[0] in (1, 3):          # C,H,W
        a = np.moveaxis(a, 0, -1); b = np.moveaxis(b, 0, -1)
        ca = None if a.shape[-1] == 1 else -1
        return float(sk_ssim(a.squeeze(), b.squeeze(), data_range=data_range, channel_axis=ca))
    return float(sk_ssim(a, b, data_range=data_range))


def batch_scores(pred: np.ndarray, target: np.ndarray, data_range: float = 1.0) -> dict:
    """pred/target: (N, C, H, W) float arrays. Returns mean/std of each metric."""
    ms, ps, ss = [], [], []
    for p, t in zip(pred, target):
        ms.append(mse(p, t))
        ps.append(psnr(p, t, data_range))
        ss.append(ssim(p, t, data_range))
    return {
        "mse_mean": float(np.mean(ms)), "mse_std": float(np.std(ms)),
        "psnr_mean": float(np.mean(ps)), "psnr_std": float(np.std(ps)),
        "ssim_mean": float(np.mean(ss)), "ssim_std": float(np.std(ss)),
        "n": len(ms),
    }
