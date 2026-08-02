import React, { useState } from "react";
import { searchSemantic } from "@/lib/api/endpoints";
import type { SemanticSearchResponse } from "@/lib/api/types";
import { Search, AlertCircle } from "lucide-react";

const SCOPE_LABELS: Record<string, string> = {
  all: "Everything",
  catalog_stories: "Growth Stories",
  catalog_tools: "Tools",
  catalog_mentors: "Mentors",
  partner_profiles: "Growth Partners",
};

function collectionLabel(collection: string): string {
  return (
    SCOPE_LABELS[collection] ??
    collection.replace("catalog_", "").replace(/_/g, " ")
  );
}

function resultTitle(payload: Record<string, unknown>, fallbackId: string): string {
  const title =
    payload.title || payload.name || payload.display_name || fallbackId;
  return String(title);
}

function resultBlurb(payload: Record<string, unknown>): string {
  const narrative =
    payload.narrative ||
    payload.description ||
    payload.bio ||
    payload.outcome;
  if (narrative) return String(narrative);
  const bottleneck = payload.bottleneck ? String(payload.bottleneck) : null;
  const stage = payload.stage ? String(payload.stage) : null;
  if (bottleneck || stage) {
    return [bottleneck && `Focus: ${bottleneck}`, stage && `Stage: ${stage}`]
      .filter(Boolean)
      .join(" · ");
  }
  return "Matched to your search.";
}

export function VectorSearchBar() {
  const [query, setQuery] = useState("");
  const collection = "all";
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SemanticSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchSemantic(query.trim(), collection, 5);
      setResponse(res);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Something went wrong. Try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="w-full space-y-5">
      <div>
        <p className="label-eyebrow text-signal">Discover</p>
        <h2 className="mt-1 font-display text-2xl font-medium tracking-tight">
          Find what fits your growth
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask in plain language — we&apos;ll match mentors, stories, and tools to
          where you are.
        </p>
      </div>

      <form
        onSubmit={handleSearch}
        className="flex flex-col gap-3 sm:flex-row sm:items-stretch"
      >
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. help with public speaking confidence..."
            className="w-full rounded-2xl border border-border bg-card/90 py-3 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground shadow-[0_4px_20px_rgba(17,17,17,0.03)] backdrop-blur-md transition focus:border-signal/40 focus:outline-none focus:ring-2 focus:ring-signal/20"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="rounded-2xl bg-foreground px-5 py-3 text-sm font-medium text-background transition hover:bg-foreground/90 disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && (
        <div className="flex items-center gap-2 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 font-mono text-xs text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {response && (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 font-mono text-[11px] text-muted-foreground">
            <span>
              Results for{" "}
              <span className="font-medium text-foreground">
                &ldquo;{response.query}&rdquo;
              </span>
            </span>
            <span>
              {response.total_results}{" "}
              {response.total_results === 1 ? "match" : "matches"}
            </span>
          </div>

          {response.results.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border bg-card/40 px-6 py-10 text-center text-sm text-muted-foreground">
              No strong matches yet. Try a different phrasing.
            </div>
          ) : (
            <ul className="grid grid-cols-1 gap-3">
              {response.results.map((item) => (
                <li
                  key={`${item.collection}-${item.id}`}
                  className="flex flex-col gap-3 rounded-2xl border border-border bg-card/90 p-4 shadow-[0_4px_20px_rgba(17,17,17,0.03)] backdrop-blur-md transition hover:border-border/80 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0 space-y-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex rounded-full border border-signal/30 bg-signal/10 px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-[0.08em] text-signal">
                        {collectionLabel(item.collection)}
                      </span>
                      <h3 className="truncate text-sm font-medium text-foreground">
                        {resultTitle(item.payload, item.id)}
                      </h3>
                    </div>
                    <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                      {resultBlurb(item.payload)}
                    </p>
                  </div>

                  <div className="shrink-0 self-end sm:self-center">
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {Math.round(item.score * 100)}% match
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
