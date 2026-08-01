/**
 * AIInterventionCard — AI-generated mission card with full reasoning + completion states.
 *
 * Refined IABTM theme:
 * - Crisp text contrast (#111111 / #3B3B3B / #707070)
 * - Restrained burnt amber (#C8892B)
 * - Outline button styling with no gray fill
 * - Soft card shadow: 0 8px 32px rgba(17,17,17,0.03)
 */
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { CheckCircle2, Circle, ChevronDown, X, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { useTrellis } from "@/lib/trellis/store";
import type { StackElement } from "@/lib/trellis/types";

const ease = [0.16, 1, 0.3, 1] as const;

function deriveImpact(el: StackElement): { label: string; color: string; alignmentGain: number } {
  if (el.type === "Micro Mission" || el.type === "Real-World Experience")
    return { label: "High",   color: "#16A34A", alignmentGain: 4 };
  if (el.type === "Media" || el.type === "Knowledge")
    return { label: "Medium", color: "#C8892B", alignmentGain: 2 };
  return { label: "Low", color: "#707070", alignmentGain: 1 };
}

function deriveConfidence(el: StackElement): number {
  const base = el.type === "Micro Mission" ? 92 : el.type === "Media" ? 84 : 78;
  return el.source === "Live web" ? base + 3 : base;
}

function daysSinceLabel(el: StackElement): string {
  const days: Record<string, number> = {
    "st_media": 8, "st_mission": 5, "st_story": 12,
  };
  const d = days[el.id] ?? 7;
  return `${d} day${d !== 1 ? "s" : ""} ago`;
}

interface AIInterventionCardProps {
  element: StackElement;
  isCompleted: boolean;
  onToggle: (id: string) => void;
  declaredLabel: string;
  currentAlignment?: number;
  animationDelay?: number;
}

export function AIInterventionCard({
  element,
  isCompleted,
  onToggle,
  declaredLabel,
  currentAlignment = 31,
  animationDelay = 0,
}: AIInterventionCardProps) {
  const { tier, dismissStackElement } = useTrellis();
  const [reasoning, setReasoning] = useState(false);
  const [wasDismissed, setWasDismissed] = useState(false);

  const variant = element.variants[tier];
  const impact = deriveImpact(element);
  const confidence = deriveConfidence(element);
  const newAlignment = Math.min(100, currentAlignment + impact.alignmentGain);

  if (wasDismissed) return null;

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97, height: 0 }}
      whileHover={{ y: isCompleted ? 0 : -2 }}
      transition={{ duration: 0.35, delay: animationDelay, ease }}
      className={`group relative rounded-2xl border p-5 transition-all duration-200 ${
        isCompleted
          ? "border-[#16A34A]/20 bg-[#F0FDF4]/60 shadow-none"
          : "border-black/[0.06] bg-white hover:border-black/[0.12] shadow-[0_8px_32px_rgba(17,17,17,0.03)]"
      } backdrop-blur-xl`}
    >
      {/* ── Completion state ── */}
      <AnimatePresence mode="wait">
        {isCompleted ? (
          <motion.div
            key="completed"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, ease }}
            className="space-y-3"
          >
            {/* Identity updated header */}
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#16A34A] shrink-0" strokeWidth={1.5} />
              <span className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-[#16A34A] font-semibold">
                Identity Updated
              </span>
            </div>

            <h3 className="text-sm font-medium text-[#707070] line-through leading-snug">
              {variant?.title ?? element.action}
            </h3>

            {/* Update metrics */}
            <div className="grid grid-cols-2 gap-2 pt-1">
              <div className="rounded-lg border border-[#16A34A]/20 bg-[#16A34A]/[0.06] p-2.5 text-center">
                <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-[#707070] mb-1">
                  {declaredLabel.split(" ").slice(-1)[0]} Score
                </p>
                <p className="font-mono text-sm font-medium text-[#16A34A]">
                  +{impact.alignmentGain}
                </p>
              </div>
              <div className="rounded-lg border border-[#16A34A]/20 bg-[#16A34A]/[0.06] p-2.5 text-center">
                <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-[#707070] mb-1">
                  Alignment now
                </p>
                <p className="font-mono text-sm font-medium text-[#16A34A]">{newAlignment}%</p>
              </div>
            </div>

            {/* Undo */}
            <button
              onClick={() => onToggle(element.id)}
              className="font-mono text-[9.5px] text-[#707070] hover:text-[#111111] transition-colors"
            >
              Mark incomplete
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="pending"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Dismiss */}
            <button
              onClick={() => {
                dismissStackElement(element.id);
                setWasDismissed(true);
                toast("Dismissed — evidence logged", {
                  description: "Gap score adjusted for the missing marker.",
                });
              }}
              aria-label="Dismiss"
              className="absolute right-4 top-4 text-[#707070] hover:text-[#111111] transition-colors opacity-0 group-hover:opacity-100"
            >
              <X className="h-3.5 w-3.5" />
            </button>

            {/* Type + title row */}
            <div className="flex items-start gap-3">
              <button
                onClick={() => onToggle(element.id)}
                className="mt-0.5 shrink-0 transition-colors"
                aria-label="Mark complete"
              >
                <Circle
                  className="h-4 w-4 text-[#707070] group-hover:text-[#C8892B] transition-colors"
                  strokeWidth={1.5}
                />
              </button>
              <div className="flex-1 min-w-0">
                <p className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#707070] mb-1.5">
                  {element.type}
                </p>
                <h3 className="text-sm font-medium text-[#111111] leading-snug">
                  {variant?.title ?? element.action}
                </h3>
                <p className="mt-1 font-mono text-[10px] text-[#C8892B]">{variant?.duration} effort</p>
              </div>
            </div>

            {/* Context signals */}
            <div className="mt-3.5 rounded-xl border border-black/[0.05] bg-[#FCFCFB] p-3 font-mono text-[10px] space-y-1.5">
              <div className="flex items-center justify-between text-[#707070]">
                <span>Chosen because</span>
                <span
                  className="font-medium"
                  style={{ color: impact.color }}
                >
                  {impact.label} impact
                </span>
              </div>
              <p className="text-[#3B3B3B] leading-relaxed">
                <span className="text-[#707070]">Confidence Builder</span> dropped{" "}
                <span className="text-[#DC2626] font-medium">12%</span> — last relevant activity{" "}
                <span className="text-[#111111]">{daysSinceLabel(element)}</span>.
              </p>
              <div className="flex items-center gap-2 pt-0.5">
                <TrendingUp className="h-3 w-3 text-[#16A34A]" strokeWidth={1.5} />
                <span className="text-[#16A34A] font-medium">
                  Expected +{impact.alignmentGain} alignment
                </span>
                <span className="text-[#707070]">· {confidence}% conf.</span>
              </div>
            </div>

            {/* Full reasoning toggle */}
            <button
              onClick={() => setReasoning((r) => !r)}
              className="mt-3 flex items-center gap-1 font-mono text-[9.5px] text-[#707070] hover:text-[#111111] transition-colors"
            >
              Based on what?
              <ChevronDown
                className={`h-3 w-3 transition-transform duration-200 ${reasoning ? "rotate-180" : ""}`}
              />
            </button>

            <AnimatePresence initial={false}>
              {reasoning && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease }}
                  className="overflow-hidden"
                >
                  <div className="mt-3 rounded-xl border border-black/[0.05] bg-[#FCFCFB] p-3.5 space-y-2.5 font-mono text-[10.5px]">
                    {[
                      ["You declared", declaredLabel],
                      ["Observed gap", element.why],
                      ["Why now", element.whyNow],
                      ["How it closes the gap", element.howItCloses],
                    ].map(([k, v]) => (
                      <div key={k}>
                        <p className="text-[9px] uppercase tracking-[0.14em] text-[#707070] mb-0.5">{k}</p>
                        <p className="text-[#3B3B3B] leading-relaxed text-[10px]">{v}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Action button — IABTM Outline styling with no gray fill */}
            <button
              onClick={() => onToggle(element.id)}
              className="mt-4 w-full rounded-xl border border-black/[0.08] bg-transparent py-2 font-mono text-[10.5px] text-[#111111] font-medium transition-all hover:bg-[#111111] hover:text-white hover:border-[#111111]"
            >
              {element.action} — Mark complete
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}
