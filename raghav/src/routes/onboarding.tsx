import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Check } from "lucide-react";

import { RequireAuth } from "@/authentication";
import { LatticeMark } from "@/components/trellis/Lattice";
import { ApiError } from "@/lib/api/client";
import * as api from "@/lib/api/endpoints";
import { mapDeclaredSelf, type OnboardingDeclaredView } from "@/lib/api/mappers";
import type { ApiDeclaredSelf } from "@/lib/api/types";
import { useTrellis } from "@/lib/trellis/store";

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
  component: OnboardingPage,
});

function OnboardingPage() {
  return (
    <RequireAuth>
      <Onboarding />
    </RequireAuth>
  );
}

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

// ---------------------------------------------------------------------------
// Per-role question sets
// ---------------------------------------------------------------------------
const QUESTIONS_BY_ROLE: Record<string, Question[]> = {
  ai_builder: [
    {
      id: "aspiration",
      prompt: "What kind of AI product or system do you want to ship?",
      hint: "Aspiration — the Declared Self starts here.",
      options: [
        "A consumer-facing AI app with real users",
        "An internal tool that makes a team 10× faster",
        "An open-source model or dataset others build on",
      ],
    },
    {
      id: "why",
      prompt: "Why is shipping publicly important to you right now?",
      hint: "Urgency — what makes this week's gap costly.",
      options: [
        "I have a demo day or launch deadline approaching",
        "I keep building but never pressing the deploy button",
        "My side projects stay private and never get feedback",
      ],
    },
    {
      id: "habits",
      prompt: "What does a typical week look like for you?",
      hint: "Current habits — the Revealed Self baseline.",
      options: [
        "Mostly reading papers and docs, little building",
        "Building daily but rarely committing or deploying",
        "Prototyping fast but abandoning before shipping",
      ],
    },
    {
      id: "blocker",
      prompt: "What's the biggest thing holding you back from shipping?",
      hint: "Bottleneck seed — Curator will refine this later.",
      options: [
        "Fear the code isn't production-quality yet",
        "I get stuck on scope and never call it done",
        "No users or distribution to ship to",
      ],
    },
    {
      id: "capacity",
      prompt: "How much focused build time can you give this each day?",
      hint: "Guardian uses this to size every intervention.",
      options: [
        "15–30 minutes — small commits only",
        "30–90 minutes — a solid feature block",
        "2+ hours when the week allows",
      ],
    },
  ],
  keynote_speaker: [
    {
      id: "aspiration",
      prompt: "What kind of speaker do you want to be?",
      hint: "Aspiration — the Declared Self starts here.",
      options: [
        "A technical keynote speaker at developer conferences",
        "A motivational speaker who moves non-technical audiences",
        "A panel expert and podcast guest who shapes discourse",
      ],
    },
    {
      id: "why",
      prompt: "Why does being heard publicly matter right now?",
      hint: "Urgency — what makes this week's gap costly.",
      options: [
        "I have a talk or presentation coming up I'm not ready for",
        "I have ideas worth sharing but no platform yet",
        "I freeze when presenting to any group, even small ones",
      ],
    },
    {
      id: "habits",
      prompt: "How often do you practice speaking out loud?",
      hint: "Current habits — the Revealed Self baseline.",
      options: [
        "Almost never — I rehearse only in my head",
        "Occasionally, but only when a talk is imminent",
        "I record myself but rarely review the footage",
      ],
    },
    {
      id: "blocker",
      prompt: "What's the biggest wall between you and the stage?",
      hint: "Bottleneck seed — Curator will refine this later.",
      options: [
        "Fear of being judged or looking unprepared",
        "I can't structure my ideas into a clear narrative",
        "I don't know how to get booked or find opportunities",
      ],
    },
    {
      id: "capacity",
      prompt: "How much time can you give to speaking practice each day?",
      hint: "Guardian uses this to size every intervention.",
      options: [
        "5–15 minutes — a voice note or short recording",
        "15–30 minutes — a structured rehearsal session",
        "30+ minutes — full run-throughs with notes",
      ],
    },
  ],
  technical_author: [
    {
      id: "aspiration",
      prompt: "What kind of writing do you want to be known for?",
      hint: "Aspiration — the Declared Self starts here.",
      options: [
        "In-depth technical tutorials and how-to guides",
        "Research-backed essays and long-form analysis",
        "A newsletter or blog with a consistent publishing cadence",
      ],
    },
    {
      id: "why",
      prompt: "Why does consistent publishing matter to you now?",
      hint: "Urgency — what makes this week's gap costly.",
      options: [
        "I have drafts sitting unfinished for months",
        "I want to build an audience but have nothing public",
        "I'm building expertise but leaving no written record",
      ],
    },
    {
      id: "habits",
      prompt: "How does your writing process actually look today?",
      hint: "Current habits — the Revealed Self baseline.",
      options: [
        "I research extensively but rarely start writing",
        "I start drafts but abandon them before publishing",
        "I write privately in notes that never see daylight",
      ],
    },
    {
      id: "blocker",
      prompt: "What stops you from hitting publish?",
      hint: "Bottleneck seed — Curator will refine this later.",
      options: [
        "The draft never feels good enough to share",
        "I run out of time before finishing a piece",
        "I'm not sure my ideas are worth an audience's time",
      ],
    },
    {
      id: "capacity",
      prompt: "How much writing time can you commit each day?",
      hint: "Guardian uses this to size every intervention.",
      options: [
        "10–20 minutes — one paragraph or outline block",
        "20–45 minutes — a focused writing session",
        "45+ minutes when the schedule allows",
      ],
    },
  ],
  product_designer: [
    {
      id: "aspiration",
      prompt: "What kind of designer do you want to become?",
      hint: "Aspiration — the Declared Self starts here.",
      options: [
        "A product designer who shapes full user experiences end-to-end",
        "A UI specialist known for polished, precise visual systems",
        "A design systems architect whose components teams ship with",
      ],
    },
    {
      id: "why",
      prompt: "Why is building a design portfolio urgent for you now?",
      hint: "Urgency — what makes this week's gap costly.",
      options: [
        "I'm job-hunting and have nothing to show a recruiter",
        "I design at work but own nothing I can share publicly",
        "I want to go freelance but lack credible case studies",
      ],
    },
    {
      id: "habits",
      prompt: "How does your design practice look this week?",
      hint: "Current habits — the Revealed Self baseline.",
      options: [
        "Mostly consuming Dribbble and design Twitter, not creating",
        "Designing in Figma but never sharing or publishing pieces",
        "Starting redesign exercises but not finishing them",
      ],
    },
    {
      id: "blocker",
      prompt: "What's the gap between designing and shipping design?",
      hint: "Bottleneck seed — Curator will refine this later.",
      options: [
        "I polish endlessly and never call the design done",
        "I don't know how to document and present case studies",
        "I design in isolation with no feedback loop",
      ],
    },
    {
      id: "capacity",
      prompt: "How much intentional design time can you give each day?",
      hint: "Guardian uses this to size every intervention.",
      options: [
        "15–30 minutes — one focused component or screen",
        "30–60 minutes — a meaningful design iteration",
        "60+ minutes for deeper explorations",
      ],
    },
  ],
  polymath: [
    {
      id: "aspiration",
      prompt: "Which disciplines do you want to synthesise?",
      hint: "Aspiration — the Declared Self starts here.",
      options: [
        "Technology + philosophy + systems thinking",
        "Science + history + creative writing",
        "Economics + psychology + design",
      ],
    },
    {
      id: "why",
      prompt: "Why does deep cross-domain knowledge matter to you now?",
      hint: "Urgency — what makes this week's gap costly.",
      options: [
        "I consume a lot but can't connect ideas across fields yet",
        "I want to write or speak in a way that bridges disciplines",
        "I sense I think shallowly in each domain without linking them",
      ],
    },
    {
      id: "habits",
      prompt: "How does your learning week actually look today?",
      hint: "Current habits — the Revealed Self baseline.",
      options: [
        "Wide reading, but no synthesis or note-making between books",
        "Deep in one topic for weeks, then jumping to something else",
        "Lots of podcasts and videos, little structured reflection",
      ],
    },
    {
      id: "blocker",
      prompt: "What prevents you from integrating knowledge deeply?",
      hint: "Bottleneck seed — Curator will refine this later.",
      options: [
        "I consume but never write up my synthesis",
        "My notes are scattered and I can't connect them",
        "I go too broad and never reach genuine depth in anything",
      ],
    },
    {
      id: "capacity",
      prompt: "How much deep-work time can you give each day?",
      hint: "Guardian uses this to size every intervention.",
      options: [
        "20–30 minutes — one focused reading or note session",
        "30–60 minutes — structured study with reflection",
        "60+ minutes of uninterrupted synthesis work",
      ],
    },
  ],
};

