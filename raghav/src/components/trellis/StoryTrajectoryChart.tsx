/**
 * StoryTrajectoryChart — Narrative SVG chart that tells a behavioural story.
 *
 * Refined IABTM theme:
 * - Burnt Amber (#C8892B) trajectory stroke & gradient fill
 * - Neutral muted ticks (#707070)
 * - Meticulously architectural, thin line weights
 */
import { useMemo, useState, useRef, useEffect } from "react";
import { motion } from "motion/react";
import { calculateAlignmentAt } from "@/lib/trellis/gapScore";
import type { DeclaredSelf, EvidenceEvent } from "@/lib/trellis/types";

const W = 640;
const H = 180;
const PAD = { top: 16, right: 20, bottom: 28, left: 36 };
const CHART_W = W - PAD.left - PAD.right;
const CHART_H = H - PAD.top - PAD.bottom;

interface DayPoint {
  day: number;        // 0 = oldest
  label: string;
  declared: number;   // 0..100
  revealed: number;   // 0..100
  driftCount: number;
  createCount: number;
  events: EvidenceEvent[];
}

function scaleX(day: number, total: number) {
  return PAD.left + (day / (total - 1)) * CHART_W;
}
function scaleY(val: number) {
  return PAD.top + CHART_H - (val / 100) * CHART_H;
}

function buildPath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  return points.reduce((d, p, i) => {
    if (i === 0) return `M ${p.x} ${p.y}`;
    const prev = points[i - 1]!;
    const cx = (prev.x + p.x) / 2;
    return `${d} C ${cx} ${prev.y} ${cx} ${p.y} ${p.x} ${p.y}`;
  }, "");
}

function buildAreaPath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  const base = CHART_H + PAD.top;
  const start = `M ${points[0]!.x} ${base}`;
  const line = points.reduce((d, p, i) => {
    if (i === 0) return `${d} L ${p.x} ${p.y}`;
    const prev = points[i - 1]!;
    const cx = (prev.x + p.x) / 2;
    return `${d} C ${cx} ${prev.y} ${cx} ${p.y} ${p.x} ${p.y}`;
  }, start);
  return `${line} L ${points[points.length - 1]!.x} ${base} Z`;
}

interface TooltipState {
  x: number;
  y: number;
  point: DayPoint;
}

