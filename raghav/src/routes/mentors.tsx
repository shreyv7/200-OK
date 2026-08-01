import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useUser } from "@clerk/react";
import { RequireAuth } from "@/authentication";
import { AppShell } from "@/components/trellis/AppShell";
import { useTrellis } from "@/lib/trellis/store";
import { motion, AnimatePresence } from "motion/react";
import {
  Users,
  Sparkles,
  MessageSquare,
  Flame,
  CheckCircle2,
  Send,
  Award,
  BookOpen,
  ArrowUpRight,
  ShieldCheck,
  UserCheck,
  X,
} from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/mentors")({
  head: () => ({
    meta: [
      { title: "Experts & Guides — Trellis" },
      {
        name: "description",
        content:
          "Bottleneck-matched mentors, AI advisor Q&A, and community growth stories.",
      },
      { property: "og:title", content: "Experts & Guides — Trellis" },
    ],
  }),
  component: MentorsRoute,
});

const ease = [0.16, 1, 0.3, 1] as const;

function MentorsRoute() {
  return (
    <RequireAuth>
      <MentorsPage />
    </RequireAuth>
  );
}

interface ExpertProfile {
  id: string;
  name: string;
  role: string;
  avatar: string;
  bottleneckCategory: "shipping" | "speaking" | "focus";
  startingGap: number;
  currentGap: number;
  breakthroughHabit: string;
  relevanceMatch: number;
  verifiedEvidence: string;
  storyQuote: string;
}

const EXPERTS: ExpertProfile[] = [
  {
    id: "exp_1",
    name: "Arjun Mehta",
    role: "Full-Stack Builder & Creator",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
    bottleneckCategory: "shipping",
    startingGap: 82,
    currentGap: 14,
    breakthroughHabit: "Committed 5 lines of code daily before checking social feeds.",
    relevanceMatch: 96,
    verifiedEvidence: "42 Commits Merged · 8 Products Shipped",
    storyQuote: "I spent 2 years tutorial-hoarding. Shipping a broken MVP on day 1 changed everything.",
  },
  {
    id: "exp_2",
    name: "Dr. Maya Lin",
    role: "AI Researcher & Speaker",
    avatar: "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
    bottleneckCategory: "speaking",
    startingGap: 76,
    currentGap: 18,
    breakthroughHabit: "Recorded a 60-second voice outline for every paper read.",
    relevanceMatch: 91,
    verifiedEvidence: "12 Keynote Talks · 15 Published Reviews",
    storyQuote: "Stage fright isn't a lack of talent; it's a lack of low-stakes micro-rehearsals.",
  },
  {
    id: "exp_3",
    name: "Vikram Rao",
    role: "Author & Systems Strategist",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
    bottleneckCategory: "focus",
    startingGap: 88,
    currentGap: 21,
    breakthroughHabit: "Scheduled 90-min phone-free focus blocks with local hard stops.",
    relevanceMatch: 88,
    verifiedEvidence: "180 Focus Hours · 3 Books Published",
    storyQuote: "You don't need 8 hours of discipline. You need 90 uninterrupted minutes.",
  },
];

interface ChatMessage {
  sender: "user" | "ai";
  text: string;
  timestamp: string;
}

