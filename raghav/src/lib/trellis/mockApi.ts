/** Lightweight local stubs for surfaces not yet wired to the live API.
 * Auth / onboarding / integrations use real backend calls (A4–A5 / D6).
 */

export const mock = {
  currentBottleneck: {
    title: "Focus Drift",
    description: "High passive consumption relative to output over the last 7 days",
    severity: "medium",
  },
  feedCards: [
    {
      id: "feed-1",
      kind: "media" as const,
      headline: "Deep work block — 25 minutes",
      tag: "Focus",
    },
    {
      id: "feed-2",
      kind: "mission" as const,
      headline: "Ship one public artifact",
      tag: "Creation",
    },
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
