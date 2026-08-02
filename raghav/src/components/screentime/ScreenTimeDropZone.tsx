import React, { useState, useRef } from "react";
import {
  Smartphone,
  CheckCircle2,
  Flame,
  BookOpen,
  ShieldAlert,
  RefreshCw,
  CalendarClock,
} from "lucide-react";
import { toast } from "sonner";
import { waitForAuthToken } from "@/authentication/token";
import { ApiError, API_BASE } from "@/lib/api/client";
import { useTrellis } from "@/lib/trellis/store";

export interface AppUsageItem {
  appName?: string;
  app_name?: string;
  category: "creation" | "passive_learning" | "focus_drift";
  durationMinutes?: number;
  duration_minutes?: number;
}

export interface ScheduleBlock {
  startTime: string;
  endTime: string;
  label: string;
  category: "creation" | "passive_learning" | "focus_drift";
  minutes: number;
  rationale: string;
}

export interface ScreenTimeResult {
  totalMinutes: number;
  focusMinutes: number;
  learningMinutes: number;
  driftMinutes: number;
  apps: AppUsageItem[];
  evidenceEventsCreated: number;
  scoreDeltaEstimate: number;
  schedule?: ScheduleBlock[];
  ocrSource?: string;
}

export function ScreenTimeDropZone() {
  const { addEvidenceEvent, triggerPulse } = useTrellis();
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<ScreenTimeResult | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    if (!file.type.startsWith("image/") && !file.name.endsWith(".json")) {
      toast.error("Please upload an image screenshot (PNG, JPG, WebP) or JSON report");
      return;
    }

    if (file.type.startsWith("image/")) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      let data: ScreenTimeResult;

      if (file.name.endsWith(".json") || file.type === "application/json") {
        const text = await file.text();
        const parsed = JSON.parse(text) as { apps?: AppUsageItem[] };
        const token = await waitForAuthToken();
        const response = await fetch(`${API_BASE}/screentime/analyze`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ apps: parsed.apps ?? parsed }),
        });
        const body = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            typeof body === "object" && body && "detail" in body
              ? String((body as { detail: unknown }).detail)
              : `Request failed (${response.status})`;
          throw new ApiError(detail, response.status, body);
        }
        data = body as ScreenTimeResult;
      } else {
        const formData = new FormData();
        formData.append("file", file);
        const token = await waitForAuthToken();
        const response = await fetch(`${API_BASE}/screentime/upload`, {
          method: "POST",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: formData,
        });
        const body = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            typeof body === "object" && body && "detail" in body
              ? String((body as { detail: unknown }).detail)
              : `Request failed (${response.status})`;
          throw new ApiError(detail, response.status, body);
        }
        data = body as ScreenTimeResult;
      }

      setResult(data);

      data.apps.forEach((app) => {
        const name = app.appName || app.app_name || "Application";
        const category = app.category || "focus_drift";

        const evType =
          category === "creation"
            ? "published_artifact"
            : category === "passive_learning"
              ? "article_read"
              : "shortform_video_30min";

        const weight =
          category === "creation" ? 4.0 : category === "passive_learning" ? 1.5 : -2.0;

        addEvidenceEvent({
          label: `${name} · ${evType}`,
          kind:
            category === "creation"
              ? "creation"
              : category === "passive_learning"
                ? "passive_learning"
                : "drift",
          strength: Math.min(1, Math.abs(weight) / 4),
          occurredAt: new Date().toISOString(),
          source: "trellis",
          simulated: false,
        });
      });

      triggerPulse();
      toast.success(
        `OCR complete · ${data.apps.length} apps · schedule ready (${data.ocrSource ?? "vision"})`,
      );
    } catch (err) {
      console.error(err);
      toast.error(
        err instanceof ApiError
          ? err.message
          : "Failed to analyze screenshot. Please try again.",
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6 text-left">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`group relative cursor-pointer overflow-hidden rounded-3xl border-2 border-dashed p-8 text-center transition-all duration-300 ${
          isDragging
            ? "border-signal bg-signal/10 scale-[1.01]"
            : "border-border/80 bg-card hover:border-signal/50 hover:bg-card/80 shadow-[0_8px_32px_rgba(17,17,17,0.03)]"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.json"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary text-foreground transition-transform duration-300 group-hover:scale-110">
          {isAnalyzing ? (
            <RefreshCw className="h-6 w-6 animate-spin text-signal" />
          ) : (
            <Smartphone className="h-6 w-6 text-signal" />
          )}
        </div>

        <div className="mt-4 space-y-1">
          <h3 className="font-display text-base font-semibold text-foreground">
            {isAnalyzing
              ? "Reading screenshot…"
              : "Drop Daily Screen Time Screenshot"}
          </h3>
        </div>
      </div>

      {result && (
        <div className="rounded-3xl border border-border bg-card p-6 shadow-sm space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-4">
            <div className="flex items-center gap-3">
              {previewUrl && (
                <img
                  src={previewUrl}
                  alt="Screen Time Screenshot"
                  className="h-12 w-10 rounded-lg object-cover border border-border"
                />
              )}
              <div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-foreground">
                    Screen Time Analyzed ({result.totalMinutes}m Total)
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  OCR source: {result.ocrSource ?? "vision"} ·{" "}
                  {result.evidenceEventsCreated} evidence events ingested
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`text-xs px-3.5 py-1.5 rounded-full font-semibold ${
                  result.scoreDeltaEstimate >= 0
                    ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                    : "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                }`}
              >
                Est. Impact: {result.scoreDeltaEstimate > 0 ? "+" : ""}
                {result.scoreDeltaEstimate} pts
              </span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-foreground">
              <div className="flex items-center gap-1.5 text-emerald-500 font-medium text-[11px] uppercase tracking-wider">
                <Flame className="h-3.5 w-3.5" />
                <span>Creation</span>
              </div>
              <p className="num mt-1 text-xl font-bold text-emerald-500">
                {result.focusMinutes}m
              </p>
            </div>

            <div className="rounded-2xl border border-blue-500/20 bg-blue-500/10 p-3 text-foreground">
              <div className="flex items-center gap-1.5 text-blue-500 font-medium text-[11px] uppercase tracking-wider">
                <BookOpen className="h-3.5 w-3.5" />
                <span>Learning</span>
              </div>
              <p className="num mt-1 text-xl font-bold text-blue-500">
                {result.learningMinutes}m
              </p>
            </div>

            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-3 text-foreground">
              <div className="flex items-center gap-1.5 text-amber-500 font-medium text-[11px] uppercase tracking-wider">
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>Drift</span>
              </div>
              <p className="num mt-1 text-xl font-bold text-amber-500">
                {result.driftMinutes}m
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              Parsed Application Telemetry
            </p>

            <div className="divide-y divide-border/50 rounded-2xl border border-border bg-secondary/30 text-xs">
              {result.apps.map((app, idx) => {
                const name = app.appName || app.app_name || "Application";
                const duration = app.durationMinutes ?? app.duration_minutes ?? 0;
                const category = app.category || "focus_drift";

                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between px-4 py-3 hover:bg-secondary/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-signal" />
                      <span className="font-semibold text-foreground text-sm">{name}</span>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className="font-bold text-foreground">{duration}m</span>
                      <span
                        className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${
                          category === "creation"
                            ? "bg-emerald-500/15 text-emerald-500 border border-emerald-500/30"
                            : category === "passive_learning"
                              ? "bg-blue-500/15 text-blue-500 border border-blue-500/30"
                              : "bg-amber-500/15 text-amber-500 border border-amber-500/30"
                        }`}
                      >
                        {category.replace("_", " ")}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {result.schedule && result.schedule.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <CalendarClock className="h-4 w-4 text-signal" />
                <p className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
                  Recommended Schedule (Next Day)
                </p>
              </div>
              <div className="space-y-2">
                {result.schedule.map((block, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl border border-border bg-secondary/20 px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-semibold text-signal">
                          {block.startTime}–{block.endTime}
                        </span>
                        <span className="text-sm font-semibold text-foreground">
                          {block.label}
                        </span>
                      </div>
                      <span className="text-[11px] text-muted-foreground">
                        {block.minutes}m
                      </span>
                    </div>
                    <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
                      {block.rationale}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
