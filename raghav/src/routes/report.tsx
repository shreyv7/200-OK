import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowDownRight, Check, X } from "lucide-react";
import { toast } from "sonner";
import { RequireAuth } from "@/authentication";
import { AppShell } from "@/components/trellis/AppShell";
import {
  acceptEvolution,
  createAgentRun,
  rejectEvolution,
} from "@/lib/api/endpoints";
import type { ApiEvolutionProposal, ApiWeeklyReport } from "@/lib/api/types";
import { useTrellis } from "@/lib/trellis/store";

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
  component: ReportPage,
});

const ease = [0.16, 1, 0.3, 1] as const;

function ReportPage() {
  return (
    <RequireAuth>
      <Report />
    </RequireAuth>
  );
}

function Report() {
  const { gap, acceptIdentityEvolution, refreshLiveData } = useTrellis();
  const [generating, setGenerating] = useState(false);
  const [report, setReport] = useState<ApiWeeklyReport | null>(null);
  const [proposal, setProposal] = useState<ApiEvolutionProposal | null>(null);
  const [proposalChoice, setProposalChoice] = useState<"accepted" | "kept" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pct = (n: number) => `${Math.round(n * 100)}%`;

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const weekly = await createAgentRun("weekly_report");
      setReport(weekly.weeklyReport ?? null);
      try {
        const evo = await createAgentRun("evolution");
        setProposal(evo.evolutionProposal ?? null);
      } catch {
        setProposal(null);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Could not generate report. Complete onboarding first.";
      setError(message);
      toast.error("Report generation failed", { description: message });
    } finally {
      setGenerating(false);
    }
  };

  const proposedLabel =
    proposal?.proposedChanges.map((c) => c.attributeLabel).join(" · ") ||
    "Updated Declared Self";

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

        {!report && (
          <div className="rounded-3xl border border-border bg-card p-8 text-center space-y-5">
            <p className="text-sm text-muted-foreground">
              Generate from the current 21-day evidence window and Declared Self.
            </p>
            <button
              onClick={() => void handleGenerate()}
              disabled={generating}
              className="inline-flex items-center gap-2 rounded-full bg-foreground px-7 py-3.5 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60 transition-colors"
            >
              {generating ? "Reading evidence…" : "Generate this week's report"}
            </button>
            {error && (
              <p className="text-sm text-failure">{error}</p>
            )}
          </div>
        )}

        <AnimatePresence>
          {report && (
            <motion.article
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease }}
              className="lattice-texture rounded-3xl border border-border bg-card p-8 sm:p-10 relative overflow-hidden"
            >
              <div className="relative">
                <div className="flex items-baseline justify-between gap-4">
                  <p className="label-eyebrow">Becoming report</p>
                  <p className="num font-mono text-xs text-muted-foreground">
                    Gap {report.gapScoreEnd}
                  </p>
                </div>

                <h2 className="mt-6 font-display text-2xl sm:text-3xl leading-tight font-medium tracking-tight">
                  {report.highlights[0] ?? "This week&apos;s identity movement"}
                </h2>
                <p className="mt-6 leading-relaxed text-muted-foreground whitespace-pre-wrap">
                  {report.narrative}
                </p>

                {report.highlights.length > 1 && (
                  <ul className="mt-6 space-y-2">
                    {report.highlights.slice(1).map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <span className="mt-1.5 h-1 w-1 rounded-full bg-signal shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                )}

                <dl className="mt-8 grid grid-cols-2 gap-5 border-t border-border pt-6 sm:grid-cols-4">
                  <Stat
                    label="Gap trend"
                    value={`${report.gapDelta > 0 ? "+" : ""}${report.gapDelta}`}
                    icon={report.gapDelta < 0}
                  />
                  <Stat
                    label="Create : Consume"
                    value={`${pct(gap.createRatio)} : ${pct(gap.consumeRatio)}`}
                  />
                  <Stat label="Start gap" value={String(report.gapScoreStart ?? "—")} />
                  <Stat label="End gap" value={String(report.gapScoreEnd)} />
                </dl>

                <p className="mt-6 font-mono text-[10px] text-muted-foreground">
                  {report.simulated
                    ? "Narrative may include simulated framing · generated via Gemini"
                    : "Narrative from live evidence · generated via Gemini"}
                </p>
              </div>
            </motion.article>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {report && proposal && (
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
                {proposal.narrative}
              </p>

              <div>
                <p className="label-eyebrow mb-2">Proposed changes</p>
                <ul className="space-y-2">
                  {proposal.proposedChanges.map((change) => (
                    <li
                      key={`${change.action}-${change.attributeId}`}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <span className="mt-1.5 h-1 w-1 rounded-full bg-signal shrink-0" />
                      {change.action} · {change.attributeLabel} — {change.reason}
                    </li>
                  ))}
                </ul>
              </div>

              <p className="font-mono text-[11px] text-muted-foreground border-t border-border pt-4">
                Proposed label:{" "}
                <span className="text-foreground font-medium">{proposedLabel}</span>
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
                      Declared self updated to &ldquo;{proposedLabel}&rdquo;. Dashboard now
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
                      void acceptEvolution(proposal.proposalId)
                        .then(() => {
                          acceptIdentityEvolution();
                          setProposalChoice("accepted");
                          return refreshLiveData();
                        })
                        .catch((err) => {
                          toast.error("Could not accept evolution", {
                            description:
                              err instanceof Error ? err.message : "Try again shortly.",
                          });
                        });
                    }}
                    className="rounded-full bg-foreground px-6 py-3.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors"
                  >
                    Accept update
                  </button>
                  <button
                    onClick={() => {
                      void rejectEvolution(proposal.proposalId)
                        .then(() => setProposalChoice("kept"))
                        .catch(() => setProposalChoice("kept"));
                    }}
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
