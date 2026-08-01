import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  createEvidence,
  getActiveStack,
  getDashboardSummary,
  getStackVariants,
  listLedger,
  listLedgerAdaptations,
  patchCapacity,
  recordLedgerAction,
} from "@/lib/api/endpoints";
import {
  mapDashboardSummary,
  mapLedgerEntry,
  mapStackFromActive,
  mapStackFromVariants,
  mapUnlearningFromLedger,
} from "@/lib/api/mappers";
import type {
  DeclaredSelf,
  EvidenceEvent,
  Gap,
  InterventionCard,
  LedgerEntry,
  StackElement,
  Unlearning,
} from "./types";

export interface BottleneckView {
  name: string;
  diagnosis: string;
  confidence: "high" | "medium" | "low";
  evidence: string[];
}

export interface SelectedPersona {
  id: string;
  title: string;
  roleLabel: string;
  bottleneckLabel: string;
  attributeLabels: [string, string];
}

export interface TrellisContextType {
  gap: Gap;
  stack: StackElement[];
  declaredSelf: DeclaredSelf;
  events: EvidenceEvent[];
  now: string;
  struts: any[];
  pulsedStruts: any[];
  capacity: number;
  setCapacity: (c: number) => void;
  tier: string;
  bottleneck: BottleneckView;
  unlearning: Unlearning | null;
  clearUnlearning: () => void;
  calendarPing: string | null;
  injectDoomscroll: () => void;
  advanceDay: () => void;
  fireCalendarTrigger: () => void;
  forceThirdDismissal: () => void;
  dayOffset: number;
  dismissalCount: number;
  ledger: LedgerEntry[];
  identityUpdated: boolean;
  acceptIdentityEvolution: () => void;
  dismissStackElement: (id: string) => Promise<void>;
  completeStackElement: (id: string) => Promise<void>;
  completedStackIds: string[];
  /** True once three dismissals retired the current lens (System Unlearning). */
  unlearned: boolean;
  nextIntervention: InterventionCard;
  logDrift: (label: string) => void;
  acceptIntervention: (card: InterventionCard) => Promise<void>;
  snoozeIntervention: (card: InterventionCard) => Promise<void>;
  /** Returns true when this dismissal crossed the unlearning threshold. */
  dismissIntervention: (card: InterventionCard) => Promise<boolean>;
  refreshLiveData: () => Promise<void>;
  liveReady: boolean;
  addEvidenceEvent: (event: Omit<EvidenceEvent, "id">) => void;
  triggerPulse: () => void;
  /** The active Future-Me persona the user selected during onboarding. */
  selectedPersona: SelectedPersona;
  selectPersona: (id: string) => void;
}

const MEDIA_INTERVENTION: InterventionCard = {
  id: "iv_media",
  lens: "Media",
  action: "Watch a 4-minute breakdown on structuring an opening",
  reasoning:
    "You have been consuming for 11 minutes with no output. A short, targeted input beats an open feed.",
  duration: "4 min",
};

const MICRO_ACTION_INTERVENTION: InterventionCard = {
  id: "iv_micro_action",
  lens: "Micro-Action",
  action: "Record a 60-second voice note explaining what you just read",
  reasoning:
    "Media prompts failed three times, so the system switched lenses: a small active rep instead of more input.",
  duration: "1 min",
};

// ---------------------------------------------------------------------------
// Persona catalogue — mirrors PERSONA_OPTIONS in onboarding.tsx
// ---------------------------------------------------------------------------
export const PERSONA_CATALOGUE: SelectedPersona[] = [
  {
    id: "ai_builder",
    title: "AI Product Builder & Founder",
    roleLabel: "Founding Engineer",
    bottleneckLabel: "Shipping Velocity",
    attributeLabels: ["System Architect", "Public Shipping"],
  },
  {
    id: "keynote_speaker",
    title: "Keynote Speaker & Public Advocate",
    roleLabel: "Public Speaker",
    bottleneckLabel: "Stage Confidence",
    attributeLabels: ["Public Speaking", "Narrative Clarity"],
  },
  {
    id: "technical_author",
    title: "Technical Author & Researcher",
    roleLabel: "Technical Writer",
    bottleneckLabel: "Publishing Consistency",
    attributeLabels: ["Deep Research", "Written Output"],
  },
  {
    id: "product_designer",
    title: "Product Designer & UI Creator",
    roleLabel: "Product Designer",
    bottleneckLabel: "Portfolio Gap",
    attributeLabels: ["Design Systems", "User Empathy"],
  },
  {
    id: "polymath",
    title: "Polymath & Discipline Scholar",
    roleLabel: "Polymath Scholar",
    bottleneckLabel: "Integration Depth",
    attributeLabels: ["Cross-Domain Synthesis", "Deep Work"],
  },
];

