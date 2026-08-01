# Product Requirements Document — TRELLIS

**Agentic AI for Human Potential — IABTM Hackathon**

Version 2.0 · Team working doc · Status: expanded current-scope build  
*(v1.2 locked a 24-hour MVP cut. This revision pulls former “future / deferred / P2-if-time” items into **current scope**. Everything below is in-scope unless listed under Non-Goals.)*

---

## 1. One-Line Summary

Trellis is an agentic AI growth curator that continuously observes who you want to become (**Declared Self**), who your behavior shows you are (**Revealed Self**), and how both evolve — then repeatedly diagnoses the bottleneck holding you back, assembles the best growth experience for the present moment, and adapts it as new evidence arrives.

---

## 2. Problem Statement (verbatim from hackathon)

> How might we design an agentic AI curator that deeply understands an individual's aspirations, habits, and evolving identity — and continuously curates the most relevant media, knowledge, and experiences to help them become the self they imagine? … Today's algorithms optimize for attention. This challenge asks you to build one that optimizes for human potential.

### How Trellis answers each phrase of the brief

| Brief requirement | Trellis mechanism |
|---|---|
| "deeply understands aspirations, habits, evolving identity" | Identity Digital Twin built from a conversational AI interview + behavioral evidence (OAuth connectors, screen-time ingest, in-app events), with identity-evolution proposals that always require user confirmation |
| "continuously curates" | Continuous Curation Engine (event-driven + Celery Tier-2 jobs) re-evaluates and refreshes the Identity Stack whenever behavior, capacity, context, outcomes, resources, or confirmed aspirations materially change — without waiting for a user query |
| "media, knowledge, AND experiences" | Identity Stack: a bottleneck-specific combination of media, knowledge, growth stories, tools, mentors, experiences, micro-missions, and reflection — never an isolated recommendation; retrieval via Tavily/YouTube, Qdrant semantic search, and Neo4j graph RAG |
| "right resources at the right time" | Moment Detector: intervenes at drift moments (doomscroll) and before leverage moments (real calendar events) |
| "passive scrolling into purposeful growth" | The Growth Feed morphs low-value scrolling into aligned micro-steps, live, with personalized live/cached resources |
| "optimizes for human potential, not attention" | The system's single optimization target is the **Identity Gap score** — visible, explainable, falsifiable — not engagement |

---

## 3. Goals and Non-Goals

### Goals (current scope — all required)

1. A working end-to-end product of the full agent loop: perceive → decide-when → decide-what → protect → act → measure.
2. The Identity Gap score visibly moves as a result of user action and real evidence (GitHub, Calendar, Notion, screen time, in-app events).
3. Real (non-mocked) curation pipelines: live web/YouTube retrieval, Qdrant semantic search, and Neo4j graph RAG feeding the Curator.
4. Real multi-user auth (Clerk + Google), real OAuth evidence connectors, encrypted tokens at rest.
5. Background jobs (Celery + Redis) for Tier-2 curation, sync, and leverage-moment scheduling.
6. Growth Partner Match with real vector similarity (Qdrant), not a hard-coded mock card.
7. Community surfaces in product: Growth Stories (seeded + submission path), mentor matching with journey similarity, contribution/reputation basics.
8. A defensible answer to "why is this agentic and not a chatbot?" and "why isn't this manipulative?"
9. Judges remember: a feed that fought back, a score that moved, an AI that admitted a failed intervention, and evidence that came from the user's real digital life.

### Non-Goals (still explicitly out of scope)

- Real DOM injection into Instagram/Twitter (browser-extension platform risk). We own a first-party Growth Feed instead; third-party scrape remains out.
- Native mobile apps (iOS/Android). Web only; screen-time evidence enters via upload/drop-box, not a mobile SDK.
- Voice pipelines (STT/TTS).

Everything formerly labeled “future roadmap,” “deferred,” “P2 if time,” or “we say this in the pitch, we don’t build it” is **in current scope** unless listed above.

---

## 4. Target User and Persona

**Primary persona (demo seed / fallback):** "Aarav," 22, wants to become *a confident public speaker and builder who ships projects*. His screen time says otherwise: 2.5 hrs/day short-form video, tutorials watched but nothing published, no events attended. Motivated but stuck in the consume-don't-create loop.

**Production path:** every signed-in user completes their own Mirror Interview; no demo-user default in staging/prod. Seeded Aarav history remains an opt-in local/demo tool only.

