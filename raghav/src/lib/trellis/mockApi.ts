export const mock = {
  demoUser: {
    name: "Aarav Sharma",
    role: "Founding Engineer",
    email: "aarav@example.com",
    declaredSelf: {
      headline: "Confident Speaker & Prolific Public Builder",
      attributes: [
        {
          id: "public_speaker",
          label: "Public Speaker",
          weight: 4.0,
          markers: [
            { id: "m1", label: "Presents live without freezing under pressure" },
            { id: "m2", label: "Delivers talks with clear structure and posture" },
          ],
        },
        {
          id: "builder",
          label: "Public Builder",
          weight: 4.0,
          markers: [
            { id: "m3", label: "Ships code commits to public repositories" },
            { id: "m4", label: "Publishes technical artifacts and demo videos" },
          ],
        },
      ],
    },
  },
  currentBottleneck: {
    title: "Focus Drift",
    description: "High passive consumption relative to output over the last 7 days",
    severity: "medium",
  },
  feedCards: [
    {
      id: "fc1",
      mode: "scroll",
      kind: "low_value",
      headline: "10 React tips you didn't know (infinite thread)",
      tag: "Passive Reading",
    },
    {
      id: "fc2",
      mode: "scroll",
      kind: "neutral",
      headline: "How top engineers structure production architectures",
      tag: "Case Study",
    },
  ],
  weeklyNarrative: {
    arc: "Closing the Gap: Public Speaker & Builder",
    body: "This week your creation ratio reached 55%, led by 3 public commits and a rehearsed presentation. Focus drift dropped by 12% following your capacity adjustment.",
  },
  identityEvolutionProposal: {
    prompt: "Based on 3 live presentation events this week, evolve declared target for Public Speaker?",
    evidence: ["College Presentation (3d ago)", "Toastmasters Open Mic (5d ago)"],
    proposed: "Elevate Public Speaker target weight to 5.0",
  },
};
