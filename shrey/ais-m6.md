# Implementation Plan — AIS — M6

## 1. Context
- **Role:** AIS (AI Systems / Curation)
- **Milestone:** M6 — Catalog Lenses + Full Ledger (P1)
- **PRD features touched:** F5A (Growth Stories), F5B (Tool Curation), F5C (Mentor Network), F5 Real-World Opportunity lens (P1), F7 P1 (full Trust Ledger history: successes + pending outcome windows).
- **Techstack modules touched:**
  - `services/api/app/agents/nodes/knowledge/` + new catalog ranking under `services/recommendation/` — stage/bottleneck ranking of stories/tools/mentors
  - `services/api/app/agents/nodes/opportunity/node.py` — Real-World Opportunity lens (search + Pune fallback)
  - `services/api/app/services/recommendation/stack_assembler.py` — admit catalog element types only when bottleneck-justified
  - `services/api/app/services/recommendation/ledger_intake.py` + new `outcome_window.py` — P1 success/pending verdict paths
  - `services/api/tests/` — ranking, no-filler, explanation-cites-journey, opportunity fallback, ledger success/pending tests
- **Goal:** Extend the Curator so seeded Growth Stories, Tools, Mentors and Real-World Opportunities can enter the Identity Stack — ranked by stage/bottleneck match (never popularity), only when justified by the current bottleneck, each with an explanation citing the shared bottleneck/journey — and add the P1 Trust Ledger success/pending outcome paths. AIS does not own catalog seeds, catalog APIs, or the ledger history endpoint.

---

## 2. Scope (in) — 1:1 with AIS M6 checkboxes in `milestones.md`
- [ ] **Rank stories/tools/mentors by stage/bottleneck match — not popularity.** (F5A/B/C)
- [ ] **Include catalog items in the stack only when justified by the bottleneck (no filler).** (F5A/B/C acceptance: never generic motivational filler / never standalone directory listing)
- [ ] **Explanations cite the shared bottleneck/journey** ("This creator faced the same bottleneck you're facing today…"). (F5A)
- [ ] **Opportunity Agent P1:** real-world events via `SearchProvider` + curated **Pune events fallback** list, labeled. (F5 lens 3)
- [ ] **Ledger P1:** success paths + pending outcome windows (worked/pending verdicts, outcome-window evidence). (F7 P1)

All M6 AIS items are **P1**. P0 curation (Next Step, Missing Action, Guardian, unlearning) already shipped M4/M5 and must stay green.

---

## 3. Scope (out)
- **Backend M6** (owns): seed 8–12 Growth Stories, 10–15 tools, 5–8 mentors (tagged identity/stage/bottleneck/outcome); catalog read APIs (or recommendation-repo embedding); **full ledger history endpoint** (worked/failed/pending + adaptations); optional Qdrant stub (Postgres keyword/tag match acceptable). AIS consumes catalog rows; does not own seeds/APIs/DB.
- **AIA M6** (owns): enrich `DecisionPacket` with **stage + bottleneck features** for catalog ranking; optional identity-summary embedding trigger (if EmbeddingProvider live). AIS consumes these fields; proposes any missing ones via Open Questions.
- **Deferred AIS:** Outside Voice cross-domain analogy (F5 lens 4, **P2**); Weekly Report / Identity Evolution (M7); story-submission or live mentor matching (PRD non-goals).
- Hard rules: ranking is **deterministic feature scoring** (stage/bottleneck fit), never popularity/watch-time; no catalog element without bottleneck justification; no vendor SDKs outside `providers/`; AIS adds no FastAPI routes / DB models.

---

