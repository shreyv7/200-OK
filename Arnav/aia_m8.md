# Implementation Plan — AIA — M8

## 1. Context

- **Role:** AIA (AI Identity Architecture)
- **Milestone:** M8 — Demo Hardening & P2 (Optional)
- **PRD features touched:** F9 P2 (Leverage-Moment Trigger), F2/F9 (Demo script legibility & projector visibility), F5 (Outside Voice Lens - P2)
- **Techstack modules touched:**
  - `services/api/app/services/identity/leverage_features.py` — **[NEW]** `extract_leverage_features()` calendar proximity feature extractor
  - `services/api/app/services/decision/packet.py` — Extend `DecisionPacket` with `leverage_features` field
  - `services/api/app/services/identity/outside_voice.py` — **[NEW]** `OutsideVoiceLens` domain-constrained recommendation lens (P2)
  - `services/api/app/services/identity/recompute.py` — Wire calendar proximity into `recompute_user_gap`
  - `services/api/tests/fixtures/aarav_seed.py` — **[UPDATE]** Tune event weights & target points so demo Gap score deltas are projector-legible (sharp 8–15 point shifts)
  - `services/api/tests/identity/test_m8_hardening.py` — **[NEW]** M8 unit test suite
- **Goal:** Harden AIA components for live demo stability. Provide calendar event proximity features to AIS for pre-event leverage interventions (F9), tune seed event parameters so Gap score shifts are projector-legible (≥ 8–15 points on mission completion/doomscroll), and provide a domain-constrained `OutsideVoiceLens` helper (P2).

---

## 2. Scope (in)

Mapped 1:1 to M8 AIA checkboxes in `milestones.md`:

- **[AIA-M8-1] Leverage-moment decision features from calendar proximity (F9):**
  - Create `leverage_features.py` module exposing `extract_leverage_features(calendar_events, ref_time) -> LeverageFeatures`.
  - `LeverageFeatures` dataclass: `has_upcoming_event: bool`, `event_title: str`, `days_until_event: float`, `relevant_attribute_id: str`, `suggested_action_type: str`.
  - Logic: Filters events occurring within 0–7 days of `ref_time` (e.g. "College Presentation on Friday"). Matches event title/description keywords against `DeclaredSelf` attributes (`"presentation"`, `"speech"` → `public_speaker`; `"demo"`, `"launch"` → `builder`).
  - Attach `leverage_features: Optional[LeverageFeatures]` to `DecisionPacket`.

- **[AIA-M8-2] Tune seed targets so Gap movement is projector-legible (Demo Hardening):**
  - Verify that Aarav persona baseline Gap score vs. post-mission completion Gap score exhibits a sharp, visible delta (≥ 8–15 points on the 0–100 scale).
  - Adjust default event weight overrides or target weekly points (`D_i`) if necessary so the demo script beats (initial state → doomscroll drift → micro-mission completion) produce clean, projector-legible score jumps.

- **[AIA-M8-3] Outside Voice lens (P2 — if time):**
  - Create `outside_voice.py` exposing `evaluate_outside_voice_lens(declared_self, gap_result) -> OutsideVoiceRecommendation | None`.
  - Constrained strictly to **5 pre-approved growth domains**: `["public_speaking", "software_building", "writing", "networking", "mindfulness"]`.
  - Returns a candidate lens recommendation for cross-domain identity expansion only when primary attribute gap is low (alignment ≥ 70%).

---

## 3. Scope (out)

AIA does **not** build for M8:

- **Backend M8:** Seed calendar leverage events, plan-view API, partner match mock endpoints, pre-warming caches, Bedrock failover test, structured logs / LangSmith setup — all Backend M8.
- **AIS M8:** Pre-generate prepared interventions for doomscroll demo path, Growth Partner Match card (embedding similarity), Execution Coach silencing, full continuous loop dry-run — all AIS M8.
- Real calendar API integrations (Google Calendar OAuth, iCal parsing) — simulated/seeded calendar events only per PRD F9.

---

## 4. Current repo state

- **M0–M7 complete and merged on `main`, `dev`, `aia`** (synced to `73292cd`).
- **Already exists:**
  - `DecisionPacket` carrying `catalog_features`, `growth_decision`, `bottleneck_candidates` — M0–M6 ✓
  - `recompute_user_gap` orchestrator — M4 ✓
  - `aarav_seed.py` fixture — M1 ✓
  - `EVENT_WEIGHTS` in `constants.py` — M0 ✓
