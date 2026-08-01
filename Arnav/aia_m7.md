# Implementation Plan — AIA — M7

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M7 — Weekly Report + Identity Evolution
- **PRD features touched:** F8 P1 (Weekly Becoming Report), F11 P1 (Identity Evolution Review — confirmation required)
- **Techstack modules touched:**
  - `services/api/app/services/identity/weekly_report.py` — **[NEW]** `generate_weekly_report()` LLM-driven identity movement narrative
  - `services/api/app/services/identity/evolution_agent.py` — **[NEW]** `propose_identity_evolution()` LLM-driven evolution proposal with cited evidence
  - `services/api/app/prompts/identity/weekly_report_v1.md` — **[NEW]** Structured prompt for the weekly report narrative
  - `services/api/app/prompts/identity/evolution_proposal_v1.md` — **[UPDATE]** Fill in the skeleton prompt with full M7 logic
  - `services/api/app/schemas/report.py` — **[NEW]** `WeeklyReport` Pydantic schema
  - `services/api/app/schemas/evolution.py` — **[NEW]** `IdentityEvolutionProposal` Pydantic schema
  - `services/api/app/services/identity/__init__.py` — Export new symbols
  - `services/api/tests/identity/test_m7_report_and_evolution.py` — **[NEW]** M7 unit test suite
- **Goal:** Provide two on-demand LLM-driven agents that consume the evidence window and Declared Self — the Weekly Report generates an identity movement narrative (not time-tracking), and the Evolution Agent proposes confirmable add/remove/reweight updates to the Declared Self. Neither agent auto-applies changes; both produce structured output for user confirmation via Backend API.

---

## 2. Scope (in)

Mapped 1:1 to M7 AIA checkboxes in `milestones.md`:

- **[AIA-M7-1] Weekly Report generation:** `generate_weekly_report(user_id, declared_self, events, gap_result, llm_provider) -> WeeklyReport`
  - Narrative focuses on **identity movement**, not hours: e.g. *"Fearful → attended 2 events → initiated 5 conversations → Confidence marker +9"*.
  - Structured `WeeklyReport` schema: `user_id`, `gap_score_start`, `gap_score_end`, `gap_delta`, `narrative: str`, `highlights: list[str]`, `generated_at`.
  - LLM prompt constructs evidence summary string (event types + attribute improvements) and returns narrative.
  - v0 fallback: if `llm_provider` is `None`, return a deterministic templated narrative from `gap_result` and `kpi_snapshot`.

- **[AIA-M7-2] Identity Evolution Agent:** `propose_identity_evolution(user_id, declared_self, events, gap_result, llm_provider) -> IdentityEvolutionProposal | None`
  - Compares evidence trends against current `DeclaredSelf` attributes.
  - LLM must cite ≥ 3 supporting evidence events for any proposed change.
  - Returns `IdentityEvolutionProposal` schema: `proposal_id`, `user_id`, `declared_self_version`, `proposed_changes: list[ProposedChange]`, `supporting_evidence_ids: list[str]`, `narrative: str`, `generated_at`.
  - `ProposedChange` schema: `action: Literal["add","remove","reweight"]`, `attribute_id`, `attribute_label`, `new_weight: float | None`, `reason: str`, `evidence_ids: list[str]`.
  - Returns `None` if LLM reports no significant evolution (or `llm_provider` is `None`).
  - **Never** calls `recompute_user_gap` or mutates `DeclaredSelf` internally — proposal only.

- **[AIA-M7-3] On-demand only:** Both functions are called explicitly by Backend (triggered via `POST /api/v1/agents/runs` type=weekly_report / evolution). No cron, no background schedule, no scheduled loop in AIA code.

- **[AIA-M7-4] Never auto-apply Declared Self changes:** `propose_identity_evolution` returns a proposal that must pass through Backend's `POST /api/v1/identity/evolution/{id}/accept` or reject endpoint before any `DeclaredSelf` mutation occurs. AIA returns the proposal; Backend and the user gate the accept/reject.

---

## 3. Scope (out)

AIA does **not** build for M7:

- **Backend M7:** `POST /api/v1/agents/runs`, `POST /api/v1/identity/evolution/{id}/accept` and reject endpoints, versioned `DeclaredSelf` persistence on accept, DB storage of `WeeklyReport` and `IdentityEvolutionProposal` — all Backend M7.
- **AIS M7:** Coordinator branch for report/evolution runs (routing to AIA agents via the coordinator graph), post-accept curation refresh using new `DeclaredSelf` — all AIS M7.
- Full automated report scheduling (PRD F8 explicitly says "one-click", "on demand from report").
- Any `DeclaredSelf` mutation or versioning — Backend-owned.
- Weekly Report UI rendering / shareable card layout — UI/UX.