**Broader user:** anyone with a stated growth aspiration whose daily digital behavior quietly diverges from it — the say–do gap. Trellis’s Identity Stack and Growth Feed are designed to map onto IABTM as an embedded curation layer; **integration-ready evidence schema and MCP adapters are part of current scope**.

### Community philosophy

Trellis believes that every person is both a learner and a future guide. As users grow, they can contribute stories, mentor others, recommend resources, and strengthen the ecosystem. Growth is not consumed individually — it compounds collectively.

**Current scope includes:** seeded catalogs **and** user contribution workflows for Growth Stories, mentor profiles with journey/bottleneck matching (embedding + graph signals), and basic reputation / verification hooks tied to evidence — not follower count.

### Curation philosophy

**Curation is not an event — it is a continuous relationship.**

Trellis assumes that identity, behavior, opportunities, capacity, and circumstances constantly evolve. Therefore, every curated selection has an expiration date. The system's responsibility is to continuously replace yesterday's best selection with today's best selection when new evidence makes that replacement materially more useful. It does not preserve a resource merely because it was previously selected.

---

## 5. Core Concept

Trellis maintains two live models:

- **Declared Self** — built from a conversational AI onboarding interview ("who are you trying to become?"). Decomposed by the LLM into 3–5 identity attributes with observable behavioral markers (e.g. *Public Speaker* → speaks in front of others, publishes recordings, attends speaking events).
- **Revealed Self** — built from a stream of **evidence events** (app usage / screen time, watch history, GitHub commits, calendar attendance, Notion activity, tasks completed, missions done). Demo may still show labeled simulated history; production users accumulate **real** events from connectors and in-app actions.

The distance between them is the **Identity Gap score (0–100)** — the primary outcome the system optimizes, where `0` means fully aligned and `100` means highly divergent. It is calculated deterministically from declared targets, weighted evidence, and a seven-day exponential recency decay (Section 9), never generated by an LLM. High-value creation contributes `+3.0` to `+5.0`, passive learning contributes `+1.0`, and low-value drift during a focus window contributes `−2.0` per 10 minutes; the resulting **Create:Consume ratio** makes the difference visible. A companion **Alignment score** is simply `100 − Gap`. A **Potential Bottleneck** layer interprets the evidence beneath that score to identify the current limiting factor — such as confidence, consistency, execution, accountability, knowledge, communication, focus, networking, discipline, or burnout. The Gap says *how far* the user is from the desired identity; the bottleneck says *what is most responsible right now*.

When the gap is widening (drift trigger) or a high-leverage moment approaches (calendar trigger), agents assemble an **Identity Stack**: a carefully selected combination of **Media, Knowledge, Growth Story, Tool, Mentor, Real-World Experience, Micro Mission, and Reflection**, chosen for the current bottleneck. An intervention does not need all eight elements; it needs the smallest coherent combination that can move the user. Trellis is therefore not recommending isolated resources — it is assembling a personalized growth experience.

Every resource in the Stack answers three questions: **Why this? Why now? How does this reduce the Identity Gap?** Every intervention is logged as a hypothesis in the **Trust Ledger** and later marked *worked / failed* based on subsequent evidence. A **Guardian** layer can downgrade or cancel any intervention based on user capacity, and always explains itself.

Identity is not treated as permanent. Periodically, an **Identity Evolution Agent** compares accumulated behavior and reflection against the current Declared Self. If a consistent new direction appears, it proposes — never silently applies — an update. The user must explicitly confirm every change.

### Continuous Curation Engine

Trellis does not generate one-time recommendations. It continuously observes the user's aspirations, behavior, context, capacity, and outcomes, re-evaluating what should be curated next. Every meaningful state change creates a new curation cycle through the event-driven loop **and** Celery Tier-2 / beat jobs.

Eligible triggers include:

- behavioral drift;
- completed or dismissed interventions;
- changing aspirations after explicit confirmation;
- approaching calendar events (real OAuth sync);
- changes in available time or Capacity Slider state;
- successful or failed experiments;
- confirmed identity evolution;
- newly discovered resources that materially outperform the current selection (web, Qdrant, Neo4j);
- connector syncs (GitHub, Calendar, Notion) and screen-time uploads.

Each trigger invalidates only the affected assumptions, not the entire user model. The Curator dynamically re-ranks available resources, retains still-valid elements, replaces stale or failed elements, and continuously assembles the strongest current Identity Stack. The Guardian still controls whether, when, and at what intensity a refreshed Stack reaches the user.

