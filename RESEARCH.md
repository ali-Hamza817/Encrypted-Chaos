# Encrypted-Chaos — Research Framing

**Working thesis title:**
**Deep Learning-Based Cryptanalysis of Chaos-Based Image Encryption Under Known-Plaintext and Unknown-Key Conditions**

This sharpens the supervisor's proposal (*"Using ML to Attack Chaos-based Image Encryption"*, Dr. Ayesha Khalid) into a defensible MS/PhD contribution. Reproducing He et al. (2019) alone is not enough for 2026; the novelty here is **generalization analysis** (unseen keys, unseen schemes), **component-level vulnerability attribution**, and a **fair comparison against a standard primitive (AES)**.

---

## 1. The product

**Encrypted-Chaos** — a benchmark toolkit + dashboard that measures how vulnerable a chaos-based image-encryption scheme is to *data-driven* (learned) cryptanalysis.

It does four things:

1. **Encrypt** — implements configurable chaos ciphers (logistic map, 2D logistic, Hénon) with permutation + diffusion + rounds, plus an **AES-CTR baseline**.
2. **Profile** — computes the standard cryptographic metrics reviewers expect: Shannon entropy, NPCR, UACI, adjacent-pixel correlation (H/V/D), histogram uniformity, key sensitivity.
3. **Attack** — trains CNN / U-Net models to reconstruct plaintext from ciphertext and reports PSNR / SSIM / MSE.
4. **Verdict** — combines reconstruction fidelity into an *Attack Risk* rating (LOW / MEDIUM / HIGH) and attributes it to specific scheme components via ablations.

The dashboard (`app/streamlit_app.py`) is the demo face: upload an image → pick a scheme + key → see ciphertext, crypto metrics, and a live ML attack with the recovered image side-by-side.

---

## 2. Research questions

| # | Question | Experiment | Difficulty | Novelty |
|---|----------|-----------|-----------|---------|
| **RQ1** | Under a *fixed* secret key, can a CNN/U-Net trained on plaintext–ciphertext pairs reconstruct **unseen plaintext images**, and at what fidelity (PSNR/SSIM)? | `configs/rq1_same_key.yaml` | Low | Baseline / reproduction |
| **RQ2** | Does an attack model trained on **many keys** generalize to ciphertexts produced by an **unseen key** (no retraining)? | `configs/rq2_cross_key.yaml` | Medium | ⭐ Primary contribution |
| **RQ3** | Does a model trained on one family of chaotic maps (e.g. logistic) transfer to a **different chaotic construction** (e.g. Hénon / 2D-logistic)? | `configs/rq3_cross_algo.yaml` | High | ⭐ Secondary contribution |
| **RQ4** | Under identical attack budgets, are chaos schemes **more susceptible to learned cryptanalysis than AES-CTR** on the same images? | `configs/rq4_aes_baseline.yaml` | Low | Control / fairness |
| **RQ5** | Which scheme components drive attack success — permutation-only vs diffusion-only, round count, static vs dynamic (per-image) keystream? | ablation sweep | Medium | ⭐ Vulnerability attribution |
| **RQ6** | How many known plaintext–ciphertext pairs are needed to reach a target reconstruction quality (data-efficiency curve)? | pair-count sweep | Low | Practicality bound |

**Hypotheses**

- **H1 (RQ1):** With a static key, diffusion-only schemes collapse to a fixed position-dependent pad; a shallow CNN recovers plaintext at SSIM > 0.9. Adding permutation + rounds sharply degrades this.
- **H2 (RQ2):** Cross-key reconstruction is *substantially* worse than same-key (large SSIM gap). If a model *does* generalize across keys, it has learned a structural weakness of the map, not a key-specific inverse — a stronger result.
- **H3 (RQ3):** Cross-algorithm transfer is near chance unless the schemes share a permutation/diffusion structure.
- **H4 (RQ4):** AES-CTR with a per-image nonce resists learned reconstruction (SSIM ≈ baseline noise) at every budget tested; chaos schemes do not.
- **H5 (RQ5):** Attack success is dominated by (a) static keystream and (b) low round count; permutation contributes the most robustness per unit cost.

---

## 3. Threat model (state this explicitly in the thesis)

