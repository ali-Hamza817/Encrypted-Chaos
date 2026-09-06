import Workbench from "./components/Workbench";
import Aurora from "./components/reactbits/Aurora";
import GradientText from "./components/reactbits/GradientText";
import ShinyText from "./components/reactbits/ShinyText";
import SplitText from "./components/reactbits/SplitText";
import AnimatedContent from "./components/reactbits/AnimatedContent";
import results from "./data/results.json";

const riskText: Record<string, string> = {
  HIGH: "text-risk-high",
  MEDIUM: "text-risk-med",
  LOW: "text-risk-low",
};

function Nav() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper/80 backdrop-blur-md">
      <div className="wrap flex h-14 items-center gap-6">
        <a href="#top" className="flex items-center gap-2 font-semibold tracking-tight">
          <svg viewBox="0 0 32 32" className="h-5 w-5" aria-hidden>
            <path
              d="M5 23c4.5-16 9-16 11 0s6.5 11 11-5"
              stroke="#0d9488"
              strokeWidth="2.6"
              fill="none"
              strokeLinecap="round"
            />
          </svg>
          Encrypted-Chaos
        </a>
        <nav className="ml-auto hidden gap-6 text-sm text-ink-dim sm:flex">
          <a className="hover:text-ink" href="#workbench">
            Workbench
          </a>
          <a className="hover:text-ink" href="#how">
            How it works
          </a>
          <a className="hover:text-ink" href="#results">
            Results
          </a>
          <a className="hover:text-ink" href="#research">
            Research
          </a>
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section id="top" className="relative overflow-hidden border-b border-line">
      <Aurora intensity={0.45} />
      <div className="wrap relative py-20 sm:py-24">
        <span className="eyebrow">
          MS / PhD thesis instrument &nbsp;·&nbsp; Supervisor: Dr. Ayesha Khalid
        </span>
        <h1 className="mt-4 max-w-4xl text-4xl leading-[1.06] sm:text-6xl">
          <SplitText text="Read an encrypted image back —" />{" "}
          <GradientText className="font-display">with no key.</GradientText>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-ink-soft">
          <b className="text-ink">Encrypted-Chaos</b> builds plaintext–ciphertext
          datasets from a chaos-based image cipher, profiles it with the classical
          security metrics, then trains CNN / U-Net models to reconstruct the plaintext
          from ciphertext alone — and reports how far they get.
        </p>
        <div className="mt-8 flex flex-wrap gap-2.5">
          {[
            ["Target", "chaos image encryption"],
            ["Attack", "known-plaintext, key-free"],
            ["Control", "AES-256-CTR"],
            ["Readout", "PSNR · SSIM · Attack Risk"],
          ].map(([k, v]) => (
            <span
              key={k}
              className="rounded-full border border-line bg-paper px-3 py-1.5 font-mono text-xs text-ink-dim"
            >
              <b className="text-ink">{k}</b>&nbsp; {v}
            </span>
          ))}
        </div>
        <div className="mt-8 flex gap-3">
          <a href="#workbench" className="btn-primary">
            Open the workbench
          </a>
          <a href="#how" className="btn-ghost">
            How it works
          </a>
        </div>
      </div>
    </section>
  );
}

