import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Check } from "lucide-react";
import { LivingTrellisBackground } from "@/components/trellis/LivingTrellisBackground";
import { LatticeMark } from "@/components/trellis/Lattice";
import { mock } from "@/lib/trellis/mockApi";

export const Route = createFileRoute("/onboarding")({
  head: () => ({
    meta: [
      { title: "Mirror Interview — Trellis" },
      {
        name: "description",
        content:
          "A short conversational interview that extracts your Declared Self into measurable identity markers.",
      },
      { property: "og:title", content: "Mirror Interview — Trellis" },
    ],
  }),
  component: Onboarding,
});

const ease = [0.16, 1, 0.3, 1] as const;

interface ChatMessage {
  id: string;
  role: "ai" | "user";
  text: string;
}

interface Question {
  id: string;
  prompt: string;
  hint: string;
  options: string[];
}

const QUESTIONS: Question[] = [
  {
    id: "aspiration",
    prompt: "Who are you trying to become?",
    hint: "Aspiration — the Declared Self starts here.",
    options: [
      "A confident public speaker who can hold a room",
      "A builder who ships projects in public",
      "Both — speak with authority and ship consistently",
    ],
  },
  {
    id: "why",
    prompt: "Why does that matter to you right now?",
    hint: "Urgency — what makes this week's gap costly.",
    options: [
      "I have a presentation coming and I freeze",
      "I finish work privately and never publish",
      "My week is full of tutorials and empty of output",
    ],
  },
  {
    id: "habits",
    prompt: "What does a typical week of yours actually look like?",
    hint: "Current habits — the Revealed Self baseline.",
    options: [
      "2+ hours of short-form video most days",
      "Lots of learning, almost no shipping",
      "Bursts of focus, then multi-day flatlines",
    ],
  },
  {
    id: "blocker",
    prompt: "What's the biggest thing holding you back?",
    hint: "Bottleneck seed — Curator will refine this later.",
    options: [
      "Fear of being seen before I'm ready",
      "I consume instead of create when tired",
      "I start too many things and finish none",
    ],
  },
  {
    id: "capacity",
    prompt: "Realistically, how much capacity can you give this each day?",
    hint: "Guardian uses this to size every intervention.",
    options: [
      "15–30 minutes — keep it micro",
      "30–60 minutes — a few focused missions",
      "60+ minutes when the week allows",
    ],
  },
];

type Phase = "chat" | "extracting" | "confirm";

