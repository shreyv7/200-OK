# Product Requirements Document — TRELLIS

**Agentic AI for Human Potential — IABTM Hackathon (24-hour build)**

Version 1.2 · Team working doc · Status: locked for build

---

## 1. One-Line Summary

Trellis is an agentic AI growth curator that continuously observes who you want to become (**Declared Self**), who your behavior shows you are (**Revealed Self**), and how both evolve — then repeatedly diagnoses the bottleneck holding you back, assembles the best growth experience for the present moment, and adapts it as new evidence arrives.

---

## 2. Problem Statement (verbatim from hackathon)

> How might we design an agentic AI curator that deeply understands an individual's aspirations, habits, and evolving identity — and continuously curates the most relevant media, knowledge, and experiences to help them become the self they imagine? … Today's algorithms optimize for attention. This challenge asks you to build one that optimizes for human potential.

### How Trellis answers each phrase of the brief

| Brief requirement | Trellis mechanism |
|---|---|
| "deeply understands aspirations, habits, evolving identity" | Identity Digital Twin built from a conversational AI interview + behavioral evidence, with periodic identity-evolution proposals that always require user confirmation |
| "continuously curates" | Continuous Curation Engine re-evaluates and refreshes the Identity Stack whenever behavior, capacity, context, outcomes, resources, or confirmed aspirations materially change — without waiting for a user query |
| "media, knowledge, AND experiences" | Identity Stack: a bottleneck-specific combination of media, knowledge, growth stories, tools, mentors, experiences, micro-missions, and reflection — never an isolated recommendation |
| "right resources at the right time" | Moment Detector: intervenes at drift moments (doomscroll) and before leverage moments (calendar events) |
| "passive scrolling into purposeful growth" | The Growth Feed morphs low-value scrolling into aligned micro-steps, live |
| "optimizes for human potential, not attention" | The system's single optimization target is the **Identity Gap score** — visible, explainable, falsifiable — not engagement |

---

## 3. Goals and Non-Goals

### Goals (what winning looks like)

1. A working end-to-end demo of the full agent loop: perceive → decide-when → decide-what → protect → act → measure.
2. The Identity Gap score visibly moves during the live demo as a result of user action.
3. At least one real (non-mocked) curation pipeline pulling live content from the internet.
4. A defensible answer to "why is this agentic and not a chatbot?" and "why isn't this manipulative?"
5. Judges remember three images: a feed that fought back, a score that moved, an AI that admitted a failed intervention.

### Non-Goals (explicitly out of scope for 24 hours)

- Real DOM injection into Instagram/Twitter (browser-extension platform risk; we own a mock feed instead).
- Real OAuth integrations with GitHub/Calendar/Notion etc. (simulated evidence events, honestly labeled).
- Real user-to-user matching, mentor outreach, or event booking. The MVP may show seeded mentor profiles and growth stories, clearly labeled as prototype data.
- Mobile app. Web only.
- Accounts/auth beyond a single demo profile.
- Voice pipelines (STT/TTS latency risk on stage).

---

## 4. Target User and Persona

**Primary persona (used for demo seed data):** "Aarav," 22, wants to become *a confident public speaker and builder who ships projects*. His screen time says otherwise: 2.5 hrs/day short-form video, tutorials watched but nothing published, no events attended. Motivated but stuck in the consume-don't-create loop.

**Broader user:** anyone with a stated growth aspiration whose daily digital behavior quietly diverges from it — the say–do gap. This is IABTM's exact audience (secondary note: Trellis's Identity Stack and Growth Feed map naturally onto IABTM's platform as an embedded curation layer later; we do not build for that now).

### Community philosophy

Trellis believes that every person is both a learner and a future guide. As users grow, they can contribute stories, mentor others, recommend resources, and strengthen the ecosystem. Growth is not consumed individually — it compounds collectively.

The 24-hour MVP demonstrates this philosophy with seeded Growth Stories and mentor profiles. Contribution workflows, reputation systems, and real mentor communication remain future platform capabilities.

### Curation philosophy

**Curation is not an event — it is a continuous relationship.**

Trellis assumes that identity, behavior, opportunities, capacity, and circumstances constantly evolve. Therefore, every curated selection has an expiration date. The system's responsibility is to continuously replace yesterday's best selection with today's best selection when new evidence makes that replacement materially more useful. It does not preserve a resource merely because it was previously selected.

---

## 5. Core Concept

Trellis maintains two live models:

- **Declared Self** — built from a 2-minute conversational AI onboarding interview ("who are you trying to become?"). Decomposed by the LLM into 3–5 identity attributes with observable behavioral markers (e.g. *Public Speaker* → speaks in front of others, publishes recordings, attends speaking events).
- **Revealed Self** — built from a stream of **evidence events** (app usage, watch history, tasks completed, missions done). For the hackathon: 3 weeks of seeded simulated history, clearly labeled "simulated," plus real events generated live during the demo.

