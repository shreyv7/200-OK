import { createFileRoute, Link } from "@tanstack/react-router";
import { LatticeMark } from "@/components/trellis/Lattice";
import { EditorialInterventionFlow } from "@/components/trellis/EditorialInterventionFlow";
import { LatticeDivider } from "@/components/trellis/LatticeDivider";
import { MorphingPersona } from "@/components/trellis/MorphingPersona";
import { ArrowRight, ChevronRight } from "lucide-react";
import { motion } from "motion/react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Trellis — An Agentic Growth Curator" },
      {
        name: "description",
        content:
          "Trellis measures the gap between who you say you want to become and what your behaviour shows. Then quietly closes it.",
      },
      { property: "og:title", content: "Trellis — An Agentic Growth Curator" },
      {
        property: "og:description",
        content:
          "There is a gap between who you say you are and who your behaviour proves you are. Trellis quietly closes that gap.",
      },
    ],
  }),
  component: Landing,
});

const flagshipEase = [0.16, 1, 0.3, 1] as const;

function Landing() {
  return (
    <div className="relative min-h-screen text-foreground selection:bg-foreground selection:text-background overflow-x-hidden">
      <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Link
            to="/"
            className="group flex items-center gap-3 transition-opacity duration-200 hover:opacity-80"
          >
            <LatticeMark className="h-5 w-5 text-foreground" />
            <span className="font-mono text-xs font-semibold tracking-[0.26em] text-foreground uppercase">
              TRELLIS
            </span>
          </Link>

          <div className="flex items-center gap-6">
            <Link
              to="/login"
              className="hidden sm:inline font-mono text-[11px] text-muted-foreground hover:text-foreground transition-colors tracking-[0.08em]"
            >
              Log in
            </Link>
            <Link
              to="/signup"
              className="group inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-2 text-xs font-medium text-background transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <span>Start here</span>
              <ChevronRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero — brand first, one composition */}
      <section className="relative z-10 mx-auto grid max-w-6xl grid-cols-1 items-center gap-14 px-6 pt-16 pb-24 sm:pt-24 sm:pb-32 lg:grid-cols-[1.05fr_0.95fr] lg:gap-20">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.85, ease: flagshipEase }}
        >
          <p className="font-display text-5xl sm:text-6xl md:text-7xl font-medium tracking-tight text-foreground leading-[0.95]">
            Trellis
          </p>
          <p className="mt-4 font-mono text-[11px] tracking-[0.2em] text-signal uppercase">
            An agentic growth curator
          </p>

          <h1 className="mt-8 max-w-xl text-2xl sm:text-3xl leading-snug font-medium tracking-tight text-foreground/90">
            Become the self you already described.
          </h1>

          <p className="mt-5 max-w-lg text-base leading-relaxed text-muted-foreground sm:text-lg">
            There is who you say you want to become, and what your week actually
            contains. Trellis measures that distance — then curates the smallest
            stack that closes it.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-6">
            <Link
              to="/onboarding"
              className="group inline-flex items-center gap-3 rounded-full bg-foreground px-7 py-3.5 text-sm font-medium text-background transition-all hover:bg-foreground/90"
            >
              <span>Begin the Mirror Interview</span>
              <ArrowRight
                className="h-4 w-4 transition-transform group-hover:translate-x-1"
                strokeWidth={1.75}
              />
            </Link>
            <Link
              to="/feed"
              className="group relative inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              <span>See the Catch</span>
              <ArrowRight className="h-3.5 w-3.5 opacity-40 transition-all group-hover:translate-x-1 group-hover:opacity-100" />
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.95, delay: 0.15, ease: flagshipEase }}
          className="mx-auto w-full max-w-[17rem] lg:max-w-[21.5rem]"
        >
          <MorphingPersona />
        </motion.div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <LatticeDivider />
      </div>

      {/* Core mechanics */}
      <section className="relative z-10 mx-auto max-w-5xl px-6 py-24 sm:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, ease: flagshipEase }}
          className="max-w-2xl"
        >
          <span className="label-eyebrow">Core mechanics</span>
          <h2 className="mt-4 font-display text-3xl leading-[1.1] font-medium tracking-tight sm:text-4xl">
            Identity is not what you wish for. It is what you repeatedly execute.
          </h2>
        </motion.div>

        <motion.div
          className="mt-16 grid gap-12 sm:grid-cols-3"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          variants={{
            hidden: { opacity: 0 },
            show: { opacity: 1, transition: { staggerChildren: 0.14 } },
          }}
        >
          {[
            {
              num: "01",
              title: "Declared Self",
              text: "A short interview extracts the identity you're aiming at — with observable markers instead of adjectives.",
            },
            {
              num: "02",
              title: "Revealed Self",
              text: "Behaviour is scored against those markers with a 7-day decay. No credit for what you did a month ago.",
            },
            {
              num: "03",
              title: "Identity Stack",
              text: "Media, missions, stories, tools — assembled for the current bottleneck, sized to the capacity you have.",
            },
          ].map((item) => (
            <motion.div
              key={item.title}
              variants={{
                hidden: { opacity: 0, y: 16 },
                show: {
                  opacity: 1,
                  y: 0,
                  transition: { duration: 0.7, ease: flagshipEase },
                },
              }}
              className="border-l border-border pl-6"
            >
              <span className="font-mono text-xs text-signal">[{item.num}]</span>
              <h3 className="mt-3 text-lg font-medium text-foreground">{item.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                {item.text}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <LatticeDivider />
      </div>

      {/* Intervention */}
      <section className="relative z-10 mx-auto max-w-5xl px-6 py-24 sm:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, ease: flagshipEase }}
          className="max-w-3xl"
        >
          <span className="label-eyebrow">The Catch</span>
          <h2 className="mt-4 font-display text-3xl leading-[1.1] font-medium tracking-tight sm:text-4xl">
            It intervenes where the drift happens — not where it&apos;s convenient.
          </h2>
          <p className="mt-5 text-base leading-relaxed text-muted-foreground sm:text-lg">
            When scroll turns low-value during a week that mattered, Trellis morphs
            the next card into a one-to-three minute action. Dismiss it three times
            and the hypothesis is retired — and the system tells you it changed.
          </p>
        </motion.div>

        <motion.div
          className="mt-14"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.7, delay: 0.1, ease: flagshipEase }}
        >
          <EditorialInterventionFlow />
        </motion.div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <LatticeDivider />
      </div>

      {/* Closing */}
      <section className="relative z-10 mx-auto max-w-5xl px-6 py-28 sm:py-36 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.8, ease: flagshipEase }}
          className="mx-auto max-w-2xl"
        >
          <span className="font-mono text-[11px] tracking-[0.24em] text-signal uppercase">
            Optimizes for potential, not attention
          </span>
          <h2 className="mt-4 font-display text-3xl sm:text-5xl leading-[1.08] font-medium tracking-tight">
            Close the gap between who you say you are and what you do.
          </h2>
          <div className="mt-10 flex justify-center">
            <Link
              to="/onboarding"
              className="group inline-flex items-center gap-3 rounded-full bg-foreground px-8 py-4 text-sm font-medium text-background transition-all hover:bg-foreground/90"
            >
              <span>Begin the Mirror Interview</span>
              <ArrowRight
                className="h-4 w-4 transition-transform group-hover:translate-x-1"
                strokeWidth={1.75}
              />
            </Link>
          </div>
        </motion.div>
      </section>

      <footer className="relative z-10 border-t border-border px-6 py-10">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 font-mono text-xs text-muted-foreground sm:flex-row">
          <div className="flex items-center gap-2">
            <LatticeMark className="h-4 w-4 opacity-50" />
            <span>TRELLIS · IABTM HACKATHON DEMO</span>
          </div>
          <p className="text-[11px] opacity-75">
            Simulated evidence labeled in-UI · frontend MVP
          </p>
        </div>
      </footer>
    </div>
  );
}