**Current-scope infrastructure for this loop:** normalized evidence events, deterministic Moment Detector, reasoning agents, Postgres persistence, Redis, Celery worker + beat, Tavily/YouTube adapters, Qdrant vector store, Neo4j graph RAG, and OAuth MCP adapters.

---

## 6. Feature Requirements

Priority key: **P0 = must ship** · **P1 = must ship for full product bar** · *(former P2 items are promoted into P0/P1 — nothing is “if time remains.”)*

### F1. Conversational Onboarding — "The Mirror Interview" (P0)

- Chat UI, 4–6 LLM-driven questions max (aspiration, why, current habits, biggest blocker, weekly capacity).
- LLM extracts a structured **Declared Self JSON**: identity attributes, each with 2–4 observable markers and a weight.
- Output shown to user for confirmation/edit ("Did I get you right?") — this is also the consent moment.
- Per real signed-in user (Clerk); no Aarav seed in the default signup path.
- Acceptance: a judge can state any aspiration and get a sensible identity graph in < 20 seconds.

### F2. Evidence Engine + Revealed Self (P0)

- A single normalized **evidence event schema**: `{timestamp, source, type, category, value, weight}` (e.g. `shortform_video_30min`, `mission_completed`, `article_read`, `event_attended`, `github_commit`, `screentime_app`).
- Optional seeded 21-day simulated history for demos, stored in DB, visibly labeled **"simulated history"** in the UI.
- Live events: any action taken in the app (mission completed, content read, feed scrolled, intervention dismissed) generates a real event through the same pipeline.
- Real connector events: GitHub, Google Calendar, Notion, and Screen Time upload — all `simulated=false` when from live OAuth/upload.
- A dev-only "simulator panel" (hidden hotkey) to inject events live on stage.
- Acceptance: every event, seeded or live, flows through one pipeline and updates the Revealed Self within 2 seconds.

### F3. Identity Gap Score + Lattice Visualization (P0)

- Live score (0–100) computed from the explainable formula in Section 9; recomputed on every new event.
- Visualization: a **trellis/lattice graphic** — one strut per identity marker; filled struts = evidence exists, bare struts = missing. Beside it, two trend lines (Declared trajectory vs Revealed trajectory).
- The Dashboard Gap Score must have a tooltip/popover showing: each identity attribute and `wᵢ`, declared target, positive creation contribution, passive-learning contribution, focus-drift penalty, recency decay, attribute deficit, final Gap, and `Alignment = 100 − Gap`.
- Click any lattice strut → the exact evidence events that contributed to it.
- Acceptance: score visibly changes when an event fires; the complete arithmetic breakdown is available in one click and contains no LLM-generated number.

### F4. Growth Feed + In-Feed Interception — "The Catch" (P0)

- An in-house, team-owned scrollable feed (mobile-frame web UI) mixing realistic low-value items with neutral items **and** personalized live/cached resource cards from the Identity Stack (YouTube/web).
- The **Moment Detector is a deterministic JavaScript rule engine**, not an LLM call. It evaluates locally after every scroll event and must complete in `<50ms`.
- Exact vulnerability rule: trigger immediately when `scroll_count >= 5` **and** `low_value_ratio > 0.70` inside the rolling 15-minute window **and** the timestamp falls within a declared focus period. Add a 10-minute cooldown after firing.
- The trigger decision stores its input values so the UI can explain exactly why it fired. No network request is allowed on the trigger path.
- On trigger, the next feed card **morphs in place** into a prepared intervention (Tier-1 cache), with the agent's one-line reasoning displayed.
- User can act, snooze, or dismiss. Dismissal is itself an evidence event.
- Acceptance: the fifth qualifying scroll triggers the local decision in `<50ms`; the prepared intervention morph begins immediately, and the Gap score reacts to the resulting evidence event.

### F5. Four-Lens Curator + Identity Stack (P0)

Whenever a meaningful state-change event starts a curation cycle, the Curator first diagnoses the highest-impact **Potential Bottleneck**, then continuously retrieves or reuses candidates (live web, YouTube, Qdrant, Neo4j), evaluates developmental fit, dynamically re-ranks them, replaces expired or failed selections, and assembles the strongest current Identity Stack:

