# Implementation Plan — AIS — M8

## 1. Context
- **Role:** AIS (AI Systems / Curation)
- **Milestone:** M8 — Demo Hardening & P2 (Optional)
- **PRD features touched:** F9 (Leverage-Moment, P2 — AIS supports the prepared-intervention path, not the calendar decision features), F10 (Growth Partner Match, P2 — mock only), F6/F7 demo-path hardening (prepared variants, Guardian-gated Coach), demo script beats 1–4 (prd.md §13), cut rule + Risks (prd.md §12/§14).
- **Techstack modules touched:**
  - `services/api/app/services/recommendation/` — prepared-intervention seam for the doomscroll path (reuse `warm_cache.py` / `variants.py` / `curation_cycle.py`); new `partner_match.py` (P2); dry-run harness.
  - `services/api/app/agents/nodes/coach/node.py` — Guardian-gated Execution Coach (P2).
  - `services/api/app/providers/embeddings.py` — AIS fills `EmbeddingProvider` usage + a deterministic fake for offline partner match (P2).
  - `services/api/tests/` — full continuous-loop dry-run + prepared-intervention + coach-gating + partner-match tests.
- **Goal:** Harden the AIS curation path so demo script beats 1–4 run with **no empty states and no on-stage LLM/API latency** — pre-generating the doomscroll intervention + its Micro-Action alternative, gating the Execution Coach behind Guardian, adding the mock Growth Partner Match card (P2), and proving the full observe→diagnose→retrieve→assemble→guardian→deliver→dismiss→unlearn→alternative→complete→ledger loop end-to-end against the script. Honesty badges must stay correct on every simulated surface.

---

## 2. Scope (in) — 1:1 with AIS M8 checkboxes in `milestones.md`
- [ ] **Pre-generate prepared interventions for the doomscroll demo path.** (F7 + demo beat 2) — produce the prepared media intervention **and** its Micro-Action alternative variant so the third-dismissal swap is instant and local (no stage LLM/search).
- [ ] **Growth Partner Match card (embedding similarity over fakes) — P2.** (F10) — deterministic embedding similarity over 5 seeded fake profiles → one labeled-prototype card.
- [ ] **Execution Coach silenced unless Guardian allows — P2.** (F6) — `coach_node` emits coaching only when the Guardian decision permits delivery/capacity; otherwise stays silent.
- [ ] **Full continuous loop dry-run: observe → … → measure against demo script.** (merge gate 1) — an offline harness/test walking beats 1–4 with no empty states.

P0-critical for the demo: **prepared interventions** + **full-loop dry-run** (merge gate 1). **P2** (droppable per cut rule): Partner Match, Coach gating.

---

## 3. Scope (out)
- **Backend M8** (owns): seed calendar leverage events + plan-view API; partner-match mock **profiles endpoint** (labeled prototype); pre-warm caches for the demo path (calls AIS seams); Bedrock failover tested once; observability basics (structured logs, LangSmith optional). AIS adds **no** FastAPI routes / DB models / migrations.
- **AIA M8** (owns): leverage-moment decision features from calendar proximity; tune seed targets so Gap movement is projector-legible; Outside Voice lens (P2, 5 domains) — only if time. AIS consumes any packet fields; does not compute Gap or leverage decisions.
- **Deferred / cut-rule:** Outside Voice (AIA P2); any partner outreach/scheduling/messaging (PRD non-goal); real embeddings if `EmbeddingProvider` is not wired (fall back to deterministic fake). If behind at the cut line: drop Partner Match + Coach gating, keep prepared interventions + dry-run + honesty badges + F7 P0 unlearning.
- Hard rules: no Gap arithmetic in AIS; **no on-stage LLM/search calls** on the Tier-0 doomscroll path (prepared/cached only); no vendor SDKs outside `providers/`; simulated surfaces (`Curated fallback`, partner-match prototype) must be truthfully labeled.

---

