/**
 * ShinyText - a light sweep travels across the text.
 * Adapted from React Bits (https://reactbits.dev, MIT).
 */
type Props = {
  text: string;
  speed?: number; // seconds
  className?: string;
};

export default function ShinyText({ text, speed = 4, className = "" }: Props) {
  return (
    <span
      className={`bg-clip-text text-transparent ${className}`}
      style={{
        backgroundImage:
          "linear-gradient(110deg, #94a3b8 35%, #0f172a 50%, #94a3b8 65%)",
        backgroundSize: "200% 100%",
        animation: `shiny ${speed}s linear infinite`,
      }}
    >
      <style>{`@keyframes shiny{0%{background-position:200% 0}100%{background-position:-200% 0}}`}</style>
      {text}
    </span>
  );
}
