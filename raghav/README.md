# Trellis Growth Curator

TRELLIS — Lovable Build Prompt (v1)

Paste everything from "## PROJECT BRIEF" down into Lovable as your first message. This is scoped as a frontend-complete, data-mocked build — every screen, animation, score, and popover in the PRD is real and interactive, but all "intelligence" (Gemini calls, Tavily search, Supabase persistence) is simulated with local mock data and clearly named functions so a real backend can be dropped in later without restructuring the UI.

PROJECT BRIEF

Build Trellis — an agentic AI growth curator. It is a web app (Next.js + React + Tailwind) that helps a user close the gap between who they say they want to become (Declared Self) and who their behavior shows they actually are (Revealed Self), by continuously curating a personalized "Identity Stack" of media, missions, and experiences.

This is a hackathon demo product for a sponsor called IABTM ("I Am Better Than Me"). Match their visual identity closely (full spec below) while building Trellis's own screens and flows — do not copy IABTM's layout or components, only their design language.

Build this as a single-page app with client-side routed views (no real auth, one hardcoded demo profile called "Aarav"). All data lives in local React state / a mock in-memory store seeded on load — structure it as if it were an API layer (e.g. lib/mockApi.ts with async functions returning promises) so it can be swapped for real Supabase/Gemini calls later without touching components.

1. DESIGN LANGUAGE (IABTM-derived — follow closely)

Overall mood: editorial, confident, minimal, high-contrast. Feels like a fashion/wellness magazine crossed with a serious productivity tool — never playful, never gamified, no confetti, no cartoon mascots, no streak-flame badges. This restraint is itself part of the pitch (Trellis explicitly rejects attention-optimized gamification).

Color system:

