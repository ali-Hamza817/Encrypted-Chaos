"""Deterministic key derivation.

A human-readable passphrase (seed string) -> a `ChaosKey` with the initial
conditions / control parameters every supported map needs. Using SHA-256 keeps
derivation reproducible across machines and makes "flip one bit of the key"
trivial for key-sensitivity tests.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ChaosKey:
    seed: str
    perm_x0: float
    perm_y0: float
    perm_r: float
    diff_x0: float
    diff_y0: float
    diff_r: float

    def perm_params(self) -> dict:
        return {"x0": self.perm_x0, "y0": self.perm_y0, "r": self.perm_r}

    def diff_params(self) -> dict:
        return {"x0": self.diff_x0, "y0": self.diff_y0, "r": self.diff_r}

    def as_dict(self) -> dict:
        return asdict(self)


def _unit(block: bytes) -> float:
    """4 bytes -> float in the open interval (0, 1)."""
    return (int.from_bytes(block, "big") + 1) / (2 ** 32 + 1)


def derive_key(seed: str) -> ChaosKey:
    h = hashlib.sha256(seed.encode("utf-8")).digest()  # 32 bytes
    # keep initial conditions away from fixed points / 0 / 1
    perm_x0 = 0.1 + 0.8 * _unit(h[0:4])
    perm_y0 = 0.1 + 0.8 * _unit(h[4:8])
    diff_x0 = 0.1 + 0.8 * _unit(h[8:12])
    diff_y0 = 0.1 + 0.8 * _unit(h[12:16])
    # control parameter in the fully-chaotic band [3.90, 3.999...]
    perm_r = 3.90 + 0.0999 * _unit(h[16:20])
    diff_r = 3.90 + 0.0999 * _unit(h[20:24])
    return ChaosKey(seed, perm_x0, perm_y0, perm_r, diff_x0, diff_y0, diff_r)


def flip_key_bit(seed: str) -> str:
    """Return a seed string one character apart -> a ~1-bit key change downstream."""
    if not seed:
        return "\x01"
    last = seed[-1]
    return seed[:-1] + chr((ord(last) ^ 0x01))


def aes_key_bytes(seed: str, nbytes: int = 32) -> bytes:
    """Derive an AES key (default AES-256) from the same passphrase space."""
    return hashlib.sha256(("aes::" + seed).encode("utf-8")).digest()[:nbytes]
