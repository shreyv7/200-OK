# Implementation Plan — AIA — M1

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M1 — Evidence Pipeline + Twin Shell
- **PRD features touched:** F2 (Evidence Engine + Revealed Self, P0)
- **Techstack modules touched:**
  - `services/api/app/services/identity/sanitizer.py` — dead-letter / invalid event rejection validator
  - `services/api/app/services/identity/enrichment.py` — rule-based event enrichment mapping to `EvidenceEvent.identityAttributeIds`
  - `services/api/app/services/identity/aggregates.py` — Revealed Self aggregate builder over `EvidenceEvent` streams
  - `services/api/app/services/identity/twin.py` — Digital Twin read model combining Backend `DeclaredSelf` + Revealed aggregates
  - `services/api/tests/fixtures/aarav_seed.py` — Aarav 21-day seeded evidence fixture generating Backend `EvidenceEvent` Pydantic instances
  - `services/api/tests/identity/test_m1_evidence.py` — unit tests for M1 evidence pipeline
- **Integration Constraints (`docs/integration-notes.md`):**
  - M0 from Backend, AIA, and AIS is integrated on `dev` and `main`.
  - Must consume `EvidenceEvent` and `DeclaredSelf` directly from **`app.schemas`** — **do not duplicate `EvidenceEvent`**.
  - Gap math lives strictly in `app.services.identity.scoring` (AIA-owned). Never let LLMs compute Gap.
- **Goal:** Update and land AIA evidence intelligence modules on branch `aia-m1`: enrich incoming `EvidenceEvent` objects with identity attribute tags, aggregate revealed behavior across temporal windows, assemble the Digital Twin read model, and enforce dead-letter rejection — verified against Backend Pydantic schemas via `pytest -q tests/identity/`.

---

## 2. Scope (in)

Mapped 1:1 to M1 AIA checkboxes in `milestones.md`:

- **[AIA-1] Evidence enrichment:** Map incoming `EvidenceEvent` objects to `identityAttributeIds` and applicability `a_ik` using rule-based/keyword matching.
- **[AIA-2] Revealed Self aggregate builder:** Compute aggregated evidence totals, event counts, and category distributions over 7-day, 14-day, and 21-day rolling windows from `EvidenceEvent` streams.
- **[AIA-3] Twin read model:** Read model combining Backend `app.schemas.identity.DeclaredSelf` with current Revealed Self aggregates.
- **[AIA-4] Reject scoring on invalid/dead-letter events:** Validator module that rejects malformed, out-of-bounds (`a_ik > 1.0`, negative weights, unknown subtypes), or corrupt events before scoring.

---

## 3. Scope (out)

Items explicitly **not** done by AIA in M1:

- **Backend:** `POST /api/v1/evidence`, `GET /api/v1/evidence`, DB tables, internal `evidence.created` event bus, simulator endpoint, full database seed script — all Backend M1 work.
- **AIS:** Subscribing to `evidence.created`, Coordinator decision hooks — all AIS M1 work.
- No live database writes or FastAPI routers (Backend owns endpoints and DB persistence).
- No Gap score computation changes (that is M2).
- No LLM calls for enrichment (rule-based MVP per `milestones.md`).

---

## 4. Current repo state

- **M0 integrated on `dev` and `main`**:
  - `services/api/app/schemas/` contains Backend Pydantic models: `EvidenceEvent`, `DeclaredSelf`, `IdentityAttribute`, `IdentityMarker`.
  - `services/api/app/services/identity/scoring/` contains AIA Gap formula logic: `constants.py`, `declared_self.py`, `gap.py`.
  - `docs/integration-notes.md` is present on `dev`.
- Branching setup required:
  - Create feature branch **`aia-m1`** from `aia` (synced with `dev`).

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Dead-Letter Sanitizer & Schema Integration**

- **What:** `services/api/app/services/identity/sanitizer.py`
  - Update `validate_and_sanitize_event` to accept either raw dictionaries or Backend `app.schemas.evidence.EvidenceEvent` objects.
  - Validation rules:
    - `userId` (or `user_id`) must be a non-empty string.
    - `type` must be present and valid.
    - `timestamp` must be a valid datetime (or `delta_days >= 0.0`).
    - Base weight / value must be numeric and non-corrupt.
  - Returns `(is_valid, sanitized_evidence_event, error_message)`.
- **Why:** Milestone checkbox AIA-4; contract with Backend for rejecting dead-letter events without raising unhandled server exceptions.
- **How:** Consume `app.schemas.evidence.EvidenceEvent` Pydantic model.
- **Done when:** `validate_and_sanitize_event` validates valid `EvidenceEvent` objects and rejects dead-letter payloads with `(False, None, error_msg)`.

