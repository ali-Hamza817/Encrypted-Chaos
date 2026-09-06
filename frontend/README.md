# Encrypted-Chaos — frontend

Vite + React + TypeScript + Tailwind, with a few vendored **React Bits**
components (`src/components/reactbits/`, MIT, adapted for a light theme). White
background, Fraunces / Inter / JetBrains Mono.

It talks to the FastAPI backend in [`../app/server.py`](../app/server.py).

## Run locally

```bash
# 1) start the backend (from the repo root)
cd ..
pip install -r requirements.txt
python scripts/run_demo_suite.py          # trains the demo models (once)
python scripts/serve.py                    # http://localhost:8000

# 2) start this frontend
cd frontend
npm install
npm run dev                                 # http://localhost:5173
```

`vite.config.ts` proxies `/api` → `http://127.0.0.1:8000`, so no env config is
needed locally. Override the target with `VITE_API_URL` if the backend runs
elsewhere.

## Deploy

**Frontend → Vercel.** Import the repo, set **Root Directory** to `frontend`.
Framework preset: Vite (already in `vercel.json`). Add an env var
`VITE_API_URL` pointing at your deployed backend.

**Backend → any Python host** (Render, Railway, Fly, Hugging Face Spaces). It
needs PyTorch, so it cannot run on Vercel's serverless runtime. Start command:

```
uvicorn app.server:app --host 0.0.0.0 --port $PORT
```

CORS is already open (`allow_origins=["*"]`); tighten it to your Vercel domain
for production in `app/server.py`.

## Add more React Bits components

`components.json` registers the `@react-bits` registry:

```bash
npx shadcn@latest add @react-bits/silk
npx shadcn@latest add @react-bits/count-up
```
