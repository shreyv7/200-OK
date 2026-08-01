# Implementation Plan — AIA — M3

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M3 — Onboarding Interview Agent ("The Mirror Interview")
- **PRD features touched:** F1 (Conversational Onboarding — "The Mirror Interview", P0)
- **Techstack modules touched:**
  - `services/api/app/agents/nodes/identity/node.py` — Identity Agent node & interview turn manager
  - `services/api/app/services/identity/extractor.py` — structured extraction & schema repair pass module
  - `services/api/app/services/identity/confirmation.py` — confirmation/consent payload builder ("Did I get you right?")
  - `services/api/app/prompts/identity/declared_self_extraction_v1.md` — finalized Gemini structured extraction prompt
  - `services/api/tests/identity/test_m3_interview_agent.py` — unit test suite for M3 logic
- **Goal:** Deliver the AIA Identity Agent for M3: orchestrate 4–6 turn conversational interview policy, extract structured `DeclaredSelf` JSON targets via `LLMProvider.generate_structured()`, validate and repair malformed outputs, assemble the "Did I get you right?" confirmation payload, and output confirmed targets for Gap arithmetic.

---

## 2. Scope (in)

Mapped 1:1 to M3 AIA checkboxes in `milestones.md`:

- **[AIA-1] Identity Agent node & turn policy:** 4–6 question interview policy (aspiration → why → habits → blocker → weekly capacity).
- **[AIA-2] Structured Extraction Prompts:** Prompts for extracting 3–5 identity attributes, 2–4 markers per attribute, weights `w_i` summing to 1.0, and target weekly points `D_i`.
- **[AIA-3] Extraction schema validation & repair pass:** Validate LLM output against Backend `app.schemas.identity` models (`DeclaredSelf`, `IdentityAttribute`, `IdentityMarker`); run auto-repair or normalization pass if weights sum ≠ 1.0 or fields missing.
- **[AIA-4] Consent/confirm payload ("Did I get you right?"):** Assemble confirmation card DTO exposing extracted identity graph for user review/editing.
- **[AIA-5] Post-confirmation Declared Self handoff:** Ensure confirmed `DeclaredSelf` attributes correctly feed Gap math inputs (`w_i`, `D_i`) without unconfirmed extraction ever overwriting active Twin.
- **[AIA-6] Latency target:** Keep structured extraction and turn generation within <20s target.

---

## 3. Scope (out)

Items explicitly **not** done by AIA in M3:

- **Backend:** `POST /api/v1/identity/onboarding`, `PATCH /api/v1/identity`, DB persistence of interview transcript & Twin versions, Clerk auth — all Backend M3 work.
- **AIS:** Post-confirm Coordinator warm cache scheduling hook — all AIS M3 work.
- No direct LLM SDK calls (all LLM calls use `app.providers.llm.LLMProvider` facade).
- UI/UX screens for chat and confirmation card.

---

## 4. Current repo state

- **M0, M1, and M2 completed and merged** on `aia-m2` branch:
  - `services/api/app/schemas/` contains Backend Pydantic models: `DeclaredSelf`, `IdentityAttribute`, `IdentityMarker`.
  - `services/api/app/services/identity/` contains `sanitizer.py`, `enrichment.py`, `aggregates.py`, `twin.py`, `lattice.py`, `kpi.py`, `bottleneck_v0.py`, `recompute.py`.
  - `services/api/app/providers/llm.py` facade is available on `dev`.
  - 19 unit tests passing cleanly (`pytest -q tests/identity/`).
- Greenfield state for M3: Identity Agent turn manager, extraction repair pass, and confirmation payload builder need to be added under `app/agents/nodes/identity/` and `app/services/identity/`.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Interview State & Confirmation Payload DTOs**

- **What:** `services/api/app/services/identity/confirmation.py`
  - `InterviewTurn(dataclass)`: `turnIndex: int`, `speaker: str` (`"agent"` | `"user"`), `text: str`, `timestamp: datetime`
  - `InterviewState(dataclass)`: `userId: str`, `currentTurn: int`, `maxTurns: int` (default 5), `transcript: list[InterviewTurn]`, `isComplete: bool`
  - `ConfirmationPayload(dataclass)`: `userId: str`, `declaredSelf: DeclaredSelf`, `summaryNarrative: str`, `attributeBreakdown: list[dict]`, `weightSumValid: bool`, `promptMessage: str` ("Did I get you right?")
- **Why:** Milestone checkboxes AIA-1 and AIA-4; structures interview state and confirmation card payload.
- **How:** Pure Python dataclasses consuming `app.schemas.identity.DeclaredSelf`.
- **Done when:** `ConfirmationPayload` and `InterviewState` DTOs are importable and validated.

