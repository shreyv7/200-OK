/**
 * AIThinkingOverlay — Brief AI reasoning moments that surface naturally.
 *
 * Refined IABTM theme:
 * - Burnt amber #C8892B icon
 * - Neutral typography (#707070 / #3B3B3B)
 */
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Cpu } from "lucide-react";

const ease = [0.16, 1, 0.3, 1] as const;

const THINKING_SEQUENCES: string[][] = [
  ["Re-evaluating behaviour...", "Comparing last 7 days...", "Confidence updated."],
  ["Scanning behaviour stream...", "Drift pattern detected.", "Gap model adjusted."],
  ["Processing new observation...", "Updating identity weights...", "Score recalculated."],
  ["Analysing trajectory delta...", "Cross-referencing declared self...", "Model stable."],
  ["Reviewing evidence quality...", "Applying decay function...", "Trust layer updated."],
  ["Checking intervention effectiveness...", "Correlating with history...", "Recommendation refreshed."],
  ["Sampling behaviour frequency...", "Recalculating decay...", "Alignment recalculated."],
];

// Status lines that cycle independently in section footers
export const SECTION_STATUS_LINES = [
  "Monitoring behaviour stream...",
  "Updating identity weights...",
  "Confidence recalculated.",
  "Evidence decay applied.",
  "Gap model refreshed.",
  "Checking intervention effectiveness...",
  "Behaviour pattern recorded.",
];

interface Props {
  isActive: boolean;
  sequenceIndex?: number;
  onComplete?: () => void;
}

export function AIThinkingOverlay({ isActive, sequenceIndex = 0, onComplete }: Props) {
  const [visibleLine, setVisibleLine] = useState(0);
  const sequence = THINKING_SEQUENCES[sequenceIndex % THINKING_SEQUENCES.length]!;

  useEffect(() => {
    if (!isActive) {
      setVisibleLine(0);
      return;
    }

    setVisibleLine(0);
    let line = 0;

    const advance = () => {
      line += 1;
      if (line < sequence.length) {
        setVisibleLine(line);
        setTimeout(advance, 400);
      } else {
        setTimeout(() => onComplete?.(), 500);
      }
    };

    const t = setTimeout(advance, 280);
    return () => clearTimeout(t);
  }, [isActive, sequenceIndex, onComplete, sequence.length]);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          initial={{ opacity: 0, y: 6, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -6, scale: 0.98 }}
          transition={{ duration: 0.3, ease }}
          className="inline-flex items-center gap-2.5 rounded-xl border border-black/[0.06] bg-white/95 px-4 py-2.5 shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-xl font-mono text-[10.5px] text-[#111111]"
        >
          <Cpu className="h-3 w-3 text-[#C8892B] animate-pulse shrink-0" strokeWidth={1.5} />
          <AnimatePresence mode="wait">
            <motion.span
              key={visibleLine}
              initial={{ opacity: 0, x: 4 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="text-[#3B3B3B]"
            >
              {sequence[visibleLine]}
            </motion.span>
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * AIStatusLine — Persistent inline status that cycles slowly.
 * Use in section footers to keep things feeling alive at all times.
 */
export function AIStatusLine({ className = "" }: { className?: string }) {
  const [statusIdx, setStatusIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setStatusIdx((i) => (i + 1) % SECTION_STATUS_LINES.length);
        setVisible(true);
      }, 400);
    }, 8_000 + Math.random() * 4_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={`flex items-center gap-1.5 font-mono text-[9.5px] text-[#707070] ${className}`}>
      <Cpu className="h-2.5 w-2.5 text-[#C8892B]" strokeWidth={1.5} />
      <AnimatePresence mode="wait">
        <motion.span
          key={statusIdx}
          initial={{ opacity: 0 }}
          animate={{ opacity: visible ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        >
          {SECTION_STATUS_LINES[statusIdx]}
        </motion.span>
      </AnimatePresence>
    </div>
  );
}

/**
 * Hook to trigger thinking moments on a slow, irregular interval.
 */
export function useAIThinking(
  intervalMs = 28_000,
  jitter = 14_000
): { isThinking: boolean; sequenceIdx: number; observationCount: number; onComplete: () => void } {
  const [isThinking, setIsThinking] = useState(false);
  const [seqIdx, setSeqIdx] = useState(0);
  const [count, setCount] = useState(0);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    const trigger = () => {
      setIsThinking(true);
      setCount((c) => c + 1);
      const next = intervalMs + Math.random() * jitter;
      timeoutId = setTimeout(trigger, next + 2_200);
    };

    timeoutId = setTimeout(trigger, 8_000);
    return () => clearTimeout(timeoutId);
  }, [intervalMs, jitter]);

  const onComplete = () => {
    setIsThinking(false);
    setSeqIdx((i) => (i + 1) % THINKING_SEQUENCES.length);
  };

  return { isThinking, sequenceIdx: seqIdx, observationCount: count, onComplete };
}
