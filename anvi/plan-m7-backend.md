# Implementation Plan — Backend — M7

## 1. Context
- Role: **backend** | Milestone: **M7 — Weekly Report + Identity Evolution**
- PRD: F8 (Weekly Report, P1), F11 (Identity Evolution Review, P1)
- Goal: an on-demand agent-run endpoint that generates a Weekly Report narrative or an Identity Evolution proposal, plus accept/reject endpoints where only "accept" ever writes a new confirmed Twin version.

## 2. Scope (in) — Backend checkboxes only
- [ ] `POST /api/v1/agents/runs` type=weekly_report / evolution
- [ ] `POST /api/v1/identity/evolution/{id}/accept` and explicit reject/keep
- [ ] Versioned Declared Self on accept only; Gap uses new version after accept
- [ ] Reject leaves data unchanged

## 3. Scope (out)
- AIA: the actual narrative-writing/evolution-reasoning quality (real LLM prompt-engineering refinement) — only the skeleton prompt (`evolution_proposal_v1.md`) exists today, same "Backend builds the calling contract, AIA refines the content" pattern as M3's onboarding.
- AIS: post-accept stack invalidation + re-curation trigger.

## 4. Current repo state (verified against `origin/dev` post-M6)
- No `AgentRun`/evolution models, schemas, or endpoints exist yet — greenfield, same as M3's onboarding was.
- `app/prompts/identity/evolution_proposal_v1.md` (AIA, M0 skeleton) is the target prompt; no equivalent weekly-report prompt file exists yet — I'll add a minimal one under `app/prompts/identity/weekly_report_v1.md` if AIA hasn't, since Backend needs *something* to call (same reasoning as M3: PRD-sourced content, not invented agent policy).
- `twin_repository` already has everything needed for versioning: `get_active_declared_self`, `create_version` — accept just calls `create_version` with the next version number and `confirmed_at=now`; no new repository logic needed there.
- `get_llm_provider` DI (M3) reused as-is for both report and evolution generation calls.

## 5. Detailed work plan

### 5.1 Schemas
1. `app/schemas/agent_run.py`: `AgentRunRequest{type: Literal["weekly_report","evolution"]}`, `WeeklyReport{narrative: str, generatedAt: datetime}`, `IdentityEvolutionProposal{id, userId, proposedAttributes: list[IdentityAttribute], citedEvidenceIds: list[str], rationale: str, status: Literal["pending","accepted","rejected"], createdAt}`, `AgentRunResult{runId, type, weeklyReport: WeeklyReport|None, evolutionProposal: IdentityEvolutionProposal|None}`.

### 5.2–5.3 Models / repositories / endpoints
2. `app/models/agent_run.py` (`AgentRunModel`: id, user_id, type, status, result_json, created_at) + `app/models/identity_evolution.py` (`IdentityEvolutionProposalModel`: id, user_id, proposed_attributes_json, cited_evidence_ids_json, rationale, status, created_at) + migration `0007_agent_runs.py`.
3. `app/repositories/agent_run_repository.py`, `app/repositories/evolution_repository.py` (create, get, mark accepted/rejected).
4. `app/services/identity/agent_runs.py` (Backend wiring, mirrors `onboarding_orchestration.py`):
   - `generate_weekly_report(db, llm_provider, user_id) -> WeeklyReport`: pulls the evidence window + Gap history (reuse `evidence_repository.list_window`, `orchestration.recompute_and_persist`'s last snapshot), formats a simple prompt (identity-movement framing per prd.md F8: "not hours"), calls `llm_provider.generate_structured`.
   - `generate_evolution_proposal(db, llm_provider, user_id) -> IdentityEvolutionProposal`: loads confirmed Declared Self + recent evidence, calls the LLM with `evolution_proposal_v1` prompt, validates against a narrow extraction schema (same pattern as M3's `_ExtractionSchema` — proposed attributes only, not full DeclaredSelf), persists as `pending`.
5. `app/api/agents.py` — `POST /api/v1/agents/runs` (dispatches to one of the two generators above based on `type`, persists an `AgentRunModel` row, returns `AgentRunResult`).
6. `app/api/identity.py` extension — `POST /api/v1/identity/evolution/{id}/accept` (loads proposal, `twin_repository.create_version` with next version + `confirmed_at=now`, marks proposal `accepted`) and `POST /api/v1/identity/evolution/{id}/reject` (marks `rejected`, no other writes — merge gate 2's "no mutation" is literally just "don't call create_version").

### 5.4 Seeds
7. One seeded evolution proposal for the demo user (prd.md F11: "MVP: one seeded evolution proposal") so the accept/reject UI has something to show without waiting on a live LLM call during the demo.

### 5.5 Tests
- `test_agent_runs.py` (weekly report + evolution generation via FakeLLMProvider), `test_evolution_accept_reject.py` (accept creates vN + Gap uses it; reject leaves `get_active_declared_self` unchanged).
- Run: `AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q`.

## 6. Dependencies & sequencing
- Merge order: **Backend → AIA → AIS** (default, per milestones.md M7).
- AIS's post-accept re-curation trigger depends on the accept endpoint existing; not a blocker for Backend's own work.

## 7. Risks
- Report generation must complete in <10s (merge gate 1) — since it's LLM-backed, keep it synchronous (not BackgroundTasks like M4's stack refresh) since the UI needs the narrative in the response, not a poll; `FakeLLMProvider` in tests is instant, real Gemini call timing is a pre-demo check, not a CI concern.
- Evolution proposal's "3 cited evidence events minimum" (prompt rule) is AIA's prompt instruction, not a Backend-enforced constraint — Backend just stores whatever citedEvidenceIds the LLM returns; not validating count server-side unless that becomes a demo problem.

## 8. Open Questions
1. **No weekly-report prompt file exists yet (only evolution's) — write a minimal one now, or inline the prompt in Python?** — **Recommendation:** add `app/prompts/identity/weekly_report_v1.md` (consistent with the existing prompt-file pattern AIA already uses) rather than inlining — keeps the convention AIA's other prompts follow, easy for them to refine later.
2. **Seed one evolution proposal — deterministic fixture content, or a real LLM call at seed time?** — **Recommendation:** deterministic fixture (same philosophy as the rest of `seed.py` — no live network calls in seed data).

## 9. Execution checklist
- [ ] Answer open questions → approve → I sync `backend` from `dev`, branch `backend-m7`, implement, test, show commit, push.