export function StoryTrajectoryChart({
  events,
  declaredSelf,
  now,
}: {
  events: EvidenceEvent[];
  declaredSelf: DeclaredSelf;
  now: Date | string;
}) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const [pathLength, setPathLength] = useState<number | null>(null);
  const revealedPathRef = useRef<SVGPathElement>(null);

  const series = useMemo<DayPoint[]>(() => {
    const pts: DayPoint[] = [];
    const DAYS = 21;
    const nowMs = new Date(now).getTime();
    for (let d = DAYS - 1; d >= 0; d--) {
      const at = new Date(nowMs - d * 86_400_000);
      const pastEvents = events.filter((e) => new Date(e.occurredAt) <= at);
      const r = calculateAlignmentAt(pastEvents, declaredSelf, at);
      const dayEvents = events.filter((e) => {
        const eDate = new Date(e.occurredAt);
        const dayStart = new Date(at); dayStart.setHours(0, 0, 0, 0);
        const dayEnd = new Date(at); dayEnd.setHours(23, 59, 59, 999);
        return eDate >= dayStart && eDate <= dayEnd;
      });
      const idx = DAYS - 1 - d;
      pts.push({
        day: idx,
        label: `D${idx + 1}`,
        declared: Math.round(40 + (DAYS - 1 - d) * 2.6),
        revealed: r.alignment,
        driftCount: dayEvents.filter((e) => e.kind === "drift").length,
        createCount: dayEvents.filter(
          (e) => e.kind === "creation" || e.kind === "completion"
        ).length,
        events: dayEvents,
      });
    }
    return pts;
  }, [events, declaredSelf, now]);

  const revealedPts = series.map((p) => ({
    x: scaleX(p.day, series.length),
    y: scaleY(p.revealed),
  }));
  const declaredPts = series.map((p) => ({
    x: scaleX(p.day, series.length),
    y: scaleY(p.declared),
  }));

  const revealedPath = buildPath(revealedPts);
  const areaPath = buildAreaPath(revealedPts);
  const declaredPath = buildPath(declaredPts);

  // Measure path length for drawing animation
  useEffect(() => {
    if (revealedPathRef.current) {
      setPathLength(revealedPathRef.current.getTotalLength());
    }
  }, [revealedPath]);

  // Drift zones: days where driftCount > 0 and no creates
  const driftZones = series.filter((p) => p.driftCount > 0 && p.createCount === 0);
  // Milestone days: creation or high-drift
  const milestones = series.filter((p) => p.createCount > 0 || p.driftCount >= 2);

  function handleMouseMove(e: React.MouseEvent<SVGSVGElement>) {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const rawX = ((e.clientX - rect.left) / rect.width) * W - PAD.left;
    const idx = Math.max(
      0,
      Math.min(series.length - 1, Math.round((rawX / CHART_W) * (series.length - 1)))
    );
    const p = series[idx]!;
    setTooltip({
      x: scaleX(p.day, series.length),
      y: scaleY(p.revealed),
      point: p,
    });
  }

  // Tick labels — show every 5 days
  const ticks = series.filter((_, i) => i % 4 === 0 || i === series.length - 1);

  return (
    <div className="relative select-none">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        style={{ height: 180 }}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setTooltip(null)}
        aria-hidden
      >
        <defs>
          {/* Burnt amber fill gradient #C8892B */}
          <linearGradient id="revealedGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#C8892B" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#C8892B" stopOpacity="0.01" />
          </linearGradient>
          {/* Drift zone fill */}
          <linearGradient id="driftGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#DC2626" stopOpacity="0.05" />
            <stop offset="100%" stopColor="#DC2626" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Subtle grid lines */}
        {[25, 50, 75].map((v) => (
          <line
            key={v}
            x1={PAD.left}
            y1={scaleY(v)}
            x2={PAD.left + CHART_W}
            y2={scaleY(v)}
            stroke="rgba(17,17,17,0.04)"
            strokeWidth={0.8}
          />
        ))}

        {/* Drift zone rectangles */}
        {driftZones.map((p) => {
          const x = scaleX(p.day, series.length) - CHART_W / series.length / 2;
          const w = CHART_W / series.length;
          return (
            <rect
              key={p.day}
              x={x}
              y={PAD.top}
              width={w}
              height={CHART_H}
              fill="url(#driftGrad)"
            />
          );
        })}

        {/* Area fill under revealed */}
        <path d={areaPath} fill="url(#revealedGrad)" />

        {/* Declared trajectory — thin dashed architectural */}
        <path
          d={declaredPath}
          fill="none"
          stroke="rgba(17,17,17,0.18)"
          strokeWidth={1}
          strokeDasharray="4 4"
        />

        {/* Revealed trajectory — animated drawing */}
        {pathLength !== null && (
          <motion.path
            ref={revealedPathRef}
            d={revealedPath}
            fill="none"
            stroke="#C8892B"
            strokeWidth={1.8}
            strokeLinecap="round"
            initial={{ strokeDashoffset: pathLength, strokeDasharray: pathLength }}
            animate={{ strokeDashoffset: 0 }}
            transition={{ duration: 1.8, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          />
        )}
        {/* Invisible ref path for measuring length */}
        {pathLength === null && (
          <path
            ref={revealedPathRef}
            d={revealedPath}
            fill="none"
            stroke="transparent"
            strokeWidth={1.8}
          />
        )}

        {/* Milestone dots */}
        {milestones.map((p) => {
          const px = scaleX(p.day, series.length);
          const py = scaleY(p.revealed);
          const isCreate = p.createCount > 0;
          return (
            <motion.circle
              key={`m-${p.day}`}
              cx={px}
              cy={py}
              r={3.5}
              fill={isCreate ? "#16A34A" : "#DC2626"}
              fillOpacity={0.7}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.3, delay: 1.8 + p.day * 0.02 }}
            />
          );
        })}

        {/* Hover cursor line + dot */}
        {tooltip && (
          <>
            <line
              x1={tooltip.x}
              y1={PAD.top}
              x2={tooltip.x}
              y2={PAD.top + CHART_H}
              stroke="rgba(17,17,17,0.1)"
              strokeWidth={1}
              strokeDasharray="2 2"
            />
            <circle
              cx={tooltip.x}
              cy={tooltip.y}
              r={4}
              fill="#C8892B"
              fillOpacity={0.9}
            />
          </>
        )}

        {/* X-axis ticks */}
        {ticks.map((p) => (
          <text
            key={p.day}
            x={scaleX(p.day, series.length)}
            y={H - 6}
            textAnchor="middle"
            fontSize={8.5}
            fill="#707070"
            fontFamily="ui-monospace, monospace"
          >
            {p.label}
          </text>
        ))}

        {/* Y-axis labels */}
        {[0, 50, 100].map((v) => (
          <text
            key={v}
            x={PAD.left - 6}
            y={scaleY(v) + 3}
            textAnchor="end"
            fontSize={8}
            fill="#707070"
            fontFamily="ui-monospace, monospace"
          >
            {v}
          </text>
        ))}
      </svg>

      {/* Tooltip overlay */}
      {tooltip && (
        <div
          className="pointer-events-none absolute z-10 rounded-xl border border-black/[0.06] bg-white/95 px-3.5 py-2.5 shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-md"
          style={{
            left: `${(tooltip.x / W) * 100}%`,
            top: `${(tooltip.y / H) * 100}%`,
            transform: "translate(-50%, -110%)",
          }}
        >
          <p className="font-mono text-[10px] text-[#707070] uppercase tracking-[0.12em] mb-1">
            {tooltip.point.label}
          </p>
          <p className="font-mono text-xs text-[#111111] font-medium">
            Alignment: {tooltip.point.revealed}%
          </p>
          {tooltip.point.createCount > 0 && (
            <p className="font-mono text-[10px] text-[#16A34A]">
              ↑ {tooltip.point.createCount} creation event{tooltip.point.createCount > 1 ? "s" : ""}
            </p>
          )}
          {tooltip.point.driftCount > 0 && (
            <p className="font-mono text-[10px] text-[#DC2626]">
              ↓ {tooltip.point.driftCount} drift event{tooltip.point.driftCount > 1 ? "s" : ""}
            </p>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="mt-3 flex items-center gap-6 font-mono text-[10px] text-[#707070]">
        <span className="flex items-center gap-1.5">
          <span className="block h-px w-5 border-t border-dashed border-[#3B3B3B]/60" />
          Declared
        </span>
        <span className="flex items-center gap-1.5">
          <span className="block h-0.5 w-5 rounded-full bg-[#C8892B]" />
          Revealed
        </span>
        <span className="flex items-center gap-1.5">
          <span className="block h-2 w-2 rounded-full bg-[#16A34A] opacity-70" />
          Creation event
        </span>
        <span className="flex items-center gap-1.5">
          <span className="block h-2 w-2 rounded-full bg-[#DC2626] opacity-70" />
          Drift spike
        </span>
      </div>
    </div>
  );
}
