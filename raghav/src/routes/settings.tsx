import { createFileRoute } from "@tanstack/react-router";
import { useEffect } from "react";
import { toast } from "sonner";
import { RequireAuth } from "@/authentication";
import { AppShell } from "@/components/trellis/AppShell";
import { IntegrationsPanel } from "@/components/trellis/IntegrationsPanel";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings & Integrations — Trellis" },
      {
        name: "description",
        content: "Manage digital source integrations (Google Calendar, GitHub, Companion).",
      },
    ],
  }),
  component: SettingsRoute,
});

function SettingsRoute() {
  return (
    <RequireAuth>
      <SettingsPage />
    </RequireAuth>
  );
}

function SettingsPage() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const provider = params.get("provider");

    if (connected === "true" && provider) {
      toast.success(`${provider} connected successfully! Real evidence sync enabled.`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  return (
    <AppShell title="Settings & Integrations">
      <div className="mx-auto max-w-4xl space-y-8 font-sans">
        <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">
          Settings
        </h1>
        <IntegrationsPanel />
      </div>
    </AppShell>
  );
}
