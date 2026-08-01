import React from "react";

export function LatticeDivider({ className = "" }: { className?: string }) {
  return (
    <div className={`relative flex w-full items-center justify-center py-4 ${className}`} aria-hidden>
      {/* Left Line */}
      <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-border/60 to-border" />
      
      {/* Central Micro Lattice Node */}
      <div className="mx-4 flex items-center gap-1.5 opacity-60">
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 text-muted-foreground" fill="none">
          <line x1="0" y1="8" x2="16" y2="8" stroke="currentColor" strokeWidth="0.8" />
          <line x1="8" y1="0" x2="8" y2="16" stroke="currentColor" strokeWidth="0.8" />
          <line x1="2" y1="2" x2="14" y2="14" stroke="currentColor" strokeWidth="0.8" strokeDasharray="1 2" />
          <line x1="14" y1="2" x2="2" y2="14" stroke="currentColor" strokeWidth="0.8" strokeDasharray="1 2" />
          <circle cx="8" cy="8" r="1.5" fill="currentColor" />
        </svg>
      </div>

      {/* Right Line */}
      <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent via-border/60 to-border" />
    </div>
  );
}