const defaultContext: TrellisContextType = {
  gap: {
    score: 32,
    alignment: 68,
    createRatio: 0.55,
    consumeRatio: 0.35,
    driftRatio: 0.1,
    breakdown: [
      {
        attributeId: "public_speaker",
        label: "Public Speaking",
        weight: 0.5,
        target: 0.75,
        revealed: 0.42,
        deficit: 0.33,
        contribution: 0.165,
        markerEvidence: [
          { markerId: "m1", label: "Speaks in front of others", strength: 0.4 },
          { markerId: "m2", label: "Practices a talk out loud", strength: 0.45 },
        ],
      },
      {
        attributeId: "builder",
        label: "System Architect",
        weight: 0.5,
        target: 0.8,
        revealed: 0.55,
        deficit: 0.25,
        contribution: 0.125,
        markerEvidence: [
          { markerId: "m3", label: "Commits and publishes code", strength: 0.6 },
          { markerId: "m4", label: "Closes a project milestone", strength: 0.5 },
        ],
      },
    ],
  },
  stack: [
    {
      id: "st_mission",
      type: "Micro Mission",
      source: "Curated",
      action: "Mark as done",
      why: "Speaking markers are the weakest strut in your lattice right now.",
      whyNow: "You have capacity today and no speaking evidence in the last 6 days.",
      howItCloses: "One recorded rep adds a real speaking marker to the revealed self.",
      variants: {
        MICRO: {
          title: "Record a 60-second explainer",
          description: "Pick one idea you already know and say it out loud on camera.",
          duration: "1-2 min",
        },
        LIGHT: {
          title: "Record a 3-minute walkthrough",
          description: "Explain a recent decision you made, unscripted, in one take.",
          duration: "5 min",
        },
        FULL: {
          title: "Run a full talk rehearsal",
          description: "Deliver a complete run-through and review the recording once.",
          duration: "20 min",
        },
      },
    },
    {
      id: "st_media",
      type: "Media",
      source: "Curated",
      action: "Mark as consumed",
      why: "Your delivery improves fastest with a concrete model to copy.",
      whyNow: "A short input now sets up the speaking rep later today.",
      howItCloses: "Passive input counts at reduced weight until you ship a rep.",
      variants: {
        MICRO: {
          title: "Watch one 2-minute clip",
          description: "A single technique on pacing under pressure.",
          duration: "2 min",
        },
        LIGHT: {
          title: "Watch a 10-minute breakdown",
          description: "How strong speakers structure an opening.",
          duration: "10 min",
        },
        FULL: {
          title: "Study a full talk with notes",
          description: "Watch once for feel, once for structure, and note three moves.",
          duration: "30 min",
        },
      },
    },
    {
      id: "st_story",
      type: "Real-World Experience",
      source: "Curated",
      action: "Log the rep",
      why: "Building in public is the marker your declared self is missing.",
      whyNow: "You have unshipped work sitting from this week.",
      howItCloses: "A public artifact fills the builder strut with fresh evidence.",
      variants: {
        MICRO: {
          title: "Push one commit",
          description: "Ship the smallest meaningful change you have open.",
          duration: "3 min",
        },
        LIGHT: {
          title: "Publish a short project log",
          description: "Two paragraphs on what you built and what broke.",
          duration: "15 min",
        },
        FULL: {
          title: "Close a project milestone",
          description: "Finish the slice, write it up, and share it somewhere public.",
          duration: "45 min",
        },
      },
    },
  ],
  declaredSelf: {
    id: "ds1",
    name: "Aarav Sharma",
    role: "Founding Engineer",
    attributes: [
      { id: "public_speaker", label: "Public Speaking", target: 15 },
      { id: "builder", label: "System Architect", target: 20 },
    ],
  },
  events: [
    { id: "e1", label: "College Presentation", kind: "creation", strength: 0.9, occurredAt: new Date().toISOString(), simulated: false },
    { id: "e2", label: "GitHub Commit: OAuth Router", kind: "creation", strength: 0.85, occurredAt: new Date().toISOString(), simulated: false },
  ],
  now: new Date().toISOString(),
  struts: [
    {
      id: "m1",
      label: "Speaks in front of others",
      attribute: "public_speaker",
      strength: 0.4,
    },
    {
      id: "m2",
      label: "Practices a talk out loud",
      attribute: "public_speaker",
      strength: 0.45,
    },
    {
      id: "m3",
      label: "Commits and publishes code",
      attribute: "builder",
      strength: 0.72,
    },
    {
      id: "m4",
      label: "Closes a project milestone",
      attribute: "builder",
      strength: 0.55,
    },
    {
      id: "m5",
      label: "Ships a public writeup",
      attribute: "builder",
      strength: 0.28,
    },
  ],
  pulsedStruts: ["m2", "m3"],
  capacity: 75,
  setCapacity: () => {},
  tier: "FULL",
  bottleneck: {
    name: "Focus Drift",
    diagnosis: "High passive consumption relative to output over the last 7 days.",
    confidence: "medium",
    evidence: [],
  },
  unlearning: null,
  clearUnlearning: () => {},
  calendarPing: null,
  injectDoomscroll: () => {},
  advanceDay: () => {},
  fireCalendarTrigger: () => {},
  forceThirdDismissal: () => {},
  dayOffset: 0,
  dismissalCount: 0,
  ledger: [],
  identityUpdated: false,
  acceptIdentityEvolution: () => {},
  dismissStackElement: async () => {},
  completeStackElement: async () => {},
  completedStackIds: [],
  unlearned: false,
  nextIntervention: MEDIA_INTERVENTION,
  logDrift: () => {},
  acceptIntervention: async () => {},
  snoozeIntervention: async () => {},
  dismissIntervention: async () => false,
  refreshLiveData: async () => {},
  liveReady: false,
  addEvidenceEvent: () => {},
  triggerPulse: () => {},
  selectedPersona: PERSONA_CATALOGUE[0]!,
  selectPersona: () => {},
};