1. **Next Step (P0)** — the smallest aligned action + one matched piece of real media. Media is continuously curated from live web/YouTube search and the cache, then dynamically re-ranked for *developmental fit* — not popularity.
2. **Missing Action / Bottleneck (P0)** — diagnoses the primary limiting factor from the fixed taxonomy, names the evidence behind it, and generates a micro-mission targeting it.
3. **Real-World Opportunity (P0)** — a nearby experience: meetup, Toastmasters, workshop, event. Live web search where possible; curated Pune events list as labeled fallback.
4. **Outside Voice (P0)** — a cross-domain analogy with explicit "why this structurally fits your pattern" reasoning, constrained to pre-vetted source domains.

- The Curator assembles an **Identity Stack** from eight resource types: **Media, Knowledge, Growth Story, Mentor, Tool, Real-World Experience, Micro Mission, and Reflection**.
- Every selected element carries: **Why this? Why now? How does this reduce the Identity Gap and increase Alignment?**
- Replacement occurs only when the candidate is materially better or the current element is stale, failed, unsafe, or mismatched to capacity.
- Acceptance: every intervention contains at least one action and one resource; Next Step uses real live content when providers are up; dismissal, completion, capacity, identity confirm, and connector sync each re-evaluate the Stack through the same event-driven + Celery path.

### F5A. Growth Stories (P0)

- Authentic first-person growth journeys matched by **stage and bottleneck** (catalog + Qdrant / Neo4j ranking).
- Seeded catalog (8–12+) **and** a user story-submission workflow with source/author labels and structured tags.
- Acceptance: Curator selects a relevant story with an explanation; submissions enter the same catalog/retrieval path after validation.

### F5B. Tool Curation (P0)

- Curator may select software/platforms/communities when a tool removes current friction.
- Seeded catalog of tools with domains, stages, bottlenecks, URLs, and safe starter actions; Notion/GitHub/Calendar connections deepen tool recommendations when connected.
- Acceptance: an Identity Stack can include a tool tied directly to its micro-mission and bottleneck.

### F5C. Mentor Network (P0)

- Mentors matched by journey, strengths, stage, and current bottleneck — never follower count — using embedding similarity and/or graph path features.
- Seeded mentor profiles **and** paths for experienced users to become mentor candidates from evidence.
- Outreach/scheduling/messaging are in scope as product surfaces (even if MVP-thin); verification and reputation use evidence signals.
- Acceptance: Curator selects a mentor with journey/bottleneck explanation; matching is not a static hard-coded list.

### F6. Guardian / Consent Layer — "The Protection" (P0)

- Runs before any intervention reaches the user. Checks: interventions-today count (cap 5), time since last, user-declared capacity, recent dismissal rate.
- Can **downgrade**, **delay**, or **cancel** — and always shows a plain-language reason.
- Interactive Live Capacity Slider (0–100%) stores capacity as a real evidence/context event.
- Every active intervention is generated or cached in three forms (`full`, `light`, `micro`). Slider thresholds: `67–100 → full`, `34–66 → light`, `0–33 → micro`. Dragging swaps the active card locally without a page refresh or LLM/API call.
- Acceptance: dragging the slider updates every visible intervention card in `<100ms`, preserves the intervention hypothesis ID, and creates no extra API request.

### F7. Trust Ledger + Reflection Loop (P0)

- Every intervention logged as: hypothesis → what was delivered → outcome window → verdict (**worked / failed / pending**) based on subsequent evidence + optional one-tap self-report.
- Logs delivery, acceptance, snooze, and dismissal synchronously; displays **System Unlearning** tags when a failure threshold is crossed.
- Failure rule: the same hypothesis family dismissed three times within 14 days becomes `failed`; lens weights update deterministically; an alternate prepared lens is requested.
- Full Ledger history: successes, failures, adaptations, and pending outcome windows.
- Acceptance: a dismissal writes the event and updates the Ledger in `<250ms`; subsequent curation no longer selects the rejected primary lens.

### F8. Weekly Becoming Report (P0)

- One-click LLM-generated narrative over the evidence window: identity movement, not hours. Rendered as a clean shareable card.
- Acceptance: generates in < 10 seconds from the signed-in user's live DB state.

### F9. Leverage-Moment Trigger (P0)

- **Real Google Calendar OAuth sync** powers upcoming events in plan view (seeded events remain a labeled fallback only).
- Agent schedules the right input to land *before* the moment via Celery beat / Tier-2 jobs ("Your talk is in 3 days — tonight: this clip + 60-second run-through").
- Acceptance: a connected calendar surfaces a leverage intervention in plan view before a high-signal event; disconnect stops ingest immediately.

### F10. Growth Partner Match (P0)

