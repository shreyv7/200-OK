import { apiFetch } from "./client";
import type {
  ApiAgentRunResult,
  ApiDashboardSummary,
  ApiDeclaredSelf,
  ApiFeedPage,
  ApiIdentityStack,
  ApiLedgerEntry,
  ApiLedgerRecordRequest,
  ApiMeUser,
  ApiOnboardingTurnResponse,
  ApiPartnerProfile,
  ApiPreparedIntervention,
  ApiStackVariants,
  QdrantStatusResponse,
  SemanticSearchResponse,
} from "./types";

export function getMe() {
  return apiFetch<ApiMeUser>("/me");
}

export function onboardingTurn(body: {
  sessionId?: string | null;
  message?: string;
  answerKind?: "preset" | "freeform" | null;
}) {
  return apiFetch<ApiOnboardingTurnResponse>("/identity/onboarding", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getIdentity() {
  return apiFetch<ApiDeclaredSelf>("/identity");
}

export function patchIdentity(body: {
  attributes: ApiDeclaredSelf["attributes"];
  confirm?: boolean;
}) {
  return apiFetch<ApiDeclaredSelf>("/identity", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function getGrowthFeed() {
  return apiFetch<ApiFeedPage>("/feed");
}

export function getPreparedFeedIntervention() {
  return apiFetch<ApiPreparedIntervention>("/feed/prepared-intervention");
}

export function recordFeedEvent(
  itemId: string,
  event: "viewed" | "opened" | "skipped" | "completed",
  metadata: Record<string, unknown> = {},
) {
  return apiFetch("/feed/events", {
    method: "POST",
    body: JSON.stringify({ itemId, event, metadata }),
  });
}

export function createEvidence(body: {
  timestamp: string;
  source: "trellis" | "youtube" | "github" | "google_calendar" | "notion" | "x";
  type: string;
  category: "creation" | "passive_learning" | "focus_drift" | "reflection";
  identityAttributeIds?: string[];
  value: number;
  baseWeight: number;
  metadata?: Record<string, unknown>;
  simulated?: boolean;
}) {
  return apiFetch("/evidence", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function patchCapacity(value: number) {
  return apiFetch<{ capacity: number }>("/capacity", {
    method: "PATCH",
    body: JSON.stringify({ value }),
  });
}

export function getDashboardSummary() {
  return apiFetch<ApiDashboardSummary>("/dashboard/summary");
}

export function getActiveStack() {
  return apiFetch<ApiIdentityStack>("/stack/active");
}

export function getStackVariants() {
  return apiFetch<ApiStackVariants>("/stack/variants");
}

export function refreshStack() {
  return apiFetch<{ status: string }>("/stack/refresh", { method: "POST" });
}

export function listLedger() {
  return apiFetch<ApiLedgerEntry[]>("/ledger");
}

export function listLedgerAdaptations() {
  return apiFetch<ApiLedgerEntry[]>("/ledger/adaptations");
}

export function recordLedgerAction(body: ApiLedgerRecordRequest) {
  return apiFetch<ApiLedgerEntry>("/ledger/record", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createAgentRun(type: "weekly_report" | "evolution") {
  return apiFetch<ApiAgentRunResult>("/agents/runs", {
    method: "POST",
    body: JSON.stringify({ type }),
  });
}

export function acceptEvolution(proposalId: string) {
  return apiFetch<ApiDeclaredSelf>(`/identity/evolution/${proposalId}/accept`, {
    method: "POST",
  });
}

export function rejectEvolution(proposalId: string) {
  return apiFetch<{ proposalId: string; status: string }>(
    `/identity/evolution/${proposalId}/reject`,
    { method: "POST" },
  );
}

export function searchSemantic(query: string, collection: string = "all", limit: number = 5) {
  const params = new URLSearchParams({ q: query, collection, limit: String(limit) });
  return apiFetch<SemanticSearchResponse>(`/search/semantic?${params.toString()}`);
}

export function getVectorSearchStatus() {
  return apiFetch<QdrantStatusResponse>("/search/status");
}

export function reindexVectorCatalog() {
  return apiFetch<{ status: string; message: string; counts?: Record<string, number> }>(
    "/search/vector/index",
    { method: "POST" },
  );
}

export function getPartnerMatches() {
  return apiFetch<ApiPartnerProfile[]>("/partners/matches");
}
