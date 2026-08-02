import { useUser } from "@clerk/react";
import { GapBreakdownSheet } from "@/components/trellis/GapBreakdownSheet";
import { BottleneckJourneyCard } from "@/components/trellis/BottleneckJourneyCard";
import { useTrellis } from "@/lib/trellis/store";
import { motion } from "motion/react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState, type MouseEvent } from "react";
import { AppShell } from "@/components/trellis/AppShell";
import { RequireAuth } from "@/authentication";
import { VectorSearchBar } from "@/components/VectorSearchBar";
import { ArrowUpRight } from "lucide-react";


export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Identity Dashboard — Trellis" },
      {
        name: "description",
        content:
          "Identity Gap score and bottleneck — see how close you are to who you said you'd become.",
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
  const {
    gap,
    declaredSelf,
    events,
    now,
    bottleneck,
    selectedPersona,
    ledger,
  } = useTrellis();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [gapTilt, setGapTilt] = useState({ x: 0, y: 0 });
  const firstName = user?.firstName || user?.fullName || "you";
  // Dynamic labels from the selected persona
  const personaRoleLabel = selectedPersona.roleLabel;
  const personaBottleneckLabel = selectedPersona.bottleneckLabel;

  const createPts = Math.round(gap.createRatio * 100);
  const consumePts = Math.round(gap.consumeRatio * 100);
  const ratio = gap.createRatio / Math.max(0.01, gap.consumeRatio + gap.driftRatio);
  const gapScore = Math.max(0, Math.min(100, Number(gap.score) || 0));
  const gapRing = 2 * Math.PI * 54; // r=54 in viewBox

  const ledgerStats = useMemo(() => {
    const worked = ledger.filter((e) => e.verdict === "worked").length;
    const failed = ledger.filter((e) => e.verdict === "failed").length;
    const pending = ledger.filter((e) => e.verdict === "pending").length;
    return { worked, failed, pending, total: ledger.length };
  }, [ledger]);

  const onGapMove = (event: MouseEvent<HTMLButtonElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width - 0.5;
    const py = (event.clientY - rect.top) / rect.height - 0.5;
    setGapTilt({ x: -(py * 18), y: px * 18 });
  };

  return (
    <AppShell title="Dashboard">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease }}
        className="mx-auto max-w-5xl space-y-8 pb-24"
      >
        <header className="flex flex-col gap-8 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.12]">
              Am I becoming the person
              <br />I said I wanted to become?
            </h1>
            <p className="mt-3 text-sm text-muted-foreground max-w-md">
              Hey {firstName} — you&apos;re working toward becoming a{" "}
              <span className="text-foreground font-medium">{personaRoleLabel}</span>.
              This page updates as Trellis sees what you actually do each day.
            </p>
          </div>

          {/* Hero Identity Gap — primary score on the platform */}
          <div className="flex flex-col items-center gap-3 sm:items-end">
          <div className="relative mx-auto shrink-0 sm:mx-0 [perspective:900px]">
            <div
              aria-hidden
              className="pointer-events-none absolute inset-x-6 bottom-1 h-8 rounded-[100%] bg-black/25 blur-2xl"
            />
            <motion.button
              type="button"
              onClick={() => setSheetOpen(true)}
              onMouseMove={onGapMove}
              onMouseLeave={() => setGapTilt({ x: 0, y: 0 })}
              animate={{
                rotateX: gapTilt.x,
                rotateY: gapTilt.y,
                z: 24,
              }}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 220, damping: 18, mass: 0.55 }}
              className="group relative flex h-[16.5rem] w-[16.5rem] flex-col items-center justify-center gap-2 rounded-full border border-white/50 bg-[linear-gradient(160deg,#FFFFFF_0%,#F4F4F2_55%,#EDEDEB_100%)] px-8 py-10 text-center shadow-[0_28px_60px_rgba(17,17,17,0.16),0_8px_20px_rgba(17,17,17,0.08),inset_0_1px_0_rgba(255,255,255,0.9)] [transform-style:preserve-3d] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal/50 sm:h-[17.5rem] sm:w-[17.5rem]"
              aria-label={`Identity Gap ${gap.score}. Open details.`}
            >
              <svg
                aria-hidden
                viewBox="0 0 120 120"
                className="pointer-events-none absolute inset-3 h-[calc(100%-1.5rem)] w-[calc(100%-1.5rem)] -rotate-90"
              >
                <circle
                  cx="60"
                  cy="60"
                  r="54"
                  fill="none"
                  stroke="rgba(17,17,17,0.06)"
                  strokeWidth="4"
                />
                <motion.circle
                  cx="60"
                  cy="60"
                  r="54"
                  fill="none"
                  stroke="var(--signal)"
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeDasharray={gapRing}
                  initial={{ strokeDashoffset: gapRing }}
                  animate={{ strokeDashoffset: gapRing * (1 - gapScore / 100) }}
                  transition={{ duration: 1.35, ease }}
                />
              </svg>

              <p className="relative z-10 text-xs font-medium tracking-wide text-signal [transform:translateZ(18px)]">
                Identity Gap
              </p>
              <motion.p
                key={gap.score}
                initial={{ opacity: 0, scale: 0.86, y: 8 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.7, ease }}
                className="relative z-10 num text-7xl font-semibold tracking-tight text-foreground leading-none [transform:translateZ(36px)]"
              >
                {gap.score}
              </motion.p>
              <p className="relative z-10 text-xs text-muted-foreground [transform:translateZ(14px)] group-hover:text-foreground transition-colors">
                Tap to see why
              </p>
            </motion.button>
          </div>
          </div>
        </header>

        <section className="space-y-3">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Path to mentoring others</h2>
            <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
              Trellis looks for steady proof that you live your declared self. Enough evidence
              unlocks the ability to guide others on the same path.
            </p>
          </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-border/60 bg-card/50 px-5 py-4 backdrop-blur-xl transition-all hover:border-border">
          <div className="flex flex-wrap items-center gap-3">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-40" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-signal" />
            </span>
            <span className="text-sm font-medium text-foreground">
              78% toward mentor unlock
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="h-1.5 w-28 rounded-full bg-secondary overflow-hidden">
              <div className="h-full rounded-full bg-signal w-[78%]" />
            </div>
            <Link
              to="/mentors"
              className="inline-flex items-center gap-1 text-sm font-medium text-foreground hover:text-signal transition-colors shrink-0"
            >
              <span>Explore guides</span>
              <ArrowUpRight className="h-3.5 w-3.5 opacity-60" />
            </Link>
          </div>
        </div>
        </section>

        <section className="space-y-3">
          <div>
            <h2 className="text-sm font-semibold text-foreground">How you spent this week</h2>
            <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
              Trellis sorts your activity into making things vs taking things in. This mix
              feeds your Identity Gap.
            </p>
          </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: "Creating",
              value: `${createPts}%`,
              sub: "Building, shipping, or doing real-world reps",
            },
            {
              label: "Consuming",
              value: `${consumePts}%`,
              sub: "Learning or watching without output yet",
            },
            {
              label: "Create vs consume",
              value: ratio.toFixed(2),
              sub: "Above 1.0 means you make more than you take in",
            },
            {
              label: "Main friction",
              value: personaBottleneckLabel,
              sub: `What’s slowing you most right now (${bottleneck.confidence} confidence)`,
            },
          ].map((m) => (
            <div key={m.label} className="rounded-2xl border border-border bg-card p-4">
              <p className="text-xs font-medium text-muted-foreground">{m.label}</p>
              <p className="num mt-1.5 text-xl font-semibold text-foreground truncate">{m.value}</p>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{m.sub}</p>
            </div>
          ))}
        </div>
        </section>

        <section className="space-y-3">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Did Trellis&apos;s nudges help?</h2>
            <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
              When Trellis suggests a small action, it tracks whether your behavior actually
              changed afterward.
            </p>
          </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: "Tracked",
              value: ledgerStats.total,
              tone: "text-foreground",
              sub: "Suggestions Trellis followed up on",
            },
            {
              label: "Helped",
              value: ledgerStats.worked,
              tone: "text-growth",
              sub: "You moved closer to your declared self",
            },
            {
              label: "Didn't land",
              value: ledgerStats.failed,
              tone: "text-failure",
              sub: "No meaningful change after the nudge",
            },
            {
              label: "Still measuring",
              value: ledgerStats.pending,
              tone: "text-muted-foreground",
              sub: "Waiting to see if behavior shifted",
            },
          ].map((s) => (
            <div key={s.label} className="rounded-2xl border border-border bg-card p-4">
              <p className="text-xs font-medium text-muted-foreground">{s.label}</p>
              <p className={`num mt-1.5 text-2xl font-semibold ${s.tone}`}>{s.value}</p>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{s.sub}</p>
            </div>
          ))}
        </div>
        </section>

        <BottleneckJourneyCard
          bottleneck={bottleneck}
          events={events}
          declaredSelf={declaredSelf}
          now={now}
          personaBottleneckLabel={personaBottleneckLabel}
        />

        <VectorSearchBar />

        <section className="rounded-3xl border border-border bg-card p-6 sm:p-8 space-y-5">
          <div>
            <h2 className="text-sm font-semibold text-foreground">
              Traits you declared vs what you showed
            </h2>
            <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
              In the Mirror Interview you named who you want to become. These bars show how
              much your recent behavior supports each trait.
            </p>
          </div>
          {(gap.breakdown ?? []).map((attr) => {
            const targetPts = Math.max(attr.target, 0.01);
            const revealedPts = Math.max(attr.revealed, 0);
            const progressPct = Math.min(100, (revealedPts / targetPts) * 100);
            return (
              <div key={attr.attributeId} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-foreground">{attr.label}</span>
                  <span className="text-muted-foreground">
                    {Math.round(progressPct)}% backed by your behavior
                  </span>
                </div>
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-black/[0.05]">
                  <motion.div
                    className="absolute top-0 h-full rounded-full bg-signal"
                    initial={{ width: 0 }}
                    animate={{ width: `${progressPct}%` }}
                    transition={{ duration: 0.9, ease }}
                  />
                </div>
              </div>
            );
          })}
        </section>

      </motion.div>

      <GapBreakdownSheet open={sheetOpen} onOpenChange={setSheetOpen} />
    </AppShell>
  );
}
