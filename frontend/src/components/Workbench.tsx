import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  analyze,
  attack,
  getHealth,
  png,
  type AnalyzeResult,
  type AttackResult,
  type ModelInfo,
  type SchemeForm,
} from "../lib/api";
import SpotlightCard from "./reactbits/SpotlightCard";
import CountUp from "./reactbits/CountUp";

const DEFAULT_FORM: SchemeForm = {
  cipher: "chaos",
  map_type: "logistic",
  rounds: 2,
  permute: true,
  diffuse: true,
  key_mode: "static",
  seed: "thesis-key-01",
  size: 64,
  model_id: "",
};

/* ---------------------------------------------------- plain-language helpers */

function humanModel(m: ModelInfo) {
  const c = (m.cipher_cfg ?? {}) as Record<string, unknown>;
  const tech = m.label;
  if (c.cipher === "aes")
    return {
      name: "AES-256 — the industry standard",
      tech,
      blurb: "What real software uses. This should be impossible to break.",
    };
  const perm = Boolean(c.permute);
  const diff = Boolean(c.diffuse);
  const dyn = c.key_mode === "dynamic";
  if (perm && diff && dyn)
    return {
      name: "Hardened chaos cipher",
      tech,
      blurb: "Shuffles pixels, mixes their values, and uses a fresh key for every image.",
    };
  if (perm && diff)
    return {
      name: "Full chaos cipher",
      tech,
      blurb: "Shuffles pixel positions and scrambles their brightness.",
    };
  if (diff && !perm)
    return {
      name: "Weak chaos cipher",
      tech,
      blurb: "Only scrambles brightness — it never moves pixels. The known-weak case.",
    };
  if (perm && !diff)
    return { name: "Shuffle-only chaos cipher", tech, blurb: "Only rearranges pixels." };
  return { name: "Chaos cipher", tech, blurb: "" };
}

function verdictCopy(risk: string) {
  if (risk === "HIGH")
    return {
      title: "The attack worked",
      line: "The AI rebuilt the picture from the encrypted version alone — it never saw the password.",
      tone: "high" as const,
    };
  if (risk === "MEDIUM")
    return {
      title: "Partial break",
      line: "The AI recovered rough shapes and layout, but not fine detail.",
      tone: "med" as const,
    };
  return {
    title: "The attack failed",
    line: "The encrypted image gave the AI nothing to work with — exactly what a strong cipher should do.",
    tone: "low" as const,
  };
}

const toneRing: Record<string, string> = {
  high: "border-risk-high/30 bg-risk-high/[0.04]",
  med: "border-risk-med/30 bg-risk-med/[0.04]",
  low: "border-risk-low/30 bg-risk-low/[0.04]",
};
const toneText: Record<string, string> = {
  high: "text-risk-high",
  med: "text-risk-med",
  low: "text-risk-low",
};

/* ---------------------------------------------------------------- tiny parts */

function Info({ text }: { text: string }) {
  return (
    <span
      tabIndex={0}
      title={text}
      className="ml-1 inline-grid h-3.5 w-3.5 cursor-help place-items-center rounded-full border border-ink-dim/40 text-[9px] font-bold text-ink-dim align-text-top"
    >
      ?
    </span>
  );
}