The distance between them is the **Identity Gap score (0–100)** — the primary outcome the system optimizes, where `0` means fully aligned and `100` means highly divergent. It is calculated deterministically from declared targets, weighted evidence, and a seven-day exponential recency decay (Section 9), never generated by an LLM. High-value creation contributes `+3.0` to `+5.0`, passive learning contributes `+1.0`, and low-value drift during a focus window contributes `−2.0` per 10 minutes; the resulting **Create:Consume ratio** makes the difference visible. A companion **Alignment score** is simply `100 − Gap`. A **Potential Bottleneck** layer interprets the evidence beneath that score to identify the current limiting factor — such as confidence, consistency, execution, accountability, knowledge, communication, focus, networking, discipline, or burnout. The Gap says *how far* the user is from the desired identity; the bottleneck says *what is most responsible right now*.

When the gap is widening (drift trigger) or a high-leverage moment approaches (calendar trigger), agents assemble an **Identity Stack**: a carefully selected combination of **Media, Knowledge, Growth Story, Tool, Mentor, Real-World Experience, Micro Mission, and Reflection**, chosen for the current bottleneck. An intervention does not need all eight elements; it needs the smallest coherent combination that can move the user. Trellis is therefore not recommending isolated resources — it is assembling a personalized growth experience.

Every resource in the Stack answers three questions: **Why this? Why now? How does this reduce the Identity Gap?** Every intervention is logged as a hypothesis in the **Trust Ledger** and later marked *worked / failed* based on subsequent evidence. A **Guardian** layer can downgrade or cancel any intervention based on user capacity, and always explains itself.

Identity is not treated as permanent. Periodically, an **Identity Evolution Agent** compares accumulated behavior and reflection against the current Declared Self. If a consistent new direction appears, it proposes — never silently applies — an update such as: "Your recent actions consistently resemble a startup founder more than a researcher. Would you like to update your identity?" The user must explicitly confirm every change.

### Continuous Curation Engine

Trellis does not generate one-time recommendations. It continuously observes the user's aspirations, behavior, context, capacity, and outcomes, re-evaluating what should be curated next. Every meaningful state change creates a new curation cycle through the existing event-driven loop.

Eligible triggers include:

- behavioral drift;
- completed or dismissed interventions;
- changing aspirations after explicit confirmation;
- approaching calendar events;
- changes in available time or Capacity Slider state;
- successful or failed experiments;
- confirmed identity evolution; and
- newly discovered resources that materially outperform the current selection.

Each trigger invalidates only the affected assumptions, not the entire user model. The Curator dynamically re-ranks available resources, retains still-valid elements, replaces stale or failed elements, and continuously assembles the strongest current Identity Stack. The Guardian still controls whether, when, and at what intensity a refreshed Stack reaches the user.

The objective is not simply to recommend content. It is to continuously maintain the best possible growth environment for the user.

For the 24-hour MVP, this capability uses infrastructure already defined in this PRD: normalized evidence events, the local event bus, deterministic triggers, the existing reasoning agents, cached resource candidates, and Supabase persistence. No additional agent, scheduler, queue, integration, or background service is required.

---

## 6. Feature Requirements

Priority key: **P0 = must ship** (demo breaks without it) · **P1 = should ship** (major judge points) · **P2 = if time remains**.

### F1. Conversational Onboarding — "The Mirror Interview" (P0)

- Chat UI, 4–6 LLM-driven questions max (aspiration, why, current habits, biggest blocker, weekly capacity).
- LLM extracts a structured **Declared Self JSON**: identity attributes, each with 2–4 observable markers and a weight.
- Output shown to user for confirmation/edit ("Did I get you right?") — this is also the consent moment.
- Acceptance: a judge can state any aspiration and get a sensible identity graph in < 20 seconds.

### F2. Evidence Engine + Revealed Self (P0)

- A single normalized **evidence event schema**: `{timestamp, source, type, category, value, weight}` (e.g. `shortform_video_30min`, `mission_completed`, `article_read`, `event_attended`).
- Seeded 21-day simulated history for the demo persona, stored in DB, visibly labeled **"simulated history"** in the UI.
- Live events: any action taken in the app (mission completed, content read, feed scrolled, intervention dismissed) generates a real event through the same pipeline.
- A dev-only "simulator panel" (hidden hotkey) to inject events live on stage (e.g. simulate 20 minutes of doomscrolling in 5 seconds).
- Acceptance: every event, seeded or live, flows through one pipeline and updates the Revealed Self within 2 seconds.

### F3. Identity Gap Score + Lattice Visualization (P0)

