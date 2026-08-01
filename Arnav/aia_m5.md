# Implementation Plan — AIA — M5

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M5 — Guardian Gate + Trust Ledger P0 (Demo Peak)
- **PRD features touched:** F6 P0 (Guardian / Consent Layer), F7 P0 (Trust Ledger — dismissal budget / completion evidence)
- **Techstack modules touched:**
  - `services/api/app/services/identity/scoring/constants.py` — Verify and formally expose Capacity tier constants as the shared config (M5 AIA-1)
  - `services/api/app/services/identity/growth_decision.py` — Upgrade `evaluate_growth_decision` with dismissal rate + intervention budget signals (M5 AIA-2)
  - `services/api/app/services/identity/guardian_decision.py` — **[NEW]** Structured `GuardianDecision` dataclass + deterministic `evaluate_guardian_action()` function (M5 AIA-3)
  - `services/api/app/services/identity/recompute.py` — Wire completion evidence → `recompute_user_gap` hook (M5 AIA-4)
  - `services/api/tests/identity/test_m5_guardian.py` — **[NEW]** M5 unit test suite
- **Goal:** Provide AIS Guardian node with a deterministic, rule-based `GuardianDecision` object (cancel / delay / downgrade + structured reason code + plain-language copy field) and extend the Growth Decision Engine to suppress or downgrade curation when dismissal rate is high or intervention budget is exhausted. Ensure completion events reliably trigger Gap recompute for demo score movement.

---

## 2. Scope (in)

Mapped 1:1 to M5 AIA checkboxes in `milestones.md`:

- **[AIA-M5-1] Capacity tier mapping constants:** `CAPACITY_FULL_MIN = 67`, `CAPACITY_LIGHT_MIN = 34`, `CAPACITY_MICRO_MIN = 0` in `constants.py` — already present (M4). Action: verify and add `INTERVENTION_DAILY_CAP = 5` and `INTERVENTION_MIN_SPACING_HOURS = 1` as new M5 constants required by Guardian rules.
- **[AIA-M5-2] Decision Engine — dismissal rate + budget integration:** Update `evaluate_growth_decision` to accept `dismissal_rate: float` and `interventions_today: int`. Rules:
  - `interventions_today >= INTERVENTION_DAILY_CAP` → `should_recurate = False` (budget exhausted, Guardian will cancel).
  - `dismissal_rate >= 0.6` (3 of 5+ recent interventions dismissed) → downgrade `curation_intensity` by one tier.
- **[AIA-M5-3] Guardian reason codes:** New `guardian_decision.py` module exposing:
  - `GuardianAction = Literal["allow", "downgrade", "delay", "cancel"]`
  - `@dataclass GuardianDecision(action, reason_code, plain_language_reason, intensity)`
  - `evaluate_guardian_action(capacity_pct, interventions_today, dismissal_rate, hours_since_last_intervention) -> GuardianDecision`
  - Rules (strictly deterministic, no LLM):
    - `interventions_today >= 5` → `cancel` / `reason_code = "daily_cap_reached"`.
    - `hours_since_last < 1` → `delay` / `reason_code = "too_frequent"`.
    - `dismissal_rate >= 0.6` → `downgrade` one tier / `reason_code = "high_dismissal_rate"`.
    - `capacity_pct < CAPACITY_LIGHT_MIN` → `downgrade` to `micro` / `reason_code = "low_capacity"`.
    - Otherwise → `allow`.
  - Plain-language reasons are **static string templates** — LLM may rephrase copy in M6+, rules decide here.
- **[AIA-M5-4] Completion evidence → Gap recompute:** Confirm that `wiring.py` / `orchestration.py` routes `mission_completed`, `attended_experience`, and `github_commit` events through `recompute_user_gap` (this path exists from M2; M5 action is to verify and add integration test that a completion event lowers Gap on the seeded Aarav persona).

---

## 3. Scope (out)

AIA does **not** build for M5:

- **Backend M5:** Capacity persistence as evidence/context event, intervention budget fields in DB, Ledger CRUD APIs, lens-weight persistence, variant storage (`full`/`light`/`micro`), ledger seeding with two prior dismissals, WS/poll dismiss path — all Backend M5.
- **AIS M5:** Guardian node/gate in LangGraph graph, `full`/`light`/`micro` variant generation/caching, Reflection P0 (3 dismissals → `failed` + lens weight −40%), System Unlearning tags on ledger entries, alternate stack cache — all AIS M5.
- LLM-generated Guardian copy phrasing — deferred to M6+.
- Trust Ledger full P1 history endpoint — M6 Backend.
- Capacity Slider local swap logic — UI/UX.

