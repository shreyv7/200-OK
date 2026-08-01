# Implementation Plan — AIA — M1

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M1 — Evidence Pipeline + Twin Shell
- **PRD features touched:** F2 (Evidence Engine + Revealed Self, P0)
- **Techstack modules touched:**
  - `services/api/app/services/identity/enrichment.py` — rule-based event enrichment mapping event → attribute IDs & applicability `a_ik`
  - `services/api/app/services/identity/aggregates.py` — Revealed Self aggregate builder over time windows
  - `services/api/app/services/identity/twin.py` — Digital Twin read model combining active Declared Self + Revealed Self aggregates
  - `services/api/app/services/identity/sanitizer.py` — dead-letter / invalid event filter
  - `services/api/tests/fixtures/aarav_seed.py` — Aarav 21-day simulated evidence fixture for AIA tests
- **Goal:** Build the AIA evidence intelligence pipeline modules: enrich incoming evidence events with identity attribute tags, aggregate revealed behavior across temporal windows, assemble the Digital Twin read model, and enforce dead-letter event rejection — verified against a seeded 21-day Aarav profile fixture.

---

## 2. Scope (in)

Mapped 1:1 to M1 AIA checkboxes in `milestones.md`:

- **[AIA-1] Evidence enrichment:** Map incoming events to `identityAttributeIds` and `a_ik` applicability scores using rule-based/keyword matching.
- **[AIA-2] Revealed Self aggregate builder:** Compute aggregated evidence totals, event counts, and category distributions over 7-day, 14-day, and 21-day rolling windows (inputs for M2 Gap math).
- **[AIA-3] Twin read model:** Data model combining active Declared Self version with current Revealed Self aggregates.
- **[AIA-4] Reject scoring on invalid/dead-letter events:** Validator module that rejects malformed, out-of-bounds (`a_ik > 1.0`, negative weights, unknown subtypes), or corrupt events before scoring.

---

## 3. Scope (out)

Items explicitly **not** done by AIA in M1:

- **Backend:** `POST /api/v1/evidence`, `GET /api/v1/evidence`, DB tables for evidence persistence, internal `evidence.created` event bus, simulator endpoint, full database seed loader — all Backend M1 work.
- **AIS:** Subscribing to `evidence.created`, decision packet placeholder hooks — all AIS M1 work.
- No live database writes or FastAPI endpoints (Backend owns routers and DB models).
- No Gap score computation yet (that is M2).
- No LLM calls for enrichment (rule-based MVP per `milestones.md`).

---

## 4. Current repo state

- **M0 completed and committed** on branch `m0`:
  - `services/api/app/services/identity/scoring/` contains `constants.py`, `declared_self.py`, `gap.py`.
  - `services/api/app/services/decision/` contains `packet.py`.
  - 10 unit tests passing cleanly via `python -m unittest discover`.
- Greenfield state for M1: no enrichment, aggregate, or twin read models exist yet.
- AIA will build pure Python modules for M1 logic and include an `aarav_seed.py` fixture generator to validate aggregate calculations independently of Backend DB readiness.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Evidence Enrichment & Sanitizer Contracts**

- **What:** `services/api/app/services/identity/sanitizer.py` and `services/api/app/services/identity/enrichment.py`
  - `SanitizedEvent(dataclass)`: validated event with sanitized fields (`event_id`, `event_type`, `attr_id`, `a_ik`, `delta_days`, `value_override`, `simulated`, `source`)
  - `validate_and_sanitize_event(raw_event: dict) -> tuple[bool, SanitizedEvent | None, str | None]`
    - Validates required fields, checks `0.0 <= a_ik <= 1.0`, checks `delta_days >= 0`, validates `event_type` against `EVENT_WEIGHTS`.
    - Returns `(False, None, error_message)` for dead-letter/corrupt events.
  - `enrich_event(event: SanitizedEvent, attributes: list[dict]) -> SanitizedEvent`
    - Rule-based keyword/category mapper: matches event metadata/type to `identityAttributeIds` and sets `a_ik` applicability score.
- **Why:** Milestone checkboxes AIA-1 and AIA-4; contract with Backend for rejecting dead-letter events.
- **How:** Pure Python modules without DB/LLM dependencies.
- **Done when:** `validate_and_sanitize_event` rejects invalid events and `enrich_event` correctly assigns attribute applicability.

