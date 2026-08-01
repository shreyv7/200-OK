# Implementation Plan — Backend — M3

## 1. Context
- Role: **backend**
- Milestone: **M3 — Mirror Interview (Identity Agent)**
- PRD features touched: F1 (Conversational Onboarding, P0)
- Techstack modules touched: API Layer (`/identity/onboarding`, `/identity` PATCH), AI Infrastructure Layer (real `LLMProvider` DI: Gemini primary, Bedrock stub), Data Layer (transcript persistence, twin draft/confirm lifecycle)
- Goal: A working chat-turn endpoint that accumulates an onboarding transcript, runs real structured extraction against Gemini using AIA's existing prompt template, lets the user edit the draft, and on confirm writes an immutable Twin v1 — enforcing `∑ w_i = 1`.

## 2. Scope (in)
Per `milestones.md` M3 → Backend checkboxes only:
- [ ] `POST /api/v1/identity/onboarding` — start/continue interview turn
- [ ] Persist transcript turns; on confirm, write Twin v1 (immutable versions)
- [ ] `PATCH /api/v1/identity` — user edits attributes/weights before confirm
- [ ] Enforce ∑ weights = 1 on confirm
- [ ] LLMProvider DI wired (Gemini primary, Bedrock failover stub)

All P0 (F1 is P0).