function familyFromCard(card: InterventionCard): string {
  return card.hypothesisFamily ?? (card.lens === "Media" ? "media" : "micro_mission");
}

function hypothesisFromCard(card: InterventionCard): string {
  return card.hypothesisId ?? card.id;
}

const COMPLETED_STACK_KEY = "trellis_completed_stack_ids";

function loadCompletedStackIds(): string[] {
  try {
    const raw = localStorage.getItem(COMPLETED_STACK_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function persistCompletedStackIds(ids: string[]) {
  try {
    localStorage.setItem(COMPLETED_STACK_KEY, JSON.stringify(ids.slice(-100)));
  } catch {
    /* ignore quota errors */
  }
}

function evidenceShapeForStackElement(element: StackElement): {
  type: string;
  category: "creation" | "passive_learning";
  value: number;
  baseWeight: number;
  kind: EvidenceEvent["kind"];
} {
  const t = element.type.toLowerCase();
  if (t.includes("media") || t.includes("story")) {
    return {
      type: "passive_item",
      category: "passive_learning",
      value: 1.0,
      baseWeight: 1.0,
      kind: "passive_learning",
    };
  }
  return {
    type: "mission_completed",
    category: "creation",
    value: 1.0,
    baseWeight: 3.0,
    kind: "creation",
  };
}

function familyForStackElement(element: StackElement): string {
  if (element.hypothesisFamily) return element.hypothesisFamily;
  const t = element.type.toLowerCase();
  if (t.includes("media")) return "media";
  if (t.includes("real")) return "real_world";
  return "micro_mission";
}

const TrellisContext = createContext<TrellisContextType>(defaultContext);

export function TrellisProvider({ children }: { children: ReactNode }) {
  const [capacity, setCapacityState] = useState(75);
  const [unlearning, setUnlearning] = useState<Unlearning | null>(null);
  const [unlearned, setUnlearned] = useState(false);
  const [dismissalCount, setDismissalCount] = useState(0);
  const [events, setEvents] = useState<EvidenceEvent[]>(defaultContext.events);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [gap, setGap] = useState<Gap>(defaultContext.gap);
  const [stack, setStack] = useState<StackElement[]>(defaultContext.stack);
  const [declaredSelf, setDeclaredSelf] = useState<DeclaredSelf>(defaultContext.declaredSelf);
  const [bottleneck, setBottleneck] = useState<BottleneckView>(defaultContext.bottleneck);
  const [liveReady, setLiveReady] = useState(false);
  const [identityUpdated, setIdentityUpdated] = useState(false);
  const [pulsedStruts, setPulsedStruts] = useState<string[]>(defaultContext.pulsedStruts);
  const [selectedPersona, setSelectedPersona] = useState<SelectedPersona>(PERSONA_CATALOGUE[0]!);
  const [completedStackIds, setCompletedStackIds] = useState<string[]>(() =>
    typeof window === "undefined" ? [] : loadCompletedStackIds(),
  );

  const selectPersona = useCallback((id: string) => {
    const found = PERSONA_CATALOGUE.find((p) => p.id === id);
    if (found) setSelectedPersona(found);
  }, []);

  const markStackCompleted = useCallback((id: string) => {
    setCompletedStackIds((prev) => {
      if (prev.includes(id)) return prev;
      const next = [...prev, id];
      persistCompletedStackIds(next);
      return next;
    });
    setStack((prev) => prev.filter((el) => el.id !== id));
  }, []);

  const nextIntervention = useMemo(
    () => (unlearned ? MICRO_ACTION_INTERVENTION : MEDIA_INTERVENTION),
    [unlearned],
  );

  const refreshLiveData = useCallback(async () => {
    try {
      const [summary, variants, active, entries, adaptations] = await Promise.all([
        getDashboardSummary().catch(() => null),
        getStackVariants().catch(() => null),
        getActiveStack().catch(() => null),
        listLedger().catch(() => []),
        listLedgerAdaptations().catch(() => []),
      ]);

      if (summary) {
        const mapped = mapDashboardSummary(summary);
        setGap(mapped.gap);
        setDeclaredSelf(mapped.declaredSelf);
        setCapacityState(mapped.capacity);
        setBottleneck(mapped.bottleneck);
      }

      const doneIds = loadCompletedStackIds();
      setCompletedStackIds(doneIds);
      const mappedStack =
        variants && Object.keys(variants).length > 0
          ? mapStackFromVariants(variants, active)
          : active
            ? mapStackFromActive(active)
            : [];
      setStack(mappedStack.filter((el) => !doneIds.includes(el.id)));

      setLedger(entries.map(mapLedgerEntry));
      const unlearn = mapUnlearningFromLedger(adaptations.length ? adaptations : entries);
      if (unlearn) {
        setUnlearned(true);
        setUnlearning(unlearn);
      }
      setLiveReady(true);
    } catch {
      setLiveReady(false);
    }
  }, []);

  useEffect(() => {
    void refreshLiveData();
  }, [refreshLiveData]);

  const setCapacity = useCallback((value: number) => {
    setCapacityState(value);
    void patchCapacity(value).catch(() => {
      /* keep optimistic local capacity if network fails */
    });
  }, []);

  const appendEvent = useCallback((event: Omit<EvidenceEvent, "id">) => {
    setEvents((prev) => [
      ...prev,
      { id: `ev_${Date.now()}_${prev.length}`, ...event },
    ]);
  }, []);

  const addEvidenceEvent = appendEvent;

  const triggerPulse = useCallback(() => {
    setPulsedStruts((prev) => (prev.length ? prev : ["m2", "m3"]));
  }, []);

  const injectDoomscroll = useCallback(() => {
    appendEvent({
      label: "Doomscroll session",
      kind: "drift",
      strength: 0.3,
      occurredAt: new Date().toISOString(),
      simulated: true,
    });
  }, [appendEvent]);

  const advanceDay = useCallback(() => {
    appendEvent({
      label: "Day advanced (simulator)",
      kind: "completion",
      strength: 0.2,
      occurredAt: new Date().toISOString(),
      simulated: true,
    });
  }, [appendEvent]);

  const prependLedger = useCallback((entry: LedgerEntry) => {
    setLedger((prev) => [entry, ...prev.filter((row) => row.id !== entry.id)]);
  }, []);

  const logDrift = useCallback(
    (label: string) => {
      appendEvent({
        label,
        kind: "drift",
        strength: 0.2,
        occurredAt: new Date().toISOString(),
        simulated: true,
      });
    },
    [appendEvent],
  );

  const acceptIntervention = useCallback(
    async (card: InterventionCard) => {
      appendEvent({
        label: card.action,
        kind: card.lens === "Media" ? "passive_learning" : "creation",
        strength: card.lens === "Media" ? 0.4 : 0.8,
        occurredAt: new Date().toISOString(),
      });
      try {
        const entry = await recordLedgerAction({
          hypothesisId: hypothesisFromCard(card),
          hypothesisFamily: familyFromCard(card),
          action: "accepted",
        });
        prependLedger(mapLedgerEntry(entry));
      } catch {
        prependLedger({
          id: `lg_local_${Date.now()}`,
          deliveredAt: new Date().toISOString(),
          verdict: "worked",
          hypothesis: `A ${card.lens} prompt at the drift moment converts into a rep`,
          family: card.lens,
          delivered: card.action,
          outcomeWindow: card.duration,
          evidence: "Accepted in-feed (local fallback).",
        });
      }
      setDismissalCount(0);
      void refreshLiveData();
    },
    [appendEvent, prependLedger, refreshLiveData],
  );

  const snoozeIntervention = useCallback(
    async (card: InterventionCard) => {
      try {
        const entry = await recordLedgerAction({
          hypothesisId: hypothesisFromCard(card),
          hypothesisFamily: familyFromCard(card),
          action: "snoozed",
        });
        prependLedger(mapLedgerEntry(entry));
      } catch {
        prependLedger({
          id: `lg_local_${Date.now()}`,
          deliveredAt: new Date().toISOString(),
          verdict: "pending",
          hypothesis: `A ${card.lens} prompt at the drift moment converts into a rep`,
          family: card.lens,
          delivered: card.action,
          outcomeWindow: "Retry in the next capacity window",
          evidence: "Snoozed — local fallback.",
        });
      }
    },
    [prependLedger],
  );

  const dismissIntervention = useCallback(
    async (card: InterventionCard) => {
      const count = dismissalCount + 1;
      setDismissalCount(count);
      appendEvent({
        label: `Dismissed: ${card.action}`,
        kind: "dismissal",
        strength: 0.1,
        occurredAt: new Date().toISOString(),
      });

      try {
        const entry = await recordLedgerAction({
          hypothesisId: hypothesisFromCard(card),
          hypothesisFamily: familyFromCard(card),
          action: "dismissed",
        });
        prependLedger(mapLedgerEntry(entry));
        if (entry.unlearningTriggered) {
          setUnlearned(true);
          setUnlearning({
            hypothesis: `${card.lens} prompts will close the gap`,
            adaptation:
              entry.note ??
              `${card.lens} weight reduced 40%. Switched to the Micro-Action lens.`,
          });
          void refreshLiveData();
          return true;
        }
        return false;
      } catch {
        const crossed = count >= 3 && !unlearned;
        if (crossed) {
          setUnlearned(true);
          setUnlearning({
            hypothesis: `${card.lens} prompts will close the speaking gap`,
            adaptation: `${card.lens} weight reduced 40%. Switched to Micro-Action.`,
          });
        }
        return crossed;
      }
    },
    [appendEvent, dismissalCount, prependLedger, refreshLiveData, unlearned],
  );

  const forceThirdDismissal = useCallback(() => {
    void dismissIntervention(nextIntervention);
  }, [dismissIntervention, nextIntervention]);

  const completeStackElement = useCallback(
    async (id: string) => {
      const element = stack.find((el) => el.id === id);
      if (!element) return;

      const shape = evidenceShapeForStackElement(element);
      const attributeIds = declaredSelf.attributes.map((a) => a.id);
      const title =
        element.variants.FULL?.title ??
        element.variants.LIGHT?.title ??
        element.variants.MICRO?.title ??
        element.type;

      markStackCompleted(id);
      appendEvent({
        label: title,
        kind: shape.kind,
        strength: shape.baseWeight / 5,
        occurredAt: new Date().toISOString(),
        simulated: false,
        source: "trellis",
      });

      try {
        await createEvidence({
          timestamp: new Date().toISOString(),
          source: "trellis",
          type: shape.type,
          category: shape.category,
          identityAttributeIds: attributeIds,
          value: shape.value,
          baseWeight: shape.baseWeight,
          metadata: {
            stackElementId: element.id,
            stackElementType: element.type,
            title,
            action: "completed",
          },
          simulated: false,
        });
      } catch {
        /* keep optimistic local completion; refresh may still recover */
      }

      try {
        const entry = await recordLedgerAction({
          hypothesisId: element.hypothesisId ?? element.id,
          hypothesisFamily: familyForStackElement(element),
          action: "completed",
        });
        prependLedger(mapLedgerEntry(entry));
      } catch {
        prependLedger({
          id: `lg_local_${Date.now()}`,
          deliveredAt: new Date().toISOString(),
          verdict: "worked",
          hypothesis: `Completing ${element.type} closes the gap`,
          family: element.type,
          delivered: title,
          outcomeWindow: "Immediate",
          evidence: "Marked done (local fallback).",
        });
      }

      void refreshLiveData();
    },
    [appendEvent, declaredSelf.attributes, markStackCompleted, prependLedger, refreshLiveData, stack],
  );

  const dismissStackElement = useCallback(
    async (id: string) => {
      const element = stack.find((el) => el.id === id);
      if (!element) return;

      markStackCompleted(id);
      appendEvent({
        label: `Dismissed: ${element.type}`,
        kind: "dismissal",
        strength: 0.1,
        occurredAt: new Date().toISOString(),
        simulated: false,
      });

      try {
        const entry = await recordLedgerAction({
          hypothesisId: element.hypothesisId ?? element.id,
          hypothesisFamily: familyForStackElement(element),
          action: "dismissed",
        });
        prependLedger(mapLedgerEntry(entry));
      } catch {
        /* local dismiss already applied */
      }

      void refreshLiveData();
    },
    [appendEvent, markStackCompleted, prependLedger, refreshLiveData, stack],
  );

  const value: TrellisContextType = {
    ...defaultContext,
    capacity,
    setCapacity,
    tier: capacityTier(capacity).toUpperCase(),
    gap,
    stack,
    declaredSelf,
    bottleneck,
    events,
    pulsedStruts,
    ledger,
    dismissalCount,
    unlearning,
    clearUnlearning: () => setUnlearning(null),
    unlearned,
    nextIntervention,
    logDrift,
    acceptIntervention,
    snoozeIntervention,
    dismissIntervention,
    forceThirdDismissal,
    injectDoomscroll,
    advanceDay,
    identityUpdated,
    acceptIdentityEvolution: () => setIdentityUpdated(true),
    refreshLiveData,
    liveReady,
    addEvidenceEvent,
    triggerPulse,
    selectedPersona,
    selectPersona,
    completeStackElement,
    dismissStackElement,
    completedStackIds,
  };

  return <TrellisContext.Provider value={value}>{children}</TrellisContext.Provider>;
}

export function useTrellis(): TrellisContextType {
  return useContext(TrellisContext);
}

export type CapacityTier = "micro" | "light" | "full";

export const capacityLabel: Record<CapacityTier, string> = {
  micro: "Micro Steps",
  light: "Light Focus",
  full: "Full Focus",
};

export function capacityTier(c: number): CapacityTier {
  if (c >= 67) return "full";
  if (c >= 34) return "light";
  return "micro";
}