- Embedding similarity over partner profiles via **Qdrant** (with deterministic local fallback when the vector store is unavailable).
- Card proposes a weekly accountability check-in; badges must honestly label **Qdrant Cloud Match** vs simulated fallback.
- Acceptance: match reflects stage/goal/bottleneck similarity; not a hard-coded single prototype card.

### F11. Identity Evolution Review (P0 — confirmation required)

- Identity Evolution Agent compares recent evidence, reflection themes, and Declared Self (on demand from Weekly Report **and** as a background/scheduled proposal when evidence is consistent).
- May propose add/remove/reweight of attributes; must cite supporting evidence.
- No update applies until the user selects **Accept update**. **Keep current identity** equally prominent.
- Acceptance: accepting creates a versioned Declared Self and triggers re-curation; rejecting leaves identity unchanged.

### F12. Screen Time & Device Telemetry (P0)

- Settings / Integrations drop-box: user uploads a Screen Time screenshot or posts structured app-usage JSON.
- Pipeline normalizes app minutes into evidence events (creation / passive learning / focus drift) through the same universal ingest path.
- Acceptance: an upload updates Revealed Self and Gap without bypassing the evidence pipeline.

### F13. Vector Search (Qdrant) (P0)

- Qdrant Cloud collections for catalog stories/tools/mentors, partner profiles, and identity-adjacent documents.
- Semantic search API + dashboard Vector Search UI; reindex endpoint for catalog vectors.
- Acceptance: with `VECTOR_DB_PROVIDER=qdrant` and credentials set, semantic search returns scored hits; with provider `fake`/no URL, product degrades gracefully.

### F14. Graph RAG (Neo4j) (P0)

- Neo4j models users, identity attributes, markers, bottlenecks, resources, domains, and hypothesis families.
- Multi-hop retrieval connects current deficits to Identity Stack candidates; dismissed families are excluded; path facts feed Curator explanations.
- Acceptance: graph context is available to curation; failures fall back to catalog/web retrieval without blocking the feed morph.

### F15. Auth, Ownership, and Integrations Hub (P0)

- Clerk JWT auth; Google social login; per-user provisioning; ownership isolation across users.
- Integrations UI: connect / status / disconnect / reconnect for Google Calendar, GitHub, Notion; Screen Time panel; honesty badges on evidence sources.
- Token encryption at rest (Fernet); no plaintext tokens in logs or API responses.
- Acceptance: two users never see each other’s data; revoke stops ingest immediately; history preserved.

---

## 7. Data Sources — Real vs Simulated (honesty map)

| Data | Source in current build | Real or simulated |
|---|---|---|
| Aspirations, values, capacity | Live AI interview (F1) | **Real** |
| Auth / identity of user | Clerk + Google OAuth | **Real** |
| 21-day behavioral history | Opt-in seed script (demo only) | **Simulated, labeled** |
| In-app behavior | App event pipeline | **Real** |
| Doomscroll telemetry | Owned Growth Feed + simulator | **Owned surface, real pipeline** |
| Screen time | Upload / structured JSON ingest (F12) | **Real user upload → real pipeline** |
| Curated media | Tavily + YouTube Data API, LLM re-ranked | **Real, live** (+ labeled fallback) |
| Semantic / partner match | Qdrant Cloud + embeddings | **Real when configured** (+ local fallback) |
| Graph context | Neo4j Graph RAG | **Real when configured** (+ fallback) |
| Local events/opportunities | Web search + Pune list fallback | **Real with labeled fallback** |
| Growth Stories | Seeded catalog + user submissions | **Mixed; labeled** |
| Tool catalog | Seeded catalog + connected tools | **Real tools, curated metadata** |
| Mentor profiles | Seeded + evidence-based mentor candidates | **Mixed; labeled** |
| Calendar | Google Calendar OAuth sync | **Real** (+ seeded fallback labeled) |
| GitHub creation evidence | GitHub OAuth sync | **Real** |
| Notion activity | Notion OAuth sync | **Real** |
| Partner profiles | Vector-matched profiles (Qdrant) | **Real matching over catalog/fixtures until multi-user pool grows** |

Principle: every source feeds one Evidence Intelligence pipeline (normalize → dedupe → score → update twin); no module consumes raw source data directly. **MCP / OAuth connectors are current-scope builds**, not pitch-only roadmap.

### MCP data bridge contract

All providers — live OAuth or fixtures — enter through the same adapter boundary. Provider-specific fields must never leak into scoring or agents.

