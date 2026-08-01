import { useUser } from "@clerk/react";
import { CapacitySlider } from "@/components/trellis/CapacitySlider";
import { StackCard } from "@/components/trellis/StackCard";
import { Lattice } from "@/components/trellis/Lattice";
import { GapBreakdownSheet } from "@/components/trellis/GapBreakdownSheet";
import { StoryTrajectoryChart } from "@/components/trellis/StoryTrajectoryChart";
import { useTrellis } from "@/lib/trellis/store";
import { mock } from "@/lib/trellis/mockApi";
import { AnimatePresence, motion } from "motion/react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/trellis/AppShell";
import { RequireAuth } from "@/authentication";
import { ArrowUpRight, Zap } from "lucide-react";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Identity Dashboard — Trellis" },
      {
        name: "description",
        content:
          "Identity Gap score, lattice, bottleneck, capacity slider, and today's Identity Stack.",
      },
      { property: "og:title", content: "Identity Dashboard — Trellis" },
    ],
  }),
  component: DashboardPage,
});

const ease = [0.16, 1, 0.3, 1] as const;

function DashboardPage() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}

function Dashboard() {
  const { user } = useUser();
  const { gap, stack, declaredSelf, events, now, struts, pulsedStruts, capacity, tier } =
    useTrellis();
  const [sheetOpen, setSheetOpen] = useState(false);
  const bottleneck = mock.currentBottleneck;
  const firstName = user?.firstName || user?.fullName || "you";

  const createPts = Math.round(gap.createRatio * 100);
  const consumePts = Math.round(gap.consumeRatio * 100);
  const ratio = gap.createRatio / Math.max(0.01, gap.consumeRatio + gap.driftRatio);

  return (
    <AppShell title="Dashboard">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease }}
        className="mx-auto max-w-5xl space-y-8 pb-24"
      >
        <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="label-eyebrow text-signal">Dashboard · F3</p>
            <h1 className="mt-2 font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.12]">
              Am I becoming the person
              <br />I said I wanted to become?
            </h1>
            <p className="mt-3 text-sm text-muted-foreground max-w-md">
              Welcome, {firstName}. Gap recomputes on every evidence event for your account.
            </p>
          </div>
          <button
            onClick={() => setSheetOpen(true)}
            className="group shrink-0 rounded-3xl border border-border bg-card px-6 py-5 text-left shadow-[0_8px_32px_rgba(17,17,17,0.03)] hover:border-signal/40 transition-colors"
          >
            <p className="label-eyebrow">Identity Gap</p>
            <p className="num mt-1 text-5xl font-medium tracking-tight text-foreground">
              {gap.score}
            </p>
            <p className="mt-1 font-mono text-[11px] text-muted-foreground flex items-center gap-1">
              Alignment {gap.alignment}
              <ArrowUpRight className="h-3 w-3 opacity-50 group-hover:opacity-100" />
            </p>
          </button>
        </header>

        {/* Subtle Mentor Unlock Progress Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-border/80 bg-card/80 px-5 py-3.5 font-mono text-xs shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-signal/15 text-signal font-bold">
              🎓
            </span>
            <div>
              <span className="font-semibold text-foreground">Mentor Readiness Progress: </span>
              <span className="text-signal font-bold">78% Unlocked</span>
              <span className="text-muted-foreground ml-2 hidden sm:inline">
                (Maintain 80%+ alignment for 7 more days to unlock Mentor status)
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-2 w-28 rounded-full bg-secondary overflow-hidden">
              <div className="h-full rounded-full bg-signal w-[78%]" />
            </div>
            <Link
              to="/mentors"
              className="text-[11px] font-semibold text-signal hover:text-foreground underline underline-offset-2 transition-colors shrink-0"
            >
              Explore Guides &rarr;
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Create", value: `${createPts}%`, sub: "action / ship" },
            { label: "Consume", value: `${consumePts}%`, sub: "passive learn" },
            {
              label: "Create:Consume",
              value: ratio.toFixed(2),
              sub: "<1 = consume wins",
            },
            { label: "Bottleneck", value: bottleneck.name, sub: bottleneck.confidence },
          ].map((m) => (
            <div key={m.label} className="rounded-2xl border border-border bg-card p-4">
              <p className="label-eyebrow">{m.label}</p>
              <p className="num mt-1 text-xl font-medium text-foreground truncate">{m.value}</p>
              <p className="font-mono text-[9px] text-muted-foreground mt-0.5">{m.sub}</p>
            </div>
          ))}
        </div>

        <section className="rounded-3xl border border-border bg-card p-6 sm:p-8">
          <div className="flex items-start justify-between gap-4 mb-5">
            <div>
              <p className="label-eyebrow">Identity lattice</p>
              <h2 className="mt-1 text-lg font-medium">Marker struts · filled = evidence</h2>
            </div>
            <button
              onClick={() => setSheetOpen(true)}
              className="font-mono text-[10px] text-muted-foreground hover:text-foreground underline underline-offset-2"
            >
              Full arithmetic
            </button>
          </div>
          <Lattice struts={struts} pulsed={pulsedStruts} />
          <p className="mt-3 font-mono text-[10px] text-muted-foreground">
            Amber = recent evidence · open Gap score for formula breakdown
          </p>
        </section>

        <div className="grid gap-5 lg:grid-cols-12">
          <section className="lg:col-span-7 rounded-3xl border border-border bg-card p-6 sm:p-8">
            <p className="label-eyebrow mb-1">21-day trajectory</p>
            <h2 className="text-lg font-medium mb-5">Declared vs Revealed</h2>
            <StoryTrajectoryChart
              events={events}
              declaredSelf={declaredSelf}
              now={now}
            />
          </section>
          <div className="lg:col-span-5 space-y-5">
            <CapacitySlider variant="expanded" />
            <section className="rounded-3xl border border-border bg-card p-6">
              <p className="label-eyebrow mb-2">Potential Bottleneck</p>
              <h2 className="text-lg font-medium">{bottleneck.name}</h2>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {bottleneck.diagnosis}
              </p>
              <ul className="mt-4 space-y-2">
                {(bottleneck.evidence ?? []).map((e) => (
                  <li
                    key={e}
                    className="flex items-start gap-2 text-xs text-muted-foreground font-mono"
                  >
                    <Zap className="h-3 w-3 text-signal shrink-0 mt-0.5" strokeWidth={1.5} />
                    {e}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>

        <section>
          <div className="flex items-end justify-between gap-4 mb-5">
            <div>
              <p className="label-eyebrow text-signal">Today&apos;s Identity Stack</p>
              <h2 className="mt-1 font-display text-2xl font-medium tracking-tight">
                Sized to {tier} capacity ({capacity}%)
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Drag capacity — variants swap locally in under 100ms. Why this / Why now /
                How it closes on every card.
              </p>
            </div>
            <Link
              to="/feed"
              className="hidden sm:inline-flex font-mono text-[11px] text-signal hover:underline"
            >
              Open Growth Feed →
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence mode="popLayout">
              {stack.map((el) => (
                <StackCard key={el.id} element={el} />
              ))}
            </AnimatePresence>
          </div>
          {stack.length === 0 && (
            <p className="rounded-2xl border border-border bg-card p-8 text-center text-sm text-muted-foreground">
              No stack elements — adjust capacity or complete onboarding.
            </p>
          )}
        </section>

        <section className="rounded-3xl border border-border bg-card p-6 sm:p-8 space-y-5">
          <p className="label-eyebrow">Attribute divergence</p>
          {(gap.breakdown ?? []).map((attr) => (
            <div key={attr.attributeId} className="space-y-1.5">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-foreground font-medium">{attr.label}</span>
                <span className="text-muted-foreground">
                  {Math.round(attr.revealed * 100)}% / {Math.round(attr.target * 100)}%
                </span>
              </div>
              <div className="relative h-2 w-full overflow-hidden rounded-full bg-black/[0.05]">
                <div
                  className="absolute top-0 h-full rounded-full bg-black/[0.12]"
                  style={{ width: `${attr.target * 100}%` }}
                />
                <motion.div
                  className="absolute top-0 h-full rounded-full bg-signal"
                  initial={{ width: 0 }}
                  animate={{ width: `${attr.revealed * 100}%` }}
                  transition={{ duration: 0.9, ease }}
                />
              </div>
            </div>
          ))}
        </section>

        <p className="font-mono text-[10px] text-muted-foreground text-center">
          TRELLIS · simulated history labeled · Shift+D opens simulator
        </p>
      </motion.div>

      <GapBreakdownSheet open={sheetOpen} onOpenChange={setSheetOpen} />
    </AppShell>
  );
}