- **Greenfield for M8:**
  - `leverage_features.py` module
  - `outside_voice.py` module
  - `LeverageFeatures` field on `DecisionPacket`
  - `test_m8_hardening.py` test suite

---

## 5. Detailed work plan

### 5.1 Contracts / schemas

**Step 1 — Extend `DecisionPacket` with `leverage_features`**

- **What:** `services/api/app/services/decision/packet.py`
  - Add `LeverageFeatures` dataclass:
    ```python
    @dataclass
    class LeverageFeatures:
        has_upcoming_event: bool
        event_id: str
        event_title: str
        days_until_event: float
        relevant_attribute_id: str
        suggested_prep_type: str  # "rehearsal" | "quick_review" | "mindset"
    ```
  - Add `leverage_features: Optional[LeverageFeatures] = None` to `DecisionPacket`.
  - Update `build_decision_packet` function to accept and pass `leverage_features`.
- **Why:** M8 AIA-1; AIS Curator node reads `DecisionPacket.leverage_features` to trigger pre-event leverage interventions (PRD F9).
- **Done when:** `from app.services.decision.packet import LeverageFeatures` resolves cleanly.

---

### 5.2 Core logic

**Step 2 — `leverage_features.py`: Calendar Proximity Feature Extractor**

- **What:** `services/api/app/services/identity/leverage_features.py`
  - `extract_leverage_features(calendar_events: List[dict], declared_self: DeclaredSelf, ref_time: datetime) -> Optional[LeverageFeatures]`
  - Iterates over `calendar_events` (dicts with `id`, `title`, `start_time`, `attribute_id`).
  - Finds the closest upcoming event within `0.0 < delta_days <= 7.0`.
  - Maps event title keywords (`"presentation"`, `"speech"`, `"talk"`) → `suggested_prep_type = "rehearsal"`; (`"demo"`, `"launch"`, `"submission"`) → `suggested_prep_type = "quick_review"`.
  - Returns `LeverageFeatures` if an upcoming event is within 7 days, else `None`.
- **Why:** M8 AIA-1; PRD F9: "Simulated calendar with 2–3 seeded upcoming events... Agent schedules the right input to land *before* the moment".
- **Done when:** `extract_leverage_features` correctly identifies an event 3 days away and assigns `suggested_prep_type`.

---

**Step 3 — `outside_voice.py`: Outside Voice Lens (P2)**

- **What:** `services/api/app/services/identity/outside_voice.py`
  - Constants: `ALLOWED_DOMAINS = {"public_speaking", "software_building", "writing", "networking", "mindfulness"}`.
  - `OutsideVoiceRecommendation` dataclass: `domain: str`, `reason: str`, `suggested_lens: str`.
  - `evaluate_outside_voice_lens(declared_self: DeclaredSelf, gap_result: GapResult) -> Optional[OutsideVoiceRecommendation]`
    - Evaluates overall alignment. If `alignment >= 70`: identifies a domain from `ALLOWED_DOMAINS` not currently in `declared_self.attributes` to suggest as a growth expansion lens.
    - Returns `None` if alignment < 70 or all allowed domains are already present.
- **Why:** M8 AIA-3; PRD F5 / M8 AIA checkbox: "Outside Voice lens (P2) constrained to 5 domains".
- **Done when:** Returns an allowed domain recommendation when user alignment is high, `None` otherwise.

---

**Step 4 — Wire `leverage_features` into `recompute_user_gap`**

- **What:** `services/api/app/services/identity/recompute.py`
  - Add optional `calendar_events: Optional[List[dict]] = None` parameter to `recompute_user_gap`.
  - Call `extract_leverage_features(calendar_events, declared_self, ref_time)` if `calendar_events` provided.
  - Pass `leverage_features` into `build_decision_packet`.
- **Why:** M8 AIA-1; enables end-to-end DecisionPacket generation with leverage features.
- **Done when:** `recompute_user_gap(…, calendar_events=[…])` attaches `leverage_features` to `DecisionPacket`.

---

**Step 5 — Tune Seed Targets for Projector Legibility**