function Pipeline() {
  return (
    <section id="how" className="scroll-mt-20 border-b border-line bg-mist py-16">
      <div className="wrap">
        <span className="eyebrow">How it works</span>
        <h2 className="mt-2 text-3xl">One pipeline, two readouts</h2>
        <p className="mt-2 max-w-2xl text-ink-soft">
          The same plaintext–ciphertext pairs feed both the defensive profile and the
          offensive model. Read them together: a scheme can score almost perfectly on the
          classical metrics and still lose ground to the learned attack.
        </p>
        <div className="mt-8 overflow-x-auto">
          <svg
            viewBox="0 0 620 336"
            className="w-full min-w-[560px] max-w-3xl"
            fill="none"
            fontFamily="'JetBrains Mono', monospace"
            fontSize="12"
          >
            <defs>
              <marker
                id="a"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M0 0 L10 5 L0 10 z" fill="#94a3b8" />
              </marker>
            </defs>
            <g stroke="#cbd5e1" strokeWidth="1.5">
              <line x1="310" y1="44" x2="310" y2="62" markerEnd="url(#a)" />
              <line x1="310" y1="110" x2="310" y2="128" markerEnd="url(#a)" />
              <path d="M310 170 L310 186 L150 186 L150 204" markerEnd="url(#a)" />
              <path d="M310 170 L310 186 L470 186 L470 204" markerEnd="url(#a)" />
              <path d="M150 262 L150 288 L310 288 L310 304" markerEnd="url(#a)" />
              <path d="M470 262 L470 288 L310 288" />
            </g>
            <g>
              {[
                [210, 8, 200, 36, "Image dataset", ""],
                [186, 62, 248, 48, "Chaos / AES encryption", "permute · diffuse · rounds · key"],
                [200, 128, 220, 42, "Plaintext–ciphertext pairs", ""],
                [44, 204, 212, 58, "Cryptographic profile", "entropy · NPCR · UACI · corr"],
                [364, 204, 212, 58, "ML attack — CNN / U-Net", "PSNR · SSIM · MSE"],
              ].map(([x, y, w, h, t, s], i) => (
                <g key={i}>
                  <rect
                    x={x as number}
                    y={y as number}
                    width={w as number}
                    height={h as number}
                    rx="8"
                    fill="#fff"
                    stroke="#e2e8f0"
                  />
                  <text
                    x={(x as number) + (w as number) / 2}
                    y={(y as number) + (s ? 22 : 23)}
                    textAnchor="middle"
                    fill="#0f172a"
                  >
                    {t as string}
                  </text>
                  {s ? (
                    <text
                      x={(x as number) + (w as number) / 2}
                      y={(y as number) + 40}
                      textAnchor="middle"
                      fill="#64748b"
                    >
                      {s as string}
                    </text>
                  ) : null}
                </g>
              ))}
              <rect
                x="196"
                y="304"
                width="228"
                height="26"
                rx="8"
                fill="#fff"
                stroke="#0d9488"
                strokeWidth="1.5"
              />
              <text x="310" y="321" textAnchor="middle" fill="#0f172a">
                Attack Risk verdict
              </text>
            </g>
          </svg>
        </div>
      </div>
    </section>
  );
}

