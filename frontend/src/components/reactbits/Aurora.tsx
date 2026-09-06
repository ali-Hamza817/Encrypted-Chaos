/**
 * Aurora - soft drifting gradient blobs.
 * Adapted from React Bits (https://reactbits.dev, MIT) as a light-theme,
 * CSS-only variant so it stays gentle on a white background.
 */
import { CSSProperties } from "react";

type Props = {
  colors?: [string, string, string];
  className?: string;
  intensity?: number; // 0..1 opacity multiplier
};

export default function Aurora({
  colors = ["#5eead4", "#99f6e4", "#a7f3d0"],
  className = "",
  intensity = 0.5,
}: Props) {
  const blob = (c: string, extra: CSSProperties): CSSProperties => ({
    position: "absolute",
    borderRadius: "9999px",
    filter: "blur(64px)",
    opacity: intensity,
    background: `radial-gradient(circle at center, ${c} 0%, transparent 70%)`,
    ...extra,
  });
  return (
    <div
      aria-hidden
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
    >
      <div
        className="animate-drift-slow"
        style={blob(colors[0], { width: 520, height: 520, top: "-14%", left: "-8%" })}
      />
      <div
        className="animate-drift-slow"
        style={blob(colors[1], {
          width: 460,
          height: 460,
          top: "-6%",
          right: "-6%",
          animationDelay: "-7s",
        })}
      />
      <div
        className="animate-drift-slow"
        style={blob(colors[2], {
          width: 380,
          height: 380,
          bottom: "-24%",
          left: "38%",
          animationDelay: "-14s",
        })}
      />
    </div>
  );
}
