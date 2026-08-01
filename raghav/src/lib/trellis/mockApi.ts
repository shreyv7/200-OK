/** Lightweight local stubs for surfaces not yet wired to the live API.
 * Auth / onboarding / integrations use real backend calls (A4–A5 / D6).
 */

export const mock = {
  currentBottleneck: {
    name: "Focus Drift",
    diagnosis:
      "High passive consumption relative to output over the last 7 days.",
    confidence: "medium",
    evidence: [
      "Scroll sessions outweigh creation blocks",
      "Few ship markers in the evidence window",
      "Capacity is available but unused for public reps",
    ],
  },
  feedCards: [
    { id: "feed-1", kind: "low_value" as const, headline: "9 desk setups that will change your life", tag: "Trending" },
    { id: "feed-2", kind: "low_value" as const, headline: "He quit his job and now earns $40k/mo doing this", tag: "Hustle" },
    { id: "feed-3", kind: "neutral" as const, headline: "How compilers actually resolve generics", tag: "Engineering" },
    { id: "feed-4", kind: "low_value" as const, headline: "POV: it's 2am and you're still scrolling", tag: "Relatable" },
    { id: "feed-5", kind: "low_value" as const, headline: "The one morning routine every founder swears by", tag: "Productivity" },
    { id: "feed-6", kind: "low_value" as const, headline: "You won't believe what happened next", tag: "Clickbait" },
    { id: "feed-7", kind: "neutral" as const, headline: "A short read on writing clearer commit messages", tag: "Craft" },
    { id: "feed-8", kind: "low_value" as const, headline: "Rating overpriced gadgets nobody asked for", tag: "Trending" },
    { id: "feed-9", kind: "low_value" as const, headline: "This 15-second hack replaced my entire workflow", tag: "Hustle" },
    { id: "feed-10", kind: "neutral" as const, headline: "Notes from a talk on system design tradeoffs", tag: "Engineering" },
  ],
  weeklyNarrative: {
    arc: "From invisible preparation to one public rep",
    body: "Complete onboarding and connect evidence sources to generate a live weekly becoming report for your account.",
  },
  identityEvolutionProposal: {
    prompt:
      "Your recent actions may suggest a refined Declared Self. Confirm only after reviewing live evidence.",
    evidence: ["Complete onboarding", "Connect Calendar / GitHub", "Accumulate real evidence"],
    proposed: "Update Declared Self after a full week of live evidence",
  },
};