---

### 5.2 Core logic

**Step 2 — Revealed Self Aggregate Builder**

- **What:** `services/api/app/services/identity/aggregates.py`
  - `AttributeAggregate(dataclass)`: `attr_id`, `total_decayed_points`, `creation_points`, `passive_points`, `drift_points`, `event_count`, `last_event_delta_days`
  - `RevealedSelfAggregates(dataclass)`: `window_days`, `attribute_aggregates: dict[str, AttributeAggregate]`, `total_events`, `create_consume_ratio`, `consistency_score`
  - `build_revealed_aggregates(events: list[SanitizedEvent], attributes: list[dict], window_days: int = 21) -> RevealedSelfAggregates`
    - Filters events by `delta_days <= window_days`.
    - Computes per-attribute recency-decayed totals using `decay_weight(delta_days)` from M0 `gap.py`.
    - Calculates category point totals (creation vs passive vs drift) and overall `create_consume_ratio`.
- **Why:** Milestone checkbox AIA-2; provides Revealed Self inputs for M2 Gap recompute.
- **How:** Pure Python function importing `gap.py` decay and calculation functions.
- **Done when:** `build_revealed_aggregates` produces correct `RevealedSelfAggregates` over seeded test windows.

---

**Step 3 — Digital Twin Read Model**

- **What:** `services/api/app/services/identity/twin.py`
  - `DigitalTwinReadModel(dataclass)`: `user_id`, `declared_version`, `declared_self`, `revealed_aggregates`, `last_updated_at`
  - `assemble_digital_twin(user_id: str, declared_self: DeclaredSelf, events: list[SanitizedEvent], window_days: int = 21) -> DigitalTwinReadModel`
    - Combines active confirmed `DeclaredSelf` with current `RevealedSelfAggregates`.
- **Why:** Milestone checkbox AIA-3; unified Twin read model for API and dashboard consumption.
- **How:** Pure Python dataclass and assembly function.
- **Done when:** `assemble_digital_twin` combines Declared Self version and Revealed Self aggregates into a valid `DigitalTwinReadModel`.

---

### 5.3 Integration / wiring

**Step 4 — Package `__init__` Exports**

- **What:** Update `services/api/app/services/identity/__init__.py` to export sanitizer, enrichment, aggregates, and twin assembly modules.
- **Why:** Keeps package import path clean (`from app.services.identity import assemble_digital_twin, enrich_event`).
- **How:** Add `__all__` exports in `identity/__init__.py`.
- **Done when:** `from app.services.identity import ...` imports cleanly.

---

### 5.4 Seeds / fixtures

**Step 5 — 21-Day Aarav Seed Fixture Generator for AIA Tests**

- **What:** `services/api/tests/fixtures/aarav_seed.py`
  - `generate_aarav_seed_events() -> list[SanitizedEvent]`
  - Generates ~30 Realistic 21-day simulated evidence events for Aarav persona (22yo wanting to be public speaker + builder):
    - 60% passive tutorial/video watching
    - 25% focus drift (10-min doomscroll bursts)
    - 15% creation (1 speech outline, 2 github commits)
  - All events explicitly tagged `simulated=True`.
- **Why:** Merge Gate 4 requirement — "AIA aggregate tests pass on seeded Aarav fixture."
- **How:** Deterministic Python generator function.
- **Done when:** Generator outputs reproducible list of ≥25 valid `SanitizedEvent` instances.

---

### 5.5 Tests

**Step 6 — M1 Unit Tests**

