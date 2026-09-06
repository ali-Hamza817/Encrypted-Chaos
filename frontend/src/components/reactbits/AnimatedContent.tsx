/**
 * AnimatedContent - fades + slides its children in when they enter the viewport.
 * Adapted from React Bits (https://reactbits.dev, MIT).
 */
import { ReactNode } from "react";
import { motion } from "motion/react";

type Props = {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
};

export default function AnimatedContent({
  children,
  className = "",
  delay = 0,
  y = 24,
}: Props) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
