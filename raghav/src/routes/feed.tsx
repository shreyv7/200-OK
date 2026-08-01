import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  Check,
  Clock,
  Gauge,
  Maximize2,
  Shield,
  Sparkles,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { RequireAuth } from "@/authentication";
import { AppShell } from "@/components/trellis/AppShell";
import { useTrellis } from "@/lib/trellis/store";
import {
  getGrowthFeed,
  getPreparedFeedIntervention,
  recordFeedEvent,
} from "@/lib/api/endpoints";
import type { ApiFeedItem } from "@/lib/api/types";
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
      data: ApiFeedItem;
    }
  | {
      id: string;
      mode: "intervention";
      card: InterventionCard;
      trigger: DetectorInputs;
      evaluatedInMs: number;
    }
  | {
      id: string;
      mode: "resource";
      resource: ApiFeedItem;
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

  const [items, setItems] = useState<FeedItem[]>([]);
  const [feedStatus, setFeedStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [preparedCard, setPreparedCard] = useState<InterventionCard | null>(null);
  const [scrolls, setScrolls] = useState<ScrollRecord[]>([]);
  const [lastFiredAt, setLastFiredAt] = useState<number | null>(null);
  const [detector, setDetector] = useState(() =>
    evaluateMomentDetector([], Date.now(), null),
  );
  const [resolvedIds, setResolvedIds] = useState<string[]>([]);
  const firedOnceRef = useRef(false);
  const [scrollRoot, setScrollRoot] = useState<HTMLDivElement | null>(null);
  const [phoneFullscreen, setPhoneFullscreen] = useState(false);

  useEffect(() => {
    if (!phoneFullscreen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPhoneFullscreen(false);
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKey);
    };
  }, [phoneFullscreen]);

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

  useEffect(() => {
    let cancelled = false;
    setFeedStatus("loading");
    void Promise.all([getGrowthFeed(), getPreparedFeedIntervention()])
      .then(([feed, prepared]) => {
        if (cancelled) return;
        setItems(
          feed.items.map((item) =>
            item.kind === "resource"
              ? { id: item.id, mode: "resource" as const, resource: item }
              : {
                  id: item.id,
                  mode: "scroll" as const,
                  kind: item.kind,
                  data: item,
                },
          ),
        );
        const action = prepared.stack.elements.find((element) => element.type === "micro_mission")
          ?? prepared.stack.elements[0];
        if (action) {
          setPreparedCard({
            id: action.id,
            lens: action.type === "media" || action.type === "knowledge" ? "Media" : "Micro-Action",
            action: action.title,
            reasoning: action.explanation.whyNow,
            duration: "A focused next step",
            hypothesisId: prepared.stack.hypothesisId,
            hypothesisFamily: action.type,
          });
        }
        setFeedStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setFeedStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const morphNextCard = useCallback(
    (result: ReturnType<typeof evaluateMomentDetector>) => {
      const card = preparedCard ?? nextIntervention;
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
    [nextIntervention, preparedCard, resolvedIds],
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
        logDrift(`Feed scroll — ${item.data.tag}: ${item.data.title}`);
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
      void acceptIntervention(card).then(() => {
        toast.success("Gap score updated", {
          description: "Intervention accepted — logged to Trust Ledger.",
        });
      });
    } else if (action === "snooze") {
      void snoozeIntervention(card).then(() => {
        toast("Snoozed", { description: "Logged as pending in the Trust Ledger." });
      });
    } else {
      void dismissIntervention(card).then(async (crossed) => {
        if (crossed) {
          toast.error("Hypothesis failed", {
            description: "System Unlearning: failed lens −40% · switched to Micro-Action.",
          });
          try {
            const prepared = await getPreparedFeedIntervention();
            const action =
              prepared.stack.elements.find((element) => element.type === "micro_mission") ??
              prepared.stack.elements[0];
            if (action) {
              setPreparedCard({
                id: action.id,
                lens:
                  action.type === "media" || action.type === "knowledge"
                    ? "Media"
                    : "Micro-Action",
                action: action.title,
                reasoning: action.explanation.whyNow,
                duration: "A focused next step",
                hypothesisId: prepared.stack.hypothesisId,
                hypothesisFamily: action.type,
              });
            }
          } catch {
            /* keep local micro-action fallback */
          }
        } else {
          toast("Dismissed", { description: "Negative evidence logged to Trust Ledger." });
        }
      });
    }
  };

  return (
    <AppShell title="Growth Feed" fitViewport>
      <div className="mx-auto grid h-full min-h-0 w-full max-w-6xl grid-cols-1 gap-4 overflow-hidden lg:grid-cols-12 lg:gap-6">
        {/* Left: context panel */}
        <aside className="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto overscroll-contain lg:col-span-5 lg:overflow-hidden">
          <header className="shrink-0 space-y-1.5">
            <div className="flex items-center justify-between gap-3">
              <p className="label-eyebrow text-signal">The Catch · F4</p>
              <button
                type="button"
                onClick={() => setPhoneFullscreen(true)}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.14em] text-foreground transition-colors hover:border-signal/40 hover:text-signal lg:hidden"
              >
                <Maximize2 className="h-3 w-3" />
                Phone
              </button>
            </div>
            <h1 className="font-display text-2xl font-medium tracking-tight text-foreground leading-[1.15] xl:text-[1.85rem]">
              Scroll until the feed fights back.
            </h1>
            <p className="text-xs leading-relaxed text-muted-foreground max-w-md line-clamp-2">
              Live YouTube and Tavily on an owned surface. When drift crosses the
              thresholds below, Trellis morphs the next card — and shows why.
            </p>
          </header>

          <div className="min-h-0 shrink overflow-hidden">
            <DetectorPanel detector={detector} stats={scrollStats} compact />
          </div>

          <div className="grid shrink-0 grid-cols-2 gap-2.5">
            <RingStat
              label="Capacity"
              value={capacity}
              max={100}
              display={`${capacity}%`}
              sub="Guardian intensity"
              tone="signal"
              hint="How hard Trellis may push"
              compact
            />
            <RingStat
              label="Identity Gap"
              value={gap.score}
              max={100}
              display={String(gap.score)}
              sub={`Alignment ${gap.alignment}`}
              tone="growth"
              hint="Lower is better"
              invertFill
              compact
            />
          </div>
        </aside>

        {/* Right: phone frame — fills remaining viewport height */}
        <div className="hidden min-h-0 min-w-0 lg:col-span-7 lg:flex lg:justify-end">
          <div
            className={`relative flex h-full min-h-0 w-full max-w-[340px] flex-col transition-opacity duration-300 xl:max-w-[360px] ${
              phoneFullscreen ? "pointer-events-none opacity-0" : ""
            }`}
          >
            <div className="mb-2 flex shrink-0 justify-end">
              <button
                type="button"
                onClick={() => setPhoneFullscreen(true)}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-foreground shadow-sm transition-colors hover:border-signal/40 hover:text-signal"
              >
                <Maximize2 className="h-3.5 w-3.5" />
                Open phone
              </button>
            </div>
            {!phoneFullscreen && (
              <PhoneFrame
                detectorState={detector.state}
                feedHeightClass="min-h-0 flex-1"
                className="min-h-0 flex-1"
                scrollRootRef={setScrollRoot}
                feedStatus={feedStatus}
                items={items}
                scrollRoot={scrollRoot}
                resolvedIds={resolvedIds}
                onCardVisible={onCardVisible}
                onResolveIntervention={resolveIntervention}
              />
            )}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {phoneFullscreen && (
          <motion.div
            className="fixed inset-0 z-[80] flex items-center justify-center px-4 py-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.22 }}
          >
            <button
              type="button"
              aria-label="Close fullscreen phone"
              className="absolute inset-0 bg-[#1a1410]/55 backdrop-blur-md"
              onClick={() => setPhoneFullscreen(false)}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Growth Feed phone fullscreen"
              className="relative z-10 flex w-full max-w-[420px] flex-col items-center gap-4"
              initial={{ opacity: 0, scale: 0.92, y: 24 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 16 }}
              transition={{ duration: 0.28, ease }}
            >
              <div className="flex w-full items-center justify-between px-1">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/70">
                  Owned surface · fullscreen
                </p>
                <button
                  type="button"
                  onClick={() => setPhoneFullscreen(false)}
                  className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-white transition-colors hover:bg-white/20"
                >
                  <X className="h-3.5 w-3.5" />
                  Close
                </button>
              </div>
              <PhoneFrame
                detectorState={detector.state}
                feedHeightClass="h-[min(72vh,640px)]"
                scrollRootRef={setScrollRoot}
                feedStatus={feedStatus}
                items={items}
                scrollRoot={scrollRoot}
                resolvedIds={resolvedIds}
                onCardVisible={onCardVisible}
                onResolveIntervention={resolveIntervention}
                elevated
              />
              <p className="font-mono text-[10px] text-white/50">
                Esc or click outside to exit
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AppShell>
  );
}

function PhoneFrame({
  detectorState,
  feedHeightClass,
  scrollRootRef,
  feedStatus,
  items,
  scrollRoot,
  resolvedIds,
  onCardVisible,
  onResolveIntervention,
  elevated = false,
  className = "",
}: {
  detectorState: DetectorState;
  feedHeightClass: string;
  scrollRootRef: (node: HTMLDivElement | null) => void;
  feedStatus: "loading" | "ready" | "error";
  items: FeedItem[];
  scrollRoot: HTMLElement | null;
  resolvedIds: string[];
  onCardVisible: (item: Extract<FeedItem, { mode: "scroll" }>) => void;
  onResolveIntervention: (
    id: string,
    action: "accept" | "snooze" | "dismiss",
    card: InterventionCard,
  ) => void;
  elevated?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`flex min-h-0 flex-col rounded-[2.2rem] border border-border bg-[#1a1a1a] p-2.5 ${
        elevated
          ? "w-full shadow-[0_40px_120px_rgba(0,0,0,0.45)]"
          : "shadow-[0_24px_80px_rgba(17,17,17,0.18)]"
      } ${className}`}
    >
      <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-[1.75rem] bg-white">
        <div className="flex shrink-0 items-center justify-between px-5 pt-2.5 pb-1.5">
          <span className="font-mono text-[10px] text-foreground">9:41</span>
          <div className="h-5 w-24 rounded-full bg-foreground/90" />
          <span className="font-mono text-[10px] text-foreground">100%</span>
        </div>

        <div className="shrink-0 border-b border-border/60 px-4 pb-2.5">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                Owned surface
              </p>
              <p className="text-sm font-medium text-foreground">For You</p>
            </div>
            <DetectorBadge state={detectorState} />
          </div>
        </div>

        <div
          ref={scrollRootRef}
          className={`${feedHeightClass} space-y-2.5 overflow-y-auto overscroll-contain px-3 py-2.5 scroll-smooth`}
          style={{ scrollbarWidth: "thin" }}
        >
          {feedStatus === "loading" && (
            <p className="py-16 text-center font-mono text-[10px] text-muted-foreground">
              loading your feed :)
            </p>
          )}
          {feedStatus === "error" && (
            <p className="px-4 py-16 text-center text-sm text-muted-foreground">
              Could not load the live feed. Confirm the API is running with
              SEARCH_PROVIDER=combined and valid YouTube/Tavily keys.
            </p>
          )}
          {items.map((item) =>
            item.mode === "scroll" ? (
              <ScrollCard
                key={item.id}
                item={item}
                root={scrollRoot}
                onVisible={() => onCardVisible(item)}
              />
            ) : item.mode === "resource" ? (
              <ResourceCard key={item.id} item={item.resource} />
            ) : (
              <InterventionMorphCard
                key={item.id}
                item={item}
                resolved={resolvedIds.includes(item.id)}
                onAccept={() => onResolveIntervention(item.id, "accept", item.card)}
                onSnooze={() => onResolveIntervention(item.id, "snooze", item.card)}
                onDismiss={() => onResolveIntervention(item.id, "dismiss", item.card)}
              />
            ),
          )}
          {feedStatus === "ready" && items.length > 0 && (
            <p className="py-6 text-center font-mono text-[10px] text-muted-foreground">
              Live owned surface · YouTube + Tavily
            </p>
          )}
        </div>
      </div>
    </div>
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
  compact = false,
}: {
  detector: ReturnType<typeof evaluateMomentDetector>;
  stats: { total: number; low: number; ratio: number };
  compact?: boolean;
}) {
  const { inputs, state } = detector;
  const scrollProgress = Math.min(1, inputs.scrollCount / MIN_SCROLL_COUNT);
  const driftPct = Math.round(inputs.lowValueRatio * 100);
  const driftTarget = Math.round(MIN_LOW_VALUE_RATIO * 100);
  const scrollOk = inputs.scrollCount >= MIN_SCROLL_COUNT;
  const driftOk = inputs.lowValueRatio > MIN_LOW_VALUE_RATIO;
  const focusOk = inputs.inFocusWindow;
  const readyToFire = scrollOk && driftOk && focusOk;

  const stateCopy: Record<DetectorState, string> = {
    monitoring: "Watching scroll — intervene when all three gates clear.",
    armed: "Almost there. One more qualifying scroll can fire The Catch.",
    fired: "Intervention fired — this panel is the receipt.",
    cooldown: "Cooling down 10 minutes so Trellis does not nag.",
  };

  return (
    <div
      className={`flex flex-col rounded-2xl border border-border bg-card/90 shadow-[0_12px_40px_rgba(17,17,17,0.04)] ${
        compact ? "gap-3 p-3.5" : "gap-4 p-5"
      }`}
    >
      <div className="flex shrink-0 items-start justify-between gap-3">
        <div className="space-y-0.5 min-w-0">
          <div className="flex items-center gap-2">
            <Shield className="h-3.5 w-3.5 text-signal" strokeWidth={1.5} />
            <p className="label-eyebrow">Why Trellis can interrupt</p>
          </div>
          <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
            {stateCopy[state]}
          </p>
        </div>
        <DetectorBadge state={state} />
      </div>

      <div className="grid shrink-0 grid-cols-[auto_1fr] items-center gap-4">
        <RingGauge
          value={scrollProgress}
          label={`${Math.min(inputs.scrollCount, MIN_SCROLL_COUNT)}/${MIN_SCROLL_COUNT}`}
          caption="Scrolls"
          tone={scrollOk ? "growth" : "signal"}
          size={compact ? 84 : 108}
        />

        <div className="min-w-0 space-y-2.5">
          <div className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-2">
              <p className="text-xs font-medium text-foreground">Drift share</p>
              <p
                className={`font-mono text-[11px] ${
                  driftOk ? "text-growth" : "text-foreground"
                }`}
              >
                {driftPct}%{" "}
                <span className="text-muted-foreground">/ &gt;{driftTarget}%</span>
              </p>
            </div>
            <div className="relative h-2 overflow-hidden rounded-full bg-secondary">
              <motion.div
                className={`absolute inset-y-0 left-0 rounded-full ${
                  driftOk ? "bg-growth" : "bg-signal"
                }`}
                initial={false}
                animate={{ width: `${Math.min(100, driftPct)}%` }}
                transition={{ duration: 0.35, ease }}
              />
              <div
                className="absolute inset-y-0 w-px bg-foreground/25"
                style={{ left: `${driftTarget}%` }}
                title={`Trigger above ${driftTarget}%`}
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <StatusChip
              ok={focusOk}
              label={focusOk ? "Focus open" : "Outside focus"}
            />
            <StatusChip
              ok={detector.evaluatedInMs < 50}
              label={`${detector.evaluatedInMs.toFixed(1)}ms`}
            />
            <StatusChip
              ok={readyToFire || state === "fired"}
              label={readyToFire || state === "fired" ? "Gates clear" : "Building"}
            />
          </div>
        </div>
      </div>

      <div className="space-y-1.5 rounded-xl bg-secondary/60 px-3 py-2.5">
        <div className="flex items-center justify-between gap-2">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            Session mix
          </p>
          <p className="font-mono text-[10px] text-muted-foreground">
            {stats.total} · {stats.low} low-value
          </p>
        </div>
        <div className="flex h-2.5 overflow-hidden rounded-full bg-background/80">
          {stats.total === 0 ? (
            <div className="w-full bg-border/60" />
          ) : (
            <>
              <motion.div
                className="bg-signal"
                initial={false}
                animate={{ width: `${(stats.low / stats.total) * 100}%` }}
                transition={{ duration: 0.35, ease }}
              />
              <motion.div
                className="bg-growth/70"
                initial={false}
                animate={{
                  width: `${((stats.total - stats.low) / stats.total) * 100}%`,
                }}
                transition={{ duration: 0.35, ease }}
              />
            </>
          )}
        </div>
        <div className="flex gap-3 font-mono text-[10px] text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-signal" />
            Low-value {Math.round(stats.ratio * 100) || 0}%
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-growth/70" />
            Neutral / craft
          </span>
        </div>
      </div>
    </div>
  );
}

function StatusChip({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.12em] ${
        ok
          ? "border-growth/30 bg-growth/5 text-growth"
          : "border-border bg-background text-muted-foreground"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-growth" : "bg-muted-foreground/40"}`} />
      {label}
    </span>
  );
}

function RingGauge({
  value,
  label,
  caption,
  tone,
  size = 96,
}: {
  value: number; // 0–1
  label: string;
  caption: string;
  tone: "signal" | "growth";
  size?: number;
}) {
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(1, value));
  const offset = circumference * (1 - clamped);
  const color = tone === "growth" ? "var(--growth)" : "var(--signal)";

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={false}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.4, ease }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="num text-lg font-medium text-foreground leading-none">{label}</span>
        <span className="mt-1 font-mono text-[9px] uppercase tracking-[0.14em] text-muted-foreground">
          {caption}
        </span>
      </div>
    </div>
  );
}

