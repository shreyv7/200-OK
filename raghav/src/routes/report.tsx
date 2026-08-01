import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowDownRight, Check, X } from "lucide-react";
import { AppShell } from "@/components/trellis/AppShell";
import { useTrellis } from "@/lib/trellis/store";
import { mock } from "@/lib/trellis/mockApi";

export const Route = createFileRoute("/report")({
  head: () => ({
    meta: [
      { title: "Weekly Becoming Report — Trellis" },
      {
        name: "description",
        content:
          "A narrative account of the week's identity movement, plus an optional confirmable Identity Evolution proposal.",
      },
      { property: "og:title", content: "Weekly Becoming Report — Trellis" },
    ],
  }),
  component: Report,
});

const ease = [0.16, 1, 0.3, 1] as const;

function Report() {
  const { gap, identityUpdated, acceptIdentityEvolution } = useTrellis();
  const [generated, setGenerated] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [proposalChoice, setProposalChoice] = useState<"accepted" | "kept" | null>(
    identityUpdated ? "accepted" : null,
  );

  const pct = (n: number) => `${Math.round(n * 100)}%`;

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      setGenerated(true);
    }, 1400);
  };

  return (
    <AppShell title="Weekly Report">
      <div className="mx-auto max-w-2xl space-y-8 pb-20">
        <header className="space-y-3">
          <p className="label-eyebrow text-signal">Weekly Becoming · F8</p>
          <h1 className="font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.1]">
            Identity movement, not hours logged.
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground max-w-lg">
            A narrative over this week&apos;s evidence window — plus, when the signals
            support it, a proposal to update who you say you are.
          </p>
        </header>

        {!generated && (
          <div className="rounded-3xl border border-border bg-card p-8 text-center space-y-5">
            <p className="text-sm text-muted-foreground">
              Generate from the current 21-day evidence window and Declared Self.
            </p>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="inline-flex items-center gap-2 rounded-full bg-foreground px-7 py-3.5 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60 transition-colors"
            >
              {generating ? "Reading evidence…" : "Generate this week's report"}
            </button>
            {generating && (
              <p className="font-mono text-[10px] text-muted-foreground animate-pulse">
                Narrative agent · structured over live DB state
              </p>
            )}
          </div>
        )}

        <AnimatePresence>
          {generated && (
            <motion.article
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease }}
              className="lattice-texture rounded-3xl border border-border bg-card p-8 sm:p-10 relative overflow-hidden"
            >
              <div className="relative">
                <div className="flex items-baseline justify-between gap-4">
                  <p className="label-eyebrow">Becoming report · week 3</p>
                  <p className="num font-mono text-xs text-muted-foreground">
                    Gap {gap.score}
                  </p>
                </div>

                <h2 className="mt-6 font-display text-2xl sm:text-3xl leading-tight font-medium tracking-tight">
                  {mock.weeklyNarrative.arc}
                </h2>
                <p className="mt-6 leading-relaxed text-muted-foreground">
                  {mock.weeklyNarrative.body}
                </p>

                <dl className="mt-8 grid grid-cols-2 gap-5 border-t border-border pt-6 sm:grid-cols-4">
                  <Stat label="Gap trend" value="−4" icon />
                  <Stat
                    label="Create : Consume"
                    value={`${pct(gap.createRatio)} : ${pct(gap.consumeRatio)}`}
                  />
                  <Stat label="Consistency" value="4 / 7 days" />
                  <Stat label="Momentum" value="Rising" />
                </dl>

                <p className="mt-6 font-mono text-[10px] text-muted-foreground">
                  Narrative from simulated evidence · labeled mock data
                </p>
              </div>
            </motion.article>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {generated && (
            <motion.section
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.12, ease }}
              className="rounded-3xl border border-border bg-card p-8 space-y-5"
            >
              <div>
                <p className="label-eyebrow text-signal">Identity Evolution · F11</p>
                <h3 className="mt-2 text-xl font-medium tracking-tight">
                  A proposal — never applied silently
                </h3>
              </div>

              <p className="text-base leading-relaxed text-foreground">
                {mock.identityEvolutionProposal.prompt}
              </p>

              <div>
                <p className="label-eyebrow mb-2">Supporting evidence</p>
                <ul className="space-y-2">
                  {mock.identityEvolutionProposal.evidence.map((e) => (
                    <li
                      key={e}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <span className="mt-1.5 h-1 w-1 rounded-full bg-signal shrink-0" />
                      {e}
                    </li>
                  ))}
                </ul>
              </div>

              <p className="font-mono text-[11px] text-muted-foreground border-t border-border pt-4">
                Proposed label:{" "}
                <span className="text-foreground font-medium">
                  {mock.identityEvolutionProposal.proposed}
                </span>
              </p>

              {proposalChoice ? (
                <div
                  className={`rounded-2xl border p-4 text-sm ${
                    proposalChoice === "accepted"
                      ? "border-growth/30 bg-growth/5 text-growth"
                      : "border-border bg-secondary text-muted-foreground"
                  }`}
                >
                  {proposalChoice === "accepted" ? (
                    <span className="flex items-center gap-2">
                      <Check className="h-4 w-4" strokeWidth={2} />
                      Declared self updated to &ldquo;
                      {mock.identityEvolutionProposal.proposed}&rdquo;. Dashboard now
                      measures against it.
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <X className="h-4 w-4" strokeWidth={2} />
                      Kept current identity. Proposal won&apos;t be raised again this
                      cycle.
                    </span>
                  )}
                </div>
              ) : (
                <div className="grid gap-3 border-t border-border pt-5 sm:grid-cols-2">
                  <button
                    onClick={() => {
                      acceptIdentityEvolution();
                      setProposalChoice("accepted");
                    }}
                    className="rounded-full bg-foreground px-6 py-3.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors"
                  >
                    Accept update
                  </button>
                  <button
                    onClick={() => setProposalChoice("kept")}
                    className="rounded-full border border-border px-6 py-3.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Keep current identity
                  </button>
                </div>
              )}
            </motion.section>
          )}
        </AnimatePresence>
      </div>
    </AppShell>
  );
}

function Stat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: boolean;
}) {
  return (
    <div>
      <dt className="label-eyebrow">{label}</dt>
      <dd className="num mt-2 flex items-center gap-1.5 text-lg font-medium">
        {value}
        {icon && <ArrowDownRight className="h-4 w-4 text-growth" strokeWidth={1.5} />}
      </dd>
    </div>
  );
}
