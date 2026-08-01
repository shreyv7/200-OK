/**
 * LiveObservationStream — A continuously-updating behaviour observation feed.
 *
 * Refined IABTM theme:
 * - Text hierarchy (#111111 / #3B3B3B / #707070)
 * - Restrained burnt amber (#C8892B)
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Hammer, BookOpen, TrendingDown, Star } from "lucide-react";
import type { EvidenceEvent } from "@/lib/trellis/types";

const ease = [0.16, 1, 0.3, 1] as const;

// Pool of simulated live observations that occasionally surface
const LIVE_POOL: Array<{
  kind: EvidenceEvent["kind"];
  label: string;
  strength: number;
  attributeId: string | null;
  identityLink: string;
}> = [
  { kind: "completion",       label: "Deep focus session completed — 52 minutes uninterrupted", strength: 0.92, attributeId: "builder",  identityLink: "Builder Identity" },
  { kind: "creation",         label: "Public commit pushed — side project update",               strength: 0.88, attributeId: "builder",  identityLink: "Builder Identity" },
  { kind: "real_world",       label: "Presentation practice detected — 10 minute run-through",  strength: 0.84, attributeId: "speaker",  identityLink: "Speaker Score" },
  { kind: "passive_learning", label: "Video consumed — speaking under pressure breakdown",       strength: 0.40, attributeId: "speaker",  identityLink: "Speaker Identity" },
  { kind: "creation",         label: "Written output published — project log entry",             strength: 0.78, attributeId: "builder",  identityLink: "Builder Identity" },
  { kind: "drift",            label: "Passive scroll detected — 18 minute session",              strength: 0.55, attributeId: null,       identityLink: "Drift Guardian" },
  { kind: "completion",       label: "Reading session finished — identity design framework",     strength: 0.60, attributeId: "builder",  identityLink: "Builder Identity" },
  { kind: "real_world",       label: "Conversation initiated — asked question in group context", strength: 0.72, attributeId: "speaker",  identityLink: "Speaker Score" },
];

interface StreamEntry {
  id: string;
  kind: EvidenceEvent["kind"];
  label: string;
  strength: number;
  identityLink: string;
  occurredAt: string;
  isNew: boolean;
}

const KIND_CONFIG: Record<string, { Icon: typeof Hammer; color: string; bgColor: string; label: string }> = {
  creation:         { Icon: Hammer,      color: "#16A34A", bgColor: "#F0FDF4", label: "Created"    },
  completion:       { Icon: Hammer,      color: "#16A34A", bgColor: "#F0FDF4", label: "Completed"  },
  real_world:       { Icon: Star,        color: "#C8892B", bgColor: "#FFFBEB", label: "Real world" },
  passive_learning: { Icon: BookOpen,    color: "#707070", bgColor: "#FCFCFB", label: "Consumed"   },
  drift:            { Icon: TrendingDown,color: "#DC2626", bgColor: "#FEF2F2", label: "Drifted"    },
  dismissal:        { Icon: TrendingDown,color: "#DC2626", bgColor: "#FEF2F2", label: "Dismissed"  },
};

function formatTimeAgo(iso: string) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60)  return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60)  return `${mins}m ago`;
  const hrs  = Math.floor(mins / 60);
  if (hrs  < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function formatHour(iso: string) {
  const h = new Date(iso).getHours();
  const m = new Date(iso).getMinutes();
  const ampm = h >= 12 ? "pm" : "am";
  return `${h % 12 || 12}:${m.toString().padStart(2, "0")} ${ampm}`;
}

function confidenceColor(s: number) {
  if (s >= 0.8) return "#16A34A";
  if (s >= 0.5) return "#C8892B";
  return "#707070";
}

export function LiveObservationStream({
  seedEvents,
  maxRows = 8,
}: {
  seedEvents: EvidenceEvent[];
  maxRows?: number;
}) {
  const poolRef = useRef(0); // cycles through LIVE_POOL

  // Seed initial rows from real events (most recent first)
  const toEntry = useCallback((ev: EvidenceEvent): StreamEntry => ({
    id: ev.id,
    kind: ev.kind,
    label: ev.label,
    strength: ev.strength,
    identityLink: ev.attributeId === "builder" ? "Builder Identity" : ev.attributeId === "speaker" ? "Speaker Score" : "Drift Guardian",
    occurredAt: ev.occurredAt,
    isNew: false,
  }), []);

  const [entries, setEntries] = useState<StreamEntry[]>(() =>
    [...seedEvents]
      .sort((a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime())
      .slice(0, maxRows)
      .map(toEntry)
  );

  // Periodically inject a new simulated observation
  useEffect(() => {
    const scheduleNext = () => {
      const delay = 12_000 + Math.random() * 23_000;
      return setTimeout(() => {
        const item = LIVE_POOL[poolRef.current % LIVE_POOL.length]!;
        poolRef.current += 1;

        const newEntry: StreamEntry = {
          id: `live_${Date.now()}`,
          kind: item.kind,
          label: item.label,
          strength: item.strength,
          identityLink: item.identityLink,
          occurredAt: new Date().toISOString(),
          isNew: true,
        };

        setEntries((prev) => {
          const updated = [newEntry, ...prev].slice(0, maxRows);
          setTimeout(() => {
            setEntries((e) =>
              e.map((x) => x.id === newEntry.id ? { ...x, isNew: false } : x)
            );
          }, 3000);
          return updated;
        });

        timeoutRef.current = scheduleNext();
      }, delay);
    };

    const timeoutRef = { current: scheduleNext() };
    return () => clearTimeout(timeoutRef.current);
  }, [maxRows]);

  return (
    <div className="space-y-0 divide-y divide-black/[0.04]">
      <AnimatePresence mode="popLayout">
        {entries.map((entry) => {
          const cfg = KIND_CONFIG[entry.kind] ?? KIND_CONFIG["passive_learning"]!;
          const { Icon } = cfg;

          return (
            <motion.div
              key={entry.id}
              layout
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.35, ease }}
              className={`relative flex items-start gap-3 px-1 py-3 group transition-colors ${
                entry.isNew ? "bg-[#C8892B]/[0.03] rounded-xl" : ""
              }`}
            >
              {/* NEW pulse indicator */}
              {entry.isNew && (
                <motion.span
                  initial={{ opacity: 1 }}
                  animate={{ opacity: 0 }}
                  transition={{ duration: 2.5, delay: 0.5 }}
                  className="absolute right-2 top-3 font-mono text-[8.5px] font-semibold text-[#C8892B] uppercase tracking-[0.14em]"
                >
                  NEW
                </motion.span>
              )}

              {/* Hover accent line */}
              <div
                className="absolute left-0 top-3 bottom-3 w-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                style={{ backgroundColor: cfg.color }}
              />

              {/* Time */}
              <div className="w-14 shrink-0 pt-0.5 text-right font-mono text-[9px] text-[#707070] leading-tight">
                <p>{formatTimeAgo(entry.occurredAt)}</p>
                <p className="text-[8px] opacity-60">{formatHour(entry.occurredAt)}</p>
              </div>

              {/* Icon */}
              <div
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
                style={{ backgroundColor: cfg.bgColor, color: cfg.color }}
              >
                <Icon className="h-3 w-3" strokeWidth={1.8} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 pr-8">
                <p className="font-mono text-[10.5px] text-[#111111] leading-snug line-clamp-2">
                  {entry.label}
                </p>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  <span className="font-mono text-[9px] font-medium" style={{ color: cfg.color }}>
                    {cfg.label}
                  </span>
                  <span className="font-mono text-[8.5px] text-[#707070]">·</span>
                  <span className="font-mono text-[9px]" style={{ color: confidenceColor(entry.strength) }}>
                    {Math.round(entry.strength * 100)}% conf.
                  </span>
                  <span className="font-mono text-[8.5px] text-[#707070]">·</span>
                  <span className="font-mono text-[9px] text-[#707070]">
                    → {entry.identityLink}
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
