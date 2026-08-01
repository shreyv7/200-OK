import React, { useState, useEffect } from "react";
import { searchSemantic, getVectorSearchStatus, reindexVectorCatalog } from "@/lib/api/endpoints";
import type { SemanticSearchResponse, QdrantStatusResponse } from "@/lib/api/types";
import { Search, Database, RefreshCw, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";

export function VectorSearchBar() {
  const [query, setQuery] = useState("");
  const [collection, setCollection] = useState("all");
  const [loading, setLoading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [status, setStatus] = useState<QdrantStatusResponse | null>(null);
  const [response, setResponse] = useState<SemanticSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reindexMsg, setReindexMsg] = useState<string | null>(null);

  useEffect(() => {
    getVectorSearchStatus()
      .then((st) => setStatus(st))
      .catch((err) => console.warn("Failed to fetch Qdrant status:", err));
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchSemantic(query.trim(), collection, 5);
      setResponse(res);
    } catch (err: any) {
      setError(err?.message || "Failed to query Qdrant vector database.");
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    setReindexMsg(null);
    try {
      const res = await reindexVectorCatalog();
      setReindexMsg(res.message || "Successfully indexed catalog items into Qdrant Cloud!");
      // Refresh status
      const st = await getVectorSearchStatus();
      setStatus(st);
    } catch (err: any) {
      setReindexMsg("Reindexing failed: " + (err?.message || "Unknown error"));
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 shadow-2xl space-y-6">
      {/* Header & Status Badge */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-indigo-500/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Qdrant Vector DB & Semantic Search
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time vector similarity matching across catalog, resources, and partner profiles.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-xs">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-300 font-medium">Qdrant Cloud:</span>
            {status?.enabled ? (
              <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                Active ({status.collections.length} collections)
              </span>
            ) : (
              <span className="text-amber-400 font-semibold flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> Standby
              </span>
            )}
          </div>

          <button
            onClick={handleReindex}
            disabled={reindexing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/30 text-indigo-200 text-xs font-medium transition duration-200 disabled:opacity-50"
            title="Index database catalog items into Qdrant Cloud"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reindexing ? "animate-spin" : ""}`} />
            {reindexing ? "Indexing..." : "Sync Vector Store"}
          </button>
        </div>
      </div>

      {reindexMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          {reindexMsg}
        </div>
      )}

      {/* Search Input Form */}
      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search semantically (e.g. 'growth stories for public speaking bottleneck')..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/90 border border-indigo-500/30 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-400 transition"
          />
        </div>

        <select
          value={collection}
          onChange={(e) => setCollection(e.target.value)}
          className="px-3 py-2.5 rounded-xl bg-slate-900/90 border border-indigo-500/30 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
        >
          <option value="all">All Collections</option>
          <option value="catalog_stories">Growth Stories</option>
          <option value="catalog_tools">Tools</option>
          <option value="catalog_mentors">Mentors</option>
          <option value="partner_profiles">Partner Profiles</option>
        </select>

        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/20 transition duration-200 disabled:opacity-50"
        >
          {loading ? "Searching..." : "Vector Search"}
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Results Display */}
      {response && (
        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
            <span>
              Query: <strong className="text-slate-200">"{response.query}"</strong>
            </span>
            <span>
              Found <strong className="text-indigo-400">{response.total_results}</strong> matches
              {response.vector_store_active ? " (Qdrant Cloud)" : " (Local Fallback)"}
            </span>
          </div>

          {response.results.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-sm bg-slate-900/40 rounded-xl border border-dashed border-slate-800">
              No vector matches found. Click "Sync Vector Store" above to index your catalog data into Qdrant Cloud!
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {response.results.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-900/60 border border-indigo-500/15 hover:border-indigo-500/40 transition duration-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
                        {item.collection.replace("catalog_", "")}
                      </span>
                      <h4 className="text-sm font-semibold text-slate-100">
                        {item.payload.title || item.payload.name || item.payload.display_name || item.id}
                      </h4>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2">
                      {item.payload.narrative ||
                        item.payload.description ||
                        item.payload.bio ||
                        item.payload.outcome ||
                        `Bottleneck: ${item.payload.bottleneck || "N/A"} | Stage: ${item.payload.stage || "N/A"}`}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <span className="text-xs text-slate-400 font-mono">Similarity:</span>
                    <span className="text-xs font-bold font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {(item.score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
