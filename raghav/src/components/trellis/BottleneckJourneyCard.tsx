import { useMemo } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  BOTTLENECK_STATUS_COPY,
  buildBottleneckTimeline,
  type BottleneckDayStatus,
} from "@/lib/trellis/bottleneckTimeline";
import type { BottleneckView } from "@/lib/trellis/store";
import type { DeclaredSelf, EvidenceEvent } from "@/lib/trellis/types";
import { cn } from "@/lib/utils";

const SPARK_W = 560;
const SPARK_H = 120;
const SPARK_PAD = { top: 12, right: 12, bottom: 22, left: 28 };
const SPARK_CHART_W = SPARK_W - SPARK_PAD.left - SPARK_PAD.right;
const SPARK_CHART_H = SPARK_H - SPARK_PAD.top - SPARK_PAD.bottom;

function scaleSparkX(index: number, total: number) {
  if (total <= 1) return SPARK_PAD.left + SPARK_CHART_W / 2;
  return SPARK_PAD.left + (index / (total - 1)) * SPARK_CHART_W;
}

function scaleSparkY(value: number) {
  return SPARK_PAD.top + SPARK_CHART_H - (value / 100) * SPARK_CHART_H;
}

function buildSparkPath(
  points: { x: number; y: number }[],
): string {
  if (points.length === 0) return "";
  return points.reduce((path, point, index) => {
    if (index === 0) return `M ${point.x} ${point.y}`;
    const prev = points[index - 1]!;
    const cx = (prev.x + point.x) / 2;
    return `${path} C ${cx} ${prev.y} ${cx} ${point.y} ${point.x} ${point.y}`;
  }, "");
}

function statusChipClass(status: BottleneckDayStatus): string {
  switch (BOTTLENECK_STATUS_COPY[status].tone) {
    case "signal":
      return "border-signal/35 bg-signal/10 text-signal";
    case "growth":
      return "border-growth/35 bg-growth/10 text-growth";
    case "muted":
      return "border-border bg-secondary text-muted-foreground";
    default:
      return "border-transparent bg-transparent text-muted-foreground/45";
  }
}

function BottleneckSparkline({
  spark,
}: {
  spark: ReturnType<typeof buildBottleneckTimeline>["spark"];
}) {
  const declaredPts = spark.map((point, index) => ({
    x: scaleSparkX(index, spark.length),
    y: scaleSparkY(point.declared),
  }));
  const revealedPts = spark.map((point, index) => ({
    x: scaleSparkX(index, spark.length),
    y: scaleSparkY(point.revealed),
  }));

  const declaredPath = buildSparkPath(declaredPts);
  const revealedPath = buildSparkPath(revealedPts);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-semibold tracking-tight text-foreground">
          Declared vs Revealed
        </p>
        <div className="flex items-center gap-5 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <span className="h-px w-5 border-t border-dashed border-muted-foreground/60" />
            Declared
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-0.5 w-5 rounded-full bg-signal" />
            Revealed
          </span>
        </div>
      </div>
      <svg
        viewBox={`0 0 ${SPARK_W} ${SPARK_H}`}
        className="w-full font-sans"
        style={{ height: SPARK_H }}
        aria-hidden
      >
        {[25, 50, 75].map((value) => (
          <line
            key={value}
            x1={SPARK_PAD.left}
            y1={scaleSparkY(value)}
            x2={SPARK_PAD.left + SPARK_CHART_W}
            y2={scaleSparkY(value)}
            stroke="rgba(17,17,17,0.05)"
            strokeWidth={0.8}
          />
        ))}
        <path
          d={declaredPath}
          fill="none"
          stroke="rgba(17,17,17,0.22)"
          strokeWidth={1.5}
          strokeDasharray="4 4"
        />
        <path
          d={revealedPath}
          fill="none"
          stroke="var(--signal)"
          strokeWidth={2}
          strokeLinecap="round"
        />
        {spark.map((point, index) => (
          <text
            key={point.label}
            x={scaleSparkX(index, spark.length)}
            y={SPARK_H - 4}
            textAnchor="middle"
            fill="#707070"
            fontSize="11"
            fontFamily="Satoshi, Inter, sans-serif"
          >
            {point.label}
          </text>
        ))}
      </svg>
    </div>
  );
}

export function BottleneckJourneyCard({
  bottleneck,
  events,
  declaredSelf,
  now,
  personaBottleneckLabel,
}: {
  bottleneck: BottleneckView;
  events: EvidenceEvent[];
  declaredSelf: DeclaredSelf;
  now: Date | string;
  personaBottleneckLabel?: string;
}) {
  const reduceMotion = useReducedMotion();
  const model = useMemo(
    () =>
      buildBottleneckTimeline({
        events,
        bottleneck,
        declaredSelf,
        now,
        personaBottleneckLabel,
      }),
    [events, bottleneck, declaredSelf, now, personaBottleneckLabel],
  );

  return (
    <section className="rounded-3xl border border-border bg-card p-6 sm:p-8 space-y-7">
      <div className="space-y-2.5">
        <p className="text-xs font-medium tracking-wide text-signal">
          What&apos;s blocking you
        </p>
        <h2 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight">
          {bottleneck.name}
        </h2>
        <p className="max-w-2xl text-base leading-relaxed text-muted-foreground">
          {bottleneck.diagnosis}
        </p>
      </div>

      <div className="space-y-6">
        {model.rows.map((row) => (
          <div key={row.id} className="space-y-3.5">
            {model.rows.length > 1 && (
              <p className="text-sm font-semibold text-foreground">
                {row.name}
              </p>
            )}
            <div className="grid grid-cols-5 gap-2 sm:gap-3">
              {model.days.map((day, index) => {
                const status = row.statuses[index] ?? "clear";
                const copy = BOTTLENECK_STATUS_COPY[status];

                return (
                  <div key={`${row.id}-${day.key}`} className="space-y-2 text-center">
                    <p className="text-xs font-medium text-muted-foreground">
                      {day.label}
                    </p>
                    <motion.div
                      initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.35, delay: index * 0.05 }}
                      className={cn(
                        "min-h-[5rem] rounded-2xl border px-2.5 py-3.5 flex items-center justify-center",
                        statusChipClass(status),
                      )}
                    >
                      <p className="text-sm font-medium leading-snug">
                        {copy.short}
                      </p>
                    </motion.div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-border pt-6">
        <BottleneckSparkline spark={model.spark} />
      </div>
    </section>
  );
}
