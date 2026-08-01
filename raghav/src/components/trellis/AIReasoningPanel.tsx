import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Cpu, CheckCircle2 } from "lucide-react";

interface AIReasoningPanelProps {
  isVisible: boolean;
  steps?: string[];
  onComplete?: () => void;
}

const defaultSteps = [
  "Parsing behavioural intent...",
  "✓ Confidence Marker detected",
  "✓ Public Speaking behaviour identified",
  "✓ Observable metric logged",
  "Updating Identity Graph...",
];

export function AIReasoningPanel({
  isVisible,
  steps = defaultSteps,
  onComplete,
}: AIReasoningPanelProps) {
  const [visibleStepCount, setVisibleStepCount] = useState<number>(0);

  useEffect(() => {
    if (!isVisible) {
      setVisibleStepCount(0);
      return;
    }

    setVisibleStepCount(1);

    const interval = setInterval(() => {
      setVisibleStepCount((prev) => {
        if (prev < steps.length) {
          return prev + 1;
        } else {
          clearInterval(interval);
          if (onComplete) {
            setTimeout(onComplete, 400);
          }
          return prev;
        }
      });
    }, 180);

    return () => clearInterval(interval);
  }, [isVisible, steps, onComplete]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.98 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="my-5 rounded-2xl border border-sky-400/30 bg-sky-950/20 p-4.5 backdrop-blur-xl shadow-lg shadow-sky-500/5 font-mono text-xs text-foreground/90"
        >
          {/* Header */}
          <div className="mb-3 flex items-center justify-between border-b border-sky-500/20 pb-2.5">
            <div className="flex items-center gap-2 text-sky-400 font-semibold tracking-wider uppercase text-[10.5px]">
              <Cpu className="h-3.5 w-3.5 animate-pulse text-sky-400" />
              <span>IDENTITY ENGINE · INFERENCE ACTIVE</span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-sky-300/70">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-sky-400" />
              </span>
              <span>SYNTHESIZING</span>
            </div>
          </div>

          {/* Line by line thinking logs */}
          <div className="space-y-1.5 text-[11px] font-mono leading-relaxed">
            {steps.slice(0, visibleStepCount).map((stepText, idx) => {
              const isChecked = stepText.startsWith("✓");
              const isLast = idx === visibleStepCount - 1 && visibleStepCount < steps.length;

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`flex items-center gap-2 ${
                    isChecked
                      ? "text-sky-300 font-medium"
                      : isLast
                      ? "text-foreground font-semibold"
                      : "text-muted-foreground"
                  }`}
                >
                  {isChecked ? (
                    <CheckCircle2 className="h-3 w-3 shrink-0 text-sky-400 stroke-[2.5]" />
                  ) : (
                    <span className="text-sky-400/60 font-bold">›</span>
                  )}
                  <span>{stepText.replace(/^✓\s*/, "")}</span>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