- **Attacker capability:** Known-Plaintext Attack (KPA). The attacker holds `N` plaintext–ciphertext pairs under the target key(s) and unlimited ciphertext-only queries afterward.
- **Attacker goal:** *perceptual* plaintext recovery of new ciphertexts — **not** key extraction. Report this honestly; "the model reconstructs images" ≠ "the key is broken."
- **Static vs dynamic key:** In *static* mode the keystream depends only on the secret key (classic weak setting — attacks partly reduce to learning a fixed pad). In *dynamic* mode a per-image public nonce feeds the keystream; the model must approximate the chaotic expansion itself. Both are supported; results must be reported separately.

---

## 4. Evaluation protocol

**Reconstruction (attack side):** MSE ↓, PSNR ↑ (dB), SSIM ↑ ([0,1]). Report mean ± std over a held-out test set that shares **no images** with training.

**Encryption quality (defense side):** entropy (target ≈ 7.99), NPCR (≈ 99.6%), UACI (≈ 33.4%), |correlation| (≈ 0), key sensitivity NPCR (≈ 99.6%). These show the scheme "passes" traditional tests even when the ML attack succeeds — that contrast is the paper's punchline.

**Attack Risk rating (headline):**

| Rating | Condition |
|--------|-----------|
| HIGH | mean SSIM ≥ 0.75 or mean PSNR ≥ 22 dB |
| MEDIUM | 0.40 ≤ SSIM < 0.75 |
| LOW | SSIM < 0.40 |

(Thresholds are configurable and must be calibrated against a same-image "encrypt = identity" ceiling and a "random noise" floor.)

**Result table template** (fill per scheme):

| Condition | PSNR (dB) | SSIM | Risk |
|-----------|-----------|------|------|
| Same key, unseen images (RQ1) | | | |
| Unseen key (RQ2) | | | |
| Unseen key + shifted distribution | | | |
| Cross-algorithm (RQ3) | | | |
| AES-CTR, per-image nonce (RQ4) | | | |

---

## 5. Datasets

- **Prototype / CI:** `synthetic` generator in `chaoscrypt/dataset.py` (gradients + shapes) — zero downloads, pipeline runs in ~1 min.
- **Main:** CIFAR-10 (32×32) for fast iteration → STL-10 / Tiny-ImageNet / DIV2K crops for the final numbers.
- **Domain-shift test (RQ2 "shifted distribution"):** medical (e.g. chest X-ray) or satellite crops as an out-of-distribution test set.

Keep a strict train/test image split. For RQ2, keys are also split: `train_keys` disjoint from `test_key`.

---

## 6. Models

| Role | Model | File |
|------|-------|------|
| Baseline A | `SimpleCNN` (deep, same-resolution, no downsampling) | `chaoscrypt/models.py` |
| Baseline B | `UNet` (encoder–decoder, global context) | `chaoscrypt/models.py` |
| Extension | U-Net + attention / ViT bottleneck | future work |

The contribution is the **cryptanalysis methodology and generalization study**, not a new architecture. Do not over-engineer the network.

---

## 7. 14-week plan

| Weeks | Milestone |
|-------|-----------|
| 1–2 | Finalize scheme implementations; validate `decrypt(encrypt(x)) == x`; reproduce crypto metrics vs literature. |
| 3–4 | Dataset pipeline; RQ1 same-key results on CIFAR-10 (CNN + U-Net). |
| 5–6 | RQ5 ablations (permute/diffuse/rounds/static-dynamic). |
| 7–9 | RQ2 cross-key study + domain-shift test set. |
| 10 | RQ4 AES baseline. |
| 11 | RQ3 cross-algorithm transfer. |
| 12 | RQ6 data-efficiency curves. |
| 13 | Dashboard polish; reproducibility pass; figures. |
| 14 | Thesis write-up. |

---

## 8. Expected contributions

1. A reproducible **benchmark** pairing traditional crypto metrics with learned-attack metrics on the *same* schemes.
2. First systematic **cross-key generalization** study for DL attacks on chaos image encryption.
3. **Component-level vulnerability attribution** (what makes a chaos scheme learnable).
4. Evidence on whether **traditional security metrics predict resistance to data-driven cryptanalysis** (hypothesis: they do not).
5. An open-source tool (`Encrypted-Chaos`) usable by other researchers to pre-screen new schemes.
