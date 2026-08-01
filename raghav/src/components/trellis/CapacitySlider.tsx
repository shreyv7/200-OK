import { Slider } from "@/components/ui/slider";
import { capacityLabel, capacityTier, useTrellis } from "@/lib/trellis/store";
import { AnimatePresence, motion } from "motion/react";

export function CapacitySlider({ variant = "bar" }: { variant?: "bar" | "expanded" }) {
  const { capacity, setCapacity } = useTrellis();
  const tier = capacityTier(capacity);

  const caption =
    tier === "micro"
      ? "Capacity changed; preserving momentum without adding load."
      : tier === "light"
        ? "Trimmed to what fits the week you're actually having."
        : "Full capacity. The stack is running at its declared weight.";

  if (variant === "bar") {
    return (
      <div className="flex items-center gap-3 font-mono text-xs">
        <span className="text-[#707070] uppercase tracking-[0.18em] text-[10.5px] hidden sm:block font-medium">
          CAPACITY
        </span>
        <Slider
          value={[capacity]}
          onValueChange={(v) => setCapacity(v[0] ?? capacity)}
          max={100}
          step={1}
          className="w-28 sm:w-36"
          aria-label="Capacity"
        />
        <span className="num w-14 font-medium text-foreground">
          {capacityLabel[tier]}
        </span>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-black/[0.06] bg-white/80 p-8 shadow-sm backdrop-blur-xl space-y-5">
      <div className="flex items-baseline justify-between border-b border-black/[0.05] pb-4 font-mono text-[10.5px]">
        <span className="flex items-center gap-2 uppercase tracking-[0.18em] text-[#9A9A9A] font-medium">
          <span className="h-1.5 w-1.5 rounded-full bg-signal" />
          DAILY CAPACITY BUDGET
        </span>
        <span className="num text-2xl font-medium text-foreground">{capacity}%</span>
      </div>

      <Slider
        value={[capacity]}
        onValueChange={(v) => setCapacity(v[0] ?? capacity)}
        max={100}
        step={1}
        className="mt-4"
        aria-label="Capacity"
      />

      <div className="grid grid-cols-3 font-mono text-[10.5px] uppercase tracking-[0.18em] text-muted-foreground">
        {(["micro", "light", "full"] as const).map((t, i) => (
          <span
            key={t}
            className={[
              i === 1 ? "text-center" : i === 2 ? "text-right" : "",
              tier === t ? "text-signal font-semibold" : "",
            ].join(" ")}
          >
            {capacityLabel[t].toUpperCase()}
          </span>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.p
          key={caption}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="font-mono text-xs text-muted-foreground leading-relaxed pt-2 border-t border-border"
        >
          {caption}
        </motion.p>
      </AnimatePresence>
    </div>
  );
}
