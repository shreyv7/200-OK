# Implementation Plan — AIS — M0

## 1. Context
- **Role:** AIS (AI Systems / Curation)
- **Milestone:** M0 — Scaffold & Frozen Contracts
- **PRD features touched:** Infra only (foundations for F5 curation, F6 Guardian, F7 Reflection/Ledger). No user-facing feature ships.
- **Techstack modules touched:**
  - `services/api/app/agents/graphs/` (Coordinator graph shell — AIS owns)
  - `services/api/app/agents/nodes/{knowledge,opportunity,planner,reflection,coach,coordinator}/` (registered stubs)
  - `services/api/app/services/recommendation/` (Identity Stack assembly signature)
  - `services/api/app/providers/{llm,search}/` (interface stubs consuming Backend facades)
  - `services/api/app/prompts/` (`curator_*`, `reflect_*` skeletons)
  - `services/api/tests/` (AIS fixture-based contract tests)
- **Goal:** Stand up the AIS-owned agentic shell — an empty-but-wired LangGraph Coordinator, provider interface stubs, an Identity Stack assembly signature with a mandatory explanation contract, and prompt skeletons — so curation logic can be filled in M4+ without touching other roles' modules, and so the schema package imports cleanly in AIS tests (Merge Gate 2) with zero vendor SDK leaks (Merge Gate 3).

## 2. Scope (in) — 1:1 with AIS M0 checkboxes
- [ ] **LangGraph empty graph stub:** Coordinator graph with all AIS nodes registered (no-op), checkpointer config wired (Postgres/Redis/in-memory selectable).
- [ ] **`SearchProvider` / `LLMProvider` interface stubs** consuming Backend provider facades (`search()`, `generate_structured()` signatures per techstack §11.1) — no vendor SDKs.
- [ ] **Identity Stack assembly function signature** + explanation-field contract tests (fixture-based): every stack element must carry `why_this` / `why_now` / `how_reduces_gap`.
- [ ] **Prompt folder skeleton:** `curator_*` and `reflect_*` template placeholders with a small versioned-prompt loader convention.
- All of M0 is infra P0 (needed for parallel build).

## 3. Scope (out)
- **Backend M0** (owns): FastAPI app, `/healthz` `/readyz`, Pydantic schema package, Alembic/Postgres, Clerk stub, folder scaffold root, seed entrypoint, GitHub Actions. AIS **consumes** these, does not create them.
- **AIA M0** (owns): `services/decision/`, `services/identity/scoring/`, Gap formula constants, Declared Self extraction TypedDict, formula unit tests.
- Any real curation logic, retrieval, ranking, LLM calls, Guardian rules, Reflection thresholds — deferred to **M4/M5**. M0 nodes are no-op pass-throughs.
- P2 (`coach/` beyond a registered stub) — deferred.

## 4. Current repo state
- Greenfield: only `docs/` + `README.md`; branch `main` only (no `dev`, `aia`, `ais`, `backend`); no `services/` tree.
- **Assumption to confirm (see Open Questions):** Backend M0 (schema package + `providers/` facades + folder scaffold) does **not** yet exist. Per `guidelines.md` §12, AIS may code against local stubs mirroring `milestones.md`/`techstack.md` contracts and call this out — which this plan does. Merge order remains Backend → AIA → AIS.

## 5. Detailed work plan

### 5.1 Contracts / schemas
1. **Local contract mirrors (temporary, clearly labeled).**
   - **What:** In `services/api/app/agents/_contracts.py` (or consume `app/schemas/` if Backend has landed), define thin TypedDict/Pydantic mirrors AIS depends on: `DecisionPacket`, `IdentityStack`, `IdentityStackElement`, `BottleneckPacket`, `LedgerEntry`, `InterventionVariant`.
   - **Why:** Merge Gate 2 requires the schema package to import cleanly in AIS tests; §12 allows stubbing when Backend M0 isn't merged.
   - **How:** If Backend schema package importable → import it directly, no mirror. Otherwise a single module tagged `# TEMP MIRROR — replace with app.schemas on Backend M0 merge`.
   - **Done when:** AIS modules import contract types with no `ImportError`; a marker test asserts the source (real vs mirror).

