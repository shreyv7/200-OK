# Team Agent Prompts — M1

Copy-paste the block for your role into Cursor. **Plan first** (Phase A); say **"approved, execute"** only after reviewing the plan.

---

## Everyone — sync before starting

```bash
git fetch origin --prune
git checkout main && git pull origin main
git checkout dev && git pull origin dev
git checkout <YOUR_ROLE>          # backend | aia | ais
git merge dev                     # get integrated M0 baseline
git checkout -b <YOUR_ROLE>-m1    # e.g. backend-m1, aia-m1, ais-m1
```

**Branches on GitHub:** `main` (stable integrated), `dev` (integration trunk), `<role>`, `<role>-m0`, `<role>-m1`.

**Do not commit to `main`, `dev`, or your role branch directly.** Commits go on `<role>-m1` only.

---

## Backend agent — M1

```text
Read docs/guidelines.md and follow it.
Role: backend
Milestone: M1

Context:
- M0 is merged on main/dev. Schemas in app/schemas/ are Backend-owned (PRD §7 EvidenceEvent).
- Read docs/integration-notes.md for cross-role seams.
- Your M1 scope is ONLY the Backend checkboxes in docs/milestones.md § M1.

Produce the implementation plan and open questions only.
Do not start coding until I approve.

After approval:
- Work on branch backend-m1 (cut from backend, synced with dev).
- Implement POST/GET /api/v1/evidence, evidence.created emission, MCP fixture adapter,
  simulator inject (dev-only), Aarav 21-day seed, user+capacity row.
- Run: cd services/api && AUTH_BYPASS=true ENV=local DATABASE_URL=sqlite:///./ci_test.db pytest -q
- CI: .github/workflows/backend-ci.yml runs on push to backend-m1 and PRs to dev/main.
- Merge order: Backend merges first → then AIA → then AIS.
```

---

## AIA agent — M1

```text
Read docs/guidelines.md and follow it.
Role: aia
Milestone: M1

Context:
- M0 is merged on main/dev. Consume schemas from app/schemas/ — do not duplicate EvidenceEvent.
- Gap math lives in app/services/identity/scoring/ (AIA-owned). Never let LLMs compute Gap.
- Read docs/integration-notes.md and docs/milestones.md § M1 AIA checkboxes only.

Produce the implementation plan and open questions only.
Do not start coding until I approve.

After approval:
- Work on branch aia-m1 (cut from aia, synced with dev).
- Implement: evidence enrichment (identityAttributeIds / a_ik), Revealed Self aggregate builder,
  twin read model, dead-letter rejection for invalid events.
- Do not implement Backend HTTP routes or AIS curation.
- Run: cd services/api && pytest -q tests/identity/
- Wait for Backend M1 evidence ingest contract if not merged yet; stub only with labeled mirrors.
- Merge after Backend M1 lands on dev.
```

---

## AIS agent — M1

```text
Read docs/guidelines.md and follow it.
Role: ais
Milestone: M1

Context:
- M0 is merged on main/dev. Migrate off app/agents/_contracts.py TEMP mirror → app/schemas/.
- Read shrey/plan-ais-m1.md and docs/milestones.md § M1 AIS checkboxes only.

Produce the implementation plan and open questions only.
Do not start coding until I approve.

After approval:
- Work on branch ais-m1 (cut from ais, synced with dev).
- Implement: evidence.created hook (no-op Coordinator), DecisionPacket placeholder,
  fixture stack invalidation flag only (no ranking), Reflection/Ledger evidence-ID intake.
- No vendor SDK imports outside providers/. No pre-scored Gap in simulator path.
- Run: cd services/api && pytest -q
- Merge after Backend + AIA M1 on dev.
```

---

## PR / merge checklist (human)

- [ ] Merge gates in `docs/milestones.md` § M1 pass for your role
- [ ] `pytest -q` green under `services/api`
- [ ] PR title: `[M1][<role>] short summary`
- [ ] PR body lists merge gates checklist
- [ ] Merge `<role>-m1` → `<role>` → open PR to `dev` (order: backend, then aia, then ais)
- [ ] After all three on `dev`, merge `dev` → `main`
