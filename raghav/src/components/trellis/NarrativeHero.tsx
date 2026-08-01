/**
 * NarrativeHero — The command center of the Identity Operating System.
 *
 * Refined IABTM theme:
 * - Crisp contrast (#111111 / #3B3B3B / #707070)
 * - Restrained burnt amber (#C8892B)
 * - Card shadows: 0 8px 32px rgba(17, 17, 17, 0.03)
 */
import { motion } from "motion/react";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { CountNumber } from "./CountNumber";

const ease = [0.16, 1, 0.3, 1] as const;

interface NarrativeHeroProps {
  gapScore: number;
  alignment: number;
  identityState: { label: string; sub: string; color: string };
  drift: { label: string; direction: "up" | "down" | "flat"; delta: number };
  createRatio: number;
  onBreakdownOpen: () => void;
  declaredLabel: string;
}

function buildNarrativeProse(
  score: number,
  drift: { direction: "up" | "down" | "flat"; delta: number }
): { line1: string; line2: string } {
  const away = 100 - score;

  const l1 =
    score <= 20
      ? `Only ${score} points separating you from the identity you declared.`
      : score <= 40
      ? `${away} points of alignment still ahead.`
      : score <= 60
      ? `Still ${away} points away from full alignment.`
      : `${away} points remain between declared and observed.`;

  const l2 =
    drift.direction === "up"
      ? "This week your behaviour is trending toward the identity you described."
      : drift.direction === "down"
      ? "This week your behaviour is pulling away from your declared identity."
      : "Holding position. No significant drift detected this week.";

  return { line1: l1, line2: l2 };
}

export function NarrativeHero({
  gapScore,
  alignment,
  identityState,
  drift,
  createRatio,
  onBreakdownOpen,
  declaredLabel,
}: NarrativeHeroProps) {
  const prose = buildNarrativeProse(gapScore, drift);
  const observedWidth = Math.max(4, Math.round(alignment));
  const declaredWidth = 100;

  // Adapt identity state color if it's amber to use burnt amber #C8892B
  const stateColor = identityState.color === "#D97706" ? "#C8892B" : identityState.color;

  return (
    <section className="grid gap-10 lg:grid-cols-12 lg:items-start">
      {/* ── Left: Dominant Gap Score + Prose ── */}
      <div className="lg:col-span-7 space-y-6">
        {/* Eyebrow */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease }}
          className="flex items-center gap-2 font-mono text-[10.5px] tracking-[0.22em] text-[#707070] uppercase font-medium"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-[#C8892B]" />
          IDENTITY GAP
        </motion.div>

        {/* Giant Number */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05, ease }}
        >
          <button
            onClick={onBreakdownOpen}
            className="group text-left hover:opacity-75 transition-opacity"
            aria-label="View gap score breakdown"
          >
            <CountNumber
              value={gapScore}
              className="num text-[8rem] sm:text-[10rem] font-medium leading-none tracking-tight text-[#111111]"
            />
          </button>
        </motion.div>

        {/* Narrative Prose */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease }}
          className="space-y-1"
        >
          <p className="text-base text-[#111111] font-medium leading-snug">
            {prose.line1}
          </p>
          <p className="text-sm text-[#3B3B3B] leading-relaxed">
            {prose.line2}
          </p>
        </motion.div>

        {/* Visual Gap Bars — Declared vs Observed */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15, ease }}
          className="space-y-3 pt-2"
        >
          {/* Declared bar */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between font-mono text-[10px] text-[#707070] uppercase tracking-[0.14em]">
              <span>Declared Identity</span>
              <span>{declaredLabel}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-black/[0.05]">
              <div
                className="h-full rounded-full bg-[#111111]/20"
                style={{ width: `${declaredWidth}%` }}
              />
            </div>
          </div>

          {/* Observed bar */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between font-mono text-[10px] text-[#707070] uppercase tracking-[0.14em]">
              <span>Observed Behaviour</span>
              <span>{alignment}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-black/[0.05]">
              <motion.div
                className="h-full rounded-full bg-[#C8892B]"
                initial={{ width: "4%" }}
                animate={{ width: `${observedWidth}%` }}
                transition={{ duration: 1.2, delay: 0.3, ease }}
              />
            </div>
          </div>

          {/* Gap label */}
          <p className="font-mono text-[10px] text-[#707070]">
            ↳ gap of{" "}
            <span className="text-[#111111] font-semibold">{100 - alignment}</span>
            {" "}points between declared and observed
          </p>
        </motion.div>
      </div>

      {/* ── Right: Secondary Metrics ── */}
      <div className="lg:col-span-5 space-y-4 lg:pt-2">
        {/* Alignment */}
        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.12, ease }}
          className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-xl"
        >
          <p className="font-mono text-[10px] tracking-[0.18em] text-[#707070] uppercase font-medium mb-2">
            ALIGNMENT
          </p>
          <div className="flex items-baseline gap-1 mb-3">
            <CountNumber
              value={alignment}
              className="num text-4xl font-medium leading-none tracking-tight text-[#111111]"
            />
            <span className="text-lg font-medium text-[#3B3B3B]">%</span>
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-black/[0.05]">
            <motion.div
              className="h-full rounded-full bg-[#C8892B]"
              initial={{ width: 0 }}
              animate={{ width: `${alignment}%` }}
              transition={{ duration: 1, delay: 0.4, ease }}
            />
          </div>
        </motion.div>

        {/* Identity State */}
        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.18, ease }}
          className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-xl"
        >
          <p className="font-mono text-[10px] tracking-[0.18em] text-[#707070] uppercase font-medium mb-2">
            IDENTITY STATE
          </p>
          <p
            className="text-2xl font-medium tracking-tight mb-1"
            style={{ color: stateColor }}
          >
            {identityState.label}
          </p>
          <p className="font-mono text-[10.5px] text-[#3B3B3B] leading-relaxed">
            {identityState.sub}
          </p>
        </motion.div>

        {/* Drift Direction */}
        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.24, ease }}
          className="rounded-2xl border border-black/[0.06] bg-white p-6 shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-xl"
        >
          <p className="font-mono text-[10px] tracking-[0.18em] text-[#707070] uppercase font-medium mb-2">
            DRIFT DIRECTION
          </p>
          <div className="flex items-center gap-2 mb-1">
            {drift.direction === "up" && (
              <TrendingUp className="h-5 w-5 text-[#16A34A]" strokeWidth={1.5} />
            )}
            {drift.direction === "down" && (
              <TrendingDown className="h-5 w-5 text-[#DC2626]" strokeWidth={1.5} />
            )}
            {drift.direction === "flat" && (
              <Minus className="h-5 w-5 text-[#707070]" strokeWidth={1.5} />
            )}
            <span
              className="text-xl font-medium tracking-tight"
              style={{
                color:
                  drift.direction === "up"
                    ? "#16A34A"
                    : drift.direction === "down"
                    ? "#DC2626"
                    : "#707070",
              }}
            >
              {drift.label}
            </span>
          </div>
          {/* Create ratio indicator */}
          <p className="font-mono text-[10px] text-[#707070]">
            {Math.round(createRatio * 100)}% of activity is creation
          </p>
        </motion.div>
      </div>
    </section>
  );
}