## 4. Current repo state
- **`origin/main` / `origin/dev`:** `73292cd` — M7 integrated (Weekly Report, Identity Evolution, report/evolution coordinator branch, post-accept re-curation).
- **Already available for M8 reuse:**
  - `warm_cache.py` — `warm_cache_after_onboarding` / `warm_cache_after_evolution` (best-effort `run_curation_cycle` prep) — the template for a doomscroll prewarm seam.
  - `variants.py` — `generate_variants` / `select_variant_by_intensity` / `select_variant_by_capacity` (full/light/micro) — the prepared alternative variants already exist.
  - `intervention_action.py` — dismiss/complete → worked/failed/pending + System Unlearning + `request_alternate_stack` (M5/M6). The "prepared alternative on 3rd dismissal" logic is present; M8 pre-generates it ahead of time.
  - `guardian/node.py` + `guardian.py` — Guardian decision (deliver/downgrade/delay/cancel) + `delivery_allowed`; Coach runs after Guardian in `GRAPH_NODE_ORDER`.
  - `coach/node.py` — **P2 stub** (`visited` only); M8 gates it on the Guardian decision.
  - `providers/embeddings.py` — `EmbeddingProvider` ABC (no impl yet); AIS fills usage + a fake for partner match.
  - Backend `intervention_repository.create(stack, variants)` + `_ensure_prepared_intervention` (seed) — persistence seam AIS feeds; `run_curation_cycle` returns stack + variants.
  - `alternate_lens.request_alternate_stack` — Micro-Action alternative generation (M5).
- **Missing (other roles / AIS):**
  - AIS doomscroll **prepare** seam (stack + micro-action alternative pre-generated as a unit).
  - Guardian-gated Coach behavior; `partner_match.py`; fake `EmbeddingProvider`; full-loop dry-run harness.
  - Backend calendar/plan-view + partner profiles endpoint + demo prewarm wiring (M8).
- **Assumption while waiting for Backend/AIA M8:** AIS builds the prepare seam + dry-run against existing `run_curation_cycle` / `intervention_action` / fixtures; partner match runs over AIS-local fake profiles + a deterministic `FakeEmbeddingProvider` so it works offline; Backend later injects real profiles/endpoint.

---

## 5. Detailed work plan

### 5.1 Contracts / schemas
**Step 1 — Prepared-intervention seam (doomscroll path).**
- **What:** Add `services/recommendation/prepared_intervention.py` with `prepare_doomscroll_intervention(user_id, *, decision_packet=None) -> PreparedIntervention` returning the prepared media stack, its full/light/micro variants, **and** the pre-generated Micro-Action alternative (the post-3rd-dismissal swap).
- **Why:** Demo beat 2 requires the alternative to morph in within ~10s with no stage LLM/API (prd.md §13 beat 2, F7 acceptance, Risks §14 "keep … entirely local").
- **How:** Reuse `run_curation_cycle` (prepared media + variants) + `request_alternate_stack` (Micro-Action). Return a dataclass Backend persists via `intervention_repository.create(stack, variants)`. No new routes/DB.
- **Done when:** Unit test: the returned bundle has ≥2 stack elements, all three variants, and a Micro-Action alternative — with no live provider calls (fixtures/fakes only).

### 5.2 Core logic
**Step 2 — Guardian-gated Execution Coach (P2).**
- **What:** Implement `coach_node` so it only emits coaching output when the Guardian decision permits (delivery allowed and capacity/intensity above a floor); otherwise it stays silent (`visited` only, no coach payload).
- **Why:** F6 — Guardian runs before anything reaches the user; M8 checkbox "Execution Coach silenced unless Guardian allows".
- **How:** Read `guardian_decision` / `delivery_allowed` from state (Guardian precedes Coach in `GRAPH_NODE_ORDER`). Deterministic gate (e.g. silent when `action ∈ {cancel, delay}` or `capacity_pct < 34`). No LLM required for the gate; any coaching text is templated/optional.
- **Done when:** Test: `cancel`/`delay`/low-capacity → no coach payload; `deliver` at adequate capacity → coach payload present.

**Step 3 — Growth Partner Match card (P2, mock).**
- **What:** Add `services/recommendation/partner_match.py`: `match_partner(user_profile, candidates) -> PartnerMatchCard | None` using **embedding cosine similarity** over 5 seeded fake profiles; returns one "someone at your stage with your goal" card with a proposed weekly check-in, labeled prototype.
- **Why:** F10 (P2 — mock only); PRD success-metric story (mentor/partner match without follower counts).
- **How:** Use `EmbeddingProvider`; add a deterministic `FakeEmbeddingProvider` (hashed/bag-of-words vector) so it runs offline. Similarity by stage + goal/bottleneck overlap; **never** popularity. Card carries a `Simulated prototype` honesty label (prd.md §7).
- **Done when:** Test: deterministic top match for a fixture profile; card labeled prototype; no popularity signal consumed.