## 4. Current repo state
- **`origin/main` / `origin/dev`:** `6a54927` — M5 integrated (Guardian gate, variants, Trust Ledger P0 failure/unlearning).
- **Already available for M6 reuse:**
  - Schema `ResourceType` already includes `growth_story`, `tool`, `mentor`, `real_world_experience`, `media`, `knowledge`, `micro_mission`, `reflection` (`app/schemas/stack.py`) — no new element types needed.
  - `StackElement` + `StackExplanation` (whyThis/whyNow/howReducesGap) — explanations already mandatory per M4.
  - `assemble_identity_stack` — currently picks **one mission + one resource** (media/knowledge) via `apply_replacement_policy`; M6 must let catalog types compete as the "resource" (and possibly add a justified extra slot).
  - `knowledge_node` retrieval + `badge_mapping` + `fallback_catalog` (bottleneck-keyed) — pattern to mirror for catalog ranking.
  - `opportunity_node` — **stub** (`visited` only); M6 fills it.
  - `ledger_intake.py` (M5) — dismissal-window failure + `record_action`/`evaluate_family_verdict`; **no success/pending outcome-window logic yet**.
  - Backend `services/curation/fallback_resources.py` — M4 seeded set, explicitly "not a catalog (that's M6's job)".
  - `DecisionPacket.rankingFeatures: dict[str,float]` + `bottleneck: BottleneckPacket` — ranking feature carrier already exists.
- **Missing (other roles / AIS):**
  - No catalog store/rows yet (Backend M6 seeds + read API).
  - No stage feature on DecisionPacket schema (AIA M6) — AIS needs `stage` for ranking; stub until landed.
  - No catalog ranking module, no opportunity retrieval + Pune fallback, no ledger success/pending path.
- **Assumption while waiting for Backend/AIA M6:** AIS codes ranking against a `CatalogItem` shape (id, type, title, url, tags: identity/stage/bottleneck/outcome) and a `CatalogProvider`-style fetch seam; ships an AIS-local seeded fixture catalog for tests until Backend seeds land; consumes `DecisionPacket.rankingFeatures["stage"]`/`bottleneck` with a safe default if AIA stage feature is absent.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas
**Step 1 — Catalog item shape + fetch seam (AIS-consumed).**
- **What:** Add `services/recommendation/catalog.py` defining a thin `CatalogItem` dataclass (`id`, `type` ∈ {growth_story, tool, mentor, real_world_experience}, `title`, `url?`, `tags={identity,stage,bottleneck,outcome}`, `starter_action?`) and a `CatalogSource` protocol (`fetch(type, bottleneck, stage) -> list[CatalogItem]`). Default impl reads an AIS seeded fixture; Backend later injects a DB/API-backed source.
- **Why:** Schema/seed ownership is Backend's; AIS needs a stable consume shape (guidelines §12) to build ranking before Backend seeds land.
- **How:** Keep `CatalogItem` AIS-local; if it must cross the API boundary, propose a Backend schema in Open Q. Map `CatalogItem → StackElement` at assemble time.
- **Done when:** Unit test constructs `CatalogItem`s and ranks them without importing Backend DB models.

### 5.2 Core logic
**Step 2 — Deterministic stage/bottleneck ranker (`catalog_ranking.py`).**
- **What:** `rank_catalog_items(items, *, bottleneck, stage) -> list[ScoredCatalogItem]` scoring each item by **bottleneck-tag match** (primary), **stage match** (secondary), and outcome relevance — explicitly **no popularity/recency-of-fame signal**.
- **Why:** F5A/B/C — ranked by stage and bottleneck match, not popularity.
- **How:** Pure function; deterministic weights (e.g. exact bottleneck tag = +1.0, adjacent = +0.3; stage match = +0.5). Ties broken by stable id order. Return score for explanation/telemetry.
- **Done when:** Test: item tagged with the active bottleneck outranks a high-"popularity" but off-bottleneck item; ordering deterministic.

**Step 3 — Bottleneck-justification gate (no filler).**
- **What:** `select_catalog_element(scored, *, min_score) -> CatalogItem | None` returning an item only when its bottleneck match clears a threshold; else `None` (no catalog element added).
- **Why:** F5A/B/C acceptance — stories never generic filler; tools never standalone directory listings; mentors matched by journey/bottleneck.
- **How:** Threshold on the bottleneck component (not total). If nothing clears it, assemble proceeds with the existing media/knowledge + mission (M4 behavior) — catalog is additive-when-justified only.
- **Done when:** Test: off-bottleneck catalog set → no catalog element in stack; matching set → included.

