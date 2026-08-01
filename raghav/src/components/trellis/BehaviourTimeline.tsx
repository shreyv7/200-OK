/**
 * BehaviourTimeline — Horizontal visual replay of recent behaviour.
 *
 * Refined IABTM theme:
 * - Text hierarchy (#111111 / #3B3B3B / #707070)
 * - Restrained burnt amber (#C8892B)
 */
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import type { EvidenceEvent } from "@/lib/trellis/types";

const ease = [0.16, 1, 0.3, 1] as const;

// Map event kind to icon character and color
const KIND_ICON: Record<string, { icon: string; color: string; bg: string }> = {
  creation:         { icon: "💻", color: "#16A34A", bg: "#F0FDF4" },
  completion:       { icon: "✓",  color: "#16A34A", bg: "#F0FDF4" },
  real_world:       { icon: "🎤", color: "#C8892B", bg: "#FFFBEB" },
  passive_learning: { icon: "📚", color: "#707070", bg: "#FCFCFB" },
  drift:            { icon: "↘",  color: "#DC2626", bg: "#FEF2F2" },
  dismissal:        { icon: "×",  color: "#DC2626", bg: "#FEF2F2" },
};

const KIND_LABEL: Record<string, string> = {
  creation:         "Published",
  completion:       "Completed",
  real_world:       "Real world",
  passive_learning: "Consumed",
  drift:            "Drifted",
  dismissal:        "Dismissed",
};

function daysAgoLabel(iso: string): string {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (d === 0) return "today";
  if (d === 1) return "yesterday";
  return `${d}d ago`;
}

export function BehaviourTimeline({
  events,
  maxEvents = 12,
}: {
  events: EvidenceEvent[];
  maxEvents?: number;
}) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Take the most recent N events, then reverse to timeline order (oldest left)
  const timeline = [...events]
    .sort((a, b) => new Date(a.occurredAt).getTime() - new Date(b.occurredAt).getTime())
    .slice(-maxEvents);

  return (
    <div>
      <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-hide relative">
        {/* Timeline base line */}
        <div className="absolute left-0 right-0 top-[22px] h-px bg-black/[0.05] pointer-events-none" />

        {/* Past label */}
        <span className="font-mono text-[8.5px] text-[#707070] shrink-0 pr-1 z-10 bg-transparent">OLDEST</span>

        {timeline.map((ev, idx) => {
          const cfg = KIND_ICON[ev.kind] ?? KIND_ICON["passive_learning"]!;
          const label = KIND_LABEL[ev.kind] ?? ev.kind;
          const isHovered = hoveredId === ev.id;

          return (
            <motion.div
              key={ev.id}
              initial={{ opacity: 0, scale: 0.6, y: 4 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.04, ease }}
              className="relative flex flex-col items-center shrink-0 z-10"
              onMouseEnter={() => setHoveredId(ev.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              {/* Event dot/icon */}
              <motion.div
                whileHover={{ scale: 1.2, y: -2 }}
                transition={{ duration: 0.2, ease }}
                className="flex h-[30px] w-[30px] items-center justify-center rounded-full border text-[11px] cursor-default"
                style={{
                  backgroundColor: cfg.bg,
                  borderColor: `${cfg.color}33`,
                  color: cfg.color,
                  fontFamily: "system-ui",
                }}
              >
                {cfg.icon}
              </motion.div>

              {/* Tooltip */}
              <AnimatePresence>
                {isHovered && (
                  <motion.div
                    initial={{ opacity: 0, y: 4, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.96 }}
                    transition={{ duration: 0.15 }}
                    className="absolute top-10 left-1/2 -translate-x-1/2 z-20 w-max max-w-[140px] rounded-lg border border-black/[0.06] bg-white/95 px-2.5 py-2 shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-xl"
                  >
                    <p className="font-mono text-[9.5px] text-[#111111] font-medium leading-snug text-center">
                      {ev.label.length > 32 ? ev.label.slice(0, 30) + "…" : ev.label}
                    </p>
                    <div className="flex items-center justify-center gap-1.5 mt-1">
                      <span className="font-mono text-[8.5px] font-medium" style={{ color: cfg.color }}>
                        {label}
                      </span>
                      <span className="font-mono text-[8.5px] text-[#707070]">·</span>
                      <span className="font-mono text-[8.5px] text-[#707070]">
                        {daysAgoLabel(ev.occurredAt)}
                      </span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}

        {/* NOW indicator */}
        <div className="flex flex-col items-center shrink-0 z-10">
          <div className="flex h-[30px] items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#C8892B] opacity-40" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#C8892B]" />
            </span>
            <span className="font-mono text-[8.5px] font-medium text-[#C8892B] uppercase tracking-[0.1em]">
              NOW
            </span>
          </div>
        </div>
      </div>

      {/* Kind legend */}
      <div className="mt-4 flex flex-wrap gap-3 font-mono text-[9px] text-[#707070]">
        {Object.entries(KIND_LABEL)
          .filter(([k]) => timeline.some((e) => e.kind === k))
          .map(([kind, label]) => {
            const cfg = KIND_ICON[kind]!;
            return (
              <span key={kind} className="flex items-center gap-1.5">
                <span style={{ color: cfg.color }}>{cfg.icon}</span>
                {label}
              </span>
            );
          })}
      </div>
    </div>
  );
}
