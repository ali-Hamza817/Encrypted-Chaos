/**
 * CountUp - animates a number from `from` to `to` when it scrolls into view.
 * Adapted from React Bits (https://reactbits.dev, MIT).
 */
import { useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";

type Props = {
  to: number;
  from?: number;
  duration?: number; // seconds
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
};

export default function CountUp({
  to,
  from = 0,
  duration = 1.1,
  decimals = 0,
  prefix = "",
  suffix = "",
  className = "",
}: Props) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [val, setVal] = useState(from);

  useEffect(() => {
    if (!inView) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / (duration * 1000));
      const eased = 1 - Math.pow(1 - t, 3);
      setVal(from + (to - from) * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, to, from, duration]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      {val.toFixed(decimals)}
      {suffix}
    </span>
  );
}
