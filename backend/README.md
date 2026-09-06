---
title: Encrypted-Chaos API
emoji: 🔓
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Encrypted-Chaos — backend API

FastAPI service for **[Encrypted-Chaos](https://github.com/ali-Hamza817/Encrypted-Chaos)**:
deep-learning cryptanalysis of chaos-based image encryption.

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | status + the trained attack models it found |
| `POST /api/analyze` | encrypt an image, return the cryptographic profile |
| `POST /api/attack` | encrypt + run a trained model + return the reconstruction |

The four demo models ship in `experiments/demo_*/`, so `/api/attack` works
immediately. `GET /` also serves a small self-contained dashboard.

## Run locally

```bash
pip install -r requirements-dev.txt
python scripts/serve.py            # http://localhost:8000
# or:  uvicorn app.server:app --reload
```

## Deploy

**Docker** (Hugging Face Spaces / Render / Fly / Cloud Run): `Dockerfile` listens
on `$PORT` (default 7860). Nothing else to configure.

**Nixpacks** (Railway): `railway.json` sets the start command and `/api/health`
check; the builder installs `requirements.txt` (CPU-only PyTorch).

CORS is open (`allow_origins=["*"]`) — restrict it to your frontend domain in
`app/server.py` for production.
