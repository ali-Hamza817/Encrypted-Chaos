"""Encrypted-Chaos: deep-learning cryptanalysis of chaos-based image encryption.

Sub-modules
-----------
chaos            chaotic maps + keystream / permutation generation (pure numpy)
keys             deterministic key derivation from a passphrase
encryption       ChaosImageCipher and AESImageCipher (pure numpy / `cryptography`)
crypto_metrics   entropy, NPCR, UACI, correlation, key sensitivity
image_metrics    MSE, PSNR, SSIM
dataset          source images + plaintext/ciphertext pair builder (torch optional)
models           SimpleCNN, UNet  (needs torch)
train            training loop     (needs torch)
evaluate         reconstruction evaluation + Attack Risk verdict
"""

from . import chaos, keys, encryption, crypto_metrics, image_metrics

__all__ = ["chaos", "keys", "encryption", "crypto_metrics", "image_metrics"]
__version__ = "0.1.0"
