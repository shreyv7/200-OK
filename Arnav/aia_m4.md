# Implementation Plan — AIA — M4

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M4 — Curation Core (Bottleneck + Next Step + Stack)
- **PRD features touched:** F5 P0 (Four-Lens Curator — Missing Action / Bottleneck lens; Continuous Curation Engine)
- **Techstack modules touched:**
  - `services/api/app/services/identity/bottleneck_v1.py` — LLM-driven Bottleneck diagnosis upgrade (replaces heuristic with Gemini structured output)
  - `services/api/app/services/identity/growth_decision.py` — Growth Decision Engine M4: determines if re-curation is warranted and at what intensity
  - `services/api/app/services/decision/packet.py` — Extend `DecisionPacket` with `low_confidence_flag` and `should_recurate` fields
  - `services/api/app/prompts/identity/bottleneck_diagnosis_v1.md` — Finalized Gemini structured extraction prompt
  - `services/api/tests/identity/test_m4_bottleneck.py` — M4 unit test suite
- **Goal:** Upgrade the heuristic bottleneck diagnosis to a Gemini-structured-output driven engine (`bottleneck_v1`), extend the Growth Decision Engine to set `should_recurate` and intensity signals for AIS, and ensure the bottleneck LLM never touches Gap numbers — always via the `LLMProvider` facade.

---

## 2. Scope (in)

Mapped 1:1 to M4 AIA checkboxes in `milestones.md`:

- **[AIA-1] Bottleneck diagnosis via Gemini structured output:** Replace heuristic `bottleneck_v0` with `bottleneck_v1` that calls `LLMProvider.generate_structured()` with `bottleneck_diagnosis_v1.md` prompt over evidence aggregates + taxonomy (PRD §9).
- **[AIA-2] Full BottleneckPacket:** `{ bottleneck, confidence, supporting_evidence[], missing_evidence[], alternative_bottleneck }` — schema already stable in `BottleneckCandidate`.
- **[AIA-3] Low-confidence flag:** If top candidate `confidence < 0.65`, set `low_confidence_flag = True` on `DecisionPacket` to signal AIS "small experiment" mode.
- **[AIA-4] Growth Decision Engine:** Evaluate deficit deltas, Create:Consume ratio, and bottleneck confidence shift to determine `should_recurate: bool` and `curation_intensity: "full" | "light" | "micro"` for AIS Coordinator.
- **[AIA-5] Gap firewall constraint:** The bottleneck LLM output path must never modify or recompute `GapResult`. Gap remains deterministic pure functions only.
- **[AIA-6] Unit tests:** LLM path with `FakeLLMProvider`, low-confidence flag trigger, growth decision curation trigger logic, Gap-firewall constraint.

---

## 3. Scope (out)

AIA does **not** build for M4:

- **Backend:** Resource cache table, `GET /api/v1/stack/active`, `POST /api/v1/stack/refresh`, SearchProvider Tavily adapter, source badges, Celery background job — all Backend M4.
- **AIS:** Coordinator graph Decision → diagnose → retrieve → assemble node pipeline, Knowledge/Planner/Identity Stack assembly, mandatory 3-field explanation per element, replacement policy, fallback catalog guarantee — all AIS M4.
- No direct Gemini SDK calls; all LLM calls via `app.providers.llm` facade.
- UI stack cards and bottleneck chip display — UI/UX.
- Real-World Opportunity (P1), Outside Voice (P2) lenses.

---

## 4. Current repo state

- **M0–M3 complete and merged on `main` and `dev`** (pulled from `main` at session start).
- **Already exists:**
  - `bottleneck_v0.py` — heuristic rule engine (✓ shipped M2)
  - `bottleneck_diagnosis_v1.md` prompt skeleton — skeleton only, `status: skeleton` (M0, needs completion for M4)
  - `app.providers.llm.base.LLMProvider` abstract base with `generate_structured(schema, messages, opts)` interface
  - `app.providers.llm.fake.FakeLLMProvider` — for offline tests without real API
  - `BottleneckCandidate`, `DecisionPacket`, `build_decision_packet` in `packet.py`
  - `GapResult`, `CreateConsumeResult`, `compute_create_consume`, `compute_consistency` in `scoring/gap.py`
  - `recompute_user_gap` orchestrator in `recompute.py`