2. **Identity Stack element explanation contract.**
   - **What:** `IdentityStackElement` requires `why_this: str`, `why_now: str`, `how_reduces_gap: str` (+ `element_type`, `source_badge`, `hypothesis_id`).
   - **Why:** PRD §6 F5 / §8 mandate all three explanation fields per element; source badge honesty (§8 retrieval fallback).
   - **How:** Enum for `element_type` (media, knowledge, growth_story, mentor, tool, experience, micro_mission, reflection) and `source_badge` (`live_web`/`cached_web`/`curated_fallback`/`simulated`).
   - **Done when:** Constructing an element without any explanation field fails validation (asserted in 5.5).

### 5.2 Core logic
3. **Provider interface stubs.**
   - **What:** `providers/llm/base.py` → `LLMProvider.generate_structured(schema, messages, opts) -> dict`; `providers/search/base.py` → `SearchProvider.search(query, opts) -> list[Document]`; plus `FakeLLMProvider` / `FakeSearchProvider` returning fixtures.
   - **Why:** AIS M0 checkbox; §9 constraint 3 (no vendor SDKs outside `providers/`); enables DI test swaps (techstack §5.4).
   - **How:** Pure ABCs/Protocols, zero `google`/`tavily`/`boto3` imports. Consume Backend facade if present; else define interface here to be reconciled on merge.
   - **Done when:** `import`-linting confirms no vendor SDK references; fakes usable in tests.

4. **LangGraph Coordinator shell.**
   - **What:** `agents/graphs/coordinator.py` builds a `StateGraph` over a typed `CoordinatorState` (trigger, twin snapshot, decision_packet, stack_draft, run_id). Registers no-op nodes: `coordinator`, `knowledge`, `opportunity`, `planner`, `reflection`, `coach` (P2 stub). Linear edges diagnose→retrieve→assemble→guard(pass-through)→reflect; checkpointer configurable (in-memory default for tests).
   - **Why:** AIS M0 checkbox; techstack §12/§13.1 Coordinator owns graph; must accept a `DecisionPacket` placeholder (forward-looking M1).
   - **How:** Each node echoes state unchanged with a `visited` marker; graph compiles and runs end-to-end on a fixture input.
   - **Done when:** `graph.invoke(fixture_state)` returns without error and all nodes report visited.

5. **Identity Stack assembly signature.**
   - **What:** `services/recommendation/stack_assembler.py` → `assemble_stack(decision_packet, candidates, capacity_tier, ledger_weights) -> IdentityStack` (NotImplemented / minimal fixture pass-through for M0).
   - **Why:** AIS M0 checkbox; PRD §6 F5 "smallest coherent combination"; guarantees never-empty contract seam for M4.
   - **How:** Signature + docstring stating replacement policy & never-empty guarantee; M0 returns a fixture stack with valid explanations.
   - **Done when:** Callable with fixtures, returns schema-valid `IdentityStack`.

### 5.3 Integration / wiring
6. **Node package + registry.**
   - **What:** `agents/nodes/<name>/node.py` per node + a registry mapping names→callables the graph consumes.
   - **Why:** Matches techstack §24 folder layout (§9 constraint 9); keeps role isolation.
   - **Done when:** Registry import builds the graph without hardcoded node bodies.

7. **DI seams (no framework coupling yet).**
   - **What:** Factory functions returning provider fakes; document how Backend `Depends()` will inject real providers in M3+.
   - **Done when:** Graph/assembler accept injected providers; tests pass fakes.

### 5.4 Seeds / fixtures
8. **AIS test fixtures.**
   - **What:** `tests/fixtures/` — sample `DecisionPacket`, candidate resources, a valid `IdentityStack`, `CoordinatorState`.
   - **Why:** Fixture-based contract tests (AIS M0 checkbox); no DB dependency.
   - **Done when:** Fixtures load standalone.

