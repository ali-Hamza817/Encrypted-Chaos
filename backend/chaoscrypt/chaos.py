"""Chaotic maps and helpers to turn their orbits into keystream bytes / permutations.

All functions are pure numpy so the encryption side has no torch dependency.
The recurrences are inherently sequential; for MVP image sizes (32x32 .. 256x256)
a plain Python loop over the warm-up plus a vectorised orbit is fast enough.
"""
from __future__ import annotations

import numpy as np

CHAOTIC_MAPS = ("logistic", "logistic2d", "henon")


def logistic_orbit(x0: float, r: float, n: int, warmup: int = 1000) -> np.ndarray:
    """x_{n+1} = r * x_n * (1 - x_n),  chaotic for r in ~[3.57, 4.0]."""
    x = float(x0)
    for _ in range(warmup):
        x = r * x * (1.0 - x)
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        x = r * x * (1.0 - x)
        out[i] = x
    return out


def logistic2d_orbit(x0: float, y0: float, r: float, n: int, warmup: int = 1000) -> np.ndarray:
    """2D coupled logistic map. Returns the interleaved x/y stream, length n."""
    x, y = float(x0), float(y0)
    for _ in range(warmup):
        x_new = r * (3.0 * y + 1.0) * x * (1.0 - x)
        y_new = r * (3.0 * x_new + 1.0) * y * (1.0 - y)
        x, y = x_new % 1.0, y_new % 1.0
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        x_new = r * (3.0 * y + 1.0) * x * (1.0 - x)
        y_new = r * (3.0 * x_new + 1.0) * y * (1.0 - y)
        x, y = x_new % 1.0, y_new % 1.0
        out[i] = x if (i % 2 == 0) else y
    return out


def henon_orbit(x0: float, y0: float, a: float = 1.4, b: float = 0.3,
                n: int = 1, warmup: int = 1000) -> np.ndarray:
    """Hénon map, normalised to (0,1) via a fixed affine + fractional part.

    Initial conditions from the key are compressed into the map's basin of
    attraction (|x0|,|y0| < ~0.3) and a divergence guard resets any orbit that
    escapes, so every key produces a usable bounded stream.
    """
    x, y = (float(x0) - 0.5) * 0.4, (float(y0) - 0.5) * 0.4
    for _ in range(warmup):
        x, y = 1.0 - a * x * x + y, b * x
        if not (np.isfinite(x) and np.isfinite(y)):
            x, y = 0.1, 0.1
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        x, y = 1.0 - a * x * x + y, b * x
        if not (np.isfinite(x) and np.isfinite(y)) or abs(x) > 1.0e6:
            x, y = 0.1, 0.1
        out[i] = (x * 3.1830988618 + 0.5) % 1.0  # spread into (0,1)
    return out


def make_orbit(map_type: str, seed_params: dict, n: int, warmup: int = 1000) -> np.ndarray:
    """Dispatch to a map by name. `seed_params` carries x0/y0/r as needed."""
    if map_type == "logistic":
        return logistic_orbit(seed_params["x0"], seed_params["r"], n, warmup)
    if map_type == "logistic2d":
        return logistic2d_orbit(seed_params["x0"], seed_params["y0"], seed_params["r"], n, warmup)
    if map_type == "henon":
        return henon_orbit(seed_params["x0"], seed_params["y0"], n=n, warmup=warmup)
    raise ValueError(f"unknown map_type {map_type!r}; expected one of {CHAOTIC_MAPS}")


def orbit_to_bytes(orbit: np.ndarray) -> np.ndarray:
    """Map a real orbit in (0,1) to uint8 keystream bytes."""
    scaled = np.floor(orbit * 1.0e14) % 256.0
    return scaled.astype(np.uint8)


def orbit_to_permutation(orbit: np.ndarray) -> np.ndarray:
    """Argsort of the orbit -> a permutation of range(len(orbit))."""
    return np.argsort(orbit, kind="stable").astype(np.int64)