## 3. Scope (out) — explicitly not touched
- **AIA M3:** the actual "4–6 question policy" (deciding *which* follow-up question to ask next based on prior answers), schema-validation repair passes on malformed extraction, the consent/confirm copy. This is genuinely AIA's Identity Agent node (`app/agents/nodes/identity/`, currently an empty placeholder) — not mine to build. See Open Question 1 for how Backend's endpoint avoids doing AIA's job while still being end-to-end functional today.
- **AIS M3:** Coordinator scheduling first DecisionPacket / warm-cache job on confirm; not blocking onboarding on retrieval failures.
- No key-rotation infrastructure (techstack.md §11.2's multi-key rotation facade is explicitly deferred to later hardening — M3 needs one working Gemini key, not a pool).
- Not fixing AIA's/AIS's other pending contract seams beyond what actually blocks this milestone (see §4 for what I *am* closing and why).

## 4. Current repo state (verified against `origin/dev` @ `3f8f384`)
- **AIS pushed M2 work directly to `dev`** (not through the `<role>-m2` → `<role>` → `dev` gate the rest of us are using) that defines a new `GapSnapshot` dataclass (`app/services/recommendation/gap_snapshot.py`) and updated `evidence_hook.emit_evidence_created(event, gap_snapshot=None)` — their docstring literally says *"Backend wires `emit_evidence_created` after persistence and passes an optional GapSnapshot from post-recompute KPIs."* My `backend-m2` work (still unmerged) deliberately left this hook uncalled, reasoning it wasn't mine to trigger blind. That reasoning no longer fully holds now that AIS has built the real consumer side and is explicitly waiting on Backend. **I'm treating closing this as a small prerequisite fix-forward, not proper M3 scope** — see §5.0.
- **Provider duplication is now load-bearing, not just noted.** `app/providers/llm.py` (my unused M0 flat module) and `app/providers/llm/` (AIS's package: `base.py`, `fake.py`) coexist. I grepped every real import in the repo — `stack_assembler.py` and its tests exclusively import the **package** form (`app.providers.llm.base`, `app.providers.llm.fake`); nothing imports my flat module. Same situation for `search.py` vs `search/`. M3 requires a real Gemini-backed `LLMProvider` implementation — I can no longer defer this collision, since adding real code forces a choice. **Resolving in favor of the package form** (already the de facto standard) — deleting my dead flat files. See Open Question 2.
- **AIA's extraction prompt already exists** at `app/prompts/identity/declared_self_extraction_v1.md` (status: skeleton, `target_schema: DeclaredSelf`, with `{interview_transcript}`/`{output_schema_json}` placeholders) plus a working `load_prompt(name)` loader in `app/prompts/loader.py`. My onboarding endpoint should load and use this real template for the actual extraction call — not invent a parallel one.
- **No AIA `aia-m3` or AIS `ais-m3` branch exists yet** — unlike M1/M2, I have no pushed reference implementation to build against. My endpoint is the first thing here; AIA's Identity Agent node will eventually replace the placeholder piece I scope in §5.2.
- Existing from M2: `twin_repository.get_active_declared_self` (filters `confirmed_at IS NOT NULL`) and `create_version` — both directly reusable; a draft (unconfirmed) twin is just a `TwinVersion` row with `confirmed_at IS NULL`, which the schema already supports without changes.
- `DeclaredSelf`/`IdentityAttribute`/`IdentityMarker` schemas (M0) are the extraction target — unchanged.

## 5. Detailed work plan

### 5.0 Prerequisite fix-forward (small, not a milestone checkbox)
1. **What:** In `app/services/identity/wiring.py`, build a `GapSnapshot` from the `RecomputeResult` my M2 `recompute_and_persist` already returns, and call AIS's `emit_evidence_created(event_schema, gap_snapshot=snapshot)` alongside my existing recompute-and-persist call.
   **Why:** AIS's M2 code (now on `dev`) is explicitly blocked on this; leaving it dangling into M3 means every future evidence event still runs AIS's "degraded placeholder" path even though real Gap numbers are available.
   **How:** convert `RecomputeResult.snapshot`/prior into `GapSnapshot(userId, gapScore, gapDelta, alignment, createConsumeRatio, consistency, momentum, timestamp, priorGapScore)`; need `row_to_schema`-style conversion of the ORM `EvidenceEventModel` row into an `EvidenceEvent` (already have `evidence_repository.to_schema`).
   **Done when:** posting evidence with a confirmed twin present results in AIS's coordinator running with a real (non-placeholder) `DecisionPacket`; existing AIS tests (`test_decision_consumer.py` etc.) are unaffected since I'm only adding a caller, not changing their code.

### 5.1 Contracts / schemas
2. **What:** `app/schemas/onboarding.py` — `OnboardingTurnRequest` (`sessionId: str | None`, `message: str`), `OnboardingTurnResponse` (`sessionId`, `nextQuestion: str | None`, `draft: DeclaredSelf | None`, `done: bool`), `IdentityPatchRequest` (`attributes: list[IdentityAttribute]`).
   **Why:** milestones.md M3 Backend checkboxes 1 & 3 need typed request/response shapes.
   **How:** `draft` is only populated once enough turns have accumulated to attempt extraction (or on explicit "wrap up" trigger); `done=True` signals the client to show the confirm/edit card (prd.md F1 "Did I get you right?").
   **Done when:** schemas round-trip; exported from `app/schemas/__init__.py`.

### 5.2 Core logic
3. **What:** `app/models/onboarding_session.py` (`OnboardingSession`: id, user_id, status [`in_progress`/`completed`], created_at) + `app/models/onboarding_turn.py` (`OnboardingTurn`: id, session_id, role [`user`/`assistant`], content, created_at) + migration `0003_onboarding.py`.
   **Why:** milestones.md M3 Backend checkbox 2 ("Persist transcript turns").
   **How:** simple append-only turn log per session; a session is "completed" once a draft has been confirmed or explicitly abandoned.
   **Done when:** repository round-trip test creates a session, appends turns, reads them back in order.

4. **What:** `app/repositories/onboarding_repository.py` — `create_session`, `append_turn`, `get_session`, `list_turns`.
   **Why:** repository pattern consistency (techstack.md §5.3); Backend owns persistence.
   **Done when:** covered by the test in step 3.

5. **What:** `app/services/identity/onboarding_orchestration.py` (Backend-owned wiring, mirrors M2's `orchestration.py` pattern) — `advance_turn(db, user_id, session_id, message) -> OnboardingTurnResponse`.
   **Why:** the actual endpoint logic: append the user's message, decide the next fixed question (see Open Question 1) or, once the fixed topic list is exhausted, call the real extraction path.
   **How:** fixed question sequence taken **verbatim from prd.md F1**: aspiration → why → current habits → biggest blocker → weekly capacity (5 questions, within the PRD's stated 4–6 range) — this is a literal PRD requirement, not an invented policy, so it's fair for Backend to scaffold as the *default* sequence pending AIA's dynamic replacement. Once all 5 are answered, load `declared_self_extraction_v1` via `load_prompt`, format with the transcript, call `LLMProvider.generate_structured(schema=DeclaredSelf.model_json_schema(), messages=[...])`, validate the result against `DeclaredSelf` (on validation failure: one retry with an error-correction message appended, then fail closed with a clear error — not a silent bad write), and persist as an **unconfirmed** `TwinVersion` draft (`confirmed_at=None`).
   **Done when:** a fixed test transcript (5 canned answers) produces a valid unconfirmed `DeclaredSelf` draft via a **fake** `LLMProvider` in tests (real Gemini only exercised in a manual/optional integration check, not CI — see §5.5).

6. **What:** Extend `app/repositories/twin_repository.py`: `get_draft(db, user_id) -> DeclaredSelf | None` (latest row where `confirmed_at IS NULL`), `update_draft(db, user_id, attributes) -> DeclaredSelf`, `confirm_draft(db, user_id) -> DeclaredSelf` (sets `confirmed_at`, becomes the active version `get_active_declared_self` returns).
   **Why:** milestones.md M3 Backend checkboxes 2–4 (persist on confirm; PATCH before confirm; enforce weight sum).
   **How:** `confirm_draft` is where `∑ w_i == 1.0` (with a small float tolerance, e.g. `abs(sum - 1.0) < 1e-6`) is enforced — reject with a 422 if violated, never silently normalize (silently rescaling would hide a real extraction/edit bug from the user).
   **Done when:** unit tests cover: draft round-trip, PATCH updates attributes without confirming, confirm with weights summing to 1.0 succeeds and becomes active, confirm with weights ≠ 1.0 is rejected.

### 5.3 Integration / wiring
7. **What:** `app/api/onboarding.py` — `POST /api/v1/identity/onboarding` (wraps `advance_turn`), `PATCH /api/v1/identity` (wraps `update_draft` + optional immediate confirm flag), extend `app/api/identity.py`'s existing `GET /identity` — unchanged (still reads the *confirmed* twin only, per its M2 contract).
   **Why:** milestones.md M3 Backend checkboxes 1 & 3.
   **How:** `PATCH /identity` body includes an optional `confirm: bool` field — when true, runs `confirm_draft` after applying edits, in one request (matches prd.md F1's single confirm/edit UX beat, avoids a two-round-trip PATCH-then-POST dance for the common case).
   **Done when:** end-to-end test: 5 onboarding turns → draft appears → PATCH edits one weight → PATCH with `confirm=true` → `GET /identity` reflects Twin v1 → a subsequent `GET /dashboard/summary` (M2) computes Gap against the new confirmed identity.

8. **What:** Resolve the provider duplication: delete `app/providers/llm.py` and `app/providers/search.py` (dead, unused flat modules); add `app/providers/llm/gemini.py` (`GeminiLLMProvider(LLMProvider)` — real `google-generativeai` SDK call, structured-output mode, single API key from config) and `app/providers/llm/bedrock.py` (`BedrockLLMProvider(LLMProvider)` — structurally present, explicitly documented as untested/stub per milestones.md wording "failover stub", raises `NotImplementedError` with a clear message if actually invoked without AWS credentials configured).
   **Why:** milestones.md M3 Backend checkbox 5; the "no vendor SDK outside providers/" hard constraint means this is the *only* place `google.generativeai` may be imported.
   **How:** `app/core/config.py` gains `gemini_api_key: str | None`, `gemini_model: str = "gemini-1.5-flash"` (or current fast-tier model name), `llm_provider: Literal["gemini","bedrock","fake"] = "fake"`. `app/core/di.py` gains `get_llm_provider() -> LLMProvider` selecting the concrete class by `settings.llm_provider` — defaults to `FakeLLMProvider` when no key is configured, so local dev/CI never accidentally needs live Gemini credentials.
   **Done when:** `get_llm_provider()` returns `FakeLLMProvider` with no env config (CI-safe default); returns `GeminiLLMProvider` when `LLM_PROVIDER=gemini` and a key is set; onboarding endpoint uses `Depends(get_llm_provider)`, never imports a concrete provider class directly.

### 5.4 Seeds / fixtures
- No seed changes needed — M2's fixture confirmed twin remains valid as the pre-onboarding baseline; a fresh onboarding run for a *different* (non-seeded) user_id is how this gets demoed live, per prd.md's demo script beat 1 ("Judge states a real aspiration").

### 5.5 Tests
9. **What:** `tests/test_onboarding_flow.py` (fixed-transcript happy path with `FakeLLMProvider`), `tests/test_identity_confirm.py` (weight-sum enforcement, draft vs. active separation), `tests/test_llm_provider_di.py` (DI selects fake/gemini/bedrock correctly by config, no accidental real network calls under default config).
   **Why:** Merge Gate 1–3 (milestones.md M3).
   **How:** override `LLM_PROVIDER` env var per-test via `get_settings` dependency override in FastAPI's `TestClient`, not real Gemini calls in CI (matches risk in §7).
   **Done when:** `cd services/api && AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q` green.

### 5.6 Demo / merge-gate verification
10. **What:** Manual verification against `milestones.md` M3 Merge Gates 1–3.
    **Why:** required before requesting merge `backend-m3` → `backend` → `dev`.
    **How:** (1) run the fixed-transcript flow through confirm, confirm Gap recomputes against seeded evidence afterward (via M2's dashboard endpoint); (2) confirm the LLM call in `onboarding_orchestration.py` only happens through `LLMProvider`, no direct SDK import elsewhere; (3) confirm PATCH/re-run never overwrites an already-active Declared Self — only a draft can be edited, confirm only promotes the current draft.
    **Done when:** all three gates verified and recorded in the Done report.

## 6. Dependencies & sequencing
- No hard dependency on AIA/AIS M3 work to *start* — I'm building the reference contract this time (opposite of M1/M2). AIA's real Identity Agent node will eventually replace the fixed 5-question sequence in `onboarding_orchestration.py` with dynamic follow-ups; when that lands, my endpoint's job shrinks to "call AIA's node" rather than "contain the sequencing logic" — a contained, low-blast-radius swap.
- §5.0's `GapSnapshot` wiring fix touches AIS's already-merged `dev` code path as a caller only (no changes to their files).
- Merge order: **Backend → AIA → AIS → `dev` → `main`** (unchanged).
- Merge Gate checklist (copied from `milestones.md` M3):
  1. End-to-end: chat turns → extract → edit/confirm → Twin v1 → Gap recomputes against seed evidence.
  2. LLM only via provider adapter; structured output schema shared.
  3. Unconfirmed extraction never overwrites active Declared Self.

## 7. Risks
- **Real Gemini calls in CI/tests** — mitigated by defaulting `LLM_PROVIDER=fake` and never letting tests depend on live network access; a real key is only exercised manually before the actual demo (matches techstack.md's own "pre-warm the flow" risk mitigation).
- **Backend's fixed 5-question sequence could be mistaken for "the" question policy** — mitigated by naming it clearly (`FIXED_ONBOARDING_TOPICS`, docstring citing prd.md F1) and treating it as a placeholder AIA's node supersedes, not a finished feature.
- **Provider file deletion (`llm.py`/`search.py`)** — low risk since grep confirmed zero real importers, but I'll re-grep immediately before deleting in execution to catch anything merged since this plan was written.
- **`∑ w_i = 1` floating-point tolerance** — using an epsilon instead of exact equality avoids rejecting valid LLM output due to floating rounding; too loose an epsilon risks accepting a real bug. `1e-6` chosen as tight-but-not-brittle.

## 8. Open Questions
1. **How much of "the interview conversation" should Backend's placeholder cover, given AIA's Identity Agent node doesn't exist yet?** Options: (a) Backend scaffolds only the fixed 5-topic sequence from prd.md F1 verbatim + wires the real extraction call at the end (my plan above), or (b) Backend does the absolute minimum (a single endpoint that takes a full transcript in one shot and extracts, no turn-by-turn state) and waits for AIA to own all conversational state.
   - **Recommendation:** (a) — it's directly sourced from the PRD's own fixed topic list (not invented), gets a real demoable end-to-end flow working now, and the swap-in point for AIA's real policy is narrow and clearly marked.
2. **Provider duplication cleanup — delete my dead `llm.py`/`search.py` now, or just add the new Gemini/Bedrock classes to the package form and leave the flat files as unused dead code for someone else to clean up later?**
   - **Recommendation:** delete now — they're confirmed unused (grepped), and leaving two `LLMProvider` ABCs with the same name in the same package is a real latent bug (whichever one a future import accidentally resolves to), not just cosmetic.
3. **Close the AIS `GapSnapshot`/`emit_evidence_created` wiring gap now (§5.0) as a small prerequisite, or leave it for a separate immediate follow-up commit outside M3?**
   - **Recommendation:** close it now, in the same `backend-m3` branch, clearly called out as a distinct prerequisite commit (not folded silently into the M3 feature commits) — it's small, low-risk (I'm only adding a caller), and unblocks a teammate who's explicitly waiting on it per their own code comments.
4. **Gemini model name / API key source** — should I default to a specific model name now, or leave it required-but-unset until you provide one?
   - **Recommendation:** default `gemini_model` to a fast-tier model name (e.g. `gemini-1.5-flash` or current equivalent) but require `GEMINI_API_KEY` to be explicitly set for `LLM_PROVIDER=gemini` to activate — never bake in a key, and default to `fake` when unset so nothing breaks locally without one.

## 9. Execution checklist (after you approve)
- [ ] Answer open questions
- [ ] Approve this plan
- [ ] Agent syncs `backend` with `dev`, creates/checks out `backend-m3`
- [ ] Implement (including the §5.0 prerequisite fix as its own commit)
- [ ] Run `AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q`
- [ ] Show commit message(s) → wait for approval → commit
- [ ] Push `backend-m3`; confirm CI green
- [ ] Done report
