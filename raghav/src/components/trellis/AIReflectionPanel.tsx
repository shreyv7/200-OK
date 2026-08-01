/**
 * AIReflectionPanel — Rotating AI insight panel.
 *
 * Refined IABTM theme:
 * - Text hierarchy (#111111 / #3B3B3B / #707070)
 * - Restrained burnt amber (#C8892B)
 */
import { useState, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Eye } from "lucide-react";

const ease = [0.16, 1, 0.3, 1] as const;

const REFLECTIONS = [
  { category: "Behaviour Pattern",     text: "You consume more than you create on weekdays. Creation events concentrate on Saturday." },
  { category: "Identity Convergence",  text: "Declared and observed identities are narrowing. Gap reduced by 4 points this week." },
  { category: "Confidence Signal",     text: "Speaking confidence has increased across three consecutive sessions." },
  { category: "Cluster Emerging",      text: "Builder and Speaker identities are beginning to overlap in observable behaviour." },
  { category: "Consistency Detected",  text: "Baseline output has been maintained for 5 consecutive days. Streak forming." },
  { category: "Drift Alert",           text: "Short-form consumption peaks on Monday and Friday. Intervention window: Tuesday morning." },
  { category: "Momentum Shift",        text: "Creation-to-drift ratio improved 18% this week. Trajectory is stabilising." },
  { category: "Marker Update",         text: "Public speaking marker has not been updated in 8 days. Evidence is decaying at 7-day half-life." },
];

export function AIReflectionPanel() {
  const [idx, setIdx] = useState(0);
  const [transitioning, setTransitioning] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scheduleNext = () => {
    const delay = 22_000 + Math.random() * 10_000;
    return setTimeout(() => {
      setTransitioning(true);
      setTimeout(() => {
        setIdx((i) => (i + 1) % REFLECTIONS.length);
        setTransitioning(false);
      }, 300);
      timeoutRef.current = scheduleNext();
    }, delay);
  };

  useEffect(() => {
    timeoutRef.current = scheduleNext();
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const current = REFLECTIONS[idx]!;

  return (
    <div className="relative rounded-2xl border border-black/[0.05] bg-[#FCFCFB] p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#707070] font-medium">
          <Eye className="h-3 w-3 text-[#C8892B]" strokeWidth={1.5} />
          AI REFLECTION
        </div>
        {/* Cycle dots */}
        <div className="flex gap-1">
          {REFLECTIONS.map((_, i) => (
            <span
              key={i}
              className={`h-1 w-1 rounded-full transition-colors duration-500 ${
                i === idx ? "bg-[#C8892B]" : "bg-black/10"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.35, ease }}
        >
          <p className="font-mono text-[9.5px] text-[#C8892B] uppercase tracking-[0.14em] font-medium mb-1.5">
            {current.category}
          </p>
          <p className="text-xs text-[#3B3B3B] leading-relaxed">{current.text}</p>
        </motion.div>
      </AnimatePresence>

      {/* Pulse on transition */}
      <AnimatePresence>
        {transitioning && (
          <motion.div
            initial={{ opacity: 0.4 }}
            animate={{ opacity: 0 }}
            exit={{}}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 rounded-2xl bg-[#C8892B]/[0.04] pointer-events-none"
          />
        )}
      </AnimatePresence>
    </div>
  );
}
