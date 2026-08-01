# TRELLIS — Agentic Coding Guidelines

**Single entrypoint for coding agents.**  
Version 1.0 · Status: locked for team use  

If a human says: *“Read `docs/guidelines.md`. My role is {aia|ais|backend}.”* — this file is the full operating manual. The agent must load the linked docs below, identify the correct milestone for that role, and **stop after producing an implementation plan + open questions** (unless the human already answered those questions and asked to execute).

---

## 1. Purpose

These guidelines exist so that:

1. One file boots the agent into the right context.
2. Work stays scoped to **one role** and **one milestone** at a time.
3. Humans approve plans, open-question answers, branch actions, and **every commit**.
4. AIA, AIS, and Backend can move in parallel and merge cleanly via `docs/milestones.md` gates.

UI/UX is out of scope for this document and does not follow this agent loop.

---

## 2. Document Hierarchy (read in this order)

| Order | File | What the agent takes from it |
|---|---|---|
| 1 | **`docs/guidelines.md`** (this file) | Workflow, branching, commit rules, plan format, hard constraints |
| 2 | **`docs/problem.md`** | Hackathon problem statement (why Trellis exists) |
| 3 | **`docs/prd.md`** | Product requirements, P0/P1/P2, acceptance criteria, demo script |
| 4 | **`docs/techstack.md`** | Architecture, folders, providers, APIs, data stores |
| 5 | **`docs/milestones.md`** | Role ownership, M0–M8 checkboxes, merge gates, cut rule |

**Conflict rule:** Product intent → `prd.md` / `problem.md`. Architecture → `techstack.md`. Who builds what when → `milestones.md`. How the agent behaves → **this file wins**.

Do not invent features outside the PRD. Do not invent stack choices outside the techstack. Do not expand scope past the current milestone’s checkboxes for the stated role.

---

## 3. Roles

The human will state exactly one role:

| Role token | Meaning | Primary ownership |
|---|---|---|
| `aia` | AI Identity Architecture | Twin, Gap math, interview/evolution agents, bottleneck + DecisionPacket |
| `ais` | AI Systems / Curation | LangGraph coordinator, curator/stack, retrieval usage, guardian/reflection nodes |
| `backend` | Backend platform | FastAPI, schemas, DB, evidence/stack/ledger APIs, seeds, provider DI shells |

Full ownership tables live in `docs/milestones.md`. **Never implement another role’s checkboxes** unless the human explicitly expands scope.

---

## 4. Default Agent Session Flow

### Phase A — Plan only (default first message)

When the human provides a role and asks the agent to follow these guidelines:

1. Read all five docs in §2.
2. Infer the **current milestone** for that role:
   - Prefer the milestone the human names (`M0`, `M1`, …).
   - If unnamed: find the lowest milestone in `milestones.md` whose **that role’s** checkboxes are not done in the repo (inspect code/git). If the repo is empty/greenfield → **M0**.
3. Produce an **Implementation Plan** in the exact format in §6.
4. Include **Open Questions** the human must answer before coding.
5. **Stop.** Do not create branches, edit files, or commit until the human answers and says to proceed (e.g. “approved, execute”).

### Phase B — Execute after answers

When the human answers open questions and approves the plan:

1. Restate any plan deltas implied by the answers (short).
2. Follow branching rules in §5 (checkout/create feature branch from role branch).
3. Implement **only** that role’s checkboxes for that milestone.
4. Run relevant tests/linters when possible.
5. When ready to commit: follow §7 (show message → wait for approval → commit).
6. After implementation, produce a short **Done report** (§8). Do not start the next milestone unless asked.

### Phase C — Next milestone

Only when the human asks for the next milestone: return to Phase A for `M{N+1}`.

---

## 5. Git Branching Model

Authoritative topology:

```text
dev                          ← team integration branch
├── backend                  ← role long-lived branch
│   ├── m0
│   ├── m1
│   ├── m2
│   └── …
├── aia
│   ├── m0
│   ├── m1
│   └── …
└── ais
    ├── m0
    ├── m1
    └── …
```

### Rules

