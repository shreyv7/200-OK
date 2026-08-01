import { apiFetch } from "./client";
import type {
  ApiDeclaredSelf,
  ApiMeUser,
  ApiOnboardingPersona,
  ApiOnboardingTurnResponse,
} from "./types";

export function getMe() {
  return apiFetch<ApiMeUser>("/me");
}

export function onboardingTurn(body: {
  sessionId?: string | null;
  message?: string;
  personaId?: string | null;
}) {
  return apiFetch<ApiOnboardingTurnResponse>("/identity/onboarding", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getOnboardingPersonas() {
  return apiFetch<ApiOnboardingPersona[]>("/identity/onboarding/personas");
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