function MentorsPage() {
  const { user } = useUser();
  const { gap } = useTrellis();
  const [selectedFilter, setSelectedFilter] = useState<"all" | "shipping" | "speaking" | "focus">("all");
  const [activeMentor, setActiveMentor] = useState<ExpertProfile>(EXPERTS[0]);
  const [chatInput, setChatInput] = useState("");
  const [isReplying, setIsReplying] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [growthStoryText, setGrowthStoryText] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      sender: "ai",
      text: `Hello ${user?.firstName || "friend"}! I am Arjun's AI Mentor Guide. I noticed your Identity Gap is currently ${gap.score}. What bottleneck are you facing with your shipping or focus today?`,
      timestamp: "Just now",
    },
  ]);

  const filteredExperts = EXPERTS.filter(
    (exp) => selectedFilter === "all" || exp.bottleneckCategory === selectedFilter
  );

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || chatInput;
    if (!textToSend.trim()) return;

    const newMsg: ChatMessage = {
      sender: "user",
      text: textToSend,
      timestamp: "Just now",
    };

    setChatMessages((prev) => [...prev, newMsg]);
    if (!queryText) setChatInput("");
    setIsReplying(true);

    setTimeout(() => {
      let aiReply = "";
      if (textToSend.toLowerCase().includes("doomscroll") || textToSend.toLowerCase().includes("focus")) {
        aiReply = `When I struggled with doomscrolling, I set a rule: never consume media during a declared focus window. Trellis logged a -2.0 drift penalty whenever I broke it, which forced me to swap 15 minutes of scrolling for a 2-minute micro-commit. Try executing a 60-second micro-action next time you feel the scroll urge!`;
      } else if (textToSend.toLowerCase().includes("ship") || textToSend.toLowerCase().includes("code")) {
        aiReply = `My breakthrough was lowering the bar to 5 lines of code. Don't try to build the complete architecture in one sitting. Push 1 tiny commit to GitHub today — that single action gives you +4.0 creation weight in your Revealed Self!`;
      } else {
        aiReply = `Based on your current Revealed Self evidence, your biggest leverage point right now is consistency over intensity. Focus on completing 1 micro-mission today rather than planning a 3-hour marathon.`;
      }

      setChatMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: aiReply,
          timestamp: "Just now",
        },
      ]);
      setIsReplying(false);
    }, 1000);
  };

  const handlePublishStory = () => {
    if (!growthStoryText.trim()) {
      toast.error("Please enter a short 1-line growth story");
      return;
    }
    toast.success("Growth Story published to the community network!");
    setModalOpen(false);
    setGrowthStoryText("");
  };

  return (
    <AppShell title="Experts & Guides">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease }}
        className="mx-auto max-w-5xl space-y-10 pb-24 font-mono"
      >
        {/* Page Header */}
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="label-eyebrow text-signal">Mentors & Guidance · F5C</p>
            <h1 className="mt-2 font-display text-3xl sm:text-4xl font-medium tracking-tight leading-[1.12]">
              Wisdom Matched to Your Bottleneck
            </h1>
            <p className="mt-3 text-sm text-muted-foreground max-w-lg leading-relaxed">
              Connect with guides who conquered the exact bottleneck holding you back. Mentorship is earned through verified evidence, not follower counts.
            </p>
          </div>

          {/* Architectural Mentor Verification Status */}
          <div className="shrink-0 rounded-2xl border border-border/60 bg-card/50 p-4 backdrop-blur-xl shadow-sm space-y-2.5 min-w-[280px]">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-medium text-foreground flex items-center gap-1.5">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-40" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-signal" />
                </span>
                Mentor Verification
              </span>
              <span className="text-signal font-semibold text-[11px]">78% Verified</span>
            </div>

            <div className="h-1 w-full rounded-full bg-secondary overflow-hidden">
              <div className="h-full rounded-full bg-signal w-[78%] transition-all duration-500" />
            </div>

            <div className="flex items-center justify-between pt-0.5">
              <span className="text-[10px] text-muted-foreground font-mono">
                21-day streak active
              </span>
              <button
                onClick={() => setModalOpen(true)}
                className="text-[11px] text-foreground font-medium hover:text-signal transition-colors flex items-center gap-1"
              >
                <span>Share Growth Story</span>
                <ArrowUpRight className="h-3 w-3 opacity-60" />
              </button>
            </div>
          </div>
        </div>

        {/* Bottleneck Filter Bar */}
        <div className="flex items-center gap-2 border-b border-border pb-4">
          <span className="text-xs text-muted-foreground uppercase tracking-wider mr-2">Filter by Bottleneck:</span>
          {[
            { id: "all", label: "All Experts" },
            { id: "shipping", label: "Shipping & Execution" },
            { id: "speaking", label: "Public Speaking" },
            { id: "focus", label: "Focus & Discipline" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedFilter(tab.id as any)}
              className={`rounded-2xl px-3.5 py-1.5 text-xs transition-all ${
                selectedFilter === tab.id
                  ? "bg-foreground text-background font-semibold shadow-sm"
                  : "bg-secondary/60 text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Section 1: Bottleneck-Matched Expert Cards */}
        <div className="space-y-4">
          <h2 className="font-display text-xl font-medium text-foreground">
            Bottleneck-Matched Mentors & Guides
          </h2>

          <div className="grid gap-6 md:grid-cols-3">
            {filteredExperts.map((exp) => (
              <div
                key={exp.id}
                onClick={() => setActiveMentor(exp)}
                className={`group cursor-pointer rounded-3xl border p-6 transition-all duration-300 flex flex-col justify-between ${
                  activeMentor.id === exp.id
                    ? "border-signal bg-card shadow-[0_8px_32px_rgba(200,137,43,0.08)] ring-1 ring-signal/50"
                    : "border-border bg-card/80 hover:border-border/80 hover:bg-card"
                }`}
              >
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <img
                      src={exp.avatar}
                      alt={exp.name}
                      className="h-12 w-12 rounded-2xl object-cover border border-border"
                    />
                    <span className="rounded-full bg-signal/15 border border-signal/30 px-2.5 py-1 text-[10px] font-bold text-signal uppercase">
                      {exp.relevanceMatch}% Bottleneck Match
                    </span>
                  </div>

                  <div>
                    <h3 className="font-display text-lg font-semibold text-foreground group-hover:text-signal transition-colors">
                      {exp.name}
                    </h3>
                    <p className="text-xs text-muted-foreground">{exp.role}</p>
                  </div>

                  <div className="rounded-2xl bg-secondary/40 p-3 text-xs space-y-1.5">
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                      <span>Gap Reduction:</span>
                      <span className="font-semibold text-foreground">
                        {exp.startingGap}% $\rightarrow$ {exp.currentGap}%
                      </span>
                    </div>
                    <p className="text-foreground text-[11px] leading-relaxed italic">
                      &ldquo;{exp.storyQuote}&rdquo;
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-border/60 flex items-center justify-between text-xs">
                  <span className="text-[10px] text-emerald-500 font-semibold flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3" />
                    {exp.verifiedEvidence.split("·")[0]}
                  </span>
                  <span className="text-signal font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                    Ask AI Twin <ArrowUpRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section 2: AI Mentor Q&A Advisor ("Talk to a Guide") */}
        <div className="rounded-3xl border border-border bg-card p-6 sm:p-8 space-y-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-signal/10 text-signal">
                <MessageSquare className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-display text-lg font-semibold text-foreground">
                  Talk to {activeMentor.name}&apos;s AI Mentor Twin
                </h3>
                <p className="text-xs text-muted-foreground">
                  Ask for advice on overcoming your current bottleneck ({activeMentor.role}).
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 font-semibold text-emerald-500 flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Revealed Self Context Connected
              </span>
            </div>
          </div>

          {/* Quick Prompt Chips */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-muted-foreground text-[11px] uppercase tracking-wider mr-1">Quick Prompts:</span>
            {[
              "How do I break doomscrolling before deep work?",
              "How do I ship my first MVP without overthinking?",
              "What micro-habit helped you close your Identity Gap?",
            ].map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(prompt)}
                className="rounded-2xl border border-border bg-secondary/30 px-3 py-1.5 text-xs text-foreground hover:border-signal/50 hover:bg-secondary transition-all"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Chat Messages Log */}
          <div className="space-y-4 max-h-80 overflow-y-auto rounded-2xl border border-border/60 bg-secondary/20 p-4 font-mono text-xs">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${
                  msg.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-lg rounded-2xl p-4 leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-foreground text-background"
                      : "bg-card border border-border text-foreground shadow-sm"
                  }`}
                >
                  <p className="text-xs font-semibold mb-1 opacity-70">
                    {msg.sender === "user" ? "You" : `${activeMentor.name}'s AI Guide`}
                  </p>
                  <p className="text-xs leading-relaxed">{msg.text}</p>
                </div>
              </div>
            ))}

            {isReplying && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 animate-spin text-signal" />
                <span>{activeMentor.name}&apos;s AI Guide is formulating advice...</span>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder={`Ask ${activeMentor.name} for advice on your current bottleneck...`}
              className="flex-1 rounded-2xl border border-border bg-background px-4 py-3 text-xs text-foreground placeholder:text-muted-foreground focus:border-signal focus:outline-none"
            />
            <button
              onClick={() => handleSendMessage()}
              className="rounded-2xl bg-foreground px-5 py-3 text-xs font-medium text-background hover:bg-foreground/90 transition-colors flex items-center gap-2"
            >
              <span>Ask</span>
              <Send className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Share Growth Story Modal */}
      <AnimatePresence>
        {modalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-mono">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md rounded-3xl border border-border bg-card p-6 shadow-xl space-y-5"
            >
              <div className="flex items-center justify-between border-b border-border/60 pb-3">
                <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
                  <Award className="h-4 w-4 text-signal" />
                  <span>Share Your 1-Line Growth Story</span>
                </div>
                <button
                  onClick={() => setModalOpen(false)}
                  className="rounded-xl p-1 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  What single micro-habit or mindset shift helped you close your Identity Gap?
                </p>
                <textarea
                  value={growthStoryText}
                  onChange={(e) => setGrowthStoryText(e.target.value)}
                  rows={3}
                  placeholder="e.g., I committed 5 lines of code every morning before opening email."
                  className="w-full rounded-2xl border border-border bg-background p-3 text-xs text-foreground placeholder:text-muted-foreground focus:border-signal focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setModalOpen(false)}
                  className="rounded-2xl border border-border px-4 py-2 text-xs text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  onClick={handlePublishStory}
                  className="rounded-2xl bg-foreground px-5 py-2 text-xs font-semibold text-background hover:bg-foreground/90 transition-colors"
                >
                  Publish Story
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </AppShell>
  );
}