- Live score (0–100) computed from the explainable formula in Section 9; recomputed on every new event.
- Visualization: a **trellis/lattice graphic** — one strut per identity marker; filled struts = evidence exists, bare struts = missing. Beside it, two trend lines (Declared trajectory vs Revealed trajectory) over the 21-day window.
- The Dashboard Gap Score must have a **P0 tooltip/popover** showing: each identity attribute and `wᵢ`, declared target, positive creation contribution, passive-learning contribution, focus-drift penalty, recency decay, attribute deficit, final Gap, and `Alignment = 100 − Gap`.
- Click any lattice strut → the exact evidence events that contributed to it, including timestamp, event weight, and decayed contribution.
- Acceptance: score visibly changes on stage when an event fires; the complete arithmetic breakdown is available in one click and contains no LLM-generated number.

### F4. Growth Feed + In-Feed Interception — "The Catch" (P0)

- An in-house, team-owned scrollable feed (mobile-frame web UI) mixing realistic low-value items (memes, gossip cards, shorts thumbnails) with neutral items. **We own this surface** — zero third-party platform risk, identical visual payoff.
- The **Moment Detector is a deterministic JavaScript rule engine**, not an LLM call. It evaluates locally after every scroll event and must complete in `<50ms`.
- Exact vulnerability rule: trigger immediately when `scroll_count >= 5` **and** `low_value_ratio > 0.70` inside the rolling 15-minute window **and** the timestamp falls within a declared focus period. Add a 10-minute cooldown after firing to prevent intervention spam.
- The trigger decision stores its input values (`scroll_count`, `low_value_ratio`, window, focus-period match) so the UI can explain exactly why it fired. No network request is allowed on the trigger path.
- On trigger, the next feed card **morphs in place** (animated transition) into an intervention card: a 1–3 minute step tied to the declared identity, with the agent's one-line reasoning displayed ("You're 25 min into low-value scroll during a speaking-practice week. This worked for you before.").
- User can act, snooze, or dismiss. Dismissal is itself an evidence event (feeds the learning loop).
- Acceptance: the fifth qualifying scroll triggers the local decision in `<50ms`; the prepared intervention morph begins immediately, and the Gap score reacts to the resulting evidence event.

### F5. Four-Lens Curator + Identity Stack (P0 core, P1 full)

Whenever a meaningful state-change event starts a curation cycle, the Curator first diagnoses the highest-impact **Potential Bottleneck**, then continuously retrieves or reuses candidates, evaluates developmental fit, dynamically re-ranks them, replaces expired or failed selections, and assembles the strongest current Identity Stack:

1. **Next Step (P0)** — the smallest aligned action + one matched piece of real media. Media is continuously curated from live web/YouTube search and the cache, then dynamically re-ranked for *developmental fit* (goal distance, difficulty, readiness) — not popularity. This is our one guaranteed-real retrieval pipeline.
2. **Missing Action / Bottleneck (P0)** — diagnoses the primary limiting factor (confidence, consistency, execution, accountability, knowledge, communication, focus, networking, discipline, or burnout), names the evidence behind it ("Your bottleneck isn't learning, it's publishing"), and generates a micro-mission targeting it. Pure structured LLM analysis over evidence data — cheap and extremely demo-strong.
3. **Real-World Opportunity (P1)** — a nearby experience: meetup, Toastmasters, workshop, event. Live web search where possible; a curated pre-fetched Pune events list as fallback, labeled as such.
4. **Outside Voice (P2)** — a cross-domain analogy (jazz, aviation, sport) with explicit "why this structurally fits your pattern" reasoning, constrained to 5 pre-vetted source domains.

- The Curator continuously assembles and personalizes an **Identity Stack** from eight resource types: **Media, Knowledge, Growth Story, Mentor, Tool, Real-World Experience, Micro Mission, and Reflection**. It selects only the combination justified by the current bottleneck; it does not fill slots mechanically.
- Every selected element carries three concise explanation fields: **Why this? Why now? How does this reduce the Identity Gap and increase the Alignment Score?** (Reducing the Alignment Score would be incorrect because higher Alignment is better.)
- Each Stack has a `curated_at` time and a logical validity condition within the existing intervention record. A trigger causes re-evaluation; replacement occurs only when the candidate is materially better or the current element is stale, failed, unsafe, or mismatched to capacity.
- Acceptance: every intervention contains at least one action and one resource; at least the Next Step lens curates real live content; the current bottleneck and all three explanations are visible; dismissal, completion, and capacity changes each cause the next Stack to be re-evaluated through the same event-driven path.

### F5A. Growth Stories (P1 — seeded MVP)

- Authentic first-person growth journeys from people who faced a similar bottleneck and later made meaningful progress: overcoming public-speaking fear, building a first startup, recovering from failure, developing consistency, or changing careers.
- Stories are dynamically re-ranked by **stage and bottleneck match**, not popularity. Each card includes the Curator's explanation, e.g. "This creator faced the same bottleneck you're facing today: fear of shipping publicly."
- MVP: 8–12 pre-written, seeded community stories with source/author labels and structured tags (`identity`, `stage`, `bottleneck`, `outcome`). No story-submission workflow is built.
- Acceptance: the Curator can select one relevant seeded story and explain its match; stories never appear as generic motivational filler.

### F5B. Tool Curation (P1 — seeded catalog)