// ---------------------------------------------------------------------------
// The 5 Future-Me persona options shown in the role modal
// ---------------------------------------------------------------------------
interface PersonaOption {
  id: string;
  icon: string;
  title: string;
  badge: string;
}

const PERSONA_OPTIONS: PersonaOption[] = [
  { id: "ai_builder",       icon: "🚀", title: "AI Product Builder & Founder",    badge: "Shipping & Code Focus" },
  { id: "keynote_speaker",  icon: "🎤", title: "Keynote Speaker & Public Advocate", badge: "Stage & Communication Focus" },
  { id: "technical_author", icon: "✍️",  title: "Technical Author & Researcher",   badge: "Writing & Research Focus" },
  { id: "product_designer", icon: "🎨", title: "Product Designer & UI Creator",    badge: "Design Systems & UX Focus" },
  { id: "polymath",         icon: "🧠", title: "Polymath & Discipline Scholar",    badge: "Deep Work & Habits Focus" },
];

type Phase = "chat" | "extracting" | "confirm";

function Onboarding() {
  const navigate = useNavigate();
  const { selectPersona } = useTrellis();

  // ── Role modal ──────────────────────────────────────────────────────────────
  const [roleModalOpen, setRoleModalOpen] = useState(true);
  const [activePersonaId, setActivePersonaId] = useState<string>("ai_builder");
  const [activeQuestions, setActiveQuestions] = useState<Question[]>(
    QUESTIONS_BY_ROLE["ai_builder"]!,
  );

  // ── Chat state ──────────────────────────────────────────────────────────────
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
      text: QUESTIONS_BY_ROLE["ai_builder"]![0]!.prompt,
    },
  ]);
  const [typing, setTyping] = useState(false);
  const [draftApi, setDraftApi] = useState<ApiDeclaredSelf | null>(null);
  const [draftDeclared, setDraftDeclared] = useState<OnboardingDeclaredView | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing, phase]);

  // ── Role selection ──────────────────────────────────────────────────────────
  const handleSelectRole = (persona: PersonaOption) => {
    const qs = QUESTIONS_BY_ROLE[persona.id] ?? QUESTIONS_BY_ROLE["ai_builder"]!;
    setActivePersonaId(persona.id);
    setActiveQuestions(qs);
    setRoleModalOpen(false);
    setPhase("chat");
    setQIndex(0);
    setAnswers([]);
    setDraftApi(null);
    setDraftDeclared(null);
    setConfirmError(null);
    // Tell global store which persona was selected
    selectPersona(persona.id);
    setMessages([
      {
        id: "m0",
        role: "ai",
        text: `Great choice — let's build your Declared Self for: ${persona.title}. I'll ask five focused questions.`,
      },
      {
        id: "m1",
        role: "ai",
        text: qs[0]!.prompt,
      },
    ]);
  };

  const currentQ = activeQuestions[qIndex]!;

  // ── Answer selection ────────────────────────────────────────────────────────
  const selectAnswer = (answer: string) => {
    if (typing || phase !== "chat") return;

    const nextAnswers = [...answers, answer];
    setAnswers(nextAnswers);
    setMessages((prev) => [
      ...prev,
      { id: `u_${qIndex}`, role: "user", text: answer },
    ]);

    const nextIndex = qIndex + 1;
    if (nextIndex < activeQuestions.length) {
      setTyping(true);
      setTimeout(() => {
        setTyping(false);
        setQIndex(nextIndex);
        setMessages((prev) => [
          ...prev,
          {
            id: `a_${nextIndex}`,
            role: "ai",
            text: activeQuestions[nextIndex]!.prompt,
          },
        ]);
      }, 700);
    } else {
      setTyping(true);
      setTimeout(() => {
        void (async () => {
          try {
            const boot = await api.onboardingTurn({ sessionId: null, message: "" });
            let sessionId = boot.sessionId;
            let draft: ApiDeclaredSelf | null = null;

            for (const msg of nextAnswers) {
              const turn = await api.onboardingTurn({ sessionId, message: msg });
              sessionId = turn.sessionId;
              if (turn.draft) draft = turn.draft;
            }

            if (draft) {
              setDraftApi(draft);
              setDraftDeclared(mapDeclaredSelf(draft));
              setConfirmError(null);
            } else {
              setConfirmError(
                "Could not extract a Declared Self from your answers. Try again.",
              );
            }
          } catch (err) {
            setConfirmError(
              err instanceof ApiError
                ? err.message
                : "Onboarding extraction failed. Try again.",
            );
          }
          setTyping(false);
          setPhase("extracting");
          setTimeout(() => setPhase("confirm"), 1200);
        })();
      }, 500);
    }
  };

  // ── Confirm & enter ─────────────────────────────────────────────────────────
  const confirmAndEnter = async () => {
    if (confirming) return;
    setConfirmError(null);

    const attributes = draftApi?.attributes ?? [];
    if (!attributes.length) {
      setConfirmError("Nothing to confirm yet — finish the interview first.");
      return;
    }

    setConfirming(true);
    try {
      await api.patchIdentity({ attributes, confirm: true });
      void navigate({ to: "/dashboard", replace: true });
    } catch (err) {
      setConfirmError(
        err instanceof ApiError ? err.message : "Could not confirm identity.",
      );
      setConfirming(false);
    }
  };

  const declared = draftDeclared ?? { headline: "", attributes: [] };

  return (
    <div className="relative min-h-screen text-foreground overflow-x-hidden">
      {/* ── Role Selection Modal ─────────────────────────────────────────────── */}
      <AnimatePresence>
        {roleModalOpen && (
          <motion.div
            key="role-modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4"
          >
            <motion.div
              key="role-modal-card"
              initial={{ scale: 0.96, opacity: 0, y: 8 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.96, opacity: 0, y: 8 }}
              transition={{ duration: 0.3, ease }}
              className="w-full max-w-md rounded-3xl border border-border bg-card p-6 shadow-2xl"
            >
              <div className="mb-5 space-y-1">
                <p className="label-eyebrow text-signal">Choose Target Role</p>
                <h2 className="font-display text-2xl font-medium tracking-tight">
                  Who do you want to become?
                </h2>
                <p className="text-xs text-muted-foreground">
                  Select your target archetype. Your interview questions will be tailored to this goal.
                </p>
              </div>

              <div className="space-y-2">
                {PERSONA_OPTIONS.map((persona) => (
                  <button
                    key={persona.id}
                    type="button"
                    onClick={() => handleSelectRole(persona)}
                    className="group w-full text-left rounded-2xl border border-border/80 bg-background/60 px-4 py-3.5 hover:border-signal/50 hover:bg-signal/5 transition-all flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{persona.icon}</span>
                      <div>
                        <p className="text-sm font-medium text-foreground group-hover:text-signal transition-colors">
                          {persona.title}
                        </p>
                        <p className="font-mono text-[10px] text-muted-foreground">
                          {persona.badge}
                        </p>
                      </div>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
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

      {/* ── Main chat ───────────────────────────────────────────────────────── */}
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

              <div className="flex items-center gap-2">
                {activeQuestions.map((q, i) => (
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
                  {declared.headline || "Your Declared Self"}
                </h1>
                <p className="mt-3 text-sm text-muted-foreground max-w-lg">
                  Confirm this Declared Self. Trellis will measure your behaviour
                  against these markers — nothing changes without your consent.
                </p>
              </div>

              {confirmError && (
                <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-4 font-mono text-xs text-destructive">
                  {confirmError}
                </div>
              )}

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

              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  onClick={() => void confirmAndEnter()}
                  disabled={confirming || !draftApi}
                  className="inline-flex items-center gap-2 rounded-full bg-foreground px-7 py-3.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors disabled:opacity-50"
                >
                  {confirming ? "Confirming…" : "Confirm & enter Trellis"}
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  onClick={() => {
                    setPhase("chat");
                    setQIndex(0);
                    setAnswers([]);
                    setDraftApi(null);
                    setDraftDeclared(null);
                    setConfirmError(null);
                    setMessages([
                      {
                        id: "m0r",
                        role: "ai",
                        text: "No problem — let's start again. " + activeQuestions[0]!.prompt,
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
