# Implementation Plan — AIA — M2

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M2 — Deterministic Gap, KPIs, Dashboard API
- **PRD features touched:** F3 (Identity Gap Score + Lattice Visualization, P0)
- **Techstack modules touched:**
  - `services/api/app/services/identity/lattice.py` — lattice strut contributing events query & decayed weight calculation
  - `services/api/app/services/identity/bottleneck_v0.py` — rule/heuristic Bottleneck Packet v0 generator
  - `services/api/app/services/identity/recompute.py` — Gap recomputation orchestrator (`recompute_user_gap`)
  - `services/api/app/services/identity/kpi.py` — KPI snapshot assembly DTOs (Gap, Alignment, Create:Consume, Consistency, Momentum)
  - `services/api/tests/identity/test_m2_gap_kpis.py` — unit tests for M2 logic
- **Goal:** Deliver the pure AIA components for M2: lattice strut contributor detail calculations (for F3 strut click popover), rule-based Bottleneck Packet v0 generator, complete KPI snapshot builder, and the `recompute_user_gap` orchestrator — locking all PRD §9 deterministic formula contracts before Backend wires the dashboard endpoints.

---

## 2. Scope (in)

Mapped 1:1 to M2 AIA checkboxes in `milestones.md`:

- **[AIA-1] Complete Gap formula popover breakdown DTOs:** Ensure per-attribute `w_i`, `D_i`, `R_i`, deficit, creation contribution, passive contribution, and drift contribution fields match F3 popover requirements.
- **[AIA-2] Lattice strut contributing events query:** Calculate contributing evidence events for a specific identity strut, including event timestamp, base weight, applicabilty `a_ik`, and recency-decayed contribution.
- **[AIA-3] KPI snapshot builder:** Compute full KPI snapshot (Gap, Alignment, Create:Consume ratio, Consistency, 7-day Momentum delta).
- **[AIA-4] Gap recomputation orchestrator (`recompute_user_gap`):** Pure service function that accepts Declared Self, event stream, and prior Gap score, returning updated `GapResult`, `KPISnapshot`, and `DecisionPacket` (with `invalidate_stack` flag).
- **[AIA-5] Bottleneck Packet v0 (heuristic):** Rule-based diagnosis candidate generator mapping largest attribute deficits, low Create:Consume ratio (<1.0), and low consistency to taxonomy candidates (e.g. `execution`, `consistency`, `focus`, `communication`).

---

## 3. Scope (out)

Items explicitly **not** done by AIA in M2:

- **Backend:** FastAPI endpoints (`GET /dashboard/summary`, `GET /identity`), Postgres KPI snapshot persistence, WebSocket/poll updates, router wiring — all Backend M2 work.
- **AIS:** Growth Decision Engine consumer hook, reading `invalidate_stack` flag to invalidate active stack — all AIS M2 work.
- No LLM calls for bottleneck diagnosis (M2 uses pure heuristic rule engine for Bottleneck v0 per `milestones.md`).
- No database reads or writes (pure Python modules only).

---

## 4. Current repo state

- **M0 and M1 completed and merged** on `aia` role branch (and pushed to remote):
  - `services/api/app/services/identity/scoring/` contains `constants.py`, `declared_self.py`, `gap.py`.
  - `services/api/app/services/identity/` contains `sanitizer.py`, `enrichment.py`, `aggregates.py`, `twin.py`.
  - `services/api/app/services/decision/` contains `packet.py`.
  - 14 unit tests passing cleanly via `python -m unittest discover -s tests/identity -t .`.
- Greenfield state for M2: lattice strut contributor query, heuristic bottleneck v0 engine, KPI snapshot builder, and `recompute_user_gap` orchestrator need to be added.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Lattice Contributor & KPI Snapshot DTOs**

- **What:** `services/api/app/services/identity/lattice.py` and `services/api/app/services/identity/kpi.py`
  - `StrutContributor(dataclass)`: `event_id`, `event_type`, `timestamp_delta_days`, `base_weight`, `a_ik`, `decay_factor`, `decayed_contribution`, `source`, `simulated`
  - `LatticeStrutDetail(dataclass)`: `attr_id`, `attr_label`, `weight`, `declared_weekly_target`, `revealed_points`, `deficit`, `contributing_events: list[StrutContributor]`
  - `KPISnapshot(dataclass)`: `gap_score`, `alignment`, `create_consume_ratio`, `create_points`, `consume_points`, `drift_points`, `consistency`, `momentum`
- **Why:** Milestone checkboxes AIA-1, AIA-2, and AIA-3; required for F3 lattice strut click popover and dashboard KPI cards.
- **How:** Pure Python dataclasses and calculation helper functions.
- **Done when:** Dataclasses and contributor calculation functions are defined and importable.