---

## 4. Current repo state

- **M0–M4 complete and merged on `main`, `dev`, `aia`** (pulled at session start; commit `9f8cba5`).
- **Already exists:**
  - `constants.py`: `CAPACITY_FULL_MIN = 67`, `CAPACITY_LIGHT_MIN = 34`, `CAPACITY_MICRO_MIN = 0`, `DISMISSAL_FAILURE_THRESHOLD = 3`, `DISMISSAL_WINDOW_DAYS = 14` — all present ✓
  - `growth_decision.py`: `evaluate_growth_decision` with `capacity_pct` intensity mapping — M4 ✓
  - `recompute.py`: `recompute_user_gap` wiring `bottleneck_v1` + `growth_decision` — M4 ✓
  - `wiring.py` / `orchestration.py`: hooks for event-driven recompute — M2/M3 ✓
  - `LedgerEntry` schema in `app/schemas/ledger.py` with `hypothesisFamily`, `action`, `verdict`, `unlearningTriggered`, `lensWeightAdjustment` — Backend-owned, AIA consumes ✓
- **Greenfield for M5 AIA:**
  - `guardian_decision.py` — does not exist yet
  - `constants.py` additions: `INTERVENTION_DAILY_CAP`, `INTERVENTION_MIN_SPACING_HOURS`
  - `growth_decision.py` extension: `dismissal_rate` + `interventions_today` inputs
  - `test_m5_guardian.py` — does not exist yet

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Add M5 Constants to `constants.py`**

- **What:** `services/api/app/services/identity/scoring/constants.py`
  - Add:
    ```python
    INTERVENTION_DAILY_CAP: int = 5        # PRD F6: cap 5 per day
    INTERVENTION_MIN_SPACING_HOURS: float = 1.0  # PRD F6: time since last
    HIGH_DISMISSAL_RATE_THRESHOLD: float = 0.6   # 3-of-5+ = suppress/downgrade
    ```
- **Why:** M5 AIA-1. These numbers are PRD-derived and must remain deterministic constants, not LLM-computed.
- **Done when:** `from app.services.identity.scoring.constants import INTERVENTION_DAILY_CAP` works cleanly.

---

### 5.2 Core logic

**Step 2 — `guardian_decision.py`: Structured Guardian Reason Codes**

- **What:** `services/api/app/services/identity/guardian_decision.py`
  - `GuardianAction = Literal["allow", "downgrade", "delay", "cancel"]`
  - `@dataclass GuardianDecision(action: GuardianAction, reason_code: str, plain_language_reason: str, intensity: str)`
  - `evaluate_guardian_action(capacity_pct, interventions_today, dismissal_rate, hours_since_last_intervention, current_intensity="full") -> GuardianDecision`
  - **Rule table (checked in priority order):**

    | Priority | Condition | Action | Reason Code | Plain-language reason |
    |---|---|---|---|---|
    | 1 | `interventions_today >= INTERVENTION_DAILY_CAP` | `cancel` | `daily_cap_reached` | `"You've had 5 growth touchpoints today. Rest is growth too."` |
    | 2 | `hours_since_last_intervention < INTERVENTION_MIN_SPACING_HOURS` | `delay` | `too_frequent` | `"Last intervention was recent. Giving you space before the next step."` |
    | 3 | `dismissal_rate >= HIGH_DISMISSAL_RATE_THRESHOLD` | `downgrade` | `high_dismissal_rate` | `"You've been skipping recent suggestions. Switching to a lighter touch."` |
    | 4 | `capacity_pct < CAPACITY_LIGHT_MIN` | `downgrade` to `micro` | `low_capacity` | `"Capacity changed; preserving momentum without adding load."` |
    | 5 | Otherwise | `allow` | `"ok"` | `""` |

  - For `downgrade`: intensity steps down one tier (`"full"` → `"light"`, `"light"` → `"micro"`, `"micro"` stays `"micro"`). If `low_capacity` and current is already `"micro"`: action stays `downgrade` with `"micro"`.
