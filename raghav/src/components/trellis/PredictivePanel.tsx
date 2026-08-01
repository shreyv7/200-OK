/**
 * PredictivePanel — AI scenario simulation panel.
 *
 * Refined IABTM theme:
 * - Text hierarchy (#111111 / #3B3B3B / #707070)
 * - Restrained burnt amber (#C8892B)
 */
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ArrowRight, TrendingUp } from "lucide-react";

const ease = [0.16, 1, 0.3, 1] as const;

interface Scenario {
  id: string;
  label: string;
  description: string;
  alignmentDelta: number;
  confidenceDelta: number;
  driftDelta: number;
  days: string;
}

function buildScenarios(
  currentAlignment: number,
  currentGap: number,
  createRatio: number,
  missionCount: number
): Scenario[] {
  const perMission = 2 + Math.round(createRatio * 3);

  return [
    {
      id: "full",
      label: "Complete today's stack",
      description: `All ${missionCount} mission${missionCount !== 1 ? "s" : ""} completed`,
      alignmentDelta:  missionCount * perMission,
      confidenceDelta: +4,
      driftDelta:      -7,
      days: "today",
    },
    {
      id: "partial",
      label: "Partial completion",
      description: `${Math.ceil(missionCount / 2)} of ${missionCount} missions`,
      alignmentDelta:  Math.ceil(missionCount / 2) * perMission,
      confidenceDelta: +2,
      driftDelta:      -3,
      days: "1–2 days",
    },
    {
      id: "none",
      label: "No action today",
      description: "Evidence continues to decay",
      alignmentDelta:  -2,
      confidenceDelta: -1,
      driftDelta:      +5,
      days: "—",
    },
  ];
}

function DeltaLine({
  label,
  value,
  suffix = "",
}: {
  label: string;
  value: number;
  suffix?: string;
}) {
  const positive = value > 0;
  const neutral  = value === 0;
  const isGoodPositive = label !== "Execution drift";
  const isGood = neutral ? true : isGoodPositive ? positive : !positive;

  const color = neutral ? "#707070" : isGood ? "#16A34A" : "#DC2626";
  const sign  = value > 0 ? "+" : "";

  return (
    <div className="flex items-center justify-between font-mono text-[10px]">
      <span className="text-[#707070]">{label}</span>
      <span className="font-medium" style={{ color }}>
        {sign}{value}{suffix}
      </span>
    </div>
  );
}

interface PredictivePanelProps {
  currentAlignment: number;
  currentGap: number;
  missionsCompleted: number;
  missionCount: number;
  createRatio: number;
}

export function PredictivePanel({
  currentAlignment,
  currentGap,
  missionsCompleted,
  missionCount,
  createRatio,
}: PredictivePanelProps) {
  const [activeScenario, setActiveScenario] = useState<string>("full");
  const pendingMissions = missionCount - missionsCompleted;

  const scenarios = buildScenarios(currentAlignment, currentGap, createRatio, pendingMissions);
  const selected = scenarios.find((s) => s.id === activeScenario) ?? scenarios[0]!;
  const forecastAlignment = Math.max(0, Math.min(100, currentAlignment + selected.alignmentDelta));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#707070] font-medium">
        <TrendingUp className="h-3 w-3 text-[#C8892B]" strokeWidth={1.5} />
        IF YOU…
      </div>

      {/* Scenario selector — three quiet outline tabs */}
      <div className="flex gap-1.5">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveScenario(s.id)}
            className={`flex-1 rounded-lg border py-2 px-2 font-mono text-[9px] transition-all duration-200 leading-snug ${
              s.id === activeScenario
                ? "border-[#111111] bg-[#111111] text-white"
                : "border-black/[0.06] bg-transparent text-[#3B3B3B] hover:border-black/[0.12] hover:text-[#111111]"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Selected scenario detail */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeScenario}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.25, ease }}
          className="space-y-3.5"
        >
          {/* Alignment trajectory */}
          <div className="flex items-center gap-3">
            <div className="text-center shrink-0">
              <p className="font-mono text-[8.5px] text-[#707070] mb-0.5">NOW</p>
              <p className="font-mono text-lg font-medium text-[#111111]">{currentAlignment}%</p>
            </div>

            <div className="flex-1 flex items-center gap-2">
              <div className="flex-1 h-px bg-gradient-to-r from-black/[0.08] via-[#C8892B]/30 to-transparent" />
              <motion.div
                animate={{ x: [0, 3, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                <ArrowRight className="h-3.5 w-3.5 text-[#C8892B] shrink-0" strokeWidth={1.5} />
              </motion.div>
              <div className="flex-1 h-px bg-gradient-to-l from-[#16A34A]/20 to-transparent" />
            </div>

            <div className="text-center shrink-0">
              <p className="font-mono text-[8.5px] text-[#707070] mb-0.5">{selected.days.toUpperCase()}</p>
              <p
                className="font-mono text-lg font-medium"
                style={{ color: selected.alignmentDelta >= 0 ? "#16A34A" : "#DC2626" }}
              >
                {forecastAlignment}%
              </p>
            </div>
          </div>

          {/* Progress comparison bar */}
          <div className="space-y-1.5">
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-black/[0.05]">
              <motion.div
                className="h-full rounded-full bg-black/20"
                initial={{ width: 0 }}
                animate={{ width: `${currentAlignment}%` }}
                transition={{ duration: 0.6, ease }}
              />
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-black/[0.05]">
              <motion.div
                className="h-full rounded-full"
                style={{
                  background: selected.alignmentDelta >= 0
                    ? "linear-gradient(90deg, #C8892B, #16A34A)"
                    : "#DC2626",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${forecastAlignment}%` }}
                transition={{ duration: 0.9, delay: 0.15, ease }}
              />
            </div>
          </div>

          {/* Consequence deltas */}
          <div className="rounded-xl border border-black/[0.05] bg-[#FCFCFB] p-3 space-y-1.5">
            <DeltaLine label="Alignment"        value={selected.alignmentDelta}  suffix="%" />
            <DeltaLine label="Confidence"       value={selected.confidenceDelta} suffix="%" />
            <DeltaLine label="Execution drift"  value={selected.driftDelta}      suffix="%" />
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
