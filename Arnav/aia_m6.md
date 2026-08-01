# Implementation Plan — AIA — M6

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M6 — Catalog Lenses + Full Ledger (P1)
- **PRD features touched:** F5A (Growth Stories), F5B (Tool Curation), F5C (Mentor Network) — specifically the ranking signals that drive catalog selection
- **Techstack modules touched:**
  - `services/api/app/services/decision/packet.py` — Extend `DecisionPacket` with `stage` and `bottleneck_features` for AIS catalog ranking
  - `services/api/app/services/identity/catalog_features.py` — **[NEW]** Pure function `extract_catalog_features(gap_result, declared_self, create_consume, bottleneck_candidates) -> CatalogFeatures` to derive stage + bottleneck feature set deterministically
  - `services/api/app/services/identity/recompute.py` — Pass `CatalogFeatures` into `build_decision_packet`
  - `services/api/app/services/identity/__init__.py` — Export new symbols
  - `services/api/tests/identity/test_m6_catalog_features.py` — **[NEW]** M6 unit test suite
- **Goal (1–2 sentences):** Produce a deterministic `CatalogFeatures` payload attached to every `DecisionPacket` that gives AIS's catalog ranker everything it needs to match Stories/Tools/Mentors by stage and bottleneck — without any LLM call. Optionally trigger an identity summary embedding if `EmbeddingProvider` is wired.

---

## 2. Scope (in)

Mapped 1:1 to M6 AIA checkboxes in `milestones.md`:

