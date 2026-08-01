import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useMemo } from "react";
import { calculateAlignmentAt } from "@/lib/trellis/gapScore";
import type { DeclaredSelf, EvidenceEvent } from "@/lib/trellis/types";

const ALIGNMENT = "#64748B";
const SIGNAL = "#D97706";

/** Declared trajectory (ultra-thin dashed engineering line) vs Revealed trajectory (thin warm amber solid). */
export function TrajectoryChart({
  events,
  declaredSelf,
  now,
}: {
  events: EvidenceEvent[];
  declaredSelf: DeclaredSelf;
  now: Date | string;
}) {
  const series = useMemo(() => {
    const points: { day: string; declared: number; revealed: number }[] = [];
    const nowMs = new Date(now).getTime();
    for (let d = 20; d >= 0; d--) {
      const at = new Date(nowMs - d * 86_400_000);
      const past = events.filter((e) => new Date(e.occurredAt) <= at);
      const r = calculateAlignmentAt(past, declaredSelf, at);
      points.push({
        day: `D${21 - d}`,
        declared: Math.round(40 + (20 - d) * 2.6),
        revealed: r.alignment,
      });
    }
    return points;
  }, [events, declaredSelf, now]);

  return (
    <div className="h-[180px] w-full font-mono text-xs select-none">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}>
          <XAxis
            dataKey="day"
            tickLine={false}
            axisLine={false}
            interval={4}
            tick={{ fontSize: 9.5, fill: "#9A9A9A" }}
          />
          <YAxis
            domain={[0, 100]}
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 9.5, fill: "#9A9A9A" }}
          />
          <Tooltip
            contentStyle={{
              background: "#FFFFFF",
              border: "1px solid rgba(0,0,0,0.06)",
              borderRadius: 12,
              fontSize: 10.5,
              fontFamily: "ui-monospace, monospace",
              boxShadow: "0 8px 20px rgba(0,0,0,0.04)",
            }}
            labelStyle={{ color: "#9A9A9A" }}
          />
          <Line
            type="monotone"
            dataKey="declared"
            stroke={ALIGNMENT}
            strokeWidth={1.2}
            strokeDasharray="3 3"
            dot={false}
            name="Declared"
          />
          <Line
            type="monotone"
            dataKey="revealed"
            stroke={SIGNAL}
            strokeWidth={1.8}
            dot={false}
            name="Revealed"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
