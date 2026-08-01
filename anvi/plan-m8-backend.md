# Implementation Plan — Backend — M8

## 1. Context
- Role: **backend** | Milestone: **M8 — Demo Hardening & P2 (Optional)**
- PRD: F9, F10 (P2), cut rule, Risks §14
- Goal: fix a real M7 integration break discovered while syncing (see §4 — this is the priority), then the actual M8 checkboxes: calendar leverage seed/API, partner-match mock, cache pre-warming, Bedrock failover check, basic observability.

## 2. Scope (in)
**Prerequisite fix (not a milestones.md bullet, but blocking real functionality):**
- [ ] Reconcile M7's duplicate `WeeklyReport`/`IdentityEvolutionProposal` schemas and dead-end generation logic (§4)

**Backend checkboxes:**
- [ ] Seed calendar leverage events; plan-view API
- [ ] Partner match mock profiles endpoint (labeled prototype)
- [ ] Pre-warm caches for demo script path
- [ ] Bedrock failover tested once
- [ ] Observability basics: structured logs, LangSmith optional

## 3. Scope (out)
- AIA: leverage-moment decision features, seed-target tuning for legible Gap movement, Outside Voice lens (P2, only if time).
- AIS: prepared doomscroll interventions, Growth Partner Match card, Execution Coach silencing, full continuous-loop dry-run.
- Not building real calendar integration or real partner matching — both explicitly mock/prototype per PRD non-goals.