### 5.5 Tests
9. **Contract + shell tests.**
   - Explanation contract: missing `why_this`/`why_now`/`how_reduces_gap` → validation error.
   - Graph shell: compiles, invokes on fixture, all nodes visited, checkpointer configurable.
   - Provider stubs: fakes satisfy interface; **no-vendor-leak test** greps AIS modules for forbidden imports (`google.generativeai`, `tavily`, `boto3`) → asserts none outside `providers/` (backs Merge Gate 3).
   - Schema import test (Merge Gate 2): contract types import cleanly.
   - **Done when:** `pytest` green for AIS suite.

### 5.6 Demo / merge-gate verification
10. **Local gate check.**
    - Confirm AIS suite imports schema package cleanly (Gate 2); vendor-leak test passes (Gate 3); Gate 1 (API up/health) is Backend-owned — AIS verifies its modules import under the API package once Backend scaffold exists.

## 6. Dependencies & sequencing
- **Need from Backend (real or stubbed):** `services/api/app/` scaffold (techstack §24), Pydantic schema package, `providers/` facades, GitHub Actions running pytest. If unmerged → local mirrors (5.1) + interface stubs (5.2), clearly labeled; reconcile on Backend M0 merge.
- **Need from AIA:** nothing blocking for M0 (only `DecisionPacket`/`BottleneckPacket` *shapes*, mirrored locally).
- **Merge order (milestones.md M0):** Backend → AIA → **AIS** (AIS merges last).
- **M0 Merge Gate checklist (copied):**
  1. `docker compose`/local brings API up; health checks green. *(Backend-owned; AIS ensures its modules don't break import.)*
  2. Schema package imports cleanly in AIA and AIS test suites. *(AIS-owned here.)*
  3. No feature imports Gemini/Tavily SDKs outside `providers/`. *(AIS enforces via test 5.5.)*

## 7. Risks
- **Schema drift** between local mirrors and Backend's real Pydantic → mitigate with single labeled mirror module + a reconciliation test; propose field changes via Open Questions, never edit Backend schemas directly (§9.7).
- **LangGraph version/checkpointer API churn** → pin version; default in-memory checkpointer for tests to avoid DB coupling in M0.
- **Accidental vendor SDK import** → automated no-leak test (5.5).
- **Over-building M0** (drifting into M4 curation logic) → nodes stay no-op; assembler stays signature+fixture only.
- **Folder mismatch** with techstack §24 → follow layout exactly.

## 8. Open Questions (block execution)
1. **Branching baseline.** Repo has only `main` (no `dev`/role branches). Per `guidelines.md` §5, work happens on `ais` → `m0` cut from `dev`.
   - **Recommendation:** With your approval, create `dev` from `main`, then `ais` from `dev`, then feature branch `m0` from `ais`. Confirm, or tell me if `dev`/`ais` will be created by someone else first.
2. **Stub vs wait for Backend M0.** Backend scaffold + schema package + `providers/` facades don't exist yet.
   - **Recommendation:** Proceed now against clearly-labeled local mirrors/interfaces (§12-compliant) and reconcile on Backend M0 merge. Confirm, or say "wait for Backend."
3. **LangGraph checkpointer for M0.** Postgres/Redis both stubbable this milestone (techstack §26).
   - **Recommendation:** In-memory checkpointer for M0 (fast, DB-free tests); wire Postgres/Redis in M1+.
4. **Test scope for the no-vendor-leak gate.** Should the enforcement test scan the whole `services/api/app` tree or only AIS-owned dirs?
   - **Recommendation:** Scan `agents/` + `services/recommendation/` (AIS surface) now; leave repo-wide enforcement to Backend's CI lint.
5. **Local Python env / dependency manager.** No `pyproject.toml`/`requirements.txt` yet.
   - **Recommendation:** If Backend hasn't landed one, I add a minimal AIS-scoped `requirements-dev.txt` (langgraph, pydantic, pytest) under `services/api/`, to be merged into Backend's canonical manifest later. Confirm ownership.

## 9. Execution checklist (after you approve)
- [ ] Answer open questions
- [ ] Approve this plan
- [ ] Agent creates/checks out `ais` → `m0` (per Q1)
- [ ] Implement AIS M0 scope (5.1–5.6)
- [ ] Run AIS pytest + no-leak test
- [ ] Show commit message(s) → wait for approval → commit
- [ ] Done report
