// API client for the Encrypted-Chaos FastAPI backend.
// Local dev: Vite proxies /api -> http://127.0.0.1:8000 (see vite.config.ts).
// Production: set VITE_API_URL to the deployed backend origin.

const BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
const url = (p: string) => `${BASE}${p}`;

export type ModelInfo = {
  id: string;
  label: string;
  psnr: number | null;
  ssim: number | null;
  risk: string | null;
  ssim_baseline: number | null;
  ssim_gain: number | null;
  size: number | null;
  seed: string | null;
  cipher_cfg: Record<string, unknown> | null;
};

export type Health = {
  status: string;
  models: ModelInfo[];
  maps: string[];
  sizes: number[];
};

export type Corr = { horizontal: number; vertical: number; diagonal: number };

export type AnalyzeResult = {
  size: number;
  spec: Record<string, unknown>;
  plain_png: string;
  cipher_png: string;
  metrics: {
    cipher_entropy: number;
    plain_entropy: number;
    corr: Corr;
    plain_corr: Corr;
    key_sensitivity: { npcr: number; uaci: number };
    histogram_chi2: number;
  };
};

export type AttackResult = {
  model_id: string;
  size: number;
  risk: "HIGH" | "MEDIUM" | "LOW";
  notes: string[];
  psnr: number;
  ssim: number;
  mse: number;
  ssim_baseline: number | null;
  ssim_gain: number | null;
  plain_png: string;
  cipher_png: string;
  recovered_png: string;
  trained: {
    label: string | null;
    psnr: number | null;
    ssim: number | null;
    ssim_baseline: number | null;
    ssim_gain: number | null;
    size: number | null;
    cfg: Record<string, unknown>;
  };
};

export type SchemeForm = {
  cipher: "chaos" | "aes";
  map_type: string;
  rounds: number;
  permute: boolean;
  diffuse: boolean;
  key_mode: "static" | "dynamic";
  seed: string;
  size: number;
  model_id?: string;
};

function buildForm(f: SchemeForm, file: File | null): FormData {
  const fd = new FormData();
  if (file) fd.append("image", file);
  fd.append("cipher", f.cipher);
  fd.append("map_type", f.map_type);
  fd.append("rounds", String(f.rounds));
  fd.append("permute", String(f.permute));
  fd.append("diffuse", String(f.diffuse));
  fd.append("key_mode", f.key_mode);
  fd.append("seed", f.seed || "key");
  fd.append("size", String(f.size));
  fd.append("gray", "true");
  if (f.model_id) fd.append("model_id", f.model_id);
  return fd;
}

async function readError(r: Response): Promise<string> {
  try {
    const j = await r.json();
    const d = j?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d) && d.length) {
      return d
        .map((e) => e?.msg + (e?.loc ? ` (${e.loc.join(".")})` : ""))
        .join("; ");
    }
    return JSON.stringify(j);
  } catch {
    return `${r.status} ${r.statusText}`;
  }
}

export async function getHealth(): Promise<Health> {
  const r = await fetch(url("/api/health"));
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

export async function analyze(f: SchemeForm, file: File | null): Promise<AnalyzeResult> {
  const r = await fetch(url("/api/analyze"), { method: "POST", body: buildForm(f, file) });
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

export async function attack(f: SchemeForm, file: File | null): Promise<AttackResult> {
  const r = await fetch(url("/api/attack"), { method: "POST", body: buildForm(f, file) });
  if (!r.ok) throw new Error(await readError(r));
  return r.json();
}

export const png = (b64: string) => `data:image/png;base64,${b64}`;
