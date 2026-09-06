"""Sanity checks for the metric implementations."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chaoscrypt.crypto_metrics import npcr, shannon_entropy, uaci
from chaoscrypt.encryption import ChaosImageCipher
from chaoscrypt.image_metrics import mse, psnr, ssim
from chaoscrypt.keys import derive_key


def test_entropy_bounds():
    zeros = np.zeros((32, 32), dtype=np.uint8)
    assert shannon_entropy(zeros) == 0.0
    rng = np.random.default_rng(0)
    noise = rng.integers(0, 256, (256, 256), dtype=np.uint8)
    assert shannon_entropy(noise) > 7.9


def test_cipher_entropy_high():
    rng = np.random.default_rng(1)
    img = rng.integers(0, 256, (64, 64), dtype=np.uint8)
    ct = ChaosImageCipher(derive_key("k"), rounds=2).encrypt(img)
    assert shannon_entropy(ct) > 7.5


def test_npcr_uaci_identical_zero():
    a = np.full((16, 16), 100, dtype=np.uint8)
    assert npcr(a, a) == 0.0
    assert uaci(a, a) == 0.0


def test_psnr_ssim_identity():
    x = np.random.default_rng(2).random((1, 32, 32)).astype(np.float32)
    assert psnr(x, x) >= 99.0
    assert ssim(x, x) > 0.999
    assert mse(x, x) == 0.0


def test_psnr_orders_correctly():
    x = np.zeros((1, 16, 16), dtype=np.float32)
    near = x + 0.01
    far = x + 0.5
    assert psnr(x, near) > psnr(x, far)
