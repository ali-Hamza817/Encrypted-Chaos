/**
 * GradientText - animated gradient fill on text.
 * Adapted from React Bits (https://reactbits.dev, MIT).
 */
import { CSSProperties, ReactNode } from "react";

type Props = {
  children: ReactNode;
  colors?: string[];
  className?: string;
  animationSpeed?: number; // seconds per cycle
};

export default function GradientText({
  children,
  colors = ["#0d9488", "#0891b2", "#059669", "#0d9488"],
  className = "",
  animationSpeed = 8,
}: Props) {
  const style: CSSProperties = {
    backgroundImage: `linear-gradient(90deg, ${colors.join(", ")})`,
    backgroundSize: "300% 100%",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    animation: `gt-move ${animationSpeed}s linear infinite`,
  };
  return (
    <span className={className} style={style}>
      <style>{`@keyframes gt-move{0%{background-position:0% 50%}100%{background-position:300% 50%}}`}</style>
      {children}
    </span>
  );
}
