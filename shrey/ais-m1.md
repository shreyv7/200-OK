# Implementation Plan — AIS — M1

## 1. Context
- **Role:** AIS (AI Systems / Curation)
- **Milestone:** M1 — Evidence Pipeline + Twin Shell ("Events in → twin/gap out")
- **PRD features touched:** F2 (P0) evidence pipeline — AIS consumes the `evidence.created` signal only; foundations for F5 (curation), F7 (Reflection/Ledger outcome windows). No user-facing curation ships this milestone.
- **Techstack modules touched:**
  - `services/api/app/agents/graphs/coordinator.py` — Coordinator graph accepts a `DecisionPacket` placeholder in state (AIS owns)
  - `services/api/app/agents/nodes/coordinator/node.py` — upgrade no-op → accepts DecisionPacket, sets fixture invalidation flag
  - `services/api/app/agents/nodes/reflection/node.py` — evidence-ID intake for later outcome windows
  - `services/api/app/services/recommendation/` — `evidence.created` subscriber seam + stack_assembler contract migration
  - `services/api/app/agents/_contracts.py` — **remove/replace** TEMP mirror → import from `app.schemas` (Backend-owned)
  - `services/api/tests/` — AIS M1 hook + intake + contract-source tests
- **Goal:** Wire AIS into the M1 evidence loop as a safe, no-op-but-real consumer: on `evidence.created`, the Coordinator runs and accepts a `DecisionPacket` placeholder (fixture `invalidate` flag only, zero ranking), the Reflection/Ledger layer can record evidence IDs against a hypothesis for future outcome windows, and all AIS code migrates off the M0 TEMP contract mirror onto the frozen Backend `app.schemas`.

---

