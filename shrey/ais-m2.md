# Implementation Plan — AIS — M2

## 1. Context
- **Role:** AIS (AI Systems / Curation)
- **Milestone:** M2 — Deterministic Gap, KPIs, Dashboard API ("Score moves on every event")
- **PRD features touched:** F3 (P0) — AIS does not compute Gap; it **consumes** Gap/KPI deltas from AIA via `DecisionPacket` and sets stack invalidation flags for continuous curation.
- **Techstack modules touched:**
  - `services/api/app/services/recommendation/evidence_hook.py` — upgrade placeholder packet → AIA-driven DecisionPacket consumer
  - `services/api/app/services/recommendation/` — active-stack invalidation state + safe empty-stack path
  - `services/api/app/agents/nodes/coordinator/node.py` — apply real `invalidateStack` / `invalidatedElementIds` from DecisionPacket (retire M1 fixture-only flag as primary path)
  - `services/api/app/agents/graphs/coordinator.py` — carry Gap/KPI fields needed for decision consumer
  - `services/api/app/services/decision/packet.py` — **consume** AIA `build_decision_packet` / map into Backend `app.schemas.DecisionPacket` (do not re-own Gap math)
  - `services/api/tests/` — M2 decision-consumer + empty-stack safety tests
- **Goal:** Become a real Growth Decision Engine **consumer**: on evidence/KPI updates, read Gap deltas from AIA outputs, populate a proper `DecisionPacket`, and set `invalidate` flags on the active stack (even when empty) — without crashing dashboard load and without ranking/retrieval (those remain M4).

---

## 2. Scope (in) — 1:1 with AIS M2 checkboxes in `milestones.md`
- [ ] **Growth Decision Engine consumer:** read Gap/KPI deltas → set `invalidate` flags on active stack (even if stack empty).
- [ ] **DecisionPacket population from AIA outputs** — replace M1's hardcoded placeholder (`gapDelta=0.0`) with values derived from AIA Gap/KPI results (via twin read model / `build_decision_packet` / Backend dashboard contract).
- [ ] **No empty-stack crash when dashboard loads** — active-stack read / Coordinator / assembler path must return a safe empty-or-fixture draft when no stack exists yet; never raise.
- All of M2 AIS is P0 infra for F3 continuous-loop wiring (still no live retrieval/ranking).

---

## 3. Scope (out)
- **AIA M2** (owns): Gap formula implementation, Create:Consume / Consistency / Momentum, Gap breakdown object, recompute-on-evidence, bottleneck packet v0, formula unit tests. AIS **consumes** these outputs; does not reimplement arithmetic.
- **Backend M2** (owns): KPI snapshot persistence, `GET /api/v1/dashboard/summary`, `GET /api/v1/identity`, Gap update WS/poll payload, lattice strut → contributing events query. AIS does not add dashboard HTTP routes.
- **Deferred AIS work:** real diagnose→retrieve→assemble (M4), Guardian/variants/unlearning (M5), catalog ranking (M6).
- Hard rules remain: no LLM Gap math; no vendor SDKs outside `providers/`; no pre-scored Gap inserts.

---

## 4. Current repo state
- **Local `main` / `origin/main` synced** at `8219c9b` (integrated M0+M1: Backend + AIA + AIS).
- **AIS M1 already on main:**
  - `evidence_hook.py` builds a **placeholder** `DecisionPacket` (`gapDelta=0.0`, `invalidateStack=False`) — must upgrade in M2.
  - `coordinator_node` reads `invalidateStack` + optional `AIS_M1_FIXTURE_INVALIDATE` env.
  - `stack_assembler.assemble_stack` always returns ≥1 fixture elements (never empty) — good base for “no empty-stack crash,” but dashboard may call a **read-active-stack** path that doesn’t exist yet.
  - Contracts migrated to `app.schemas` (`CONTRACT_SOURCE = "app.schemas"`).