- The Curator may continuously curate software, platforms, communities, or productivity systems when a tool removes the user's current friction: Cursor, Notion, Obsidian, Slack/Discord communities, GitHub, Google Calendar, Anki, Figma, or Linear.
- Every tool selection includes one line stating why it is the best next tool for the user's current stage. A tool is selected only when it enables an action; never as a standalone directory listing.
- MVP: a seeded catalog of 10–15 tools with domains, stages, bottlenecks, URLs, and safe starter actions. No external tool integration is required.
- Acceptance: one Identity Stack can include a tool tied directly to its micro-mission and bottleneck.

### F5C. Optional Mentor Network (P1 — prototype)

- Users may eventually become mentors after demonstrating experience through evidence in a specific domain. Mentor candidates may include community mentors, experienced users, professionals, creators, and domain experts.
- Mentors are matched by journey, strengths, stage, and current bottleneck — never follower count or popularity.
- MVP: 5–8 seeded mentor profiles and a dynamically curated mentor card only. No outreach, scheduling, messaging, verification, or live matching.
- Acceptance: the Curator can dynamically select one seeded mentor and explain the journey/bottleneck match. Future roadmap: AI-assisted matching using Identity Gap and journey similarity.

### F6. Guardian / Consent Layer — "The Protection" (P0)

- Runs before any intervention reaches the user. Checks: interventions-today count (cap 5), time since last, user-declared capacity, recent dismissal rate.
- Can **downgrade** (full mission → 90-second version), **delay**, or **cancel** — and always shows a plain-language reason.
- The Dashboard exposes an **Interactive Live Capacity Slider (0–100%)**. `0%` means recovery-only capacity; `100%` means full planned capacity. The selected value is stored as a real evidence/context event.
- Every active intervention is generated or cached in three forms (`full`, `light`, `micro`). Slider thresholds map deterministically: `67–100 → full`, `34–66 → light`, `0–33 → micro`. Dragging the slider swaps the active card locally without a page refresh or LLM/API call.
- Example stage transition: a 15-minute speaking-practice mission morphs into a 60-second mental rehearsal as the slider moves below 34%, with the explanation: "Capacity changed; preserving momentum without adding load."
- Acceptance: dragging the slider updates every visible intervention card in `<100ms`, preserves the intervention hypothesis ID, and creates no extra API request. **This remains the scripted emotional peak of the demo.**

### F7. Trust Ledger + Reflection Loop (P0 core, P1 full)

- Every intervention logged as: hypothesis → what was delivered → outcome window → verdict (**worked / failed / pending**) based on subsequent evidence + optional one-tap self-report.
- The P0 core logs delivery, acceptance, snooze, and dismissal synchronously and displays explicit **System Unlearning** tags whenever a failure threshold is crossed.
- Example entry:
  - **❌ Failed Hypothesis:** "10-min Public Speaking Video" — dismissed 3 times.
  - **💡 System Adaptation:** "Lowered Media Lens weight by 40%. Switched primary lens to Micro-Action."
- MVP failure rule: the same hypothesis family dismissed three times within 14 days becomes `failed`. The third dismissal immediately updates its lens weight using a deterministic rule and requests an alternative from an already prepared/cached lens. A single dismissal remains negative evidence, not proof of failure.
- Full P1 Ledger shows the entire history, including successes, failures, adaptations, and pending outcome windows. Seed with ~10 past entries; the demo hypothesis begins with two labeled historical dismissals so the live third dismissal visibly crosses the rule.
- Acceptance: a stage dismissal writes the event and updates the Ledger in `<250ms`; the **Hypothesis Failed** and **System Unlearning** states appear without refresh; subsequent curation no longer selects the rejected primary lens.

### F8. Weekly Becoming Report (P1)

- One-click LLM-generated narrative over the evidence window: identity movement, not hours ("Fearful → attended 2 events → initiated 5 conversations → Confidence marker +9"). Rendered as a clean shareable card.
- Acceptance: generates in < 10 seconds from live DB state.

### F9. Leverage-Moment Trigger (P2)

- Simulated calendar with 2–3 seeded upcoming events (e.g. "college presentation, Friday"). Agent schedules the right input to land *before* the moment ("Your talk is in 3 days — tonight: this 6-min clip on openings + record a 60-second run-through").
- Acceptance: one pre-seeded leverage intervention visible in the plan view.

### F10. Growth Partner Match (P2 — mock only)

- Embedding similarity over 5 fake user profiles → "someone at your stage with your goal" card with a proposed weekly accountability check-in. Clearly labeled prototype.

### F11. Identity Evolution Review (P1 — confirmation required)

