import React, { createContext, useContext, useState, type ReactNode } from "react";
import type { DeclaredSelf, EvidenceEvent, Gap, StackElement, Unlearning } from "./types";

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
  ledger: any[];
  identityUpdated: boolean;
  acceptIdentityEvolution: () => void;
  dismissStackElement: (id: string) => void;
  completeStackElement: (id: string) => void;
}

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
  struts: [],
  pulsedStruts: [],
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
};

const TrellisContext = createContext<TrellisContextType>(defaultContext);

export function TrellisProvider({ children }: { children: ReactNode }) {
  const [capacity, setCapacity] = useState(75);
  const [unlearning, setUnlearning] = useState<Unlearning | null>(null);

  const value: TrellisContextType = {
    ...defaultContext,
    capacity,
    setCapacity,
    tier: capacityTier(capacity).toUpperCase(),
    unlearning,
    clearUnlearning: () => setUnlearning(null),
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
