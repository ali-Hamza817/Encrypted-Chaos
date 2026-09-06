# Encrypted-Chaos — frontend

Vite + React + TypeScript + Tailwind, with a few vendored **React Bits**
components (`src/components/reactbits/`, MIT, adapted for a light theme). White
background, Poppins / JetBrains Mono.

Talks to the FastAPI backend in [`../backend/`](../backend).

## Run locally

```bash
# 1) backend  (from repo root)
cd backend
pip install -r requirements-dev.txt
python scripts/run_demo_suite.py        # trains the demo models (once)
python scripts/serve.py                  # http://localhost:8000

# 2) this frontend  (new terminal, from repo root)
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

`vite.config.ts` proxies `/api` → `http://127.0.0.1:8000`, so no env config is
needed locally. Override the target with `VITE_API_URL`.

## Deploy

**Frontend → Vercel.** Import the repo, set **Root Directory** to `frontend`
(Vite preset comes from `vercel.json`). Add an environment variable
`VITE_API_URL` pointing at the deployed backend, e.g.
`https://encrypted-chaos-production.up.railway.app`.

**Backend → Railway.** Import the repo, set **Root Directory** to `backend`.
`railway.json` provides the start command and `/api/health` health check. The
four demo models ship in the repo, so the attack works immediately.

## Add more React Bits components

`components.json` registers the `@react-bits` registry:

```bash
npx shadcn@latest add @react-bits/silk
```
