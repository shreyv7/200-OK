export interface ApiIdentityMarker {
  id: string;
  label: string;
  description?: string | null;
}

export interface ApiIdentityAttribute {
  id: string;
  label: string;
  weight: number;
  targetWeeklyPoints: number;
  markers: ApiIdentityMarker[];
}

export interface ApiDeclaredSelf {
  id: string;
  userId: string;
  version: number;
  attributes: ApiIdentityAttribute[];
  createdAt: string;
  confirmedAt?: string | null;
}

export interface ApiOnboardingTurnResponse {
  sessionId: string;
  nextQuestion?: string | null;
  draft?: ApiDeclaredSelf | null;
  done: boolean;
}

export interface ApiMeUser {
  id: string;
  clerkId?: string | null;
  email?: string | null;
  fullName?: string | null;
  profileImage?: string | null;
  lastLoginAt?: string | null;
  createdAt?: string;
  updatedAt?: string | null;
  capacity?: number;
}

export type ApiSourceBadge = "Live web" | "Cached web" | "Curated fallback" | "Graph RAG";

export interface ApiStackExplanation {
  whyThis: string;
  whyNow: string;
  howReducesGap: string;
}

export interface ApiStackElement {
  id: string;
  type: string;
  title: string;
  url?: string | null;
  sourceBadge: ApiSourceBadge;
  explanation: ApiStackExplanation;
  metadata?: Record<string, unknown>;
}

export interface ApiIdentityStack {
  id: string;
  userId: string;
  hypothesisId: string;
  bottleneck: string;
  elements: ApiStackElement[];
  curatedAt: string;
  validUntil?: string | null;
}

export interface ApiInterventionVariant {
  hypothesisId: string;
  intensity: "full" | "light" | "micro";
  stack: ApiIdentityStack;
  generatedAt: string;
}

export type ApiStackVariants = Partial<
  Record<"full" | "light" | "micro", ApiInterventionVariant>
>;

export interface ApiAttributeContribution {
  attributeId: string;
  w_i: number;
  D_i: number;
  R_i: number;
  deficit_i: number;
}

export interface ApiGapBreakdown {
  userId: string;
  gapScore: number;
  alignmentScore: number;
  createPoints: number;
  consumePoints: number;
  driftPoints: number;
  createConsumeRatio: number;
  consistency: number;
  momentum: number;
  attributes: ApiAttributeContribution[];
}

export interface ApiBottleneckPacket {
  bottleneck: string;
  confidence: number;
  supporting_evidence: string[];
  missing_evidence: string[];
  alternative_bottleneck?: string | null;
}

export interface ApiDashboardSummary {
  userId: string;
  declaredSelf: ApiDeclaredSelf;
  gap: ApiGapBreakdown;
  bottleneck?: ApiBottleneckPacket | null;
  capacity: number;
}

export type ApiLedgerAction =
  | "delivered"
  | "accepted"
  | "snoozed"
  | "dismissed"
  | "completed";

export type ApiLedgerVerdict = "worked" | "failed" | "pending";

export interface ApiLedgerEntry {
  id: string;
  userId: string;
  hypothesisId: string;
  hypothesisFamily: string;
  action: ApiLedgerAction;
  verdict: ApiLedgerVerdict;
  timestamp: string;
  unlearningTriggered: boolean;
  lensWeightAdjustment?: Record<string, number> | null;
  note?: string | null;
}

export interface ApiLedgerRecordRequest {
  hypothesisId: string;
  hypothesisFamily: string;
  action: ApiLedgerAction;
}

export interface ApiWeeklyReport {
  id: string;
  userId: string;
  gapScoreStart?: number | null;
  gapScoreEnd: number;
  gapDelta: number;
  narrative: string;
  highlights: string[];
  generatedAt: string;
  simulated: boolean;
}

export interface ApiProposedChange {
  action: "add" | "remove" | "reweight";
  attributeId: string;
  attributeLabel: string;
  newWeight?: number | null;
  reason: string;
  evidenceIds: string[];
}

export interface ApiEvolutionProposal {
  proposalId: string;
  userId: string;
  declaredSelfVersion: number;
  proposedChanges: ApiProposedChange[];
  supportingEvidenceIds: string[];
  narrative: string;
  generatedAt: string;
}

export interface ApiAgentRunResult {
  runId: string;
  type: "weekly_report" | "evolution";
  weeklyReport?: ApiWeeklyReport | null;
  evolutionProposal?: ApiEvolutionProposal | null;
}

export interface ApiFeedItem {
  id: string;
  kind: "low_value" | "neutral" | "resource";
  title: string;
  tag: string;
  url?: string | null;
  sourceBadge?: ApiSourceBadge | null;
  thumbnailUrl?: string | null;
  channelTitle?: string | null;
  durationSeconds?: number | null;
  explanation?: ApiStackExplanation | null;
  metadata: Record<string, unknown>;
}

export interface ApiFeedPage {
  items: ApiFeedItem[];
  nextCursor?: string | null;
}

export interface ApiPreparedIntervention {
  stack: ApiIdentityStack;
}

export interface VectorSearchResultItem {
  id: string;
  collection: string;
  score: number;
  payload: Record<string, unknown>;
}

export interface SemanticSearchResponse {
  query: string;
  total_results: number;
  vector_store_active: boolean;
  results: VectorSearchResultItem[];
}

export interface QdrantStatusResponse {
  enabled: boolean;
  url: string | null;
  collection_prefix: string;
  collections: string[];
}

export interface ApiPartnerProfile {
  id: string;
  name: string;
  stage: string;
  goal: string;
  matchReason?: string;
  similarity?: number;
  sourceBadge?: string;
  prototype?: boolean;
}