function RingStat({
  label,
  value,
  max,
  display,
  sub,
  tone,
  hint,
  invertFill = false,
  compact = false,
}: {
  label: string;
  value: number;
  max: number;
  display: string;
  sub: string;
  tone: "signal" | "growth";
  hint: string;
  invertFill?: boolean;
  compact?: boolean;
}) {
  const ratio = max === 0 ? 0 : value / max;
  // For Gap, lower is better — ring fills toward alignment (inverse of gap).
  const fill = invertFill ? 1 - ratio : ratio;

  return (
    <div
      className={`rounded-2xl border border-border bg-card/90 ${
        compact ? "space-y-2 p-3" : "space-y-3 p-4"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="label-eyebrow">{label}</span>
        {tone === "signal" ? (
          <Gauge className="h-3.5 w-3.5 text-signal" strokeWidth={1.5} />
        ) : (
          <Sparkles className="h-3.5 w-3.5 text-growth" strokeWidth={1.5} />
        )}
      </div>
      <div className="flex items-center gap-2.5">
        <RingGauge
          value={fill}
          label={display}
          caption=""
          tone={tone}
          size={compact ? 58 : 72}
        />
        <div className="min-w-0 space-y-0.5">
          <p className="font-mono text-[10px] text-muted-foreground">{sub}</p>
          <p className="text-[10px] leading-snug text-muted-foreground line-clamp-2">
            {hint}
          </p>
        </div>
      </div>
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
  const card = item.data;
  const isYouTube = Boolean(card.metadata?.video_id) || card.tag === "YouTube";

  return (
    <div
      ref={ref}
      className={`rounded-2xl border p-4 ${
        isLow ? "border-border bg-white" : "border-border/60 bg-[#F7F7F5]"
      }`}
    >
      <div className="flex items-center justify-between mb-3 gap-2">
        <span
          className={`font-mono text-[9px] uppercase tracking-[0.16em] px-2 py-0.5 rounded-full border ${
            isLow
              ? "text-[#B45309] border-[#B45309]/25 bg-[#B45309]/5"
              : "text-muted-foreground border-border"
          }`}
        >
          {card.tag}
        </span>
        <div className="flex items-center gap-2 font-mono text-[9px] text-muted-foreground">
          {card.sourceBadge && <span>{card.sourceBadge}</span>}
          <span>{isLow ? "low-value" : "neutral"}</span>
        </div>
      </div>
      {card.thumbnailUrl ? (
        <a
          href={card.url ?? undefined}
          target="_blank"
          rel="noreferrer"
          className="mb-3 block overflow-hidden rounded-xl bg-secondary"
          onClick={() => {
            if (!card.url) return;
            void recordFeedEvent(card.id, "opened", {
              url: card.url,
              provider: isYouTube ? "youtube" : "web",
            });
          }}
        >
          <img
            src={card.thumbnailUrl}
            alt=""
            className="aspect-video w-full object-cover"
            loading="lazy"
          />
        </a>
      ) : null}
      <p className="text-[15px] font-medium leading-snug text-foreground">
        {card.title}
      </p>
      {card.channelTitle && (
        <p className="mt-1 font-mono text-[10px] text-muted-foreground">
          {card.channelTitle}
        </p>
      )}
      {card.url && !card.thumbnailUrl && (
        <a
          href={card.url}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex text-xs font-medium text-signal underline-offset-2 hover:underline"
          onClick={() => {
            void recordFeedEvent(card.id, "opened", {
              url: card.url,
              provider: isYouTube ? "youtube" : "web",
            });
          }}
        >
          Open source
        </a>
      )}
    </div>
  );
}

function ResourceCard({ item }: { item: ApiFeedItem }) {
  const isYouTube = Boolean(item.metadata.video_id);
  const isSpotify =
    item.tag === "Spotify" || item.metadata.provider === "spotify";
  const openResource = () => {
    void recordFeedEvent(item.id, "opened", {
      url: item.url,
      provider: isSpotify ? "spotify" : isYouTube ? "youtube" : "web",
    });
  };

  return (
    <article
      className={`rounded-2xl border bg-white p-4 ${
        isSpotify
          ? "border-[#1DB954]/35 shadow-[0_8px_24px_rgba(29,185,84,0.10)]"
          : "border-signal/25 shadow-[0_8px_24px_rgba(200,137,43,0.08)]"
      }`}
    >
      {item.thumbnailUrl ? (
        <div className="relative mb-3 overflow-hidden rounded-xl bg-secondary">
          <img
            src={item.thumbnailUrl}
            alt=""
            className={`w-full object-cover ${
              isSpotify ? "aspect-square" : "aspect-video"
            }`}
            loading="lazy"
          />
          {isSpotify && (
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-3 pb-2.5 pt-8">
              <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-white/75">
                Playlist for you
              </p>
            </div>
          )}
        </div>
      ) : isSpotify ? (
        <div className="mb-3 flex aspect-square items-end rounded-xl bg-gradient-to-br from-[#1DB954] via-[#169c46] to-[#0d3d24] p-3">
          <div>
            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-white/70">
              Playlist for you
            </p>
            <p className="mt-1 text-sm font-medium text-white line-clamp-2">
              {item.title}
            </p>
          </div>
        </div>
      ) : null}
      <div className="flex items-center justify-between gap-3">
        <span
          className={`font-mono text-[9px] uppercase tracking-[0.16em] ${
            isSpotify ? "text-[#169c46]" : "text-signal"
          }`}
        >
          {isSpotify ? "Spotify" : isYouTube ? "YouTube next step" : item.tag}
        </span>
        {item.sourceBadge && (
          <span className="rounded-full border border-border px-2 py-0.5 font-mono text-[9px] text-muted-foreground">
            {isSpotify ? "Persona match" : item.sourceBadge}
          </span>
        )}
      </div>
      <h3 className="mt-2 text-[15px] font-medium leading-snug text-foreground">
        {item.title}
      </h3>
      {item.channelTitle && (
        <p className="mt-1 font-mono text-[10px] text-muted-foreground">{item.channelTitle}</p>
      )}
      {item.explanation && (
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          {item.explanation.whyThis || item.explanation.whyNow}
        </p>
      )}
      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          onClick={openResource}
          className={`mt-3 inline-flex rounded-xl px-3 py-2 text-xs font-medium transition-colors ${
            isSpotify
              ? "bg-[#1DB954] text-white hover:bg-[#17a34a]"
              : "bg-foreground text-background hover:bg-foreground/90"
          }`}
        >
          {isSpotify ? "Open in Spotify" : "Open resource"}
        </a>
      )}
    </article>
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
