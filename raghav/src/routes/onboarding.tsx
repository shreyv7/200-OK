import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Check, Mic, MicOff, Send } from "lucide-react";

import { RequireAuth } from "@/authentication";
import { LatticeMark } from "@/components/trellis/Lattice";
import { useSpeechToText } from "@/hooks/useSpeechToText";
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
}

const PERSONA_OPTIONS: PersonaOption[] = [
  { id: "ai_builder",       icon: "🚀", title: "AI Product Builder & Founder" },
  { id: "keynote_speaker",  icon: "🎤", title: "Keynote Speaker & Public Advocate" },
  { id: "technical_author", icon: "✍️",  title: "Technical Author & Researcher" },
  { id: "product_designer", icon: "🎨", title: "Product Designer & UI Creator" },
  { id: "polymath",         icon: "🧠", title: "Polymath & Discipline Scholar" },
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
  const [answers, setAnswers] = useState<
    Array<{ text: string; kind: "preset" | "freeform" }>
  >([]);
  const [customAnswer, setCustomAnswer] = useState("");
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
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const speechBaseRef = useRef("");

  const {
    supported: speechSupported,
    listening,
    error: speechError,
    toggle: toggleListening,
    stop: stopListening,
  } = useSpeechToText({
    lang: "en-US",
    continuous: true,
    onResult: (transcript, isFinal) => {
      const base = speechBaseRef.current;
      const joined = [base, transcript].filter(Boolean).join(" ").trim();
      setCustomAnswer(joined.slice(0, 2000));
      if (isFinal) {
        speechBaseRef.current = joined.slice(0, 2000);
      }
    },
  });

  useEffect(() => {
    const el = chatScrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, typing, phase]);

  useEffect(() => {
    if (phase !== "chat" || typing) return;
    const id = window.setTimeout(() => textareaRef.current?.focus(), 120);
    return () => window.clearTimeout(id);
  }, [phase, typing, qIndex]);

  useEffect(() => {
    // Fresh utterance base whenever the question changes
    speechBaseRef.current = "";
    stopListening();
  }, [qIndex, stopListening]);

  // ── Role selection ──────────────────────────────────────────────────────────
  const handleSelectRole = (persona: PersonaOption) => {
    const qs = QUESTIONS_BY_ROLE[persona.id] ?? QUESTIONS_BY_ROLE["ai_builder"]!;
    setActivePersonaId(persona.id);
    setActiveQuestions(qs);
    setRoleModalOpen(false);
    setPhase("chat");
    setQIndex(0);
    setAnswers([]);
    setCustomAnswer("");
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
  const trimmedCustom = customAnswer.trim();
  const canSubmitCustom = trimmedCustom.length >= 2 && !typing && phase === "chat";

  // ── Answer selection ────────────────────────────────────────────────────────
  const selectAnswer = (answer: string, kind: "preset" | "freeform") => {
    const cleaned = answer.trim();
    if (!cleaned || typing || phase !== "chat") return;

    const nextAnswers = [...answers, { text: cleaned, kind }];
    setAnswers(nextAnswers);
    setCustomAnswer("");
    speechBaseRef.current = "";
    stopListening();
    setMessages((prev) => [
      ...prev,
      { id: `u_${qIndex}`, role: "user", text: cleaned },
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

            for (const entry of nextAnswers) {
              const turn = await api.onboardingTurn({
                sessionId,
                message: entry.text,
                answerKind: entry.kind,
              });
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

  const submitCustomAnswer = (event?: FormEvent) => {
    event?.preventDefault();
    if (!canSubmitCustom) return;
    selectAnswer(trimmedCustom, "freeform");
  };

  const skipQuestion = () => {
    if (typing || phase !== "chat") return;
    selectAnswer("Skipped", "freeform");
  };

  const onCustomKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submitCustomAnswer();
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
    <div className="relative flex h-dvh flex-col overflow-hidden text-foreground">
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
              className="w-full max-w-lg rounded-[1.75rem] border border-border bg-card p-7 sm:p-8 shadow-2xl"
            >
              <div className="mb-6 space-y-2">
                <p className="label-eyebrow text-signal">Choose Target Role</p>
                <h2 className="font-display text-3xl sm:text-[2.15rem] font-bold tracking-tight leading-[1.1]">
                  Who do you want to become?
                </h2>
              </div>

              <div className="space-y-2.5">
                {PERSONA_OPTIONS.map((persona) => (
                  <button
                    key={persona.id}
                    type="button"
                    onClick={() => handleSelectRole(persona)}
                    className="group w-full text-left rounded-2xl border border-border/80 bg-background/60 px-5 py-4 hover:border-signal/50 hover:bg-signal/5 transition-all flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3.5">
                      <span className="text-xl">{persona.icon}</span>
                      <p className="text-base font-semibold text-foreground group-hover:text-signal transition-colors">
                        {persona.title}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <header className="z-40 shrink-0 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-4xl items-center px-5 py-3">
          <div className="flex items-center gap-2.5">
            <LatticeMark className="h-4 w-4" />
            <span className="font-mono text-[11px] font-semibold tracking-[0.24em] uppercase">
              TRELLIS
            </span>
          </div>
        </div>
      </header>

      <main className="relative z-10 flex min-h-0 w-full flex-1 overflow-hidden">
        {/* Extreme-left stacked wordmark — absolute so it never eats vertical space */}
        {(phase === "chat" || phase === "extracting") && (
          <aside
            aria-hidden
            className="pointer-events-none absolute left-3 top-3 z-0 sm:left-5 sm:top-4"
          >
            <p className="font-old-italic text-[clamp(2.75rem,8vw,5.5rem)] leading-[0.8] tracking-[-0.03em]">
              <span className="block text-foreground">The</span>
              <span className="my-[0.12em] block h-px w-full bg-foreground" aria-hidden />
              <span className="block text-signal">Mirror</span>
            </p>
          </aside>
        )}

        {/* Extreme-right golden question counter */}
        {(phase === "chat" || phase === "extracting") && (
          <aside
            className="pointer-events-none absolute right-3 top-1/2 z-0 -translate-y-1/2 sm:right-6 lg:right-10"
            aria-label={`Question ${Math.min(qIndex + 1, activeQuestions.length)} of ${activeQuestions.length}`}
          >
            <div className="relative flex h-[clamp(7.5rem,18vw,11rem)] w-[clamp(7.5rem,18vw,11rem)] items-center justify-center rounded-full border-[3px] border-signal">
              <div
                aria-hidden
                className="absolute inset-2 rounded-full border border-signal/25"
              />
              <p className="relative font-display text-[clamp(1.75rem,4.5vw,2.75rem)] font-bold leading-none tracking-tight text-signal">
                <span>
                  {phase === "extracting"
                    ? activeQuestions.length
                    : Math.min(qIndex + 1, activeQuestions.length)}
                </span>
                <span className="text-signal/45">/</span>
                <span>{activeQuestions.length}</span>
              </p>
            </div>
          </aside>
        )}

        <div className="relative z-10 mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col px-4 sm:px-6 py-3 sm:py-4">
        <AnimatePresence mode="wait">
          {phase === "chat" || phase === "extracting" ? (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.4, ease }}
              className="flex min-h-0 flex-1 flex-col gap-3"
            >
              <div className="shrink-0 space-y-2.5">
                <div className="pl-[min(28vw,8.5rem)] sm:pl-[min(22vw,9.5rem)]">
                  <h1 className="font-display text-xl sm:text-2xl font-bold tracking-tight leading-[1.15]">
                    Tell me who you&apos;re becoming.
                  </h1>
                </div>
                <div className="flex items-center gap-2">
                  {activeQuestions.map((q, i) => (
                    <div
                      key={q.id}
                      className={`h-1 flex-1 rounded-full transition-colors ${
                        i < answers.length
                          ? "bg-signal"
                          : i === qIndex && phase === "chat"
                            ? "bg-foreground/35"
                            : "bg-border"
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Card fills leftover viewport; composer pinned; middle scrolls */}
              <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-card">
                <div
                  ref={chatScrollRef}
                  className="min-h-0 flex-1 space-y-2.5 overflow-y-auto overscroll-contain px-4 py-3 sm:px-5"
                >
                  {messages.map((m) => (
                    <motion.div
                      key={m.id}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, ease }}
                      className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[92%] rounded-2xl px-3.5 py-2.5 text-sm font-semibold leading-relaxed ${
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
                      <div className="rounded-2xl rounded-bl-md bg-secondary px-3.5 py-2.5 font-mono text-xs text-muted-foreground">
                        Thinking…
                      </div>
                    </div>
                  )}
                  {phase === "extracting" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="rounded-xl border border-signal/30 bg-signal/5 p-3.5 font-mono text-xs space-y-1.5"
                    >
                      <p className="text-signal uppercase tracking-[0.16em]">
                        Extracting Declared Self…
                      </p>
                      <p className="text-muted-foreground">
                        Mapping answers → identity attributes → markers
                      </p>
                    </motion.div>
                  )}
                </div>

                {phase === "chat" && !typing && (
                  <div className="shrink-0 border-t border-border bg-card px-4 py-3 sm:px-5 space-y-2.5">
                    <div>
                      <p className="text-base sm:text-lg font-semibold tracking-tight leading-snug">
                        {currentQ.prompt}
                      </p>
                    </div>

                    <div className="max-h-[28vh] space-y-1.5 overflow-y-auto overscroll-contain">
                      {currentQ.options.map((opt) => (
                        <button
                          key={opt}
                          type="button"
                          onClick={() => selectAnswer(opt, "preset")}
                          className="group w-full text-left rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground transition-all hover:border-signal/50 hover:bg-signal/5"
                        >
                          <span className="flex items-center justify-between gap-2">
                            <span className="leading-snug">{opt}</span>
                            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                          </span>
                        </button>
                      ))}
                    </div>

                    <form onSubmit={submitCustomAnswer} className="space-y-2">
                      <div className="flex items-end gap-2">
                        <div className="relative min-w-0 flex-1">
                          <textarea
                            id="mirror-custom-answer"
                            ref={textareaRef}
                            value={customAnswer}
                            onChange={(e) => {
                              const next = e.target.value.slice(0, 2000);
                              setCustomAnswer(next);
                              speechBaseRef.current = next;
                            }}
                            onKeyDown={onCustomKeyDown}
                            rows={2}
                            maxLength={2000}
                            placeholder="Optional — type your own answer here…"
                            className="min-h-[3rem] max-h-24 w-full resize-none rounded-xl border border-border bg-background px-3.5 py-2.5 pr-14 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground/70 outline-none transition-colors focus:border-foreground/25 focus:ring-2 focus:ring-foreground/10"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              if (!listening) {
                                speechBaseRef.current = customAnswer.trim();
                              }
                              toggleListening();
                            }}
                            disabled={!speechSupported}
                            title={
                              !speechSupported
                                ? "Voice input not supported in this browser"
                                : listening
                                  ? "Stop listening"
                                  : "Speak your answer"
                            }
                            aria-label={listening ? "Stop voice input" : "Start voice input"}
                            className={`absolute top-1/2 right-2.5 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full transition-colors ${
                              listening
                                ? "bg-signal text-white"
                                : "bg-secondary text-foreground hover:bg-foreground/10"
                            } disabled:cursor-not-allowed disabled:opacity-40`}
                          >
                            {listening ? (
                              <MicOff className="h-4.5 w-4.5" strokeWidth={2.25} />
                            ) : (
                              <Mic className="h-4.5 w-4.5" strokeWidth={2.25} />
                            )}
                          </button>
                        </div>
                        <div className="flex shrink-0 flex-col items-stretch gap-1.5">
                          <button
                            type="button"
                            onClick={skipQuestion}
                            disabled={typing}
                            className="inline-flex items-center justify-center rounded-full border border-border px-4 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:border-foreground/20 hover:text-foreground disabled:opacity-40"
                          >
                            Skip
                          </button>
                          <button
                            type="submit"
                            disabled={!canSubmitCustom}
                            className="inline-flex items-center justify-center gap-1.5 rounded-full bg-foreground px-4 py-2.5 text-sm font-semibold text-background transition-colors hover:bg-foreground/90 disabled:opacity-40"
                          >
                            Continue
                            <Send className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                      {(listening || speechError) && (
                        <p className="font-mono text-[10px] text-muted-foreground">
                          {listening ? "Listening… tap the mic to stop" : ""}
                          {speechError
                            ? `${listening ? " · " : ""}${speechError}`
                            : ""}
                        </p>
                      )}
                    </form>
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
              className="flex min-h-0 flex-1 flex-col gap-5"
            >
              <div className="shrink-0">
                <p className="label-eyebrow text-signal">Did I get you right?</p>
                <h1 className="mt-2 font-display text-3xl sm:text-4xl font-bold tracking-tight leading-[1.08]">
                  {declared.headline || "Your Declared Self"}
                </h1>
                <p className="mt-3 text-base sm:text-lg text-muted-foreground max-w-2xl leading-relaxed">
                  Confirm this Declared Self. Trellis will measure your behaviour
                  against these markers — nothing changes without your consent.
                </p>
              </div>

              {confirmError && (
                <div className="shrink-0 rounded-2xl border border-destructive/30 bg-destructive/10 p-5 font-mono text-sm text-destructive">
                  {confirmError}
                </div>
              )}

              <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
                <div className="grid gap-4 sm:grid-cols-2">
                  {declared.attributes.map((attr) => (
                    <div
                      key={attr.id}
                      className="rounded-[1.5rem] border border-border bg-card p-6 sm:p-7 space-y-4"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="label-eyebrow">Identity attribute</p>
                          <h3 className="mt-1.5 text-xl font-semibold tracking-tight">
                            {attr.label}
                          </h3>
                        </div>
                        <span className="font-mono text-[11px] text-signal border border-signal/30 bg-signal/5 px-2.5 py-1 rounded-full">
                          {Math.round(attr.weight * 100)}%
                        </span>
                      </div>
                      <div>
                        <p className="label-eyebrow mb-2.5">Observable markers</p>
                        <ul className="space-y-2.5">
                          {attr.markers.map((m) => (
                            <li
                              key={m.id}
                              className="flex items-center gap-2.5 text-base text-muted-foreground"
                            >
                              <Check className="h-4 w-4 text-signal shrink-0" strokeWidth={2} />
                              {m.label}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex shrink-0 flex-wrap gap-3 pt-1">
                <button
                  onClick={() => void confirmAndEnter()}
                  disabled={confirming || !draftApi}
                  className="inline-flex items-center gap-2 rounded-full bg-foreground px-8 py-4 text-base font-semibold text-background hover:bg-foreground/90 transition-colors disabled:opacity-50"
                >
                  {confirming ? "Confirming…" : "Confirm & enter Trellis"}
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  onClick={() => {
                    setPhase("chat");
                    setQIndex(0);
                    setAnswers([]);
                    setCustomAnswer("");
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
                  className="rounded-full border border-border px-7 py-4 text-base text-muted-foreground hover:text-foreground transition-colors"
                >
                  Edit answers
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
