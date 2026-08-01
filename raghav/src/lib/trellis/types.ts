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

export interface Gap {
  score: number;
  createRatio: number;
  consumeRatio: number;
  driftRatio: number;
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
