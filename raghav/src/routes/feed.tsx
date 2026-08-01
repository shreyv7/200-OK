import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  Check,
  Clock,
  Gauge,
  Shield,
  Sparkles,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { RequireAuth } from "@/authentication";
import { AppShell } from "@/components/trellis/AppShell";
import { useTrellis } from "@/lib/trellis/store";
import { mock } from "@/lib/trellis/mockApi";
import {
  evaluateMomentDetector,
  MIN_LOW_VALUE_RATIO,
  MIN_SCROLL_COUNT,
  type DetectorInputs,
  type DetectorState,
  type ScrollRecord,
} from "@/lib/trellis/momentDetector";
import type { InterventionCard } from "@/lib/trellis/types";

export const Route = createFileRoute("/feed")({
  head: () => ({
    meta: [
      { title: "Growth Feed — Trellis" },
      {
        name: "description",
        content:
          "An owned scroll surface where Trellis detects drift and morphs the next card into a growth intervention.",
      },
      { property: "og:title", content: "Growth Feed — Trellis" },
    ],
  }),
  component: GrowthFeedPage,
});

function GrowthFeedPage() {
  return (
    <RequireAuth>
      <GrowthFeed />
    </RequireAuth>
  );
}

const ease = [0.16, 1, 0.3, 1] as const;

type FeedItem =
  | {
      id: string;
      mode: "scroll";
      kind: "low_value" | "neutral";
      headline: string;
      tag: string;
    }
  | {
      id: string;
      mode: "intervention";
      card: InterventionCard;
      trigger: DetectorInputs;
      evaluatedInMs: number;
    };