- **Why:** M5 AIA-3; PRD F6: "always shows a plain-language reason"; Guardian notes "rules decide" — no LLM on this path.
- **Done when:** `evaluate_guardian_action` returns correct `GuardianDecision` for each priority scenario in tests.

---

**Step 3 — Extend `evaluate_growth_decision` with Dismissal Budget**

- **What:** `services/api/app/services/identity/growth_decision.py`
  - Add two optional parameters: `dismissal_rate: float = 0.0` and `interventions_today: int = 0`.
  - New rules integrated into `evaluate_growth_decision`:
    - If `interventions_today >= INTERVENTION_DAILY_CAP`: set `should_recurate = False`, override reason to `"Daily intervention budget exhausted"`.
    - If `dismissal_rate >= HIGH_DISMISSAL_RATE_THRESHOLD` and `intensity == "full"`: downgrade `intensity` to `"light"` (Guardian will further enforce).
- **Why:** M5 AIA-2; AIS Coordinator reads `DecisionPacket.should_recurate` and `curation_intensity` to decide whether to invoke the Guardian node at all.
- **Done when:** `evaluate_growth_decision(…, interventions_today=5)` returns `should_recurate=False`; dismissal rate ≥ 0.6 downgrades intensity.

---

**Step 4 — Verify completion evidence → Gap recompute path**

- **What:** Review `services/api/app/services/identity/wiring.py` and `orchestration.py`
  - Confirm `mission_completed`, `attended_experience`, `github_commit` are routed to `recompute_user_gap` (these are `CREATION_TYPES` in `constants.py`).
  - If routing exists: add one integration test only. If missing: add a lightweight wiring call.
- **Why:** M5 AIA-4; PRD F7: "Completing alternate micro-mission lowers Gap on seeded persona" (Merge Gate 4).
- **Done when:** A test seeding a `mission_completed` event for Aarav shows Gap score drops by ≥1 point vs. baseline.

---

### 5.3 Integration / wiring

**Step 5 — Update `services/identity/__init__.py` Exports**

- Export `GuardianDecision`, `GuardianAction`, `evaluate_guardian_action`.
- **Done when:** `from app.services.identity import evaluate_guardian_action` resolves cleanly.

---

### 5.4 Seeds / fixtures

No new seed fixtures required for M5 AIA. Existing `aarav_seed.py` has `mission_completed` events sufficient for completion-evidence tests. The ledger seed (two prior dismissals) is **Backend M5 work**.

---

### 5.5 Tests

**Step 6 — M5 Unit Test Suite**

- **What:** `services/api/tests/identity/test_m5_guardian.py`
  - **Test 1 (Daily cap → cancel):** `evaluate_guardian_action(capacity_pct=80, interventions_today=5, dismissal_rate=0.0, hours_since_last=4)` → `action=="cancel"`, `reason_code=="daily_cap_reached"`.
  - **Test 2 (Too frequent → delay):** `evaluate_guardian_action(capacity_pct=80, interventions_today=1, dismissal_rate=0.0, hours_since_last=0.3)` → `action=="delay"`, `reason_code=="too_frequent"`.
  - **Test 3 (High dismissal rate → downgrade from full):** `evaluate_guardian_action(capacity_pct=80, interventions_today=1, dismissal_rate=0.7, hours_since_last=2, current_intensity="full")` → `action=="downgrade"`, `intensity=="light"`, `reason_code=="high_dismissal_rate"`.
  - **Test 4 (Low capacity → downgrade to micro):** `evaluate_guardian_action(capacity_pct=20, interventions_today=1, dismissal_rate=0.0, hours_since_last=2)` → `action=="downgrade"`, `intensity=="micro"`, `reason_code=="low_capacity"`.
  - **Test 5 (Allow path):** `evaluate_guardian_action(capacity_pct=80, interventions_today=1, dismissal_rate=0.0, hours_since_last=2)` → `action=="allow"`.
  - **Test 6 (Budget exhaustion → should_recurate=False):** `evaluate_growth_decision(gap_res, interventions_today=5)` → `should_recurate==False`.
  - **Test 7 (Dismissal downgrade in growth decision):** `evaluate_growth_decision(gap_res, dismissal_rate=0.7, capacity_pct=80)` → `curation_intensity=="light"`.
  - **Test 8 (Completion event lowers Gap):** Aarav seed baseline Gap > Gap after injecting `mission_completed` event.
