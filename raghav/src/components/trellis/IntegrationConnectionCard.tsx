import { useState, type ReactNode } from "react";
import { toast } from "sonner";
import { AlertCircle, CheckCircle2, Loader2, RefreshCw, Unplug } from "lucide-react";
import {
  useConnectProvider,
  useRevokeProvider,
  useTriggerGithubSync,
  type IntegrationStatus,
} from "@/lib/integrations/useIntegrations";

interface IntegrationCardProps {
  provider: "google-calendar" | "github";
  title: string;
  description: string;
  icon: ReactNode;
  status: IntegrationStatus | undefined;
  isLoading: boolean;
}

export function IntegrationConnectionCard({
  provider,
  title,
  description,
  icon,
  status,
  isLoading,
}: IntegrationCardProps) {
  const connectMutation = useConnectProvider();
  const revokeMutation = useRevokeProvider();
  const syncMutation = useTriggerGithubSync();

  const [isConnecting, setIsConnecting] = useState(false);

  const isConnected = status?.isActive ?? false;
  const isExpired = status ? !status.isActive && status.revokedAt === null : false;

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      const res = await connectMutation.mutateAsync(provider);
      window.location.href = res.authUrl;
    } catch (err: any) {
      toast.error(err.message || `Failed to initiate connection to ${title}`);
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await revokeMutation.mutateAsync(provider);
      toast.success(`${title} disconnected. Ingesting stopped.`);
    } catch (err: any) {
      toast.error(err.message || `Failed to disconnect ${title}`);
    }
  };

  const handleSyncNow = async () => {
    try {
      const res = await syncMutation.mutateAsync();
      toast.success(res.message || `Synced ${res.synced} events from GitHub`);
    } catch (err: any) {
      toast.error(err.message || "GitHub sync failed");
    }
  };

  const formatDate = (isoStr: string | null) => {
    if (!isoStr) return "";
    try {
      return new Date(isoStr).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="relative rounded-2xl border border-border bg-card/90 p-5 font-mono shadow-[0_4px_20px_rgba(17,17,17,0.03)] backdrop-blur-md transition-all duration-200 hover:border-border/80">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border bg-secondary/60 text-foreground">
            {icon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold tracking-tight text-foreground">{title}</h3>

              {isLoading ? (
                <span className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground/40" />
              ) : isConnected ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-signal/30 bg-signal/10 px-2 py-0.5 text-[9px] font-medium text-signal">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-75" />
                    <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-signal" />
                  </span>
                  ACTIVE
                </span>
              ) : isExpired ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[9px] font-medium text-amber-500">
                  <AlertCircle className="h-2.5 w-2.5" />
                  NEEDS RECONNECT
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-secondary/50 px-2 py-0.5 text-[9px] font-medium text-muted-foreground">
                  OFFLINE
                </span>
              )}
            </div>

            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{description}</p>

            {isConnected && status?.connectedAt && (
              <p className="mt-2 text-[10px] text-muted-foreground/80">
                Connected on {formatDate(status.connectedAt)}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0 sm:self-center">
          {isConnected ? (
            <>
              {provider === "github" && (
                <button
                  onClick={handleSyncNow}
                  disabled={syncMutation.isPending}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-secondary px-3.5 py-2 text-xs font-medium text-foreground transition-all hover:bg-secondary/80 disabled:opacity-50"
                >
                  {syncMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3.5 w-3.5" />
                  )}
                  <span>Sync Now</span>
                </button>
              )}

              <button
                onClick={handleDisconnect}
                disabled={revokeMutation.isPending}
                className="inline-flex items-center gap-1.5 rounded-xl border border-destructive/30 bg-destructive/10 px-3.5 py-2 text-xs font-medium text-destructive transition-all hover:bg-destructive/20 disabled:opacity-50"
              >
                {revokeMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Unplug className="h-3.5 w-3.5" />
                )}
                <span>Disconnect</span>
              </button>
            </>
          ) : (
            <button
              onClick={handleConnect}
              disabled={isConnecting || connectMutation.isPending}
              className="inline-flex items-center gap-1.5 rounded-xl bg-foreground px-4 py-2 text-xs font-medium text-background transition-all hover:bg-foreground/90 disabled:opacity-50"
            >
              {isConnecting || connectMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <CheckCircle2 className="h-3.5 w-3.5" />
              )}
              <span>{isExpired ? "Reconnect" : "Connect"}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