---

## 4. Current repo state

- **M0–M6 complete and merged on `main`, `dev`, `aia`** (synced to `3745cf4`).
- **Already exists (from earlier milestones):**
  - `DeclaredSelf`, `IdentityAttribute`, `IdentityMarker` schemas in `app/schemas/identity.py` ✓
  - `GapResult`, `KPISnapshot`, `EvidenceEvent` fully wired ✓
  - `recompute_user_gap` producing `gap_result` and `kpi_snapshot` ✓
  - `LLMProvider` facade in `app/providers/` (used by `bottleneck_v1.py`) ✓
  - `evolution_proposal_v1.md` prompt stub in `app/prompts/identity/` — **skeleton only** (needs full M7 prompt body) ✓
  - `Aarav` demo seed events including `mission_completed`, `attended_experience`, `github_commit` ✓
- **Greenfield for M7:**
  - `weekly_report.py` — does not exist
  - `evolution_agent.py` — does not exist
  - `app/schemas/report.py` — does not exist
  - `app/schemas/evolution.py` — does not exist
  - `weekly_report_v1.md` prompt — does not exist
  - `evolution_proposal_v1.md` prompt body — skeleton only, needs full content
  - `test_m7_report_and_evolution.py` — does not exist

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — `app/schemas/report.py`: WeeklyReport schema**

- **What:**
  ```python
  class WeeklyReport(BaseModel):
      userId: str
      gapScoreStart: int | None
      gapScoreEnd: int
      gapDelta: int
      narrative: str
      highlights: list[str]  # 2-4 short bullet points
      generatedAt: datetime
      simulated: bool = True  # honesty label (PRD §9 constraint)
  ```
- **Why:** M7 AIA-1; structured output for Backend to persist and return via the `weekly_report` agent run endpoint.
- **Done when:** `from app.schemas.report import WeeklyReport` resolves cleanly.

---

**Step 2 — `app/schemas/evolution.py`: IdentityEvolutionProposal schema**

- **What:**
  ```python
  ProposedChangeAction = Literal["add", "remove", "reweight"]

  class ProposedChange(BaseModel):
      action: ProposedChangeAction
      attributeId: str
      attributeLabel: str
      newWeight: float | None = None
      reason: str
      evidenceIds: list[str]

  class IdentityEvolutionProposal(BaseModel):
      proposalId: str
      userId: str
      declaredSelfVersion: int
      proposedChanges: list[ProposedChange]
      supportingEvidenceIds: list[str]
      narrative: str
      generatedAt: datetime
  ```
- **Why:** M7 AIA-2; PRD F11: "must cite supporting evidence"; never auto-applied (proposal only).
- **Done when:** `from app.schemas.evolution import IdentityEvolutionProposal` resolves cleanly.

---

### 5.2 Core logic

**Step 3 — Fill `evolution_proposal_v1.md` prompt**

- **What:** `services/api/app/prompts/identity/evolution_proposal_v1.md`
  - Replace skeleton body with full structured prompt:
    - System role: "Trellis Identity Evolution Agent — evaluate evidence trends vs. Declared Self"
    - Input context: `declared_self` (attribute list with current weights), `recent_evidence_summary` (last 21 days aggregated by type and attribute), `gap_score_now`, `gap_delta`
    - Output format: JSON matching `IdentityEvolutionProposal` schema — `proposedChanges` array (each with `action`, `attributeId`, `attributeLabel`, `newWeight`, `reason`, `evidenceIds`), `narrative`, `supportingEvidenceIds`
    - Constraint block: cite ≥ 3 evidence IDs per change; return `{"proposedChanges": []}` if no evolution detected; never propose to remove all attributes; never auto-accept
- **Why:** M7 AIA-2; prompt was skeleton from M0 — now fully specified.
- **Done when:** Prompt renders valid JSON on a fake fixture call.

---

**Step 4 — `weekly_report_v1.md` prompt**

- **What:** `services/api/app/prompts/identity/weekly_report_v1.md`
  - System role: "Trellis Weekly Becoming Report — narrative writer"
  - Input: `evidence_summary` (events grouped by type + attribute + score delta), `gap_score_start`, `gap_score_end`, `bottleneck_label`, `top_attribute_progress`
  - Output format: JSON with `narrative` (2–4 sentences, identity movement framing) and `highlights` (2–4 bullets, "Fearful → attended 2 events…" style)
  - Constraint: no time-tracking language ("hours", "minutes spent"); focus on identity state change
