import React, { useState, useEffect } from "react";
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
    <div className="relative mx-auto flex w-full max-w-md flex-col rounded-2xl border border-border/40 bg-background/40 p-6 backdrop-blur-xl shadow-2xl shadow-black/[0.02] transition-all duration-500 hover:border-foreground/20">
      {/* Top Engine Header */}
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

      {/* Real-time Computational Graphic Engine Canvas */}
      <div className="relative h-[290px] w-full overflow-hidden rounded-xl border border-border/20 bg-muted/10 p-4">
        <svg viewBox="0 0 320 250" className="h-full w-full select-none" aria-hidden>
          <defs>
            {/* Subtle Electric Blue Pulse Gradient */}
            <linearGradient id="bluePulseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.1" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.1" />
            </linearGradient>

            {/* Glowing filter */}
            <filter id="softBlueGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Grid Intersections */}
          {[60, 120, 180, 240].map((x) => (
            <line
              key={`x-${x}`}
              x1={x}
              y1={10}
              x2={x}
              y2={240}
              stroke="currentColor"
              strokeWidth="0.5"
              strokeOpacity="0.04"
              strokeDasharray="2 4"
            />
          ))}
          {[50, 100, 150, 200].map((y) => (
            <line
              key={`y-${y}`}
              x1={10}
              y1={y}
              x2={310}
              y2={y}
              stroke="currentColor"
              strokeWidth="0.5"
              strokeOpacity="0.04"
              strokeDasharray="2 4"
            />
          ))}

          {/* Confidence Heat Envelope */}
          <motion.ellipse
            cx={160}
            cy={125}
            rx={95}
            ry={65}
            fill="none"
            stroke="#38bdf8"
            strokeWidth="0.75"
            strokeOpacity="0.25"
            strokeDasharray="4 6"
            animate={{
              rx: [90, 105, 90],
              ry: [60, 72, 60],
              strokeOpacity: [0.15, 0.35, 0.15],
            }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          />

          {/* Dynamic Connected Node Topology */}
          {[
            { x1: 160, y1: 45, x2: 70, y2: 125, key: "l1" },
            { x1: 160, y1: 45, x2: 250, y2: 125, key: "l2" },
            { x1: 70, y1: 125, x2: 120, y2: 205, key: "l3" },
            { x1: 250, y1: 125, x2: 200, y2: 205, key: "l4" },
            { x1: 120, y1: 205, x2: 200, y2: 205, key: "l5" },
            { x1: 70, y1: 125, x2: 250, y2: 125, key: "l6" },
          ].map((edge, i) => (
            <g key={edge.key}>
              <line
                x1={edge.x1}
                y1={edge.y1}
                x2={edge.x2}
                y2={edge.y2}
                stroke="currentColor"
                strokeWidth="1"
                strokeOpacity="0.12"
              />

              {/* Electric Blue Signal Pulse */}
              <motion.circle
                r={2}
                fill="#38bdf8"
                filter="url(#softBlueGlow)"
                animate={{
                  cx: [edge.x1, edge.x2],
                  cy: [edge.y1, edge.y2],
                  opacity: [0, 0.9, 0],
                }}
                transition={{
                  duration: 4 + i * 0.8,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: i * 0.6,
                }}
              />
            </g>
          ))}

          {/* Computed Identity Node Hubs */}
          {[
            { x: 160, y: 45, label: "DECLARED", sub: "1.00" },
            { x: 70, y: 125, label: "SIGNAL", sub: "0.88" },
            { x: 250, y: 125, label: "CAPACITY", sub: "3/d" },
            { x: 120, y: 205, label: "DRIFT", sub: "-0.14" },
            { x: 200, y: 205, label: "TAPESTRY", sub: "CONVERGING" },
          ].map((node, i) => {
            const isHighlight = i === logIndex;
            return (
              <g key={node.label}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isHighlight ? 6 : 4}
                  fill="var(--color-background)"
                  stroke={isHighlight ? "#38bdf8" : "currentColor"}
                  strokeWidth={isHighlight ? 2 : 1}
                  strokeOpacity={isHighlight ? 0.9 : 0.4}
                />
                {isHighlight && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={2}
                    fill="#38bdf8"
                  />
                )}
                <text
                  x={node.x}
                  y={node.y + 18}
                  textAnchor="middle"
                  className="fill-foreground font-mono text-[8.5px] font-medium tracking-wider uppercase"
                >
                  {node.label}
                </text>
                <text
                  x={node.x}
                  y={node.y + 28}
                  textAnchor="middle"
                  className="fill-muted-foreground font-mono text-[7.5px] opacity-70"
                >
                  {node.sub}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Real-time Stream Terminal Overlay */}
        {activeLog && (
          <div className="absolute bottom-3 left-3 right-3 rounded-lg border border-border/30 bg-background/80 p-2.5 backdrop-blur-md font-mono text-[10.5px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeLog.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.25 }}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="text-signal">[{activeLog.timestamp}]</span>
                  <span className="text-foreground/90 font-medium">{activeLog.metric}:</span>
                  <span className="text-muted-foreground">{activeLog.value}</span>
                </div>
                <span className="text-[9.5px] text-signal/80">
                  P({(activeConfidence * 100).toFixed(0)}%)
                </span>
              </motion.div>
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Engine Metrics Footer */}
      <div className="mt-4 flex items-center justify-between border-t border-border/30 pt-3 font-mono text-[10.5px] text-muted-foreground">
        <span>CONFIDENCE: {(activeConfidence * 100).toFixed(1)}%</span>
        <span>MODEL: CONTINUOUS</span>
      </div>
    </div>
  );
}