## 4. Priority fix: M7 schema/logic duplication (discovered during sync, not yet on any branch)
- **What happened:** AIA's M7 merge added `app/schemas/evolution.py` (`IdentityEvolutionProposal`/`ProposedChange`, add/remove/reweight model) and `app/schemas/report.py` (`WeeklyReport` with `gapScoreStart/End/Delta`, `highlights`, `simulated`) — **separate from my own M7 `app/schemas/agent_run.py`** which defines classes with the *same names* but different (simpler) shapes. `app/schemas/__init__.py` now imports both, so `from app.schemas import WeeklyReport` silently resolves to AIA's version (import order), while my own `app/api/agents.py`/`app/services/identity/agent_runs.py` still import their own `agent_run.py` versions directly — a live ambiguity, not just cosmetic.
- **The functional break:** AIA also shipped complete, working generation logic — `app.services.identity.weekly_report.generate_weekly_report(...)` and `app.services.identity.evolution_agent.propose_identity_evolution(...)` (with real `MIN_EVIDENCE_CITATIONS=3` enforcement and a deterministic v0 fallback when no LLM is available) — exported from `app/services/identity/__init__.py`. **Nothing calls them.** My M7 endpoint (`POST /agents/runs`) still runs its own hand-rolled prompt-formatting against my own duplicate schemas, ignoring AIA's real implementation entirely — same "component built, wiring never happened" pattern as M1's evidence hook and M2's GapSnapshot, except this time the dead code is *mine*, not a stub waiting for me.
- **My `accept_evolution` endpoint is also wrong relative to AIA's real model:** it does `twin_repository.create_confirmed_version(db, user_id, proposal.proposedAttributes)` — a flat full-attribute-list replace. AIA's `ProposedChange` is an add/remove/reweight diff against the *current* Declared Self, not a replacement list. Accepting a real proposal today would silently drop any attribute not mentioned in the proposal.
- **Fix (mine to do — I own `app/schemas/` and the endpoint wiring):**
  1. Delete `app/schemas/agent_run.py`'s `WeeklyReport`/`IdentityEvolutionProposal` classes (keep `AgentRunRequest`/`AgentRunResult`, retyped to reference AIA's schemas instead).
  2. Rewrite `app/services/identity/agent_runs.py` to call `generate_weekly_report(...)` and `propose_identity_evolution(...)` directly (passing `declared_self`, `events`, `gap_result` — reusing M2's `orchestration.recompute_and_persist` internals for the Gap inputs) instead of hand-formatting prompts.
  3. Rewrite `accept_evolution` to apply `proposal.proposedChanges` as a diff: `add` inserts a new `IdentityAttribute`, `remove` drops one by id, `reweight` updates `weight` on an existing one — against the current confirmed Declared Self's attribute list — then `create_confirmed_version` with the *merged* result, not the raw proposal.
  4. Update `evolution_repository`/`app/models/identity_evolution.py` field names to match AIA's shape (`proposalId`→`id` mapping, `proposedChanges` instead of `proposed_attributes`) — small migration.
  5. Re-run/update M7's tests (`test_agent_runs.py`, `test_evolution_accept_reject.py`) against the corrected behavior.
  6. Clean up the stray `weekly_report_v1.md` prompt edit (mustache placeholders) — since AIA's real `generate_weekly_report` builds its prompt inline in Python and doesn't load this file at all, either delete the file or leave it clearly marked unused to avoid a future reader assuming it's live.

## 5. Detailed work plan (actual M8 checkboxes)

### 5.1–5.3 Models / endpoints
1. `app/models/calendar_event.py` (`CalendarEventModel`: id, user_id, title, event_time, leverage_tag) + migration `0008_m8.py` (same migration also adds `partner_profile` fixture table if not just hardcoded in-memory — see Open Question 1).
2. `app/api/calendar.py` — `GET /api/v1/calendar/plan-view` (upcoming seeded events, sorted).
3. `app/api/partners.py` — `GET /api/v1/partners/matches` (returns 5 seeded fake profiles, clearly labeled `"prototype": true`).
4. Cache pre-warm: a small `app/workers/prewarm.py` script (or a step added to `seed.py`) that calls `stack_orchestration.refresh_stack` once more for the demo user with the *real* configured providers (if keys present) so the first live demo click isn't a cold cache — no-op safely if `LLM_PROVIDER`/`SEARCH_PROVIDER` are still `fake`.
5. Bedrock failover: one manual/integration-style test that swaps `LLM_PROVIDER=bedrock` and confirms `BedrockLLMProvider` is selected and raises the documented `NotImplementedError` cleanly (i.e. "tested once" per the checkbox — not a live AWS call, since no credentials are expected to exist).
6. Observability: structured JSON logging config in `app/core/logging.py` (`trace_id`/`user_id` fields per techstack.md §22), applied to `main.py` startup. LangSmith explicitly optional — skip unless already configured.

### 5.4 Seeds
7. Seed 2–3 fixed calendar leverage events (prd.md F9 example: "college presentation, Friday") and the 5 fake partner profiles (F10) into `seed.py`.

### 5.5 Tests
- `test_calendar_endpoint.py`, `test_partners_endpoint.py`, `test_evolution_diff_apply.py` (the corrected accept logic), `test_bedrock_failover.py`.

## 6. Dependencies & sequencing
- Merge order: **any order if gates green; prefer Backend seeds → AIA tuning → AIS prewarm** (per milestones.md M8 — the only milestone without a strict role sequence).
- The §4 fix should land *before* or *alongside* this branch's other work since it's a correctness issue on `dev` right now, not exclusively an M8-labeled task — flagging in case you'd rather split it into its own immediate commit ahead of the rest of M8.

## 7. Risks
- **Cut rule**: milestones.md explicitly says M8 is optional and P2 items get dropped first if behind schedule. The §4 fix is *not* optional (it's a real bug), but the calendar/partner/observability checkboxes genuinely are — I'll sequence the fix first and treat the rest as droppable if time runs short.
- Re-typing `AgentRunResult` to reference AIA's schemas is a breaking response-shape change for M7's endpoint — acceptable since M7 only just merged and no UI is wired to the old shape yet (per the repo's UI/UX-is-separate note in guidelines.md).

## 8. Open Questions
1. **Partner profiles: a new small DB table, or a hardcoded in-memory fixture list (like `fallback_resources.py`)?** — **Recommendation:** hardcoded in-memory list — F10 is explicitly "mock only," no persistence value, matches the lightest-weight prior art (`fallback_resources.py`).
2. **Confirm priority: fix §4 first as its own commit, then the rest of M8?** — **Recommendation:** yes — keeps the correctness fix reviewable separately from the optional P2 additions.

## 9. Execution checklist
- [ ] Answer open questions → approve → I sync `backend` from `dev`, branch `backend-m8`, fix §4 first, then implement the rest, test, show commit(s), push.