function Segmented({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { v: string; label: string }[];
}) {
  return (
    <div className="flex overflow-hidden rounded-xl border border-line">
      {options.map((o) => (
        <button
          key={o.v}
          type="button"
          onClick={() => onChange(o.v)}
          aria-pressed={value === o.v}
          className={`flex-1 px-3 py-2 text-xs font-semibold transition ${
            value === o.v ? "bg-brand text-white" : "bg-mist text-ink-dim hover:text-ink"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function ToggleRow({
  label,
  hint,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  hint: string;
  checked: boolean;
  onChange: (b: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`flex w-full items-start justify-between gap-3 rounded-xl border p-3 text-left transition ${
        checked ? "border-brand/40 bg-brand-soft/25" : "border-line bg-mist"
      } ${disabled ? "opacity-40" : "hover:border-ink-dim/40"}`}
    >
      <span>
        <span className="block text-sm font-semibold text-ink">{label}</span>
        <span className="mt-0.5 block text-xs text-ink-dim">{hint}</span>
      </span>
      <span
        className={`relative mt-0.5 h-5 w-9 shrink-0 rounded-full border transition ${
          checked ? "border-brand bg-brand" : "border-line bg-white"
        }`}
      >
        <span
          className={`absolute top-0.5 h-3.5 w-3.5 rounded-full bg-white shadow transition ${
            checked ? "left-[18px]" : "left-0.5 bg-ink-dim"
          }`}
        />
      </span>
    </button>
  );
}

function ImageCard({
  step,
  title,
  caption,
  src,
  placeholder,
  highlight,
}: {
  step: string;
  title: string;
  caption: string;
  src?: string;
  placeholder: string;
  highlight?: boolean;
}) {
  return (
    <figure
      className={`overflow-hidden rounded-2xl border bg-white ${
        highlight ? "border-brand shadow-lift" : "border-line"
      }`}
    >
      <figcaption className="flex items-center gap-2 border-b border-line px-3 py-2">
        <span className="grid h-5 w-5 place-items-center rounded-full bg-mist font-mono text-[10px] font-bold text-ink-dim">
          {step}
        </span>
        <span className="text-xs font-semibold text-ink">{title}</span>
      </figcaption>
      <div
        className="grid aspect-square place-items-center p-2"
        style={{
          backgroundImage:
            "repeating-conic-gradient(#eef2f6 0% 25%, transparent 0% 50%)",
          backgroundSize: "14px 14px",
        }}
      >
        {src ? (
          <img
            src={src}
            alt={title}
            className="h-full w-full rounded-lg object-contain"
            style={{ imageRendering: "pixelated" }}
          />
        ) : (
          <span className="px-3 text-center text-[11px] leading-snug text-ink-dim">
            {placeholder}
          </span>
        )}
      </div>
      <div className="border-t border-line px-3 py-2 text-[11px] text-ink-dim">
        {caption}
      </div>
    </figure>
  );
}

function ScoreTile({
  label,
  value,
  scale,
  meaning,
  good,
}: {
  label: string;
  value: string;
  scale: string;
  meaning: string;
  good?: boolean | null;
}) {
  return (
    <div className="rounded-xl border border-line bg-white p-3.5">
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-semibold text-ink">{label}</span>
        {good != null && (
          <span
            className={`font-mono text-[10px] font-bold ${
              good ? "text-risk-low" : "text-ink-dim"
            }`}
          >
            {good ? "STRONG" : "WEAK"}
          </span>
        )}
      </div>
      <div className="mt-1 font-mono text-2xl tabular-nums text-ink">{value}</div>
      <div className="mt-0.5 font-mono text-[10px] uppercase tracking-wide text-ink-dim">
        {scale}
      </div>
      <p className="mt-1.5 text-[11px] leading-snug text-ink-dim">{meaning}</p>
    </div>
  );
}

function SecurityCheck({
  label,
  pass,
  detail,
}: {
  label: string;
  pass: boolean;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-2.5 rounded-xl border border-line bg-white p-3">
      <span
        className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full text-[10px] font-bold text-white ${
          pass ? "bg-risk-low" : "bg-risk-med"
        }`}
      >
        {pass ? "✓" : "!"}
      </span>
      <div>
        <span className="block text-xs font-semibold text-ink">{label}</span>
        <span className="mt-0.5 block text-[11px] leading-snug text-ink-dim">{detail}</span>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- main */

export default function Workbench() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [form, setForm] = useState<SchemeForm>(DEFAULT_FORM);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState<"" | "analyze" | "attack">("");
  const [aRes, setARes] = useState<AnalyzeResult | null>(null);
  const [kRes, setKRes] = useState<AttackResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const set = <K extends keyof SchemeForm>(k: K, v: SchemeForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const currentModel = useMemo(
    () => models.find((m) => m.id === form.model_id),
    [models, form.model_id],
  );

  const syncToModel = useCallback((m: ModelInfo) => {
    const c = (m.cipher_cfg ?? {}) as Record<string, unknown>;
    setForm((f) => ({
      ...f,
      model_id: m.id,
      cipher: (c.cipher as SchemeForm["cipher"]) ?? f.cipher,
      map_type: (c.map_type as string) ?? f.map_type,
      rounds: (c.rounds as number) ?? f.rounds,
      permute: c.permute != null ? Boolean(c.permute) : f.permute,
      diffuse: c.diffuse != null ? Boolean(c.diffuse) : f.diffuse,
      key_mode: (c.key_mode as SchemeForm["key_mode"]) ?? f.key_mode,
      size: m.size ?? f.size,
      seed: m.seed ?? f.seed,
    }));
  }, []);

  useEffect(() => {
    getHealth()
      .then((h) => {
        setModels(h.models);
        if (h.models[0]) syncToModel(h.models[0]);
      })
      .catch((e) => setErr(`Can't reach the backend. Is it running on port 8000? (${e.message})`));
  }, [syncToModel]);

  const pickFile = (f: File) => {
    setFile(f);
    setKRes(null);
    setARes(null);
    setPreview((p) => {
      if (p) URL.revokeObjectURL(p);
      return URL.createObjectURL(f);
    });
  };
  const clearFile = () => {
    setFile(null);
    setKRes(null);
    setARes(null);
    setPreview((p) => {
      if (p) URL.revokeObjectURL(p);
      return null;
    });
    if (fileInput.current) fileInput.current.value = "";
  };

  const run = async (kind: "analyze" | "attack") => {
    setErr(null);
    setBusy(kind);
    try {
      if (kind === "analyze") setARes(await analyze(form, file));
      else setKRes(await attack(form, file));
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy("");
    }
  };

  const aes = form.cipher === "aes";
  const hm = currentModel ? humanModel(currentModel) : null;
  const m = aRes?.metrics;
  const gain = kRes?.ssim_gain ?? null;
  const verdict = kRes ? verdictCopy(kRes.risk) : null;

  // security checks derived from the crypto profile
  const checks = m
    ? [
        {
          label: "Looks like random noise",
          pass: m.cipher_entropy >= 7.9,
          detail: `Randomness score ${m.cipher_entropy.toFixed(2)} out of 8.00 — a strong cipher is right at 8.`,
        },
        {
          label: "No leftover patterns",
          pass:
            Math.max(
              Math.abs(m.corr.horizontal),
              Math.abs(m.corr.vertical),
              Math.abs(m.corr.diagonal),
            ) <= 0.05,
          detail:
            "Neighbouring pixels in the encrypted image are unrelated (correlation ≈ 0), so there's no visible structure to exploit.",
        },
        {
          label: "Tiny password change = totally different",
          pass: m.key_sensitivity.npcr >= 99,
          detail: `Flip one bit of the password and ${m.key_sensitivity.npcr.toFixed(
            1,
          )}% of pixels change. A brute-force guesser gets no warm/cold signal.`,
        },
      ]
    : [];

  return (
    <section id="workbench" className="scroll-mt-20 py-16">
      <div className="wrap">
        {/* ---- intro ---- */}
        <span className="eyebrow">Try it yourself</span>
        <h2 className="mt-2 text-3xl sm:text-4xl">Upload · encrypt · recover</h2>
        <p className="mt-3 max-w-2xl text-ink-soft">
          Watch a neural network rebuild a picture from its <i>encrypted</i> version —
          without ever being given the password. It's loaded with a sample image, so you
          can just press <b className="text-ink">Run the AI attack</b> below.
        </p>

        <ol className="mt-6 grid gap-3 sm:grid-cols-3">
          {[
            ["1", "Pick an image", "Use the built-in sample or drop your own."],
            ["2", "Choose a cipher to break", "Pick how the image gets encrypted."],
            ["3", "Run the AI attack", "See how much of the original it recovers."],
          ].map(([n, t, d]) => (
            <li
              key={n}
              className="flex items-start gap-3 rounded-xl border border-line bg-mist p-3"
            >
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-brand font-mono text-xs font-bold text-white">
                {n}
              </span>
              <span>
                <span className="block text-sm font-semibold text-ink">{t}</span>
                <span className="mt-0.5 block text-xs text-ink-dim">{d}</span>
              </span>
            </li>
          ))}
        </ol>

        <div className="mt-8 grid gap-6 lg:grid-cols-[380px_1fr]">
          {/* ============ SETUP ============ */}
          <form className="card p-5" onSubmit={(e) => e.preventDefault()}>
            <div className="flex flex-col gap-5">
              {/* step 1 */}
              <div>
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-mist font-mono text-[10px] text-ink-dim">
                    1
                  </span>
                  Your image
                </div>
                <div
                  tabIndex={0}
                  role="button"
                  onClick={() => fileInput.current?.click()}
                  onKeyDown={(e) =>
                    (e.key === "Enter" || e.key === " ") && fileInput.current?.click()
                  }
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (e.dataTransfer.files[0]) pickFile(e.dataTransfer.files[0]);
                  }}
                  className="cursor-pointer rounded-xl border border-dashed border-line bg-mist p-4 text-center text-sm text-ink-dim transition hover:border-brand hover:bg-brand-soft/30 focus:outline-none focus:ring-4 focus:ring-brand-soft"
                >
                  {preview ? (
                    <img
                      src={preview}
                      alt="your upload"
                      className="mx-auto mb-2 h-24 w-24 rounded-lg border border-line object-cover"
                      style={{ imageRendering: "pixelated" }}
                    />
                  ) : (
                    <div className="py-3">
                      <span className="font-medium text-ink">Using the sample image</span>
                      <div className="mt-1">Click or drop a PNG / JPG to use your own</div>
                    </div>
                  )}
                  {file && (
                    <div className="mt-1 flex items-center justify-between font-mono text-[11px]">
                      <span className="truncate">{file.name}</span>
                      <button
                        type="button"
                        className="text-brand-ink underline"
                        onClick={(e) => {
                          e.stopPropagation();
                          clearFile();
                        }}
                      >
                        back to sample
                      </button>
                    </div>
                  )}
                  <input
                    ref={fileInput}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) =>
                      e.target.files?.[0] && pickFile(e.target.files[0])
                    }
                  />
                </div>
              </div>

              {/* step 2 */}
              <div>
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-mist font-mono text-[10px] text-ink-dim">
                    2
                  </span>
                  Cipher to break
                </div>
                <select
                  className="input"
                  value={form.model_id}
                  onChange={(e) => {
                    const mm = models.find((x) => x.id === e.target.value);
                    if (mm) syncToModel(mm);
                    else set("model_id", e.target.value);
                  }}
                >
                  {models.length === 0 && <option value="">no trained model found</option>}
                  {models.map((mm) => (
                    <option key={mm.id} value={mm.id}>
                      {humanModel(mm).name}
                    </option>
                  ))}
                </select>
                {hm && (
                  <div className="mt-2 rounded-xl bg-mist p-3">
                    <p className="text-xs text-ink-soft">{hm.blurb}</p>
                    {currentModel?.ssim != null && (
                      <p className="mt-1.5 text-[11px] text-ink-dim">
                        In testing, this attack model rebuilt{" "}
                        <b className="text-ink">
                          {Math.round((currentModel.ssim ?? 0) * 100)}%
                        </b>{" "}
                        of image structure (a blind guess gets{" "}
                        {Math.round((currentModel.ssim_baseline ?? 0) * 100)}%).
                      </p>
                    )}
                    <p className="mt-1 font-mono text-[10px] text-ink-dim/70">{hm.tech}</p>
                  </div>
                )}
              </div>

              {/* step 3 knobs */}
              <div>
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-mist font-mono text-[10px] text-ink-dim">
                    3
                  </span>
                  Tweak the cipher, then attack
                </div>
                <p className="mb-2.5 text-xs text-ink-dim">
                  These start matched to the model above. Turn one off and re-run to see
                  the recovery change.
                </p>
                <div className="flex flex-col gap-2.5">
                  <ToggleRow
                    label="Pixel shuffling"
                    hint="Moves every pixel to a scrambled position."
                    checked={form.permute}
                    disabled={aes}
                    onChange={(b) => set("permute", b)}
                  />
                  <ToggleRow
                    label="Value mixing"
                    hint="Scrambles each pixel's brightness with a chaotic keystream."
                    checked={form.diffuse}
                    disabled={aes}
                    onChange={(b) => set("diffuse", b)}
                  />
                </div>

                <button
                  type="button"
                  onClick={() => setShowAdvanced((s) => !s)}
                  className="mt-3 text-xs font-medium text-brand-ink underline"
                >
                  {showAdvanced ? "Hide" : "Show"} advanced settings
                </button>
                {showAdvanced && (
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <span className="field-label">Cipher family</span>
                      <div className="mt-1">
                        <Segmented
                          value={form.cipher}
                          onChange={(v) => set("cipher", v as SchemeForm["cipher"])}
                          options={[
                            { v: "chaos", label: "Chaos" },
                            { v: "aes", label: "AES-256" },
                          ]}
                        />
                      </div>
                    </div>
                    <label className="flex flex-col gap-1">
                      <span className="field-label">
                        Chaos formula
                        <Info text="The mathematical map that generates the pseudo-random keystream." />
                      </span>
                      <select
                        className="input"
                        disabled={aes}
                        value={form.map_type}
                        onChange={(e) => set("map_type", e.target.value)}
                      >
                        <option value="logistic">Logistic map</option>
                        <option value="logistic2d">2D logistic</option>
                        <option value="henon">Hénon map</option>
                      </select>
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="field-label">
                        Key style
                        <Info text="Static = same key every image (a fixed pad, learnable). Dynamic = a fresh key per image." />
                      </span>
                      <select
                        className="input"
                        value={form.key_mode}
                        onChange={(e) =>
                          set("key_mode", e.target.value as SchemeForm["key_mode"])
                        }
                      >
                        <option value="static">Same key always</option>
                        <option value="dynamic">New key per image</option>
                      </select>
                    </label>
                    <label className="col-span-2 flex flex-col gap-1">
                      <span className="field-label">
                        Passes — <span className="text-ink">{form.rounds}</span>
                        <Info text="How many times shuffle + mix are repeated." />
                      </span>
                      <input
                        type="range"
                        min={1}
                        max={5}
                        step={1}
                        disabled={aes}
                        value={form.rounds}
                        onChange={(e) => set("rounds", Number(e.target.value))}
                        className="accent-brand"
                      />
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="field-label">Password</span>
                      <input
                        className="input"
                        value={form.seed}
                        onChange={(e) => set("seed", e.target.value)}
                      />
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="field-label">Image size</span>
                      <select
                        className="input"
                        value={form.size}
                        onChange={(e) => set("size", Number(e.target.value))}
                      >
                        {[32, 48, 64, 96, 128].map((s) => (
                          <option key={s} value={s}>
                            {s}×{s}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-2.5 border-t border-line pt-4">
                <button
                  type="button"
                  className="btn-primary"
                  disabled={busy !== "" || models.length === 0}
                  onClick={() => run("attack")}
                >
                  {busy === "attack" ? "Attacking…" : "▶  Run the AI attack"}
                </button>
                <button
                  type="button"
                  className="btn-ghost"
                  disabled={busy !== ""}
                  onClick={() => run("analyze")}
                >
                  {busy === "analyze"
                    ? "Encrypting…"
                    : "Encrypt & check the cipher's strength"}
                </button>
              </div>

              {err && (
                <div className="rounded-xl border border-risk-high/40 bg-risk-high/5 px-3 py-2 text-xs text-risk-high">
                  {err}
                </div>
              )}
            </div>
          </form>

          {/* ============ RESULTS ============ */}
          <div className="flex flex-col gap-5">
            {/* verdict */}
            <AnimatePresence mode="wait">
              {verdict ? (
                <motion.div
                  key={kRes?.risk}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`rounded-2xl border p-5 ${toneRing[verdict.tone]}`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`grid h-6 w-6 place-items-center rounded-full text-sm font-bold text-white ${
                        verdict.tone === "high"
                          ? "bg-risk-high"
                          : verdict.tone === "med"
                            ? "bg-risk-med"
                            : "bg-risk-low"
                      }`}
                    >
                      {verdict.tone === "low" ? "✓" : "!"}
                    </span>
                    <h3 className={`text-lg ${toneText[verdict.tone]}`}>{verdict.title}</h3>
                  </div>
                  <p className="mt-2 text-sm text-ink-soft">{verdict.line}</p>
                  <div className="mt-3 flex flex-wrap items-end gap-x-6 gap-y-1">
                    <div>
                      <div className="font-mono text-3xl tabular-nums text-ink">
                        <CountUp to={Math.round(kRes!.ssim * 100)} suffix="%" />
                      </div>
                      <div className="text-[11px] text-ink-dim">
                        of the image structure recovered
                      </div>
                    </div>
                    <div className="text-xs text-ink-dim">
                      A blind guess (just the average image) scores{" "}
                      {Math.round((kRes!.ssim_baseline ?? 0) * 100)}%. This model beat that
                      by{" "}
                      <b className={toneText[verdict.tone]}>
                        {gain != null && gain >= 0 ? "+" : ""}
                        {gain != null ? Math.round(gain * 100) : "—"} points
                      </b>
                      .
                    </div>
                  </div>
                  {kRes!.notes?.length > 0 && (
                    <div className="mt-3 flex flex-col gap-1.5">
                      {kRes!.notes.map((n, i) => (
                        <p
                          key={i}
                          className="rounded-lg bg-white/70 px-3 py-2 text-[11px] text-ink-dim"
                        >
                          {n}
                        </p>
                      ))}
                    </div>
                  )}
                </motion.div>
              ) : (
                <div className="rounded-2xl border border-dashed border-line bg-mist p-5 text-sm text-ink-dim">
                  Press <b className="text-ink">Run the AI attack</b> — the recovered image
                  and a plain-English verdict will appear here.
                </div>
              )}
            </AnimatePresence>

            {/* image trio */}
            <SpotlightCard className="card p-5">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <ImageCard
                  step="A"
                  title="Original"
                  placeholder="Your photo — what we're trying to recover."
                  caption="The secret picture."
                  src={
                    kRes ? png(kRes.plain_png) : aRes ? png(aRes.plain_png) : undefined
                  }
                />
                <ImageCard
                  step="B"
                  title="Encrypted"
                  placeholder="What an eavesdropper sees — should look like TV static."
                  caption="Sent over the wire. This is all the AI gets."
                  src={
                    kRes ? png(kRes.cipher_png) : aRes ? png(aRes.cipher_png) : undefined
                  }
                />
                <ImageCard
                  step="C"
                  title="AI's reconstruction"
                  placeholder="The model's guess at the original — appears after an attack."
                  caption={
                    kRes
                      ? `Rebuilt from B alone, no password. Match: ${Math.round(
                          kRes.ssim * 100,
                        )}%.`
                      : "Run the attack to fill this in."
                  }
                  src={kRes ? png(kRes.recovered_png) : undefined}
                  highlight={!!kRes}
                />
              </div>
            </SpotlightCard>

            {/* how good is the recovery */}
            <AnimatePresence>
              {kRes && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="card p-5"
                >
                  <h3 className="text-base">How good is the reconstruction?</h3>
                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <ScoreTile
                      label="Structure match"
                      value={kRes.ssim.toFixed(2)}
                      scale="0 = nothing · 1 = identical"
                      meaning="How much of the shapes, edges and layout the AI got right (SSIM)."
                    />
                    <ScoreTile
                      label="Beat a blind guess by"
                      value={`${gain != null && gain >= 0 ? "+" : ""}${(gain ?? 0).toFixed(2)}`}
                      scale="above 0.12 = learned something real"
                      meaning="Improvement over just predicting the average of all images. This is the honest measure of a break."
                      good={gain != null ? gain >= 0.12 : null}
                    />
                    <ScoreTile
                      label="Sharpness"
                      value={`${kRes.psnr.toFixed(0)} dB`}
                      scale="higher = closer to original"
                      meaning="Pixel-level closeness (PSNR). ~30 dB looks near-perfect; ~13 dB is noise."
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* is the encryption any good */}
            <AnimatePresence>
              {m && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="card p-5"
                >
                  <h3 className="text-base">Is the encryption itself any good?</h3>
                  <p className="mt-1 text-xs text-ink-dim">
                    These are the textbook checks a cryptography reviewer runs. The twist
                    of this research: a cipher can pass all of them and still lose to the
                    AI above.
                  </p>
                  <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-3">
                    {checks.map((c) => (
                      <SecurityCheck key={c.label} {...c} />
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowRaw((s) => !s)}
                    className="mt-3 text-xs font-medium text-brand-ink underline"
                  >
                    {showRaw ? "Hide" : "Show"} raw numbers
                  </button>
                  {showRaw && (
                    <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1.5 font-mono text-xs">
                      {[
                        ["Cipher entropy", m.cipher_entropy.toFixed(4), "≈ 7.99"],
                        ["Plain entropy", m.plain_entropy.toFixed(4), "—"],
                        ["Corr — horizontal", m.corr.horizontal.toFixed(4), "0"],
                        ["Corr — vertical", m.corr.vertical.toFixed(4), "0"],
                        ["Corr — diagonal", m.corr.diagonal.toFixed(4), "0"],
                        ["Key-sens NPCR", `${m.key_sensitivity.npcr.toFixed(2)}%`, "≈ 99.6"],
                        ["Key-sens UACI", `${m.key_sensitivity.uaci.toFixed(2)}%`, "≈ 33.5"],
                        ["Histogram χ²", m.histogram_chi2.toFixed(1), "≈ 255"],
                      ].map(([k, v, ideal]) => (
                        <div key={k} className="flex justify-between gap-2">
                          <dt className="text-ink-dim">{k}</dt>
                          <dd className="tabular-nums">
                            {v} <span className="text-ink-dim/60">({ideal})</span>
                          </dd>
                        </div>
                      ))}
                    </dl>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