---

**Step 2 — Rule-Based Evidence Enrichment**

- **What:** `services/api/app/services/identity/enrichment.py`
  - Function `enrich_evidence_event(event: EvidenceEvent, declared_self: Optional[DeclaredSelf] = None) -> EvidenceEvent`
  - Rule-based keyword/category mapper:
    - Inspects `event.type`, `event.metadata` (title, description), and `event.category`.
    - Keywords for public speaking (`speak`, `talk`, `presentation`, `toastmaster`) -> maps `public_speaker` into `event.identityAttributeIds`.
    - Keywords for building (`commit`, `code`, `build`, `github`, `project`, `ship`) -> maps `builder` into `event.identityAttributeIds`.
    - If unmapped and `declared_self` provided, maps to primary attribute ID with reduced applicability.
- **Why:** Milestone checkbox AIA-1; maps incoming evidence to identity attributes before aggregate calculation.
- **How:** Pure function over Pydantic `EvidenceEvent`.
- **Done when:** `enrich_evidence_event` correctly populates `event.identityAttributeIds` based on keyword rules.

---

### 5.2 Core logic

**Step 3 — Revealed Self Aggregate Builder**

- **What:** `services/api/app/services/identity/aggregates.py`
  - Update `build_revealed_aggregates(events: list[EvidenceEvent], attribute_ids: list[str], window_days: int = 21) -> RevealedSelfAggregates`
    - Converts `EvidenceEvent` list to `EvidenceInput` scoring objects (computing `delta_days` from `event.timestamp` relative to target reference time).
    - Computes per-attribute recency-decayed totals `R_i` using `gap.py` `compute_revealed`.
    - Computes category point totals (`creation`, `passive_learning`, `focus_drift`) and overall `create_consume_ratio`.
    - Computes 7-day active day `consistency_score`.
- **Why:** Milestone checkbox AIA-2; Revealed Self inputs for M2 Gap computation.
- **How:** Pure module consuming Backend `EvidenceEvent` Pydantic model.
- **Done when:** `build_revealed_aggregates` computes correct point totals and ratios over test streams.

---

**Step 4 — Digital Twin Read Model**

- **What:** `services/api/app/services/identity/twin.py`
  - Dataclass `DigitalTwinReadModel`: `userId: str`, `declaredVersion: int`, `declaredSelf: DeclaredSelf`, `revealedAggregates: RevealedSelfAggregates`, `gapResult: GapResult`, `lastUpdatedAt: datetime`
  - Function `assemble_digital_twin(user_id: str, declared_self: DeclaredSelf, events: list[EvidenceEvent], window_days: int = 21) -> DigitalTwinReadModel`
    - Combines Backend `app.schemas.identity.DeclaredSelf` Pydantic model with current `RevealedSelfAggregates` and `GapResult`.
- **Why:** Milestone checkbox AIA-3; unified Digital Twin read model.
- **How:** Pure assembly function consuming `app.schemas.identity.DeclaredSelf` and `app.schemas.evidence.EvidenceEvent`.
- **Done when:** `assemble_digital_twin` produces complete `DigitalTwinReadModel`.

---

### 5.3 Integration / wiring

**Step 5 — Service Package Exports**

- **What:** Update `services/api/app/services/identity/__init__.py` to export sanitizer, enrichment, aggregates, and twin assembly functions.
- **Why:** Ensures clean import path for Backend and AIS (`from app.services.identity import assemble_digital_twin`).
- **Done when:** All modules import cleanly from `app.services.identity`.

---

### 5.4 Seeds / fixtures

**Step 6 — Aarav 21-Day Seed Fixture Generator (Backend Pydantic Schemas)**

- **What:** `services/api/tests/fixtures/aarav_seed.py`
  - Update `get_aarav_declared_self()` to return `app.schemas.identity.DeclaredSelf` Pydantic model.
  - Update `generate_aarav_seed_events()` to return list of `app.schemas.evidence.EvidenceEvent` Pydantic instances.
  - Generates ~30 Realistic 21-day simulated evidence events for Aarav (60% passive, 25% drift, 15% creation), all tagged `simulated=True`.
- **Why:** Merge Gate 4 requirement — "AIA aggregate tests pass on seeded Aarav fixture."
- **Done when:** `generate_aarav_seed_events()` outputs valid `EvidenceEvent` Pydantic objects.

---

### 5.5 Tests

**Step 7 — M1 Unit Tests Suite**

