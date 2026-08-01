import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils";

const PERSONAS = [
  { src: "/1.png", alt: "A child version of the declared self" },
  { src: "/2.png", alt: "An elder version of the declared self" },
  { src: "/3.png", alt: "A teenage version of the declared self" },
  { src: "/4.png", alt: "A painting version of the declared self" },
  { src: "/5.png", alt: "A toddler version of the declared self" },
] as const;

/** Time a persona is fully settled before the next one takes over. */
const HOLD_MS = 2000;
const MORPH_S = 1.1;
const flagshipEase = [0.16, 1, 0.3, 1] as const;

export function MorphingPersona({ className }: { className?: string }) {
  const [index, setIndex] = useState(0);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    for (const persona of PERSONAS) {
      const img = new window.Image();
      img.src = persona.src;
    }
  }, []);

  useEffect(() => {
    const id = window.setInterval(
      () => setIndex((i) => (i + 1) % PERSONAS.length),
      HOLD_MS,
    );
    return () => window.clearInterval(id);
  }, []);

  const current = PERSONAS[index];

  return (
    <div className={cn("relative w-full", className)}>
      <motion.div
        className="relative aspect-[564/988] w-full overflow-hidden rounded-[2rem] border border-border bg-[#F6F6F6]"
        style={{ boxShadow: "0 24px 80px rgba(17,17,17,0.06)" }}
        animate={reduceMotion ? undefined : { y: [0, -8, 0] }}
        transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
      >
        <AnimatePresence initial={false}>
          <motion.img
            key={current.src}
            src={current.src}
            alt={current.alt}
            draggable={false}
            className="absolute inset-0 h-full w-full object-cover select-none"
            initial={
              reduceMotion
                ? { opacity: 0 }
                : { opacity: 0, scale: 1.06, filter: "blur(18px)" }
            }
            animate={
              reduceMotion
                ? { opacity: 1 }
                : { opacity: 1, scale: 1, filter: "blur(0px)" }
            }
            exit={
              reduceMotion
                ? { opacity: 0 }
                : { opacity: 0, scale: 0.97, filter: "blur(18px)" }
            }
            transition={{
              duration: reduceMotion ? 0.3 : MORPH_S,
              ease: flagshipEase,
              opacity: { duration: reduceMotion ? 0.3 : MORPH_S * 0.8 },
            }}
          />
        </AnimatePresence>

        {/* Light sweep that crosses the frame at the moment of the change */}
        {!reduceMotion && (
          <AnimatePresence initial={false}>
            <motion.div
              key={`sweep-${index}`}
              aria-hidden
              className="pointer-events-none absolute inset-y-0 -left-1/2 w-1/2 skew-x-[-12deg] bg-gradient-to-r from-transparent via-white/70 to-transparent"
              initial={{ x: 0, opacity: 0 }}
              animate={{ x: "300%", opacity: [0, 1, 0] }}
              transition={{ duration: MORPH_S, ease: "easeInOut" }}
            />
          </AnimatePresence>
        )}

        {/* Grounding vignette so the character sits in the frame */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-b from-white/25 via-transparent to-[#F6F6F6]"
        />
      </motion.div>

      <div className="mt-5 flex items-center gap-1.5">
        {PERSONAS.map((persona, i) => (
          <span
            key={persona.src}
            className="relative h-px flex-1 overflow-hidden bg-border"
          >
            <motion.span
              className="absolute inset-y-0 left-0 bg-signal"
              initial={{ width: 0 }}
              animate={{ width: i === index ? "100%" : 0 }}
              transition={{
                duration: i === index ? HOLD_MS / 1000 : 0.35,
                ease: i === index ? "linear" : "easeOut",
              }}
            />
          </span>
        ))}
      </div>
      <p className="mt-3 font-mono text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
        Same person, different weeks
      </p>
    </div>
  );
}