- The Identity Evolution Agent periodically compares recent evidence, reflection themes, and the existing Declared Self. For the MVP, this runs on demand from the Weekly Report rather than as background infrastructure.
- It may propose that the user add, remove, or reweight an identity attribute when evidence is consistent across multiple events; it must cite the supporting evidence.
- Example: "You originally wanted to become a public speaker, but your recent behavior suggests a growing interest in entrepreneurship."
- No proposed update changes the Declared Self or Gap formula until the user explicitly selects **Accept update**. **Keep current identity** must be equally prominent.
- MVP: one seeded evolution proposal generated from the demo history; no autonomous background schedule.
- Acceptance: accepting the proposal creates a versioned Declared Self; rejecting it leaves all identity data unchanged.

---

## 7. Data Sources — Real vs Simulated (honesty map)

| Data | Source in 24h build | Real or simulated |
|---|---|---|
| Aspirations, values, capacity | Live AI interview (F1) | **Real** |
| 21-day behavioral history | Seeded generator script | **Simulated, labeled** |
| In-app behavior (scrolls, missions, dismissals) | App event pipeline | **Real** |
| Doomscroll telemetry | Owned mock feed + simulator panel | **Simulated surface, real pipeline** |
| Curated media | Web search / YouTube Data API, LLM re-ranked | **Real, live** |
| Local events/opportunities | Web search + pre-fetched Pune list fallback | **Real with labeled fallback** |
| Growth Stories | Seeded community-story catalog | **Simulated prototype data, labeled** |
| Tool catalog | Seeded structured catalog with real product URLs | **Real tools, curated metadata** |
| Mentor profiles | 5–8 seeded profiles | **Simulated prototype data, labeled** |
| Calendar | Seeded JSON | **Simulated, labeled** |
| Partner profiles | 5 fake profiles | **Simulated, labeled** |

Principle carried from the Forge plans: every source feeds one Evidence Intelligence pipeline (normalize → dedupe → score → update twin); no module consumes raw source data directly. Future MCP integrations (GitHub, Calendar, Notion, YouTube history) plug into the same schema — we say this in the pitch, we don't build it.

### MCP data bridge contract

The MVP uses simulated MCP payloads, but they must enter the application through the same adapter boundary future OAuth/MCP connectors will use. Provider-specific fields must never leak into scoring or agents.

```typescript
interface EvidenceEvent {
  id: string;
  userId: string;
  timestamp: string;
  source: 'github' | 'google_calendar' | 'youtube' | 'notion' | 'trellis';
  type: string;
  category: 'creation' | 'passive_learning' | 'focus_drift' | 'reflection';
  identityAttributeIds: string[];
  value: number;
  baseWeight: number;
  metadata: Record<string, unknown>;
  simulated: boolean;
}

interface RawMCPPayload {
  sourceProvider: 'github' | 'google_calendar' | 'youtube' | 'notion';
  rawPayload: Record<string, any>;
}

interface EvidenceAdapter {
  normalize(payload: RawMCPPayload): EvidenceEvent;
}
```

Each provider implements only `normalize()`. The common pipeline then validates the event, rejects duplicates using a provider event ID/hash, assigns or verifies category weights, persists it, and recomputes the Revealed Self. The simulator invokes these same adapters with fixtures; it does not insert pre-scored identity data directly.

---

## 8. Agent Architecture

Trellis has five reasoning agents plus one deterministic Moment Detector over shared state. This separation keeps judgment agentic while moving stage-critical detection and adaptation off the LLM path.

| Agent | Decides | Tools/data it alone has |
|---|---|---|
| **Identity Modeler** | What the Declared and Revealed Selves are; the Gap score and Potential Bottleneck | Interview extraction, evidence aggregates, scoring formula, bottleneck taxonomy |
| **Identity Evolution Agent** | Whether accumulated evidence justifies proposing a change to the Declared Self | Versioned identity history, evidence trends, optional reflective check-ins; may propose but never apply without confirmation |
| **Moment Detector (deterministic controller)** | *When* to act | Local event stream, explicit JS trigger rules, calendar; no LLM |
| **Curator** | Continuously retrieves, evaluates, dynamically re-ranks, replaces, and assembles the most developmentally relevant combination of media, knowledge, stories, mentors, tools, experiences, micro-missions, and reflections; explains every choice | Web/YouTube search, story/tool/mentor catalogs, events list, Trust Ledger outcomes, current capacity, active Stack validity |
| **Guardian** | *Whether/how much* reaches the user | Capacity state, intervention budget, dismissal history |
| **Reflection Agent** | Whether it *worked* | Post-window evidence, self-reports; writes verdicts, updates lens weights |

The Curator's explanation contract is mandatory for every selected element: **Why this? Why now? How does this reduce the Identity Gap and increase Alignment?** It must also explain replacements: what changed, what was removed, and why the new selection is more developmentally appropriate.

### Continuous Curation Loop

```text
Observe
  ↓
Understand Current Identity
  ↓
Detect Change
  ↓
Re-evaluate Development Needs
  ↓
Retrieve Better Resources
  ↓
Assemble New Identity Stack
  ↓
Deliver Intervention
  ↓
Measure Outcome
  ↓
Update User Model
  ↓
Repeat Continuously
```

