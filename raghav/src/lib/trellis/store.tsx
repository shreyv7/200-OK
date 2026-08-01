import React, { createContext, useContext, useState, type ReactNode } from "react";
import type { DeclaredSelf, EvidenceEvent, Gap, StackItem, Unlearning } from "./types";

export interface TrellisContextType {
  gap: Gap;
  stack: StackItem[];
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
  gap: { score: 32, createRatio: 0.55, consumeRatio: 0.35, driftRatio: 0.1 },
  stack: [
    { id: "s1", title: "College Presentation Prep", category: "creation", weight: 4.0 },
    { id: "s2", title: "GitHub Commit: Auth Flow", category: "creation", weight: 4.0 },
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
    unlearning,
    clearUnlearning: () => setUnlearning(null),
  };

  return <TrellisContext.Provider value={value}>{children}</TrellisContext.Provider>;
}

export function useTrellis(): TrellisContextType {
  return useContext(TrellisContext);
}

export function capacityLabel(c: number): string {
  if (c >= 67) return "Full Focus";
  if (c >= 34) return "Light Focus";
  return "Micro Steps";
}

export function capacityTier(c: number): string {
  if (c >= 67) return "FULL";
  if (c >= 34) return "LIGHT";
  return "MICRO";
}
