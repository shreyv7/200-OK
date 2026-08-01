import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ChevronDown, XCircle, CheckCircle2, Clock, Lightbulb } from "lucide-react";
import { AppShell } from "@/components/trellis/AppShell";
import { useTrellis } from "@/lib/trellis/store";
import type { LedgerEntry, Verdict } from "@/lib/trellis/types";

export const Route = createFileRoute("/ledger")({
  head: () => ({
    meta: [
      { title: "Trust Ledger — Trellis" },
      {
        name: "description",
        content:
          "Every hypothesis Trellis delivered, what it predicted, and whether behaviour confirmed it. Failures are kept, not hidden.",
      },
      { property: "og:title", content: "Trust Ledger — Trellis" },
    ],
  }),
  component: Ledger,
});

const filters = ["All", "Worked", "Failed", "Pending"] as const;

function Ledger() {
  const { ledger, unlearning } = useTrellis();
  const [filter, setFilter] = useState<(typeof filters)[number]>("All");

  const rows = ledger.filter(
    (e) => filter === "All" || e.verdict === filter.toLowerCase(),
  );

  const stats = useMemo(() => {
    const worked = ledger.filter((e) => e.verdict === "worked").length;
    const failed = ledger.filter((e) => e.verdict === "failed").length;
    const pending = ledger.filter((e) => e.verdict === "pending").length;
    return { worked, failed, pending, total: ledger.length };
  }, [ledger]);

  return (
    <AppShell title="Trust Ledger">
      <div className="mx-auto max-w-3xl space-y-8 pb-20">
        <header className="space-y-3">
          <p className="label-eyebrow text-signal">Trust Ledger · F7</p>
          <h1 className="font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.1]">
            Every hypothesis, kept in the open.
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground max-w-xl">
            Nothing is quietly retried. Each intervention carries a verdict — and when
            it fails, the adaptation that followed is written here as System Unlearning.
          </p>
        </header>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total", value: stats.total, tone: "text-foreground" },
            { label: "Worked", value: stats.worked, tone: "text-growth" },
            { label: "Failed", value: stats.failed, tone: "text-failure" },
            { label: "Pending", value: stats.pending, tone: "text-muted-foreground" },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-2xl border border-border bg-card p-4"
            >
              <p className="label-eyebrow">{s.label}</p>
              <p className={`num mt-1 text-2xl font-medium ${s.tone}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Live unlearning banner */}
        <AnimatePresence>
          {unlearning && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-2xl border border-signal/40 bg-signal/5 p-5 space-y-2"
            >
              <div className="flex items-center gap-2 text-signal">
                <XCircle className="h-4 w-4" strokeWidth={1.5} />
                <p className="font-mono text-[11px] uppercase tracking-[0.16em] font-medium">
                  System Unlearning
                </p>
              </div>
              <p className="text-sm text-foreground">
                Failed hypothesis: &ldquo;{unlearning.hypothesis}&rdquo;
              </p>
              <p className="flex items-start gap-2 text-sm text-muted-foreground">
                <Lightbulb className="h-4 w-4 text-signal shrink-0 mt-0.5" strokeWidth={1.5} />
                {unlearning.adaptation}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full border px-4 py-1.5 font-mono text-xs transition-colors ${
                filter === f
                  ? "border-foreground bg-foreground text-background"
                  : "border-border text-muted-foreground hover:text-foreground"
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Entries */}
        <div className="space-y-3">
          {rows.map((entry, i) => (
            <Row key={entry.id} entry={entry} index={i} />
          ))}
          {rows.length === 0 && (
            <p className="rounded-2xl border border-border bg-card p-8 text-center text-sm text-muted-foreground">
              No entries with that verdict.
            </p>
          )}
        </div>
      </div>
    </AppShell>
  );
}

function VerdictIcon({ verdict }: { verdict: Verdict }) {
  if (verdict === "worked")
    return <CheckCircle2 className="h-4 w-4 text-growth" strokeWidth={1.5} />;
  if (verdict === "failed")
    return <XCircle className="h-4 w-4 text-failure" strokeWidth={1.5} />;
  return <Clock className="h-4 w-4 text-muted-foreground" strokeWidth={1.5} />;
}

function Row({ entry, index }: { entry: LedgerEntry; index: number }) {
  const [open, setOpen] = useState(index < 2);

  const verdictStyles: Record<Verdict, string> = {
    worked: "border-growth/30 text-growth bg-growth/5",
    failed: "border-failure/30 text-failure bg-failure/5",
    pending: "border-border text-muted-foreground bg-secondary/50",
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
      className="rounded-2xl border border-border bg-card overflow-hidden"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-5 py-4 text-left"
      >
        <VerdictIcon verdict={entry.verdict} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-foreground">
            {entry.hypothesis}
          </p>
          <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
            {entry.family} ·{" "}
            {new Date(entry.deliveredAt).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.1em] ${verdictStyles[entry.verdict]}`}
        >
          {entry.verdict}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
          strokeWidth={1.5}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <dl className="space-y-3 px-5 pb-5 text-xs border-t border-border pt-4">
              <div>
                <dt className="label-eyebrow">Delivered</dt>
                <dd className="mt-1 text-muted-foreground leading-relaxed">
                  {entry.delivered}
                </dd>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="label-eyebrow">Outcome window</dt>
                  <dd className="num mt-1 text-muted-foreground">
                    {entry.outcomeWindow}
                  </dd>
                </div>
                <div>
                  <dt className="label-eyebrow">Evidence</dt>
                  <dd className="mt-1 text-muted-foreground leading-relaxed">
                    {entry.evidence}
                  </dd>
                </div>
              </div>
              {entry.adaptation && (
                <div className="rounded-xl border border-l-2 border-l-signal border-border bg-signal/5 p-3.5 font-mono text-[11px] leading-relaxed">
                  <span className="text-signal font-medium">System Unlearning · </span>
                  <span className="text-foreground">{entry.adaptation}</span>
                </div>
              )}
            </dl>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}
