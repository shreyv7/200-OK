# Implementation Plan — Backend — M1

## 1. Context
- Role: **backend**
- Milestone: **M1 — Evidence Pipeline + Twin Shell**
- PRD features touched: F2 (Evidence Engine + Revealed Self, P0), MCP adapter boundary, seed history start
- Techstack modules touched: Evidence Intelligence Layer, MCP Integration Layer (fixture adapters only), Data Layer (Postgres/SQLite for CI), API Layer (`/api/v1/evidence`)
- Goal: One idempotent ingest path so any event — seeded or live — flows through the same pipeline and becomes queryable; a fixture MCP adapter proves the adapter boundary; the 21-day seeded Aarav history is loadable and reproducible.

## 2. Scope (in)
Per `milestones.md` M1 → Backend checkboxes only:
- [ ] `POST /api/v1/evidence` idempotent ingest (hash/dedupe)
- [ ] `GET /api/v1/evidence` windowed list
- [ ] Persist EvidenceEvents; emit internal `evidence.created`
- [ ] MCP adapter interface + at least one fixture adapter (e.g. github/youtube simulated)
- [ ] Simulator inject endpoint (dev-only): doomscroll burst, time advance
- [ ] Seed: 21-day Aarav simulated history, labeled `simulated: true`
- [ ] User + capacity row for demo profile

All P0 (F2 is P0).

## 3. Scope (out) — explicitly not touched
- **AIA M1:** evidence enrichment (`identityAttributeIds`/`a_ik`), Revealed Self aggregate builder, Twin read model, dead-letter rejection of invalid events. Per `team-agent-prompts-m1.md`, AIA "waits for Backend M1 evidence ingest contract if not merged yet" — I own being that contract.
- **AIS M1:** `evidence.created` Coordinator hook (no-op), DecisionPacket placeholder, fixture stack-invalidation flag, Reflection/Ledger evidence-ID intake.
- No Gap math (M2). No LLM calls anywhere in this milestone's ingest/simulator path (Tier-0, per techstack.md §3).
- Not touching AIA's `app/services/identity/` or AIS's `app/agents/`, `app/services/recommendation/`, or their `app/providers/llm/`, `app/providers/search/` package variants — `integration-notes.md` seam #3 (llm.py vs llm/ package duplication) is noted but consolidation is explicitly deferred ("M1+"), not a blocking Backend M1 checkbox.
- Not fixing AIS's `app/agents/_contracts.py` TEMP mirror or snake_case/camelCase drift — that's AIS's stated M1 migration task, not mine.

