# Implementation Plan — AIS — M7

## 1. Context
- **Role:** AIS (AI Systems / Curation)
- **Milestone:** M7 — Weekly Report + Identity Evolution
- **PRD features touched:** F8 (Weekly Becoming Report, P1), F11 (Identity Evolution Review, P1 — confirmation required). AIS does **not** author the report narrative or the evolution proposal (AIA owns the reasoning); AIS owns the **Coordinator run branch** for these run types and the **post-accept re-curation** so the stack rebuilds against the new Declared Self.
- **Techstack modules touched:**
  - `services/api/app/agents/graphs/coordinator.py` — conditional branch so `weekly_report` / `evolution` runs route through the coordinator shell without forcing the full curation path.
  - `services/api/app/agents/graphs/run_context.py` — add `evolution.accepted` (+ `report.requested`) trigger types.
  - `services/api/app/agents/nodes/` — report/evolution graph slot (AIS provides routing + a thin pass-through node seam; AIA fills reasoning).
  - `services/api/app/services/recommendation/` — new `evolution_hook.py` (accept → invalidate → re-curate), reusing the M3 `onboarding_hook.py` pattern; `curation_cycle.py` / `stack_state.py` for invalidation + refresh.
  - `services/api/tests/` — coordinator-branch routing, accept-triggers-recuration, reject-no-mutation, new-version-used tests.
- **Goal:** When a Weekly Report / Identity Evolution run is requested, the Coordinator shell routes it correctly (report/evolution nodes owned by AIA), and when the user **accepts** an evolution proposal, AIS invalidates the current stack assumptions and triggers a re-curation job so the next Identity Stack is built against the new (versioned) Declared Self. Rejecting changes nothing.

---

## 2. Scope (in) — 1:1 with AIS M7 checkboxes in `milestones.md`
- [ ] **Coordinator branch for report/evolution runs.** (F8/F11) — coordinator graph accepts `weekly_report` / `evolution` run types and routes them to the report/evolution slot instead of the full diagnose→retrieve→assemble curation path.
- [ ] **After accepted evolution: invalidate stack assumptions; trigger re-curation job.** (F11 acceptance + M7 merge gate 3) — accept event → `invalidateStack=True` → `run_curation_cycle` against the new Declared Self version.

Both AIS M7 items are **P1**. All M4/M5/M6 P0/P1 curation paths must stay green.

---

## 3. Scope (out)
- **Backend M7** (owns): `POST /api/v1/agents/runs` (type=weekly_report / evolution); `POST /api/v1/identity/evolution/{id}/accept` + explicit reject/keep; versioned Declared Self persisted **on accept only**; Gap uses new version after accept; reject leaves data unchanged. AIS adds **no** FastAPI routes / DB models.
- **AIA M7** (owns): Weekly Report narrative generation (identity movement from evidence, not hours); Identity Evolution Agent proposal (add/remove/reweight with cited evidence); on-demand from report (no cron); **never** auto-applies Declared Self changes. AIS provides the graph slot; AIA fills the node reasoning.
- **Deferred / other:** F9 Leverage-Moment (P2, M8), F10 Growth Partner Match (P2, M8), Execution Coach gating (P2, M8). No background scheduler/cron (PRD: evolution runs on demand from the report).
- Hard rules: no Gap arithmetic in AIS; AIS **never** mutates the Declared Self or applies an evolution proposal (confirmation + persistence are Backend/AIA); no vendor SDKs outside `providers/`; a **rejected** proposal must cause zero state change on the AIS side.

---

## 4. Current repo state
- **`origin/main` / `origin/dev`:** `3745cf4` — M6 integrated (catalog lenses, opportunity lens, ledger P1 worked/pending; AIA `catalog_features` on DecisionPacket).
- **Already available for M7 reuse:**
  - **Trigger pattern:** `CoordinatorRunContext` (`run_context.py`) with `TriggerType = Literal["evidence.created", "manual", "onboarding.confirmed"]`; `coordinator_node` already branches on `trigger` (e.g. `trigger == "onboarding.confirmed"` forces invalidate).
  - **Hook pattern:** `onboarding_hook.py` — `on_onboarding_confirmed(event)` builds a DecisionPacket (always `invalidateStack=True`), invokes `build_coordinator_graph()`, and kicks a best-effort warm cache. This is the exact template for `on_evolution_accepted`.
  - **Graph:** `build_coordinator_graph()` (`coordinator.py`) with linear `GRAPH_NODE_ORDER` (coordinator→knowledge→opportunity→planner→assemble→guardian→reflection→coach) via `add_edge`. M7 introduces the first **conditional** routing.
  - **Re-curation:** `run_curation_cycle()` (`curation_cycle.py`) already the public refresh seam; `stack_state.apply_invalidation()` / `set_active_stack()` handle invalidation + active-stack registry.
  - **Node registry:** `registry.py` maps node names → callables; adding a report/evolution slot follows the same pattern.
  - **Identity contract:** `DeclaredSelf.version` (`schemas/identity.py`) already versioned; `OnboardingConfirmEvent.twinVersion` shows the version-carrying event pattern.
