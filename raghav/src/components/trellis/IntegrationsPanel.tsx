import { Calendar, Github, NotebookPen } from "lucide-react";
import { IntegrationConnectionCard } from "./IntegrationConnectionCard";
import { CompanionPanel } from "./CompanionPanel";
import { useIntegrationsStatus } from "@/lib/integrations/useIntegrations";
import { ScreenTimePanel } from "@/components/screentime";

export function IntegrationsPanel() {
  const { data: statuses, isLoading, error } = useIntegrationsStatus();

  const getStatus = (provider: string) => {
    return statuses?.find((s) => s.provider === provider);
  };

  return (
    <div className="space-y-6">
      <CompanionPanel />

      {/* Screen Time & Device Telemetry Drop Box */}
      <ScreenTimePanel />

      {error && (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Couldn’t load integrations. Check that you’re signed in and the API is running.
        </div>
      )}

      <div className="space-y-4">
        <IntegrationConnectionCard
          provider="google-calendar"
          title="Google Calendar"
          description="Sync meetings into your evidence feed."
          icon={<Calendar className="h-5 w-5 text-signal" />}
          status={getStatus("google-calendar")}
          isLoading={isLoading}
        />

        <IntegrationConnectionCard
          provider="github"
          title="GitHub"
          description="Sync commits and PRs as creation evidence."
          icon={<Github className="h-5 w-5 text-foreground" />}
          status={getStatus("github")}
          isLoading={isLoading}
        />

        <IntegrationConnectionCard
          provider="notion"
          title="Notion"
          description="Sync page edits as creation evidence."
          icon={<NotebookPen className="h-5 w-5 text-foreground" />}
          status={getStatus("notion")}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