**Step 4 — Assembler admits justified catalog element.**
- **What:** Extend `assemble_identity_stack` so, after the mission + primary resource, it may add **one** justified catalog element (story/tool/mentor) via Steps 2–3, keeping the "smallest coherent combination" rule (cap total elements, e.g. ≤4; never mechanical 8-slot fill).
- **Why:** F5 — smallest justified combination; M6 merge gate 1 (≥1 demo stack includes a seeded story/tool/mentor with match explanation).
- **How:** Add optional `catalog_source` + `stage` params (defaults preserve M4/M5 behavior when absent). Tool inclusion ties to the micro-mission (F5B: "tied directly to its micro-mission and bottleneck").
- **Done when:** With a matching catalog source, stack contains a catalog element; without, stack is unchanged from M5.

**Step 5 — Catalog explanations cite shared bottleneck/journey.**
- **What:** Extend `explanations.build_explanation` (or a `build_catalog_explanation`) so story/tool/mentor elements produce `whyThis` citing the **shared bottleneck/journey** (e.g. "This creator faced the same bottleneck you're facing today: {bottleneck}").
- **Why:** F5A explanation requirement + merge gate 3 (never without justification).
- **How:** Deterministic templates keyed by element type + bottleneck + outcome tag; optional LLM polish behind provider try/except (never blocking).
- **Done when:** Test: each catalog element's `whyThis` references the active bottleneck (and journey/outcome for stories/mentors).

**Step 6 — Opportunity Agent P1 (`opportunity_node`).**
- **What:** Implement `opportunity_node` to build an events query from bottleneck/stage, call `SearchProvider` for real-world events, and fall back to a curated **Pune events** list (labeled `Curated fallback`) on empty/timeout/failure. Emit `real_world_experience` candidates.
- **Why:** F5 lens 3 (P1) — events via search + Pune fallback.
- **How:** Mirror `knowledge_node` retrieval + badge mapping; add `pune_events_fallback.py` seeded list (labeled). Never raise; never block (Tier-2). Opportunity element enters stack only when justified (Step 3 applies) and capacity allows.
- **Done when:** Test: live event docs → `real_world_experience` candidate with Live/Cached badge; failure → Pune fallback labeled `Curated fallback`.

**Step 7 — Ledger P1 success + pending outcome windows (`outcome_window.py` + `ledger_intake` upgrade).**
- **What:** Add outcome-window evaluation: `completed`/positive evidence within a window → `worked`; open window with insufficient evidence → `pending`; extend `evaluate_family_verdict` (or a new `evaluate_outcome`) to return `worked`/`pending` in addition to M5 `failed`. Build `LedgerEntry` rows for success/pending with notes.
- **Why:** F7 P1 — full ledger shows successes + pending outcome windows; merge gate 2 (ledger shows seeded history + live demo chain).
- **How:** Deterministic thresholds (reuse `DISMISSAL_WINDOW_DAYS` style constant for a success/outcome window; propose `OUTCOME_WINDOW_DAYS` in Open Q). Keep M5 failure path intact. AIS returns `LedgerEntry`s; Backend persists + serves the history endpoint.
- **Done when:** Test: completion evidence in window → `worked` entry; open window → `pending`; M5 failure path still green.

### 5.3 Integration / wiring
**Step 8 — Wire catalog + opportunity into the curation graph/cycle.**
- **What:** Pass `catalog_source`, `stage`, and opportunity results through `CoordinatorState` → `assemble_node`; `on_intervention_action`/reflection emits `worked`/`pending` entries. `run_curation_cycle` gains optional `catalog_source`/`stage` (defaults keep M5 behavior).
- **Why:** Backend refresh/Celery invoke AIS; AIS owns the curation cycle they call.
- **How:** No new routes. Document the `catalog_source` injection seam in module docstrings (same pattern as providers).
- **Done when:** `run_curation_cycle` with a matching catalog source returns a stack containing a justified catalog element + explanation.

