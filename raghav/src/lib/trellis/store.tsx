import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type {
  DeclaredSelf,
  EvidenceEvent,
  Gap,
  InterventionCard,
  LedgerEntry,
  StackElement,
  Unlearning,
} from "./types";

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
  dismissStackElement: (id: string) => void;
  completeStackElement: (id: string) => void;
  /** True once three dismissals retired the current lens (System Unlearning). */
  unlearned: boolean;
  nextIntervention: InterventionCard;
  logDrift: (label: string) => void;
  acceptIntervention: (card: InterventionCard) => void;
  snoozeIntervention: (card: InterventionCard) => void;
  /** Returns true when this dismissal crossed the unlearning threshold. */
  dismissIntervention: (card: InterventionCard) => boolean;
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
  dismissStackElement: () => {},
  completeStackElement: () => {},
  unlearned: false,
  nextIntervention: MEDIA_INTERVENTION,
  logDrift: () => {},
  acceptIntervention: () => {},
  snoozeIntervention: () => {},
  dismissIntervention: () => false,
  selectedPersona: PERSONA_CATALOGUE[0]!,
  selectPersona: () => {},
};

const TrellisContext = createContext<TrellisContextType>(defaultContext);

const DISMISSALS_BEFORE_UNLEARNING = 3;

export function TrellisProvider({ children }: { children: ReactNode }) {
  const [capacity, setCapacity] = useState(75);
  const [unlearning, setUnlearning] = useState<Unlearning | null>(null);
  const [unlearned, setUnlearned] = useState(false);
  const [dismissalCount, setDismissalCount] = useState(0);
  const [events, setEvents] = useState<EvidenceEvent[]>(defaultContext.events);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [gapDelta, setGapDelta] = useState(0);
  const [selectedPersona, setSelectedPersona] = useState<SelectedPersona>(PERSONA_CATALOGUE[0]!);

  const selectPersona = useCallback((id: string) => {
    const found = PERSONA_CATALOGUE.find((p) => p.id === id);
    if (found) setSelectedPersona(found);
  }, []);

  const nextIntervention = useMemo(
    () => (unlearned ? MICRO_ACTION_INTERVENTION : MEDIA_INTERVENTION),
    [unlearned],
  );

  const gap: Gap = useMemo(
    () => ({
      ...defaultContext.gap,
      score: Math.max(0, defaultContext.gap.score - gapDelta),
      alignment: Math.min(100, defaultContext.gap.alignment + gapDelta),
    }),
    [gapDelta],
  );

  const appendEvent = useCallback((event: Omit<EvidenceEvent, "id">) => {
    setEvents((prev) => [
      ...prev,
      { id: `ev_${Date.now()}_${prev.length}`, ...event },
    ]);
  }, []);

  const appendLedger = useCallback(
    (entry: Omit<LedgerEntry, "id" | "deliveredAt">) => {
      setLedger((prev) => [
        {
          id: `lg_${Date.now()}_${prev.length}`,
          deliveredAt: new Date().toISOString(),
          ...entry,
        },
        ...prev,
      ]);
    },
    [],
  );

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
    (card: InterventionCard) => {
      appendEvent({
        label: card.action,
        kind: card.lens === "Media" ? "passive_learning" : "creation",
        strength: card.lens === "Media" ? 0.4 : 0.8,
        occurredAt: new Date().toISOString(),
      });
      appendLedger({
        verdict: "worked",
        hypothesis: `A ${card.lens} prompt at the drift moment converts into a rep`,
        family: card.lens,
        delivered: card.action,
        outcomeWindow: card.duration,
        evidence: "Accepted in-feed and logged as a completed rep.",
      });
      setGapDelta((d) => Math.min(defaultContext.gap.score, d + 4));
      setDismissalCount(0);
    },
    [appendEvent, appendLedger],
  );

  const snoozeIntervention = useCallback(
    (card: InterventionCard) => {
      appendLedger({
        verdict: "pending",
        hypothesis: `A ${card.lens} prompt at the drift moment converts into a rep`,
        family: card.lens,
        delivered: card.action,
        outcomeWindow: "Retry in the next capacity window",
        evidence: "Snoozed — no outcome recorded yet.",
      });
    },
    [appendLedger],
  );

  const dismissIntervention = useCallback(
    (card: InterventionCard) => {
      const count = dismissalCount + 1;
      setDismissalCount(count);
      appendEvent({
        label: `Dismissed: ${card.action}`,
        kind: "dismissal",
        strength: 0.1,
        occurredAt: new Date().toISOString(),
      });

      const crossed = count >= DISMISSALS_BEFORE_UNLEARNING && !unlearned;
      const adaptation = `${card.lens} weight reduced 40%. Switched to the Micro-Action lens for the next intervention.`;

      appendLedger({
        verdict: "failed",
        hypothesis: `A ${card.lens} prompt at the drift moment converts into a rep`,
        family: card.lens,
        delivered: card.action,
        outcomeWindow: card.duration,
        evidence: `Dismissed in-feed (${count} of ${DISMISSALS_BEFORE_UNLEARNING} before the lens is retired).`,
        ...(crossed ? { adaptation } : {}),
      });

      if (crossed) {
        setUnlearned(true);
        setUnlearning({
          hypothesis: `${card.lens} prompts will close the speaking gap`,
          adaptation,
        });
      }
      return crossed;
    },
    [appendEvent, appendLedger, dismissalCount, unlearned],
  );

  const value: TrellisContextType = {
    ...defaultContext,
    capacity,
    setCapacity,
    tier: capacityTier(capacity).toUpperCase(),
    gap,
    events,
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
    selectedPersona,
    selectPersona,
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
