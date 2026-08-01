# Implementation Plan — Backend — M6

## 1. Context
- Role: **backend** | Milestone: **M6 — Catalog Lenses + Full Ledger (P1)**
- PRD: F5A/F5B/F5C (Growth Stories, Tools, Mentors — P1), F7 P1 (full ledger history)
- Goal: seed a small tagged catalog (stories/tools/mentors) with read APIs AIS can rank against, and confirm/extend the ledger history endpoint for P1's fuller view.

## 2. Scope (in) — Backend checkboxes only
- [ ] Seed 8–12 Growth Stories, 10–15 tools, 5–8 mentors (tagged: identity, stage, bottleneck, outcome)
- [ ] Catalog read APIs
- [ ] Full ledger history endpoint with worked/failed/pending + adaptations
- [ ] Optional Qdrant stub — skip (Postgres tag match is explicitly MVP-acceptable per milestones.md; no reason to add Qdrant for a P1 milestone)

## 3. Scope (out)
- AIS: ranking stories/tools/mentors by stage/bottleneck match, bottleneck-justified inclusion, explanation copy, Opportunity Agent (events/Pune fallback). Backend serves tagged catalog rows; AIS decides what to include and why.
- AIA: DecisionPacket stage/bottleneck enrichment fields, optional embedding trigger.
- Not building real embeddings/Qdrant — plain Postgres tag-match columns are sufficient per the milestone's own stated MVP allowance.

## 4. Current repo state (verified against `origin/dev` @ `6a54927`, post-M5)
- `app/schemas/stack.py` already has `ResourceType` including `"growth_story" | "tool" | "mentor"` — no schema change needed for stack elements themselves.
- `GET /api/v1/ledger` (M5, `app/api/ledger.py`) already returns the full per-user history ordered by timestamp with `verdict` (`worked/failed/pending`) — this likely already satisfies most of "full ledger history endpoint"; M6's addition is mostly making sure **pending outcome windows** are visible (AIS's `ledger_intake.py` tracks these in-memory only) and adding a lightweight "adaptations" view (entries where `unlearningTriggered=True` or `lensWeightAdjustment` is set) rather than a wholly new endpoint.
- No catalog tables/models exist yet — this is new, greenfield work for M6.
- No `aia-m6`/`ais-m6` branches pushed yet — building the reference contract this time (same as M3/M5).

## 5. Detailed work plan (kept tight)

### 5.1–5.2 Models / repositories
1. `app/models/catalog.py`: `GrowthStoryModel`, `ToolModel`, `MentorModel` — each with `id, title/name, description, identity_tags (JSON list), stage_tags (JSON list), bottleneck_tags (JSON list), outcome, url` (tool/mentor only where relevant) + migration `0006_catalog.py`.
2. `app/repositories/catalog_repository.py`: `list_stories(bottleneck=None, stage=None)`, `list_tools(...)`, `list_mentors(...)` — simple `WHERE tag IN (...)` / JSON-contains filtering (Postgres-acceptable per milestone note; SQLite in tests can do an equivalent Python-side filter post-fetch since JSON containment operators differ across dialects — keep the filter logic in Python over a full-table fetch, this catalog is tiny).

### 5.3 Integration
3. `app/api/catalog.py` — `GET /api/v1/catalog/stories`, `/tools`, `/mentors`, each accepting optional `bottleneck`/`stage` query params for AIS to filter against. Read-only, no auth complexity beyond the existing `get_current_user_id` pattern (catalog isn't user-scoped, but keep consistent auth gate).
4. `app/schemas/catalog.py` — `GrowthStorySchema`, `ToolSchema`, `MentorSchema` (frozen response shapes) exported from `app/schemas/__init__.py`.
5. Ledger: add `GET /api/v1/ledger/adaptations` (entries with `unlearningTriggered=True` or non-null `lensWeightAdjustment`) — small addition to existing `app/api/ledger.py`/`ledger_repository.py`, not a rewrite.

### 5.4 Seeds
6. Extend `seed.py`: hardcoded, deterministic catalog fixtures (8–12 stories / 10–15 tools / 5–8 mentors) tagged against the same taxonomy AIA already uses (`confidence, consistency, execution, accountability, knowledge, communication, focus, networking, discipline, burnout` from `scoring/constants.py`'s `BOTTLENECK_TAXONOMY`-equivalent) and the demo persona's stage. Idempotent upsert by fixed IDs, same pattern as the rest of the script.

### 5.5 Tests
- `test_catalog_endpoints.py` (list + tag filtering), `test_catalog_seed.py` (counts + idempotency), `test_ledger_adaptations.py`.
- Run: `AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q`.

## 6. Dependencies & sequencing
- Merge order (per milestones.md M6): **Backend (seeds + APIs) → AIS → AIA (packet fields if needed)**.
- AIS's ranking/inclusion logic depends on these catalog read APIs existing; Backend's work is independently testable without waiting on them.

## 7. Risks
- Tag-match filtering done in Python over a full fetch (not a real Postgres JSON query) — fine at this catalog size (~25-30 rows total), would need revisiting only if the catalog grows substantially post-hackathon.
- Duplicating "full ledger history" intent if AIS's M6 "pending outcome windows" work expects a different shape than my `/ledger` + `/ledger/adaptations` split — flag for reconciliation once their M6 lands, same pattern as prior milestones.

## 8. Open Questions
1. **Is `GET /ledger` (already built in M5) + a small `/ledger/adaptations` addition sufficient for "full ledger history," or does M6 want a genuinely new richer endpoint?** — **Recommendation:** the small addition — M5's endpoint already returns verdict + full fields; re-deriving "adaptations" as a filtered view is the minimal correct interpretation of the checkbox.
2. **Catalog tag-matching: real Postgres JSON containment query vs. Python-side filter?** — **Recommendation:** Python-side filter over a full fetch — catalog is tiny (~30 rows), avoids SQLite/Postgres dialect divergence in tests.

## 9. Execution checklist
- [ ] Answer open questions → approve → I sync `backend` from `dev`, branch `backend-m6`, implement, test, show commit, push.