```typescript
interface EvidenceEvent {
  id: string;
  userId: string;
  timestamp: string;
  source: 'github' | 'google_calendar' | 'youtube' | 'notion' | 'screentime' | 'trellis';
  type: string;
  category: 'creation' | 'passive_learning' | 'focus_drift' | 'reflection';
  identityAttributeIds: string[];
  value: number;
  baseWeight: number;
  metadata: Record<string, unknown>;
  simulated: boolean;
}

interface RawMCPPayload {
  sourceProvider: 'github' | 'google_calendar' | 'youtube' | 'notion' | 'screentime';
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
| **Identity Evolution Agent** | Whether accumulated evidence justifies proposing a change to the Declared Self | Versioned identity history, evidence trends, reflective check-ins; may propose but never apply without confirmation |
| **Moment Detector (deterministic controller)** | *When* to act | Local event stream, explicit JS trigger rules, calendar proximity; no LLM |
| **Curator** | Continuously retrieves, evaluates, dynamically re-ranks, replaces, and assembles the Identity Stack; explains every choice | Web/YouTube search, Qdrant semantic retrieval, Neo4j graph RAG, story/tool/mentor catalogs, Trust Ledger outcomes, capacity, Stack validity |
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
Retrieve Better Resources (web / YouTube / Qdrant / Neo4j)
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

This loop is the lifetime operating model of Trellis. Any eligible state-change event enters the same loop. The system may preserve the current Stack, replace only one stale element, downgrade through the Guardian, or assemble a new Stack.

**Current-scope runtime:** event-driven request path (Tier 0/1) plus Celery worker/beat for Tier-2 reasoning, connector sync, pre-warm, and calendar leverage scheduling. Identity evolution requires confirmation. Seeded events remain optional for demos; live connectors and scrolls demonstrate continuous adaptation.

**Why agentic (the judge answer):** a recommender ranks items when asked. Trellis continuously monitors meaningful changes, diagnoses the actual limiting factor, re-evaluates whether the current Stack is still best, dynamically assembles a better multi-resource experience when needed, explains every choice, protects the user from its own eagerness, then measures the outcome and changes future curation because of it. It can also notice that the destination itself may be evolving, while preserving human authority over any identity change. Remove the autonomous, persistent loop and the product ceases to exist.

### Tiered latency architecture

- **Tier 0 — synchronous deterministic (`<100ms`):** scroll trigger evaluation, Gap recomputation, capacity-tier swapping, dismissal logging, failure-threshold checks, lens-weight updates, and optimistic UI state. These paths never call Gemini, Bedrock, Tavily, Qdrant, Neo4j, or the DB write path before rendering the morph.
- **Tier 1 — prepared/cache-first (`<300ms` target):** fetch a pre-generated intervention variant or cached retrieval result. The trigger path always has at least one prepared intervention.
- **Tier 2 — asynchronous reasoning/retrieval (`1–10s`, never blocks interaction):** Gemini bottleneck analysis and explanation, Tavily/YouTube retrieval, Qdrant/Neo4j enrichment, weekly reports, identity-evolution proposals, connector sync. Results refresh the candidate pool and prepare the *next* intervention.

### Retrieval fallback logic

Every search / retrieval request follows an adapter-controlled chain:

1. Return a fresh matching cache entry immediately if one exists.
2. Otherwise call Tavily (1.5s timeout) and/or YouTube for video metadata; optionally enrich with Qdrant semantic hits and Neo4j multi-hop context.
3. Validate that each result has a title, URL, extract, and source; persist valid results.
4. On timeout, quota exhaustion, malformed results, or network failure, use a pre-fetched seeded resource/event set matched by identity and bottleneck.
5. Show a source badge — **Live web**, **Cached web**, **Curated fallback**, **Qdrant**, or **Graph** — so the product never implies seeded retrieval was live.

Retrieval failure must never produce an empty intervention or block the deterministic feed morph.

---

## 9. Identity Gap Score (explainable formula)

The LLM never calculates this score. It can classify evidence into identity attributes, but deterministic code performs all arithmetic.

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
| Passive learning | Video watched, article read, focused app time | `+1.0` |
| Low-value focus drift | Doomscrolling / short-form during a declared focus window | `−2.0` per completed 10 minutes |

Concrete subtype weights are configuration constants, not model output: completed mission `+3.0`, GitHub commit `+4.0`, published artifact `+5.0`, attended experience `+4.0`, passive item completed `+1.0`, focus drift `−2.0/10 min`.

### Create:Consume ratio

For the same recency window:

```
CreatePoints = Σ creation/action positive weighted contributions
ConsumePoints = Σ passive-learning positive weighted contributions
DriftPoints = abs(Σ low-value focus-drift negative contributions)

