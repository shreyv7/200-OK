import { useAuth } from "@clerk/react";
import { useEffect, useRef } from "react";

import { getMe } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import {
  mapMeToPlatformUser,
  useAuthSession,
} from "./AuthSession";
import { resetAuthBridge, setAuthTokenGetter } from "./token";

/** Clerk JWTs are short-lived (~60s). Refresh often so Companion can keep posting. */
const COMPANION_TOKEN_REFRESH_MS = 30_000;
/** Re-hit /me so Postgres last_login_at / profile stay warm during a long session. */
const ME_REFRESH_MS = 5 * 60_000;
const ME_MAX_ATTEMPTS = 4;

function bridgeTokenToCompanion(token: string | null) {
  document.dispatchEvent(
    new CustomEvent("trellis:set-auth-token", {
      detail: { token },
      bubbles: true,
    }),
  );
  window.postMessage({ type: "TRELLIS_SET_AUTH_TOKEN", token }, "*");
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

/** Registers Clerk session tokens for API calls and provisions the Postgres user via /me. */
export function ClerkAuthBridge() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const session = useAuthSession();
  const sessionRef = useRef(session);
  sessionRef.current = session;

  useEffect(() => {
    if (!isLoaded) {
      sessionRef.current.setBootstrapping();
      return;
    }

    if (!isSignedIn) {
      resetAuthBridge();
      setAuthTokenGetter(null);
      bridgeTokenToCompanion(null);
      sessionRef.current.setSignedOut();
      return;
    }

    setAuthTokenGetter(() => getToken());
    sessionRef.current.setProvisioning();

    let cancelled = false;

    const provisionMe = async () => {
      let lastError = "Could not connect your account";
      for (let attempt = 1; attempt <= ME_MAX_ATTEMPTS; attempt += 1) {
        if (cancelled) return;
        try {
          const me = await getMe();
          if (cancelled) return;
          sessionRef.current.setReady(mapMeToPlatformUser(me));
          return;
        } catch (err) {
          lastError =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : lastError;
          // Brief backoff — Clerk JWT / API may still be warming up.
          await sleep(350 * attempt);
        }
      }
      if (!cancelled) {
        console.error("[Trellis] Failed to provision Postgres user via /me:", lastError);
        sessionRef.current.setError(lastError);
      }
    };

    const syncToken = async () => {
      try {
        const token = await getToken();
        if (cancelled) return;
        bridgeTokenToCompanion(token);
      } catch {
        /* later API calls surface auth failures */
      }
    };

    const onTokenRequest = () => {
      void syncToken();
    };
    const onWindowMessage = (event: MessageEvent) => {
      if (event.data?.type === "TRELLIS_REQUEST_AUTH_TOKEN") onTokenRequest();
    };
    document.addEventListener("trellis:request-auth-token", onTokenRequest);
    window.addEventListener("message", onWindowMessage);

    void syncToken();
    void provisionMe();

    const tokenTimer = window.setInterval(() => {
      void syncToken();
    }, COMPANION_TOKEN_REFRESH_MS);

    const meTimer = window.setInterval(() => {
      void provisionMe();
    }, ME_REFRESH_MS);

    return () => {
      cancelled = true;
      window.clearInterval(tokenTimer);
      window.clearInterval(meTimer);
      document.removeEventListener("trellis:request-auth-token", onTokenRequest);
      window.removeEventListener("message", onWindowMessage);
    };
  }, [getToken, isLoaded, isSignedIn]);

  return null;
}