1. **`dev`** is the integration trunk for Backend / AIA / AIS merges.
2. Each engineer has a **role branch** named exactly: `backend`, `aia`, or `ais`, created from `dev` and kept up to date with `dev` when starting a new milestone.
3. All implementation for a milestone happens on a **feature branch** named exactly: `m0`, `m1`, `m2`, … `m8` (lowercase, no role prefix — the role is already the parent branch).
4. Before coding a milestone, the agent must:
   - Ensure the role branch exists (create from `dev` if missing, **after human approval**).
   - `git checkout <role-branch>` and update from `dev` if the human wants (`git merge dev` or rebase only if human asks).
   - Create/checkout `m{N}` **from the role branch**:  
     `git checkout -b m{N}` (or checkout existing `m{N}`).
5. **Do not commit directly to `dev` or to the role branch** during milestone work. Commits go on `m{N}`.
6. Merging `m{N}` → role branch, and role branch → `dev`, is a **human-gated** step. The agent may prepare the PR/merge commands but must not merge without explicit approval.
7. Milestone merge readiness into `dev` still follows `milestones.md` Merge Gates (usually Backend → AIA → AIS).

### Example (Backend, M1)

```text
git checkout dev
git pull   # if remote exists and human wants
git checkout backend          # or create: git checkout -b backend
git merge dev                 # only if human asked to sync
git checkout -b m1            # feature branch for milestone 1
# ... implement ...
# commit only after §7 approval
# later (human approval): merge m1 → backend → (team) backend → dev
```

---

## 6. Implementation Plan Format (mandatory)

The agent’s Phase A output **must** use this structure:

```markdown
# Implementation Plan — {ROLE} — M{N}

## 1. Context
- Role: …
- Milestone: M{N} — (title from milestones.md)
- PRD features touched: (F# …)
- Techstack modules touched: (paths / layers)
- Goal (1–2 sentences): …

## 2. Scope (in)
- Bullet list mapped 1:1 to this role’s checkboxes in milestones.md for M{N}
- Note P0 vs P1 if relevant

## 3. Scope (out)
- Explicitly list other roles’ work this milestone that we will NOT do
- P2 / cut-rule items deferred

## 4. Current repo state
- What already exists for this milestone
- Assumptions if code is missing

## 5. Detailed work plan
Numbered steps. Each step must include:
- **What** will be created/changed (files/modules)
- **Why** (link to PRD acceptance or milestone checkbox)
- **How** (approach, interfaces, data flow)
- **Done when** (testable acceptance for that step)

Group steps as:
### 5.1 Contracts / schemas
### 5.2 Core logic
### 5.3 Integration / wiring
### 5.4 Seeds / fixtures (if any)
### 5.5 Tests
### 5.6 Demo / merge-gate verification

## 6. Dependencies & sequencing
- What must exist from other roles (stubs vs real)
- Suggested wait / stub strategy if blocked
- Merge gate checklist copied from milestones.md for this M

## 7. Risks
- Technical risks + mitigations (quota, empty stack, schema drift, etc.)

## 8. Open Questions
Numbered questions that **block execution**.  
Each question should be concrete (default recommendation allowed).

Example shape:
1. …?  
   - Recommendation: …
2. …?

## 9. Execution checklist (after you approve)
- [ ] Answer open questions
- [ ] Approve this plan
- [ ] Agent creates/checks out `{role}` → `m{N}`
- [ ] Implement
- [ ] Show commit message(s) → wait for approval → commit
- [ ] Done report
```

### Open questions quality bar

Ask only what changes implementation. Prefer recommendations. Typical topics:

- Env keys / provider choice for local (Gemini vs fixture)
- Stub vs wait for the other role’s contract
- Seed persona details / demo path assumptions
- Sync strategy with `dev` before branching
- Whether Neo4j/Qdrant/Celery are in or stubbed this milestone (per techstack hackathon notes)

Do **not** ask vague questions like “should we use best practices?”

---

## 7. Commit Rules (hard)

1. **Never commit unless the human explicitly asks to commit** or answers “yes” to a proposed commit.
2. **Before every commit**, the agent must show:
   - `git status`
   - `git diff` summary (staged/unstaged)
   - The **exact proposed commit message**
   - File list to be included
3. Wait for explicit approval of that message (or an edited message from the human).
4. Only then run `git add` / `git commit`.
5. Prefer one logical commit per milestone slice; split if the human asks.
6. Commit message style (Conventional-ish, role-tagged):

```text
[M{N}][{role}] short imperative summary

Optional body: why, merge-gate note, PRD F# refs.
```