- **Done when:** `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 38 tests green.

---

### 5.6 Demo / merge-gate verification

**Step 7 — M5 Merge Gate Verification (AIA contribution)**

- Gate 3: `capacity_pct` change does not require LLM — verified by `evaluate_guardian_action` having zero LLM calls (pure dataclass logic).
- Gate 4: Completing alternate micro-mission lowers Gap on seeded persona — verified by Test 8.
- Gate 1 & 2 (Backend + AIS gates): AIA provides structured `GuardianDecision` that AIS Guardian node and Backend can read without parsing freeform strings.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M5)
- `interventions_today`, `hours_since_last_intervention`, and `dismissal_rate` — Backend M5 stores and exposes these on the user/budget context. **AIA functions accept these as plain parameters; no Backend API call is made inside AIA logic.**
- Lens-weight persistence — Backend M5 stores. AIA reads `lensWeightAdjustment` from `LedgerEntry` (schema already exists).

### What AIS needs from AIA (M5)
- `GuardianDecision` → AIS Guardian node consumes `action`, `reason_code`, `plain_language_reason`, and `intensity` to decide delivery mode.
- `DecisionPacket.should_recurate = False` when budget exhausted → AIS Coordinator skips curation cycle.

### Suggested sequencing within AIA M5

```
Sync main → cut aia → cut m5 feature branch from aia
  → Step 1 (Constants) → Step 2 (guardian_decision.py)
  → Step 3 (growth_decision extension) → Step 4 (verify completion wiring)
  → Step 5 (__init__ exports) → Step 6 (Tests) → Step 7 (Gate verify)
```

### Merge gate checklist (M5)
- [ ] Third dismissal flips Failed + Unlearning in <250ms (Backend + AIS gate)
- [ ] Subsequent refresh avoids rejected primary lens (AIS gate)
- [x] **Variants share hypothesis ID; capacity change does not require LLM** ← AIA Gate (GuardianDecision is deterministic)
- [ ] **Completing alternate micro-mission lowers Gap on seeded persona** ← AIA Gate (Test 8)

**Merge order (M5):** Backend (ledger + variants storage) → AIS (guardian + reflection rules) → **AIA (decision budget integration)**.
*Note from milestones.md:* AIS may merge before AIA since DecisionPacket extension points are already available from M4.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| `interventions_today` / `dismissal_rate` unavailable at call time | Both parameters default to `0` / `0.0` — safe passthrough; AIS or Backend passes real values when available. |
| Circular imports (`guardian_decision.py` → `constants.py` → same package) | `guardian_decision.py` imports only from `constants` (not from `packet` or `gap`); no circular dependency risk. |
| Completion-evidence recompute path broken by M4 refactor | Test 8 explicitly verifies the end-to-end Gap drop; if it fails, `recompute.py` wiring is the fix point. |
| `plain_language_reason` strings hardcoded — copy might need adjustment | These are static Python string constants, trivially editable without logic changes. LLM phrasing is explicitly deferred to M6+. |

---

## 8. Open Questions

1. **Branch cut:** Cut `m5` from `aia` (now synced with `main`)?
   - Recommendation: **Yes** — `git checkout aia && git checkout -b m5`.

2. **Priority tie-breaking:** If both `daily_cap_reached` (cap 5) AND `low_capacity` (pct < 34) apply simultaneously, which takes priority? The plan uses cap-reached first (cancel > downgrade) — does this match the intended UX?
   - Recommendation: **Cancel takes priority** — if budget is exhausted there is nothing to downgrade to.

3. **`hours_since_last_intervention` source:** This value is computed by Backend from the ledger (last delivery timestamp). Should AIA treat it as a passed-in `float` parameter (hours as a float), or as a `datetime` and compute the delta internally?
   - Recommendation: **Passed-in `float` (hours)** — simpler, keeps AIA independent of datetime arithmetic outside `recompute.py`.

4. **Completion-evidence wiring:** A quick check shows `wiring.py` already calls `recompute_user_gap` on evidence events. Is an explicit integration test sufficient to satisfy Gate 4, or do you want an explicit endpoint test too?
   - Recommendation: **Unit test sufficient** — Backend endpoint test is a Backend M5 concern.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–4)
- [ ] Approve this plan
- [ ] Agent cuts `m5` from `aia`
- [ ] Implement Steps 1–7 in order
- [ ] Run `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 38 tests green
- [ ] Show `git status` + diff summary + proposed commit message → wait for human approval → commit
- [ ] Done report