- **[AIA-M6-1] Enrich `DecisionPacket` with `stage` + bottleneck features for catalog ranking (P1):**
  - Derive a `stage: str` from the current `gap_score` (deterministic tier: `"early"`, `"developing"`, `"advancing"`, `"peak"`).
  - Derive `bottleneck_label: str` (top candidate's label from `bottleneck_candidates`).
  - Derive `bottleneck_confidence: float`.
  - Derive `top_deficit_attr_id: str` (attribute with highest deficit in `per_attribute`).
  - Package all four into a `CatalogFeatures` dataclass and attach to `DecisionPacket.catalog_features`.
  
- **[AIA-M6-2] Optional identity summary embedding trigger (P1 — if `EmbeddingProvider` is live):**
  - `trigger_identity_embedding(declared_self, embedding_provider) -> list[float] | None`
  - Returns `None` if `embedding_provider` is `None` (graceful bypass).
  - If live: embed a short identity summary string (`"<attr1>, <attr2>, ... | bottleneck: <label>"`) via `embedding_provider.embed([text])`.
  - Caller (recompute or wiring) decides whether to persist; AIA only produces the vector.

---

## 3. Scope (out)

AIA does **not** build for M6:

- **Backend M6:** Seed 8–12 Growth Stories, 10–15 tools, 5–8 mentors with tags; catalog read APIs; full ledger history endpoint; optional Qdrant stub — all Backend M6.
- **AIS M6:** Rank stories/tools/mentors by `stage`/`bottleneck_label` match, include in stack only when justified, explanations citing shared bottleneck/journey, Opportunity Agent P1, Ledger P1 success paths — all AIS M6.
- Real embeddings-based mentor matching (M7+ if EmbeddingProvider not live).
- Any story/tool/mentor selection logic — purely AIS catalog work.

---

## 4. Current repo state

- **M0–M5 complete and merged on `main`, `dev`, `aia`** (commit `6a54927` after pull).
- **Already exists:**
  - `DecisionPacket` with `user_id`, `gap_score`, `alignment`, `bottleneck_candidates`, `curation_intensity`, etc. — M0–M5 ✓
  - `GapResult.per_attribute: List[AttributeBreakdown]` with `attr_id` and `deficit` — M0 ✓
  - `EmbeddingProvider` ABC stub in `app/providers/embeddings.py` — M0 ✓
  - `recompute_user_gap` orchestrator wiring `bottleneck_v1` + `growth_decision` — M4 ✓
- **Greenfield for M6:**
  - `CatalogFeatures` dataclass
  - `extract_catalog_features()` pure function
  - `trigger_identity_embedding()` optional function
  - `DecisionPacket.catalog_features` field
  - M6 unit tests

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Extend `DecisionPacket` with `catalog_features`**

- **What:** `services/api/app/services/decision/packet.py`
  - Add `CatalogFeatures` dataclass:
    ```python
    @dataclass
    class CatalogFeatures:
        stage: str                  # "early" | "developing" | "advancing" | "peak"
        bottleneck_label: str       # top BottleneckCandidate label, "" if none
        bottleneck_confidence: float  # 0.0 if none
        top_deficit_attr_id: str    # attr_id with highest deficit, "" if none
    ```
  - Add field to `DecisionPacket`: `catalog_features: Optional[CatalogFeatures] = None`
  - Update `build_decision_packet` to accept and pass `catalog_features`.
- **Why:** AIS Coordinator reads `DecisionPacket.catalog_features.stage` and `.bottleneck_label` to rank Stories/Tools/Mentors (M6 AIA-1); PRD F5A "re-ranked by stage and bottleneck match".
- **Done when:** `CatalogFeatures` importable from `app.services.decision.packet`; existing tests still pass.

---

### 5.2 Core logic

**Step 2 — `catalog_features.py`: Extract Catalog Features**

- **What:** `services/api/app/services/identity/catalog_features.py`
  - `STAGE_TIERS` mapping (deterministic, pure function):
    ```python
    # Gap score → stage name (higher Gap = earlier stage)
    # 0-25 = "peak", 26-50 = "advancing", 51-75 = "developing", 76-100 = "early"
    ```
  - `extract_catalog_features(gap_result, bottleneck_candidates) -> CatalogFeatures`
    - Derives `stage` from `gap_result.gap_score` via `STAGE_TIERS`.
    - Derives `bottleneck_label` and `bottleneck_confidence` from `bottleneck_candidates[0]` if non-empty.
    - Derives `top_deficit_attr_id` from `max(per_attribute, key=lambda a: a.deficit).attr_id`.
    - Returns `CatalogFeatures`.
  - `trigger_identity_embedding(declared_self, embedding_provider) -> list[float] | None`
    - Builds summary text: `", ".join([a.id for a in declared_self.attributes])`.
    - Calls `embedding_provider.embed([summary_text])[0]` if provider is not `None`.
    - On any exception: returns `None` (graceful bypass per hackathon cut rule).
- **Why:** M6 AIA-1 (stage + features) and AIA-2 (embedding trigger). Both are optional signals — they enrich the packet but never block Gap computation.
- **Done when:** `extract_catalog_features` returns correct `stage` for each Gap score tier; `trigger_identity_embedding` returns `None` when provider is `None`.

---

**Step 3 — Wire `extract_catalog_features` into `recompute_user_gap`**

- **What:** `services/api/app/services/identity/recompute.py`
  - After `bottleneck_candidates` are produced, call `extract_catalog_features(gap_result, bottleneck_candidates)`.
  - Pass `catalog_features` into `build_decision_packet(…, catalog_features=catalog_features)`.
  - Accept optional `embedding_provider` parameter (already `None`-defaulted); call `trigger_identity_embedding` if provided.
- **Why:** M6 AIA-1; every `DecisionPacket` produced by `recompute_user_gap` now carries catalog ranking features transparently.
- **Done when:** `recompute_user_gap` returns `DecisionPacket` with non-`None` `catalog_features`; `gap_score` unchanged.

---

### 5.3 Integration / wiring

**Step 4 — Update `services/identity/__init__.py` Exports**

- Export `CatalogFeatures`, `extract_catalog_features`, `trigger_identity_embedding`.
- **Done when:** clean imports from `app.services.identity`.

---

### 5.4 Seeds / fixtures

No new seed fixtures required for M6 AIA. Stage derivation is a pure function over `gap_score`; Aarav seed provides sufficient data.

---

### 5.5 Tests

**Step 5 — M6 Unit Test Suite**

- **What:** `services/api/tests/identity/test_m6_catalog_features.py`
  - **Test 1 (Stage tiers):** `extract_catalog_features` maps Gap 10 → `"peak"`, Gap 35 → `"advancing"`, Gap 60 → `"developing"`, Gap 85 → `"early"`.
  - **Test 2 (Bottleneck label pass-through):** When `bottleneck_candidates = [BottleneckCandidate("execution", 0.85)]`, `catalog_features.bottleneck_label == "execution"` and `bottleneck_confidence == 0.85`.
  - **Test 3 (Top deficit attr):** `catalog_features.top_deficit_attr_id` matches the `attr_id` with highest deficit in `GapResult.per_attribute`.
  - **Test 4 (Empty candidates):** When `bottleneck_candidates = []`, `bottleneck_label == ""` and `bottleneck_confidence == 0.0`.
  - **Test 5 (Embedding trigger with None provider):** `trigger_identity_embedding(aarav_declared, None)` returns `None` without error.
  - **Test 6 (DecisionPacket carries catalog_features):** `recompute_user_gap` with Aarav seed returns `DecisionPacket` with non-`None` `catalog_features` and correct `stage`.
  - **Test 7 (Gap Firewall remains intact):** `gap_score` is unchanged by `extract_catalog_features` call.
- **Done when:** `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 45 tests green.

---

### 5.6 Demo / merge-gate verification

**Step 6 — M6 Merge Gate Check (AIA contribution)**

- Gate 1: At least one demo stack includes a seeded story or tool or mentor with match explanation — **AIA Gate:** `DecisionPacket.catalog_features.stage` and `bottleneck_label` are populated and consumed by AIS ranker.
- Gate 3: Catalog items never appear without bottleneck justification — **AIA Gate:** `bottleneck_label` is always present in `catalog_features` (empty string default when no candidates, which AIS treats as no bottleneck filter).

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M6)
- Catalog seeds (stories/tools/mentors) — Backend M6. AIA does not call catalog APIs; AIA only produces the ranking features AIS uses.

### What AIS needs from AIA (M6)
- `DecisionPacket.catalog_features.stage` and `.bottleneck_label` for catalog ranking.

### Suggested sequencing within AIA M6
```
Sync main → cut aia → cut m6 feature branch from aia
  → Step 1 (CatalogFeatures + DecisionPacket field)
  → Step 2 (catalog_features.py module)
  → Step 3 (wire into recompute_user_gap)
  → Step 4 (__init__ exports)
  → Step 5 (Tests)
  → Step 6 (Gate verify)
```

### M6 Merge gate checklist
- [ ] At least one demo stack includes a seeded story/tool/mentor with match explanation (Backend + AIS gate)
- [ ] Ledger shows seeded history + live demo chain (Backend + AIS gate)
- [ ] **Catalog items never appear without bottleneck justification** ← AIA Gate (`catalog_features.bottleneck_label` populated)

**Merge order (M6):** Backend (seeds + APIs) → AIS → **AIA (packet fields)**.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Stage tier boundary questions (where exactly does "early" end?) | Boundaries are PRD-derived: Gap score maps naturally — higher Gap = further from Declared Self = earlier stage. Boundaries are documentation-level decisions, not LLM calls. |
| `EmbeddingProvider` not live during hackathon | `trigger_identity_embedding` gracefully returns `None` when provider is `None`; zero test failures. |
| `per_attribute` empty (no declared attributes) | `extract_catalog_features` returns `top_deficit_attr_id = ""` with no panic; guard with `if not per_attribute` check. |

---

## 8. Open Questions

1. **Stage tier boundaries:** Is `gap_score 0–25 = "peak"`, `26–50 = "advancing"`, `51–75 = "developing"`, `76–100 = "early"` reasonable for AIS's catalog ranker? (AIS seeds catalogs with `stage` tags matching these names.)
   - Recommendation: **Yes** — maps naturally: 0 Gap means identity fully aligned (peak performer), 76+ means just starting the journey.

2. **Stage naming convention:** Should AIS's catalog tags use these exact strings (`"early"`, `"developing"`, `"advancing"`, `"peak"`)? If AIS uses different labels in the seeded catalog, we should align now.
   - Recommendation: **Confirm with AIS team** before coding; otherwise default to the four above.

3. **`catalog_features` field on `DecisionPacket`:** Should it be `Optional[CatalogFeatures]` defaulting to `None` (backward-compatible) or always populated from M6 onward?
   - Recommendation: **Optional defaulting to `None`** — all M0–M5 tests continue to pass without changes.

4. **Embedding trigger scope:** Should `trigger_identity_embedding` be called inside `recompute_user_gap` (if `embedding_provider` is passed in) or only on explicit onboarding confirm?
   - Recommendation: **Only on explicit confirm** for now (no extra latency on every evidence event). `recompute_user_gap` stays fast; the caller passes the embedding if they want it.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–4)
- [ ] Approve this plan
- [ ] Agent cuts `m6` from `aia`
- [ ] Implement Steps 1–6 in order
- [ ] Run `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 45 tests green
- [ ] Show `git status` + diff summary + proposed commit message → wait for human approval → commit
- [ ] Done report
