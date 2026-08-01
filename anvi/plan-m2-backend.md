# Implementation Plan — Backend — M2

## 1. Context
- Role: **backend**
- Milestone: **M2 — Deterministic Gap, KPIs, Dashboard API**
- PRD features touched: F3 (Identity Gap Score + Lattice Visualization, P0)
- Techstack modules touched: Identity Intelligence Layer (consuming AIA's pure functions), Growth Decision Engine (consuming AIA's packet builder), API Layer (`/dashboard/summary`, `/identity`, lattice endpoint), Data Layer (new KPI snapshot table)
- Goal: Wire AIA's already-implemented deterministic Gap/KPI/bottleneck functions into real persisted state and REST endpoints, so the Identity Gap score visibly moves on every event with zero LLM calls in the path, and the dashboard/lattice popover can bind to a single API.

## 2. Scope (in)
Per `milestones.md` M2 → Backend checkboxes only:
- [ ] Persist KPI snapshots: Gap, Alignment, Create:Consume, Consistency, Momentum
- [ ] `GET /api/v1/dashboard/summary` — twin, KPIs, breakdown, bottleneck placeholder
- [ ] `GET /api/v1/identity` — versioned Declared Self
- [ ] WebSocket or 2s poll payload for Gap updates (poll acceptable for MVP per techstack.md §3/prd.md §11 — see Open Question 3)
- [ ] Lattice strut → contributing events query (timestamp, weight, decayed contribution)
- **Wiring, not a separate checkbox but required to satisfy Merge Gate 2:** call AIA's `recompute_user_gap` from the `evidence.created` hook I built in M1, and persist the resulting KPI snapshot.

All P0 (F3 is P0).