- **What:** `services/api/tests/identity/test_m1_evidence.py`
  - **Test 1 (Sanitizer):** Rejects invalid `a_ik` (>1.0 or <0.0), negative `delta_days`, unknown event types. Accepts valid events.
  - **Test 2 (Enrichment):** Correctly maps event keywords to attribute IDs and assigns default `a_ik`.
  - **Test 3 (Aggregates on Aarav Seed):** Computes `RevealedSelfAggregates` on 21-day Aarav fixture. Asserts `create_consume_ratio < 1.0` (reflecting Aarav's consume-heavy state), positive creation points, and total event count ≥ 25.
  - **Test 4 (Digital Twin Assembly):** Assembles `DigitalTwinReadModel` combining DeclaredSelf v1 + Aarav aggregates.
- **Why:** Validates all M1 AIA checkboxes and Merge Gate 4.
- **How:** Standard `unittest.TestCase` suite running natively via `python -m unittest discover`.
- **Done when:** All tests in `test_m1_evidence.py` pass.

---

### 5.6 Demo / merge-gate verification

**Step 7 — Merge Gate Verification**

- **What:** Verify M1 AIA Merge Gate:
  - Gate 4: AIA aggregate tests pass on seeded Aarav fixture.
- **Done when:** `python -m unittest discover -s tests -t .` passes 100% of M0 + M1 tests.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M1)
- Backend will build DB tables and `POST /evidence` endpoint. AIA logic is written as pure service modules that Backend's service layer will call upon ingest.
- No blocking dependency: AIA tests use `aarav_seed.py` fixture generator.

### Suggested sequencing within AIA M1
```
Step 1 (Sanitizer & Enrichment) → Step 2 (Aggregates) → Step 3 (Twin Model)
  → Step 4 (__init__ exports) → Step 5 (Aarav Seed Fixture) → Step 6 (Unit Tests) → Step 7 (Verification)
```

### Merge gate checklist (M1)
- [ ] Seed load produces ≥ N events; all marked simulated where appropriate (Backend / AIA fixture)
- [ ] Live `POST /evidence` appears in GET within pipeline SLA (Backend gate)
- [ ] Simulator inject uses same adapters (Backend gate)
- [ ] AIA aggregate tests pass on seeded Aarav fixture (AIA gate — owned)

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Rule-based enrichment `a_ik` assignment is too simplistic | Use conservative defaults (`a_ik = 1.0` for explicit attribute matches, `0.5` for generic category matches) until LLM enrichment lands in M3/M4. |
| Aarav seed event timestamps drift relative to test execution | Use relative `delta_days` (0 = today, 21 = 21 days ago) instead of absolute ISO strings in scoring inputs. |
| Backend DB model differs from `SanitizedEvent` dataclass | Keep `SanitizedEvent` cleanly decoupled; Backend repository layer will map between DB ORM model and `SanitizedEvent`. |

---

## 8. Open Questions

1. **Rule-based Enrichment Mapping:** Should default enrichment use keyword matching on event titles/types (e.g. `"video_speaking"` → `public_speaker` attribute with `a_ik=1.0`), or require caller to pass explicit attribute IDs?
   - Recommendation: **Support both** — if explicit `attr_id` is passed, use it; otherwise fallback to simple keyword lookup map in `enrichment.py`.

2. **Windowing default for Revealed Self:** Should the default aggregation window be **21 days** (matching PRD Aarav seed length) or **7 days** (matching half-life decay)?
   - Recommendation: **21 days** for default Revealed Self history view, with parameter support for 7d / 14d windows.

3. **Branching strategy for M1:** We are currently on `m0` feature branch (which is committed). Should AIA merge `m0` → `aia` role branch first, and then cut `m1` from `aia`?
   - Recommendation: **Yes** — per `guidelines.md §5`, checkout `aia`, merge `m0`, then `git checkout -b m1` from `aia`.

4. **Aarav persona attribute IDs:** Should we standardize the attribute IDs for Aarav's seed persona as `public_speaker` (weight 0.5) and `builder` (weight 0.5)?
   - Recommendation: **Yes** — aligns with PRD persona description ("Aarav wants to become a confident public speaker and builder").

5. **Sanitizer dead-letter action:** When an invalid/corrupt event is rejected by `validate_and_sanitize_event`, should it return a structured error tuple or raise a custom `DeadLetterEventException`?
   - Recommendation: **Return error tuple `(False, None, error_msg)`** to allow non-raising validation pipelines in Backend ingest.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–5 above)
- [ ] Approve this plan
- [ ] Agent merges `m0` → `aia` and checks out `m1` feature branch
- [ ] Implement Steps 1–7 in order
- [ ] Run unit test suite — all green
- [ ] Show `git status` + diff + proposed commit message → wait for human approval → commit
- [ ] Done report