CreateConsumeRatio = CreatePoints / max(1, ConsumePoints + DriftPoints)
```

A ratio `<1` means consumption/drift outweighs creation; `=1` means balance; `>1` means action outweighs consumption. The ratio is diagnostic and drives the Missing Action lens; it is not a second optimization target.

The Dashboard popover required by F3 lists the exact values above and the events that produced them. Secondary displayed metrics derived from the same pipeline are **Consistency** (evidence spread across days) and **Momentum** (seven-day Gap delta).

### Potential Bottleneck model

The bottleneck is a structured diagnosis, not a second opaque score. The Identity Modeler supplies the Curator with:

```
{ bottleneck, confidence, supporting_evidence[], missing_evidence[], alternative_bottleneck }
```

The initial taxonomy is fixed: confidence, consistency, execution, accountability, knowledge, communication, focus, networking, discipline, and burnout. Gemini selects from this taxonomy using evidence aggregates and must cite at least two supporting signals. If confidence is low, the Curator defaults to a small experiment rather than presenting the diagnosis as fact.

---

## 10. UX — Screens

1. **Auth** — Clerk sign-in / sign-up (Google social).
2. **Onboarding chat** (F1) → confirmation card of the extracted identity graph.
3. **Dashboard**: lattice + Gap popover + Create:Consume + bottleneck + trend lines + Identity Stack + Capacity Slider + Vector Search bar.
4. **Growth Feed** (F4): phone-frame scrollable feed; intervention cards morph inline; live resource cards interleaved.
5. **Trust Ledger** (F7): experiment history with worked/failed/pending verdicts and System Unlearning.
6. **Weekly Report** (F8): narrative card + confirmable Identity Evolution proposal (F11).
7. **Settings / Integrations**: Calendar, GitHub, Notion connect/disconnect; Screen Time drop-box; honesty badges.
8. **Plan view**: leverage moments from real calendar + scheduled pre-event interventions.
9. Hidden **simulator panel** (dev hotkey): inject doomscroll burst, advance time, fire calendar trigger.

Design language: calm, plant/architecture motif (trellis lattice), no gamification confetti, no streaks — the anti-attention aesthetic is part of the pitch.

---

## 11. Tech Stack (current architecture)

- **Frontend:** `raghav/` — Vite + TanStack Start/Router + React + Tailwind + shadcn/ui; Motion for feed-morph; Clerk React SDK.
- **Backend:** `services/api` — FastAPI, SQLAlchemy, Alembic; separate from the frontend.
- **Database:** Postgres (Docker Compose / hosted). System of record for identities, evidence, interventions, ledger, integrations, cached search results.
- **Auth:** Clerk (JWKS JWT verification, Google social, per-user provisioning).
- **LLM — primary:** Google Gemini (`google.genai`), with key rotation pool and daily per-user call budget.
- **LLM — fallback:** AWS Bedrock via the same provider adapter / failover wrapper.
- **Retrieval:** Tavily Search API + YouTube Data API v3; composite provider supported; honesty badges required.
- **Vector DB:** Qdrant Cloud (`VECTOR_DB_PROVIDER=qdrant`).
- **Graph:** Neo4j Graph RAG (`RAG neo4j/` schema, queries, provider prototype → wire into Curator).
- **Jobs:** Celery + Redis (worker + beat) for Tier-2 curation, sync, pre-warm, leverage scheduling.
- **Integrations:** OAuth MCP adapters — Google Calendar, GitHub, Notion; Screen Time upload API; encrypted tokens at rest.
- **Realtime:** local client event bus for Tier-0 interactions; async persistence + background refresh for Tier-2.

Implementation constraint: all LLM calls go through one provider adapter; all search/vector/graph calls go through their adapters. No feature may import vendor SDKs directly outside those adapters.

---

## 12. Build Plan (current scope — no cut-list for former P2)

| Track | Deliverable |
|---|---|
| A — Auth & ownership | Clerk JWT, provisioning, ownership audit, FE auth, per-user onboarding, CORS/env matrix |
| B — LLM | Gemini live, key rotation, Bedrock failover, repair/harden paths, budget, prompt facade |
| C — Retrieval & jobs | Tavily/YouTube live, Next Step ranking, Celery worker/beat, trigger-driven stack refresh, rate limits/telemetry |
| D — Evidence connectors | Token infra, integrations router, Calendar, GitHub, Notion, honesty flags, FE connections UI |
| Feed | Owned Growth Feed API + live resource cards + Catch morph |
| Screen time | Upload/analyze → evidence pipeline |
| Qdrant | Collections, semantic search API, partner match, dashboard Vector Search, reindex |
| Neo4j | Schema, queries, Graph RAG context into Curator |
| Community | Story submission, mentor matching, reputation basics |
| Demo polish | Wire all primary FE routes off mock data; rehearsal of full agent loop on real user |

There is **no** hour-15 cut rule that drops F8/F9/F10/F11/community/graph/vector. If capacity is tight, prioritize wiring FE to live APIs over new surface area, but do not reclassify those features as future.

---

## 13. Demo Script (expanded beats)

1. **The Mirror.** Judge signs in (or uses a fresh account). Onboarding extracts the identity graph live; dashboard renders the lattice. Open Gap popover to prove deterministic math.
2. **Real evidence.** Connect GitHub and/or Calendar, or drop a Screen Time screenshot — Gap / Revealed Self update from `simulated=false` events.
3. **The Catch and Rejection.** Doomscroll five qualifying cards; Moment Detector fires; intervention morphs; third dismissal crosses System Unlearning; alternate completes → Gap moves.
4. **The Protection.** Capacity Slider 80% → 20%; Guardian swaps full → micro locally with explanation.
5. **Retrieval intelligence.** Show Live/Cached/Qdrant/Graph badges on stack or Vector Search results; Weekly Report + optional Identity Evolution confirm.
6. **The Proof.** Trust Ledger chain: rejected hypothesis → unlearning → alternative completed → new evidence → score changed.

Closing line: "Every feed you've used optimizes one number — your attention. Trellis optimizes a different one, shows its math, unlearns when it is wrong, and reads the life you already live."

---

## 14. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Gemini quota / latency | Fast model, key rotation, daily call cap, Bedrock failover, Tier-2 async, prepared interventions |
| Tavily / YouTube / Qdrant / Neo4j failure | Cache → live → labeled curated fallback; never block Catch morph |
| Gap score looks arbitrary | Deterministic formula + arithmetic popover; no LLM-generated score |
| Judges probe "real vs theater" | Honesty map + source badges; connectors labeled; simulator demoted to dev |
| Surveillance / manipulation concern | Guardian + consent; dismissible interventions; narrow OAuth scopes |
| Identity-evolution feels presumptuous | Cite evidence; require Accept; Keep current equally prominent |
| Scope pressure | FE wiring and connector honesty first; adapters keep vendors swappable |
| Stage network latency | Tier-0 local for Catch/capacity/unlearning; pre-warm stacks |

---

## 15. Success Metrics

**For the hackathon / live demo:** all P0 acceptance criteria pass in rehearsal; Gap movement legible; at least one live connector or screen-time ingest; at least one Live/Cached/Qdrant badge visible; Catch + Unlearning + Capacity beats land.

**For the product:** weekly Gap delta per user, bottleneck-resolution rate, intervention acceptance rate, create:consume ratio improvement, ledger success-rate trend, Growth Story-to-action conversion, mentor-match acceptance, confirmed identity evolution, connector attach rate — none of which is watch time. Trellis becomes the curation layer whose KPI is user growth, plugged into IABTM via the same evidence-event / MCP schema.

---

## 16. Locked Infrastructure Decisions

1. **LLM:** Google Gemini is the primary provider. AWS Bedrock is the in-path failover when the Gemini pool is exhausted (feature-flagged until credentials exist).
2. **Search:** Tavily is the primary web-search provider; YouTube Data API for video metadata; composite provider allowed.
3. **Database:** Postgres is the system of record (not anonymous single-demo Supabase-only access).
4. **Auth:** Clerk JWT + Google social; multi-user ownership mandatory.
5. **Vector DB:** Qdrant Cloud for semantic search and partner match.
6. **Graph:** Neo4j for Graph RAG context into curation.
7. **Jobs:** Celery + Redis for Tier-2 and scheduled leverage/sync work.
8. **Implementation constraint:** all LLM / search / vector / graph calls go through adapters only. No feature may import vendor SDKs outside those adapters.
9. **Scope constraint:** former “future / deferred / P2-if-time” items in v1.2 are **current scope** in v2.0. Only Section 3 Non-Goals remain out.