### 5.4 Seeds / fixtures
**Step 9 — AIS test catalog + Pune events fixtures.**
- **What:** `tests/fixtures/sample_data.py`: `sample_catalog_items()` (stories/tools/mentors tagged by bottleneck/stage/outcome), `sample_offbottleneck_catalog()`, `sample_pune_events()`, `sample_completion_evidence()`.
- **Why:** Merge gates + demo reliability; keep AIS tests DB-free until Backend seeds land.
- **How:** Pure fixtures mirroring Backend's tag shape; Backend owns the real seeded catalog rows.
- **Done when:** Offline pytest exercises ranking/justification/opportunity/ledger without network or DB.

### 5.5 Tests
**Step 10 — AIS M6 tests:**
- `test_catalog_ranking.py` — bottleneck/stage match beats popularity; deterministic order.
- `test_catalog_no_filler.py` — off-bottleneck set → no catalog element; matching set → included.
- `test_catalog_explanations_cite_journey.py` — story/tool/mentor `whyThis` cites shared bottleneck/journey.
- `test_opportunity_events_and_fallback.py` — live events badge; failure → Pune fallback labeled.
- `test_ledger_success_and_pending.py` — completion → `worked`; open window → `pending`; M5 failure intact.
- `test_stack_includes_catalog_element.py` — end-to-end `run_curation_cycle` with catalog source.
- Keep vendor-leak gate + all M4/M5 tests green.
- **Done when:** `cd services/api && pytest -q` green.

### 5.6 Demo / merge-gate verification
**Step 11 — AIS-relevant M6 Merge Gates:**
1. **≥1 demo stack includes a seeded story/tool/mentor with match explanation** — AIS assembler + ranking + explanation; Backend supplies seeds.
2. **Ledger shows seeded history + live demo chain** — AIS emits worked/pending/failed entries; Backend persists + serves history endpoint.
3. **Catalog items never appear without bottleneck justification** — AIS justification gate + `test_catalog_no_filler`.
- **Done when:** Gates 1 & 3 covered by AIS tests; gate 2 verified once Backend history endpoint + seeds wired.

---

## 6. Dependencies & sequencing

### What AIS needs from other roles
| Need | From | Status | Stub strategy |
|---|---|---|---|
| Seeded catalog rows (stories/tools/mentors, tagged) | Backend M6 | Not landed | AIS `CatalogItem` fixtures + `CatalogSource` seam; Backend injects real source |
| Catalog read API / repo embedding | Backend M6 | Not landed | AIS consumes via `CatalogSource`; no direct DB access |
| Full ledger history endpoint | Backend M6 | Not landed | AIS returns worked/pending/failed `LedgerEntry`s; Backend persists/serves |
| `stage` (+ bottleneck) features on DecisionPacket | AIA M6 | `rankingFeatures` dict exists; no `stage` yet | Read `rankingFeatures.get("stage")`; default stage if absent (propose field in Open Q) |
| Optional identity embedding | AIA M6 | Optional | Deterministic tag match works without embeddings (MVP acceptable per milestones) |

### Sequencing within AIS M6
```
Step 1 (catalog shape) → Step 2 (ranker) → Step 3 (justification gate)
  → Step 4 (assembler admits catalog) → Step 5 (catalog explanations)
  → Step 6 (opportunity P1) → Step 7 (ledger success/pending)
  → Step 8 (graph/cycle wiring) → Step 9 (fixtures) → Step 10 (tests) → Step 11 (gates)
```

### Merge gate checklist (M6) — from `milestones.md`
- [ ] ≥1 demo stack includes a seeded story or tool or mentor with match explanation
- [ ] Ledger shows seeded history + live demo chain
- [ ] Catalog items never appear without bottleneck justification