### 5.3 Integration / wiring
**Step 4 — Full continuous-loop dry-run harness.**
- **What:** Add `services/recommendation/demo_dryrun.py` (thin, importable) that runs the scripted loop for the demo persona: observe (seeded/simulated evidence) → diagnose/curate (`run_curation_cycle`) → Guardian → deliver → **capacity change** (beat 3 swap) → dismiss ×3 → **failed + System Unlearning** → prepared Micro-Action alternative → complete → ledger verdict — returning a structured trace.
- **Why:** M8 merge gate 1 (beats 1–4 runnable without empty states) + Risks §14 (pre-warm the flow; keep it local).
- **How:** Compose existing seams (`prepare_doomscroll_intervention`, `intervention_action.on_intervention_action`, guardian, ledger). No new routes; Backend prewarm can call it. Assert non-empty stack + variants + alternative + ledger chain at each beat.
- **Done when:** Dry-run returns a complete trace with no empty states; every simulated element carries a correct honesty badge.

### 5.4 Seeds / fixtures
**Step 5 — AIS M8 fixtures.**
- **What:** `tests/fixtures/sample_data.py`: `sample_partner_profiles()` (5 fake profiles tagged stage/goal/bottleneck), `sample_prepared_intervention_inputs()`, and a demo-persona state helper for the dry-run.
- **Why:** Keep M8 tests offline/deterministic (guidelines §12; Risks §14 "identical demo data every run").
- **How:** Pure fixtures mirroring Backend's profile shape; Backend owns the real partner-profiles endpoint.
- **Done when:** Offline pytest exercises prepared-intervention + coach gating + partner match + dry-run without network/DB.

### 5.5 Tests
**Step 6 — AIS M8 tests:**
- `test_prepared_intervention_doomscroll.py` — prepared media stack + variants + Micro-Action alternative, no live provider calls.
- `test_coach_gated_by_guardian.py` — silent on cancel/delay/low-capacity; present on deliver.
- `test_partner_match_embedding.py` — deterministic top match; prototype-labeled; no popularity signal.
- `test_full_loop_dry_run.py` — beats 1–4 trace with no empty states; unlearning + alternative + ledger chain present.
- Keep vendor-leak gate + all M0–M7 tests green.
- **Done when:** `cd services/api && pytest -q` green.

### 5.6 Demo / merge-gate verification
**Step 7 — AIS-relevant M8 Merge Gates:**
1. **Demo script beats 1–4 runnable without empty states** — `test_full_loop_dry_run` + prepared interventions.
2. **Cut rule respected** — P2 (Partner Match, Coach gating) isolated behind flags/optional imports; P0 unlearning + prepared path never depend on them.
3. **Honesty badges correct on all simulated surfaces** — partner card `Simulated prototype`; opportunity/catalog fallbacks `Curated fallback`; assert in tests.
- **Done when:** Gates 1 & 3 covered by AIS tests; gate 2 verified by dropping P2 imports and re-running the dry-run green.

---

## 6. Dependencies & sequencing

### What AIS needs from other roles
| Need | From | Status | Stub strategy |
|---|---|---|---|
| Demo prewarm wiring (calls AIS prepare seam) | Backend M8 | Not landed | AIS exposes `prepare_doomscroll_intervention`; Backend calls in seed/prewarm |
| Partner-match mock profiles endpoint | Backend M8 | Not landed | AIS uses `sample_partner_profiles()` fixtures; Backend injects real endpoint |
| `EmbeddingProvider` implementation | Backend | ABC only | AIS ships `FakeEmbeddingProvider` (deterministic, offline) |
| Seed target tuning (projector-legible Gap) | AIA M8 | Not landed | Dry-run asserts direction of Gap change, not exact magnitude |
| Calendar leverage decision features | AIA/Backend M8 | Not landed | AIS supports prepared-intervention path only; leverage decision is out of scope |

### Sequencing within AIS M8
```
Step 1 (prepared seam) → Step 2 (coach gate, P2) → Step 3 (partner match, P2)
  → Step 4 (dry-run harness) → Step 5 (fixtures) → Step 6 (tests) → Step 7 (gates)
```
If time-pressured: **Step 1 → Step 4 → Step 5 → Step 6/7 first** (P0 demo path), then P2 Steps 2–3.

