import { UserButton, useUser } from "@clerk/react";
import { useEffect, useState, type ReactNode } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { AnimatePresence, motion } from "motion/react";
import { FileText, LayoutDashboard, Rss, ScrollText, Settings, Users } from "lucide-react";
import { LatticeMark } from "./Lattice";
import { CapacitySlider } from "./CapacitySlider";
import { SimulatorDrawer } from "./SimulatorDrawer";
import { useTrellis } from "@/lib/trellis/store";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/mentors", label: "Experts & Guides", icon: Users },
  { to: "/feed", label: "Growth Feed", icon: Rss },
  { to: "/ledger", label: "Trust Ledger", icon: ScrollText },
  { to: "/report", label: "Weekly Report", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function AppShell({ title, children }: { title: string; children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { unlearning, clearUnlearning, calendarPing } = useTrellis();
  const { user } = useUser();
  const [simOpen, setSimOpen] = useState(false);
  const isDev = import.meta.env.DEV;

  const displayName =
    user?.fullName ||
    user?.firstName ||
    user?.primaryEmailAddress?.emailAddress ||
    "Signed in";
  const displaySub =
    user?.primaryEmailAddress?.emailAddress ||
    user?.username ||
    "Trellis member";
  const avatarLetter = (displayName[0] || "T").toUpperCase();

  useEffect(() => {
    if (!isDev) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.shiftKey && (e.key === "D" || e.key === "d")) {
        const t = e.target as HTMLElement | null;
        if (t && ["INPUT", "TEXTAREA"].includes(t.tagName)) return;
        e.preventDefault();
        setSimOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isDev]);


  useEffect(() => {
    if (!unlearning) return;
    const t = setTimeout(clearUnlearning, 6000);
    return () => clearTimeout(t);
  }, [unlearning, clearUnlearning]);

  return (
    <div className="relative flex h-svh overflow-hidden text-foreground selection:bg-foreground selection:text-background">
      {/* Desktop sidebar — pinned; main column scrolls independently */}
      <aside className="relative z-20 hidden h-full w-52 shrink-0 flex-col border-r border-border bg-background/80 backdrop-blur-xl md:flex">
        <div className="flex items-center gap-2.5 px-6 py-6">
          <LatticeMark className="h-4 w-4 text-foreground" />
          <span className="font-mono text-[11px] font-semibold tracking-[0.26em] text-foreground uppercase">
            TRELLIS
          </span>
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 py-1">
          {nav.map((item) => {
            const active = pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`relative flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-xs transition-colors duration-200 ${
                  active
                    ? "text-foreground font-medium"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="absolute left-0 top-2 bottom-2 w-0.5 rounded-full bg-signal"
                    transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                  />
                )}
                <item.icon
                  className={`h-3.5 w-3.5 shrink-0 ${active ? "text-signal" : "text-muted-foreground"}`}
                  strokeWidth={1.5}
                />
                <span className="font-mono">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="shrink-0 px-5 py-5 border-t border-border">
          <div className="flex items-center gap-2.5">
            <UserButton afterSignOutUrl="/" />
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-foreground text-[10px] font-mono font-medium text-background md:hidden">
              {avatarLetter}
            </div>
            <div className="leading-tight min-w-0">
              <p className="text-[11px] font-medium text-foreground truncate">
                {displayName}
              </p>
              <p className="font-mono text-[9.5px] text-muted-foreground truncate">
                {displaySub}
              </p>
            </div>
          </div>
        </div>
      </aside>

      <div className="relative z-10 flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto overscroll-contain pb-20 md:pb-0">
        <header className="sticky top-0 z-30 flex shrink-0 items-center justify-between gap-4 border-b border-border bg-background/80 px-5 sm:px-8 py-4 backdrop-blur-xl">
          <div className="flex items-center gap-2 font-mono text-[10px] text-muted-foreground tracking-[0.16em] uppercase">
            <span className="text-foreground font-medium">TRELLIS</span>
            <span className="opacity-60">/</span>
            <span>{title}</span>
          </div>

          <div className="flex items-center gap-4 sm:gap-5">
            <CapacitySlider />
            <div className="hidden sm:flex items-center gap-1.5 font-mono text-[9.5px] text-muted-foreground">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-40" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-signal" />
              </span>
              <span>Engine active</span>
            </div>
          </div>
        </header>

        <AnimatePresence>
          {unlearning && (
            <motion.div
              initial={{ y: -30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -30, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              onClick={clearUnlearning}
              role="status"
              className="mx-5 sm:mx-8 mt-6 cursor-pointer rounded-2xl border border-signal/30 bg-card/95 p-4 font-mono text-xs leading-relaxed text-foreground shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-md"
            >
              <p className="font-medium text-signal">
                Hypothesis Failed: &lsquo;{unlearning.hypothesis}&rsquo; — dismissed 3
                times.
              </p>
              <p className="mt-1 text-signal">
                System Adaptation: {unlearning.adaptation}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {calendarPing && (
            <motion.div
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              className="mx-5 sm:mx-8 mt-6 rounded-2xl border border-border bg-card/95 p-4 font-mono text-xs text-muted-foreground shadow-[0_8px_32px_rgba(17,17,17,0.03)] backdrop-blur-md"
            >
              Calendar trigger:{" "}
              <span className="font-medium text-foreground">{calendarPing}</span> —
              rehearsal window is narrowing.
            </motion.div>
          )}
        </AnimatePresence>

        <main className="min-w-0 flex-1 px-5 sm:px-8 py-8 sm:py-10">{children}</main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 inset-x-0 z-40 flex md:hidden border-t border-border bg-background/95 backdrop-blur-xl">
        {nav.map((item) => {
          const active = pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex flex-1 flex-col items-center gap-1 py-3 text-[9px] font-mono uppercase tracking-[0.08em] ${
                active ? "text-signal" : "text-muted-foreground"
              }`}
            >
              <item.icon className="h-4 w-4" strokeWidth={1.5} />
              <span>{item.label.split(" ")[0]}</span>
            </Link>
          );
        })}
      </nav>

      {isDev && <SimulatorDrawer open={simOpen} onOpenChange={setSimOpen} />}
    </div>
  );
}