**Merge order:** Backend (seeds + APIs) → **AIS** → AIA (packet fields if needed).

**Branch naming (repo convention):** cut `ais-m6` from role branch `ais` synced with `main`/`dev` at M5 tip (`6a54927`), matching M1–M5 (`ais-m{N}`).

---

## 7. Risks
| Risk | Mitigation |
|---|---|
| Backend catalog seeds/API not ready | `CatalogSource` seam + AIS fixture catalog; ranking testable offline |
| AIA `stage` feature missing | Rank on bottleneck primarily; default stage; degrade gracefully |
| Catalog filler creeps into stacks | Hard justification threshold on bottleneck component; `test_catalog_no_filler` |
| Popularity signal sneaks into ranking | Ranker only consumes tag/stage/outcome features; no view/like fields modeled |
| Opportunity retrieval blocks Tier-2 | Non-raising, timeout via provider; Pune fallback labeled; never blocks stack |
| Ledger P1 changes break M5 failure path | Add worked/pending alongside failed; keep M5 rule + tests intact |
| Over-stuffing stack (8-slot temptation) | Cap total elements (≤4), one catalog element max, only when justified |

---

## 8. Open Questions (block execution)
1. **`CatalogItem` ownership:** AIS-local consume dataclass, or Backend-owned schema mirrored in `app.schemas`?
   - Recommendation: **AIS-local `CatalogItem` + `CatalogSource` seam for M6**; promote to `app.schemas` only if UI/Backend needs the exact shape serialized.
2. **`stage` feature location:** add `stage` to `DecisionPacket` (AIA) or read from `rankingFeatures`?
   - Recommendation: **read `rankingFeatures.get("stage")` for M6** (no schema change); propose a typed `stage` field to AIA if it becomes load-bearing.
3. **Justification threshold** for admitting a catalog element:
   - Recommendation: **require an exact bottleneck-tag match** (bottleneck score ≥ 1.0) to include; stage only reorders. Keeps "no filler" strict for the demo.
4. **How many catalog elements per stack:**
   - Recommendation: **at most one** catalog element (story OR tool OR mentor) beyond the P0 mission+resource, preserving "smallest coherent combination"; total elements ≤4.
5. **Outcome-window length for `worked`/`pending`:**
   - Recommendation: **`OUTCOME_WINDOW_DAYS = 7`** (aligns with the 7-day recency decay); completion/positive evidence in-window → `worked`, else `pending`. Propose constant home in `scoring/constants.py`.
6. **Opportunity source:** reuse the same `SearchProvider` (Tavily/cache) as knowledge, or a separate events search?
   - Recommendation: **reuse `SearchProvider`** with an events-flavored query + Pune fallback; no new provider (F5 lens 3 MVP).
7. **Branch base:** cut `ais-m6` from current `main` (`6a54927`) now, or wait for `backend-m6` seeds?
   - Recommendation: **implement on `ais-m6` from synced `main`/`dev` after approval**; merge to `dev` after Backend M6 (AIS precedes AIA per milestones).

---

## 9. Execution checklist (after you approve)
- [ ] Answer open questions 1–7 (or accept recommendations)
- [ ] Approve this plan
- [ ] Sync `dev`/`main`; cut `ais-m6` from role branch `ais` (repo naming)
- [ ] Implement Steps 1–11
- [ ] Run `cd services/api && pytest -q` — green
- [ ] Show commit message → wait for approval → commit / push `ais-m6`
- [ ] Done report; merge to `dev` when you ask (after Backend M6)

---

## Sync / wait note
- Preparing this plan **after M5 integration** on `main` (`6a54927`).
- Backend M6 (catalog seeds/APIs, ledger history endpoint) and AIA M6 (stage/bottleneck packet features) may land in parallel; AIS M6 is designed to rank + justify + explain against a `CatalogSource` seam and fixture catalog so it can be built and unit-tested before Backend seeds exist.
- **Phase A only:** no M6 code/branch/commit until you approve and answer (or accept) the open questions.