## 3. Scope (out) — explicitly not touched
- **AIA M2 (already implemented on their pushed `aia-m2` branch, unmerged):** the actual Gap formula (`app/services/identity/scoring/gap.py`), Create:Consume/Consistency/Momentum math, `RevealedSelfAggregates` builder, `BottleneckCandidate`/`DecisionPacket` construction (`app/services/decision/packet.py`), `LatticeStrutDetail` computation, evidence enrichment (`app/services/identity/enrichment.py`). I consume these as pure functions; I do not reimplement or modify any Gap arithmetic.
- **AIS M2:** stack-invalidation consumption of the `DecisionPacket`, no-empty-stack guarantee on dashboard load — not mine.
- No LLM calls anywhere in this milestone's path (Tier-0 per techstack.md §3) — AIA's bottleneck v0 is rule-based, not Gemini-backed yet (that's M4).
- Not building the real Mirror Interview (M3) — but M2's `GET /api/v1/identity` and dashboard need *some* confirmed Declared Self to operate on, which doesn't exist yet. Addressed in §5.4 and Open Question 1.

## 4. Current repo state (verified by reading AIA's pushed `origin/aia-m2` branch — unmerged to `dev`/`main`, same sequencing situation as M1)
- **`origin/main`/`origin/dev` are still at the M0 merge commit (`5824e93`)** — my `backend-m1` work and AIA's `aia-m1`/`aia-m2` work are all pushed but unmerged. I'm building M2 against my own `backend-m1` (which has the real evidence pipeline) plus AIA's pushed `aia-m2` contents (read-only reference, since I can't merge their branch myself) — flagged as Open Question 4, same pattern as M1.
- **AIA has already delivered, on `aia-m2`:**
  - `app/services/identity/scoring/gap.py` — pure `GapResult`, `AttributeBreakdown`, `CreateConsumeResult`, `decay_weight`, `compute_revealed`, `compute_gap_score`, `compute_create_consume`, `compute_consistency`, `compute_momentum`.
  - `app/services/identity/recompute.py` — `recompute_user_gap(user_id, declared_self, events, prior_gap_score, window_days, ref_time) -> (GapResult, KPISnapshot, DecisionPacket)`. **This is the single call Backend needs to invoke on every accepted evidence event.**
  - `app/services/identity/kpi.py` — `KPISnapshot` dataclass: `gapScore, alignment, createConsumeRatio, createPoints, consumePoints, driftPoints, consistencyScore, momentumDelta` (camelCase, but field names differ slightly from my frozen `schemas/gap.py` `GapBreakdown` — `alignment` vs `alignmentScore`, `consistencyScore` vs `consistency`, `momentumDelta` vs `momentum`. I map explicitly at the API boundary, not by renaming either side's contract).
  - `app/services/identity/bottleneck_v0.py` — `diagnose_bottleneck_v0(...) -> List[BottleneckCandidate]`, rule-based, taxonomy-matched.
  - `app/services/identity/lattice.py` — `get_lattice_strut_detail(attr, events, window_days, ref_time, limit) -> LatticeStrutDetail` (includes `contributingEvents: List[StrutContributor]` with timestamp/baseWeight/decayFactor/decayedContribution — exactly F3's lattice-click requirement).
  - `app/services/identity/twin.py` — `assemble_digital_twin(...) -> DigitalTwinReadModel`.
  - `app/services/identity/enrichment.py` — `enrich_evidence_event(event, declared_self) -> EvidenceEvent`, populates `identityAttributeIds` on the fly via keyword rules.
  - `app/services/decision/packet.py` — **AIA's own `DecisionPacket`/`BottleneckCandidate` dataclasses** (snake_case: `user_id`, `gap_score`, `bottleneck_candidates`...), separate from my frozen Pydantic `app.schemas.decision.DecisionPacket`/`app.schemas.bottleneck.BottleneckPacket`. Same contract-drift pattern integration-notes.md already flagged for AIS — **not fixing AIA's duplication (role isolation), but I must adapt it to my frozen schema at the API response boundary.** See Open Question 2.
- **A concrete bug I need to prevent, not just note:** my M1 `_to_schema()` (in `app/api/evidence.py`) hardcodes `identityAttributeIds=[]` when reading rows back from the DB (I never persisted that field — a known M1 gap I flagged at the time). AIA's `get_lattice_strut_detail` and `recompute_user_gap` both filter/match on `attr.id in e.identityAttributeIds`. **If I feed DB-read events straight into AIA's functions, every attribute match is empty and the Gap/lattice results are silently wrong** (not an error — a wrong number, which is worse for a demo). Fix: run AIA's `enrich_evidence_event` over every event *after* reading from the repository and *before* calling `recompute_user_gap`/`get_lattice_strut_detail`. This is a required implementation step (§5.2, step 2), not optional polish.
- **No confirmed `DeclaredSelf` exists yet** — M3 (Mirror Interview) is what creates one via the onboarding flow, and M3 hasn't been built. `GET /api/v1/identity` and the dashboard need a real `DeclaredSelf` to compute Gap against *now*. Addressed in §5.4 + Open Question 1.
- Existing from M0/M1: `app/models/twin_version.py` (JSON `attributes` blob, no structured read path yet), `app/schemas/identity.py` (frozen `DeclaredSelf`/`IdentityAttribute`), `app/schemas/gap.py` (frozen `GapBreakdown`/`AttributeContribution`), `app/schemas/bottleneck.py`, `app/schemas/decision.py`, `app/services/evidence/service.py` (`on_evidence_created` hook — exactly where the recompute call attaches), `app/repositories/evidence_repository.py` (`list_window`).

## 5. Detailed work plan

### 5.1 Contracts / schemas
1. **What:** No new frozen contract needed for the API surface — `GapBreakdown`, `BottleneckPacket`, `DecisionPacket`, `DeclaredSelf` already exist from M0. Add one new schema: `DashboardSummary` (wraps `DeclaredSelf` + `GapBreakdown` + `BottleneckPacket` + lattice-ready attribute list) so `GET /dashboard/summary` has a single typed response.
   **Why:** milestones.md M2 Backend checkbox 2 — "twin, KPIs, breakdown, bottleneck placeholder" needs one coherent response shape.
   **How:** `app/schemas/dashboard.py`: `DashboardSummary(userId, declaredSelf: DeclaredSelf, gap: GapBreakdown, bottleneck: BottleneckPacket | None, capacity: float)`.
   **Done when:** schema round-trips in a test; exported from `app/schemas/__init__.py`.

### 5.2 Core logic
2. **What:** `app/services/identity/orchestration.py` (Backend-owned wiring module — distinct from AIA's `app/services/identity/*` pure modules) — `recompute_and_persist(db, user_id) -> KPISnapshotModel`: loads the confirmed `DeclaredSelf` (via new twin repository, §5.3 step 4), loads the evidence window via `evidence_repository.list_window`, **runs `enrich_evidence_event` over every event**, calls AIA's `recompute_user_gap`, maps the returned `GapResult`/`KPISnapshot`/`DecisionPacket` into my frozen `GapBreakdown`/`DecisionPacket` schemas, persists a `KPISnapshotModel` row.
   **Why:** this is the actual "recompute on every accepted evidence event" checkbox (milestones.md lists it under AIA but explicitly says "called from Backend service" — the call site is backend's job).
   **How:** field-by-field adapter functions `_kpi_to_gap_breakdown(kpi, gap_result) -> GapBreakdown` and `_decision_packet_to_schema(dp) -> DecisionPacket` — explicit mapping, not renaming either side (respects role isolation; AIA's internal dataclasses stay theirs).
   **Done when:** unit test: given a fixed seeded event set and declared self, `recompute_and_persist` produces a stable `GapBreakdown` matching hand-computed expected values; identity-attribute matching is non-empty for events with keyword-matchable metadata.

3. **What:** Register `evidence_service.on_evidence_created(lambda row: recompute_and_persist(db, row.user_id))` at app startup (or per-request DB session — see Risk 1 about session lifetime across the callback boundary).
   **Why:** closes the M1→M2 loop: "Injecting a mission_completed event changes Gap without LLM calls" (Merge Gate 2).
   **How:** the listener needs its own DB session (the one from the ingest request will already be closed by the time listeners fire, depending on hook timing) — use a fresh `SessionLocal()` inside the listener, not the caller's session.
   **Done when:** POST `/evidence` → the next `GET /dashboard/summary` reflects the updated Gap without any additional manual trigger.

### 5.3 Integration / wiring
4. **What:** `app/repositories/twin_repository.py` — `get_active_declared_self(db, user_id) -> DeclaredSelf | None`, `create_version(db, user_id, declared_self) -> TwinVersionModel` (deserializing/serializing the `attributes` JSON column into `schemas.identity.DeclaredSelf`).
   **Why:** milestones.md §1 module map — `repositories/` is Backend's; `GET /api/v1/identity` needs this read path.
   **How:** "active" = latest row where `confirmed_at IS NOT NULL`, ordered by `version DESC`.
   **Done when:** round-trip test: create a version, read it back, fields match.

5. **What:** `app/api/dashboard.py` — `GET /api/v1/dashboard/summary`. `app/api/identity.py` — `GET /api/v1/identity`.
   **Why:** milestones.md M2 Backend checkboxes 2–3.
   **How:** `dashboard/summary` calls `twin_repository.get_active_declared_self`, the latest `KPISnapshotModel` (or triggers a fresh `recompute_and_persist` if none exists / stale), and the latest bottleneck candidates (top-1 by confidence, adapted to `BottleneckPacket`). `identity` just returns the active `DeclaredSelf`. Both use `get_current_user_id` (same `AUTH_BYPASS` pattern as M1).
   **Done when:** `GET /dashboard/summary` returns all fields required by F3's popover (per-attribute `w_i`, `D_i`, `R_i`, deficit, creation/passive/drift contributions, final Gap, Alignment) with zero LLM calls in the request path.

6. **What:** `app/api/lattice.py` — `GET /api/v1/identity/attributes/{attr_id}/evidence` returning the `StrutContributor` list for that attribute (adapted into a frozen response shape, not AIA's raw dataclass).
   **Why:** milestones.md M2 Backend checkbox 5; F3 "click any lattice strut → the exact evidence events."
   **How:** load `DeclaredSelf`, find the matching `IdentityAttribute`, load+enrich the evidence window, call AIA's `get_lattice_strut_detail`, map `StrutContributor` → a small frozen `LatticeContributor` schema (add to `app/schemas/gap.py` or a new `app/schemas/lattice.py`).
   **Done when:** clicking a strut with known seeded events returns a non-empty, correctly-ordered (highest decayed contribution first) contributor list.

7. **What:** Poll-based realtime — no new endpoint. Confirm `GET /dashboard/summary` is cheap enough (no LLM, single DB round trip plus in-memory recompute) for a client to poll every 2s per techstack.md §3/prd.md §11 ("skip websockets... 2-second polling only").
   **Why:** milestones.md M2 Backend checkbox 4 ("WebSocket or 2s poll payload for Gap updates" — poll explicitly allowed).
   **How:** no implementation beyond making sure step 5's endpoint doesn't do anything Tier-1/Tier-2 (no retrieval, no LLM) — verify by inspection.
   **Done when:** confirmed and stated in the Done report; no WS code written (out of scope per Open Question 3).

### 5.4 Seeds / fixtures
8. **What:** Extend `app/workers/seed.py` (from M1) to also upsert a fixed, confirmed `TwinVersion` v1 for the demo user — Aarav's persona attributes from prd.md §4/§5 (e.g. `public_speaker`, `builder`) with weights summing to 1.0 and `targetWeeklyPoints` per attribute.
   **Why:** M2 needs *something* to compute Gap against; M3 (real onboarding) doesn't exist yet. Without this, `GET /api/v1/identity` and the dashboard have nothing to serve.
   **How:** hardcoded, deterministic — not LLM-generated (this is fixture data, not a real interview result); marked as a normal (non-`simulated`) confirmed twin version, since Declared Self isn't itself evidence.
   **Done when:** running seed produces exactly one confirmed `TwinVersion` v1 for the demo user, idempotent on re-run (same upsert pattern as the M1 user row).

### 5.5 Tests
9. **What:** `tests/test_dashboard.py`, `tests/test_identity_endpoint.py`, `tests/test_lattice.py`, `tests/test_recompute_wiring.py`.
   **Why:** Merge Gates 1–3 (milestones.md M2); AIA's own gate 3/4 depend on backend hosting results correctly, not recomputing anything itself.
   **How:** seed a fixed twin + a handful of known events, assert the full arithmetic chain end-to-end through the HTTP layer; one test explicitly injects a `mission_completed` event via `POST /evidence` and asserts the next `GET /dashboard/summary` shows a *different* (lower) Gap — this is Merge Gate 2, made concrete.
   **Done when:** `cd services/api && AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q` green.

### 5.6 Demo / merge-gate verification
10. **What:** Manual/CI verification against `milestones.md` M2 Merge Gates 1–4.
    **Why:** required before requesting merge `backend-m2` → `backend` → `dev`.
    **How:** (1) dashboard summary returns full arithmetic fields; (2) inject `mission_completed`, confirm Gap changes with zero LLM calls (grep + runtime check); (3) confirm AIA's formula constants aren't duplicated in backend code — backend only calls, never reimplements; (4) confirm `DecisionPacket` includes gap delta + invalidate flags in the shape AIS's stub expects (cross-check against AIS's M1/M2 no-op consumption if visible on their pushed branch).
    **Done when:** all four gates verified and recorded in the Done report.

## 6. Dependencies & sequencing
- **Hard dependency:** AIA's `aia-m2` branch content (pure functions in `app/services/identity/*` and `app/services/decision/packet.py`) — I'm building against what's already pushed there (read-only), since I can't merge it into my own branch without human approval. If AIA changes these signatures before merge, my adapter functions (§5.2 step 2) need updating — isolated to one file, low blast radius.
- No dependency on AIS M2 — they consume my `DecisionPacket`/dashboard output, not the reverse.
- Merge order: **Backend → AIA → AIS → `dev` → `main`** (unchanged).
- Merge Gate checklist (copied from `milestones.md` M2):
  1. Dashboard summary returns full arithmetic fields required by F3 popover.
  2. Injecting a `mission_completed` event changes Gap without LLM calls.
  3. AIA unit tests lock formula constants; Backend only hosts results. *(their gate — I must not touch `scoring/gap.py`)*
  4. DecisionPacket includes gap delta + invalidate flags for AIS.

## 7. Risks
- **DB session lifetime across the `evidence.created` callback boundary** — the listener registered in step 3 fires synchronously inside the same request, but if it opens a *new* `SessionLocal()` while the original request's session hasn't committed yet, reads could race on some backends (not SQLite in tests, but worth being deliberate about: commit the evidence insert before invoking listeners — already true in my M1 `evidence_repository.create_if_not_exists`, which commits before returning).
- **AIA's `DecisionPacket`/`BottleneckCandidate` dataclass duplication** (Open Question 2) — adapting their dataclass shape into my frozen schema means my adapter is coupled to their exact field names; if they rename fields between now and merge, my adapter breaks loudly (a clear ImportError/AttributeError, not silent corruption) — acceptable risk given role isolation.
- **Seeded placeholder `DeclaredSelf`** (§5.4) could look like it's pre-empting M3's actual onboarding work if not clearly labeled as a fixture — mitigated by keeping it in the seed script (already understood as fixture-only) and not building any interview UI/logic.
- **`main`/`dev` still unmerged from M1** — same structural risk as before; rebasing `backend-m2` onto `dev` once the M1 merge lands is a known follow-up step, not a blocker to planning/building now.

## 8. Open Questions
1. **Seed a placeholder confirmed `DeclaredSelf` for the demo user in M2, since M3 (real onboarding) doesn't exist yet?** Without it, `GET /identity` and the dashboard have nothing to compute against.
   - **Recommendation:** yes — hardcoded fixture twin v1 (Aarav's persona from prd.md §4), clearly a seed-script fixture, not real onboarding output. M3 will later create real confirmed versions through the actual interview flow; this fixture just unblocks M2's endpoints today.
2. **AIA's `app/services/decision/packet.py` `DecisionPacket`/`BottleneckCandidate` dataclasses duplicate/diverge from Backend's frozen `app.schemas.decision.DecisionPacket`/`app.schemas.bottleneck.BottleneckPacket` (snake_case vs camelCase, different field sets).** Should Backend (a) write an adapter at the API boundary (what I've planned), or (b) flag this to a human to get AIA to consume Backend's frozen schema directly instead of maintaining their own?
   - **Recommendation:** (a) for M2 — adapt now to unblock the milestone; note it in the Done report for a human to route to AIA as a contract-alignment follow-up (same treateament as the `llm.py`/`llm/` duplication I flagged in M1 and deliberately left untouched — role isolation).
3. **WebSocket vs 2s polling for Gap updates** — milestones.md explicitly allows either; prd.md §11/techstack.md §3 explicitly recommend skipping websockets for the MVP.
   - **Recommendation:** polling only (no new endpoint/infra) — confirmed by two source docs, not just my preference.
4. **`main`/`dev` still hasn't merged my M1 work (or AIA's).** Build M2 now against my own `backend-m1` + AIA's pushed `aia-m2` (read-only reference), same as the M1 precedent?
   - **Recommendation:** yes, consistent with how M1 proceeded — rebase onto `dev` once the real merge lands, before requesting M2's own merge.

## 9. Execution checklist (after you approve)
- [ ] Answer open questions
- [ ] Approve this plan
- [ ] Agent syncs `backend` with `dev` (or `backend-m1` if `dev` still unmerged), creates/checks out `backend-m2`
- [ ] Implement
- [ ] Run `AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q`
- [ ] Show commit message(s) → wait for approval → commit
- [ ] Push `backend-m2`; confirm CI green
- [ ] Done report