---

### 5.2 Core logic

**Step 2 — Extraction Schema Validation & Auto-Repair Pass**

- **What:** `services/api/app/services/identity/extractor.py`
  - `validate_and_repair_extraction(raw_extracted_dict: dict, user_id: str) -> tuple[bool, Optional[DeclaredSelf], Optional[str]]`
    - Validates presence of attributes, labels, markers.
    - Normalizes attribute weights if `sum(w_i) != 1.0` by re-scaling `w_i_normalized = w_i / sum(w_i)` rounded to 2 decimals, ensuring exact 1.0 sum.
    - Ensures default `targetWeeklyPoints` (e.g. 15.0) if unstated.
    - Returns `(True, DeclaredSelf_instance, None)` or `(False, None, error_msg)` if irreparable.
- **Why:** Milestone checkbox AIA-3; PRD requirement for structured output schema validation and repair pass.
- **How:** Pure validation and repair function operating on Pydantic `DeclaredSelf`.
- **Done when:** `validate_and_repair_extraction` successfully repairs non-normalized weights and constructs valid `DeclaredSelf`.

---

**Step 3 — Identity Agent Node & Turn Manager**

- **What:** `services/api/app/agents/nodes/identity/node.py`
  - `IdentityAgentNode`:
    - `generate_next_interview_question(state: InterviewState, llm_provider: LLMProvider) -> str`
      - Follows 4–6 turn policy: Turn 1 (aspiration) → Turn 2 (why / core motivation) → Turn 3 (current habits) → Turn 4 (biggest blocker) → Turn 5 (capacity & targets).
    - `extract_declared_self(state: InterviewState, llm_provider: LLMProvider) -> tuple[bool, Optional[DeclaredSelf], Optional[ConfirmationPayload]]`
      - Formats full interview transcript.
      - Invokes `llm_provider.generate_structured(schema=DeclaredSelf, prompt=...)`.
      - Runs `validate_and_repair_extraction`.
      - Builds `ConfirmationPayload` ("Did I get you right?").
- **Why:** Milestone checkboxes AIA-1, AIA-2, and AIA-4; core Identity Agent reasoning node.
- **How:** Consumes `app.providers.llm.LLMProvider` facade; no vendor SDK imports outside `providers/`.
- **Done when:** `IdentityAgentNode` manages turns and extracts confirmed `DeclaredSelf` targets.

---

**Step 4 — Confirmation Payload Builder**

- **What:** `build_confirmation_payload(user_id: str, declared_self: DeclaredSelf) -> ConfirmationPayload` in `confirmation.py`
  - Generates 2-sentence summary narrative of extracted identity.
  - Builds attribute breakdown showing label, target weekly points `D_i`, weight `w_i` %, and markers.
  - Sets `promptMessage = "Did I get you right? Review your identity targets below before confirming."`
- **Why:** Milestone checkbox AIA-4; consent/confirm moment ("Did I get you right?").
- **How:** Pure Python helper.
- **Done when:** `build_confirmation_payload` creates ready-to-render confirmation payload.

---

### 5.3 Integration / wiring

**Step 5 — Service Package Exports**

- **What:** Update `services/api/app/services/identity/__init__.py` to export `InterviewTurn`, `InterviewState`, `ConfirmationPayload`, `validate_and_repair_extraction`, `build_confirmation_payload`, and `IdentityAgentNode`.
- **Why:** Exposes Identity Agent tools for Backend routers and AIS hooks.
- **Done when:** Clean imports from `app.services.identity`.

---

### 5.4 Seeds / fixtures

**Step 6 — Sample Onboarding Transcript Fixture for AIA Tests**

- **What:** `services/api/tests/fixtures/interview_transcript_seed.py`
  - `get_sample_aarav_transcript() -> InterviewState`
  - 5-turn realistic transcript for Aarav persona (aspires to be public speaker and builder, struggles with shortform video scroll).
- **Why:** Used for offline testing of extraction, repair pass, and confirmation payload without requiring live LLM API calls.
- **Done when:** `get_sample_aarav_transcript()` returns valid `InterviewState`.

---

### 5.5 Tests

**Step 7 — M3 Unit Tests Suite**