- **Missing (other roles / AIS):**
  - AIA report/evolution **node reasoning** (Weekly Report narrative, evolution proposal) — not landed.
  - Backend `agents/runs` + evolution accept/reject endpoints + versioned persist — not landed.
  - AIS `evolution_hook.py`, trigger types, and coordinator conditional branch — not built.
- **Assumption while waiting for Backend/AIA M7:** AIS codes against an AIS-local `EvolutionAcceptedEvent` seam (mirroring `OnboardingConfirmEvent`: `userId`, `twinVersion`/new `declaredSelfVersion`, `acceptedAt`, optional `gapSnapshot`) and a thin report/evolution node slot that AIA fills; re-curation reuses `run_curation_cycle` with `invalidateStack=True` and the post-accept DecisionPacket.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas
**Step 1 — Evolution/report run seams (AIS-consumed).**
- **What:** Add `services/recommendation/evolution_trigger.py` with a frozen `EvolutionAcceptedEvent` dataclass (`userId`, `declaredSelfVersion: int`, `acceptedAt: str`, `gapSnapshot: GapSnapshot | None`, `trigger: Literal["evolution.accepted"]`) — mirroring `OnboardingConfirmEvent`. Extend `run_context.py` `TriggerType` to include `"evolution.accepted"` and `"report.requested"`.
- **Why:** Schema/endpoint ownership is Backend's; AIS needs a stable consume shape (guidelines §12) to build the branch + re-curation before Backend endpoints land.
- **How:** AIS-local dataclass; promote to `app.schemas` only if Backend needs the exact serialized shape (Open Q1). No DB, no routes.
- **Done when:** Unit test constructs an `EvolutionAcceptedEvent` and the new trigger types type-check.

### 5.2 Core logic
**Step 2 — Coordinator branch for report/evolution runs.**
- **What:** Introduce a `run_type` / trigger-keyed conditional in `build_coordinator_graph()` so `report.requested` and `evolution.accepted` (proposal-generation) runs route to a **report/evolution slot** and then `END`, instead of the full curation chain. Default/`evidence.created`/`onboarding.confirmed`/`manual` runs keep today's linear path unchanged.
- **Why:** M7 AIS checkbox "Coordinator branch for report/evolution runs" (F8/F11).
- **How:** Add a `report_evolution` node to `registry.py` as a **thin pass-through seam** (AIS owns routing; AIA fills narrative/proposal reasoning — Open Q4). Use a LangGraph conditional edge from `START`/`coordinator` on `state["trigger"]` (or a `state["run_type"]`). Keep `GRAPH_NODE_ORDER` intact for curation runs.
- **Done when:** Test: a `report.requested` run visits the report/evolution slot and **not** knowledge/opportunity/planner/assemble; a normal `evidence.created`/`stack.refresh` run still visits the full curation path.

**Step 3 — Evolution-accepted hook (invalidate + re-curate).**
- **What:** Add `services/recommendation/evolution_hook.py` with `on_evolution_accepted(event: EvolutionAcceptedEvent)`: build a post-accept `DecisionPacket` with `invalidateStack=True`, apply invalidation to active stack flags, and call `run_curation_cycle(..., trigger="evolution.accepted")` so a fresh stack is produced against the new Declared Self version.
- **Why:** M7 AIS checkbox "after accepted evolution: invalidate stack assumptions; trigger re-curation job" + merge gate 3 (post-accept curation refresh uses new Declared Self).
- **How:** Mirror `on_onboarding_confirmed` structure (run_id `evolve-{userId}-v{version}`, best-effort warm cache reuse). If `event.gapSnapshot` present, reuse `consume_gap_update`; else emit an `invalidateStack=True` packet. Register via an `emit_evolution_accepted` in-process emitter (subscriber list pattern from `onboarding_hook.py`).
- **Done when:** Test: `on_evolution_accepted` returns a stack whose curation ran with `invalidate=True`; active-stack flags show invalidation; re-curation used the packet carrying the new version.

**Step 4 — Reject / keep is a no-op on the AIS side.**
- **What:** Ensure there is **no** AIS state mutation path for a rejected/kept proposal — no trigger, no invalidation, no re-curation. Document that AIS only reacts to `evolution.accepted`.
- **Why:** F11 acceptance ("rejecting leaves all identity data unchanged") + M7 merge gate 2 (Reject → no mutation).
- **How:** Simply do not wire any reject handler; add a guard/test asserting that only the accept event triggers re-curation. Backend/AIA own the reject endpoint.
- **Done when:** Test: firing a "rejected" (or absence of accept) does not change active stack / flags / ledger.

