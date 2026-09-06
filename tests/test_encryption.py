"""Correctness of the ciphers: encrypt/decrypt round-trips and basic diffusion."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chaoscrypt.encryption import ChaosImageCipher
from chaoscrypt.keys import derive_key


def _img(seed=0, size=32, ch=1):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(size, size) if ch == 1 else (size, size, ch), dtype=np.uint8)


@pytest.mark.parametrize("map_type", ["logistic", "logistic2d", "henon"])
@pytest.mark.parametrize("permute,diffuse", [(True, True), (True, False), (False, True)])
@pytest.mark.parametrize("rounds", [1, 3])
def test_roundtrip_static(map_type, permute, diffuse, rounds):
    key = derive_key("unit-test-key")
    c = ChaosImageCipher(key, map_type=map_type, rounds=rounds,
                         permute=permute, diffuse=diffuse, key_mode="static")
    img = _img()
    assert np.array_equal(c.decrypt(c.encrypt(img)), img)


def test_roundtrip_dynamic_nonce():
    key = derive_key("dyn")
    c = ChaosImageCipher(key, rounds=2, key_mode="dynamic")
    img = _img(1)
    nonce = b"0123456789abcdef"
    assert np.array_equal(c.decrypt(c.encrypt(img, nonce=nonce), nonce=nonce), img)


def test_wrong_key_fails_to_recover():
    img = _img(2)
    good = ChaosImageCipher(derive_key("right"), rounds=2)
    bad = ChaosImageCipher(derive_key("wrong"), rounds=2)
    ct = good.encrypt(img)
    assert not np.array_equal(bad.decrypt(ct), img)


def test_ciphertext_changes_pixels():
    img = _img(3)
    c = ChaosImageCipher(derive_key("k"), rounds=2)
    ct = c.encrypt(img)
    assert np.mean(ct != img) > 0.9        # almost every pixel changed


def test_color_roundtrip():
    key = derive_key("color")
    c = ChaosImageCipher(key, rounds=2)
    img = _img(4, size=32, ch=3)
    assert np.array_equal(c.decrypt(c.encrypt(img)), img)