function Results() {
  const maxGain = 0.6;
  return (
    <section id="results" className="scroll-mt-20 border-b border-line py-16">
      <div className="wrap">
        <span className="eyebrow">Measured results</span>
        <h2 className="mt-2 text-3xl">One model, one budget, four ciphers</h2>
        <p className="mt-2 max-w-2xl text-ink-soft">
          Success is scored as <b className="text-ink">SSIM gain</b> — how far the
          reconstruction beats the trivial “always predict the average image” floor. Gain
          near zero means the attack learned nothing.
        </p>
        <p className="mt-3 font-mono text-xs text-ink-dim">
          {results.setup.model} · {results.setup.params_m}M params ·{" "}
          {results.setup.n_train} train / {results.setup.n_test} test ·{" "}
          {results.setup.epochs} epochs · {results.setup.image} · {results.setup.device} ·{" "}
          {results.setup.elapsed_sec}s total
        </p>

        <div className="mt-6 space-y-3">
          {results.rows.map((r) => (
            <AnimatedContent key={r.id} className="card p-4">
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                <div className="min-w-[260px] flex-1 text-sm font-medium">{r.label}</div>
                <div className="flex items-center gap-3">
                  <div className="h-2.5 w-40 overflow-hidden rounded-full bg-mist">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.max(0, Math.min(1, r.gain / maxGain)) * 100}%`,
                        background:
                          r.gain >= 0.3
                            ? "#e11d48"
                            : r.gain >= 0.12
                              ? "#d97706"
                              : "#059669",
                      }}
                    />
                  </div>
                  <span className="w-16 text-right font-mono text-sm tabular-nums">
                    {r.gain >= 0 ? "+" : ""}
                    {r.gain.toFixed(3)}
                  </span>
                </div>
                <div className="font-mono text-xs text-ink-dim">
                  SSIM {r.ssim.toFixed(3)} · PSNR {r.psnr} dB
                </div>
                <span
                  className={`rounded-md border px-2 py-0.5 font-mono text-[11px] font-semibold ${riskText[r.risk]} border-current`}
                >
                  {r.risk}
                </span>
              </div>
            </AnimatedContent>
          ))}
        </div>

        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <div className="card p-5">
            <h3 className="text-lg">The cipher passes the classical tests</h3>
            <p className="mt-1 text-sm text-ink-soft">
              Profiled on logistic-map permutation + diffusion (2 rounds, static key) over
              64 images — every conventional metric lands on target, yet the diffusion-only
              variant is still broken.
            </p>
            <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 font-mono text-sm">
              {[
                ["Entropy", `${results.crypto.entropy}`, "≈ 7.99"],
                ["Histogram χ²", `${results.crypto.hist_chi2}`, "≈ 255"],
                ["Key-sens NPCR", `${results.crypto.npcr}%`, "≈ 99.6"],
                ["Key-sens UACI", `${results.crypto.uaci}%`, "≈ 33.5"],
                ["Corr H", `${results.crypto.corr_h}`, "0"],
                ["Corr V / D", `${results.crypto.corr_v} / ${results.crypto.corr_d}`, "0"],
              ].map(([k, v, ideal]) => (
                <div key={k} className="flex items-baseline justify-between gap-2">
                  <dt className="text-ink-dim">{k}</dt>
                  <dd className="tabular-nums">
                    {v} <span className="text-ink-dim">({ideal})</span>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="card border-l-[3px] border-l-risk-med p-5">
            <h3 className="text-lg">Reading the numbers honestly</h3>
            <p className="mt-1 text-sm text-ink-soft">
              A high gain means the model recovered perceptual <i>structure</i> — not that
              the key was extracted. Diffusion-only static-key chaos (gain{" "}
              <b className="text-ink">+0.76</b>) is a fixed position-dependent transform a
              shallow U-Net learns directly. A global pixel permutation defeats <i>this</i>{" "}
              attack at <i>this</i> budget — a component-attribution finding (RQ5), not
              proof of security. Per-image keying and AES show no recovery. Figures are
              from a short CPU budget — directional, not final.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

const RQ = [
  ["Under a fixed key, can a CNN / U-Net reconstruct unseen plaintext images, and at what fidelity?", "same-key known-plaintext attack · baseline"],
  ["Does a model trained on many keys generalize to ciphertext from an unseen key?", "★ primary contribution · cross-key generalization"],
  ["Does a model trained on one chaotic map transfer to a different chaotic construction?", "★ secondary · cross-algorithm transfer"],
  ["Under identical budgets, are chaos schemes more susceptible than AES-CTR on the same images?", "control · fairness bound"],
  ["Which components drive attack success — permutation vs diffusion, rounds, keying mode?", "★ vulnerability attribution · ablations"],
  ["How many known pairs are needed to reach a target reconstruction quality?", "data-efficiency curve"],
];

function Research() {
  return (
    <section id="research" className="scroll-mt-20 border-b border-line bg-mist py-16">
      <div className="wrap">
        <span className="eyebrow">Research questions</span>
        <h2 className="mt-2 text-3xl">What the thesis answers</h2>
        <p className="mt-2 max-w-2xl text-ink-soft">
          Reproducing the 2019 attack is not a contribution in 2026. These move the work
          toward <i>generalization</i> — and toward whether the classical metrics predict
          resistance to data-driven attacks at all.
        </p>
        <ol className="mt-6 divide-y divide-line border-y border-line">
          {RQ.map(([q, tag], i) => (
            <li key={i} className="grid grid-cols-[44px_1fr] gap-4 py-4">
              <span className="font-mono text-sm font-semibold text-brand-ink">
                RQ{i + 1}
              </span>
              <div>
                <p className="text-sm font-medium">{q}</p>
                <p className="mt-1 font-mono text-[11px] text-ink-dim">{tag}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="py-12">
      <div className="wrap text-sm text-ink-dim">
        <p className="max-w-3xl">
          <ShinyText text="Encrypted-Chaos" className="font-semibold" /> — MVP for the
          thesis “Using ML to Attack Chaos-based Image Encryption”, supervised by Dr.
          Ayesha Khalid. Python package + FastAPI backend + this React frontend.
        </p>
        <p className="mt-3 font-mono text-[11px] leading-relaxed">
          [1] He, Ming, Wang &amp; Wang (2019). A deep learning based attack for the
          chaos-based image encryption. arXiv:1907.12245.
          <br />
          [2] Zhang &amp; Liu (2023). Chaos-based image encryption: review, application,
          and challenges. Mathematics 11(11):2585.
        </p>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <Nav />
      <Hero />
      <Workbench />
      <Pipeline />
      <Results />
      <Research />
      <Footer />
    </div>
  );
}
