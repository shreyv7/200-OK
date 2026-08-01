import { apiFetch } from "./client";
import type {
  ApiDeclaredSelf,
  ApiFeedPage,
  ApiMeUser,
  ApiOnboardingTurnResponse,
  ApiPreparedIntervention,
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
