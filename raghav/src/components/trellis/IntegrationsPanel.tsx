import { Calendar, Github } from "lucide-react";
import { IntegrationConnectionCard } from "./IntegrationConnectionCard";
import { useIntegrationsStatus } from "@/lib/integrations/useIntegrations";

export function IntegrationsPanel() {
  const { data: statuses, isLoading, error } = useIntegrationsStatus();

  const getStatus = (provider: string) => {
    return statuses?.find((s) => s.provider === provider);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border/80 bg-secondary/30 p-4 font-mono text-xs text-muted-foreground">
        <p className="font-medium text-foreground">Honest Data Engine Active</p>
        <p className="mt-1 leading-relaxed">
          Connecting your digital sources streams real evidence directly into Trellis.
          Synced events bypass simulation, update your Revealed Self, and dynamically drive your Identity Gap score.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-4 font-mono text-xs text-destructive">
          Failed to load integration status. Make sure the API server is running on http://localhost:8000.
        </div>
      )}

      <div className="space-y-4">
        <IntegrationConnectionCard
          provider="google-calendar"
          title="Google Calendar"
          description="Syncs real upcoming meetings, talks, and presentations to trigger pre-event leverage rehearsal moments (attended_experience)."
          icon={<Calendar className="h-5 w-5 text-signal" />}
          status={getStatus("google-calendar")}
          isLoading={isLoading}
        />

        <IntegrationConnectionCard
          provider="github"
          title="GitHub"
          description="Syncs real commits and merged Pull Requests directly into your creation evidence feed (github_commit & published_artifact)."
          icon={<Github className="h-5 w-5 text-foreground" />}
          status={getStatus("github")}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
