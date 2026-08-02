import React from "react";
import { Smartphone } from "lucide-react";
import { ScreenTimeDropZone } from "./ScreenTimeDropZone";

export function ScreenTimePanel() {
  return (
    <div className="rounded-3xl border border-border/80 bg-card p-6 space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-signal/10 text-signal">
          <Smartphone className="h-5 w-5" />
        </div>
        <h3 className="text-base font-semibold tracking-tight text-foreground">
          Screen Time
        </h3>
      </div>

      <ScreenTimeDropZone />
    </div>
  );
}
