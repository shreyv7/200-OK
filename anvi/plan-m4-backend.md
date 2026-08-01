# Implementation Plan — Backend — M4

## 1. Context
- Role: **backend**
- Milestone: **M4 — Curation Core (Bottleneck + Next Step + Stack)**
- PRD features touched: F5 P0 (Next Step + Missing Action lenses, Continuous Curation Engine)
- Techstack modules touched: Recommendation Engine (retrieval chain), Data Layer (resource cache, interventions shell), Background Processing (Tier-2 curation job)
- Goal: A working `stack/refresh` → `stack/active` loop backed by a real cache→Tavily→fallback retrieval chain, persisted interventions, and correct source-honesty badges — with AIS's existing (currently fixture-only) `assemble_stack()` now receiving real providers to build against.

## 2. Scope (in)
Per `milestones.md` M4 → Backend checkboxes only:
- [ ] Resource cache table; seeded fallback resources
- [ ] `GET /api/v1/stack/active`, `POST /api/v1/stack/refresh`
- [ ] Persist interventions/hypotheses shell (verdict pending)
- [ ] Celery (or background task): Tier-2 curation job
- [ ] SearchProvider adapter: cache → Tavily (1.5s timeout) → seeded fallback
- [ ] Source badges on every resource: Live web / Cached web / Curated fallback
- [ ] Prepared intervention storage for trigger path (at least one cached stack)

All P0 (F5 Next Step + Missing Action is P0).

## 3. Scope (out) — explicitly not touched
- **AIA M4:** real Gemini-backed bottleneck diagnosis (replacing M2's rule-based `bottleneck_v0.py`), low-confidence "small experiment" flagging, Growth Decision Engine re-run logic. My M2 `orchestration.py` already surfaces whatever `decision_packet.bottleneck_candidates` AIA's recompute call returns into `DashboardSummary.bottleneck` — this should keep working unmodified once AIA's M4 work replaces the v0 heuristic with a real one, since the `BottleneckPacket` schema doesn't change.
- **AIS M4:** the actual retrieval ranking / explanation generation / replacement policy inside `assemble_stack()` — currently a fixture-only stub (`app/services/recommendation/stack_assembler.py`, explicit comment: *"M1 returns a fixture-valid stack. M4+ will retrieve, rank, and explain."*). Backend's job is to give that function real `SearchProvider`/`LLMProvider` instances and call it; not to rewrite its ranking/assembly logic.
- Not building Guardian/capacity gating (M5) or Trust Ledger dismiss/unlearning (M5) — the "interventions/hypotheses shell" here is verdict-`pending`-only, no dismiss/complete transitions yet.
- Not implementing real Celery/Redis infrastructure unless needed — see Open Question 2.

## 4. Current repo state (verified against `origin/dev` @ `2198c79`, post M3 merge)
- **A third instance of the "component built, wiring dangling" pattern**, this time in AIA's M3 work: `app/agents/nodes/identity/node.py`'s `IdentityAgentNode.extract_declared_self()` calls `llm_provider.generate_structured(schema=DeclaredSelf, prompt=prompt)` — but my frozen `LLMProvider.generate_structured(self, schema: dict, messages: list[dict], opts=None)` requires a JSON-schema **dict** (not the Pydantic class) and **`messages`** (not a single `prompt` string). Wrapped in a broad `except Exception`, so it never crashes — it just silently always falls through to a hardcoded two-attribute heuristic fallback, meaning real Gemini extraction is currently unreachable through that node even after wiring. **This is an M3-era defect in an AIA-owned file, out of M4's scope to fix** (M4 doesn't touch onboarding) — flagging prominently in this plan and the eventual Done report rather than silently patching another role's module. Also unrelated to M4: nothing in `app/` currently instantiates `IdentityAgentNode` at all (same dangling pattern as M1's evidence hook and M2's GapSnapshot, both of which *were* in my own milestones to close — this one isn't).
- **AIS's `assemble_stack()`** (`app/services/recommendation/stack_assembler.py`) already has the exact shape Backend needs to call: accepts a `DecisionPacket`, optional `candidates`, `capacity_tier`, `ledger_weights`, and **injectable** `llm`/`search` provider kwargs (falling back to `FakeLLMProvider`/`FakeSearchProvider` if not passed) — comment: *"Backend Depends() will inject real providers in M3+."* It currently ignores whatever providers it's given and always returns two hardcoded `"Curated fallback"`-badged elements — that's fine; my job is to call it correctly and pass real providers, not to fix its internals.
- **`app/providers/search/base.py`** docstring literally says: *"Retrieval facade — cache → live → fallback chain lives in Backend adapter."* — confirms the chain-building checkbox is unambiguously mine.
- `app/schemas/stack.py` (M0, frozen) already defines `SourceBadge = Literal["Live web", "Cached web", "Curated fallback"]`, `IdentityStack`, `StackElement`, `StackExplanation` — no schema changes needed for the stack shape itself.
- No `aia-m4`/`ais-m4` branches exist yet — like M3, I'm building the reference contract this time, not reading ahead.