- **Why:** M7 AIA-1; PRD F8: "identity movement, not hours".
- **Done when:** Prompt template renders complete JSON on a fixture call.

---

**Step 5 — `weekly_report.py`: Weekly Report generation**

- **What:** `services/api/app/services/identity/weekly_report.py`
  - `build_evidence_summary(events: List[EvidenceEvent], gap_result: GapResult) -> str` — deterministic serialization of the evidence window for the prompt (AIA-owned, no LLM)
  - `generate_weekly_report(user_id, declared_self, events, gap_result, prior_gap_score, llm_provider) -> WeeklyReport`:
    1. Call `build_evidence_summary` to assemble the prompt input string.
    2. If `llm_provider` is available: call `llm_provider.generate(prompt)` with `weekly_report_v1.md` template, validate JSON response against `WeeklyReport` fields.
    3. If `llm_provider` is `None` (v0 fallback): construct a deterministic narrative from gap delta and top attribute progress.
    4. Return fully populated `WeeklyReport`.
  - **Gap Firewall:** `generate_weekly_report` only reads `gap_result.gap_score` and `per_attribute`; never modifies or recomputes it.
- **Why:** M7 AIA-1; PRD F8 acceptance: "generates in <10s from live DB state".
- **Done when:** `generate_weekly_report(…, llm_provider=None)` returns a valid `WeeklyReport` with non-empty `narrative` and `highlights`.

---

**Step 6 — `evolution_agent.py`: Identity Evolution Agent**

- **What:** `services/api/app/services/identity/evolution_agent.py`
  - `build_evolution_context(declared_self, events, gap_result) -> str` — deterministic serialization of context for the evolution prompt (attribute list, evidence by attribute, gap delta)
  - `propose_identity_evolution(user_id, declared_self, events, gap_result, llm_provider) -> IdentityEvolutionProposal | None`:
    1. If `llm_provider` is `None`: return `None` (no evolution proposal without LLM).
    2. Call `llm_provider.generate(prompt)` with `evolution_proposal_v1.md` template.
    3. Validate JSON response — if `proposedChanges` is empty: return `None`.
    4. Validate each `ProposedChange.evidenceIds` has ≥ 3 entries; on failure: strip the change (not the whole proposal).
    5. Return `IdentityEvolutionProposal` with `proposalId = uuid4()`, `declaredSelfVersion = declared_self.version`.
  - **Hard constraint:** No mutation of `declared_self`, no call to `recompute_user_gap`.
- **Why:** M7 AIA-2; PRD F11: "must cite supporting evidence", "never auto-applied".
- **Done when:** `propose_identity_evolution(…, llm_provider=None)` returns `None`; `propose_identity_evolution(…, llm_provider=fake_provider)` returns an `IdentityEvolutionProposal` or `None` with no exception.

---

### 5.3 Integration / wiring

**Step 7 — Update `services/identity/__init__.py` Exports**

- Export `WeeklyReport` (from `app.schemas.report`), `generate_weekly_report`, `IdentityEvolutionProposal`, `ProposedChange`, `propose_identity_evolution`.
- **Done when:** All symbols resolve from `app.services.identity`.

---

### 5.4 Seeds / fixtures

No new seed fixtures required for M7 AIA. Aarav seed provides sufficient evidence events for weekly report and evolution proposal tests. PRD F11 mentions "one seeded evolution proposal generated from the demo history; no autonomous background schedule" — the **demo seed** is a Backend M7 concern (two prior dismissals, etc.); AIA just generates the proposal on demand.

---

### 5.5 Tests

**Step 8 — M7 Unit Test Suite**

- **What:** `services/api/tests/identity/test_m7_report_and_evolution.py`
  - **Test 1 (Weekly Report v0 — no LLM):** `generate_weekly_report(…, llm_provider=None)` returns `WeeklyReport` with non-empty `narrative`, non-empty `highlights`, and correct `gapScoreEnd` matching `gap_result.gap_score`.
  - **Test 2 (Weekly Report with fake LLM):** `generate_weekly_report(…, llm_provider=FakeLLMProvider)` returns `WeeklyReport` with `narrative` and `highlights` from the mocked LLM response.
  - **Test 3 (Evolution Agent — no LLM returns None):** `propose_identity_evolution(…, llm_provider=None)` returns `None` without error.
  - **Test 4 (Evolution Agent — fake LLM with valid proposal):** `propose_identity_evolution(…, llm_provider=FakeLLMProvider)` returns `IdentityEvolutionProposal` with at least one `ProposedChange` with ≥ 3 `evidenceIds`.
  - **Test 5 (Evolution Agent — evidence citation check):** A `ProposedChange` with < 3 `evidenceIds` in the fake LLM response is stripped from `proposedChanges`, not the whole proposal.
  - **Test 6 (Evolution proposal — no mutation):** `declared_self.version` and `declared_self.attributes` are unchanged after `propose_identity_evolution` call.
  - **Test 7 (WeeklyReport simulated flag):** `WeeklyReport.simulated == True` (PRD honesty label constraint).