- **What:** `services/api/tests/identity/test_m3_interview_agent.py`
  - **Test 1 (Turn Policy):** Verifies 4–6 turn policy question sequence (aspiration → why → habits → blocker → capacity).
  - **Test 2 (Weight Auto-Repair):** Verifies `validate_and_repair_extraction` normalizes `[0.6, 0.6]` weights to `[0.5, 0.5]` so `sum(w_i) == 1.0`.
  - **Test 3 (Confirmation Payload):** Verifies `build_confirmation_payload` produces non-empty narrative and correct weight percentage format.
  - **Test 4 (Unconfirmed Safety):** Asserts unconfirmed `DeclaredSelf` extraction flags `confirmed = False` so active Twin is never overwritten prematurely (Merge Gate 3).
  - **Test 5 (LLM Provider Structured Extraction with Fake Provider):** Runs extraction test using `FakeLLMProvider` facade.
- **Why:** Validates all M3 AIA checkboxes and Merge Gates 1–3.
- **How:** Executable via `cd services/api && pytest -q tests/identity/`.
- **Done when:** `pytest -q tests/identity/` passes 100% green.

---

### 5.6 Demo / merge-gate verification

**Step 8 — Merge Gate Verification**

- **What:** Verify M3 AIA Merge Gates:
  - Gate 1: End-to-end extraction → repair → confirmation payload → Twin v1 inputs.
  - Gate 2: LLM invoked only via `app.providers.llm.LLMProvider` facade.
  - Gate 3: Unconfirmed extraction never sets `confirmed = True` prematurely.
- **Done when:** `pytest -q tests/identity/` exits 0 with zero errors.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M3)
- `LLMProvider` facade in `app.providers.llm` — **already present on `dev`**.
- Backend will build REST endpoint `POST /api/v1/identity/onboarding` calling AIA's `IdentityAgentNode`.

### Suggested sequencing within AIA M3
```
Branch setup (checkout aia-m3 from aia synced with dev)
  → Step 1 (DTOs) → Step 2 (Extraction Repair) → Step 4 (Confirmation Payload)
  → Step 3 (Identity Agent Node) → Step 5 (__init__ exports) → Step 6 (Transcript Fixture)
  → Step 7 (Unit Tests) → Step 8 (Merge Gate Verification)
```

### Merge gate checklist (M3)
- [ ] End-to-end: chat turns → extract → edit/confirm → Twin v1 → Gap recomputes (AIA verified)
- [ ] LLM only via provider adapter (`app.providers.llm.LLMProvider`) (AIA verified)
- [ ] Unconfirmed extraction never overwrites active Declared Self (AIA verified)

**Merge order:** Backend (endpoints + provider) → AIA (agent) → AIS (post-confirm hook).

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| LLM returns unparseable JSON or missing attribute fields | The auto-repair pass (`validate_and_repair_extraction`) provides deterministic fallbacks for missing fields before schema validation fails. |
| Attribute weights extracted from LLM sum to 0.95 or 1.05 due to rounding | The auto-repair pass explicitly re-scales `w_i = w_i / sum(w_i)` so weight sum is guaranteed to be 1.0. |
| LLM latency exceeds 20s target | Use fast Gemini model via `LLMProvider` and restrict prompt tokens to essential transcript context. |

---

## 8. Open Questions

1. **Branch Name:** Should we create feature branch `aia-m3` cut from `aia` (synced with `dev`)?
   - Recommendation: **Yes** — sync `aia` with `dev`, then `git checkout -b aia-m3` from `aia`.

2. **Default Max Turns:** Should the conversational onboarding interview turn policy cap at **5 turns**?
   - Recommendation: **5 turns max** (Turn 1: aspiration, Turn 2: why, Turn 3: current habits, Turn 4: blocker, Turn 5: target points & capacity).

3. **Weight Auto-Repair Tolerance:** What threshold should trigger auto-repair vs error rejection when `sum(w_i) != 1.0`?
   - Recommendation: **Auto-repair any non-zero weights** by normalizing `w_i / sum(w_i)` automatically, ensuring 100% valid outputs without unnecessary user error screens.

4. **Default Target Weekly Points `D_i`:** If LLM extraction omits `targetWeeklyPoints` for an attribute, what default should be assigned?
   - Recommendation: **`15.0` evidence points/week** (matching `DEFAULT_DECLARED_TARGET` in `constants.py`).

5. **LLM Provider facade:** Confirm that all M3 agent LLM calls must use `app.providers.llm.LLMProvider` facade without importing `google.generativeai` directly.
   - Recommendation: **Yes** — strictly enforced by Merge Gate 2 and `test_no_vendor_leak.py`.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–5 above)
- [ ] Approve this plan
- [ ] Agent syncs `aia` with `dev` and creates `aia-m3` feature branch
- [ ] Implement Steps 1–8 in order
- [ ] Run `cd services/api && pytest -q tests/identity/` — all green
- [ ] Show `git status` + diff + proposed commit message → wait for human approval → commit
- [ ] Done report