## 5. Detailed work plan

### 5.1 Contracts / schemas
- No new frozen schema needed beyond what M0 already defines (`IdentityStack`, `StackElement`, `SourceBadge`). One small addition: `app/schemas/intervention.py` → `InterventionRecord` (`id`, `userId`, `hypothesisId`, `stack: IdentityStack`, `verdict: Literal["pending"]`, `createdAt`) for the persisted shell's API-facing shape — kept separate from M5's full `LedgerEntry` (M0) which already models verdict transitions; this is deliberately narrower.

### 5.2 Core logic
1. **What:** `app/models/resource_cache.py` (`ResourceCacheModel`: id, query_hash, title, url, extract, source, badge, fetched_at) + `app/models/intervention.py` (`InterventionModel`: id, user_id, hypothesis_id, stack_json, verdict default `"pending"`, created_at) + migration `0004_curation.py`.
   **Why:** milestones.md M4 Backend checkboxes 1 & 3.
   **Done when:** tables migrate cleanly; round-trip repository tests pass.

2. **What:** `app/repositories/resource_cache_repository.py` (`get_fresh(query_hash, ttl) -> list[Document] | None`, `store(query_hash, documents, badge)`), `app/repositories/intervention_repository.py` (`create`, `get_active(user_id) -> InterventionModel | None`, i.e. latest by `created_at`).
   **Why:** repository pattern consistency; Backend owns persistence.

3. **What:** `app/providers/search/tavily.py` — `TavilySearchProvider(SearchProvider)`, real Tavily API call, hard 1.5s timeout (prd.md §8 retrieval fallback logic step 2).
   **Why:** milestones.md M4 checkbox 5; only file allowed to import the Tavily SDK/client.
   **How:** mirrors `gemini.py`'s pattern — lazy import inside `__init__`/call, config-gated (`TAVILY_API_KEY`), never imported unless selected.

