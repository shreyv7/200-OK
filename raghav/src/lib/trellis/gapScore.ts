import type { DeclaredSelf, EvidenceEvent } from "./types";

export function calculateGapScore(
  createRatio: number,
  consumeRatio: number,
  driftRatio: number
): number {
  const score = createRatio * 100 - driftRatio * 50;
  return Math.max(0, Math.min(100, Math.round(score)));
}

const CREATE_KINDS = new Set(["creation", "completion", "real_world"]);
const DRIFT_KINDS = new Set(["drift", "dismissal"]);
const HALF_LIFE_DAYS = 7;

/** Alignment (0-100) at a point in time, using a 7-day half-life decay over evidence. */
export function calculateAlignmentAt(
  events: EvidenceEvent[],
  _declaredSelf: DeclaredSelf,
  at: Date
): { alignment: number } {
  let create = 0;
  let passive = 0;
  let drift = 0;

  for (const e of events) {
    const ageDays = (at.getTime() - new Date(e.occurredAt).getTime()) / 86_400_000;
    if (ageDays < 0) continue;
    const weight = (e.strength ?? 0) * Math.pow(0.5, ageDays / HALF_LIFE_DAYS);
    if (CREATE_KINDS.has(e.kind)) create += weight;
    else if (DRIFT_KINDS.has(e.kind)) drift += weight;
    else passive += weight;
  }

  const total = create + passive + drift;
  if (total === 0) return { alignment: 0 };

  const alignment = ((create + passive * 0.35) / total) * 100 - (drift / total) * 20;
  return { alignment: Math.max(0, Math.min(100, Math.round(alignment))) };
}
