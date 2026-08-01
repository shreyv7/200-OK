import { useEffect, useState } from "react";
import { getVectorSearchStatus, reindexVectorCatalog } from "@/lib/api/endpoints";
import type { QdrantStatusResponse } from "@/lib/api/types";
import { CheckCircle2, RefreshCw } from "lucide-react";

/**
 * Admin/ops control for refreshing the searchable catalog index.
 * Kept off the main dashboard so end users never see infra details.
 */
export function CatalogSyncPanel() {
  const [status, setStatus] = useState<QdrantStatusResponse | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    getVectorSearchStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  const handleRefresh = async () => {
    setReindexing(true);
    setMessage(null);
    try {
      const res = await reindexVectorCatalog();
      setMessage(res.message || "Catalog search index refreshed.");
      const st = await getVectorSearchStatus();
      setStatus(st);
    } catch (err: unknown) {
      const detail =
        err instanceof Error ? err.message : "Unknown error";
      setMessage(`Refresh failed: ${detail}`);
    } finally {
      setReindexing(false);
    }
  };

  const ready = Boolean(status?.enabled);

  return (
    <div className="rounded-2xl border border-border bg-card/90 p-5 font-mono shadow-[0_4px_20px_rgba(17,17,17,0.03)] backdrop-blur-md">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h3 className="text-sm font-semibold tracking-tight text-foreground">
            Catalog search index
          </h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Keeps mentors, stories, and tools discoverable from Search on the
            dashboard. Refresh after seeding or updating catalog content.
          </p>
          <p className="pt-1 text-[11px] text-muted-foreground">
            Status:{" "}
            <span className={ready ? "font-medium text-signal" : "font-medium text-amber-600"}>
              {ready ? "Ready" : "Unavailable"}
            </span>
          </p>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={reindexing}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-xl border border-border bg-secondary px-3.5 py-2 text-xs font-medium text-foreground transition hover:bg-secondary/80 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${reindexing ? "animate-spin" : ""}`} />
          {reindexing ? "Refreshing…" : "Refresh index"}
        </button>
      </div>

      {message && (
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-border bg-secondary/40 px-3 py-2.5 text-xs text-muted-foreground">
          <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-signal" />
          {message}
        </div>
      )}
    </div>
  );
}