- **Greenfield for M4:**
  - `bottleneck_v1.py` — LLM-driven diagnosis
  - `growth_decision.py` — re-curation decision engine extension
  - M4 unit test suite
  - Finalized `bottleneck_diagnosis_v1.md` prompt

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Extend `DecisionPacket` with M4 fields**

- **What:** `services/api/app/services/decision/packet.py`
  - Add two fields to `DecisionPacket`:
    - `low_confidence_flag: bool = False` — set when top bottleneck `confidence < LOW_CONFIDENCE_THRESHOLD` (0.65)
    - `should_recurate: bool = False` — set by Growth Decision Engine when a new curation cycle is warranted
    - `curation_intensity: str = "full"` — `"full"` | `"light"` | `"micro"` for AIS Guardian interplay
- **Why:** AIS Coordinator reads these fields to trigger stack refresh at the right intensity (M4 AIS contract).
- **How:** Add fields with defaults to `DecisionPacket` dataclass; update `build_decision_packet` signature to accept these values.
- **Done when:** `DecisionPacket` dataclass has the three new fields and existing tests still pass.

---

### 5.2 Core logic

**Step 2 — Finalize `bottleneck_diagnosis_v1.md` Prompt**

- **What:** `services/api/app/prompts/identity/bottleneck_diagnosis_v1.md`
  - Update status from `skeleton` → `milestone: M4`
  - Finalize system instruction text for Gemini structured output call
  - Include: taxonomy enforcement, evidence aggregate input variables, `confidence` rubric (high/medium/low thresholds), `supporting_evidence_ids` extraction instructions, and required output JSON structure matching `BottleneckCandidate` array
- **Why:** M4 AIA-1; without a finalized prompt there is no LLM-driven diagnosis.
- **Done when:** Prompt can be loaded by `app.prompts.loader` and used as `messages` in `LLMProvider.generate_structured()`.

---

**Step 3 — `bottleneck_v1.py`: LLM-Driven Bottleneck Diagnosis**

- **What:** `services/api/app/services/identity/bottleneck_v1.py`
  - `diagnose_bottleneck_v1(gap_result, create_consume, consistency, events, llm_provider, user_id) -> List[BottleneckCandidate]`
    - Builds attribute deficit JSON summary (no LLM arithmetic — purely from deterministic `GapResult`).
    - Builds evidence aggregate summary (creation count, drift count, passive count, consistency score, C:C ratio).
    - Loads prompt from `bottleneck_diagnosis_v1.md` via `app.prompts.loader`.
    - Calls `llm_provider.generate_structured(schema=..., messages=[...])`.
    - Validates returned list against `BottleneckCandidate` schema; on parse failure, falls back to `diagnose_bottleneck_v0` result with a `confidence=0.50` downgrade.
    - Returns validated `List[BottleneckCandidate]` (max 3 candidates).
- **Why:** M4 AIA-1 and AIA-2; PRD §5 F5 "Pure structured LLM analysis over evidence data."
- **How:** Entirely via `LLMProvider` facade; zero direct Gemini SDK imports.
- **Done when:** `diagnose_bottleneck_v1` with `FakeLLMProvider` returns valid `BottleneckCandidate` list with correct taxonomy labels.

---

**Step 4 — `growth_decision.py`: Growth Decision Engine M4**

- **What:** `services/api/app/services/identity/growth_decision.py`
  - `evaluate_growth_decision(gap_result, prior_gap_score, bottleneck_candidates, create_consume, capacity_pct) -> GrowthDecision(dataclass)`
    - `GrowthDecision(should_recurate, curation_intensity, low_confidence_flag, reason)`
  - **Curation trigger rules (deterministic, no LLM):**
    - `should_recurate = True` if: `abs(gap_delta) >= 5` OR `bottleneck changed from prior` OR `C:C ratio < 0.5` OR `prior_recurated_at > 24h ago`.
    - `should_recurate = False` if Gap delta is < 2 and bottleneck stable.
  - **Intensity rules:**
    - `capacity_pct >= 67` → `"full"`, `34–66` → `"light"`, `< 34` → `"micro"`.
  - **Low confidence flag:**
    - `low_confidence_flag = True` if top `candidate.confidence < 0.65`.