### 5.3 Integration / wiring
**Step 5 — Wire trigger + branch through the cycle.**
- **What:** Thread the new trigger through `coordinator_node` (treat `evolution.accepted` like `onboarding.confirmed` for invalidation intent) and `run_curation_cycle` (accept `trigger="evolution.accepted"`, defaults preserve M6 behavior). Ensure `CoordinatorState` carries any `run_type` field needed for routing (NotRequired, like the M6 additions).
- **Why:** Backend `agents/runs` + evolution accept call into AIS; AIS owns the curation cycle and coordinator shell they invoke.
- **How:** No new routes. Document the `on_evolution_accepted` + report/evolution-branch injection seams in module docstrings (same DI-seam pattern as providers / `catalog_source`).
- **Done when:** `on_evolution_accepted` end-to-end returns a refreshed stack; report run routes to the report slot; all through the existing graph/cycle entry points.

### 5.4 Seeds / fixtures
**Step 6 — AIS M7 fixtures.**
- **What:** `tests/fixtures/sample_data.py`: `sample_evolution_accepted_event()` (with new `declaredSelfVersion` + optional `gapSnapshot`), and a helper for a "report requested" run state.
- **Why:** Keep AIS M7 tests DB-free and offline until Backend endpoints + AIA reasoning land (guidelines §12).
- **How:** Pure fixtures mirroring the event seam from Step 1; no DB, no network.
- **Done when:** Offline pytest exercises branch routing + accept-recuration + reject-no-op without network or DB.

### 5.5 Tests
**Step 7 — AIS M7 tests:**
- `test_coordinator_report_branch.py` — report/evolution run routes to the report slot and skips the curation chain; curation runs still traverse the full path.
- `test_evolution_accept_triggers_recuration.py` — accept → `invalidateStack=True` → fresh stack via `run_curation_cycle`.
- `test_evolution_reject_no_mutation.py` — no accept ⇒ no invalidation, no re-curation, no ledger write.
- `test_evolution_uses_new_declared_self_version.py` — re-curation consumes the packet/version produced post-accept (merge gate 3, AIS-side assertion via version-carrying packet).
- Keep vendor-leak gate + all M4/M5/M6 tests green.
- **Done when:** `cd services/api && pytest -q` green.

### 5.6 Demo / merge-gate verification
**Step 8 — AIS-relevant M7 Merge Gates:**
1. **Report generates in <10s from live DB state** — AIS ensures the report branch is a non-blocking Tier-2 route (no full curation on a report run); narrative latency is AIA/Backend.
2. **Accept → Twin vN; Reject → no mutation** — AIS re-curates only on accept; reject is a verified no-op on the AIS side (persistence/versioning is Backend/AIA).
3. **Post-accept curation refresh uses new Declared Self** — AIS `on_evolution_accepted` invalidates + re-curates against the new-version packet.
- **Done when:** Gates 2 & 3 covered by AIS tests; gate 1 verified once AIA report node + Backend `agents/runs` are wired.

---

## 6. Dependencies & sequencing

### What AIS needs from other roles
| Need | From | Status | Stub strategy |
|---|---|---|---|
| `POST /api/v1/agents/runs` (weekly_report/evolution) | Backend M7 | Not landed | AIS exposes coordinator branch + `on_evolution_accepted` seam; Backend calls it |
| Evolution accept/reject endpoints + versioned persist | Backend M7 | Not landed | AIS reacts to `evolution.accepted` event only; Backend owns persist + reject |
| Weekly Report narrative + evolution proposal reasoning | AIA M7 | Not landed | AIS provides thin report/evolution node slot; AIA fills reasoning |
| Post-accept DecisionPacket using new Declared Self version | AIA/Backend M7 | `DeclaredSelf.version` exists; packet has `catalog_features` | Consume packet as-is; if version not surfaced, read from `EvolutionAcceptedEvent.declaredSelfVersion` (Open Q3) |

### Sequencing within AIS M7
```
Step 1 (event + trigger seams) → Step 2 (coordinator branch) → Step 3 (accept hook: invalidate + re-curate)
  → Step 4 (reject no-op guard) → Step 5 (trigger/branch wiring) → Step 6 (fixtures) → Step 7 (tests) → Step 8 (gates)
```

### Merge gate checklist (M7) — from `milestones.md`
- [ ] Report generates in <10s from live DB state
- [ ] Accept → Twin vN; Reject → no mutation
- [ ] Post-accept curation refresh uses new Declared Self

