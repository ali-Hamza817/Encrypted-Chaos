"""Encrypted-Chaos -- FastAPI backend for the interactive MVP.

    python scripts/serve.py         # -> http://localhost:8000
    # or: uvicorn app.server:app --reload

Endpoints
---------
GET  /                 the single-page frontend
GET  /api/health       status + discovered attack models + option lists
POST /api/analyze      encrypt an image + return the cryptographic profile
POST /api/attack       encrypt + run a trained model + return the reconstruction
"""
from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chaoscrypt.crypto_metrics import (correlation_report, histogram_uniformity_chi2,
                                       key_sensitivity, shannon_entropy)
from chaoscrypt.encryption import build_cipher
from chaoscrypt.evaluate import attack_risk
from chaoscrypt.image_metrics import mse, psnr, ssim
from chaoscrypt.utils import load_json

WEB = Path(__file__).resolve().parent / "web"
EXPROOT = ROOT / "experiments"
SIZES = [32, 48, 64, 96, 128]
MAPS = ["logistic", "logistic2d", "henon"]
CFG_KEYS = ("cipher", "map_type", "rounds", "permute", "diffuse", "key_mode")

app = FastAPI(title="Encrypted-Chaos", docs_url="/api/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # dev + Vercel static site; tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(WEB)), name="static")

_MODEL_CACHE: dict[str, tuple] = {}


# ----------------------------------------------------------------- helpers
def _bool(x) -> bool:
    return str(x).strip().lower() in ("1", "true", "yes", "on")


def _clean_size(size) -> int:
    try:
        size = int(size)
    except (TypeError, ValueError):
        return 64
    return size if size in SIZES else 64


def _b64_png(arr, upscale_to: int = 288) -> str:
    a = np.asarray(arr)
    if a.dtype != np.uint8:
        a = np.clip(a, 0.0, 1.0) * 255.0 if a.max() <= 1.0 + 1e-6 else np.clip(a, 0, 255)
        a = a.astype(np.uint8)
    im = Image.fromarray(a, "L" if a.ndim == 2 else "RGB")
    if max(im.size) < upscale_to:
        f = max(1, upscale_to // max(im.size))
        im = im.resize((im.size[0] * f, im.size[1] * f), Image.NEAREST)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _load_image(data: bytes | None, size: int, gray: bool) -> np.ndarray:
    src = io.BytesIO(data) if data else (WEB / "sample.png")
    im = Image.open(src).convert("L" if gray else "RGB").resize((size, size))
    return np.array(im, dtype=np.uint8)


def _spec(cipher, map_type, rounds, permute, diffuse, key_mode, seed) -> dict:
    return {"cipher": cipher, "map_type": map_type, "rounds": int(rounds),
            "permute": _bool(permute), "diffuse": _bool(diffuse),
            "key_mode": key_mode, "seed": seed}


def _pretty(name: str, cfg: dict | None) -> str:
    if not cfg:
        return name
    if cfg.get("cipher") == "aes":
        return "AES-256-CTR"
    bits = []
    if cfg.get("permute") and cfg.get("diffuse"):
        bits.append("permute+diffuse")
    elif cfg.get("diffuse"):
        bits.append("diffusion-only")
    elif cfg.get("permute"):
        bits.append("permutation-only")
    nr = cfg.get("rounds", 1)
    bits.append(f"{nr} round" + ("" if nr == 1 else "s"))
    bits.append(cfg.get("key_mode", "static") + " key")
    return f"{cfg.get('map_type', 'logistic')} map, " + ", ".join(bits)


_HIDE_MODELS = {"smoke"}


def _discover_models() -> list[dict]:
    out = []
    for d in sorted(p.parent for p in EXPROOT.glob("*/model.pt")):
        if d.name in _HIDE_MODELS:
            continue
        info = {"id": d.name, "label": d.name, "psnr": None, "ssim": None,
                "risk": None, "cipher_cfg": None, "size": None, "seed": None,
                "ssim_baseline": None, "ssim_gain": None}
        rep = d / "report.json"
        if rep.exists():
            try:
                r = load_json(rep)
                sc = r.get("scores", {})
                info["psnr"] = sc.get("psnr_mean")
                info["ssim"] = sc.get("ssim_mean")
                info["risk"] = sc.get("risk")
                info["ssim_baseline"] = sc.get("ssim_baseline")
                info["ssim_gain"] = sc.get("ssim_gain")
                tc = r.get("test_cipher") or {}
                info["cipher_cfg"] = {k: tc.get(k) for k in CFG_KEYS}
                info["seed"] = tc.get("seed")
                info["size"] = r.get("config", {}).get("data", {}).get("image_size")
                info["label"] = _pretty(d.name, info["cipher_cfg"])
            except Exception:
                pass
        for k in ("psnr",):
            if info[k] is not None:
                info[k] = round(info[k], 2)
        for k in ("ssim", "ssim_baseline", "ssim_gain"):
            if info[k] is not None:
                info[k] = round(info[k], 3)
        out.append(info)
    # most-successful attack first, so it is the UI's default selection
    out.sort(key=lambda m: (m["ssim_gain"] is None, -(m["ssim_gain"] or 0)))
    return out


def _get_model(model_id: str):
    if model_id not in _MODEL_CACHE:
        import torch
        from chaoscrypt.models import build_model
        pt = EXPROOT / model_id / "model.pt"
        if not pt.exists():
            raise HTTPException(404, f"no trained model '{model_id}'")
        blob = torch.load(pt, map_location="cpu")
        m = build_model(blob["model_cfg"])
        m.load_state_dict(blob["state_dict"])
        m.eval()
        _MODEL_CACHE[model_id] = (m, blob["model_cfg"])
    return _MODEL_CACHE[model_id]


# ----------------------------------------------------------------- routes
@app.get("/")
def index():
    return FileResponse(str(WEB / "index.html"))


@app.get("/api/health")
def health():
    return {"status": "ok", "models": _discover_models(), "maps": MAPS, "sizes": SIZES}


@app.post("/api/analyze")
async def analyze(
    image: UploadFile | None = File(None),
    cipher: str = Form("chaos"), map_type: str = Form("logistic"),
    rounds: int = Form(2), permute: str = Form("true"), diffuse: str = Form("true"),
    key_mode: str = Form("static"), seed: str = Form("thesis-key-01"),
    size: int = Form(64), gray: str = Form("true"),
):
    size = _clean_size(size)
    data = await image.read() if image is not None else None
    try:
        plain = _load_image(data, size, _bool(gray))
    except Exception as e:  # noqa
        raise HTTPException(400, f"could not read image: {e}")

    spec = _spec(cipher, map_type, rounds, permute, diffuse, key_mode, seed)
    try:
        ct = build_cipher(spec).encrypt(plain)
    except Exception as e:  # noqa
        raise HTTPException(400, f"encryption failed: {e}")

    cor, pcor = correlation_report(ct), correlation_report(plain)
    ks = key_sensitivity(lambda s: build_cipher({**spec, "seed": s}), plain, seed)
    return {
        "size": size,
        "spec": spec,
        "plain_png": _b64_png(plain),
        "cipher_png": _b64_png(ct),
        "metrics": {
            "cipher_entropy": round(shannon_entropy(ct), 4),
            "plain_entropy": round(shannon_entropy(plain), 4),
            "corr": {k: round(v, 4) for k, v in cor.items()},
            "plain_corr": {k: round(v, 4) for k, v in pcor.items()},
            "key_sensitivity": {"npcr": round(ks["npcr"], 2), "uaci": round(ks["uaci"], 2)},
            "histogram_chi2": round(histogram_uniformity_chi2(ct), 1),
        },
    }


@app.post("/api/attack")
async def attack(
    image: UploadFile | None = File(None),
    model_id: str = Form(""),
    cipher: str = Form("chaos"), map_type: str = Form("logistic"),
    rounds: int = Form(1), permute: str = Form("false"), diffuse: str = Form("true"),
    key_mode: str = Form("static"), seed: str = Form("demo-key-01"),
    size: int = Form(32), gray: str = Form("true"),
):
    import torch

    size = _clean_size(size)
    data = await image.read() if image is not None else None

    available = _discover_models()
    if not available:
        raise HTTPException(400, "No trained model is available. Run "
                                 "`python scripts/run_demo_suite.py` first.")
    if not model_id or model_id not in {m["id"] for m in available}:
        model_id = available[0]["id"]          # sensible default instead of a 422
    model, mcfg = _get_model(model_id)
    plain = _load_image(data, size, mcfg.get("in_ch", 1) == 1 or _bool(gray))

    spec = _spec(cipher, map_type, rounds, permute, diffuse, key_mode, seed)
    try:
        ct = build_cipher(spec).encrypt(plain)
    except Exception as e:  # noqa
        raise HTTPException(400, f"encryption failed: {e}")

    x = np.ascontiguousarray(np.asarray(ct, np.float32)[None, None] / 255.0)
    with torch.no_grad():
        rec = model(torch.from_numpy(x)).clamp(0, 1).numpy()[0, 0]

    gt = np.asarray(plain, np.float32) / 255.0
    p, s, m = float(psnr(rec, gt)), float(ssim(rec, gt)), float(mse(rec, gt))

    meta = {mm["id"]: mm for mm in _discover_models()}.get(model_id, {})
    tcfg = meta.get("cipher_cfg") or {}
    # judge on gain over the model's "predict the mean image" floor, not raw SSIM
    base = meta.get("ssim_baseline")
    gain = round(s - base, 3) if base is not None else None
    risk = attack_risk({"ssim_mean": s, "psnr_mean": p,
                        **({"ssim_gain": gain} if gain is not None else {})})
    changed = [k for k in CFG_KEYS
               if tcfg.get(k) is not None and tcfg.get(k) != spec.get(k)]
    notes = []
    if changed:
        notes.append("Model trained against " + _pretty(model_id, tcfg)
                     + f". You changed {', '.join(changed)} - reduced recovery is expected "
                       "here (this is the ablation).")
    if meta.get("seed") and meta["seed"] != seed:
        notes.append(f"This model was trained on passphrase '{meta['seed']}'. A static-key "
                     f"attack only inverts the key it learned - a different passphrase "
                     f"defeats it (that gap is exactly RQ1 vs RQ2).")
    if meta.get("size") and meta["size"] != size:
        notes.append(f"Model trained at {meta['size']}px; running at {size}px.")

    return {
        "model_id": model_id, "size": size, "risk": risk, "notes": notes,
        "psnr": round(p, 2), "ssim": round(s, 3), "mse": round(m, 5),
        "ssim_baseline": base, "ssim_gain": gain,
        "plain_png": _b64_png(plain), "cipher_png": _b64_png(ct),
        "recovered_png": _b64_png(rec),
        "trained": {"label": meta.get("label"), "psnr": meta.get("psnr"),
                    "ssim": meta.get("ssim"), "risk": meta.get("risk"),
                    "ssim_baseline": meta.get("ssim_baseline"),
                    "ssim_gain": meta.get("ssim_gain"),
                    "cfg": tcfg, "size": meta.get("size")},
    }
