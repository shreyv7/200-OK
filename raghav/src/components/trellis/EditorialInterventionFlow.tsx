import React, { useState, useEffect } from "react";
import { motion } from "motion/react";

interface Step {
  num: string;
  title: string;
  desc: string;
  metric: string;
}

const STEPS: Step[] = [
  {
    num: "01",
    title: "Scrolling detected",
    desc: "Habitual low-value drift detected during active focus window.",
    metric: "Drift signal: +0.18",
  },
  {
    num: "02",
    title: "Guardian notices drift",
    desc: "Evaluates behaviour score against your declared 7-day decay horizon.",
    metric: "Decay window: 7d",
  },
  {
    num: "03",
    title: "Mission generated",
    desc: "Replaces next low-value card with a 1-to-3 minute targeted action.",
    metric: "Duration: 180s",
  },
  {
    num: "04",
    title: "User completes",
    desc: "Capacity-sized micro-action claimed and logged.",
    metric: "Verdict: Worked",
  },
  {
    num: "05",
    title: "Identity improves",
    desc: "Revealed behaviour converges back toward declared trajectory.",
    metric: "Gap closed: 14%",
  },
];

export function EditorialInterventionFlow() {
  const [activeIdx, setActiveIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIdx((prev) => (prev + 1) % STEPS.length);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="w-full py-8">
      {/* Editorial Step Grid */}
      <div className="grid gap-8 md:grid-cols-5">
        {STEPS.map((s, idx) => {
          const isActive = activeIdx === idx;
          return (
            <div
              key={s.num}
              className="group cursor-pointer transition-all duration-300"
              onClick={() => setActiveIdx(idx)}
            >
              {/* Line Node */}
              <div className="mb-4 flex items-center gap-3">
                <div
                  className={`h-2.5 w-2.5 rounded-full transition-all duration-300 ${
                    isActive
                      ? "bg-signal ring-4 ring-signal/20"
                      : "bg-foreground/20 group-hover:bg-foreground/40"
                  }`}
                />
                <div
                  className={`h-[1px] flex-1 transition-colors duration-300 ${
                    isActive ? "bg-signal/60" : "bg-border/60"
                  }`}
                />
              </div>

              {/* Step Meta */}
              <span className="font-mono text-[10px] tracking-wider text-muted-foreground uppercase">
                STEP {s.num}
              </span>

              {/* Title & Sub */}
              <h4 className={`mt-2 text-base font-medium leading-snug transition-colors duration-200 ${
                isActive ? "text-foreground" : "text-foreground/80 group-hover:text-foreground"
              }`}>
                {s.title}
              </h4>

              <p className="mt-2 text-xs leading-relaxed text-muted-foreground/80">
                {s.desc}
              </p>

              <div className="mt-4 font-mono text-[10px] text-muted-foreground/60">
                {s.metric}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