**Merge order:** Backend (endpoints + versioned persist) → AIA (report/evolution reasoning) → **AIS** (branch + re-curation).

**Branch naming (repo convention):** cut `ais-m7` from role branch `ais` synced with `main`/`dev` at M6 tip (`3745cf4`), matching M1–M6 (`ais-m{N}`).

---

## 7. Risks
| Risk | Mitigation |
|---|---|
| AIA report/evolution reasoning not ready | Thin pass-through report/evolution node slot; AIS routing + tests work against a stub node |
| Backend accept/version endpoints not ready | AIS reacts to an AIS-local `EvolutionAcceptedEvent`; Backend injects/calls the seam |
| Re-curation runs on reject (accidental mutation) | Only `evolution.accepted` wired; explicit `test_evolution_reject_no_mutation` |
| Conditional graph edge breaks linear curation path | Keep `GRAPH_NODE_ORDER` intact for curation triggers; branch only on report/evolution triggers; regression tests on M4/M5/M6 paths |
| Stale stack served after accept | `invalidateStack=True` + `apply_invalidation` + `set_active_stack` on the fresh stack |
| New Declared Self version not reflected in re-curation | Carry version via packet/event; assert in `test_evolution_uses_new_declared_self_version` |
| Report run accidentally triggers full curation (>10s) | Report branch routes to report slot then END; no knowledge/opportunity/planner/assemble on report runs |

---

## 8. Open Questions (block execution)
1. **Event ownership:** AIS-local `EvolutionAcceptedEvent` consume dataclass, or Backend-owned schema mirrored in `app.schemas`?
   - Recommendation: **AIS-local `EvolutionAcceptedEvent` + trigger seam for M7** (mirrors `OnboardingConfirmEvent`); promote to `app.schemas` only if Backend/UI needs the exact serialized shape.
2. **Coordinator branch mechanism:** conditional edges inside the existing `build_coordinator_graph()` keyed on trigger/`run_type`, or a separate report/evolution graph?
   - Recommendation: **conditional routing within the same coordinator graph** (report/evolution trigger → report slot → END), preserving the linear curation path for all other triggers. Least disruptive to M4–M6.
3. **New-version propagation:** does the post-accept `DecisionPacket` already carry the new Declared Self version, or should AIS read it from the accept event?
   - Recommendation: **consume the post-accept packet as-is** (Backend/AIA rebuild it against Twin vN); fall back to `EvolutionAcceptedEvent.declaredSelfVersion` for run_id/telemetry only. Propose surfacing `declaredSelfVersion` on the packet to AIA if it becomes load-bearing.
4. **Report/evolution node ownership:** should AIS ship a thin pass-through `report_evolution` node now (AIA fills later), or wait for AIA's node?
   - Recommendation: **AIS ships the routing + a thin seam node** so the branch and re-curation are testable offline; AIA replaces the node body with real Weekly Report / evolution reasoning.
5. **Re-curation intensity on accept:** full re-curation, or respect `curation_intensity` from the packet?
   - Recommendation: **full re-curation on accept** (identity changed ⇒ stack assumptions invalid); honor `curation_intensity` only if AIA sets it explicitly.
6. **Warm cache on accept:** reuse the M3 best-effort warm-cache after re-curation, or skip?
   - Recommendation: **reuse best-effort warm cache** (non-blocking, same as onboarding) so the refreshed stack is ready for the dashboard; failures logged, never raised.
7. **Branch base:** cut `ais-m7` from current `main` (`3745cf4`) now, or wait for `backend-m7`?
   - Recommendation: **implement on `ais-m7` from synced `main`/`dev` after approval**; merge to `dev` after Backend M7 and AIA M7 (AIS is last per M7 merge order).

---

## 9. Execution checklist (after you approve)
- [ ] Answer open questions 1–7 (or accept recommendations)
- [ ] Approve this plan
- [ ] Sync `dev`/`main`; cut `ais-m7` from role branch `ais` (repo naming)
- [ ] Implement Steps 1–8
- [ ] Run `cd services/api && pytest -q` — green
- [ ] Show commit message → wait for approval → commit / push `ais-m7`
- [ ] Done report; merge to `dev` when you ask (after Backend M7 → AIA M7)

---

## Sync / wait note
- Preparing this plan **after M6 integration** on `main` (`3745cf4`).
- Backend M7 (`agents/runs`, evolution accept/reject, versioned persist) and AIA M7 (Weekly Report narrative, Identity Evolution Agent) may land in parallel; AIS M7 is designed so the **coordinator branch** + **post-accept re-curation** can be built and unit-tested against an `EvolutionAcceptedEvent` seam and a thin report/evolution node before the other roles' M7 work lands.
- **Phase A only:** no M7 code/branch/commit until you approve and answer (or accept) the open questions.
