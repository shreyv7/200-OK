/** Deprecated local stubs — dashboard / ledger / report / capacity now hit live APIs.
 * Kept only for optional simulator copy until those strings move fully server-side.
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