- **AIA M1 on main (inputs AIS will need):**
  - `services/identity/twin.py` → `assemble_digital_twin` → `GapResult`
  - `services/identity/aggregates.py` → Revealed Self aggregates + create:consume
  - `services/decision/packet.py` → dataclass `DecisionPacket` + `build_decision_packet(...)` (snake_case; **shape differs** from Backend Pydantic `app.schemas.DecisionPacket`)
- **Backend M1 on main:** evidence ingest/simulator/seed. **No `dashboard/summary` yet** (Backend M2).
- **Remote:** `origin/aia-m2` already exists; no `backend-m2` / `ais-m2` yet at plan time.
- **Merge order for M2:** AIA → Backend → **AIS** (AIS merges last).

### Known seam (must resolve in Open Questions / adapter)
| Source | Shape |
|---|---|
| AIA `services/decision/packet.py` dataclass | `user_id, gap_score, gap_delta, alignment, create_consume_ratio, bottleneck_candidates, invalidate_stack, timestamp` |
| Backend `app.schemas.DecisionPacket` | `userId, gapDelta, invalidateStack, invalidatedElementIds, bottleneck, rankingFeatures` |

AIS M2 should **map AIA outputs → Backend schema DecisionPacket** (single cross-role DTO) and keep run-scoped fields in `CoordinatorRunContext` (already M1 pattern).

---

## 5. Detailed work plan

### 5.1 Contracts / schemas
**Step 1 — DecisionPacket adapter (AIS-owned mapper).**
- **What:** `app/services/recommendation/decision_adapter.py` with `to_schema_decision_packet(aia_packet | gap_kpis) -> app.schemas.DecisionPacket`.
- **Why:** Milestone checkbox “DecisionPacket population from AIA outputs”; avoids dual sources of truth; Backend/UI/AIS share one Pydantic DTO.
- **How:** Map `gap_delta → gapDelta`, `invalidate_stack → invalidateStack`; set `rankingFeatures` from create:consume / consistency / momentum when available; leave `bottleneck=None` unless AIA v0 heuristic packet present; never invent Gap numbers.
- **Done when:** Unit test round-trips AIA `build_decision_packet` output into a valid `app.schemas.DecisionPacket` with matching delta/invalidate.

### 5.2 Core logic
**Step 2 — Growth Decision Engine consumer.**
- **What:** `app/services/recommendation/decision_consumer.py` exposing `consume_gap_update(user_id, gap_result, prior_gap, kpis, active_stack=None) -> DecisionPacket` that:
  1. Calls AIA `build_decision_packet` (or equivalent) for invalidate rule (`|gap_delta| >= GAP_DELTA_INVALIDATION_THRESHOLD`).
  2. Maps to schema `DecisionPacket`.
  3. Applies invalidation to an in-memory (or injectable) **active stack state**: set `invalidate=True` on stack draft / registry even when `active_stack is None` / empty.
- **Why:** Checkbox — read Gap/KPI deltas → set invalidate flags on active stack (even if empty).
- **How:** Pure/service module; no LLM; no HTTP. Store active-stack flags in `app/services/recommendation/stack_state.py` (`get_active_stack_flags`, `apply_invalidation`).
- **Done when:** Injecting a gap delta ≥ threshold sets `invalidateStack=True` and active-stack flag True; delta 0 leaves False; empty active stack does not raise.

**Step 3 — Upgrade `evidence_hook` off placeholder.**
- **What:** Replace `build_placeholder_decision_packet` with a path that accepts optional twin/gap inputs (or a thin callback/`GapSnapshot` protocol). When AIA twin/gap available → populate real packet; when not (tests without twin) → labeled **degraded placeholder** still allowed for unit isolation, but default M2 path uses AIA outputs.
- **Why:** M1 stub must not remain the production path once Gap moves on every event.
- **How:** Signature like `on_evidence_created(event, *, gap_snapshot=None, prior_gap=None)` → consumer → Coordinator. Backend/AIA can wire snapshot after recompute; AIS does not own recompute.
- **Done when:** Test with fixture GapResult (gap rises/falls) yields non-zero `gapDelta` and correct invalidate flag; no Gap arithmetic inside AIS modules.