## 4. Current repo state (verified against merged `dev`/`main`, commit `5824e93`)
- `app/schemas/evidence.py` — my M0 `EvidenceEvent`/`RawMCPPayload` contract, unmodified since M0 merge. This is the canonical shape I build the ingest endpoint and adapter around.
- `app/models/evidence_event.py` + migration `0001_initial.py` — table exists (`user_id`, `timestamp`, `source`, `type`, `category`, `value`, `base_weight`, `event_metadata`, `simulated`, `dedupe_hash` unique).
- `app/models/user.py` — `User` model with `capacity` field already present.
- `app/repositories/` — still empty (per my M0 decision, deferred). First real content lands this milestone.
- `app/integrations/mcp/{github,youtube,calendar,drive,notion,cursor,vscode}/` — empty packages, ready for the fixture adapter.
- `app/workers/seed.py` — still the M0 stub ("not yet implemented").
- `app/core/security.py` — `get_current_user_id` with `AUTH_BYPASS` local dev bypass, usable as-is.
- Test infra already in place from the merge: `pytest.ini` (`testpaths = tests`), `requirements-dev.txt` (adds `langgraph`), `tests/test_no_vendor_leak.py` (scans `app/agents` + `app/services/recommendation` only — my evidence code isn't in its scan path, so no interference either direction), `tests/test_schema_imports.py`.
- **Known cross-role seam (integration-notes.md #3):** `app/providers/llm.py` (mine) and `app/providers/llm/` (AIS's package) coexist on disk — a real Python import ambiguity, but not in my ingest/adapter/seed code path, so it doesn't block M1. Flagged as Risk, not fixed here (out of scope per guidelines.md §9.7 role isolation — AIS should resolve their own duplicate).

## 5. Detailed work plan

### 5.1 Contracts / schemas
1. **What:** No new frozen contract needed — `EvidenceEvent`/`RawMCPPayload` already cover the ingest/list/adapter shapes. Add one small internal-only DTO if the ingest endpoint needs a request body distinct from the full `EvidenceEvent` (e.g. client shouldn't supply `id`/`dedupe_hash` — server generates them).
   **Why:** keep `app/schemas/` the single frozen surface AIA/AIS import from (integration-notes.md table).
   **How:** Add `EvidenceIngestRequest` to `app/schemas/evidence.py` only if the round-trip test in 5.5 proves the bare `EvidenceEvent` is awkward as a request body; otherwise skip this step entirely (avoid unnecessary schema surface).
   **Done when:** decision made and either the DTO is added with a test, or explicitly skipped in the Done report.

### 5.2 Core logic
2. **What:** `app/repositories/evidence_repository.py` — first real file in this package.
   **Why:** milestones.md §1 module map assigns `repositories/` to Backend.
   **How:** `create_if_not_exists(session, event: EvidenceEvent, dedupe_hash: str) -> tuple[EvidenceEventModel, bool]` (bool = was newly created); `list_window(session, user_id, since=None, until=None, limit=100) -> list[EvidenceEventModel]` ordered by timestamp.
   **Done when:** unit tests cover: fresh insert, duplicate-hash no-op (returns existing row, `created=False`), and windowed ordering.

3. **What:** `app/services/evidence_service.py` — dedupe-hash computation + idempotent ingest orchestration + in-process `evidence.created` emission.
   **Why:** F2 "every event flows through one pipeline"; guidelines.md §9.2 "One evidence path."
   **How:** `dedupe_hash = sha256(f"{userId}|{source}|{type}|{timestamp.isoformat()}|{value}")` (natural-key hash; simulator/seed generators add a synthetic discriminator into `type`/`metadata` so distinct synthetic events never collide). A minimal in-process listener registry: `on_evidence_created(callback)` / internally call all registered callbacks after a successful new insert. No Celery/Redis — synchronous, Tier-0 latency budget.
   **Done when:** calling `ingest(event)` twice with identical natural key persists once; registered callbacks fire exactly once per newly created event, never on duplicates.

### 5.3 Integration / wiring
4. **What:** `app/api/evidence.py` — `POST /api/v1/evidence`, `GET /api/v1/evidence`; register router in `main.py`.
   **Why:** milestones.md M1 Backend checkboxes 1–2.
   **How:** `POST` accepts an `EvidenceEvent`-shaped body (or the new DTO from 5.1), calls `evidence_service.ingest`, returns `201` on new / `200` on duplicate with the persisted record; `GET` accepts `since`, `until`, `limit` query params, requires `get_current_user_id` dependency, calls `evidence_repository.list_window`.
   **Done when:** integration test: POST then GET returns it inside the window; repeated identical POST does not duplicate rows; response schema matches `EvidenceEvent`.

5. **What:** `app/integrations/mcp/base.py` — `EvidenceAdapter` ABC (`normalize(raw: RawMCPPayload) -> EvidenceEvent`); concrete `app/integrations/mcp/github/adapter.py` (`FixtureGithubAdapter`) mapping a canned commit-shaped fixture to an `EvidenceEvent` with `simulated=True`.
   **Why:** milestones.md M1 Backend checkbox 4; prd.md §7 MCP data bridge contract.
   **How:** Follow `prd.md` §7's `EvidenceAdapter` interface literally — the fixture reads a static sample dict (in `tests/fixtures/` or adapter-local), never a live GitHub call.
   **Done when:** `FixtureGithubAdapter().normalize(sample)` returns a valid `EvidenceEvent`; feeding that output through `evidence_service.ingest()` persists it exactly like any other event (no special-cased path).

6. **What:** `app/api/simulator.py` — dev-only `POST /api/v1/simulator/inject`, body `{"scenario": "doomscroll_burst" | "time_advance", "params": {...}}`; router mounted only when `settings.env == "local"`.
   **Why:** milestones.md M1 Backend checkbox 5; F2 "dev-only simulator panel... injects events live on stage."
   **How:** `doomscroll_burst` generates N `focus_drift`-category events via a second fixture adapter (`app/integrations/mcp/trellis/adapter.py`, source=`trellis`) — never a raw table insert, so guidelines.md §9.2 ("no pre-scored Gap inserts from the simulator") holds structurally; `time_advance` re-timestamps a batch for demo pacing.
   **Done when:** hitting the endpoint locally produces real rows visible via `GET /evidence`; requesting it with `env != local` yields 404 (router not mounted).

### 5.4 Seeds / fixtures
7. **What:** Implement `app/workers/seed.py` for real (currently the M0 stub): create/upsert the demo `User` row (fixed id, default capacity), generate 21 days of simulated `EvidenceEvent`s via the fixture adapters (mix of `mission_completed`, `passive_learning`, `focus_drift` per prd.md §9 weight table), insert every one through `evidence_service.ingest()` (never a raw bulk INSERT — must exercise the real pipeline), all `simulated=True`.
   **Why:** milestones.md M1 Backend checkboxes 6–7; F2 acceptance.
   **How:** Fixed RNG seed for reproducibility (prd.md §11: "every demo run is identical"); ~70-100 events across 21 days (sparse creation, more passive/drift, matching Aarav's persona in prd.md §4).
   **Done when:** `python -m app.workers.seed` is idempotent (re-running doesn't duplicate rows, thanks to dedupe), produces a single demo `User` row and the expected event count on a clean DB.

### 5.5 Tests
8. **What:** `tests/test_evidence_ingest.py`, `tests/test_mcp_adapter.py`, `tests/test_simulator.py`, `tests/test_seed.py`.
   **Why:** Merge Gates 1 & 3 (milestones.md M1); required for `pytest -q` to stay green per your CI instructions.
   **How:** Use the existing `sqlite:///./ci_test.db` DATABASE_URL pattern (matches your specified run command) so tests don't need a live Postgres. `test_simulator.py` explicitly asserts injected rows carry no pre-scored Gap/score field and only reached the DB via the adapter+service path.
   **Done when:** `cd services/api && AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q` passes, including all pre-existing tests (no regressions to AIA's `tests/identity/` or AIS's `tests/test_*` files).

### 5.6 Demo / merge-gate verification
9. **What:** Manual/CI verification pass against `milestones.md` M1 Merge Gates 1–3 (gate 4 is AIA's).
   **Why:** required before requesting merge `backend-m1` → `backend` → `dev`.
   **How:** run seed fresh, time `POST` → `GET` round trip (target comfortably <2s, should be near-instant with no LLM in path); confirm CI workflow (`.github/workflows/backend-ci.yml`) runs green on push to `backend-m1`.
   **Done when:** all three backend-relevant gates pass and are recorded in the Done report.

## 6. Dependencies & sequencing
- No hard blocking dependency on AIA/AIS M1 work — they consume my `evidence.created` hook and `app/schemas/evidence.py` (unchanged), not the reverse.
- Per `team-agent-prompts-m1.md`: AIA waits for my ingest contract before wiring their aggregate builder against real data; AIS's coordinator no-op hook attaches to my emission point whenever ready.
- Merge order: **Backend → AIA → AIS → `dev` → `main`** (confirmed by both `milestones.md` and `integration-notes.md`).
- Merge Gate checklist (copied from `milestones.md` M1):
  1. Seed load produces ≥ N events; all marked simulated where appropriate.
  2. Live `POST /evidence` appears in GET within pipeline SLA (target <2s including recompute hook).
  3. Simulator inject uses same adapters — no pre-scored Gap fields inserted.
  4. AIA aggregate tests pass on seeded Aarav fixture. *(their gate; my seed data must support it — not my checkbox to close)*

## 7. Risks
- **`app/providers/llm.py` vs `app/providers/llm/` duplication** (integration-notes.md seam #3) could cause ambiguous imports if anything in my ingest path ever imports from `providers` — verified it doesn't; flagging only so it doesn't silently break later when someone does touch it.
- **Dedupe hash collisions in seed-generated data** — 21 days of similar synthetic events risk colliding on a naive natural-key hash. Mitigated by embedding a synthetic per-event discriminator (index or minute-level jitter) in the generator.
- **In-process event-bus scope creep** — kept to a plain callback list; no framework, since Celery is explicitly deferred (techstack.md §26).
- **SQLite vs Postgres dialect drift** — your test run command uses `sqlite:///./ci_test.db`, but the models/migration target Postgres (`JSON`, `server_default=sa.false()` etc.). Need to confirm SQLAlchemy models don't use Postgres-only types that break under SQLite in CI (current models use portable types — `JSON`, `String`, `Float`, `Boolean`, `DateTime` — should be fine, but I'll verify with an actual test run before calling this closed).

## 8. Open Questions
1. **Ingest request DTO vs reusing `EvidenceEvent` directly** — should `POST /api/v1/evidence` accept the full `EvidenceEvent` (client supplies `id`), or a slimmer request DTO where the server generates `id`/dedupe hash?
   - **Recommendation:** slim `EvidenceIngestRequest` (no `id` field) — client-supplied `id`s invite collision/spoofing across sources; server-generated `id` + hash is safer and matches "idempotent ingest" framing in milestones.md.
2. **Fixture adapter set** — milestones.md says "e.g. github/youtube simulated." Build one (github) or two (github + a trellis-sourced adapter for the simulator)?
   - **Recommendation:** two — `FixtureGithubAdapter` (satisfies the literal M0/M1 checkbox) plus a `trellis`-sourced adapter feeding the simulator, since the simulator must not bypass the adapter boundary (guidelines.md §9.2) and github fixtures don't naturally model doomscroll/focus-drift events.
3. **Seed volume** — no exact count specified in PRD beyond "21-day simulated history."
   - **Recommendation:** ~70-100 events total, weighted toward passive/drift with sparse creation (matches Aarav's persona — prd.md §4 "tutorials watched but nothing published"), tunable later in M2/M8 for projector legibility.
4. **`llm.py`/`llm/` and `search.py`/`search/` duplication cleanup** — not in my M1 checkbox list, but it's a real repo defect right now. Should I leave it entirely untouched (AIS's problem per role isolation), or file it as a note in the Done report for a human to route to AIS?
   - **Recommendation:** leave the code untouched (respect role isolation, guidelines.md §9.7); just note it in the Done report so a human can flag it to AIS/AIA rather than silently rediscovering it in M2+.

## 9. Execution checklist (after you approve)
- [ ] Answer open questions
- [ ] Approve this plan
- [ ] Agent syncs `backend` with `dev`, creates/checks out `backend-m1`
- [ ] Implement
- [ ] Run `AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q`
- [ ] Show commit message(s) → wait for approval → commit
- [ ] Push `backend-m1`; confirm `backend-ci.yml` green
- [ ] Done report