### Merge gate checklist (M8) — from `milestones.md`
- [ ] Demo script beats 1–4 runnable without empty states
- [ ] Cut rule respected: drop P2 + nonessential P1 UI extras; keep F7 P0 unlearning
- [ ] Honesty badges correct on all simulated surfaces

**Merge order:** any order if gates green; prefer Backend seeds → AIA tuning → **AIS prewarm**.

**Branch naming (repo convention):** cut `ais-m8` from role branch `ais` synced with `main`/`dev` at M7 tip (`73292cd`), matching M1–M7 (`ais-m{N}`).

---

## 7. Risks
| Risk | Mitigation |
|---|---|
| On-stage LLM/search latency breaks beat 2 | Everything prepared/cached ahead; prepared alternative pre-generated; Tier-0 path calls no providers |
| Empty stack/variant at any beat | Dry-run asserts non-empty stack + variants + alternative + ledger at each beat; fallback catalog guarantees ≥2 elements |
| `EmbeddingProvider` not wired | `FakeEmbeddingProvider` deterministic fallback; partner match is P2 and offline |
| P2 work destabilizes P0 demo path | P2 isolated behind optional imports/flags; cut-rule test drops P2 and re-runs dry-run |
| Honesty badge missing on simulated card | Partner card forced `Simulated prototype`; badge assertions in tests |
| Coach chatter during low capacity | Deterministic Guardian gate silences coach on cancel/delay/low-capacity |
| Seed magnitude not projector-legible | AIA owns tuning; AIS dry-run checks Gap-change direction, coordinates with AIA on targets |

---

## 8. Open Questions (block execution)
1. **Prepared-intervention ownership:** AIS exposes a `prepare_doomscroll_intervention` seam (stack + variants + Micro-Action alternative) that Backend persists, or AIS writes via `intervention_repository` directly?
   - Recommendation: **AIS exposes the pure seam; Backend persists** via `intervention_repository.create` in seed/prewarm (keeps AIS free of DB writes, guidelines §9.7).
2. **Partner-match embeddings (P2):** real `EmbeddingProvider` or AIS-local deterministic fake?
   - Recommendation: **ship `FakeEmbeddingProvider`** (deterministic, offline) behind the provider adapter; use real embeddings only if Backend wires one. Card always labeled `Simulated prototype`.
3. **Coach gate threshold (P2):** what silences the Execution Coach?
   - Recommendation: **silent when `guardian_decision.action ∈ {cancel, delay}` or `capacity_pct < 34`** (micro tier); coach only on `deliver` at light/full. Deterministic, no LLM.
4. **Dry-run form:** pytest integration test only, or also a runnable script/CLI?
   - Recommendation: **importable `demo_dryrun.py` + `test_full_loop_dry_run.py`**; Backend prewarm can import it. A thin `__main__` is optional.
5. **Cut-rule confirmation:** if behind, drop Partner Match + Coach gating and keep prepared interventions + dry-run + honesty badges?
   - Recommendation: **yes** — P2 (Steps 2–3) are droppable; Steps 1, 4–7 are the P0 demo-hardening core.
6. **Branch base:** cut `ais-m8` from current `main` (`73292cd`) now?
   - Recommendation: **implement on `ais-m8` from synced `main`/`dev` after approval**; merge any order once gates green (prefer after Backend prewarm + AIA tuning).

---

## 9. Execution checklist (after you approve)
- [ ] Answer open questions 1–6 (or accept recommendations)
- [ ] Approve this plan
- [ ] Sync `dev`/`main`; cut `ais-m8` from role branch `ais` (repo naming)
- [ ] Implement Steps 1–7 (P0 path first, then P2 if time)
- [ ] Run `cd services/api && pytest -q` — green
- [ ] Show commit message → wait for approval → commit / push `ais-m8`
- [ ] Done report; merge to `dev` when you ask (any order once gates green)

---

## Sync / wait note
- Preparing this plan **after M7 integration** on `main` (`73292cd`).
- M8 is demo hardening: AIS's load-bearing work is the **prepared doomscroll intervention** and the **full-loop dry-run** (merge gate 1); Partner Match and Coach gating are **P2** and first to be cut under pressure (prd.md §12 cut rule).
- Designed to build and unit-test offline against existing seams (`run_curation_cycle`, `intervention_action`, `variants`, fixtures) + a `FakeEmbeddingProvider`, so it does not block on Backend prewarm/profiles or AIA seed tuning.
- **Phase A only:** no M8 code/branch/commit until you approve and answer (or accept) the open questions.