- **What:** `services/api/tests/identity/test_m1_evidence.py`
  - **Test 1:** `test_sanitizer_validation` — validates `EvidenceEvent` payloads and rejects dead-letter inputs.
  - **Test 2:** `test_enrichment_mapping` — verifies keyword enrichment populates `identityAttributeIds`.
  - **Test 3:** `test_aarav_aggregates` — computes `RevealedSelfAggregates` over Aarav 21-day Pydantic event stream; asserts `create_consume_ratio < 1.0`.
  - **Test 4:** `test_digital_twin_assembly` — assembles `DigitalTwinReadModel` combining `DeclaredSelf` Pydantic model + Aarav event stream.
- **Why:** Validates all M1 AIA checkboxes.
- **How:** Executable via `cd services/api && pytest -q tests/identity/`.
- **Done when:** `cd services/api && pytest -q tests/identity/` passes 100% green.

---

### 5.6 Demo / merge-gate verification

**Step 8 — Merge Gate Smoke Check**

- **What:** Verify M1 AIA Merge Gate:
  - Gate 4: AIA aggregate tests pass on seeded Aarav fixture using Backend schemas.
- **Done when:** `pytest -q tests/identity/` exits 0 with zero errors.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M1)
- Backend `EvidenceEvent` (`app.schemas.evidence`) and `DeclaredSelf` (`app.schemas.identity`) — **already present on `dev`**.
- Backend M1 service layer will call AIA's `enrich_evidence_event` and `validate_and_sanitize_event` on `POST /evidence`.

### Suggested sequencing within AIA M1
```
Branch setup (checkout aia-m1 from aia synced with dev)
  → Step 1 (Sanitizer) → Step 2 (Enrichment) → Step 3 (Aggregates) → Step 4 (Twin Model)
  → Step 5 (__init__ exports) → Step 6 (Aarav Seed Fixture) → Step 7 (Tests) → Step 8 (Gate check)
```

### Merge gate checklist (M1)
- [ ] Seed load produces ≥ N events; all marked simulated where appropriate (Backend / AIA fixture)
- [ ] Live `POST /evidence` appears in GET within pipeline SLA (Backend gate)
- [ ] Simulator inject uses same adapters (Backend gate)
- [ ] AIA aggregate tests pass on seeded Aarav fixture (AIA gate — owned)

**Merge order:** Backend → AIA → AIS → `dev` → `main`.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Pydantic `EvidenceEvent` field `timestamp` timezone mismatch during `delta_days` calculation | Ensure all timestamp comparisons convert `datetime` objects to UTC timezone-aware datetimes before computing age in days. |
| AIS or Backend imports AIA modules directly during parallel work | Keep function signatures stable and export all public interfaces through `app.services.identity.__init__`. |
| Pydantic schema validation errors on raw payloads | Return explicit error tuple `(False, None, err_msg)` from `validate_and_sanitize_event` so callers can handle bad requests cleanly. |

---

## 8. Open Questions

1. **Branch Name:** User specified `aia-m1` as the branch name (cut from `aia`, synced with `dev`). Should we create `aia-m1` from `aia` (after pulling latest `dev`)?
   - Recommendation: **Yes** — sync `aia` with `dev`, then `git checkout -b aia-m1` from `aia`.

2. **Schema Import Path:** Should AIA import `EvidenceEvent` from `app.schemas.evidence` or `app.schemas` directly?
   - Recommendation: **`from app.schemas.evidence import EvidenceEvent`** (and re-export via `app.schemas`).

3. **`delta_days` calculation helper:** Should AIA provide a helper `get_event_delta_days(timestamp: datetime, ref_time: Optional[datetime] = None) -> float` to convert Pydantic `datetime` to fractional days?
   - Recommendation: **Yes** — place in `sanitizer.py` or `gap.py` for consistent timestamp math across AIA modules.

4. **Re-running tests:** User instructed to run tests via `cd services/api && pytest -q tests/identity/`. Confirm `pytest` is used as test runner for this branch execution.
   - Recommendation: **Yes** — use `pytest -q tests/identity/` as specified.

5. **Merge path:** User noted "Merge after Backend M1 lands on dev". Should AIA keep work on `aia-m1` branch until Backend M1 lands on `dev`?
   - Recommendation: **Yes** — prepare commit on `aia-m1`, show commit for approval, and wait for human instruction to merge into `dev`.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–5 above)
- [ ] Approve this plan
- [ ] Agent syncs `aia` with `dev` and creates `aia-m1` feature branch
- [ ] Implement Steps 1–8 in order
- [ ] Run `cd services/api && pytest -q tests/identity/` — all green
- [ ] Show `git status` + diff + proposed commit message → wait for human approval → commit
- [ ] Done report
