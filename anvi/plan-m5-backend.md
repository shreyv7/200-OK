# Implementation Plan — Backend — M5

## 1. Context
- Role: **backend** | Milestone: **M5 — Guardian Gate + Trust Ledger P0** (demo peak)
- PRD: F6 (Guardian/Capacity, P0), F7 P0 (Trust Ledger + System Unlearning)
- Goal: persist capacity + intervention budget, a real Trust Ledger (list/record), pre-stored full/light/micro variants, and a seeded hypothesis with two prior dismissals so the third live dismissal trips System Unlearning.

## 2. Scope (in) — Backend checkboxes only
- [ ] Capacity as evidence/context event; store 0–100 (already have `User.capacity`; need the event/update path)
- [ ] Intervention budget fields: interventions-today, last intervention time, dismissal rate
- [ ] Ledger APIs: list, record deliver/accept/snooze/dismiss/complete
- [ ] Persist lens weights; expose on decision/stack refresh
- [ ] Pre-store three variants per active intervention: full/light/micro
- [ ] Seed ledger: demo hypothesis with two prior dismissals
- [ ] Sub-250ms path for dismiss logging (poll is fine; no new WS infra, same call as M2)

## 3. Scope (out)
- AIS: Guardian gate logic itself (cap 5/day, spacing check, downgrade/delay/cancel reasoning), reflection rule that flips a hypothesis to `failed` and requests an alternate lens, System Unlearning tag semantics. Backend stores what AIS decides; doesn't decide it.
- AIA: capacity tier constants (already exist — `CAPACITY_FULL_MIN=67/LIGHT_MIN=34` in `scoring/constants.py`), Decision Engine budget-aware intensity logic.
- Not touching AIS's in-memory `ledger_intake.py`/`stack_state.py` — Backend adds real persistence *alongside*, doesn't rewrite their modules.

## 4. Current repo state (verified against `origin/dev` @ `9f8cba5`, post-M4)
- `app/models/user.py` already has `capacity: float` (0–100, default 100) — no new column needed, just an update path + treating capacity changes as a context event per F6.
- `app/schemas/ledger.py` (M0, frozen): `LedgerEntry{id,userId,hypothesisId,hypothesisFamily,action,verdict,timestamp,unlearningTriggered,lensWeightAdjustment,note}` and `app/schemas/stack.py`'s `InterventionVariant{hypothesisId,intensity,stack,generatedAt}` — both already shaped correctly; no schema changes needed.
- AIS's `app/services/recommendation/ledger_intake.py` docstring: *"Persistence and verdict logic land in M5"* — currently pure in-memory evidence-ID tracking per hypothesis. Backend's ledger table is the persistence layer this is waiting on.
- `app/services/identity/scoring/constants.py` already has `DISMISSAL_FAILURE_THRESHOLD=3`, `DISMISSAL_WINDOW_DAYS=14` — reuse, don't redefine.
- No `aia-m5`/`ais-m5` branches exist yet — building the reference contract this time.

## 5. Detailed work plan (tight — implementation should move fast)

### 5.1–5.2 Models / repositories
1. `app/models/ledger_entry.py` (`LedgerEntryModel`: mirrors `LedgerEntry` schema) + `app/models/intervention_budget.py` (`InterventionBudgetModel`: user_id, interventions_today, last_intervention_at, dismissal_count_14d) + migration `0005_ledger_capacity.py`.
2. `app/repositories/ledger_repository.py`: `record(db, entry: LedgerEntry) -> LedgerEntryModel`, `list_for_user(db, user_id) -> list[LedgerEntryModel]`, `count_recent_dismissals(db, hypothesis_family, window_days=14) -> int`.
3. `app/repositories/budget_repository.py`: `get_or_create(db, user_id)`, `record_intervention_delivered(db, user_id)`, `recent_dismissal_rate(db, user_id) -> float`.

### 5.3 Integration
4. `app/api/capacity.py` — `PATCH /api/v1/capacity` (body: `{value: float}`, 0–100) updates `User.capacity` and inserts a `trellis`-sourced context evidence event via the existing M1 adapter (capacity change *is* an evidence/context event per F6) — reuse `evidence_service.ingest`, not a new pipeline.
5. `app/api/ledger.py` — `GET /api/v1/ledger` (list), `POST /api/v1/ledger/record` (body: hypothesisId, hypothesisFamily, action). On `dismissed`: check `count_recent_dismissals` — if it now hits the M0-frozen `DISMISSAL_FAILURE_THRESHOLD`, set `verdict="failed"`, `unlearningTriggered=True` (deterministic rule Backend enforces at write time, per guidelines.md's "no LLM arithmetic" — this is Backend's job, not AIS's, since it's a hard threshold check identical in spirit to M3's weight-sum enforcement).
6. Extend `app/services/curation/stack_orchestration.py`'s `refresh_stack` to also generate/store the three `InterventionVariant`s (full/light/micro) sharing one `hypothesisId`, via a new `app/repositories/variant_repository.py` (or a JSON column on `InterventionModel`) — simplest: add `variants_json` column to `interventions` table alongside the existing `stack_json`.
7. Dashboard/stack responses expose current lens weights (a simple `dict[str,float]` derived from ledger `lensWeightAdjustment` history, latest-wins per lens) — add to `DashboardSummary` or a small new field on `GET /stack/active`.

### 5.4 Seeds
8. Extend `seed.py`: insert two `dismissed` `LedgerEntry` rows for one fixed hypothesis family (dated within the 14-day window) so a third live dismissal during the demo trips the threshold immediately.

### 5.5 Tests
- `test_ledger_endpoints.py` (record/list, threshold-trip on 3rd dismissal, idempotent seed), `test_capacity_endpoint.py`, `test_intervention_variants.py` (three variants share hypothesisId).
- Run: `AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q`.

## 6. Dependencies & sequencing
- Merge order (per milestones.md M5, non-default): **Backend (ledger+variants storage) → AIS (guardian+reflection rules) → AIA (decision budget integration)**.
- AIS's Guardian gate and reflection logic will call into the ledger/budget repositories Backend builds here — same cross-role pattern as M2–M4.

## 7. Risks
- Threshold-trip logic (3 dismissals → failed) living in Backend's `POST /ledger/record` vs. AIS's future reflection module could duplicate the rule in two places once AIS lands their M5 work — flag for reconciliation then, don't block now.
- `variants_json` reuses `InterventionModel` rather than a new table — smallest change that satisfies the checkbox; revisit only if M6+ needs richer variant querying.

## 8. Open Questions
1. **Threshold check in `POST /ledger/record` now, knowing AIS's M5 reflection module may also implement it?** — **Recommendation:** yes, implement it in Backend now (deterministic rule, needed for the demo path to work at all before AIS's M5 lands); expect to reconcile/simplify once AIS's module exists, same pattern as prior milestones.
2. **Variants storage: new table vs. JSON column on `interventions`?** — **Recommendation:** JSON column (`variants_json`) — smallest change, no new join needed for M5's scope.
3. **Capacity change as evidence event — reuse `FixtureTrellisAdapter` with a new event type, or a dedicated non-adapter path?** — **Recommendation:** new event type `capacity_set` through the same adapter+ingest pipeline (guidelines.md "one evidence path" — no exceptions for capacity either).

## 9. Execution checklist
- [ ] Answer open questions → approve → I sync `backend` from `dev`, branch `backend-m5`, implement, test, show commit, push.
