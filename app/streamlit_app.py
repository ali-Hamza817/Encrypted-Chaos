"""Encrypted-Chaos -- dashboard.

    streamlit run app/streamlit_app.py

Upload an image -> encrypt with a chosen chaos scheme -> see cryptographic
metrics -> (optionally) load a trained attack model and recover the plaintext.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chaoscrypt.crypto_metrics import (correlation_report, histogram_uniformity_chi2,
                                       key_sensitivity, shannon_entropy)
from chaoscrypt.encryption import build_cipher
from chaoscrypt.image_metrics import psnr, ssim

st.set_page_config(page_title="Encrypted-Chaos", page_icon="🔐", layout="wide")
st.title("🔐 Encrypted-Chaos")
st.caption("Deep-learning cryptanalysis of chaos-based image encryption — MVP dashboard")

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Encryption scheme")
    cipher_kind = st.radio("Cipher", ["chaos", "aes"], horizontal=True)
    map_type = st.selectbox("Chaotic map", ["logistic", "logistic2d", "henon"],
                            disabled=cipher_kind == "aes")
    rounds = st.slider("Rounds", 1, 5, 2, disabled=cipher_kind == "aes")
    permute = st.checkbox("Permutation", value=True, disabled=cipher_kind == "aes")
    diffuse = st.checkbox("Diffusion", value=True, disabled=cipher_kind == "aes")
    key_mode = st.selectbox("Key mode", ["static", "dynamic"])
    seed = st.text_input("Secret key (passphrase)", "thesis-key-01")
    size = st.select_slider("Resize to", [32, 48, 64, 96, 128], value=64)
    gray = st.checkbox("Grayscale", value=True)

    st.divider()
    st.header("Attack model (optional)")
    ckpt = st.text_input("Checkpoint path", "experiments/rq1_same_key/model.pt")
    run_attack = st.button("Run ML attack", type="primary")


def to_array(pil: Image.Image) -> np.ndarray:
    pil = pil.convert("L" if gray else "RGB").resize((size, size))
    return np.array(pil, dtype=np.uint8)


spec = {"cipher": cipher_kind, "seed": seed, "key_mode": key_mode,
        "map_type": map_type, "rounds": rounds, "permute": permute, "diffuse": diffuse}

up = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "bmp"])
if up is None:
    st.info("Upload an image to begin. No model needed for the encryption profile.")
    st.stop()

plain = to_array(Image.open(up))
cipher = build_cipher(spec)
ct = cipher.encrypt(plain)

c1, c2, c3 = st.columns(3)
c1.image(plain, caption="Plaintext", use_container_width=True, clamp=True)
c2.image(ct, caption="Ciphertext", use_container_width=True, clamp=True)

# ------------------------------------------------------------------ crypto profile
with c3:
    st.subheader("Cryptographic profile")
    cor = correlation_report(ct)
    ks = key_sensitivity(lambda s: build_cipher({**spec, "seed": s}), plain, seed)
    st.metric("Entropy (bpp)", f"{shannon_entropy(ct):.4f}", help="ideal ≈ 7.99")
    m1, m2 = st.columns(2)
    m1.metric("Corr H", f"{cor['horizontal']:.4f}")
    m2.metric("Corr V", f"{cor['vertical']:.4f}")
    m1.metric("Key-sens NPCR %", f"{ks['npcr']:.2f}", help="ideal ≈ 99.6")
    m2.metric("Key-sens UACI %", f"{ks['uaci']:.2f}", help="ideal ≈ 33.5")
    st.metric("Histogram χ²", f"{histogram_uniformity_chi2(ct):.1f}", help="lower = more uniform")

st.divider()

# ------------------------------------------------------------------ ML attack
if run_attack:
    try:
        import torch
        from chaoscrypt.models import build_model

        blob = torch.load(ckpt, map_location="cpu")
        model = build_model(blob["model_cfg"])
        model.load_state_dict(blob["state_dict"])
        model.eval()

        x = np.asarray(ct, dtype=np.float32) / 255.0
        x = x[None, None] if x.ndim == 2 else np.moveaxis(x, 2, 0)[None]
        with torch.no_grad():
            rec = model(torch.from_numpy(np.ascontiguousarray(x))).clamp(0, 1).numpy()[0]
        rec_img = (rec[0] if rec.shape[0] == 1 else np.moveaxis(rec, 0, -1))

        gt = np.asarray(plain, dtype=np.float32) / 255.0
        p = psnr(rec_img, gt); s = ssim(rec_img, gt)
        risk = "HIGH" if (s >= 0.75 or p >= 22) else "MEDIUM" if s >= 0.40 else "LOW"

        a, b, cc = st.columns(3)
        a.image(ct, caption="Ciphertext (model input)", use_container_width=True, clamp=True)
        b.image(np.clip(rec_img, 0, 1), caption="Recovered plaintext", use_container_width=True,
                clamp=True)
        cc.image(plain, caption="True plaintext", use_container_width=True, clamp=True)

        k1, k2, k3 = st.columns(3)
        k1.metric("PSNR", f"{p:.2f} dB")
        k2.metric("SSIM", f"{s:.3f}")
        k3.metric("Attack Risk", risk)
        {"HIGH": st.error, "MEDIUM": st.warning, "LOW": st.success}[risk](
            f"Attack Risk: {risk} — SSIM {s:.3f}, PSNR {p:.2f} dB on this sample."
        )
    except FileNotFoundError:
        st.error(f"No checkpoint at `{ckpt}`. Train one first:\n\n"
                 "`python scripts/run_experiment.py configs/rq1_same_key.yaml`")
    except Exception as e:  # noqa
        st.exception(e)
else:
    st.info("Set a checkpoint path and click **Run ML attack** to attempt recovery.")
