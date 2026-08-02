import { useEffect, useState } from "react";
import { useAuth } from "@clerk/react";
import { CheckCircle2, ExternalLink, Loader2, Puzzle } from "lucide-react";
import { toast } from "sonner";

const PING_INTERVAL_MS = 2500;

type CompanionState = {
  installed: boolean;
  version: string | null;
  checking: boolean;
};

function companionInstallUrl() {
  if (typeof window !== "undefined") {
    return `${window.location.origin}/tampermonkey/trellis-telemetry.user.js`;
  }
  return "http://localhost:8080/tampermonkey/trellis-telemetry.user.js";
}

function broadcastAuthToken(token: string) {
  document.dispatchEvent(
    new CustomEvent("trellis:set-auth-token", {
      detail: { token },
      bubbles: true,
    }),
  );
  window.postMessage({ type: "TRELLIS_SET_AUTH_TOKEN", token }, "*");
}

function pingCompanion() {
  document.dispatchEvent(new CustomEvent("trellis:companion-ping", { bubbles: true }));
  window.postMessage({ type: "TRELLIS_COMPANION_PING" }, "*");
}

export function CompanionPanel() {
  const { isSignedIn, getToken } = useAuth();
  const [state, setState] = useState<CompanionState>({
    installed: false,
    version: null,
    checking: true,
  });

  useEffect(() => {
    const markReady = (version?: string) => {
      setState({
        installed: true,
        version: version || document.documentElement.getAttribute("data-trellis-companion-installed"),
        checking: false,
      });
    };

    const onPong = (event: Event) => {
      const detail = (event as CustomEvent<{ version?: string }>).detail;
      markReady(detail?.version);
    };

    const onMessage = (event: MessageEvent) => {
      if (event.data?.type === "TRELLIS_COMPANION_PONG") {
        markReady(event.data.version);
      }
    };

    document.addEventListener("trellis:companion-pong", onPong);
    document.addEventListener("trellis:companion-ready", onPong);
    window.addEventListener("message", onMessage);

    const attr = document.documentElement.getAttribute("data-trellis-companion-installed");
    if (attr) {
      markReady(attr);
    } else {
      setState((prev) => ({ ...prev, checking: true }));
    }

    pingCompanion();
    const timer = window.setInterval(() => {
      const installedAttr = document.documentElement.getAttribute("data-trellis-companion-installed");
      if (installedAttr) {
        markReady(installedAttr);
      } else {
        pingCompanion();
        setState((prev) => ({ ...prev, checking: false, installed: prev.installed }));
      }
    }, PING_INTERVAL_MS);

    return () => {
      document.removeEventListener("trellis:companion-pong", onPong);
      document.removeEventListener("trellis:companion-ready", onPong);
      window.removeEventListener("message", onMessage);
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!isSignedIn || !state.installed) return;
    void (async () => {
      try {
        const token = await getToken();
        if (token) broadcastAuthToken(token);
      } catch {
        /* retry via ClerkAuthBridge */
      }
    })();
  }, [getToken, isSignedIn, state.installed]);

  const handleInstall = () => {
    window.open(companionInstallUrl(), "_blank", "noopener,noreferrer");
    toast.message("Click Install in Tampermonkey, then refresh.");
    setTimeout(() => pingCompanion(), 1500);
    setTimeout(() => pingCompanion(), 4000);
  };

  return (
    <div className="rounded-2xl border border-border/80 bg-background/70 p-5">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-xl border border-border/70 bg-secondary/40 p-2">
          <Puzzle className="h-5 w-5 text-foreground" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold tracking-tight text-foreground">
              Browser tracking
            </h3>
            {state.checking ? (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" /> Checking
              </span>
            ) : state.installed ? (
              <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                <CheckCircle2 className="h-3 w-3" /> Live
              </span>
            ) : (
              <span className="text-xs text-muted-foreground">Not set up</span>
            )}
          </div>

          {state.installed ? (
            <p className="mt-1.5 text-sm text-muted-foreground">
              Keep Trellis open while you browse.
            </p>
          ) : (
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleInstall}
                className="inline-flex items-center gap-2 rounded-full bg-foreground px-4 py-2.5 text-sm font-semibold text-background transition hover:opacity-90"
              >
                Install Companion
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
              <a
                href="https://www.tampermonkey.net/"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2.5 text-sm text-muted-foreground transition hover:text-foreground hover:bg-secondary/50"
              >
                Get Tampermonkey
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
