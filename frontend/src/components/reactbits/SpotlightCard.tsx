/**
 * SpotlightCard - a soft radial highlight follows the cursor across the card.
 * Adapted from React Bits (https://reactbits.dev, MIT).
 */
import { ReactNode, useRef, useState } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  spotlightColor?: string;
};

export default function SpotlightCard({
  children,
  className = "",
  spotlightColor = "rgba(13,148,136,0.14)",
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: "50%", y: "-20%" });
  const [on, setOn] = useState(false);

  return (
    <div
      ref={ref}
      onMouseMove={(e) => {
        const r = ref.current!.getBoundingClientRect();
        setPos({ x: `${e.clientX - r.left}px`, y: `${e.clientY - r.top}px` });
      }}
      onMouseEnter={() => setOn(true)}
      onMouseLeave={() => setOn(false)}
      className={`relative overflow-hidden ${className}`}
    >
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-300"
        style={{
          opacity: on ? 1 : 0,
          background: `radial-gradient(340px circle at ${pos.x} ${pos.y}, ${spotlightColor}, transparent 70%)`,
        }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}