## 2. Scope (in) — 1:1 with AIS M1 checkboxes in `milestones.md`
- [ ] **Subscribe/hook pattern:** on `evidence.created`, the Coordinator may no-op but **must accept a `DecisionPacket` placeholder**. Implement an in-process subscriber seam (`on_evidence_created`) that constructs a placeholder `DecisionPacket` and invokes the Coordinator graph.
- [ ] **No resource ranking yet — fixture "stack invalidation flag" only.** `stack_assembler` stays fixture-valid; the only live behavior is propagating the DecisionPacket `invalidate` flag into the stack draft. No retrieval, no LLM, no re-rank.
- [ ] **Reflection/Ledger evidence-ID intake:** Reflection/Ledger modules can receive and store evidence IDs associated with a hypothesis so later milestones (M5) can close outcome windows. In-memory/structured intake only — no verdict logic, no DB writes.
- [ ] **(Team-prompt requirement) Contract migration:** replace the M0 `app/agents/_contracts.py` TEMP mirror with imports from Backend-owned `app.schemas` (documented seam #1 in `integration-notes.md`), reconciling snake_case ↔ camelCase and shape differences.
- All items are infra P0 (unblock M2 decision consumer + M4 curation).

---

## 3. Scope (out)
- **Backend M1** (owns): `POST/GET /api/v1/evidence`, idempotent ingest + dedupe, `evidence.created` **emission**, MCP fixture adapter, simulator inject endpoint, 21-day Aarav seed, user+capacity row. AIS **consumes** the emitted signal; it does not build ingest, persistence, or HTTP routes.
- **AIA M1** (owns): evidence enrichment (`identityAttributeIds`/`a_ik`), Revealed Self aggregate builder, twin read model, dead-letter rejection. AIS does not compute aggregates or Gap.
- **Deferred to later AIS milestones:** real Decision Engine consumption + gap-delta invalidation logic (M2), Coordinator diagnose→retrieve→assemble path, Knowledge/Planner real nodes (M4), Guardian gate + variants + Reflection failure/unlearning rules + real Ledger APIs (M5), catalog ranking (M6).
- **Hard rule:** no vendor SDK imports outside `providers/`; the simulator/evidence path must never carry a pre-scored Gap.

---

## 4. Current repo state
- **M0 is merged on `main`/`dev`.** AIS shell exists and is green:
  - `agents/graphs/coordinator.py` — compiled LangGraph shell, linear `coordinator → knowledge → opportunity → planner → reflection → coach → END`, all **no-op** nodes returning `{"visited": [name]}`. `CoordinatorState` already has a `decision_packet: dict` slot and `stack_draft`.
  - `agents/nodes/*` — all no-op pass-throughs.
  - `services/recommendation/stack_assembler.py` — fixture-valid `assemble_stack(...)`, **imports from `app.agents._contracts`** (the mirror), never returns an empty stack.
  - `agents/_contracts.py` — TEMP mirror (`# TEMP MIRROR — replace with app.schemas on Backend M0 merge`).
- **Backend `app.schemas` is frozen and importable** (`from app.schemas import DecisionPacket, IdentityStack, LedgerEntry, ...`).
- **⚠️ Contract shape divergence (the key M1 seam):**
  | Concept | M0 mirror (`_contracts.py`) | Backend `app.schemas` |
  |---|---|---|
  | `DecisionPacket` | `run_id, user_id, gap_score, gap_delta, invalidate_stack, bottleneck, trigger, metadata` | `userId, gapDelta, invalidateStack, invalidatedElementIds, bottleneck, rankingFeatures` (no `run_id`/`trigger`/`gap_score`) |
  | `IdentityStack` | `stack_id, hypothesis_id, curated_at, elements, invalidate, simulated` | `id, userId, hypothesisId, bottleneck, elements, curatedAt, validUntil` (no `invalidate`/`simulated`) |
  | `StackElement` | flat `why_this/why_now/how_reduces_gap` | nested `explanation: StackExplanation{whyThis,whyNow,howReducesGap}` |
  | `SourceBadge` | enum `live_web/cached_web/curated_fallback/simulated` | Literal `"Live web"/"Cached web"/"Curated fallback"` |
  | `ElementType`/`ResourceType` | enum `experience` | Literal `real_world_experience` (+ others) |
  Backend schema **has no `run_id`/`trigger`** that the AIS Coordinator run needs, and **no `invalidate`/`simulated`** flags on the stack. This must be resolved (see Open Questions Q1–Q2): AIS will keep run-scoped fields (`run_id`, `trigger`) in an **AIS-internal `CoordinatorRunContext`** separate from the persisted `DecisionPacket`, and adopt the Backend DTO for anything that crosses the role boundary.
- **`evidence.created` transport does not exist yet** (Backend M1 not landed). Per `guidelines.md §12`, AIS codes against a labeled local stub mirroring the contract and merges after Backend M1 is on `dev`.
- Tests currently green: `test_graph_shell.py`, `test_stack_assembler.py`, `test_explanation_contract.py`, `test_schema_imports.py`, `test_no_vendor_leak.py`.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas
**Step 1 — Retire the TEMP mirror; adopt `app.schemas`.**
- **What:** Delete/empty `app/agents/_contracts.py` (or reduce it to AIS-only working types that do **not** duplicate Backend DTOs). Repoint `stack_assembler.py` and any node imports to `from app.schemas import IdentityStack, StackElement, StackExplanation, DecisionPacket, LedgerEntry`.
- **Why:** `integration-notes.md` seam #1 + team prompt: "Migrate off `app/agents/_contracts.py` TEMP mirror → `app/schemas`." Merge-gate hygiene (single source of truth for contracts).
- **How:** Adopt camelCase Backend fields; convert the assembler's flat explanation fields into nested `StackExplanation`; map badges to Backend Literals (`"Curated fallback"`); map `experience` → `real_world_experience`. Retain a marker constant `CONTRACT_SOURCE = "app.schemas"` for the contract-source test.
- **Done when:** `grep` shows no imports from `app.agents._contracts` anywhere; `from app.agents._contracts import ...` no longer used by AIS code; existing `test_stack_assembler.py` / `test_explanation_contract.py` updated and green against `app.schemas`.

**Step 2 — AIS-internal `CoordinatorRunContext`.**
- **What:** New `app/agents/graphs/run_context.py` (AIS-owned) holding run-scoped, non-persisted fields the graph needs but the Backend `DecisionPacket` lacks: `run_id: str`, `trigger: str` (`"evidence.created" | "manual"`), optional `gap_score`.
- **Why:** Backend `DecisionPacket` intentionally omits `run_id`/`trigger`. Keeping them AIS-internal avoids proposing Backend schema churn mid-milestone while preserving idempotent-by-`run_id` graph runs (techstack §2.4).
- **How:** Small `pydantic`/`dataclass` model; carried in `CoordinatorState` alongside the placeholder `DecisionPacket`.
- **Done when:** Coordinator run is uniquely keyed by `run_id`; unit test constructs a run context + placeholder packet together.

### 5.2 Core logic
**Step 3 — `evidence.created` subscriber seam.**
- **What:** `app/services/recommendation/evidence_hook.py` exposing `on_evidence_created(event: EvidenceEvent) -> CoordinatorState` (name TBD per Q3). It builds a **placeholder** `DecisionPacket` (`gapDelta=0.0`, `invalidateStack=False` unless a fixture flag is set, `bottleneck=None`, `rankingFeatures={}`) + a `CoordinatorRunContext(trigger="evidence.created")`, then invokes `build_coordinator_graph()`.
- **Why:** M1 checkbox — "on `evidence.created`, Coordinator may no-op but must accept DecisionPacket placeholder."
- **How:** In-process synchronous callback (matches techstack "local event bus" for sub-second paths). Registration seam (`register_evidence_subscriber(callback)`) so Backend M1 can wire the real emitter without AIS importing Backend internals. No LLM, no search, no DB, no pre-scored gap.
- **Done when:** Calling `on_evidence_created(sample_event)` runs the graph and returns state whose `visited` includes `"coordinator"` and whose `decision_packet` is a valid `DecisionPacket`.

**Step 4 — Coordinator node accepts the DecisionPacket + fixture invalidation flag.**
- **What:** Upgrade `coordinator_node` from pure no-op: read `decision_packet` from state, echo it forward, and set `stack_draft.invalidate` from a **fixture** flag (env/const `AIS_M1_FIXTURE_INVALIDATE`, default `False`). Still no ranking/assembly of real resources.
- **Why:** M1 checkbox — "fixture 'stack invalidation flag' only." Keeps the graph honest about the invalidation seam without doing curation work.
- **How:** Node returns `{"visited": ["coordinator"], "decision_packet": packet, "stack_draft": {"invalidate": bool}}`. Other nodes remain no-ops.
- **Done when:** Graph run with a placeholder packet yields `stack_draft["invalidate"]` reflecting the fixture flag; no resource ranking occurs.

**Step 5 — Reflection/Ledger evidence-ID intake.**
- **What:** `app/services/recommendation/ledger_intake.py` (AIS-owned, in-memory for M1) with `record_evidence_ids(hypothesis_id, evidence_ids) -> None` and `get_pending_window(hypothesis_id) -> list[str]`, plus wiring so `reflection_node` can call it. No verdict logic, no unlearning, no DB.
- **Why:** M1 checkbox — "ensure Reflection/Ledger modules can receive evidence IDs for later outcome windows." Sets up M5's outcome-window closure.
- **How:** Structured store keyed by `hypothesis_id`, values = evidence IDs + timestamp. `LedgerEntry` (from `app.schemas`) used as the shape when/if surfaced; M1 stores intake only.
- **Done when:** `reflection_node` (or the intake module) accepts evidence IDs and they are retrievable by hypothesis; unit test round-trips IDs.

### 5.3 Integration / wiring
**Step 6 — Register subscriber + expose seam to Backend.**
- **What:** Provide `register_evidence_subscriber()` and a default registration that Backend M1's evidence service can call after persistence + `evidence.created`. Document the seam in `integration-notes.md`-style docstring (no doc file edit unless asked).
- **Why:** Decouples AIS from Backend's emitter implementation (in-process fn vs Redis vs Celery — see Q2).
- **How:** Module-level registry list; `emit_evidence_created(event)` fans out to registered callbacks. If Backend M1 hasn't landed, a labeled stub `# STUB emitter — replace with Backend evidence.created wiring on M1 merge` drives tests.
- **Done when:** A stub emit call triggers the AIS subscriber; swapping to Backend's real emitter requires no AIS logic change.

### 5.4 Seeds / fixtures
- No seed data owned by AIS (Aarav 21-day history is Backend M1). AIS adds test fixtures only: a sample `EvidenceEvent` and a placeholder `DecisionPacket` in `tests/fixtures/sample_data.py` (extend existing file).

### 5.5 Tests
**Step 7 — AIS M1 test suite** (`services/api/tests/`):
- `test_evidence_hook.py`: `on_evidence_created(sample_event)` runs the graph; returned state has a valid `DecisionPacket` and `visited` includes `coordinator`; **no gap fields are computed by AIS** (assert `gapDelta == 0.0` placeholder, not derived).
- `test_stack_invalidation_flag.py`: fixture flag `True` → `stack_draft["invalidate"] is True`; default → `False`; assembler still returns ≥1 action + ≥1 resource with explanations (no ranking).
- `test_ledger_intake.py`: evidence IDs recorded against a hypothesis are retrievable; empty window returns `[]`.
- `test_contract_source.py`: assert AIS imports resolve to `app.schemas` (marker `CONTRACT_SOURCE == "app.schemas"`), **not** the retired mirror.
- Keep/extend `test_no_vendor_leak.py`: no `google.generativeai` / `tavily` imports in `agents/` or `services/` outside `providers/`.
- **Done when:** `cd services/api && pytest -q` is fully green.

### 5.6 Demo / merge-gate verification
**Step 8 — Verify AIS-relevant M1 Merge Gates:**
1. Gate 1 (seed ≥ N events, simulated where appropriate) — **Backend-owned**; AIS confirms its hook accepts seeded/simulated events unchanged. ✓ N/A to AIS logic.
2. Gate 2 (live `POST /evidence` visible in GET within SLA) — Backend-owned; AIS confirms subscriber latency is Tier-0 (no LLM/search/DB on the hook path). ✓ AIS contributes non-blocking.
3. Gate 3 (simulator uses same adapters — **no pre-scored Gap fields inserted**) — AIS asserts its hook never writes/derives Gap. ✓ AIS owns this assertion in `test_evidence_hook.py`.
4. Gate 4 (AIA aggregate tests pass) — AIA-owned. ✓ N/A.
- **Done when:** `pytest -q` green + `grep` gate for vendor leaks clean + no `_contracts` imports remain.

---

## 6. Dependencies & sequencing

### What AIS needs from other roles
| Need | From | Status | Stub strategy (per `guidelines.md §12`) |
|---|---|---|---|
| `evidence.created` emission + `EvidenceEvent` payload | Backend M1 | Not landed yet | AIS defines `register_evidence_subscriber`/`emit_evidence_created` seam + labeled STUB emitter; swap to Backend's real emit on merge. |
| Frozen `app.schemas` DTOs | Backend M0 | ✅ Available | Import directly; migrate off mirror (Step 1). |
| Revealed Self aggregates / Gap inputs | AIA M1/M2 | Not needed for no-op | Coordinator placeholder ignores aggregates until M2 decision consumer. |

### Suggested sequencing within AIS M1
```
Step 1 (retire mirror) → Step 2 (run context) → Step 3 (hook) → Step 4 (coordinator flag)
  → Step 5 (ledger intake) → Step 6 (register seam) → Step 7 (tests) → Step 8 (gate check)
```

### Merge gate checklist (M1) — copied from `milestones.md`
- [ ] Seed load produces ≥ N events, simulated where appropriate (Backend; AIS hook tolerant)
- [ ] Live `POST /evidence` in GET within SLA (Backend; AIS non-blocking on hook path)
- [ ] Simulator inject uses same adapters — no pre-scored Gap (AIS asserts in hook test)
- [ ] AIA aggregate tests pass on seeded Aarav fixture (AIA)

**Merge order:** Backend → AIA → **AIS** (AIS merges after Backend + AIA M1 land on `dev`).

---

## 7. Risks
| Risk | Mitigation |
|---|---|
| **DecisionPacket shape mismatch** (mirror has `run_id`/`trigger`/`gap_score`; Backend DTO doesn't) blocks migration | Keep run-scoped fields in AIS-internal `CoordinatorRunContext`; use Backend `DecisionPacket` only across role boundaries. Raise as Q1 before coding. |
| **`evidence.created` transport undecided** → rework if Backend picks Redis/Celery | Build behind `register_evidence_subscriber` seam; in-process default matches techstack local event bus; swap without AIS logic change. Q2. |
| **Stack invalidation flag drifts into real ranking** (scope creep) | Guard with fixture flag + test asserting no retrieval/LLM calls; ranking is explicitly M2/M4. |
| **Pre-scored Gap leaks via hook** | `test_evidence_hook.py` asserts `gapDelta` is placeholder `0.0`, never derived; Gate 3 assertion. |
| **Ledger intake over-builds toward M5** | In-memory intake only, no verdict/unlearning/DB; `LedgerEntry` shape reused but not persisted. |
| **Migration breaks green M0 tests** | Update `test_stack_assembler.py`/`test_explanation_contract.py` in the same change; run full `pytest -q`. |

---

## 8. Open Questions (block execution)
1. **DecisionPacket run-scoped fields.** Backend's `app.schemas.DecisionPacket` has no `run_id`/`trigger`/`gap_score` that the M0 mirror + Coordinator relied on. Keep these in an **AIS-internal `CoordinatorRunContext`** (my plan), or propose Backend add `runId`/`trigger` to the shared DTO via PR?
   - Recommendation: **AIS-internal `CoordinatorRunContext`** for M1 (no Backend schema churn); revisit a shared field only if M2 needs it persisted.
2. **`evidence.created` transport.** In-process synchronous callback (my default), Redis pub/sub, or Celery task?
   - Recommendation: **in-process callback seam** for the MVP sub-second path (techstack §2.1/§4.6 local event bus); Celery reserved for Tier-2 later.
3. **Subscriber ownership/location + name.** Should the hook live in `app/services/recommendation/evidence_hook.py` with entry `on_evidence_created(event)` (my plan), or does Backend prefer AIS to expose a graph-run function it calls directly (e.g. `run_coordinator_for_event`)?
   - Recommendation: **`on_evidence_created(event)` + `register_evidence_subscriber`** so Backend wires without importing graph internals.
4. **Ledger intake persistence in M1.** In-memory structured intake now, Backend adds the ledger table/APIs in M5 (my plan) — or does Backend want AIS to write `LedgerEntry` rows via a repository already in M1?
   - Recommendation: **in-memory intake only** in M1; DB + APIs in M5 per `milestones.md`.
5. **Badge/type literal alignment.** Adopt Backend Literals (`"Curated fallback"`, `real_world_experience`) across the assembler and drop the mirror enums (my plan), or keep an AIS enum + adapter layer?
   - Recommendation: **adopt Backend Literals directly**; delete mirror enums to avoid dual sources.
6. **Branch/sync.** Cut `ais-m1` from `ais` synced with `dev`. If Backend M1 isn't on `dev` yet, proceed against the labeled STUB emitter and merge after Backend+AIA — confirm this is acceptable vs waiting.
   - Recommendation: **proceed with stub now, merge after Backend+AIA M1** (per §12 + team prompt).

---

## 9. Execution checklist (after you approve)
- [ ] Answer open questions 1–6
- [ ] Approve this plan
- [ ] Agent syncs & checks out `ais` → creates `ais-m1` (from `ais`, merged with `dev`)
- [ ] Implement Steps 1–8 in order
- [ ] Run `cd services/api && pytest -q` — all green; run vendor-leak grep gate; confirm no `app.agents._contracts` imports remain
- [ ] Show `git status` + diff summary + proposed commit message → wait for approval → commit
- [ ] Done report; ready for human merge `ais-m1` → `ais` → `dev` after Backend + AIA M1