---

### 5.2 Core logic

**Step 2 — Lattice Contributor Calculation**

- **What:** `get_lattice_strut_detail(attr_id: str, declared_attr: dict, events: list[SanitizedEvent], window_days: int = 21) -> LatticeStrutDetail`
  - Filters events matching `attr_id` within `window_days`.
  - Computes `decay_factor = e^(-λ × delta_days)` and `decayed_contribution = a_ik × base_weight × decay_factor`.
  - Orders contributing events descending by decayed contribution.
  - Returns complete `LatticeStrutDetail`.
- **Why:** Milestone checkbox AIA-2; PRD §3 requirement — "Click any lattice strut -> the exact evidence events that contributed to it, including timestamp, event weight, and decayed contribution."
- **How:** Pure function over `SanitizedEvent` list.
- **Done when:** `get_lattice_strut_detail` accurately calculates decayed contribution per event.

---

**Step 3 — Heuristic Bottleneck Packet v0 Generator**

- **What:** `services/api/app/services/identity/bottleneck_v0.py`
  - `diagnose_bottleneck_v0(gap_result: GapResult, create_consume: CreateConsumeResult, consistency: float, events: list[SanitizedEvent]) -> list[BottleneckCandidate]`
  - Rule engine:
    - If `create_consume.ratio < 0.5` or `create_consume.drift_points > create_consume.create_points`: Candidate `execution` (confidence 0.8, supporting evidence = drift event IDs).
    - If `consistency < 0.4`: Candidate `consistency` (confidence 0.75).
    - If attribute with largest deficit is `public_speaker`: Candidate `communication` or `confidence` (confidence 0.7).
    - If attribute with largest deficit is `builder`: Candidate `execution` or `focus` (confidence 0.7).
  - Constrained strictly to `BOTTLENECK_TAXONOMY` from `packet.py`.
- **Why:** Milestone checkbox AIA-5; rule/heuristic candidate list for M2 before Gemini LLM bottleneck diagnosis lands in M4.
- **How:** Deterministic rule engine; returns list of `BottleneckCandidate` dataclass instances.
- **Done when:** `diagnose_bottleneck_v0` produces structured `BottleneckCandidate` list for seeded Aarav history.

---

**Step 4 — Gap Recomputation & KPI Snapshot Orchestrator**

- **What:** `services/api/app/services/identity/recompute.py`
  - `recompute_user_gap(user_id: str, declared_self: DeclaredSelf, events: list[SanitizedEvent], prior_gap_score: Optional[int] = None, window_days: int = 21, timestamp: str = "2026-08-01T12:00:00Z") -> tuple[GapResult, KPISnapshot, DecisionPacket]`
    - Converts attributes and events to scoring inputs.
    - Computes `GapResult` via `compute_gap_score`.
    - Computes `CreateConsumeResult` and `consistency`.
    - Computes `momentum` delta (`gap_now - prior_gap_score`).
    - Generates Bottleneck v0 candidates using `diagnose_bottleneck_v0`.
    - Assembles `DecisionPacket` using `build_decision_packet` (with `invalidate_stack` flag).
- **Why:** Milestone checkbox AIA-4; single pure entrypoint called by Backend evidence ingest service.
- **How:** Pure orchestrator function combining M0 scoring functions, M1 aggregates, and M2 DTOs.
- **Done when:** `recompute_user_gap` returns `(GapResult, KPISnapshot, DecisionPacket)` tuple.

---

### 5.3 Integration / wiring

**Step 5 — Package `__init__` Exports**

- **What:** Update `services/api/app/services/identity/__init__.py` to export `get_lattice_strut_detail`, `diagnose_bottleneck_v0`, `recompute_user_gap`, `KPISnapshot`, `LatticeStrutDetail`, `StrutContributor`.
- **Why:** Keeps identity package interface clean.
- **How:** Add `__all__` exports.
- **Done when:** Imports work cleanly via `from app.services.identity import recompute_user_gap, get_lattice_strut_detail`.

---

### 5.4 Seeds / fixtures

No new seeds needed — M2 logic will be tested against `aarav_seed.py` fixture generator created in M1.

---

### 5.5 Tests

**Step 6 — M2 Unit Tests**

