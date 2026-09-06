"""Traditional cryptographic evaluation metrics for image ciphers.

These are the numbers a crypto reviewer expects to see. The thesis punchline is
that a scheme can score well here and still fall to the ML attack.
"""
from __future__ import annotations

import numpy as np


def _gray(img: np.ndarray) -> np.ndarray:
    img = np.asarray(img)
    if img.ndim == 3:
        return img.mean(axis=2)
    return img.astype(np.float64)


def shannon_entropy(img: np.ndarray) -> float:
    """Bits per pixel. Ideal for an 8-bit cipher image ~ 8.0 (report ~7.99)."""
    hist = np.bincount(np.asarray(img, dtype=np.uint8).ravel(), minlength=256).astype(np.float64)
    p = hist / hist.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def npcr(c1: np.ndarray, c2: np.ndarray) -> float:
    """Number of Pixel Change Rate (%) between two cipher images."""
    c1 = np.asarray(c1, dtype=np.uint8)
    c2 = np.asarray(c2, dtype=np.uint8)
    return float(np.mean(c1 != c2) * 100.0)


def uaci(c1: np.ndarray, c2: np.ndarray) -> float:
    """Unified Average Changing Intensity (%)."""
    c1 = np.asarray(c1, dtype=np.float64)
    c2 = np.asarray(c2, dtype=np.float64)
    return float(np.mean(np.abs(c1 - c2) / 255.0) * 100.0)


def adjacent_correlation(img: np.ndarray, direction: str = "horizontal",
                         n_pairs: int = 4096, seed: int = 0) -> float:
    """Pearson correlation of randomly sampled adjacent pixel pairs."""
    g = _gray(img)
    h, w = g.shape
    rng = np.random.default_rng(seed)
    if direction == "horizontal":
        r = rng.integers(0, h, n_pairs); c = rng.integers(0, w - 1, n_pairs)
        a, b = g[r, c], g[r, c + 1]
    elif direction == "vertical":
        r = rng.integers(0, h - 1, n_pairs); c = rng.integers(0, w, n_pairs)
        a, b = g[r, c], g[r + 1, c]
    elif direction == "diagonal":
        r = rng.integers(0, h - 1, n_pairs); c = rng.integers(0, w - 1, n_pairs)
        a, b = g[r, c], g[r + 1, c + 1]
    else:
        raise ValueError("direction must be horizontal|vertical|diagonal")
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def correlation_report(img: np.ndarray, **kw) -> dict:
    return {d: adjacent_correlation(img, d, **kw)
            for d in ("horizontal", "vertical", "diagonal")}


def histogram_uniformity_chi2(img: np.ndarray) -> float:
    """Chi-square statistic vs a flat 256-bin histogram (lower = more uniform)."""
    hist = np.bincount(np.asarray(img, dtype=np.uint8).ravel(), minlength=256).astype(np.float64)
    expected = hist.sum() / 256.0
    return float(((hist - expected) ** 2 / expected).sum())


def key_sensitivity(cipher_factory, image: np.ndarray, seed: str) -> dict:
    """Encrypt `image` under `seed` and under a ~1-bit-changed seed; compare."""
    from .keys import flip_key_bit
    c1 = cipher_factory(seed).encrypt(image)
    c2 = cipher_factory(flip_key_bit(seed)).encrypt(image)
    return {"npcr": npcr(c1, c2), "uaci": uaci(c1, c2)}


def plaintext_sensitivity(cipher, image: np.ndarray, seed_pixel: int = 0) -> dict:
    """Flip the LSB of one plaintext pixel, measure NPCR/UACI of the ciphertext.
    (Differential-attack resistance; meaningful mostly for plaintext-dependent keying.)"""
    img = np.asarray(image, dtype=np.uint8).copy()
    flat = img.reshape(-1)
    flat[seed_pixel % flat.size] ^= 1
    c1 = cipher.encrypt(image)
    c2 = cipher.encrypt(img)
    return {"npcr": npcr(c1, c2), "uaci": uaci(c1, c2)}


def full_report(cipher, image: np.ndarray, cipher_factory=None, seed: str | None = None) -> dict:
    """One call -> every metric above for a single sample image."""
    ct = cipher.encrypt(image)
    rep = {
        "entropy": shannon_entropy(ct),
        "histogram_chi2": histogram_uniformity_chi2(ct),
        "correlation": correlation_report(ct),
        "plaintext_entropy": shannon_entropy(image),
    }
    if cipher_factory is not None and seed is not None:
        rep["key_sensitivity"] = key_sensitivity(cipher_factory, image, seed)
        rep["plaintext_sensitivity"] = plaintext_sensitivity(cipher, image)
    return rep