**Step 4 — Coordinator applies real invalidation (not fixture-primary).**
- **What:** `coordinator_node` uses `decision_packet.invalidateStack` + `invalidatedElementIds` as primary; keep env fixture flag only behind a clearly labeled test override (or drop if unused).
- **Why:** Continuous curation needs real delta-driven invalidation for M4 refresh triggers.
- **How:** Write `stack_draft = {invalidate, invalidated_element_ids, hypothesis_id}`; still no retrieval.
- **Done when:** Graph run with `invalidateStack=True` marks draft; `False` does not.

### 5.3 Integration / wiring
**Step 5 — Safe dashboard / empty-stack path.**
- **What:** `get_active_stack_or_empty(user_id) -> IdentityStack | None` (or always returns a **non-crashing** fixture draft for demo user when none exists). Document that Backend `dashboard/summary` may call this; AIS guarantees no exception / no empty element list crash in assembler consumers.
- **Why:** Checkbox — “No empty-stack crash when dashboard loads.”
- **How:** Guard `assemble_stack` callers; if no decision packet, synthesize minimal invalidation-aware empty-safe response (`elements=[]` **or** fixture fallback — prefer fixture fallback consistent with M1 “never empty intervention” principle when delivering; for dashboard draft, allow `None`/empty with explicit `invalidate` flag without raising).
- **Done when:** Test invokes consumer + active-stack getter with no prior stack → no exception; returns structured safe result.

### 5.4 Seeds / fixtures
- Extend `tests/fixtures/sample_data.py` with:
  - Sample `GapResult` / KPI deltas (aligned + drifted)
  - Sample AIA-style decision inputs mapped through adapter
  - Empty active-stack fixture

### 5.5 Tests
**Step 6 — AIS M2 tests** (`services/api/tests/`):
- `test_decision_adapter.py` — AIA packet → schema packet field mapping.
- `test_decision_consumer.py` — gap delta ≥ threshold → invalidate; below threshold → no invalidate; empty stack OK.
- `test_evidence_hook_m2.py` — hook with gap snapshot populates non-zero `gapDelta`; AIS never computes Gap from raw events itself.
- `test_empty_stack_dashboard_safe.py` — consumer/get-active with no stack → no crash.
- Keep vendor-leak + schema import gates green.
- **Done when:** `cd services/api && pytest -q` green.

### 5.6 Demo / merge-gate verification
**Step 7 — AIS-relevant M2 Merge Gates:**
1. Dashboard summary arithmetic fields — **Backend/AIA**; AIS ensures consumer doesn’t block/crash that path.
2. `mission_completed` changes Gap without LLM — **AIA/Backend**; AIS asserts its path still makes **zero** LLM/search calls.
3. AIA formula constants locked — **AIA**; AIS does not fork constants.
4. **DecisionPacket includes gap delta + invalidate flags for AIS** — AIS owns verification tests that consume these fields end-to-end in the Coordinator.
- **Done when:** Gate 4 tests pass; grep shows no Gap formula reimplementation under `services/recommendation/` or `agents/`.

---

## 6. Dependencies & sequencing

### What AIS needs from other roles
| Need | From | Status | Stub strategy |
|---|---|---|---|
| Gap formula + `GapResult` / KPI helpers | AIA M2 | `origin/aia-m2` exists; M1 twin/gap already on main | Code against `assemble_digital_twin` / `build_decision_packet` on main; adopt M2 additions when merged |
| `GET /dashboard/summary` + KPI persistence | Backend M2 | Not on remote yet | AIS does not call HTTP; expose consumer function Backend can invoke post-recompute |
| Frozen `app.schemas.DecisionPacket` | Backend M0 | ✅ | Continue mapping into this DTO |

