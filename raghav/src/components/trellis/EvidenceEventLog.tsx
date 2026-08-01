/**
 * EvidenceEventLog — AI-style event log for the behaviour feed.
 *
 * Refined IABTM theme:
 * - Crisp text hierarchy (#111111 / #3B3B3B / #707070)
 * - Restrained burnt amber (#C8892B)
 */
import { motion, AnimatePresence } from "motion/react";
import { Hammer, BookOpen, TrendingDown, Star } from "lucide-react";
import type { EvidenceEvent } from "@/lib/trellis/types";

const ease = [0.16, 1, 0.3, 1] as const;

interface KindConfig {
  label: string;
  color: string;      // border + dot
  bgColor: string;    // row background tint
  Icon: React.FC<{ className?: string; strokeWidth?: number }>;
}

const KIND_MAP: Record<string, KindConfig> = {
  creation:         { label: "Created",     color: "#16A34A", bgColor: "#F0FDF4", Icon: Hammer },
  completion:       { label: "Completed",   color: "#16A34A", bgColor: "#F0FDF4", Icon: Hammer },
  real_world:       { label: "Real world",  color: "#C8892B", bgColor: "#FFFBEB", Icon: Star },
  passive_learning: { label: "Consumed",    color: "#707070", bgColor: "#FCFCFB", Icon: BookOpen },
  drift:            { label: "Drifted",     color: "#DC2626", bgColor: "#FEF2F2", Icon: TrendingDown },
  dismissal:        { label: "Dismissed",   color: "#DC2626", bgColor: "#FEF2F2", Icon: TrendingDown },
};

function confidenceLabel(strength: number): { text: string; color: string } {
  if (strength >= 0.8) return { text: `${Math.round(strength * 100)}% conf.`, color: "#16A34A" };
  if (strength >= 0.5) return { text: `${Math.round(strength * 100)}% conf.`, color: "#C8892B" };
  return { text: `${Math.round(strength * 100)}% conf.`, color: "#707070" };
}

function formatTimeAgo(occurredAt: string): string {
  const days = Math.floor(
    (Date.now() - new Date(occurredAt).getTime()) / 86_400_000
  );
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days}d ago`;
}

function formatHour(occurredAt: string): string {
  const h = new Date(occurredAt).getHours();
  const ampm = h >= 12 ? "pm" : "am";
  const hour = h % 12 || 12;
  return `${hour}:00 ${ampm}`;
}

// Create / consume / drift summary for the bottom
function buildRatioSummary(events: EvidenceEvent[]) {
  const create = events.filter(
    (e) => e.kind === "creation" || e.kind === "completion" || e.kind === "real_world"
  ).length;
  const consume = events.filter((e) => e.kind === "passive_learning").length;
  const drift = events.filter((e) => e.kind === "drift" || e.kind === "dismissal").length;
  return { create, consume, drift };
}

export function EvidenceEventLog({
  events,
  maxRows = 9,
}: {
  events: EvidenceEvent[];
  maxRows?: number;
}) {
  const sorted = [...events]
    .sort(
      (a, b) =>
        new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime()
    )
    .slice(0, maxRows);

  const ratio = buildRatioSummary(events);

  return (
    <div>
      {/* Event rows */}
      <div className="space-y-0 divide-y divide-black/[0.04]">
        <AnimatePresence>
          {sorted.map((ev, idx) => {
            const cfg = KIND_MAP[ev.kind] ?? KIND_MAP["passive_learning"]!;
            const conf = confidenceLabel(ev.strength);
            const { Icon } = cfg;

            return (
              <motion.div
                key={ev.id}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25, delay: idx * 0.035, ease }}
                className="relative flex items-start gap-3 px-1 py-3 group"
              >
                {/* Color-coded left bar */}
                <div
                  className="absolute left-0 top-3 bottom-3 w-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ backgroundColor: cfg.color }}
                />

                {/* Time column */}
                <div className="w-16 shrink-0 pt-0.5 text-right font-mono text-[9.5px] text-[#707070] leading-tight">
                  <p>{formatTimeAgo(ev.occurredAt)}</p>
                  <p className="text-[8.5px] opacity-60">{formatHour(ev.occurredAt)}</p>
                </div>

                {/* Icon */}
                <div
                  className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
                  style={{ backgroundColor: cfg.bgColor, color: cfg.color }}
                >
                  <Icon
                    className="h-3 w-3"
                    strokeWidth={1.8}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-mono text-[11px] text-[#111111] leading-snug truncate">
                      {ev.label}
                    </p>
                    {(ev as any).simulated === false || (ev as any).isSimulated === false ? (
                      <span className="inline-flex items-center rounded border border-emerald-600/30 bg-emerald-500/10 px-1.5 py-0.2 text-[8.5px] font-semibold text-emerald-600 shrink-0">
                        LIVE
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded border border-neutral-300 bg-neutral-100 px-1.5 py-0.2 text-[8.5px] font-medium text-neutral-500 shrink-0">
                        SIM
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span
                      className="font-mono text-[9.5px] font-medium"
                      style={{ color: cfg.color }}
                    >
                      {cfg.label}
                    </span>
                    <span className="font-mono text-[9px] text-[#707070]">·</span>
                    <span
                      className="font-mono text-[9.5px]"
                      style={{ color: conf.color }}
                    >
                      {conf.text}
                    </span>
                  </div>
                </div>
              </motion.div>

            );
          })}
        </AnimatePresence>
      </div>

      {/* Create / Consume / Drift ratio footer */}
      <div className="mt-4 pt-4 border-t border-black/[0.05] grid grid-cols-3 gap-1 text-center">
        {[
          { label: "CREATE", value: ratio.create, color: "#16A34A" },
          { label: "CONSUME", value: ratio.consume, color: "#707070" },
          { label: "DRIFT", value: ratio.drift, color: "#DC2626" },
        ].map(({ label, value, color }) => (
          <div key={label}>
            <p
              className="font-mono text-base font-medium"
              style={{ color }}
            >
              {value}
            </p>
            <p className="font-mono text-[9px] text-[#707070] uppercase tracking-[0.14em] mt-0.5">
              {label}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