- **Why:** M4 AIA-3 and AIA-4; PRD §8 "Continuous Curation Engine triggers"; AIS Coordinator needs clear `should_recurate` and `intensity` signals.
- **How:** Pure deterministic logic. Capacity tier boundaries reuse PRD §6 F6 constants (`CAPACITY_FULL_MIN = 67`, `CAPACITY_LIGHT_MIN = 34`).
- **Done when:** `evaluate_growth_decision` returns correct `GrowthDecision` for each trigger scenario in unit tests.

---

**Step 5 — Wire `bottleneck_v1` + `growth_decision` into `recompute_user_gap`**

- **What:** `services/api/app/services/identity/recompute.py`
  - Update `recompute_user_gap` signature to accept optional `llm_provider` and `capacity_pct`.
  - If `llm_provider` provided: call `diagnose_bottleneck_v1`; else fall back to `diagnose_bottleneck_v0`.
  - Call `evaluate_growth_decision` and populate `DecisionPacket` with `low_confidence_flag`, `should_recurate`, `curation_intensity`.
- **Why:** M4 AIA-5; Gap firewall — bottleneck LLM never gets to recompute `GapResult`; separation is enforced by function call order.
- **Done when:** `recompute_user_gap` with `llm_provider=FakeLLMProvider()` produces updated `DecisionPacket` with new fields.

---

### 5.3 Integration / wiring

**Step 6 — Update `services/identity/__init__.py` Exports**

- Export `diagnose_bottleneck_v1`, `evaluate_growth_decision`, `GrowthDecision`.
- **Done when:** clean imports from `app.services.identity`.

---

### 5.4 Seeds / fixtures

No new seed fixtures required for M4 AIA. Existing `aarav_seed.py` provides sufficient evidence events for bottleneck diagnosis testing.

---

### 5.5 Tests

**Step 7 — M4 Unit Test Suite**

- **What:** `services/api/tests/identity/test_m4_bottleneck.py`
  - **Test 1 (LLM path):** `diagnose_bottleneck_v1` with `FakeLLMProvider` returns valid `BottleneckCandidate` list with at least one item from taxonomy.
  - **Test 2 (Fallback to v0):** If `FakeLLMProvider` raises exception, `diagnose_bottleneck_v1` gracefully falls back to heuristic `bottleneck_v0` result.
  - **Test 3 (Low-confidence flag):** `evaluate_growth_decision` sets `low_confidence_flag = True` when top candidate `confidence < 0.65`.
  - **Test 4 (Curation trigger):** `evaluate_growth_decision` sets `should_recurate = True` when gap delta ≥ 5.
  - **Test 5 (Gap firewall):** Verify `bottleneck_v1` output never overwrites `gap_result.gap_score` — deterministic Gap remains unchanged after bottleneck call.
  - **Test 6 (Intensity tiers):** Verify `curation_intensity` maps correctly to `capacity_pct` per PRD F6 thresholds.
- **Done when:** `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 30 tests green.

---

### 5.6 Demo / merge-gate verification

**Step 8 — Merge Gate Verification**

- Gate 1: Backend M4 stack/refresh API available in `dev` — AIA `bottleneck_v1` produces `DecisionPacket.should_recurate = True` that AIS Coordinator reads to trigger `POST /api/v1/stack/refresh`.
- Gate 2: Bottleneck visible in `GET /api/v1/dashboard/summary` (Backend wires from `DecisionPacket`, AIA provides packet).
- Gate 3: Retrieval failure still yields seeded stack (Backend fallback) — AIA firewall ensures Gap untouched.
- Gate 4: AIA `should_recurate` and `curation_intensity` fields are consumed by AIS Coordinator without modification.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M4)

- `GET /api/v1/stack/active` and `POST /api/v1/stack/refresh` — Backend M4 work. AIA does **not** call these endpoints; AIA only produces the `DecisionPacket` that AIS Coordinator uses to trigger them.
- `capacity_pct` field availability — Backend persists it; AIA's `evaluate_growth_decision` accepts it as a passed-in parameter.

### What AIS needs from AIA (M4)

- `DecisionPacket.should_recurate`, `DecisionPacket.curation_intensity`, `DecisionPacket.low_confidence_flag` — **these are the M4 AIA→AIS contract fields**.
- `bottleneck_candidates[0].label` and `confidence` — for Curator to diagnose bottleneck lens selection.

### Suggested sequencing within AIA M4

```
Sync main → cut aia → cut m4 feature branch
  → Step 1 (Extend DecisionPacket) → Step 2 (Finalize prompt)
  → Step 3 (bottleneck_v1) → Step 4 (growth_decision)
  → Step 5 (wire into recompute_user_gap)
  → Step 6 (__init__ exports) → Step 7 (Tests) → Step 8 (Gate verify)