- **Done when:** `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 52 tests green.

---

### 5.6 Demo / merge-gate verification

**Step 9 — M7 Merge Gate Verification (AIA contribution)**

- Gate 1: Report generates in < 10s from live DB state — verified by test (v0 fallback is instant; v1 with fake provider is instant).
- Gate 2: Accept → Twin vN; Reject → no mutation — **AIA Gate:** `propose_identity_evolution` never mutates `DeclaredSelf`; verified by Test 6.
- Gate 3: Post-accept curation refresh uses new Declared Self — **AIS gate** only; AIA provides the `IdentityEvolutionProposal` that Backend accepts, then AIS re-curates.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M7)
- `POST /api/v1/agents/runs` type=weekly_report / evolution — Backend M7. **AIA functions accept plain Python objects; no HTTP call is made inside AIA agents.**
- Versioned `DeclaredSelf` persistence on accept — Backend M7. AIA reads `declared_self.version` from the passed-in object.

### What AIS needs from AIA (M7)
- `generate_weekly_report` and `propose_identity_evolution` — callable by AIS Coordinator's report/evolution branch.

### Suggested sequencing within AIA M7
```
Sync main → cut aia → cut m7 feature branch from aia
  → Step 1 (schemas: WeeklyReport, IdentityEvolutionProposal)
  → Step 2 (fill evolution_proposal_v1.md prompt)
  → Step 3 (weekly_report_v1.md prompt)
  → Step 4 (weekly_report.py module)
  → Step 5 (evolution_agent.py module)
  → Step 6 (__init__ exports)
  → Step 7 (Tests)
  → Step 8 (Gate verify)
```

**Merge order (M7):** Backend (endpoints + versioning) → **AIA (report + evolution agents)** → AIS (coordinator branch + post-accept re-curation).

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| LLM response non-JSON / schema mismatch | `validate_and_repair_extraction` already exists (from M3); reuse it or replicate the same pattern for report and evolution responses. |
| Evolution proposal cites invalid `evidenceIds` (hallucination) | Strip changes with < 3 valid evidence IDs (Step 6, Test 5); never fail the whole response. |
| Weekly Report takes > 10s with live LLM | PRD acceptance is "< 10s from live DB state"; v0 fallback is instant; use fixture provider in tests; real latency is an LLM infra concern. |
| `evolution_proposal_v1.md` skeleton prompt causes LLM to produce wrong schema | Prompt update in Step 3 includes explicit JSON output format and field list. |
| Backend M7 not merged before AIA M7 runs | AIA functions are pure Python; they don't depend on Backend endpoints — safe to develop in parallel. |

---

## 8. Open Questions

1. **LLM provider call interface:** Does `llm_provider.generate(prompt)` return a plain `str` (matching the existing `bottleneck_v1.py` pattern), or is there a different method signature?
   - Recommendation: **Use same `llm_provider.complete(prompt)` or `.generate(prompt)` pattern as `bottleneck_v1.py`** — inspect that file and mirror exactly.

2. **`validate_and_repair_extraction` reuse:** Can `weekly_report.py` and `evolution_agent.py` import `validate_and_repair_extraction` from `app.services.identity.extractor` to clean LLM JSON output, or should each have its own inline parser?
   - Recommendation: **Reuse `validate_and_repair_extraction`** — it already exists in the package.

3. **`WeeklyReport` and `IdentityEvolutionProposal` schema location:** Should both live in `app/schemas/` (Backend-adjacent) or inside `app/services/identity/` as AIA-local dataclasses?
   - Recommendation: **`app/schemas/`** — Backend M7 will read and persist these; they must be importable by the Backend API layer without importing AIA service logic.

4. **v0 weekly report fallback wording:** For the no-LLM fallback, should the narrative be a simple template string (e.g. *"This week your Identity Gap moved from {prior} to {now}. Top active attribute: {attr}."*) or entirely empty?
   - Recommendation: **Simple template string** — empty narrative would break the UI card rendering.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–4)
- [ ] Approve this plan
- [ ] Agent cuts `m7` from `aia`
- [ ] Implement Steps 1–9 in order
- [ ] Run `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 52 tests green
- [ ] Show `git status` + diff summary + proposed commit message → wait for human approval → commit
- [ ] Done report
