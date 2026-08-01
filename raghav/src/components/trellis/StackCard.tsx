import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ChevronDown, X } from "lucide-react";
import { toast } from "sonner";
import { useTrellis } from "@/lib/trellis/store";
import type { StackElement } from "@/lib/trellis/types";

export function StackCard({ element }: { element: StackElement }) {
  const { tier, dismissStackElement, completeStackElement } = useTrellis();
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState(false);
  const variant = element.variants[tier];

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="relative flex flex-col justify-between rounded-3xl border border-black/[0.06] bg-white/80 p-6 shadow-sm backdrop-blur-xl"
    >
      <div>
        {/* Card Header */}
        <div className="flex items-start justify-between gap-3">
          <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-[#9A9A9A] font-medium">
            {element.type}
          </span>
          <div className="flex items-center gap-2">
            {element.source && (
              <span className="rounded-full border border-black/[0.06] bg-[#FAFAF8] px-2.5 py-0.5 font-mono text-[10px] tracking-wide text-[#666666]">
                {element.source}
              </span>
            )}
            <button
              onClick={() => {
                dismissStackElement(element.id);
                toast("Dismissed — evidence logged", {
                  description: "Gap score adjusted for the missing marker.",
                });
              }}
              aria-label="Dismiss"
              className="text-[#9A9A9A] transition-colors hover:text-[#111111]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Card Body */}
        <AnimatePresence mode="wait">
          <motion.div
            key={tier}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="mt-4"
          >
            <h3 className="text-lg leading-snug font-medium text-[#111111]">
              {variant.title}
            </h3>
            <p className="mt-2 text-xs leading-relaxed text-[#666666]">
              {variant.description}
            </p>
            <p className="num mt-3 text-[10.5px] font-mono text-[#D97706] font-medium">
              ESTIMATED DURATION: {variant.duration}
            </p>
          </motion.div>
        </AnimatePresence>

        {/* Toggle Details */}
        <button
          onClick={() => setOpen((o) => !o)}
          className="mt-5 flex items-center gap-1.5 font-mono text-[11px] text-[#666666] transition-colors hover:text-[#111111]"
        >
          <span>Why this? Why now?</span>
          <ChevronDown
            className={`h-3.5 w-3.5 transition-transform duration-200 ${
              open ? "rotate-180 text-[#111111]" : ""
            }`}
          />
        </button>

        <AnimatePresence initial={false}>
          {open && (
            <motion.dl
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className="overflow-hidden text-xs font-mono"
            >
              <div className="mt-4 space-y-3 border-t border-black/[0.05] pt-4">
                {[
                  ["WHY THIS", element.why],
                  ["WHY NOW", element.whyNow],
                  ["CLOSING THE GAP", element.howItCloses],
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-[10px] text-[#9A9A9A] uppercase tracking-[0.16em] font-medium">
                      {k}
                    </dt>
                    <dd className="mt-1 leading-relaxed text-[#666666] font-sans text-xs">
                      {v}
                    </dd>
                  </div>
                ))}
              </div>
            </motion.dl>
          )}
        </AnimatePresence>
      </div>

      {/* Action Footer */}
      <div className="mt-6 pt-4 border-t border-black/[0.04] flex items-center justify-between">
        <button
          disabled={done}
          onClick={() => {
            setDone(true);
            completeStackElement(element.id);
            toast("Gap score updated", { description: "A lattice strut is filling in." });
          }}
          className="rounded-full bg-[#111111] px-5 py-2.5 text-xs font-medium text-[#FCFCFA] transition-all hover:bg-[#D97706] disabled:opacity-50"
        >
          {done ? "✓ Logged" : element.action}
        </button>

        <span className="font-mono text-[10px] text-[#9A9A9A]">
          {done ? "ACTIVE" : "PENDING"}
        </span>
      </div>
    </motion.article>
  );
}
