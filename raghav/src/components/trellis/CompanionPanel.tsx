import { useEffect, useState } from "react";
import { useAuth } from "@clerk/react";
import { CheckCircle2, ExternalLink, Loader2, Puzzle } from "lucide-react";
import { toast } from "sonner";

const USERSCRIPT_URL = "http://localhost:8002/tampermonkey/trellis-telemetry.user.js";
const PING_INTERVAL_MS = 2500;

type CompanionState = {
  installed: boolean;
  version: string | null;
  checking: boolean;
};

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

    let cancelled = false;
    const syncToken = async () => {
      try {
        const token = await getToken();
        if (!cancelled && token) broadcastAuthToken(token);
      } catch {
        // Non-blocking: Companion will retry on the next interval.
      }
    };

    void syncToken();
    const timer = window.setInterval(() => {
      void syncToken();
    }, 60_000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [getToken, isSignedIn, state.installed]);

  const handleInstall = () => {
    window.open(USERSCRIPT_URL, "_blank", "noopener,noreferrer");
    toast.message("Tampermonkey should open an Install dialog. Click Install once.");
    setTimeout(() => pingCompanion(), 1500);
  };

  return (
    <div className="rounded-2xl border border-border/80 bg-background/70 p-5">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-xl border border-border/70 bg-secondary/40 p-2">
          <Puzzle className="h-5 w-5 text-foreground" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-display text-base text-foreground">Trellis Companion</h3>
            {state.checking ? (
              <span className="inline-flex items-center gap-1 font-mono text-[11px] text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" /> Checking
              </span>
            ) : state.installed ? (
              <span className="inline-flex items-center gap-1 font-mono text-[11px] text-emerald-600">
                <CheckCircle2 className="h-3 w-3" /> Installed{state.version ? ` v${state.version}` : ""}
              </span>
            ) : (
              <span className="font-mono text-[11px] text-muted-foreground">Not detected</span>
            )}
          </div>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
            One-click Tampermonkey userscript that streams Instagram, Facebook, and YouTube browsing
            into your Evidence Pipeline — scrolls, dwell time, shorts/reels, and focus-drift signals.
          </p>

          <ol className="mt-3 space-y-1 font-mono text-[11px] text-muted-foreground">
            <li>1. Install the Tampermonkey browser extension if you do not have it.</li>
            <li>2. Click Enable Behavioral Tracking and press Install once.</li>
            <li>3. Browse Instagram / YouTube / Facebook — Trellis ingests events automatically.</li>
          </ol>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleInstall}
              className="inline-flex items-center gap-2 rounded-xl bg-foreground px-3 py-2 font-mono text-xs text-background transition hover:opacity-90"
            >
              Enable Behavioral Tracking
              <ExternalLink className="h-3.5 w-3.5" />
            </button>
            <a
              href="https://www.tampermonkey.net/"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-border px-3 py-2 font-mono text-xs text-foreground transition hover:bg-secondary/50"
            >
              Get Tampermonkey
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
