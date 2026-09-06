"""Target ciphers.

`ChaosImageCipher` : permutation + diffusion built from a chaotic keystream,
                    with configurable rounds and static / dynamic keying.
`AESImageCipher`   : AES-CTR baseline (the control for RQ4).

Design notes
------------
* Diffusion uses XOR chaining  c_i = p_i XOR k_i XOR c_{i-1}.  That recurrence is
  exactly a cumulative bitwise XOR, so it vectorises via
  ``np.bitwise_xor.accumulate`` -- encryption/decryption are O(n) numpy, no loop.
* "static" keystream depends only on the secret key (classic weak setting;
  attacks partly reduce to learning a fixed pad).  "dynamic" mixes a per-image
  public nonce into the map seed, so the attacker must approximate the chaotic
  expansion itself.  Report the two regimes separately (see RESEARCH.md).
"""
from __future__ import annotations

import hashlib

import numpy as np

from .chaos import make_orbit, orbit_to_bytes, orbit_to_permutation
from .keys import ChaosKey, aes_key_bytes


def _nonce_offsets(nonce: bytes) -> tuple[float, float]:
    """Turn a nonce into two small deterministic perturbations in (0, 1e-3)."""
    d = hashlib.sha256(nonce).digest()
    a = int.from_bytes(d[0:4], "big") / (2 ** 32) * 1.0e-3
    b = int.from_bytes(d[4:8], "big") / (2 ** 32) * 1.0e-3
    return a, b


class ChaosImageCipher:
    def __init__(
        self,
        key: ChaosKey,
        map_type: str = "logistic",
        rounds: int = 2,
        permute: bool = True,
        diffuse: bool = True,
        key_mode: str = "static",
        warmup: int = 1000,
    ):
        if key_mode not in ("static", "dynamic"):
            raise ValueError("key_mode must be 'static' or 'dynamic'")
        self.key = key
        self.map_type = map_type
        self.rounds = int(rounds)
        self.permute = permute
        self.diffuse = diffuse
        self.key_mode = key_mode
        self.warmup = warmup

    # ------------------------------------------------------------------ helpers
    def _seed_params(self, base: dict, nonce: bytes | None) -> dict:
        p = dict(base)
        if self.key_mode == "dynamic" and nonce is not None:
            da, db = _nonce_offsets(nonce)
            p["x0"] = (p["x0"] + da) % 1.0 or 0.123456
            p["y0"] = (p["y0"] + db) % 1.0 or 0.654321
        return p

    def _keystream(self, n: int, nonce: bytes | None) -> np.ndarray:
        params = self._seed_params(self.key.diff_params(), nonce)
        return orbit_to_bytes(make_orbit(self.map_type, params, n, self.warmup))

    def _permutation(self, n: int, nonce: bytes | None) -> np.ndarray:
        params = self._seed_params(self.key.perm_params(), nonce)
        return orbit_to_permutation(make_orbit(self.map_type, params, n, self.warmup))

    # ------------------------------------------------------------------ public
    def encrypt(self, image: np.ndarray, nonce: bytes | None = None) -> np.ndarray:
        img = np.asarray(image, dtype=np.uint8)
        flat = img.reshape(-1).copy()
        n = flat.size
        perm = self._permutation(n, nonce) if self.permute else None
        ks = self._keystream(n, nonce) if self.diffuse else None

        c = flat
        for _ in range(self.rounds):
            if perm is not None:
                c = c[perm]
            if ks is not None:
                d = np.bitwise_xor(c, ks)
                c = np.bitwise_xor.accumulate(d)
        return c.reshape(img.shape)

    def decrypt(self, cipher: np.ndarray, nonce: bytes | None = None) -> np.ndarray:
        c = np.asarray(cipher, dtype=np.uint8).reshape(-1).copy()
        n = c.size
        perm = self._permutation(n, nonce) if self.permute else None
        inv_perm = np.argsort(perm) if perm is not None else None
        ks = self._keystream(n, nonce) if self.diffuse else None

        for _ in range(self.rounds):
            if ks is not None:
                prev = np.empty_like(c)
                prev[0] = 0
                prev[1:] = c[:-1]
                d = np.bitwise_xor(c, prev)          # undo the cumulative XOR
                c = np.bitwise_xor(d, ks)
            if inv_perm is not None:
                c = c[inv_perm]
        return c.reshape(np.asarray(cipher).shape)

    def config(self) -> dict:
        return {
            "cipher": "chaos",
            "map_type": self.map_type,
            "rounds": self.rounds,
            "permute": self.permute,
            "diffuse": self.diffuse,
            "key_mode": self.key_mode,
            "seed": self.key.seed,
        }


class AESImageCipher:
    """AES-CTR over the raw image bytes. `key_mode='dynamic'` uses a random
    per-image nonce (provided back to the attacker); 'static' fixes the nonce."""

    def __init__(self, seed: str = "aes-baseline", key_mode: str = "dynamic", key_bits: int = 256):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # noqa
        self._Cipher, self._algorithms, self._modes = Cipher, algorithms, modes
        self.seed = seed
        self.key_mode = key_mode
        self.key = aes_key_bytes(seed, key_bits // 8)
        self._static_nonce = hashlib.sha256(self.key + b"nonce").digest()[:16]

    def _nonce(self, nonce: bytes | None) -> bytes:
        if self.key_mode == "static":
            return self._static_nonce
        return nonce if nonce is not None else np.random.bytes(16)

    def encrypt(self, image: np.ndarray, nonce: bytes | None = None) -> np.ndarray:
        img = np.asarray(image, dtype=np.uint8)
        n = self._nonce(nonce)
        enc = self._Cipher(self._algorithms.AES(self.key), self._modes.CTR(n)).encryptor()
        ct = enc.update(img.tobytes()) + enc.finalize()
        return np.frombuffer(ct, dtype=np.uint8).reshape(img.shape).copy()

    def decrypt(self, cipher: np.ndarray, nonce: bytes | None = None) -> np.ndarray:
        arr = np.asarray(cipher, dtype=np.uint8)
        n = self._nonce(nonce)
        dec = self._Cipher(self._algorithms.AES(self.key), self._modes.CTR(n)).decryptor()
        pt = dec.update(arr.tobytes()) + dec.finalize()
        return np.frombuffer(pt, dtype=np.uint8).reshape(arr.shape).copy()

    def config(self) -> dict:
        return {"cipher": "aes", "mode": "CTR", "key_mode": self.key_mode, "seed": self.seed}


def build_cipher(spec: dict):
    """Factory from a config dict (see configs/*.yaml)."""
    spec = dict(spec)
    kind = spec.pop("cipher", "chaos")
    if kind == "aes":
        return AESImageCipher(
            seed=spec.get("seed", "aes-baseline"),
            key_mode=spec.get("key_mode", "dynamic"),
            key_bits=spec.get("key_bits", 256),
        )
    from .keys import derive_key
    seed = spec.get("seed", "demo-key")
    return ChaosImageCipher(
        key=derive_key(seed),
        map_type=spec.get("map_type", "logistic"),
        rounds=spec.get("rounds", 2),
        permute=spec.get("permute", True),
        diffuse=spec.get("diffuse", True),
        key_mode=spec.get("key_mode", "static"),
    )