This loop is the lifetime operating model of Trellis, not a sequence that runs only when the user opens a chat or requests a recommendation. Any eligible state-change event enters the same loop. The system may decide to preserve the current Stack when it remains best, replace only one stale element, downgrade it through the Guardian, or assemble a new Stack.

In the MVP, the loop runs event-driven and in-process using the existing local event bus and five reasoning agents plus the deterministic Moment Detector. Seeded events demonstrate longer-term continuity; live scroll, completion, dismissal, capacity, and experiment events demonstrate continuous adaptation on stage. Identity evolution remains invoked from the Weekly Report and requires confirmation. No cron infrastructure or additional agent is introduced.

**Why agentic (the judge answer):** a recommender ranks items when asked. Trellis continuously monitors meaningful changes, diagnoses the actual limiting factor, re-evaluates whether the current Stack is still best, dynamically assembles a better multi-resource experience when needed, explains every choice, protects the user from its own eagerness, then measures the outcome and changes future curation because of it. It can also notice that the destination itself may be evolving, while preserving human authority over any identity change. Remove the autonomous, persistent loop and the product ceases to exist.

### Tiered latency architecture

- **Tier 0 — synchronous deterministic (`<100ms`):** scroll trigger evaluation, Gap recomputation, capacity-tier swapping, dismissal logging, failure-threshold checks, lens-weight updates, and optimistic UI state. These paths never call Gemini, Bedrock, Tavily, or Supabase before rendering.
- **Tier 1 — prepared/cache-first (`<300ms` target):** fetch a pre-generated intervention variant or cached retrieval result from client state/Supabase. The trigger path always has at least one prepared intervention.
- **Tier 2 — asynchronous reasoning/retrieval (`1–10s`, never blocks interaction):** Gemini bottleneck analysis and explanation, Tavily/YouTube retrieval, weekly reports, and identity-evolution proposals. Results continuously refresh the candidate pool, prepare the *next* intervention, and update the current Stack only when the replacement policy permits.

### Retrieval fallback logic

Every search request follows one adapter-controlled chain:

1. Return a fresh matching Supabase cache entry immediately if one exists.
2. Otherwise call Tavily with a hard timeout of 1.5 seconds (YouTube API only for video-specific metadata).
3. Validate that each result has a title, URL, extract, and source; persist valid results to Supabase.
4. On timeout, quota exhaustion, malformed results, or network failure, use a pre-fetched seeded resource/event set matched by identity and bottleneck.
5. Show a source badge — **Live web**, **Cached web**, or **Curated fallback** — so the stage never implies seeded retrieval was live.

Retrieval failure must never produce an empty intervention or block the deterministic feed morph.

---

## 9. Identity Gap Score (explainable formula)

The LLM never calculates this score. It can classify evidence into identity attributes, but deterministic TypeScript performs all arithmetic.

For identity attribute \(i\):

- \(D_i > 0\): the declared weekly target in evidence points.
- \(w_i \in [0,1]\): importance weight confirmed during onboarding, with \(\sum_i w_i = 1\).
- \(a_{ik} \in [0,1]\): how strongly evidence event \(k\) applies to attribute \(i\).
- \(q_k\): signed event value multiplied by its fixed event-type weight.
- \(\Delta t_k\): event age in days.
- \(\lambda = \ln(2) / 7\text{ days}\), giving evidence a seven-day half-life.

The recency-decayed Revealed evidence and normalized deficit are:

```
R_i = Σ_k (a_ik × q_k × e^(-λΔt_k))
deficit_i = clamp((D_i - R_i) / D_i, 0, 1)

GapScore = round(100 × Σ_i (w_i × deficit_i))
AlignmentScore = 100 - GapScore
```

This is the bounded implementation of the conceptual relationship:

```
Alignment ≈ 100 - Σ_i w_i × (Declared_i - Σ_k Evidence_k × e^(-λΔt_k))
```

Normalization by \(D_i\) and clamping are required so different target units cannot push the score below 0 or above 100.

### Fixed evidence weights

| Event class | Examples | Weight |
|---|---|---:|
| High-value creation/action | GitHub commit, published post, completed mission, attended event | `+3.0` to `+5.0` (fixed per event subtype) |
| Passive learning | Video watched, article read | `+1.0` |
| Low-value focus drift | Doomscrolling during a declared focus window | `−2.0` per completed 10 minutes |

Concrete MVP subtype weights are configuration constants, not model output: completed mission `+3.0`, GitHub commit `+4.0`, published artifact `+5.0`, attended experience `+4.0`, passive item completed `+1.0`, focus drift `−2.0/10 min`.

### Create:Consume ratio

For the same recency window:

```
CreatePoints = Σ creation/action positive weighted contributions
ConsumePoints = Σ passive-learning positive weighted contributions
DriftPoints = abs(Σ low-value focus-drift negative contributions)

CreateConsumeRatio = CreatePoints / max(1, ConsumePoints + DriftPoints)
```

