export interface EvidenceEvent {
  id: string;
  label: string;
  kind: "creation" | "completion" | "real_world" | "passive_learning" | "drift" | "dismissal";
  strength: number;
  occurredAt: string;
  simulated?: boolean;
  isSimulated?: boolean;
  source?: string;
}

export interface DeclaredSelf {
  id: string;
  name: string;
  role: string;
  attributes: Array<{ id: string; label: string; target: number }>;
}

export interface GapBreakdownRow {
  attributeId: string;
  label: string;
  weight: number;
  target: number;
  revealed: number;
  deficit: number;
  contribution: number;
  markerEvidence: Array<{ markerId: string; label: string; strength: number }>;
}

export interface Gap {
  score: number;
  alignment: number;
  createRatio: number;
  consumeRatio: number;
  driftRatio: number;
  breakdown: GapBreakdownRow[];
}

export interface StackVariant {
  title: string;
  description: string;
  duration: string;
}

export interface StackElement {
  id: string;
  type: string;
  source?: string;
  action: string;
  why: string;
  whyNow: string;
  howItCloses: string;
  /** Keyed by capacity tier: MICRO | LIGHT | FULL. */
  variants: Record<string, StackVariant>;
}

export interface StackItem {
  id: string;
  title: string;
  category: string;
  weight: number;
  description?: string;
  preparedIntervention?: string;
}

export interface Unlearning {
  hypothesis: string;
  adaptation: string;
}

export type InterventionLens = "Media" | "Micro-Action" | "Real-World";

export interface InterventionCard {
  id: string;
  lens: InterventionLens;
  action: string;
  reasoning: string;
  duration: string;
  /** Backend hypothesis id for Trust Ledger recording. */
  hypothesisId?: string;
  /** Backend hypothesis family (media / micro_mission / …). */
  hypothesisFamily?: string;
}

export type Verdict = "worked" | "failed" | "pending";

export interface LedgerEntry {
  id: string;
  verdict: Verdict;
  /** The prediction Trellis made when it delivered the intervention. */
  hypothesis: string;
  /** Intervention family / lens, e.g. Media or Micro-Action. */
  family: string;
  deliveredAt: string;
  /** What the user actually saw. */
  delivered: string;
  outcomeWindow: string;
  evidence: string;
  /** Present when the failure triggered System Unlearning. */
  adaptation?: string;
}