function GrowthFeed() {
  const {
    acceptIntervention,
    snoozeIntervention,
    dismissIntervention,
    unlearned,
    nextIntervention,
    logDrift,
    gap,
    capacity,
  } = useTrellis();

  const [items, setItems] = useState<FeedItem[]>(() =>
    mock.feedCards.map((c) => ({
      id: c.id,
      mode: "scroll" as const,
      kind: c.kind,
      headline: c.headline,
      tag: c.tag,
    })),
  );
  const [scrolls, setScrolls] = useState<ScrollRecord[]>([]);
  const [lastFiredAt, setLastFiredAt] = useState<number | null>(null);
  const [detector, setDetector] = useState(() =>
    evaluateMomentDetector([], Date.now(), null),
  );
  const [resolvedIds, setResolvedIds] = useState<string[]>([]);
  const firedOnceRef = useRef(false);
  const [scrollRoot, setScrollRoot] = useState<HTMLDivElement | null>(null);

  const scrollStats = useMemo(() => {
    const low = scrolls.filter((s) => s.kind === "low_value").length;
    return {
      total: scrolls.length,
      low,
      ratio: scrolls.length === 0 ? 0 : low / scrolls.length,
    };
  }, [scrolls]);

  const recompute = useCallback(
    (nextScrolls: ScrollRecord[], firedAt: number | null) => {
      const result = evaluateMomentDetector(nextScrolls, Date.now(), firedAt);
      setDetector(result);
      return result;
    },
    [],
  );

  const morphNextCard = useCallback(
    (result: ReturnType<typeof evaluateMomentDetector>) => {
      const card = nextIntervention;
      setItems((prev) => {
        const idx = prev.findIndex(
          (it) => it.mode === "scroll" && !resolvedIds.includes(it.id),
        );
        if (idx === -1) return prev;
        const next = [...prev];
        next[idx] = {
          id: `iv_${card.id}_${Date.now()}`,
          mode: "intervention",
          card,
          trigger: result.inputs,
          evaluatedInMs: result.evaluatedInMs,
        };
        return next;
      });
      toast("Moment Detector fired", {
        description: `scroll=${result.inputs.scrollCount} · low-value ${(result.inputs.lowValueRatio * 100).toFixed(0)}% · ${result.evaluatedInMs.toFixed(1)}ms`,
      });
    },
    [nextIntervention, resolvedIds],
  );

  // When System Unlearning swaps lenses, remorph any pending intervention card
  useEffect(() => {
    if (!unlearned) return;
    setItems((prev) =>
      prev.map((it) =>
        it.mode === "intervention" && !resolvedIds.includes(it.id)
          ? { ...it, card: nextIntervention }
          : it,
      ),
    );
  }, [unlearned, nextIntervention, resolvedIds]);

  const onCardVisible = useCallback(
    (item: Extract<FeedItem, { mode: "scroll" }>) => {
      const record: ScrollRecord = { at: Date.now(), kind: item.kind };
      const nextScrolls = [...scrolls, record].slice(-40);
      setScrolls(nextScrolls);

      // Only low-value scrolls write drift evidence (PRD F4)
      if (item.kind === "low_value") {
        logDrift(`Feed scroll — ${item.tag}: ${item.headline}`);
      }

      const result = recompute(nextScrolls, lastFiredAt);
      if (result.fired && !firedOnceRef.current) {
        firedOnceRef.current = true;
        const now = Date.now();
        setLastFiredAt(now);
        morphNextCard(result);
        setTimeout(() => {
          firedOnceRef.current = false;
        }, 10 * 60_000);
      }
    },
    [scrolls, lastFiredAt, logDrift, recompute, morphNextCard],
  );

  const resolveIntervention = (
    id: string,
    action: "accept" | "snooze" | "dismiss",
    card: InterventionCard,
  ) => {
    setResolvedIds((prev) => [...prev, id]);
    if (action === "accept") {
      acceptIntervention(card);
      toast.success("Gap score updated", {
        description: "Intervention accepted — lattice strut filling in.",
      });
    } else if (action === "snooze") {
      snoozeIntervention(card);
      toast("Snoozed", { description: "Logged as pending in the Trust Ledger." });
    } else {
      const crossed = dismissIntervention(card);
      if (crossed) {
        toast.error("Hypothesis failed", {
          description: "System Unlearning: Media −40% · switched to Micro-Action.",
        });
      } else {
        toast("Dismissed", { description: "Negative evidence logged." });
      }
    }
  };

  return (
    <AppShell title="Growth Feed">
      <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-12 pb-24">
        {/* Left: context panel */}
        <aside className="lg:col-span-5 space-y-6">
          <header className="space-y-3">
            <p className="label-eyebrow text-signal">The Catch · F4</p>
            <h1 className="font-display text-3xl sm:text-4xl font-medium tracking-tight text-foreground leading-[1.1]">
              Scroll until the feed fights back.
            </h1>
            <p className="text-sm leading-relaxed text-muted-foreground max-w-md">
              This is an owned mock feed — not Instagram. Keep scrolling low-value
              cards during a focus window. On the fifth qualifying scroll, a
              deterministic Moment Detector morphs the next card into an intervention.
            </p>
          </header>

          <DetectorPanel detector={detector} stats={scrollStats} />

          <div className="grid grid-cols-2 gap-3">
            <MiniStat
              icon={Gauge}
              label="Capacity"
              value={`${capacity}%`}
              sub="Guardian sizing"
            />
            <MiniStat
              icon={Sparkles}
              label="Identity Gap"
              value={String(gap.score)}
              sub={`Alignment ${gap.alignment}`}
            />
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 space-y-3">
            <p className="label-eyebrow">How to demo</p>
            <ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
              <li>Scroll five low-value cards in the phone.</li>
              <li>Watch the next card morph into an intervention.</li>
              <li>Dismiss three times to trigger System Unlearning.</li>
              <li>Accept the micro-action — Gap score drops.</li>
            </ol>
            <p className="font-mono text-[10px] text-muted-foreground pt-2 border-t border-border">
              Press <span className="text-signal">Shift+D</span> for the simulator panel.
            </p>
          </div>
        </aside>

        {/* Right: phone frame */}
        <div className="lg:col-span-7 flex justify-center lg:justify-end">
          <div className="relative w-full max-w-[380px]">
            {/* Phone chrome */}
            <div className="rounded-[2.4rem] border border-border bg-[#1a1a1a] p-3 shadow-[0_24px_80px_rgba(17,17,17,0.18)]">
              <div className="rounded-[1.9rem] overflow-hidden bg-white relative">
                {/* Status bar */}
                <div className="flex items-center justify-between px-5 pt-3 pb-2">
                  <span className="font-mono text-[10px] text-foreground">9:41</span>
                  <div className="h-5 w-24 rounded-full bg-foreground/90" />
                  <span className="font-mono text-[10px] text-foreground">100%</span>
                </div>

                {/* App header */}
                <div className="px-4 pb-3 border-b border-border/60">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                        Owned surface
                      </p>
                      <p className="text-sm font-medium text-foreground">For You</p>
                    </div>
                    <DetectorBadge state={detector.state} />
                  </div>
                </div>

                {/* Scrollable feed */}
                <div
                  ref={setScrollRoot}
                  className="h-[560px] overflow-y-auto overscroll-contain px-3 py-3 space-y-3 scroll-smooth"
                  style={{ scrollbarWidth: "thin" }}
                >
                  {items.map((item) =>
                    item.mode === "scroll" ? (
                      <ScrollCard
                        key={item.id}
                        item={item}
                        root={scrollRoot}
                        onVisible={() => onCardVisible(item)}
                      />
                    ) : (
                      <InterventionMorphCard
                        key={item.id}
                        item={item}
                        resolved={resolvedIds.includes(item.id)}
                        onAccept={() => resolveIntervention(item.id, "accept", item.card)}
                        onSnooze={() => resolveIntervention(item.id, "snooze", item.card)}
                        onDismiss={() => resolveIntervention(item.id, "dismiss", item.card)}
                      />
                    ),
                  )}
                  <p className="py-6 text-center font-mono text-[10px] text-muted-foreground">
                    End of demo feed · simulated surface
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function DetectorBadge({ state }: { state: DetectorState }) {
  const map: Record<DetectorState, { label: string; className: string }> = {
    monitoring: { label: "Monitoring", className: "text-muted-foreground border-border" },
    armed: { label: "Armed", className: "text-signal border-signal/40 bg-signal/5" },
    fired: { label: "Fired", className: "text-growth border-growth/40 bg-growth/5" },
    cooldown: { label: "Cooldown", className: "text-muted-foreground border-border" },
  };
  const m = map[state];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.14em] ${m.className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {m.label}
    </span>
  );
}

function DetectorPanel({
  detector,
  stats,
}: {
  detector: ReturnType<typeof evaluateMomentDetector>;
  stats: { total: number; low: number; ratio: number };
}) {
  const { inputs } = detector;
  const rows = [
    {
      label: "scroll_count",
      value: String(inputs.scrollCount),
      ok: inputs.scrollCount >= MIN_SCROLL_COUNT,
      need: `≥ ${MIN_SCROLL_COUNT}`,
    },
    {
      label: "low_value_ratio",
      value: `${(inputs.lowValueRatio * 100).toFixed(0)}%`,
      ok: inputs.lowValueRatio > MIN_LOW_VALUE_RATIO,
      need: `> ${(MIN_LOW_VALUE_RATIO * 100).toFixed(0)}%`,
    },
    {
      label: "focus_window",
      value: inputs.inFocusWindow ? "true" : "false",
      ok: inputs.inFocusWindow,
      need: "declared period",
    },
    {
      label: "eval_latency",
      value: `${detector.evaluatedInMs.toFixed(2)}ms`,
      ok: detector.evaluatedInMs < 50,
      need: "< 50ms",
    },
  ];

  return (
    <div className="rounded-2xl border border-border bg-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-3.5 w-3.5 text-signal" strokeWidth={1.5} />
          <p className="label-eyebrow">Moment Detector</p>
        </div>
        <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-[0.14em]">
          Deterministic · no LLM
        </span>
      </div>

      <div className="space-y-2">
        {rows.map((r) => (
          <div
            key={r.label}
            className="flex items-center justify-between rounded-xl bg-secondary/80 px-3.5 py-2.5 font-mono text-[11px]"
          >
            <span className="text-muted-foreground">{r.label}</span>
            <div className="flex items-center gap-3">
              <span className="text-[10px] text-muted-foreground/70">{r.need}</span>
              <span className={r.ok ? "text-growth font-medium" : "text-foreground"}>
                {r.value}
              </span>
            </div>
          </div>
        ))}
      </div>

      <p className="font-mono text-[10px] text-muted-foreground">
        Session: {stats.total} scrolls · {stats.low} low-value ·{" "}
        {(stats.ratio * 100).toFixed(0)}% ratio
      </p>
    </div>
  );
}

function MiniStat({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Gauge;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center justify-between text-muted-foreground mb-2">
        <span className="label-eyebrow">{label}</span>
        <Icon className="h-3.5 w-3.5 text-signal" strokeWidth={1.5} />
      </div>
      <p className="num text-xl font-medium text-foreground">{value}</p>
      <p className="font-mono text-[9px] text-muted-foreground mt-0.5">{sub}</p>
    </div>
  );
}

function ScrollCard({
  item,
  root,
  onVisible,
}: {
  item: Extract<FeedItem, { mode: "scroll" }>;
  root: HTMLElement | null;
  onVisible: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || !root) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting && !seen.current) {
          seen.current = true;
          onVisible();
        }
      },
      { root, threshold: 0.7, rootMargin: "0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [onVisible, root]);

  const isLow = item.kind === "low_value";

  return (
    <div
      ref={ref}
      className={`rounded-2xl border p-4 ${
        isLow ? "border-border bg-white" : "border-border/60 bg-[#F7F7F5]"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <span
          className={`font-mono text-[9px] uppercase tracking-[0.16em] px-2 py-0.5 rounded-full border ${
            isLow
              ? "text-[#B45309] border-[#B45309]/25 bg-[#B45309]/5"
              : "text-muted-foreground border-border"
          }`}
        >
          {item.tag}
        </span>
        <span className="font-mono text-[9px] text-muted-foreground">
          {isLow ? "low-value" : "neutral"}
        </span>
      </div>
      <p className="text-[15px] font-medium leading-snug text-foreground">
        {item.headline}
      </p>
      <div className="mt-4 h-28 rounded-xl bg-gradient-to-br from-black/[0.04] via-black/[0.02] to-signal/10 relative overflow-hidden">
        <div className="absolute inset-0 lattice-texture opacity-40" />
        <div className="absolute bottom-3 left-3 right-3 flex gap-1.5">
          <div className="h-1.5 flex-1 rounded-full bg-black/10" />
          <div className="h-1.5 w-8 rounded-full bg-black/10" />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4 font-mono text-[10px] text-muted-foreground">
        <span>♥ 2.4k</span>
        <span>💬 184</span>
        <span>↗ Share</span>
      </div>
    </div>
  );
}

function InterventionMorphCard({
  item,
  resolved,
  onAccept,
  onSnooze,
  onDismiss,
}: {
  item: Extract<FeedItem, { mode: "intervention" }>;
  resolved: boolean;
  onAccept: () => void;
  onSnooze: () => void;
  onDismiss: () => void;
}) {
  const { card, trigger, evaluatedInMs } = item;

  return (
    <motion.div
      layout
      initial={{ opacity: 0.4, scale: 0.96, filter: "blur(4px)" }}
      animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
      transition={{ duration: 0.55, ease }}
      className={`rounded-2xl border-2 p-4 ${
        resolved
          ? "border-growth/30 bg-growth/5"
          : "border-signal/50 bg-white shadow-[0_8px_32px_rgba(200,137,43,0.12)]"
      }`}
    >
      <AnimatePresence mode="wait">
        {!resolved ? (
          <motion.div
            key="active"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="inline-flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-[0.16em] text-signal border border-signal/30 bg-signal/5 px-2 py-0.5 rounded-full">
                <Sparkles className="h-3 w-3" strokeWidth={1.5} />
                Intervention · {card.lens}
              </span>
              <span className="font-mono text-[9px] text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {card.duration}
              </span>
            </div>

            <p className="text-[15px] font-medium leading-snug text-foreground">
              {card.action}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground italic">
              “{card.reasoning}”
            </p>

            <div className="mt-3 rounded-xl bg-secondary/80 p-3 font-mono text-[10px] space-y-1">
              <p className="text-muted-foreground uppercase tracking-[0.14em]">
                Why this fired
              </p>
              <p className="text-foreground">
                scroll_count={trigger.scrollCount} · low_value_ratio=
                {(trigger.lowValueRatio * 100).toFixed(0)}% · focus=true ·{" "}
                {evaluatedInMs.toFixed(1)}ms
              </p>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2">
              <button
                onClick={onAccept}
                className="col-span-2 flex items-center justify-center gap-1.5 rounded-xl bg-foreground px-3 py-2.5 text-xs font-medium text-background hover:bg-foreground/90 transition-colors"
              >
                <Check className="h-3.5 w-3.5" strokeWidth={2} />
                Do it
              </button>
              <button
                onClick={onSnooze}
                className="rounded-xl border border-border px-3 py-2.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Snooze
              </button>
            </div>
            <button
              onClick={onDismiss}
              className="mt-2 w-full flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-[11px] text-muted-foreground hover:text-failure transition-colors"
            >
              <X className="h-3 w-3" />
              Dismiss
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="done"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="py-4 text-center"
          >
            <Check className="mx-auto h-5 w-5 text-growth mb-2" strokeWidth={2} />
            <p className="font-mono text-xs text-growth">Logged to Trust Ledger</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
