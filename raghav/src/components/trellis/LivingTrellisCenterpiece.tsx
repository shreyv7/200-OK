import React, { useState } from "react";
import { motion } from "motion/react";

interface NodePoint {
  id: string;
  label: string;
  sub: string;
  x: number;
  y: number;
  status?: string;
  highlight?: boolean;
}

const NODES: NodePoint[] = [
  { id: "n1", label: "DECLARED SELF", sub: "Goal trajectory", x: 180, y: 50, status: "Active" },
  { id: "n2", label: "REVEALED SIGNAL", sub: "7-day decay score", x: 60, y: 160, status: "0.84" },
  { id: "n3", label: "CAPACITY STACK", sub: "Sized micro-actions", x: 300, y: 160, status: "3 missions/d" },
  { id: "n4", label: "DRIFT GUARDIAN", sub: "Pattern detection", x: 120, y: 280, status: "Monitoring" },
  { id: "n5", label: "IDENTITY TAPESTRY", sub: "Alignment outcome", x: 240, y: 280, status: "Converging" },
];

const EDGES = [
  { from: "n1", to: "n2", d: "M180,50 L60,160", label: "Marker evaluation" },
  { from: "n1", to: "n3", d: "M180,50 L300,160", label: "Capacity budget" },
  { from: "n2", to: "n4", d: "M60,160 L120,280", label: "Drift scoring" },
  { from: "n3", to: "n5", d: "M300,160 L240,280", label: "Stack execution" },
  { from: "n2", to: "n5", d: "M60,160 L240,280", label: "Behavioural delta" },
  { from: "n4", to: "n5", d: "M120,280 L240,280", label: "Intervention feedback" },
  { from: "n1", to: "n5", d: "M180,50 L240,280", label: "Core axis" },
];

export function LivingTrellisCenterpiece() {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  return (
    <div className="relative mx-auto flex w-full max-w-lg flex-col items-center rounded-2xl border border-border/50 bg-background/60 p-6 backdrop-blur-xl shadow-2xl shadow-black/[0.03] transition-all duration-500 hover:border-foreground/20">
      {/* Top Bar Header Badge */}
      <div className="mb-4 flex w-full items-center justify-between border-b border-border/40 pb-3 text-xs font-medium text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </span>
          <span className="font-mono text-[10px] tracking-wider uppercase text-foreground/80">
            LIVING IDENTITY TRELLIS
          </span>
        </div>
        <span className="font-mono text-[10px] opacity-60">SYNC: 100%</span>
      </div>

      {/* SVG Canvas */}
      <div className="relative h-[330px] w-full overflow-hidden">
        <svg viewBox="0 0 360 330" className="h-full w-full select-none" aria-hidden>
          <defs>
            {/* Ambient Line Gradient */}
            <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.08" />
              <stop offset="50%" stopColor="currentColor" stopOpacity="0.25" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0.08" />
            </linearGradient>

            {/* Glowing Pulse Filter */}
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Grid Pattern */}
          <pattern id="centerpieceGrid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path
              d="M 30 0 L 0 0 0 30"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
              strokeOpacity="0.04"
            />
          </pattern>
          <rect width="100%" height="100%" fill="url(#centerpieceGrid)" />

          {/* Edges */}
          {EDGES.map((edge, idx) => {
            const isHovered = activeNode === edge.from || activeNode === edge.to;
            return (
              <g key={idx}>
                {/* Base Edge */}
                <motion.path
                  d={edge.d}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={isHovered ? 1.5 : 1}
                  strokeOpacity={isHovered ? 0.45 : 0.12}
                  strokeDasharray="4 4"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ duration: 1.5, delay: idx * 0.15, ease: "easeOut" }}
                />

                {/* Traveling Energy Pulse Packet */}
                <motion.circle
                  r={isHovered ? 2.5 : 1.8}
                  fill="currentColor"
                  filter="url(#glow)"
                  initial={{ offsetDistance: "0%" }}
                  animate={{
                    offsetDistance: ["0%", "100%"],
                    opacity: [0, 0.9, 0],
                  }}
                  transition={{
                    duration: 8 + idx * 1.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: idx * 1.2,
                  }}
                  style={{
                    offsetPath: `path("${edge.d}")`,
                  }}
                />
              </g>
            );
          })}

          {/* Nodes */}
          {NODES.map((node) => {
            const isSelected = activeNode === node.id;
            return (
              <g
                key={node.id}
                className="cursor-pointer transition-all duration-300"
                onMouseEnter={() => setActiveNode(node.id)}
                onMouseLeave={() => setActiveNode(null)}
              >
                {/* Node Outer Ripple Ring */}
                <motion.circle
                  cx={node.x}
                  cy={node.y}
                  r={18}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="0.75"
                  strokeOpacity={isSelected ? 0.35 : 0.06}
                  animate={{
                    scale: [1, 1.15, 1],
                    strokeOpacity: isSelected ? [0.35, 0.6, 0.35] : [0.06, 0.14, 0.06],
                  }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                />

                {/* Node Core */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isSelected ? 6 : 4}
                  className="fill-background stroke-foreground/70 transition-all duration-300"
                  strokeWidth={1.5}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isSelected ? 2.5 : 1.5}
                  className="fill-foreground transition-all duration-300"
                />

                {/* Label Box */}
                <text
                  x={node.x}
                  y={node.y + 24}
                  textAnchor="middle"
                  className="fill-foreground font-mono text-[9px] font-medium tracking-wider uppercase"
                >
                  {node.label}
                </text>

                {/* Status Subtitle Badge */}
                <text
                  x={node.x}
                  y={node.y + 36}
                  textAnchor="middle"
                  className="fill-muted-foreground font-sans text-[8.5px] opacity-75"
                >
                  {node.status}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Footer Metrics Indicator */}
      <div className="mt-2 flex w-full items-center justify-between border-t border-border/40 pt-3 text-[11px] text-muted-foreground font-mono">
        <span>DECAY WINDOW: 7D</span>
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-foreground/60"></span>
          REAL-TIME GRAPH
        </span>
      </div>
    </div>
  );
}
