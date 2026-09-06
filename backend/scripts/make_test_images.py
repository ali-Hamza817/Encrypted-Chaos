"""Generate a labelled set of test images for the web app + measure exactly what
the default model should produce for each, so you can verify it works.

    python scripts/make_test_images.py

Writes:
    test_images/in_distribution/*.png     (same style the model trained on)
    test_images/out_of_distribution/*.png  (deliberately different)
    test_images/README.md                  (expected results, measured now)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chaoscrypt.dataset import synthetic_images
from chaoscrypt.encryption import build_cipher
from chaoscrypt.evaluate import mean_image_baseline
from chaoscrypt.image_metrics import psnr, ssim
from chaoscrypt.keys import flip_key_bit
from chaoscrypt.utils import load_json

OUT = ROOT / "test_images"
MODEL_DIR = ROOT / "experiments" / "demo_weak_chaos"
NATIVE = 32          # the size the model was trained at
VIEW = 256           # saved file size (nearest-upscaled, so it survives the app resize)


def save(arr32: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.fromarray(arr32.astype(np.uint8), "L").resize((VIEW, VIEW), Image.NEAREST)
    im.save(path)


# ---------------------------------------------------------------- image makers
def in_distribution() -> list[tuple[str, np.ndarray]]:
    # seeds far from training (train=0, demo test=999) -> genuinely unseen, same style
    imgs = synthetic_images(8, size=NATIVE, channels=1, seed=4242)
    return [(f"sample_{i + 1}", imgs[i]) for i in range(6)]


def ood_text() -> np.ndarray:
    im = Image.new("L", (NATIVE, NATIVE), 235)
    d = ImageDraw.Draw(im)
    d.text((3, 4), "TOP", fill=15)
    d.text((2, 16), "SECRET", fill=15)
    return np.array(im)


def ood_checker() -> np.ndarray:
    y, x = np.mgrid[0:NATIVE, 0:NATIVE]
    return np.where(((x // 4) + (y // 4)) % 2 == 0, 30, 225).astype(np.uint8)


def ood_photo_like() -> np.ndarray:
    y, x = np.mgrid[0:NATIVE, 0:NATIVE].astype(float)
    cx, cy = NATIVE / 2, NATIVE / 2.4
    face = 210 * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * 9.0**2)))
    eyes = 120 * (
        np.exp(-(((x - (cx - 5)) ** 2 + (y - (cy - 2)) ** 2) / 3.0))
        + np.exp(-(((x - (cx + 5)) ** 2 + (y - (cy - 2)) ** 2) / 3.0))
    )
    bg = 60 + 20 * np.sin(x / 5.0)
    return np.clip(bg + face - eyes, 0, 255).astype(np.uint8)


def ood_noise() -> np.ndarray:
    return np.random.default_rng(7).integers(0, 256, (NATIVE, NATIVE), dtype=np.uint8)


# ---------------------------------------------------------------- scoring
def load_model():
    import torch
    from chaoscrypt.models import build_model

    blob = torch.load(MODEL_DIR / "model.pt", map_location="cpu")
    m = build_model(blob["model_cfg"])
    m.load_state_dict(blob["state_dict"])
    m.eval()
    return m


def attack_score(model, img32: np.ndarray, spec: dict) -> tuple[float, float]:
    import torch

    ct = build_cipher(spec).encrypt(img32)
    x = np.ascontiguousarray(np.asarray(ct, np.float32)[None, None] / 255.0)
    with torch.no_grad():
        rec = model(torch.from_numpy(x)).clamp(0, 1).numpy()[0, 0]
    gt = img32.astype(np.float32) / 255.0
    return float(ssim(rec, gt)), float(psnr(rec, gt))


def main() -> None:
    if not (MODEL_DIR / "model.pt").exists():
        sys.exit("train the demo models first:  python scripts/run_demo_suite.py")

    rep = load_json(MODEL_DIR / "report.json")
    tc = rep["test_cipher"]
    base_spec = {k: tc[k] for k in
                 ("cipher", "map_type", "rounds", "permute", "diffuse", "key_mode", "seed")}
    seed = base_spec["seed"]
    model = load_model()

    groups = {
        "in_distribution": in_distribution(),
        "out_of_distribution": [
            ("text", ood_text()),
            ("checkerboard", ood_checker()),
            ("photo_like", ood_photo_like()),
            ("pure_noise", ood_noise()),
        ],
    }

    # floor for "gain": predict-the-mean over the in-distribution batch
    ind = np.stack([a for _, a in groups["in_distribution"]]).astype(np.float32)[:, None] / 255.0
    floor = mean_image_baseline(ind)["ssim_mean"]

    rows = []
    for group, items in groups.items():
        for name, img in items:
            p = OUT / group / f"{name}.png"
            save(img, p)
            s_match, ps_match = attack_score(model, img, base_spec)
            s_shuf, _ = attack_score(model, img, {**base_spec, "permute": True, "rounds": 2})
            s_wrong, _ = attack_score(model, img, {**base_spec, "seed": flip_key_bit(seed)})
            rows.append((group, name, s_match, ps_match, s_match - floor, s_shuf, s_wrong))

    lines = [
        "# Test images",
        "",
        "Upload these in the app (**http://localhost:5173**), keep the cipher set to the",
        f"default **Weak chaos cipher**, and press **Run the AI attack**. The model was",
        f"trained at {NATIVE}x{NATIVE}; the app resizes every upload to that automatically.",
        "",
        "\"Structure recovered\" is the SSIM shown in the app (x100). \"Beat blind guess\"",
        f"is that minus the ~{floor * 100:.0f}% a constant average-image prediction scores.",
        "",
        "## What each file should do",
        "",
        "| File | Matched cipher | Beat blind guess | + Pixel shuffling ON | + Wrong password |",
        "|---|---|---|---|---|",
    ]
    for group, name, s, _ps, gain, s_shuf, s_wrong in rows:
        lines.append(
            f"| `{group}/{name}.png` | **{s * 100:.0f}%** structure | "
            f"{'+' if gain >= 0 else ''}{gain * 100:.0f} pts | "
            f"{s_shuf * 100:.0f}% (collapses) | {s_wrong * 100:.0f}% (collapses) |"
        )

    lines += [
        "",
        "## How to know the model is working",
        "",
        "1. **It recovers the in-distribution samples.** Upload any `in_distribution/*.png`",
        "   with the matched **Weak chaos cipher** -> the app should say *\"The attack worked\"*",
        "   and show a recovered image that clearly resembles the original (structure ~60-85%,",
        "   beating the blind-guess baseline by a wide margin).",
        "",
        "2. **It collapses when you change the cipher.** Same image, turn **Pixel shuffling**",
        "   ON (or raise Passes) and re-run -> recovery drops to a few percent and the verdict",
        "   flips to *\"The attack failed\"*. The model learned *this* cipher's inverse, not magic.",
        "",
        "3. **It collapses on a wrong password.** In advanced settings, change the password by",
        "   one character -> recovery collapses. A static-key attack only inverts the key it",
        "   was trained on (this is the RQ1 vs RQ2 gap in the research).",
        "",
        "4. **It degrades on out-of-distribution images.** `text.png` and `photo_like.png`",
        "   (sharp edges / smooth gradients unlike the training style) recover only partially,",
        "   and `pure_noise.png` not at all (SSIM on noise-vs-noise is meaningless, gain <= 0).",
        "   `checkerboard.png` still recovers well - it is trivially low-entropy. The CNN",
        "   learned a smooth approximation tuned to the training image style, not an exact",
        "   decryptor. Expected and honest.",
        "",
        "5. **AES and the hardened chaos ciphers never recover anything** (~5%, *\"attack",
        "   failed\"*) for any image. That contrast is the whole point.",
        "",
        "If 1-3 hold, the pipeline (encryption -> model -> scoring) is wired correctly.",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {sum(len(v) for v in groups.values())} images + README to {OUT}")
    for group, name, s, _ps, gain, s_shuf, s_wrong in rows:
        print(f"  {group:20s} {name:14s} match {s*100:5.1f}%  gain {gain*100:+5.1f}  "
              f"shuffle {s_shuf*100:4.1f}%  wrongkey {s_wrong*100:4.1f}%")


if __name__ == "__main__":
    main()
