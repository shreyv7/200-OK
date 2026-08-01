# Implementation Plan — AIA — M0

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M0 — Scaffold & Frozen Contracts
- **PRD features touched:** Infra only (no F# features); enables F1/F3/F5 work downstream (Gap math, interview extraction, bottleneck packet)
- **Techstack modules touched:**
  - `services/api/app/services/decision/` — Growth Decision Engine pure module scaffold
  - `services/api/app/services/identity/scoring/` — Gap formula constants + pure scoring functions
  - `services/api/app/schemas/` — shared Pydantic contracts (consumed from Backend; AIA proposes shape for Declared Self / Gap / Bottleneck / Decision packets)
  - `services/api/app/prompts/` — folder skeleton (AIA-owned: identity/bottleneck/evolution)
- **Goal:** Stand up the AIA-owned pure Python packages for scoring and decision logic, freeze the Gap formula constants and Declared Self extraction schema, and write unit tests for formula edge cases — so AIA can work against stable contracts without waiting for Backend wiring.

---

## 2. Scope (in)

Mapped 1:1 to M0 AIA checkboxes in `milestones.md`:

- **[AIA-1]** Pure Python package layout for `services/decision/` and `services/identity/scoring/` — no LLM calls yet, no DB calls.
- **[AIA-2]** Gap formula **constants file**: all fixed weights (`λ`, event-subtype weights, capacity tier thresholds), matching PRD §9 exactly.
- **[AIA-3]** JSON Schema / TypedDict for the **Declared Self extraction target** — prompt-ready, covering identity attributes, markers, and weights, suitable for Gemini structured output.
- **[AIA-4]** **Unit tests** for formula edge cases using fixture numbers (fully aligned persona yields Gap ≈ 0; drifted persona yields Gap > 50; clamping prevents negative/over-100 outputs; creation event lowers deficit; drift raises deficit). Tests pass even though the data pipeline is not wired yet.

---

## 3. Scope (out)

Items explicitly **not** done by AIA in M0:

- **Backend:** FastAPI app, `/healthz`, Alembic, Postgres, Redis, Clerk stub, seed script, GitHub Actions — all Backend M0 work.
- **AIS:** LangGraph graph stub, `SearchProvider`/`LLMProvider` interface stubs, Identity Stack assembly signature, prompt folder for `curator_*` / `reflect_*` — all AIS M0 work.
- No LLM calls of any kind this milestone.
- No actual Gap recomputation from real DB evidence — that's M2.
- No bottleneck diagnosis via LLM — that's M4.
- P2 features (Outside Voice, Growth Partner Match, Evolution Agent) — deferred.

---

## 4. Current repo state

- Repo is **greenfield**: only `docs/` and `.gitignore` exist; no `services/`, `apps/`, or any Python code.
- No virtual environment, no `pyproject.toml`, no test runner configured yet.
- Backend has not landed its Pydantic schemas yet (M0 Backend work). AIA will define its own pure TypedDict/dataclass shapes for the **Declared Self extraction target** and **Gap formula inputs/outputs**, and later reconcile with Backend's Pydantic models when they land.
- Assumptions:
  - Python 3.12 is available locally.
  - `pytest` will be used as the test runner (standard for the stack).
  - AIA works in the `aia` → `m0` branch; no Backend code exists to import.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Declared Self extraction TypedDict**

- **What:** `services/api/app/services/identity/scoring/declared_self.py`
  - `IdentityMarker(TypedDict)`: `id, label, description, observable_examples: list[str]`
  - `IdentityAttribute(TypedDict)`: `id, label, description, weight: float, markers: list[IdentityMarker], declared_weekly_target: float`
  - `DeclaredSelf(TypedDict)`: `version: int, user_id: str, attributes: list[IdentityAttribute], confirmed: bool, created_at: str`
  - Validation helper: `validate_weights(attrs) -> bool` — asserts `sum(w_i) ≈ 1.0`.
- **Why:** Milestone checkbox AIA-3; this is the schema Gemini must fill during onboarding (M3). Freezing it now ensures AIS/Backend can plan against a stable shape.
- **How:** Plain TypedDict + runtime validation helper. No LLM, no DB. JSON Schema exported via `typing_extensions` / `jsonschema` for prompt embedding.
- **Done when:** `from services.identity.scoring.declared_self import DeclaredSelf, validate_weights` works in a clean Python env; JSON Schema round-trip test passes.

---

**Step 2 — Gap formula constants file**

- **What:** `services/api/app/services/identity/scoring/constants.py`
  - `LAMBDA = math.log(2) / 7` — seven-day half-life decay
  - Event subtype weights (from PRD §9):
    ```python
    EVENT_WEIGHTS = {
        "mission_completed":    3.0,
        "github_commit":        4.0,
        "published_artifact":   5.0,
        "attended_experience":  4.0,
        "passive_item":         1.0,
        "focus_drift_10min":   -2.0,
    }
    ```
  - Category bucketing:
    ```python
    CREATION_TYPES = {"mission_completed", "github_commit", "published_artifact", "attended_experience"}
    PASSIVE_TYPES  = {"passive_item"}
    DRIFT_TYPES    = {"focus_drift_10min"}
    ```
  - Capacity tier thresholds:
    ```python
    CAPACITY_FULL_MIN  = 67
    CAPACITY_LIGHT_MIN = 34
    CAPACITY_MICRO_MIN = 0
    ```
  - Failure threshold: `DISMISSAL_FAILURE_THRESHOLD = 3`, `DISMISSAL_WINDOW_DAYS = 14`
- **Why:** Milestone checkbox AIA-2; PRD §9 hard constraint — these are never LLM outputs.
- **How:** Single constants module, no imports from DB or LLM.
- **Done when:** Module importable; all constants match PRD §9 values exactly; reviewed against PRD table in unit tests.

---

### 5.2 Core logic

**Step 3 — Pure Gap scoring functions**

- **What:** `services/api/app/services/identity/scoring/gap.py`
  - `decay_weight(delta_days: float) -> float` — `e^(-λ × Δt)`
  - `compute_revealed(events: list[EvidenceInput], attr_id: str) -> float` — `R_i = Σ (a_ik × q_k × e^(-λΔt_k))`
  - `compute_deficit(D_i: float, R_i: float) -> float` — `clamp((D_i - R_i) / D_i, 0, 1)`
  - `compute_gap_score(attributes: list[AttrInput], events: list[EvidenceInput]) -> GapResult`
    - Returns `GapResult(gap_score: int, alignment: int, per_attribute: list[AttributeBreakdown])`
    - `AttributeBreakdown`: `attr_id, w_i, D_i, R_i, deficit, creation_contribution, passive_contribution, drift_contribution`
  - `compute_create_consume(events: list[EvidenceInput]) -> CreateConsumeResult`
    - `CreateConsumeResult(create_points, consume_points, drift_points, ratio)`
  - `compute_consistency(events: list[EvidenceInput], window_days: int = 7) -> float` — fraction of days with ≥1 positive event
  - `compute_momentum(gap_now: int, gap_7d_ago: int) -> int` — signed delta
  - Internal dataclasses (not Pydantic yet): `EvidenceInput(event_type, attr_id, a_ik, delta_days)`, `AttrInput(attr_id, w_i, D_i)`
- **Why:** Milestone checkbox AIA-1; core deterministic logic needed by M2 wiring. Pure functions with no I/O are safe to write before Backend exists.
- **How:** Pure Python dataclasses + math only. Import only `constants.py`. No LangGraph, no DB, no LLM.
- **Done when:** All functions importable; unit tests (Step 5) pass.

---

**Step 4 — Decision package scaffold**

- **What:** `services/api/app/services/decision/__init__.py` and `services/api/app/services/decision/packet.py`
  - `BottleneckCandidate(dataclass)`: `label: str, confidence: float, supporting_evidence_ids: list[str], missing_evidence_ids: list[str], alternative: str | None`
  - `DecisionPacket(dataclass)`: `user_id, gap_score, gap_delta, alignment, create_consume_ratio, bottleneck_candidates: list[BottleneckCandidate], invalidate_stack: bool, timestamp: str`
  - `BOTTLENECK_TAXONOMY: list[str]` = `["confidence", "consistency", "execution", "accountability", "knowledge", "communication", "focus", "networking", "discipline", "burnout"]`
  - Stub function `build_decision_packet(...) -> DecisionPacket` — takes GapResult + prior_gap, returns packet with `invalidate_stack = (gap_delta > INVALIDATION_THRESHOLD)` (threshold configurable constant). Bottleneck candidates list is empty at M0 (populated in M2/M4).
- **Why:** Milestone checkbox AIA-1; AIS needs the `DecisionPacket` contract to stub its Coordinator node in M0.
- **How:** Pure dataclasses; `build_decision_packet` is a deterministic rule, no LLM.
- **Done when:** AIS can `from services.decision.packet import DecisionPacket` and construct a fixture instance in tests.

---

### 5.3 Integration / wiring

**Step 5 — Package `__init__` files and import chain**

- **What:** Create `__init__.py` files to make the following importable as packages:
  - `services/api/app/services/__init__.py`
  - `services/api/app/services/identity/__init__.py`
  - `services/api/app/services/identity/scoring/__init__.py`
  - `services/api/app/services/decision/__init__.py`
  - Top-level `services/api/app/__init__.py` (if needed for test discovery)
- Also create `services/api/pyproject.toml` (or `setup.py`) so the package is pip-installable in editable mode for tests.
- **Why:** Required for `Merge Gate 2` — "Schema package imports cleanly in AIA and AIS test suites."
- **How:** Minimal `pyproject.toml` with `[tool.pytest.ini_options]` and `pythonpath = ["."]`.
- **Done when:** `pytest --collect-only` finds AIA tests without import errors.

---

**Step 6 — Prompt folder skeleton**

- **What:**
  - `services/api/app/prompts/identity/declared_self_extraction_v1.md` — placeholder with prompt shape, variable slots (`{interview_transcript}`, `{output_schema_json}`), and milestone tag `[M0][aia]`.
  - `services/api/app/prompts/identity/bottleneck_diagnosis_v1.md` — placeholder.
  - `services/api/app/prompts/identity/evolution_proposal_v1.md` — placeholder.
- **Why:** `milestones.md §4 Definition of Done` — prompt versions recorded under `prompts/` with milestone tag.
- **How:** Markdown files only; no LLM calls.
- **Done when:** Files exist at correct paths; content has correct schema reference to `DeclaredSelf` TypedDict.

---

### 5.4 Seeds / fixtures

No seeds for AIA M0. Fixture data lives in test files (Step 7).

---

### 5.5 Tests

**Step 7 — Unit tests for Gap formula edge cases**

- **What:** `services/api/tests/identity/scoring/test_gap.py`
  - **Fixture A — Fully aligned persona:** `R_i ≈ D_i` for all attributes → `gap_score ≈ 0`, `alignment ≈ 100`.
  - **Fixture B — Fully drifted persona:** `R_i = 0` for all attributes → `gap_score = 100`, `alignment = 0`.
  - **Fixture C — Partial drift (Aarav-like):** Mix of creation and passive events → `40 < gap_score < 80`; breakdown sums check out; `create_consume_ratio < 1`.
  - **Fixture D — Decay test:** Same event at `Δt = 0` vs `Δt = 7` — decayed version contributes exactly half the weight.
  - **Fixture E — Clamp test:** Even if `R_i >> D_i` (overachiever), `deficit_i = 0` (no negative gap from one attribute).
  - **Fixture F — Creation event lowers gap:** Add a `mission_completed` to Fixture C → `new_gap < old_gap`.
  - **Fixture G — Drift raises gap:** Add `focus_drift_10min` event to Fixture C → `new_gap > old_gap`.
  - **Fixture H — Weight sum validation:** `validate_weights` rejects attrs summing to ≠ 1.
  - **Fixture I — DecisionPacket construction:** `build_decision_packet` returns packet with correct `invalidate_stack` flag.
- **Why:** Milestone checkbox AIA-4; Merge Gate 3 — formula constants must be locked by tests before Backend wires results.
- **How:** `pytest`; no mocks needed — pure functions only.
- **Done when:** `pytest services/api/tests/identity/` exits green with all fixtures.

---

### 5.6 Demo / merge-gate verification

**Step 8 — Merge gate smoke check**

- **What:** Verify all three M0 Merge Gates pass from AIA side:
  1. **Gate 1** (docker/local brings API up): AIA has no server — N/A for AIA until Backend lands. ✓ (not AIA's gate)
  2. **Gate 2** (schema package imports cleanly in AIA test suite): `pytest --collect-only` shows all AIA tests discovered; no `ImportError`. ✓ AIA owns this.
  3. **Gate 3** (no Gemini/Tavily imports outside `providers/`): `grep -r "import google.generativeai\|import tavily" services/api/app/services/ services/api/app/agents/` → zero results. ✓ AIA owns this.
- **Done when:** All three checks pass locally before merge.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M0)

| Need | Status | Stub strategy |
|---|---|---|
| `EvidenceEvent` Pydantic schema | Not yet landed | AIA uses its own internal `EvidenceInput` dataclass; reconcile field names when Backend M0 merges. No blocking dependency. |
| `pyproject.toml` / monorepo structure | Not defined | AIA creates its own minimal `pyproject.toml` under `services/api/`; Backend may consolidate later. |
| DB / FastAPI | Not needed | AIA M0 has zero DB or HTTP dependencies. |

### What AIS needs from AIA (M0)

- `DecisionPacket` dataclass shape → AIS stubs its Coordinator with a fixture `DecisionPacket`.
- AIA should finalize `packet.py` **before** AIS writes its Coordinator stub test.

### Suggested sequencing within AIA M0

```
Step 2 (constants) → Step 1 (DeclaredSelf schema) → Step 3 (gap.py) → Step 4 (decision packet)
  → Step 5 (package wiring) → Step 7 (tests) → Step 6 (prompt stubs) → Step 8 (gate check)
```

### Merge gate checklist (M0)

- [ ] `docker compose up` → health checks green (Backend gate — not AIA)
- [ ] Schema package imports cleanly in AIA test suite (`pytest --collect-only` green)
- [ ] No Gemini/Tavily SDK imports outside `providers/` in AIA code

**Merge order:** Backend first → AIA → AIS.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Backend `EvidenceEvent` schema differs from AIA's `EvidenceInput` fields | Keep AIA's internal dataclass minimal; add a `from_evidence_event()` adapter in M1 when Backend schema lands. |
| `pyproject.toml` layout conflicts with future monorepo root setup | Scope `pyproject.toml` to `services/api/` only; use `pythonpath` in pytest config to avoid install-mode conflicts. |
| Formula constants diverge from PRD §9 wording | Tests in Step 7 explicitly assert against PRD-quoted values; any constant change requires test update. |
| Weight sum = 1.0 constraint causes float precision issues | Use `abs(sum(weights) - 1.0) < 1e-6` in `validate_weights`. |
| AIS reads a stale `DecisionPacket` shape | Land `packet.py` early in the milestone; AIS is told to import from this path. |

---

## 8. Open Questions

1. **Monorepo root / Python environment:** Does the team want a single `pyproject.toml` at the repo root, or per-service (`services/api/pyproject.toml`)? AIA will create a per-service one unless told otherwise.
   - Recommendation: **per-service**, consistent with `techstack.md §24` folder isolation. Easy to hoist to monorepo root later.

2. **`EvidenceInput` field naming:** AIA's internal dataclass will use `(event_type, attr_id, a_ik, delta_days)`. Should AIA pre-align field names with Backend's planned `EvidenceEvent` Pydantic schema now, or reconcile in M1?
   - Recommendation: **reconcile in M1** — keep AIA internal names now, add a thin adapter when Backend M0 is merged, to avoid blocking AIA on Backend schedule.

3. **`declared_weekly_target` units:** PRD §9 says `D_i > 0` in "evidence points" but doesn't specify the numeric range per attribute. What should Aarav's `D_i` values be for the seed persona? (e.g. Public Speaker attribute: `D_i = 20` evidence points/week?)
   - Recommendation: **AIA proposes defaults** in `constants.py` (e.g. `DEFAULT_DECLARED_TARGET = 15.0`) that yield `gap_score ≈ 65–70` for the Aarav seed persona. Backend seed script uses these values.

4. **Dev branch sync:** Is `dev` branch empty / does it exist yet on remote? Should AIA create the `aia` role branch from `main` or from `dev`?
   - Recommendation: create from **`main`** if `dev` doesn't exist yet, or ask human to create `dev` first per `guidelines.md §5`.

5. **Python version lock:** Confirm Python **3.12** is the target. Any preference for `uv` vs standard `pip` for local env setup?
   - Recommendation: **`uv`** for speed in a hackathon, but plain `pip` is fine; just needs an answer before writing `pyproject.toml`.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–5 above)
- [ ] Approve this plan
- [ ] Agent checks out / creates `aia` branch from `dev` (or `main`) → creates `m0` feature branch
- [ ] Implement Steps 1–8 in order
- [ ] Run `pytest services/api/tests/identity/` — all green
- [ ] Run grep gate check (no vendor imports outside `providers/`)
- [ ] Show `git status` + diff + proposed commit message → wait for human approval → commit
- [ ] Done report