function Onboarding() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("chat");
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "m0",
      role: "ai",
      text: "I'm going to ask you a few short questions — not personality adjectives, but things that show up as behaviour. Ready when you are.",
    },
    {
      id: "m1",
      role: "ai",
      text: QUESTIONS[0]!.prompt,
    },
  ]);
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing, phase]);

  const currentQ = QUESTIONS[qIndex]!;

  const selectAnswer = (answer: string) => {
    if (typing || phase !== "chat") return;

    const nextAnswers = [...answers, answer];
    setAnswers(nextAnswers);
    setMessages((prev) => [
      ...prev,
      { id: `u_${qIndex}`, role: "user", text: answer },
    ]);

    const nextIndex = qIndex + 1;
    if (nextIndex < QUESTIONS.length) {
      setTyping(true);
      setTimeout(() => {
        setTyping(false);
        setQIndex(nextIndex);
        setMessages((prev) => [
          ...prev,
          {
            id: `a_${nextIndex}`,
            role: "ai",
            text: QUESTIONS[nextIndex]!.prompt,
          },
        ]);
      }, 700);
    } else {
      setTyping(true);
      setTimeout(() => {
        setTyping(false);
        setPhase("extracting");
        setTimeout(() => setPhase("confirm"), 1800);
      }, 500);
    }
  };

  const declared = mock.demoUser.declaredSelf;

  return (
    <div className="relative min-h-screen bg-background text-foreground overflow-x-hidden">
      <LivingTrellisBackground />

      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-2.5">
            <LatticeMark className="h-4 w-4" />
            <span className="font-mono text-[11px] font-semibold tracking-[0.24em] uppercase">
              TRELLIS
            </span>
          </div>
          <p className="font-mono text-[10px] text-muted-foreground uppercase tracking-[0.16em]">
            Mirror Interview · F1
          </p>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-3xl px-5 py-8 sm:py-12">
        <AnimatePresence mode="wait">
          {phase === "chat" || phase === "extracting" ? (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.4, ease }}
              className="space-y-6"
            >
              <div>
                <p className="label-eyebrow text-signal">The Mirror</p>
                <h1 className="mt-2 font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.1]">
                  Tell me who you&apos;re becoming.
                </h1>
                <p className="mt-3 text-sm text-muted-foreground max-w-lg">
                  Four to six questions. I&apos;ll extract a Declared Self with
                  observable markers you can confirm before anything is measured.
                </p>
              </div>

              {/* Progress */}
              <div className="flex items-center gap-2">
                {QUESTIONS.map((q, i) => (
                  <div
                    key={q.id}
                    className={`h-1 flex-1 rounded-full transition-colors ${
                      i < answers.length
                        ? "bg-signal"
                        : i === qIndex && phase === "chat"
                          ? "bg-foreground/30"
                          : "bg-border"
                    }`}
                  />
                ))}
              </div>

              {/* Chat thread */}
              <div className="rounded-3xl border border-border bg-card/90 backdrop-blur-xl p-5 sm:p-7 min-h-[420px] flex flex-col">
                <div className="flex-1 space-y-4 overflow-y-auto max-h-[48vh] pr-1">
                  {messages.map((m) => (
                    <motion.div
                      key={m.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, ease }}
                      className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                          m.role === "user"
                            ? "bg-foreground text-background rounded-br-md"
                            : "bg-secondary text-foreground rounded-bl-md"
                        }`}
                      >
                        {m.text}
                      </div>
                    </motion.div>
                  ))}
                  {typing && (
                    <div className="flex justify-start">
                      <div className="rounded-2xl rounded-bl-md bg-secondary px-4 py-3 font-mono text-xs text-muted-foreground">
                        Thinking…
                      </div>
                    </div>
                  )}
                  {phase === "extracting" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="rounded-2xl border border-signal/30 bg-signal/5 p-4 font-mono text-xs space-y-2"
                    >
                      <p className="text-signal uppercase tracking-[0.16em]">
                        Extracting Declared Self…
                      </p>
                      <p className="text-muted-foreground">
                        Mapping answers → identity attributes → observable markers →
                        weights
                      </p>
                    </motion.div>
                  )}
                  <div ref={bottomRef} />
                </div>

                {/* Options */}
                {phase === "chat" && !typing && (
                  <div className="mt-6 space-y-2 border-t border-border pt-5">
                    <p className="label-eyebrow mb-3">{currentQ.hint}</p>
                    {currentQ.options.map((opt) => (
                      <button
                        key={opt}
                        onClick={() => selectAnswer(opt)}
                        className="group w-full text-left rounded-2xl border border-border bg-background px-4 py-3.5 text-sm text-foreground transition-all hover:border-signal/50 hover:bg-signal/5"
                      >
                        <span className="flex items-center justify-between gap-3">
                          <span>{opt}</span>
                          <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="confirm"
              initial={{ opacity: 0, y: 16, filter: "blur(4px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ duration: 0.55, ease }}
              className="space-y-6"
            >
              <div>
                <p className="label-eyebrow text-signal">Did I get you right?</p>
                <h1 className="mt-2 font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.1]">
                  {declared.headline}
                </h1>
                <p className="mt-3 text-sm text-muted-foreground max-w-lg">
                  Confirm this Declared Self. Trellis will measure your behaviour
                  against these markers — nothing changes without your consent.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {declared.attributes.map((attr) => (
                  <div
                    key={attr.id}
                    className="rounded-3xl border border-border bg-card p-6 space-y-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="label-eyebrow">Identity attribute</p>
                        <h3 className="mt-1 text-lg font-medium">{attr.label}</h3>
                      </div>
                      <span className="font-mono text-[10px] text-signal border border-signal/30 bg-signal/5 px-2 py-1 rounded-full">
                        w = {attr.weight}
                      </span>
                    </div>
                    <div>
                      <p className="label-eyebrow mb-2">Observable markers</p>
                      <ul className="space-y-2">
                        {attr.markers.map((m) => (
                          <li
                            key={m.id}
                            className="flex items-center gap-2 text-sm text-muted-foreground"
                          >
                            <Check className="h-3.5 w-3.5 text-signal shrink-0" strokeWidth={2} />
                            {m.label}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl border border-border bg-secondary/60 p-4 font-mono text-[11px] text-muted-foreground">
                Extracted from your answers · consent moment · you can edit later via
                Identity Evolution (Weekly Report)
              </div>

              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  onClick={() => navigate({ to: "/dashboard" })}
                  className="inline-flex items-center gap-2 rounded-full bg-foreground px-7 py-3.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors"
                >
                  Confirm & enter Trellis
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  onClick={() => {
                    setPhase("chat");
                    setQIndex(0);
                    setAnswers([]);
                    setMessages([
                      {
                        id: "m0r",
                        role: "ai",
                        text: "No problem — let's start again. Who are you trying to become?",
                      },
                    ]);
                  }}
                  className="rounded-full border border-border px-6 py-3.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Edit answers
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
