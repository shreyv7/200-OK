import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Check, Activity, ShieldAlert, Zap, TrendingUp } from "lucide-react";

interface FlowStep {
  id: string;
  step: string;
  label: string;
  sub: string;
  icon: React.ComponentType<{ className?: string }>;
  tag: string;
}

const STEPS: FlowStep[] = [
  {
    id: "step-1",
    step: "01",
    label: "Scrolling detected",
    sub: "Low-value habit loop",
    icon: Activity,
    tag: "Signal: Drift",
  },
  {
    id: "step-2",
    step: "02",
    label: "Guardian notices drift",
    sub: "Scores vs 7-day decay",
    icon: ShieldAlert,
    tag: "Evaluation",
  },
  {
    id: "step-3",
    step: "03",
    label: "Mission generated",
    sub: "1–3 min intervention",
    icon: Zap,
    tag: "Targeted Stack",
  },
  {
    id: "step-4",
    step: "04",
    label: "User completes",
    sub: "Capacity-sized action",
    icon: Check,
    tag: "Action Claimed",
  },
  {
    id: "step-5",
    step: "05",
    label: "Identity improves",
    sub: "Tapestry delta added",
    icon: TrendingUp,
    tag: "Gap Closed",
  },
];

export function InterventionFlow() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % STEPS.length);
    }, 2800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full rounded-2xl border border-border/50 bg-background/50 p-6 sm:p-10 backdrop-blur-md shadow-lg shadow-black/[0.02]">
      {/* Header Label */}
      <div className="mb-8 flex items-center justify-between border-b border-border/40 pb-4">
        <span className="label-eyebrow font-mono">AUTOMATED DRIFT INTERVENTION CYCLE</span>
        <span className="font-mono text-[11px] text-muted-foreground">STATE MACHINE v1.0</span>
      </div>

      {/* Steps Flow */}
      <div className="relative flex flex-col gap-6 md:flex-row md:items-stretch md:justify-between md:gap-2">
        {STEPS.map((s, index) => {
          const Icon = s.icon;
          const isActive = activeStep === index;
          const isPast = activeStep > index;

          return (
            <div
              key={s.id}
              className="relative flex flex-1 flex-col justify-between rounded-xl border border-border/40 bg-background/70 p-4 transition-all duration-500 hover:border-foreground/30 hover:shadow-md"
              style={{
                borderColor: isActive ? "oklch(var(--foreground) / 0.4)" : undefined,
              }}
              onMouseEnter={() => setActiveStep(index)}
            >
              {/* Top Meta */}
              <div>
                <div className="flex items-center justify-between font-mono text-[10px] text-muted-foreground">
                  <span className="opacity-60">{s.step}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[9px] font-medium transition-colors ${
                      isActive
                        ? "bg-foreground text-background"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {s.tag}
                  </span>
                </div>

                {/* Icon & Label */}
                <div className="mt-4 flex items-center gap-3">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-lg border transition-all duration-300 ${
                      isActive
                        ? "border-foreground bg-foreground text-background"
                        : "border-border bg-muted/30 text-muted-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium leading-tight text-foreground">
                      {s.label}
                    </h4>
                    <p className="mt-0.5 text-xs text-muted-foreground">{s.sub}</p>
                  </div>
                </div>
              </div>

              {/* Step indicator dot */}
              <div className="mt-5 flex items-center gap-1.5 pt-2 border-t border-border/30">
                <motion.div
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    isActive ? "w-6 bg-foreground" : "w-1.5 bg-muted-foreground/30"
                  }`}
                />
                {isActive && (
                  <span className="font-mono text-[9px] text-muted-foreground">ACTIVE</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