A ratio `<1` means consumption/drift outweighs creation; `=1` means balance; `>1` means action outweighs consumption. The ratio is diagnostic and drives the Missing Action lens; it is not a second optimization target. Focus drift also directly lowers \(R_i\), so its impact is visible in both the Gap breakdown and this ratio.

The Dashboard popover required by F3 lists the exact values above and the events that produced them. Secondary displayed metrics derived from the same pipeline are **Consistency** (evidence spread across days) and **Momentum** (seven-day Gap delta).

### Potential Bottleneck model

The bottleneck is a structured diagnosis, not a second opaque score. The Identity Modeler supplies the Curator with:

```
{ bottleneck, confidence, supporting_evidence[], missing_evidence[], alternative_bottleneck }
```

The initial taxonomy is fixed: confidence, consistency, execution, accountability, knowledge, communication, focus, networking, discipline, and burnout. Gemini selects from this taxonomy using evidence aggregates and must cite at least two supporting signals. If confidence is low, the Curator defaults to a small experiment rather than presenting the diagnosis as fact.

---

## 10. UX — Screens

1. **Onboarding chat** (F1) → confirmation card of the extracted identity graph.
2. **Dashboard**: lattice visualization + Gap score with arithmetic popover + Create:Consume ratio + current Potential Bottleneck + trend lines + momentum + today's expanded Identity Stack + interactive Capacity Slider (0–100%).
3. **Growth Feed** (F4): phone-frame scrollable feed; intervention cards morph inline.
4. **Trust Ledger** (F7): experiment history with worked/failed/pending verdicts.
5. **Weekly Report** (F8): narrative card plus an optional, explicitly confirmable Identity Evolution proposal (F11).
6. Hidden **simulator panel** (dev hotkey): inject doomscroll burst, advance time, fire calendar trigger.

Design language: calm, plant/architecture motif (trellis lattice), no gamification confetti, no streaks — the anti-attention aesthetic is part of the pitch.

---

## 11. Tech Stack (vibe-coding optimized)

- **Frontend:** Next.js + React + Tailwind + shadcn/ui; Framer Motion for the feed-morph animation; Recharts for trends. Single repo, deployed on Vercel (localhost fallback for demo).
- **Backend:** Next.js API routes (no separate server). Event pipeline = one POST endpoint + processing function.
- **Database:** Supabase Postgres using the Supabase JavaScript client. Use a single demo profile and anonymous access protected by Row Level Security; do not spend hackathon time building full authentication.
- **LLM — primary:** Google Gemini API free tier. Use a fast Gemini model for all latency-sensitive agent calls: interview extraction, bottleneck diagnosis, curation and explanation, Guardian reasoning, weekly reports, identity-evolution proposals, and optional cross-domain analogies. Require structured JSON outputs and keep prompts/model names behind one provider adapter.
- **LLM — fallback:** AWS Bedrock, enabled only if Gemini's free-tier quotas or reliability become a blocker. The provider adapter must expose one shared `generateStructured()` interface so switching providers requires an environment-variable change rather than rewriting agents. Preconfigure and test one Bedrock model before the demo if AWS access is available.
- **Retrieval:** **Tavily Search API** as the primary web-search service. It is purpose-built for AI agents, returns clean extracted text plus source URLs, requires little parsing, and currently offers 1,000 free credits per month without a credit card — sufficient for the hackathon. Use YouTube Data API v3 only when video-specific metadata is required. Cache successful search results in Supabase and ship a small pre-fetched fallback set for stage reliability.
- **Realtime:** local client event bus/React state for all sub-second demo interactions, followed by asynchronous Supabase persistence. Use 2-second polling only to reconcile cross-page state; skip websockets.
- **Seed script:** generates the 21-day evidence history, ledger entries, fake calendar, Growth Stories, tool catalog, and mentor profiles deterministically, so every demo run is identical.

Everything above is standard, well-documented, and AI-codegen-friendly. Nothing requires infra we haven't used, platform approvals, or multi-user coordination.

---

## 12. 24-Hour Build Plan

| Hours | Deliverable |
|---|---|
| 0–2 | Repo scaffold, DB schema (versioned identity, events, interventions, ledger, resource catalogs), seed script with demo persona |
| 2–5 | F1 onboarding interview + Declared Self extraction; F2 event pipeline |
| 5–8 | F3 deterministic Gap math + arithmetic popover + lattice/dashboard with live updates |
| 8–12 | F4 mock feed + deterministic Moment Detector + morph animation + simulator panel; F7 P0 dismissal/unlearning path |
| 12–15 | F5 Curator: Potential Bottleneck diagnosis + Next Step lens with real retrieval + Missing Action lens |
| 15–17 | F6 Guardian with live 0–100% Capacity Slider + locally prepared full/light/micro variants |
| 17–19 | F7 full P1 Trust Ledger history; seed reusable story/tool/mentor catalogs |
| 19–20 | F8 Weekly Report; F11 seeded identity-evolution proposal if core flow is stable |
| 20–22 | Full demo rehearsal ×3, seed-data tuning so the score movement reads clearly on a projector |
| 22–24 | Polish, P2 items only if everything above is stable, pitch deck |