Example:

```text
[M1][backend] Add idempotent evidence ingest and Aarav seed loader

Implements F2 ingest path for milestone merge gates.
```

7. **Never** `--no-verify`, force-push, or amend unless the human explicitly orders it (and amend rules in the user’s git policy still apply).
8. **Never** commit secrets (`.env`, API keys, credentials).
9. Do not push to remote unless the human explicitly asks.

---

## 8. Done Report Format (after execution)

```markdown
# Done — {ROLE} — M{N}

## Shipped
- …

## Tests run
- …

## Merge gates status (this role)
- [ ] / [x] against milestones.md

## Blocked on other roles
- …

## Suggested commit(s)
(If not yet committed: show message and wait)

## Next
- Ready for human merge `m{N}` → `{role}` when approved
- Next plan available on request for M{N+1}
```

---

## 9. Hard Engineering Constraints (always on)

Agents must obey these even if a shortcut looks faster:

1. **Deterministic core:** Gap, Alignment, Create:Consume, ledger failure thresholds (3 dismissals / 14 days), capacity tiers, Moment Detector rules — no LLM arithmetic.
2. **One evidence path:** all signals → `EvidenceEvent` → pipeline. No pre-scored Gap inserts from the simulator.
3. **Provider adapters only:** no direct Gemini / Bedrock / Tavily SDK imports outside `providers/`.
4. **Honesty labels:** `simulated: true` and source badges (`Live web` / `Cached web` / `Curated fallback`) must not be lied about.
5. **Structured I/O:** LLM outputs validated against schemas; invalid → repair or fail safely.
6. **Tiered latency:** Tier-0 paths must not call LLMs or block on search.
7. **Role isolation:** do not “helpfully” rewrite another role’s modules; propose contract changes in Open Questions instead.
8. **Hackathon cut rule:** if human says we’re behind, prefer `milestones.md` § Cut Rule over new P2 work.
9. **Match folder layout** in `techstack.md` §24 unless human approves a deviation.
10. **No drive-by refactors** outside the milestone plan.

---

## 10. What the Agent Must Not Do

- Skip the plan phase on a new milestone/role session.
- Implement M{N+1} while finishing M{N}.
- Create branches or merge to `dev` without approval.
- Commit without showing the message and receiving approval.
- Change `prd.md` / `techstack.md` / `milestones.md` / `guidelines.md` unless the human asks.
- Build UI screens (UI/UX owner).
- Add real Instagram/Twitter DOM injection, full OAuth MCP, or other PRD non-goals.

---

## 11. Human Prompt Templates

### Start planning

```text
Read docs/guidelines.md and follow it.
Role: backend
Milestone: M0
Produce the implementation plan and open questions only.
```

(Omit `Milestone:` to let the agent infer the lowest incomplete one.)

### Approve and execute

```text
Open question answers:
1. …
2. …

Plan approved. Execute on branch per guidelines.
```

### Commit

```text
Show status/diff and a commit message for approval.
```

(or after the agent proposes one: `Yes, commit with that message.`)

### Next milestone

```text
Read docs/guidelines.md. Role: aia. Plan M2 only.
```

---

## 12. Coordination Notes for Parallel Work

- Schema changes are **Backend-owned**. AIA/AIS propose fields in Open Questions; Backend lands them on `backend/m{N}` first when possible.
- If Backend M{N} is not in `dev` yet, AIA/AIS may code against local stubs that mirror `milestones.md` / `techstack.md` contracts — call this out in the plan.
- Integration merge to `dev` should wait for that milestone’s Merge Gates, not for perfect P1 polish.
- When in doubt, optimize for the **demo script** in `prd.md` §13.

---

## 13. Quick Compliance Checklist (agent self-check)

Before ending a planning turn:

- [ ] Read problem, prd, techstack, milestones
- [ ] Plan is for one role + one milestone
- [ ] Steps are detailed with done-when criteria
- [ ] Open questions are blocking and concrete
- [ ] No code/branch/commit yet

Before ending an execution turn:

- [ ] On `{role}` → `m{N}` (not `dev`)
- [ ] Only in-scope files changed
- [ ] Constraints in §9 respected
- [ ] Commit attempted only after message approval
- [ ] Done report produced

---

*End of guidelines. Humans: point agents here first. Agents: this file is law for process; product/architecture docs are law for content.*
