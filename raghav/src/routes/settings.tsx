import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/trellis/AppShell";
import { IntegrationsPanel } from "@/components/trellis/IntegrationsPanel";
import { SlidersHorizontal, Zap } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings & Integrations — Trellis" },
      {
        name: "description",
        content: "Manage digital source integrations (Google Calendar, GitHub) and account preferences.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"integrations" | "preferences">("integrations");

  useEffect(() => {
    // Handle OAuth redirect return toast
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const provider = params.get("provider");

    if (connected === "true" && provider) {
      toast.success(`${provider} connected successfully! Real evidence sync enabled.`);
      // Clean query params from URL without reload
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  return (
    <AppShell title="Settings & Integrations">
      <div className="mx-auto max-w-4xl space-y-8 font-mono">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Settings</h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Manage your digital source connections and identity engine preferences.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab("integrations")}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-medium transition-colors ${
              activeTab === "integrations"
                ? "border-signal text-foreground font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Digital Sources & Integrations</span>
          </button>

          <button
            onClick={() => setActiveTab("preferences")}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-medium transition-colors ${
              activeTab === "preferences"
                ? "border-signal text-foreground font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>Preferences</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "integrations" && <IntegrationsPanel />}

        {activeTab === "preferences" && (
          <div className="rounded-2xl border border-border bg-card/60 p-8 text-center text-xs text-muted-foreground">
            Account & notifications preferences coming soon.
          </div>
        )}
      </div>
    </AppShell>
  );
}