**Cut rule:** if behind schedule at hour 15, drop F7's full-history P1 view, F8, F11, story/tool/mentor UI, and all P2. Preserve F7's P0 live dismissal/System Unlearning path and every other P0 capability.

---

## 13. Demo Script (4 beats, ~3 minutes)

1. **The Mirror.** Judge states a real aspiration. Onboarding extracts the identity graph live; dashboard renders the lattice over the labeled simulated history. Gap score: 68. Open its popover for three seconds to expose the declared targets, fixed weights, recency decay, creation boosts, and drift penalties — proving the number is deterministic.
2. **The Catch and Rejection.** Presenter doomscrolls five qualifying low-value cards. The local Moment Detector fires instantly and a media intervention morphs into the feed. The presenter dismisses it; because the seeded history contains two clearly labeled prior dismissals of that hypothesis family, this third rejection crosses the deterministic failure threshold. Within 250ms the Ledger shows **Hypothesis Failed** and **System Unlearning: Media −40%; switched to Micro-Action**. The prepared alternative morphs in, with **Why this / Why now / How it closes the Gap**. Presenter completes it → Gap score drops → a lattice strut fills in. Target duration for rejection and adaptation: 10 seconds.
3. **The Protection.** Move the Capacity Slider from 80% to 20%. The Guardian swaps a 15-minute mission for a 60-second mental rehearsal immediately, without refresh or API latency: "Capacity changed; preserving momentum without adding load."
4. **The Proof.** Open the Trust Ledger showing the complete chain: rejected hypothesis → explicit unlearning → alternative completed → new evidence → score changed. Closing line: "Every feed you've used optimizes one number — your attention. Trellis optimizes a different one, shows its math, and unlearns when it is wrong."

---

## 14. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Gemini free-tier quota, latency, or stage failure | Minimize calls, use the fast model, cache deterministic outputs in Supabase, and pre-warm the flow. Keep AWS Bedrock behind the same provider adapter and test the fallback before judging begins |
| Tavily quota or network failure | Use the free keyed plan, cache every successful result in Supabase, and fall back automatically to a small pre-fetched resource/event set |
| Gap score looks arbitrary | Deterministic bounded formula, fixed event weights, seven-day decay, and a P0 arithmetic popover exposing every contribution; no LLM-generated score |
| Judges probe "real vs theater" | Honesty map (Section 7) stated proactively; each agent has genuinely distinct tools; simulated data always labeled in-UI |
| "Isn't this surveillance/manipulation?" | Guardian + consent framing is a *core demo beat*, not a defense; narrow permissions story; every intervention explained and dismissible |
| Identity-evolution proposal feels presumptuous | Require repeated evidence, cite the signals behind the proposal, present it as a question, and never update the Declared Self without explicit confirmation |
| P1 catalogs expand scope | Use small seeded story/tool/mentor datasets and one reusable resource-card component; no contribution, verification, messaging, or booking workflows |
| Morph animation jank | Owned feed, pre-built card components, animation tested at hour 12, not hour 23 |
| Stage network latency blocks the catch | Keep trigger, capacity adaptation, failure threshold, lens update, and UI state entirely local; use prepared intervention variants and the cache → Tavily → seeded fallback chain |
| Scope creep | P0 list is frozen; cut rule at hour 15 is pre-agreed |

---

## 15. Success Metrics

**For the hackathon:** all P0 acceptance criteria pass in rehearsal ×3; demo ≤ 3 min; Gap score movement legible from the back of the room.

**For the product (post-hackathon story):** weekly Gap delta per user, bottleneck-resolution rate, intervention acceptance rate, create:consume ratio improvement, ledger success-rate trend, Growth Story-to-action conversion, mentor-match acceptance, and confirmed identity evolution — none of which is watch time. This is the metric story for IABTM integration: Trellis becomes the curation layer whose KPI is user growth, plugged into IABTM's existing content and community surfaces via the same evidence-event schema (MCP integrations from the Forge plan are the roadmap, not the build).

---

## 16. Locked Infrastructure Decisions

1. **LLM:** Google Gemini API free tier is the primary provider. AWS Bedrock is the tested fallback if free-tier limits or reliability become a blocker.
2. **Search:** Tavily Search API is the primary search provider because its agent-oriented response includes extracted content and source URLs with minimal integration work. Use the free keyed plan and cache results.
3. **Database:** Supabase Postgres is the system of record for identities, evidence events, interventions, cached search results, and Trust Ledger entries.
4. **Implementation constraint:** all LLM calls go through one provider adapter, and all search calls go through one retrieval adapter. No feature may import Gemini, Bedrock, or Tavily SDKs directly outside those adapters.