```

### Merge gate checklist (M4)

- [ ] Refresh produces stack with ≥1 action + ≥1 resource; explanations present (AIS + Backend gate)
- [ ] At least one demo path shows Live web or Cached web badge (Backend + AIS gate)
- [ ] **Bottleneck visible in dashboard summary** (AIA Gate — `DecisionPacket.bottleneck_candidates` populated with LLM-diagnosed label)
- [ ] Retrieval failure still yields seeded stack; feed morph never blocked (Backend + AIS gate)

**Merge order:** Backend (cache/search/stack API) → **AIA (bottleneck + decision)** → AIS (graph + assembly).

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| LLM returns taxonomy label outside the 10 allowed values | `bottleneck_v1` validates label against `BOTTLENECK_TAXONOMY` list; invalid label → fall back to `bottleneck_v0` result with `confidence=0.50` downgrade. |
| Gemini quota exhaustion during tests | All unit tests use `FakeLLMProvider` — zero real API calls in CI. |
| LLM returns confidence that inflates Gap numbers | Gap firewall enforced in `recompute_user_gap`: `diagnose_bottleneck_v1` never receives or returns `gap_score`. Separate call ordering is the firewall. |
| `capacity_pct` not yet available from Backend | Default to `capacity_pct=100` (`"full"` tier) when not provided — safe fallback. |

---

## 8. Open Questions

1. **Branch strategy:** Should I cut `m4` feature branch from the `aia` role branch (synced with `main`/`dev`)? `main` is now ahead of `aia` — do you want me to first sync `aia` with `main` then cut `m4`?
   - Recommendation: **Yes** — pull `main`, merge into `aia`, then `git checkout -b m4`.

2. **`LLMProvider.generate_structured` signature:** The current base interface uses `(schema: dict, messages: list[dict], opts: dict)`. Should bottleneck prompt messages follow `[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]` Gemini message format?
   - Recommendation: **Yes** — use chat-style messages list matching existing `FakeLLMProvider` behavior.

3. **Low-confidence threshold:** Is `0.65` the right cut-off for `low_confidence_flag`? Below this, AIS enters "small experiment" mode rather than committing a full curation refresh.
   - Recommendation: **`0.65`** — matches PRD's intent of "confident diagnosis before full curation commit."

4. **`recompute_user_gap` backward-compat:** The current signature doesn't include `llm_provider` or `capacity_pct`. Should these be optional keyword-only parameters with `None` defaults (so all existing M0–M3 tests continue to pass without modification)?
   - Recommendation: **Yes** — add `llm_provider=None, capacity_pct=100` as optional kwargs; when `llm_provider=None`, fall back to `bottleneck_v0`.

5. **Bottleneck v0 fate:** Should `bottleneck_v0.py` remain as the deterministic fallback used by `bottleneck_v1` when LLM is unavailable? Or should it be archived?
   - Recommendation: **Keep `bottleneck_v0` as fallback** — it is referenced by existing tests and serves as the offline / LLM-unavailable path.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–5 above)
- [ ] Approve this plan
- [ ] Agent syncs `aia` with `main`, creates `m4` feature branch from `aia`
- [ ] Implement Steps 1–8 in order
- [ ] Run `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` — all green
- [ ] Show `git status` + diff + proposed commit message → wait for human approval → commit
- [ ] Done report
