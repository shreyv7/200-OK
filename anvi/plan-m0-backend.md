# Implementation Plan — Backend — M0

## 1. Context
- Role: **backend**
- Milestone: **M0 — Scaffold & Frozen Contracts**
- PRD features touched: Infra only (no F# yet); enables F1–F11 downstream
- Techstack modules touched: API Layer, Data Layer (Postgres/Redis), AI Infrastructure Layer stubs, folder structure per `techstack.md` §24
- Goal: Stand up a bootable FastAPI skeleton with frozen Pydantic contracts, DB/migrations scaffolding, and CI, so AIA and AIS can build against stable schemas without waiting on backend internals.

## 2. Scope (in)
Per `milestones.md` M0 → Backend checkboxes:
- [ ] FastAPI app skeleton: `/healthz`, `/readyz`, config, DI container
- [ ] Postgres + Alembic bootstrap; Redis optional stub
- [ ] Pydantic v2 schemas: `EvidenceEvent`, `DeclaredSelf`, `GapBreakdown`, `BottleneckPacket`, `DecisionPacket`, `IdentityStack`, `LedgerEntry`, `InterventionVariant`
- [ ] Clerk JWT dependency stub (accept demo token / bypass flag for local)
- [ ] Folder layout matching `techstack.md` §24
- [ ] Seed script entrypoint (empty runners OK)
- [ ] GitHub Actions: lint + pytest smoke

All P0 (M0 has no P1/P2 split — it's pure infra gate).

## 3. Scope (out)
- AIA: `services/decision/`, `services/identity/scoring/`, Gap formula constants, Declared Self extraction TypedDict, formula unit tests — **not our job**.
- AIS: LangGraph empty graph stub, `SearchProvider`/`LLMProvider` interface *consumers*, Identity Stack assembly signature, prompt folder skeleton — **not our job**.
- No real business logic (no Gap math, no evidence ingest endpoint — that's M1).
- No real LLM/search provider implementations — only DI shells/interfaces for others to implement against.
- No Neo4j/Qdrant/Celery wiring — deferred until a later milestone actually needs them.
- No UI.

## 4. Current repo state
- `200-OK/` is the repo root; git already initialized with remote `origin` (`github.com/shreyv7/200-OK`), trunk branch `main` (2 commits: scaffold + docs). No `services/`, no `apps/` yet.
- **Deviation from guidelines.md §5:** the guidelines describe trunk as `dev`, but this repo's actual trunk is `main`. Treating `main` as the integration trunk in place of `dev` for this repo; role branch `backend` and feature branch `m0` are created from `main`.

## 5. Answered open questions (locked for execution)
1. **Pydantic version:** v2 (per techstack.md §5.1, the architecture source of truth).
2. **Repo root:** `200-OK/` is the repository root.
3. **Database:** PostgreSQL + SQLAlchemy + Alembic, run locally via Docker (not Supabase — techstack.md is authoritative over prd.md's hackathon-speed suggestion).
4. **Neo4j/Qdrant scope:** M0 creates only an empty `repositories/` package placeholder; no Neo4j/Qdrant interfaces yet.

## 6. Detailed work plan

### 6.1 Contracts / schemas
- `services/api/app/schemas/`: `evidence.py`, `identity.py`, `gap.py`, `bottleneck.py`, `decision.py`, `stack.py`, `ledger.py` — Pydantic v2 models mirroring `prd.md` §7 (`EvidenceEvent`) and §9 (Gap breakdown fields, `BottleneckPacket` shape). Fields loose/optional where formulas aren't implemented yet.
- Done when: schemas import cleanly, round-trip serialization tests pass.

### 6.2 Core logic
- `core/config.py` (Pydantic `BaseSettings`), `core/di.py` (DI wiring DB session, repos, provider stubs), `core/security.py` (Clerk JWT stub honoring `AUTH_BYPASS` env flag for local dev).
- `main.py`, `api/health.py`: `/healthz` (liveness), `/readyz` (checks DB connection).
- Done when: app boots locally with `AUTH_BYPASS=true`; health endpoints return correct codes.

### 6.3 Integration / wiring
- `models/` (SQLAlchemy base + minimal tables: users, evidence_events, twin_versions), `alembic.ini` + `migrations/` initial revision.
- `docker-compose.yml` (Postgres + Redis services).
- `providers/`: abstract `LLMProvider`, `SearchProvider`, `EmbeddingProvider` (no vendor SDK imports).
- `repositories/` placeholder package only (per open question 4).
- Full folder scaffold per `techstack.md` §24 (agents/graphs, agents/nodes/*, integrations/mcp/*, workers/, prompts/, config/) — empty `__init__.py` files only, each annotated with owning role.
- Done when: `alembic upgrade head` runs clean; folder tree matches techstack.md §24.

### 6.4 Seeds / fixtures
- `workers/seed.py` stub entrypoint (prints "not yet implemented", exits 0). Real seeding is M1 scope.

### 6.5 Tests
- `tests/test_health.py`, `tests/test_schemas.py` using `TestClient`.
- Done when: `pytest` green.

### 6.6 Demo / merge-gate verification
- `.github/workflows/backend-ci.yml`: lint + pytest.
- Manual verification against Merge Gates 1–3 (`milestones.md` M0): API up + healthy; schemas import standalone for AIA/AIS; no Gemini/Tavily SDK imports outside `providers/`.

## 7. Dependencies & sequencing
- Merge order: Backend → AIA → AIS (per milestones.md).
- AIA/AIS M0 work has no hard blocking dependency on this branch being merged, but need the schemas package committed on `backend`/`m0` to write contract tests against.

## 8. Risks
- Local Postgres/Redis friction on Windows → mitigated via `docker-compose.yml`.
- Clerk not configured yet → `AUTH_BYPASS` flag for local, real JWKS verification deferred (documented, not implemented in M0).
- Folder-stub scope creep into AIA/AIS logic → explicitly avoided; only empty `__init__.py` placeholders created outside backend's own modules.

## 9. Execution checklist
- [x] Answer open questions
- [x] Approve plan
- [ ] Agent creates/checks out `backend` → `m0` (from `main`)
- [ ] Implement
- [ ] Show commit message(s) → wait for approval → commit
- [ ] Done report