- **What:** Review `services/api/tests/fixtures/aarav_seed.py` and `constants.py`.
  - Verify that completing a `mission_completed` event drops Aarav's Gap score by at least **8 to 15 points**, making the live demo chart jump clearly visible to an audience on a projector.
  - Adjust default event values if needed so score shifts are sharp and non-ambiguous.
- **Why:** M8 AIA-2; M8 checkbox: "Tune seed targets so Gap movement is projector-legible".
- **Done when:** Baseline Gap vs. completion event Gap delta is ≥ 8 points in tests.

---

### 5.3 Integration / wiring

**Step 6 — Update `services/identity/__init__.py` Exports**

- Export `LeverageFeatures`, `extract_leverage_features`, `OutsideVoiceRecommendation`, `evaluate_outside_voice_lens`.
- **Done when:** All M8 symbols import cleanly from `app.services.identity`.

---

### 5.4 Tests

**Step 7 — M8 Unit Test Suite**

- **What:** `services/api/tests/identity/test_m8_hardening.py`
  - **Test 1 (Leverage features extraction):** Calendar event 3 days away ("College Talk") produces `has_upcoming_event=True`, `days_until_event=3.0`, `suggested_prep_type="rehearsal"`.
  - **Test 2 (Leverage features past/far event):** Event 10 days away or past event returns `None`.
  - **Test 3 (DecisionPacket carries leverage_features):** `recompute_user_gap` with calendar event populates `packet.leverage_features`.
  - **Test 4 (Outside Voice lens allowed domains):** `evaluate_outside_voice_lens` returns a domain strictly in `ALLOWED_DOMAINS`.
  - **Test 5 (Outside Voice lens low alignment):** Returns `None` when Gap score is high (alignment < 70%).
  - **Test 6 (Demo Gap legibility):** Aarav seed + `mission_completed` event yields a Gap reduction of ≥ 8 points.
- **Done when:** `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 56 tests green.

---

## 6. Dependencies & sequencing

### What AIA needs from Backend (M8)
- Calendar event dictionaries (passed in as plain parameter list; AIA does not call DB or external APIs).

### What AIS needs from AIA (M8)
- `DecisionPacket.leverage_features` to schedule leverage interventions before calendar events.

### Suggested sequencing within AIA M8
```
Sync main → cut aia → cut m8 feature branch from aia
  → Step 1 (packet.py extension)
  → Step 2 (leverage_features.py)
  → Step 3 (outside_voice.py)
  → Step 4 (recompute.py wiring)
  → Step 5 (seed tuning verification)
  → Step 6 (__init__ exports)
  → Step 7 (Tests)
```

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Calendar event timestamps in different timezones | Convert all datetime comparisons to UTC using `timezone.utc`. |
| Seed Gap delta too small for demo projector | Explicitly test for ≥ 8 point delta in Test 6; tune `value` or `baseWeight` if needed. |
| Outside Voice lens suggested domain already present | Filter out all `[attr.id for attr in declared_self.attributes]` from recommendations. |

---

## 8. Open Questions

1. **Calendar event input format:** Should `extract_leverage_features` accept a list of plain `dict` objects (e.g. `{"id": "c1", "title": "Talk", "start_time": "...", "attribute_id": "public_speaker"}`) or a dedicated Pydantic model?
   - Recommendation: **Accept dict or Pydantic model transparently** using `getattr`/`.get()` accessors for maximum compatibility with Backend.

2. **Projector legibility threshold:** Is an **8–15 point Gap score shift** on mission completion sufficient for the demo visual peak?
   - Recommendation: **Yes** — on a 0–100 scale, a 10-point drop (e.g. 58 → 48) is instantly recognizable on a dashboard line/gauge chart.

3. **Outside Voice lens domain set:** The 5 domains are `["public_speaking", "software_building", "writing", "networking", "mindfulness"]`. Are these agreed upon for P2?
   - Recommendation: **Yes** — aligns with techstack/PRD examples.

---

## 9. Execution checklist (after you approve)

- [ ] Answer open questions (1–3)
- [ ] Approve this plan
- [ ] Agent cuts `m8` from `aia`
- [ ] Implement Steps 1–7 in order
- [ ] Run `ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q tests/identity/` → all 56 tests green
- [ ] Show `git status` + diff summary + proposed commit message → wait for human approval → commit
- [ ] Done report
