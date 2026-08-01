import { useAuth } from "@clerk/react";
import { useEffect } from "react";

import { API_BASE } from "@/lib/api/client";
import { setAuthTokenGetter } from "./token";

function bridgeTokenToCompanion(token: string) {
  document.dispatchEvent(
    new CustomEvent("trellis:set-auth-token", {
      detail: { token },
      bubbles: true,
    }),
  );
  window.postMessage({ type: "TRELLIS_SET_AUTH_TOKEN", token }, "*");
}

/** Registers Clerk session tokens for API calls and syncs the local user row via /me. */
export function ClerkAuthBridge() {
  const { isLoaded, isSignedIn, getToken } = useAuth();

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      setAuthTokenGetter(null);
      return;
    }

    setAuthTokenGetter(() => getToken());

    void (async () => {
      const token = await getToken();
      if (!token) return;
      bridgeTokenToCompanion(token);
      try {
        await fetch(`${API_BASE}/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
      } catch {
        // Non-blocking: route guards and later API calls will surface auth failures.
      }
    })();
  }, [getToken, isLoaded, isSignedIn]);

  return null;
}
