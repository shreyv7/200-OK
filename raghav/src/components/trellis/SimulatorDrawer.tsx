import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useTrellis } from "@/lib/trellis/store";
import { toast } from "sonner";

const actions = [
  { key: "doom", label: "Inject 5× doomscroll" },
  { key: "day", label: "Advance 1 day" },
  { key: "cal", label: "Fire calendar trigger" },
  { key: "dismiss", label: "Force 3rd dismissal (unlearning)" },
] as const;

export function SimulatorDrawer({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const {
    injectDoomscroll,
    advanceDay,
    fireCalendarTrigger,
    forceThirdDismissal,
    dayOffset,
    events,
    dismissalCount,
    gap,
  } = useTrellis();

  const run = (key: (typeof actions)[number]["key"]) => {
    if (key === "doom") {
      injectDoomscroll();
      toast("5 drift events injected");
    }
    if (key === "day") {
      advanceDay();
      toast("Clock advanced 1 day — evidence decayed");
    }
    if (key === "cal") fireCalendarTrigger();
    if (key === "dismiss") forceThirdDismissal();
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full border-l border-border bg-card font-mono sm:max-w-sm"
      >
        <SheetHeader>
          <SheetTitle className="font-mono text-sm tracking-widest text-signal">
            SIMULATOR / DEBUG
          </SheetTitle>
        </SheetHeader>
        <div className="space-y-2 px-4">
          {actions.map((a) => (
            <button
              key={a.key}
              onClick={() => run(a.key)}
              className="w-full rounded-xl border border-border bg-secondary/50 px-3 py-3 text-left text-xs transition-colors hover:border-signal/40 hover:bg-signal/5"
            >
              {"> "}
              {a.label}
            </button>
          ))}
        </div>
        <div className="mt-6 space-y-1 px-4 text-[11px] text-muted-foreground">
          <p>day_offset = {dayOffset}</p>
          <p>evidence_events = {events.length}</p>
          <p>session_dismissals = {dismissalCount}</p>
          <p>gap_score = {gap.score}</p>
          <p className="pt-3 text-muted-foreground/70">Shift+D toggles this panel</p>
        </div>
      </SheetContent>
    </Sheet>
  );
}