- **What:** `services/api/tests/identity/test_m2_gap_kpis.py`
  - **Test 1 (Lattice Contributor Detail):** Verifies `get_lattice_strut_detail` calculates event decay factors, decayed contributions, and orders events descending.
  - **Test 2 (Heuristic Bottleneck v0):** Verifies `diagnose_bottleneck_v0` produces valid `execution`/`focus` candidates for Aarav's consume-heavy seed history.
  - **Test 3 (Gap Recompute & Decision Packet):** Runs `recompute_user_gap` on Aarav seed. Verifies `GapResult`, `KPISnapshot`, and `DecisionPacket` are non-null and internally consistent.
  - **Test 4 (Event Injection Movement):** Verifies injecting a `mission_completed` (+3.0) lowers Gap and changes `gap_delta` without calling any LLM.
  - **Test 5 (Focus Drift Injection Movement):** Verifies injecting a `focus_drift_10min` (-2.0) raises Gap without calling any LLM.
- **Why:** Validates all M2 AIA checkboxes and M2 Merge Gates 1–4.
- **How:** Standard `unittest.TestCase` running natively via `python -m unittest discover`.
- **Done when:** All tests in `test_m2_gap_kpis.py` pass.

---

### 5.6 Demo / merge-gate verification

**Step 7 — Merge Gate Verification**

- **What:** Verify M2 AIA Merge Gates:
  - Gate 1: Dashboard summary fields present in DTOs (`GapResult`, `KPISnapshot`, `LatticeStrutDetail`).
  - Gate 2: Injecting `mission_completed` changes Gap without LLM calls.
  - Gate 3: AIA unit tests lock formula constants; Backend only hosts results.
  - Gate 4: `DecisionPacket` includes `gap_delta` + `invalidate_stack` flag.
- **Done when:** `python -m unittest discover -s tests/identity -t .` passes 100% of M0 + M1 + M2 tests.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M2)
- Backend will build REST endpoint `GET /dashboard/summary` and wire `recompute_user_gap` into `POST /evidence`.
- No blocking dependency: AIA code is written as pure service modules that Backend calls.

### Suggested sequencing within AIA M2
```
Step 1 (DTOs) → Step 2 (Lattice Query) → Step 3 (Bottleneck v0) → Step 4 (Recompute Orchestrator)
  → Step 5 (__init__ exports) → Step 6 (Unit Tests) → Step 7 (Merge Gate Verification)
```

### Merge gate checklist (M2)
- [ ] Dashboard summary returns full arithmetic fields required by F3 popover (AIA DTOs verified)
- [ ] Injecting a mission_completed event changes Gap without LLM calls (AIA test verified)
- [ ] AIA unit tests lock formula constants; Backend only hosts results (AIA tests verified)
- [ ] DecisionPacket includes gap delta + invalidate flags for AIS (AIA verified)

**Merge order:** AIA (formula lib) → Backend (wire + API) → AIS (decision consumer).

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Float rounding mismatch between frontend display and backend arithmetic | Use `round(val, 2)` for all displayed float DTO fields (`R_i`, `deficit`, `ratio`, `decayed_contribution`). |
| Bottleneck v0 rules produce empty candidates list | Always include a fallback `execution` or `consistency` candidate if gap > 40 and no specific rule fires. |
| Invalidation threshold `GAP_DELTA_INVALIDATION_THRESHOLD` fires too frequently | Configured as constant `= 5.0` in `constants.py`; easy to tune if stack invalidation triggers too easily. |

---

## 8. Open Questions

1. **Lattice Strut Contributor Sorting:** Should contributing events for a strut be ordered descending by `decayed_contribution` (highest impact first) or chronologically by timestamp?
   - Recommendation: **Descending by decayed_contribution** (highest impact first), with timestamp included on each event item.

2. **Bottleneck Candidate Count:** How many candidates should `diagnose_bottleneck_v0` return?
   - Recommendation: **Top 1–2 candidates** max to prevent overwhelming AIS curator nodes downstream.

3. **Branching strategy for M2:** Should we checkout `aia` role branch and cut `m2` feature branch (`git checkout aia; git checkout -b m2`)?
   - Recommendation: **Yes** — per `guidelines.md §5`.

4. **Momentum Calculation Default:** If `prior_gap_score` is `None` (first event / onboarding fresh start), should `momentum` be `0`?
   - Recommendation: **Yes** — `0` signed delta when no prior snapshot exists.

5. **Lattice Strut Contributor Limit:** Should `get_lattice_strut_detail` limit the list of contributing events returned per strut (e.g. top 10 contributing events)?
   - Recommendation: **Limit to top 10 events** per strut to keep UI popovers clean and lightweight.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–5 above)
- [ ] Approve this plan
- [ ] Agent checks out `aia` → creates `m2` feature branch
- [ ] Implement Steps 1–7 in order
- [ ] Run unit test suite — all green
- [ ] Show `git status` + diff + proposed commit message → wait for human approval → commit
- [ ] Done report