Base: pure white (#FFFFFF) for light surfaces, near-black (#0A0A0A / #111111) for dark surfaces

Text: near-black on light (#111111), near-white on dark (#F5F5F5)

The app is primarily dark mode for the main product (dashboard, feed, ledger) — mirrors IABTM's dashboard — with the landing/onboarding flow allowed to be light, editorial, high-whitespace like IABTM's marketing homepage

One accent color system, used sparingly and functionally, never decoratively:

Signal amber/orange (#F5A623-ish) — for the Gap score movement, flame/momentum indicators

Alignment blue (#4A7CFF-ish, muted) — for Declared trajectory lines, progress bars

Growth green (muted sage, not neon) — for "worked" verdicts, positive deltas

Failure red/rust (muted, not alarm-red) — for "failed" verdicts only, used rarely

Everything else stays grayscale. Color = meaning, never decoration.

Typography:

Large, confident sans-serif headlines (system font stack: Inter, or -apple-system fallback) — big type, generous line-height, IABTM-style ("Become the self you imagine" scale headlines on the landing/onboarding-complete screens)

Body text smaller, high contrast, generous line-height

Numbers (scores, percentages) get their own large tabular-nums treatment — they should feel like the hero content on the Dashboard, not buried in small UI chrome

Shape & surface language:

Pill-shaped primary buttons (fully rounded, like IABTM's black "Start Here" pill), solid fill, no gradients

Cards: subtle rounded corners (12–16px), on dark surfaces use a slightly-lighter-than-background card fill (#1A1A1A on #0A0A0A) with a hairline border (1px solid rgba(255,255,255,0.08)), no heavy drop shadows

Generous whitespace/padding — never cramped, never dense-dashboard-SaaS-style

Editorial photography-style imagery where used (portraits, real-feeling stock), never illustration/emoji as primary visual content

Motif: the trellis/lattice — a physical garden trellis is a lattice structure that a plant grows up and is supported by. Use this as a literal recurring visual motif: thin diagonal/grid line-work, especially in the Identity Gap visualization (Section 4 below), used as subtle background texture on empty states, and optionally as a faint watermark pattern in the app's dark backgrounds. This ties the brand name to the visual system the way IABTM's name ties to its "better than me" self-comparison framing.

Iconography: simple, thin-stroke line icons (like Lucide — use lucide-react), never filled/bold icon sets, never emoji in the product UI (emoji are allowed only inside seeded Trust Ledger example text, per the PRD's own copy examples).

Motion: purposeful, not decorative. Framer Motion for: the feed-card morph (Section 5), capacity slider variant swaps (Section 6), score number transitions (count-up/count-down, not just snap), lattice struts filling in. No bouncy/springy playful easing — use calm, confident ease-out curves (200–400ms).

2. GLOBAL STRUCTURE

Build as a Next.js app with these routes/views (client-side state-driven navigation is fine, doesn't need to be literal Next routes if simpler in Lovable):

/ — Landing (marketing-style, light mode, IABTM-homepage-inspired) → CTA into onboarding

/onboarding — The Mirror Interview (F1)

/dashboard — Main app shell (F3, F5, F6) — this is the primary screen, dark mode

/feed — Growth Feed with The Catch (F4) — dark mode, phone-frame constrained width

/ledger — Trust Ledger (F7) — dark mode

/report — Weekly Becoming Report (F8) + Identity Evolution proposal (F11) — allow light or dark, your call, but keep consistent

Hidden simulator panel: triggered by pressing Shift + D anywhere in the dashboard/feed — a slide-out drawer (dark, monospace-flavored, "debug" visual treatment distinct from the rest of the app) with buttons: "Inject 5x doomscroll", "Advance 1 day", "Fire calendar trigger", "Force 3rd dismissal (trigger unlearning)"

Persistent left sidebar in the main app (dashboard/feed/ledger/report), styled like IABTM's dashboard sidebar: logo mark top-left (design a simple wordmark: "TRELLIS" in the same confident all-caps treatment as IABTM's logo, plus a small lattice-icon mark), nav items with line icons: Dashboard, Growth Feed, Trust Ledger, Weekly Report. Bottom of sidebar: small user card (avatar circle, "Aarav", "Demo Profile").

Top bar inside main app: page title on the left, on the right a compact Capacity Slider always visible (not just on dashboard — PRD implies it should affect the whole app's intervention intensity) plus a bell/notification icon.

3. ONBOARDING — "The Mirror Interview" (F1)

Full-screen light-mode chat interface, generous whitespace, IABTM-editorial feel

A single message thread, AI messages left-aligned in a soft-gray bubble, user replies right-aligned in solid black bubble with white text (matches pill-button color)

Sequence of 5 scripted questions (mock the "LLM" with a deterministic scripted flow, but make it feel conversational):

"What's the version of yourself you're trying to become?"

"Why does that matter to you right now?"

"Walk me through a normal weekday — what do you actually do with your time?"

"What's the biggest thing you feel is blocking you?"

"Realistically, how many hours a week can you give this?"

Free-text input for the user, but since this is a demo, also provide 2–3 quick-reply suggestion chips under each AI question so a judge can move fast

After question 5, show a 1.5s "thinking" state (subtle pulsing lattice-line animation, not a generic spinner) then render a Declared Self confirmation card:

Extracted identity attributes as chips/rows (e.g. "Confident Public Speaker", "Consistent Builder/Shipper") each with 2–4 observable markers listed underneath in smaller text, and an editable weight shown as a small horizontal bar

Headline above the card, IABTM-scale typography: "Here's who you're becoming."

Two buttons: pill "Looks right → Enter Trellis" (primary, black) and text-link "Edit this" (secondary)

Clicking confirm navigates to /dashboard and seeds the mock store with this Declared Self plus the 21-day simulated history (see Section 8)

4. DASHBOARD (F3, F5, F6 core)

This is the hero screen. Dark mode. Layout (adjust responsively but preserve hierarchy):

Top section — Identity Gap:

Large "Identity Gap" number, 0–100, huge tabular-nums typography (this is the single most important number in the product — treat it like IABTM treats their headline text)

Directly beside/below it: "Alignment: {100-Gap}" in the muted blue accent, smaller

A lattice visualization: build this as an SVG or Canvas component — a grid of diagonal struts (literal trellis pattern), one strut per identity attribute/marker. Filled/bright struts = evidence exists and is recent; dim/bare struts = missing or decayed evidence. This should visually read as "a structure with gaps in it," reinforcing the name and the concept. Animate struts filling in with a glow pulse when a new evidence event fires (e.g. after completing a mission in the Feed).

Below the lattice: two trend lines on a minimal line chart (Recharts) — "Declared trajectory" (blue, dashed) vs "Revealed trajectory" (amber, solid) over the 21-day window. No gridlines/axis clutter — minimal, editorial chart style, axis labels only.

Gap Score popover: clicking the Gap number opens a detail panel (side sheet or modal) showing the full arithmetic breakdown per the PRD formula:

Table/list of each identity attribute: weight wᵢ, declared target Dᵢ, decayed revealed evidence Rᵢ, deficit, contribution to final score

Create:Consume ratio shown as a simple horizontal split-bar (green create portion vs red/amber consume+drift portion)

Final formula shown in a monospace "math strip": GapScore = round(100 × Σ(wᵢ × deficitᵢ))

This must NOT read as an LLM-generated blob — present it like a receipt/audit log, monospace numbers, clearly deterministic

Potential Bottleneck card:

A distinct card, slightly larger/more prominent than others: bottleneck name in large type (e.g. "Execution" or "Consistency"), a one-line diagnosis sentence underneath ("Your bottleneck isn't learning, it's publishing."), and 2 bullet "supporting evidence" lines

Small "confidence" indicator (low/medium/high as a subtle dot-strength indicator, not a percentage — keep it qualitative to match the PRD's "if confidence is low, default to a small experiment" behavior)

Today's Identity Stack:

Row/grid of cards, each representing one active element of today's Stack (Media, Knowledge, Growth Story, Tool, Mentor, Real-World Experience, Micro Mission, Reflection) — only render the elements that are actually active (per PRD: never fill all 8 slots mechanically, typically 2–4 active)

Each card: type label (small, uppercase, muted), title, one-line description, and an expandable "Why this? / Why now? / How this closes the Gap" three-line explanation block (collapsed by default, click to expand — icon rotates)

A small source badge on Media cards: "Live web" / "Cached web" / "Curated fallback" (muted pill, top-right of card) — mock all three states so it's visually demonstrable

Each Stack card has a primary action ("Start" / "Read" / "Watch") and a subtle dismiss (X) — dismissing triggers a toast-style micro-confirmation and (per PRD) logs a mock evidence event, visibly nudging the Gap score down slightly with an animated count transition

Capacity Slider (F6) — present in the top bar globally, but give it a dedicated expanded view accessible from the dashboard too:

Horizontal slider, 0–100%, with three labeled zones underneath: 0–33% Micro, 34–66% Light, 67–100% Full

Dragging it live-updates every visible Stack card's copy/duration to match its tier (mock 3 pre-written variants per card: full/light/micro) with NO loading state — must feel instant (<100ms), a direct swap/crossfade, not a re-fetch

Small caption under the slider that updates live: e.g. "Capacity changed; preserving momentum without adding load." when moving down, or nothing/positive framing when moving up

This is explicitly the emotional peak interaction of the demo — make the crossfade animation satisfying: old copy fades+shrinks out, new copy fades+grows in, ~250ms

5. GROWTH FEED — "The Catch" (F4)

Constrain this view to a centered phone-frame width (~390px) even on desktop, with a subtle device-frame border, floating on the dark background — visually signals "this is the scroll surface we own," distinct from the rest of the app

Scrollable card feed, mix of mock low-value content cards (meme-style headline text + placeholder image blocks, gossip-style headlines, "shorts" thumbnail cards — all clearly fake/placeholder, labeled generically like "Trending Now" content, not real brand names) and neutral cards

Implement the deterministic trigger client-side for real (this is good demo craft, don't fully mock it): track scroll events in local state, and when scroll_count >= 5 low-value cards have passed AND ratio of low-value:total in the last N cards > 0.70, trigger the morph — this logic can run in a plain JS function/hook, no backend needed, and should genuinely execute in the browser

On trigger: the next card in the feed morphs in place — animate a flip/dissolve transition where the low-value card transforms into an intervention card (different visual treatment: black background, white text, small lattice-icon, the amber accent border) showing: a short reasoning line ("You're a few minutes into low-value scroll during a speaking-practice week. This worked for you before.") + a 1–3 min micro-action + Accept / Snooze / Dismiss buttons

Dismiss action: show the card visibly leaving/collapsing, and — this is a key demo beat — if this is the 3rd mock-tracked dismissal of "the same hypothesis family" (hardcode this as achievable via the simulator panel or by dismissing twice more in the session), trigger a distinct "Hypothesis Failed / System Unlearning" toast/banner that slides down from the top: "❌ Hypothesis Failed: '10-min Public Speaking Video' — dismissed 3 times. 💡 System Adaptation: Lowered Media Lens weight by 40%. Switched primary lens to Micro-Action." — styled as a system-log-like banner (monospace, dark card, amber left border), auto-dismisses after ~6s or on click

After that banner, the next intervention card that morphs in should visibly be a different type (Micro-Action instead of Media) — demonstrating the "unlearning" changed behavior

Completing (Accept) an intervention: card shows a satisfying checkmark/complete state, then a toast "Gap score updated" and navigating back to Dashboard should show the Gap number having moved and a lattice strut animating to "filled"

6. TRUST LEDGER (F7)

Dark mode, simple vertical list/table of past interventions, most recent first

Each row: hypothesis name, delivered date, verdict badge (worked = sage green pill, failed = muted rust pill, pending = gray outline pill), and expandable detail (what was delivered, outcome window, evidence that determined the verdict)

Seed ~10 historical entries (see Section 8) plus live entries generated during the session from Feed interactions

Include at least 2 pre-seeded entries showing the "Hypothesis Failed → System Unlearning" pattern so the Ledger tells a coherent story even before the user does anything live

Simple filter chips at top: All / Worked / Failed / Pending

7. WEEKLY BECOMING REPORT (F8) + IDENTITY EVOLUTION (F11)

A single shareable "report card" — bordered card, could genuinely look exportable/screenshottable, editorial layout matching IABTM's confident-headline style

Narrative-style copy (mock this as pre-written template text that fills in from state, not a real LLM call): identity movement framed as a journey, e.g. "Fearful → attended 2 events → initiated 5 conversations → Confidence marker +9"

Below the narrative: small stat row (Gap trend arrow, Create:Consume ratio, Consistency, Momentum)

Identity Evolution proposal (only show once, triggered by a button "Generate this week's report" or auto-shown on first visit): a distinct card that appears below the report — "Your recent actions consistently resemble a startup founder more than a researcher. Would you like to update your identity?" with the supporting evidence bullets, and two equally-weighted buttons: "Accept update" and "Keep current identity" (do NOT make Accept visually dominant — PRD requires equal prominence). Selecting either shows a brief confirmation state and (if accepted) would update the Declared Self shown on Dashboard — mock this state change.

8. MOCK DATA TO SEED ON LOAD

Structure this as a lib/mockData.ts / lib/mockApi.ts module with clearly named exports so it's easy to later swap for real Supabase calls:

demoUser: Aarav, 22, Declared Self = ["Confident Public Speaker" (weight 0.5), "Consistent Builder/Shipper" (weight 0.5)], each with 3 observable markers

evidenceEvents: generate 21 days of plausible mock events with realistic timestamps, mostly passive-learning and drift events with occasional creation events, clearly commented simulated: true in the data shape (matches the PRD's EvidenceEvent interface — replicate that TypeScript interface in the codebase even though it's mock-backed, so the shape is future-compatible)

initialGapScore: 68, with a believable per-attribute breakdown that arithmetically produces that number using the PRD's formula (actually implement the formula as a real TS function operating on the mock evidence, don't hardcode the output — this makes the popover breakdown genuinely correct and demonstrable)

currentBottleneck: "Execution", with 2 supporting evidence strings

todaysStack: 3 active elements (e.g. one Media, one Micro Mission, one Growth Story), each with the three explanation fields written out

growthStories: 8 seeded short first-person story summaries with tags (identity, stage, bottleneck, outcome)

toolCatalog: 10 seeded real tools (Cursor, Notion, Obsidian, GitHub, Google Calendar, Figma, Linear, Anki, Discord, Slack) each with a one-line "why this fits your stage" string

mentorProfiles: 5 seeded mentor cards (name, one-line background, matched bottleneck, journey blurb) — use generic placeholder names/avatars, not real people

trustLedger: 10 seeded historical entries with a mix of worked/failed/pending, including 2 that show the unlearning pattern

calendarEvents: 2–3 seeded upcoming events (e.g. "College presentation — Friday")

Implement calculateGapScore(evidenceEvents, declaredSelf) as a real deterministic function following the PRD Section 9 formula exactly (recency decay with 7-day half-life, weighted deficit sum) — this is worth doing properly since it's pure math, no API needed, and it's the credibility centerpiece of the whole product

9. TONE / COPY RULES THROUGHOUT

Never use gamified language: no "streak," "level up," "XP," no exclamation-mark hype copy

Calm, direct, slightly literary — matches IABTM's "Become the self you imagine" register

Every AI-attributed sentence in the UI should sound like a thoughtful observation, not a notification: prefer "Your bottleneck isn't learning, it's publishing." over "You're not learning enough! Try publishing more!"

Labels for simulated/fallback data must always be visible, never hidden — small muted badges, not asterisks-in-fine-print

10. WHAT NOT TO BUILD (keep Lovable focused)

No real authentication — single hardcoded demo profile

No real API calls to Gemini, Tavily, YouTube, or Supabase — all mocked in local state/TS modules as described above

No mobile app — responsive web only, phone-frame is a styling choice for the Feed view only

No real search/retrieval — Media cards use pre-written mock results with the source-badge system described above

End of prompt. After first generation, iterate screen-by-screen — Dashboard and Feed are the highest-leverage screens to polish first since they carry the demo's emotional beats (Section 13 of the PRD: Mirror → Catch and Rejection → Protection → Proof).

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/01b1f20d-28cd-4638-bf74-0ec77f9fcc9c).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
