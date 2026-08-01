import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { Sparkles, Activity, CheckCircle } from "lucide-react";

interface IdentityNode {
  id: string;
  label: string;
  weight: number;
  unlocked: boolean;
  x: number;
  y: number;
  driftX: number;
  driftY: number;
}

interface OnboardingIdentityGraphProps {
  currentStep: number;
  totalSteps: number;
  selectedAnswers: string[];
  extractedMarkers?: string[];
  isCompleted?: boolean;
}

// Fixed target confidence levels per question step
const CONFIDENCE_STEPS = [18, 37, 56, 79, 100];

export function OnboardingIdentityGraph({
  currentStep,
  totalSteps,
  selectedAnswers,
  extractedMarkers = [],
  isCompleted = false,
}: OnboardingIdentityGraphProps) {
  // Calculating dynamic confidence score based on step & selections
  const confidenceValue = isCompleted
    ? 100
    : CONFIDENCE_STEPS[Math.min(currentStep, CONFIDENCE_STEPS.length - 1)];

  // Dynamic nodes with weight interpolation and labels
  const nodes: IdentityNode[] = [
    {
      id: "n1",
      label: "DECLARED AIM",
      weight: 0.95,
      unlocked: true,
      x: 160,
      y: 45,
      driftX: 2,
      driftY: -2,
    },
    {
      id: "n2",
      label: currentStep >= 1 ? "HORIZON: MOMENTUM" : "FOCUS HORIZON",
      weight: currentStep >= 1 ? 0.88 : 0.2,
      unlocked: currentStep >= 1 || isCompleted,
      x: 65,
      y: 125,
      driftX: -3,
      driftY: 2,
    },
    {
      id: "n3",
      label: currentStep >= 2 ? "RIGOUR: SHIPPING" : "BUILDER RIGOUR",
      weight: currentStep >= 2 ? 0.92 : 0.15,
      unlocked: currentStep >= 2 || isCompleted,
      x: 255,
      y: 125,
      driftX: 3,
      driftY: 1,
    },
    {
      id: "n4",
      label: currentStep >= 3 ? "SIGNAL: FOCUS" : "PRESENCE SIGNAL",
      weight: currentStep >= 3 ? 0.84 : 0.1,
      unlocked: currentStep >= 3 || isCompleted,
      x: 95,
      y: 215,
      driftX: -2,
      driftY: -2,
    },
    {
      id: "n5",
      label: currentStep >= 4 ? "CAPACITY: 60M+" : "CAPACITY BUDGET",
      weight: currentStep >= 4 ? 0.9 : 0.1,
      unlocked: currentStep >= 4 || isCompleted,
      x: 225,
      y: 215,
      driftX: 2,
      driftY: 3,
    },
  ];

  const edges = [
    { from: "n1", to: "n2", unlocked: currentStep >= 1 || isCompleted },
    { from: "n1", to: "n3", unlocked: currentStep >= 2 || isCompleted },
    { from: "n2", to: "n4", unlocked: currentStep >= 3 || isCompleted },
    { from: "n3", to: "n5", unlocked: currentStep >= 4 || isCompleted },
    { from: "n4", to: "n5", unlocked: currentStep >= 4 || isCompleted },
    { from: "n2", to: "n3", unlocked: currentStep >= 2 || isCompleted },
  ];

  return (
    <div className="relative mx-auto flex w-full max-w-sm flex-col gap-4 rounded-3xl border border-border/40 bg-background/60 p-6 backdrop-blur-2xl shadow-2xl shadow-black/10">
      {/* Header with Live Signal indicator */}
      <div className="flex items-center justify-between border-b border-border/30 pb-3.5 font-mono text-[10.5px]">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-sky-500" />
          </span>
          <span className="tracking-wider uppercase font-semibold text-foreground/90">
            LIVING IDENTITY MODEL
          </span>
        </div>
        <span className="text-sky-400 font-mono font-medium tracking-wide">
          {isCompleted ? "CONVERGED" : `STEP ${currentStep + 1}/${totalSteps}`}
        </span>
      </div>

      {/* SVG Topology Canvas */}
      <div className="relative h-[260px] w-full overflow-hidden rounded-2xl border border-border/30 bg-muted/10 p-2 shadow-inner">
        <svg viewBox="0 0 320 250" className="h-full w-full select-none" aria-hidden>
          <defs>
            <filter id="nodeGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Edges with Animated Stroke & Dash Shimmer */}
          {edges.map((e, idx) => {
            const nFrom = nodes.find((n) => n.id === e.from)!;
            const nTo = nodes.find((n) => n.id === e.to)!;
            return (
              <g key={idx}>
                <motion.line
                  x1={nFrom.x}
                  y1={nFrom.y}
                  x2={nTo.x}
                  y2={nTo.y}
                  stroke={e.unlocked ? "url(#edgeGradient)" : "currentColor"}
                  strokeWidth={e.unlocked ? 1.5 : 0.75}
                  strokeOpacity={e.unlocked ? 0.6 : 0.1}
                  strokeDasharray={e.unlocked ? "none" : "3 3"}
                  initial={{ strokeOpacity: 0.1 }}
                  animate={{ strokeOpacity: e.unlocked ? (isCompleted ? 0.85 : 0.6) : 0.1 }}
                  transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                />

                {/* Computational Particle Traveling along Edge */}
                {e.unlocked && (
                  <>
                    <motion.circle
                      r={2.5}
                      fill="#38bdf8"
                      filter="url(#nodeGlow)"
                      animate={{
                        cx: [nFrom.x, nTo.x],
                        cy: [nFrom.y, nTo.y],
                        opacity: [0, 1, 0],
                      }}
                      transition={{
                        duration: 2.4 + idx * 0.4,
                        repeat: Infinity,
                        ease: "easeInOut",
                      }}
                    />
                    {/* Reverse faint echo particle */}
                    <motion.circle
                      r={1.5}
                      fill="#818cf8"
                      animate={{
                        cx: [nTo.x, nFrom.x],
                        cy: [nTo.y, nFrom.y],
                        opacity: [0, 0.6, 0],
                      }}
                      transition={{
                        duration: 3.2 + idx * 0.3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 1.2,
                      }}
                    />
                  </>
                )}
              </g>
            );
          })}

          {/* Breathing & Drifting Nodes */}
          {nodes.map((node) => {
            return (
              <motion.g
                key={node.id}
                animate={{
                  x: node.unlocked ? [0, node.driftX, 0] : 0,
                  y: node.unlocked ? [0, node.driftY, 0] : 0,
                }}
                transition={{
                  duration: 4 + Math.random() * 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                {/* Outer Breathing Glow Ring */}
                <motion.circle
                  cx={node.x}
                  cy={node.y}
                  r={node.unlocked ? 16 : 10}
                  fill="none"
                  stroke={node.unlocked ? "#38bdf8" : "currentColor"}
                  strokeWidth={0.75}
                  strokeOpacity={node.unlocked ? 0.4 : 0.08}
                  animate={
                    node.unlocked
                      ? {
                          scale: [1, 1.25, 1],
                          strokeOpacity: [0.3, 0.7, 0.3],
                        }
                      : {}
                  }
                  transition={{
                    duration: 3.2,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />

                {/* Solid Core Node */}
                <motion.circle
                  cx={node.x}
                  cy={node.y}
                  r={node.unlocked ? 5.5 : 3.5}
                  fill={node.unlocked ? "#38bdf8" : "var(--color-muted-foreground)"}
                  filter={node.unlocked ? "url(#nodeGlow)" : undefined}
                  animate={
                    node.unlocked
                      ? {
                          scale: [1, 1.15, 1],
                        }
                      : {}
                  }
                  transition={{
                    duration: 2.8,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />

                {/* Node Label */}
                <text
                  x={node.x}
                  y={node.y + 24}
                  textAnchor="middle"
                  className={`font-mono text-[8.5px] tracking-wider uppercase transition-all duration-700 ${
                    node.unlocked
                      ? "fill-foreground font-semibold drop-shadow-sm"
                      : "fill-muted-foreground/40"
                  }`}
                >
                  {node.label}
                </text>
              </motion.g>
            );
          })}
        </svg>
      </div>

      {/* Identity Confidence Progression Box */}
      <div className="rounded-2xl border border-sky-400/20 bg-sky-500/5 p-4 backdrop-blur-md">
        <div className="flex items-center justify-between font-mono text-xs">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Activity className="h-3.5 w-3.5 text-sky-400" />
            <span className="tracking-wider uppercase">IDENTITY CONFIDENCE</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-sky-400/80 animate-pulse font-mono">
              {isCompleted ? "STABILIZED" : "INCREASING..."}
            </span>
            <span className="text-base font-bold font-mono text-sky-400">
              {confidenceValue}%
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-muted/40">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-sky-400 to-indigo-400 shadow-sm shadow-sky-400/50"
            initial={{ width: "18%" }}
            animate={{ width: `${confidenceValue}%` }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
      </div>

      {/* Extracted Behaviour Markers Feed */}
      <div className="rounded-2xl border border-border/30 bg-background/40 p-4 font-mono text-xs">
        <div className="mb-2.5 flex items-center justify-between border-b border-border/20 pb-2 text-[10.5px] text-muted-foreground">
          <span className="tracking-wider uppercase font-medium">BEHAVIOUR MARKERS ADDED</span>
          <span className="text-sky-400 font-semibold">{extractedMarkers.length} ACTIVE</span>
        </div>

        {extractedMarkers.length === 0 ? (
          <p className="text-[11px] text-muted-foreground/50 italic py-1">
            Selecting answers extracts observable action markers into your identity stack...
          </p>
        ) : (
          <div className="space-y-1.5">
            <AnimatePresence>
              {extractedMarkers.map((marker, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 6 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-center gap-2 text-[11px] text-foreground/90 font-mono"
                >
                  <CheckCircle className="h-3 w-3 shrink-0 text-sky-400 stroke-[2.5]" />
                  <span className="truncate">{marker}</span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