### Sequencing within AIS M2
```
Step 1 (adapter) → Step 2 (consumer + stack_state) → Step 3 (evidence_hook upgrade)
  → Step 4 (coordinator) → Step 5 (empty-stack safety) → Step 6 (tests) → Step 7 (gates)
```

### Merge gate checklist (M2) — from `milestones.md`
- [ ] Dashboard summary returns full F3 arithmetic fields (Backend/AIA)
- [ ] Injecting `mission_completed` changes Gap without LLM (AIA/Backend)
- [ ] AIA unit tests lock formula constants (AIA)
- [ ] DecisionPacket includes gap delta + invalidate flags for AIS (**AIS verifies**)

**Merge order:** AIA → Backend → **AIS**.

**Branch naming (repo convention):** cut `ais-m2` from `ais` synced with `dev`/`main` (same pattern as `ais-m1`).

---

## 7. Risks
| Risk | Mitigation |
|---|---|
| Dual DecisionPacket shapes (AIA dataclass vs Backend Pydantic) | Single adapter module; tests lock mapping; AIS never invents a third shape |
| Backend M2 dashboard not ready | Consumer is callable without HTTP; empty-stack safety tested in-process |
| Accidentally reimplementing Gap math in AIS | Tests assert AIS modules only call AIA helpers; no `compute_gap_score` import in recommendation except via twin/decision APIs if needed for wiring — prefer receiving precomputed GapResult |
| Fixture env flag masks real invalidation | Demote fixture flag; primary path = `invalidateStack` from packet |
| Empty stack vs “never empty intervention” tension | Distinguish **active stack registry** (may be empty/None) from **delivery assembler** (fixture fallback); dashboard must not crash either way |

---

## 8. Open Questions (block execution)
1. **Gap input wiring:** Should AIS call `assemble_digital_twin` / `build_decision_packet` directly inside `on_evidence_created`, or should Backend pass a precomputed `GapSnapshot` into the hook after recompute?
   - Recommendation: **Backend/service passes GapSnapshot into AIS consumer** (AIS stays a pure consumer); for local tests, allow direct AIA helper injection. Avoid AIS owning evidence→DB→twin orchestration.
2. **Active stack storage in M2:** In-memory registry only (my plan), or write a Backend stack row flag this milestone?
   - Recommendation: **in-memory / service-level flags in M2**; Backend stack persistence lands with M4 stack APIs. Expose clear function signature for Backend to call.
3. **Empty stack for dashboard:** Return `None`, empty `elements=[]`, or always a fixture draft?
   - Recommendation: **`get_active_stack` returns `None` + `invalidate` flags object without raising**; `assemble_stack` remains never-empty for delivery. Dashboard binds safely to null stack.
4. **Retire `AIS_M1_FIXTURE_INVALIDATE`?** Keep as test-only override or delete?
   - Recommendation: **keep as test-only override**, documented; production path uses DecisionPacket only.
5. **Sync with `aia-m2`:** Wait for AIA M2 merge to `dev` before coding, or start against main + labeled stubs for any new M2 AIA fields?
   - Recommendation: **start from updated `main`, adapt when `aia-m2` lands**; merge `ais-m2` only after AIA+Backend M2 are on `dev`.

---

## 9. Execution checklist (after you approve)
- [ ] Answer open questions 1–5
- [ ] Approve this plan
- [ ] Sync `main`/`dev`; cut `ais-m2` from role branch synced with `dev`
- [ ] Implement Steps 1–7
- [ ] Run `cd services/api && pytest -q` — green; vendor-leak grep clean
- [ ] Show commit message → wait for approval → commit
- [ ] Done report; push `ais-m2` when Backend+AIA M2 are ready (merge order)

---

## Sync note (this session)
- Confirmed local `main` == `origin/main` at `8219c9b` (M0+M1 integrated) **before** writing this plan.
- Phase A only: **no code/branch/commit for M2 until you approve.**
