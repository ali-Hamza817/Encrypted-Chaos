"""Source images and the plaintext/ciphertext pair builder.

`synthetic` needs nothing installed and runs in seconds -- use it for CI and the
quickstart. `cifar10` / `stl10` pull via torchvision for real experiments.
"""
from __future__ import annotations

import numpy as np

from .encryption import build_cipher

# --------------------------------------------------------------------- sources


def synthetic_images(n: int, size: int = 32, channels: int = 1, seed: int = 0) -> np.ndarray:
    """Diverse procedural images: random-frequency gratings + smooth blobs + shapes
    + texture noise, with varied brightness/contrast.

    Diversity matters for honest cryptanalysis benchmarking: if every image looked
    alike, a model that just predicts the dataset mean would score a high SSIM and
    a failed attack would look like a success. Here the per-pixel mean over the set
    is close to flat grey, so the "predict the mean" baseline SSIM stays low.
    """
    rng = np.random.default_rng(seed)
    out = np.zeros((n, size, size, channels), dtype=np.uint8)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    yn, xn = yy / size, xx / size
    for i in range(n):
        img = np.full((size, size), rng.uniform(40, 215), dtype=np.float64)
        # 1-3 sinusoidal gratings, random orientation / frequency / phase
        for _ in range(rng.integers(1, 4)):
            theta = rng.uniform(0, np.pi)
            freq = rng.uniform(1.0, 6.0)
            phase = rng.uniform(0, 2 * np.pi)
            amp = rng.uniform(20, 90)
            proj = np.cos(theta) * xn + np.sin(theta) * yn
            img += amp * np.sin(2 * np.pi * freq * proj + phase)
        # a few smooth Gaussian blobs
        for _ in range(rng.integers(0, 4)):
            cx, cy = rng.uniform(0, 1, 2)
            sig = rng.uniform(0.08, 0.3)
            img += rng.uniform(-90, 90) * np.exp(
                -(((xn - cx) ** 2 + (yn - cy) ** 2) / (2 * sig ** 2)))
        # optional hard-edged shape
        if rng.random() < 0.6:
            if rng.random() < 0.5:
                x0, y0 = rng.integers(0, size, 2)
                w, h = rng.integers(3, max(4, size // 2), 2)
                img[y0:y0 + h, x0:x0 + w] = rng.uniform(0, 255)
            else:
                cx, cy = rng.integers(0, size, 2)
                r = rng.integers(2, max(3, size // 3))
                img[(xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2] = rng.uniform(0, 255)
        # fine texture
        img += rng.normal(0, rng.uniform(2, 18), size=(size, size))
        # random contrast around the mid-grey
        img = 128 + (img - img.mean()) * rng.uniform(0.6, 1.4)
        out[i] = np.repeat(np.clip(img, 0, 255)[..., None], channels, axis=2).astype(np.uint8)
    return out if channels > 1 else out[..., 0]


def _torchvision_images(source: str, n: int, size: int, channels: int, split: str,
                        root: str = "./data") -> np.ndarray:
    from torchvision import datasets
    train = split == "train"
    if source == "cifar10":
        ds = datasets.CIFAR10(root, train=train, download=True)
    elif source == "cifar100":
        ds = datasets.CIFAR100(root, train=train, download=True)
    elif source == "stl10":
        ds = datasets.STL10(root, split="train" if train else "test", download=True)
    else:
        raise ValueError(f"unknown source {source!r}")
    mode = "L" if channels == 1 else "RGB"
    imgs = []
    for i in range(min(n, len(ds))):
        pil = ds[i][0].convert(mode).resize((size, size))
        imgs.append(np.array(pil, dtype=np.uint8))
    arr = np.stack(imgs)
    return arr


def load_source_images(source: str, n: int, size: int = 32, channels: int = 1,
                       split: str = "train", root: str = "./data", seed: int = 0) -> np.ndarray:
    if source == "synthetic":
        return synthetic_images(n, size, channels, seed=seed + (0 if split == "train" else 999))
    return _torchvision_images(source, n, size, channels, split, root)


# --------------------------------------------------------------------- pairing


def encrypt_batch(cipher, images: np.ndarray, dynamic_nonce: bool = False,
                  rng: np.random.Generator | None = None):
    """Return (cipher_imgs, nonces). `nonces` is None unless dynamic_nonce."""
    rng = rng or np.random.default_rng(0)
    ct = np.empty_like(images)
    nonces = [] if dynamic_nonce else None
    for i in range(len(images)):
        nb = rng.bytes(16) if dynamic_nonce else None
        ct[i] = cipher.encrypt(images[i], nonce=nb)
        if dynamic_nonce:
            nonces.append(nb)
    return ct, nonces


def build_pair_arrays(cipher_specs, images: np.ndarray, dynamic_nonce: bool = False,
                      seed: int = 0):
    """cipher_specs: a single spec dict (one key) OR a list of specs (multi-key).
    When a list is given, images are split evenly and each chunk uses one spec.
    Returns float32 arrays X (cipher) and Y (plain) in [0,1], shape (N,C,H,W)."""
    if isinstance(cipher_specs, dict):
        cipher_specs = [cipher_specs]
    rng = np.random.default_rng(seed)
    chunks = np.array_split(np.arange(len(images)), len(cipher_specs))
    ct_all = np.empty_like(images)
    for spec, idx in zip(cipher_specs, chunks):
        if len(idx) == 0:
            continue
        cipher = build_cipher(spec)
        ct, _ = encrypt_batch(cipher, images[idx], dynamic_nonce, rng)
        ct_all[idx] = ct
    x = _to_nchw_float(ct_all)
    y = _to_nchw_float(images)
    return x, y


def _to_nchw_float(arr: np.ndarray) -> np.ndarray:
    a = np.asarray(arr, dtype=np.float32) / 255.0
    if a.ndim == 3:                      # N,H,W  -> N,1,H,W
        a = a[:, None, :, :]
    elif a.ndim == 4:                    # N,H,W,C -> N,C,H,W
        a = np.moveaxis(a, 3, 1)
    return np.ascontiguousarray(a)


# --------------------------------------------------------------------- torch Dataset


class PairDataset:
    """Lightweight torch Dataset wrapper (import guarded so numpy-only use is fine)."""

    def __init__(self, x: np.ndarray, y: np.ndarray):
        import torch
        self.x = torch.from_numpy(x)
        self.y = torch.from_numpy(y)

    def __len__(self):
        return self.x.shape[0]

    def __getitem__(self, i):
        return self.x[i], self.y[i]