4. **What:** `app/services/recommendation/retrieval_chain.py` (Backend-owned, distinct from AIS's `stack_assembler.py`) — `search_with_fallback(db, query, seeded_fallback_fn) -> tuple[list[Document], SourceBadge]` implementing prd.md §8's exact chain: fresh cache hit → return `"Cached web"`; else call `TavilySearchProvider` with the 1.5s timeout → on success, persist to cache, return `"Live web"`; on timeout/quota/malformed → seeded fixture set, return `"Curated fallback"`.
   **Why:** the actual "SearchProvider adapter: cache → Tavily → seeded fallback" + "source badges" checkboxes — this is the concrete chain the docstring in `search/base.py` says belongs here.
   **Done when:** unit tests force each of the three paths (mock a cache hit, mock a slow/failing Tavily call, mock a real success) and assert the correct badge every time; retrieval failure never raises — always returns the fallback set.

### 5.3 Integration / wiring
5. **What:** `app/core/config.py` + `core/di.py` — `tavily_api_key`, `search_provider: Literal["fake","tavily"] = "fake"`; `get_search_provider()` DI function mirroring `get_llm_provider()`.
   **Why:** same DI pattern as M3's LLMProvider; defaults to `FakeSearchProvider` so CI/local dev never needs a live Tavily key.

6. **What:** `app/api/stack.py` — `GET /api/v1/stack/active` (reads `intervention_repository.get_active`, 404 if none — but see step 7 for why this should rarely 404 in practice), `POST /api/v1/stack/refresh` (builds/loads the current `DecisionPacket` — reusing M2's `orchestration.recompute_and_persist` output or a fresh recompute — fetches real search candidates via `retrieval_chain.search_with_fallback`, calls AIS's `assemble_stack(decision_packet, candidates=..., search=get_search_provider(), llm=get_llm_provider())`, persists the result via `intervention_repository.create`).
   **Why:** milestones.md M4 Backend checkbox 2.
   **How:** `refresh` runs the retrieval + assembly as a `BackgroundTasks` job (see Open Question 2) so the endpoint returns immediately with a "refreshing" ack while the real stack populates — matching prd.md's Tier-2 latency budget (1–10s, never blocks interaction) and F4's "retrieval failure never blocks the feed morph" requirement.
   **Done when:** `POST /stack/refresh` → poll `GET /stack/active` → a stack with ≥1 action + ≥1 resource and full explanations appears; refresh never 500s even if Tavily is unreachable.

7. **What:** Seed script extension (`app/workers/seed.py`) — pre-bake one `InterventionModel` row for the demo user at seed time (a "Curated fallback"-badged stack via the same `retrieval_chain`/`assemble_stack` path, not a hand-written row) so `GET /stack/active` never 404s on a fresh demo environment.
   **Why:** milestones.md M4 Backend checkbox 7 ("Prepared intervention storage for trigger path — at least one cached stack").
   **Done when:** running seed produces exactly one active intervention for the demo user, idempotent on re-run.

### 5.4 Seeds / fixtures
- Seeded fallback resources: a small static list of `Document`s (5–8 entries) tagged by bottleneck/identity, used as the final link in the retrieval chain — lives alongside the fixture adapters (`app/integrations/mcp/` already has the pattern) or a new `app/services/recommendation/fixtures/fallback_resources.py`. Kept small; this is fallback content, not a catalog (that's M6's job).

### 5.5 Tests
- `tests/test_resource_cache.py`, `tests/test_retrieval_chain.py` (all three badge paths), `tests/test_stack_endpoints.py` (refresh → active round trip, never-empty guarantee, capacity_tier passthrough), `tests/test_search_provider_di.py` (mirrors M3's `test_llm_provider_di.py`).
- **Done when:** `cd services/api && AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q` green.

### 5.6 Demo / merge-gate verification
- Manual pass against Merge Gates 1–4: (1) refresh produces ≥1 action + ≥1 resource with explanations — note this depends on AIS's M4 work actually populating real elements, not just my M0-stub-calling wiring, so this gate may only fully close once AIS's M4 lands; (2) confirm at least one path can show `"Live web"`/`"Cached web"` once a real Tavily key is configured (not required for CI, but I'll verify the code path is reachable); (3) bottleneck already appears in dashboard summary since M2 — reverify unaffected; (4) simulate a Tavily timeout and confirm the fallback stack still returns.

## 6. Dependencies & sequencing
- **Soft dependency on AIS's M4 work**: my `POST /stack/refresh` calls `assemble_stack()` today and will get back the same two hardcoded fixture elements AIS's stub currently produces — real ranking/retrieval-aware assembly only appears once AIS updates that function. This doesn't block my own checkboxes (the cache/chain/endpoints/persistence all work standalone and are independently testable), but merge gate 1 fully closing depends on AIS's M4 slice landing too — matching the stated merge order.
- Merge order: **Backend (cache/search/stack API) → AIA (bottleneck + decision) → AIS (graph + assembly)** — this milestone's order differs slightly from the M0–M3 "Backend → AIA → AIS" default; copied verbatim from `milestones.md` M4.
- Merge Gate checklist (copied from `milestones.md` M4):
  1. Refresh produces stack with ≥1 action + ≥1 resource; explanations present.
  2. At least one demo path shows Live web or Cached web badge.
  3. Bottleneck visible in dashboard summary. *(already true since M2)*
  4. Retrieval failure still yields seeded stack; feed morph never blocked.

## 7. Risks
- **`IdentityAgentNode`/`LLMProvider` signature mismatch (§4)** — not fixed here (out of M4 scope), but real Gemini onboarding extraction silently never fires until it is. Recommend routing to AIA explicitly, separate from this milestone.
- **Tavily 1.5s timeout under test/CI** — must not let any test accidentally make a real network call; `search_provider` defaults to `fake`, and the chain's Tavily branch is only unit-tested with a mocked/injected provider, never the real SDK.
- **Background task failure visibility** — if `BackgroundTasks`-run refresh fails silently, `stack/active` would just keep serving the last good stack (acceptable — matches "never empty" guarantee) but errors should still be logged, not swallowed silently.

## 8. Open Questions
1. **Should Backend fix AIA's `IdentityAgentNode` call-site mismatch as a quick prerequisite (like the M3 GapSnapshot fix), or strictly leave it out of scope this milestone?**
   - **Recommendation:** leave it out of scope and just flag it clearly — unlike the GapSnapshot case (which was Backend's own explicitly-named wiring job per AIS's docstring), this bug lives inside AIA's file and M4 doesn't touch onboarding at all; touching it would be scope creep into an unrelated milestone. Report it plainly in the Done report instead.
2. **Celery vs. FastAPI `BackgroundTasks` for the Tier-2 curation job?** No Redis/Celery worker infra exists yet even though `redis_url` is in config.
   - **Recommendation:** `BackgroundTasks` — no new infra, matches the techstack's explicit "hackathon speed" column allowance ("Celery (or background task)"), and this milestone's latency budget (1–10s, non-blocking) doesn't need a durable job queue yet.
3. **Resource cache TTL / freshness window** — prd.md doesn't specify an exact cache lifetime for search results.
   - **Recommendation:** a simple fixed TTL (e.g. 1 hour) is enough for a 24h hackathon demo; not worth making configurable per-resource yet.

## 9. Execution checklist (after you approve)
- [ ] Answer open questions
- [ ] Approve this plan
- [ ] Agent syncs `backend` with `dev`, creates/checks out `backend-m4`
- [ ] Implement
- [ ] Run `AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q`
- [ ] Show commit message(s) → wait for approval → commit
- [ ] Push `backend-m4`; confirm CI green
- [ ] Done report
