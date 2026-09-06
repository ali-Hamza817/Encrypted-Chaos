/**
 * SplitText - words/chars animate in with a staggered spring.
 * Adapted from React Bits (https://reactbits.dev, MIT); framer-motion instead of GSAP.
 */
import { useMemo } from "react";
import { motion } from "motion/react";

type Props = {
  text: string;
  className?: string;
  delay?: number; // seconds before start
  stagger?: number; // seconds between words
  by?: "word" | "char";
};

export default function SplitText({
  text,
  className = "",
  delay = 0,
  stagger = 0.045,
  by = "word",
}: Props) {
  const parts = useMemo(
    () => (by === "word" ? text.split(/(\s+)/) : Array.from(text)),
    [text, by],
  );
  return (
    <span className={className} aria-label={text}>
      {parts.map((p, i) =>
        /^\s+$/.test(p) ? (
          <span key={i}> </span>
        ) : (
          <motion.span
            key={i}
            className="inline-block will-change-transform"
            initial={{ y: "0.5em", opacity: 0, filter: "blur(6px)" }}
            animate={{ y: 0, opacity: 1, filter: "blur(0px)" }}
            transition={{
              delay: delay + i * stagger,
              duration: 0.5,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            {p}
          </motion.span>
        ),
      )}
    </span>
  );
}
