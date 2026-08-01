import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Check } from "lucide-react";

import { RequireAuth } from "@/authentication";
import { LatticeMark } from "@/components/trellis/Lattice";
import { ApiError } from "@/lib/api/client";
import * as api from "@/lib/api/endpoints";
import { mapDeclaredSelf, type OnboardingDeclaredView } from "@/lib/api/mappers";
import type {
  ApiDeclaredSelf,
  ApiOnboardingPersona,
  ApiOnboardingQuestion,
} from "@/lib/api/types";

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

const DEFAULT_QUESTIONS: ApiOnboardingQuestion[] = [
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

type Phase = "persona" | "chat" | "extracting" | "confirm";

function Onboarding() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("persona");
  const [qIndex, setQIndex] = useState(0);
  const [personas, setPersonas] = useState<ApiOnboardingPersona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<ApiOnboardingPersona | null>(null);
  const [questions, setQuestions] = useState<ApiOnboardingQuestion[]>(DEFAULT_QUESTIONS);
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
      text: DEFAULT_QUESTIONS[0]!.prompt,
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

  useEffect(() => {
    void api.getOnboardingPersonas().then(setPersonas).catch(() => setPersonas([]));
  }, []);

  const currentQ = questions[qIndex]!;

  const selectPersona = (persona: ApiOnboardingPersona | null) => {
    const nextQuestions = persona?.questions ?? DEFAULT_QUESTIONS;
    setSelectedPersona(persona);
    setQuestions(nextQuestions);
    setQIndex(0);
    setAnswers([]);
    setMessages([
      {
        id: "m0",
        role: "ai",
        text: persona
          ? `We'll start with your ${persona.title} path. This is a starting point, not a label — you will confirm the identity I extract.`
          : "I'm going to ask a few short questions — not personality adjectives, but things that show up as behaviour.",
      },
      { id: "m1", role: "ai", text: nextQuestions[0]!.prompt },
    ]);
    setPhase("chat");
  };

  const selectAnswer = (answer: string) => {
    if (typing || phase !== "chat") return;

    const nextAnswers = [...answers, answer];
    setAnswers(nextAnswers);
    setMessages((prev) => [
      ...prev,
      { id: `u_${qIndex}`, role: "user", text: answer },
    ]);

    const nextIndex = qIndex + 1;
    if (nextIndex < questions.length) {
      setTyping(true);
      setTimeout(() => {
        setTyping(false);
        setQIndex(nextIndex);
        setMessages((prev) => [
          ...prev,
          {
            id: `a_${nextIndex}`,
            role: "ai",
            text: questions[nextIndex]!.prompt,
          },
        ]);
      }, 700);
    } else {
      setTyping(true);
      setTimeout(() => {
        void (async () => {
          try {
            const boot = await api.onboardingTurn({ sessionId: null, message: "", personaId: selectedPersona?.id ?? null });
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
          {phase === "persona" ? (
            <motion.section
              key="persona"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease }}
              className="space-y-6"
            >
              <div>
                <p className="label-eyebrow text-signal">Choose a starting path</p>
                <h1 className="mt-2 font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.1]">
                  What kind of growth are you working toward?
                </h1>
                <p className="mt-3 max-w-xl text-sm text-muted-foreground">
                  Pick a path to make the interview more useful. It does not define you;
                  you will review and confirm every identity marker before Trellis uses it.
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {personas.map((persona) => (
                  <button
                    key={persona.id}
                    onClick={() => selectPersona(persona)}
                    className="group rounded-3xl border border-border bg-card p-5 text-left transition-all hover:border-signal/50 hover:bg-signal/5"
                  >
                    <p className="label-eyebrow text-signal">Onboarding path</p>
                    <h2 className="mt-2 text-lg font-medium">{persona.title}</h2>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{persona.description}</p>
                    <p className="mt-4 font-mono text-[10px] text-muted-foreground">{persona.outcome}</p>
                  </button>
                ))}
              </div>
              <button
                onClick={() => selectPersona(null)}
                className="rounded-full border border-border px-5 py-3 text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Continue with a custom path
              </button>
            </motion.section>
          ) : phase === "chat" || phase === "extracting" ? (
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
                {questions.map((q, i) => (
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
