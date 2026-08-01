import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";

interface ComputationLog {
  id: string;
  timestamp: string;
  metric: string;
  value: string;
  confidence: number;
  type: "signal" | "eval" | "cluster";
}

const COMPUTATION_LOGS: ComputationLog[] = [
  { id: "c1", timestamp: "0.04s", metric: "DECLARED AXIS", value: "Rigour & Craft", confidence: 0.94, type: "cluster" },
  { id: "c2", timestamp: "0.12s", metric: "BEHAVIOURAL SIGNAL", value: "7-day decay active", confidence: 0.88, type: "signal" },
  { id: "c3", timestamp: "0.28s", metric: "IDENTITY DELTA", value: "Δ -0.14 gap detected", confidence: 0.82, type: "eval" },
  { id: "c4", timestamp: "0.45s", metric: "CAPACITY SIZING", value: "3 missions / day", confidence: 0.96, type: "cluster" },
  { id: "c5", timestamp: "0.62s", metric: "DRIFT GUARDIAN", value: "Scroll pattern match", confidence: 0.91, type: "eval" },
];

export function LivingIdentityEngine() {
  const [logIndex, setLogIndex] = useState(0);
  const [activeConfidence, setActiveConfidence] = useState(0.88);

  useEffect(() => {
    const interval = setInterval(() => {
      setLogIndex((prev) => (prev + 1) % COMPUTATION_LOGS.length);
      setActiveConfidence(0.84 + Math.random() * 0.14);
    }, 3200);
    return () => clearInterval(interval);
  }, []);

  const activeLog = COMPUTATION_LOGS[logIndex];

  return (
    <div className="relative mx-auto flex w-full max-w-md flex-col rounded-2xl border border-border/40 bg-background p-6 shadow-2xl shadow-black/[0.02] transition-all duration-500 hover:border-foreground/20">
      <div className="mb-5 flex items-center justify-between border-b border-border/30 pb-3.5 font-mono text-[11px]">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-signal" />
          </span>
          <span className="tracking-wider uppercase text-foreground/80">
            LIVING IDENTITY ENGINE
          </span>
        </div>
        <span className="text-muted-foreground/70">STATE: SYNTHESIZING</span>
      </div>

      <div className="rounded-xl border border-border/20 bg-muted/10 p-4 font-mono text-[10.5px]">
        {activeLog && (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeLog.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.25 }}
              className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-signal">[{activeLog.timestamp}]</span>
                <span className="text-foreground/90 font-medium">{activeLog.metric}:</span>
                <span className="text-muted-foreground">{activeLog.value}</span>
              </div>
              <span className="text-[9.5px] text-signal/80">
                P({(activeConfidence * 100).toFixed(0)}%)
              </span>
            </motion.div>
          </AnimatePresence>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-border/30 pt-3 font-mono text-[10.5px] text-muted-foreground">
        <span>CONFIDENCE: {(activeConfidence * 100).toFixed(1)}%</span>
        <span>MODEL: CONTINUOUS</span>
      </div>
    </div>
  );
}
