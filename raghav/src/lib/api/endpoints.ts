import { apiFetch } from "./client";
import type {
  ApiDeclaredSelf,
  ApiMeUser,
  ApiOnboardingTurnResponse,
  ApiPartnerProfile,
  QdrantStatusResponse,
  SemanticSearchResponse,
} from "./types";

export function getMe() {
  return apiFetch<ApiMeUser>("/me");
}

export function onboardingTurn(body: {
  sessionId?: string | null;
  message?: string;
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
    { method: "POST" }
  );
}

export function getPartnerMatches() {
  return apiFetch<ApiPartnerProfile[]>("/partners/matches");
}
