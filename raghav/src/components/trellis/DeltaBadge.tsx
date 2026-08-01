/**
 * DeltaBadge — Animated score/alignment delta indicator.
 *
 * Appears beside a score when it changes.
 * Shows "+2 Alignment" or "−1 Drift" in green/red.
 * Fades upward and disappears after ~2.5 seconds.
 * Used everywhere scores update to communicate the AI is actively computing.
 */
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

interface Delta {
  id: string;       // unique per trigger — use Date.now().toString()
  value: number;    // positive = gain, negative = loss
  label: string;    // e.g. "Alignment", "Drift", "Confidence"
}

interface DeltaBadgeProps {
  delta: Delta | null;
}

export function DeltaBadge({ delta }: DeltaBadgeProps) {
  const [visible, setVisible] = useState(false);
  const [current, setCurrent] = useState<Delta | null>(null);

  useEffect(() => {
    if (!delta) return;
    setCurrent(delta);
    setVisible(true);
    const t = setTimeout(() => setVisible(false), 2_200);
    return () => clearTimeout(t);
  }, [delta?.id]);

  if (!current) return null;

  const positive = current.value > 0;
  const color    = positive ? "#16A34A" : "#DC2626";
  const sign     = positive ? "+" : "";

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key={current.id}
          initial={{ opacity: 0, y: 4, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.9 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[9.5px] font-semibold"
          style={{
            color,
            borderColor: `${color}33`,
            backgroundColor: `${color}0D`,
          }}
        >
          {sign}{current.value} {current.label}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Hook — returns { triggerDelta, delta }.
 * Call triggerDelta(value, label) to fire a badge.
 */
export function useDeltaBadge() {
  const [delta, setDelta] = useState<Delta | null>(null);

  const triggerDelta = (value: number, label: string) => {
    setDelta({ id: Date.now().toString(), value, label });
  };

  return { delta, triggerDelta };
}

/**
 * InlineStatus — Small inline "Identity updated." confirmation text.
 * Fades in and out after an action.
 */
interface InlineStatusProps {
  message: string;
  visible: boolean;
}

export function InlineStatus({ message, visible }: InlineStatusProps) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.span
          initial={{ opacity: 0, x: 4 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="font-mono text-[10px] text-[#16A34A]"
        >
          {message}
        </motion.span>
      )}
    </AnimatePresence>
  );
}
