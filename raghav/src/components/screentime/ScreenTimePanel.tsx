import React from "react";
import { Smartphone, Sparkles, ShieldCheck } from "lucide-react";
import { ScreenTimeDropZone } from "./ScreenTimeDropZone";

export function ScreenTimePanel() {
  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-border/80 bg-card p-6 shadow-[0_8px_32px_rgba(17,17,17,0.03)] space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-signal/10 text-signal">
              <Smartphone className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-display text-base font-semibold text-foreground">
                Screen Time & Device Telemetry Drop Box
              </h3>
              <p className="font-mono text-xs text-muted-foreground">
                Upload daily iOS Screen Time or Android Digital Wellbeing screenshots to measure "The Real You".
              </p>
            </div>
          </div>

          <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-mono text-[10px] font-semibold text-emerald-500 uppercase tracking-wider">
            <ShieldCheck className="h-3 w-3" />
            Revealed Self Sync
          </span>
        </div>

        <ScreenTimeDropZone />
      </div>
    </div>
  );
}
