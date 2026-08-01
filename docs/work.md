# WORK.MD — Make Trellis Real (No More Simulations)

**Derived from:** `docs/improvisedplan.md`, `docs/improvisedplan2.md`, `docs/improvisedplan3.md`, `docs/prd.md`, `docs/milestones.md`
**Team:** 4 people — **A**, **B**, **C**, **D**
**Repo:** `github.com/shreyv7/200-OK` · Backend: `services/api` (FastAPI) · Frontend: `raghav/` (Vite / TanStack Start)

---

## 0. The one-line mission

Backend M0–M8 is done, but everything runs on fakes by default: `AUTH_BYPASS=true`, `demo-user-aarav`, `FakeLLMProvider`, `FakeSearchProvider`, fixture MCP adapters, and seeded 21-day history. This document is the task list to replace **every** simulated path with real users, real Gemini (+ optional Bedrock failover), real Tavily/YouTube retrieval, and real OAuth-synced evidence — while keeping fakes **only** for CI/tests.

### Ground rules (apply to every task)

1. Evidence never bypasses the unified `EvidenceEvent` pipeline (`normalize → validate → dedupe → score → persist`).
2. Gap / Alignment / Create:Consume / capacity tiers / Moment Detector stay **deterministic** — LLMs never touch these numbers.
3. All LLM/search/embedding calls go through `providers/` adapters only — no direct SDK imports in `agents/` or `services/`.
4. `simulated: true` and source badges stay in the schema — but their meaning becomes "genuine fallback only," not "everything."
5. Tests/CI keep running on fake providers. **Staging/prod never run** `AUTH_BYPASS=true`, `LLM_PROVIDER=fake`, or `SEARCH_PROVIDER=tavily`-off.
6. No seeding in production. New users get real onboarding, not Aarav.

---

## 1. Task Split

Ownership is vertical: each person owns their slice end-to-end (backend + any FE wiring their slice needs). A is also the merge captain (see §3).

---

### PERSON A — Real Auth, Real Users, Merge Captain

Goal: kill `demo-user-aarav`. Real multi-user signup/signin with Clerk + Google OAuth; every row in the DB scoped to a real `user_id`.

- **A1. Clerk JWT verification (backend).** Replace the `501` branch in `app/core/security.py` with real JWKS verification (`PyJWT[crypto]` or `python-jose`): fetch Clerk JWKS, verify signature/issuer/audience, extract `sub`. Keep `auth_bypass` working only when `ENV=local` (for pytest).
- **A2. User provisioning.** On first-seen `sub`, upsert a `User` row keyed by `clerk_subject`. Migration: add `email`, `last_login_at`, unique index on `clerk_subject`. Remove `demo_user_id` from every non-test code path.
- **A3. Ownership audit (highest-risk task in this file).** Grep every usage of `get_current_user_id` and `demo_user_id` across `app/repositories/` and `app/services/`; confirm every read/write filters by the authenticated `user_id`. No endpoint may accept `user_id` from body/query when it's derivable from the token. Write an integration test that creates two users and asserts zero cross-contamination (independent gaps, ledgers, stacks).
- **A4. Frontend auth.** Install the Clerk SDK in `raghav/`, wrap the app root in `<ClerkProvider>`, add `/login` + `/signup` routes, enable Google as a social connection in the Clerk dashboard, protect `/dashboard` `/feed` `/ledger` `/report`, attach the session JWT to every API call, replace the hardcoded "Aarav" sidebar card with the real signed-in user.
- **A5. Per-user onboarding.** New signup → `/onboarding` → Mirror Interview → Declared Self v1 for **that** user. No Aarav seed anywhere in the flow. Keep the seed script only behind an explicit dev/demo flag.
- **A6. CORS + env config.** Add FRONTEND dev/prod origins to FastAPI; document `local` / `staging` / `prod` env matrices (which flags are legal where).

**Done when:** a brand-new Google account can sign up, complete the interview, and see a Gap score with zero seed data; two users see fully independent data; pytest still passes with `auth_bypass` locally.

---

### PERSON B — Real LLM Intelligence (Gemini primary, Bedrock failover)

Goal: flip `llm_provider=fake` → `gemini` as the runtime default and make every agent path survive real-world LLM behavior (latency, rate limits, malformed JSON).

- **B1. Flip the default.** Real `GEMINI_API_KEY`s; `LLM_PROVIDER=gemini` in non-test envs (`app/core/di.py`). Keep `fake` as the pytest default — don't touch test config.
- **B2. Key rotation facade.** If `GeminiLLMProvider` wraps a single key, extend it: key pool, round-robin, cooldown on 429/5xx, per-key health metrics.
- **B3. Bedrock failover.** Add `boto3`; implement automatic in-path failover in `get_llm_provider` when the Gemini pool is exhausted (not a manual env switch). Test with a staged kill of the Gemini keys. (If we don't buy Bedrock yet, ship the failover code behind a flag with a stub test.)
- **B4. Harden every live LLM path** against real failure modes (timeout, partial JSON, refusals) with the existing repair/reject/fallback chain:
  - F1 Mirror Interview extraction (<20s, structured Declared Self)
  - Bottleneck diagnosis (fixed taxonomy + ≥2 cited evidence signals)
  - F8 Weekly Becoming Report (<10s, from the signed-in user's **live** DB rows)
  - F11 Identity Evolution (propose from real evidence; accept → new twin version; never silent apply)
  - Guardian downgrade explanations
- **B5. Cost guardrails.** Per-user daily LLM call cap + token usage logging.
- **B6. Prompt registry.** Consolidate scattered prompts under `prompts/` with versions; a single `generateStructured()` facade — no ad-hoc LLM calls.

**Done when:** all agent runs execute on Gemini for a real signed-in user; killing Gemini keys fails over to Bedrock (or the flagged stub) with no user-facing error; malformed output still falls back safely; CI still runs on fakes.

---

### PERSON C — Real Retrieval, Live Curation, Background Jobs

Goal: the Identity Stack shows **Live web** / **Cached web** badges in a normal session, not "Curated fallback," and Tier-2 work runs off the request path.

- **C1. Tavily live.** Production `TAVILY_API_KEY`; `SEARCH_PROVIDER=tavily` in non-test envs. Chain stays: cache → Tavily (1.5s timeout) → curated fallback, badges honest at every step.
- **C2. YouTube Data API.** Real video metadata when a lens needs media (Next Step / knowledge lens).
- **C3. Next Step lens (F5) real.** Developmental-fit ranking over live candidates instead of fixture missions; Opportunity lens with live local search + labeled fallback.
- **C4. Celery + Redis worker.** Add a `worker` service to `docker-compose.yml` (`celery -A app.workers worker` + beat). Convert `app/workers/prewarm.py` and inline Tier-2 curation into Celery tasks with retry/backoff. Verify: stopping the worker leaves Tier-0/1 (dashboard, capacity slider, dismiss logging) fully working.
- **C5. Trigger-driven stack refresh.** Background refresh on dismiss / complete / capacity change / identity confirm — no more one-shot seeded stack. Pre-warm the prepared intervention for the Catch moment with live retrieval.
- **C6. Rate limiting + observability basics.** Redis-backed rate limits on evidence ingest and LLM-triggering endpoints; `trace_id`/`user_id`/`run_id` propagation API → Celery → agents → providers; token/cost metrics surfaced (with B).

**Done when:** a normal session shows at least one Live/Cached web badge; retrieval failure still yields a labeled fallback stack; sync/refresh jobs run on schedule without a user request; a burst of POSTs from one user throttles without hurting others.

---

### PERSON D — Real Evidence: OAuth Connectors (Calendar, GitHub) + Token Infra

Goal: the Revealed Self updates from the user's actual digital life. Replace `FixtureGithubAdapter` and seeded `calendar_events` with real OAuth-synced data. Depends on A1–A2 (real users must exist before per-user tokens mean anything) — build token infra and adapters against `auth_bypass` locally while A lands.

- **D1. Token infra first (shared for all providers).** New `integration_connections` table: `id, user_id, provider, access_token_encrypted, refresh_token_encrypted, scopes, connected_at, revoked_at`. Fernet/KMS encryption at rest via `cryptography`. CI check + repo-layer test asserting the stored column is ciphertext; no token ever in logs or API responses.
- **D2. Integrations router.** `app/api/integrations.py`: `GET/POST /api/v1/integrations/{provider}/connect` (OAuth redirect + callback), `.../status`, `DELETE` (revoke → ingest stops immediately, history preserved). Transparent token refresh; refresh failure → mark revoked + FE reconnect prompt, never silent stale data.
- **D3. Google Calendar connector (first — same OAuth vendor as sign-in).** `google-api-python-client` + real `normalize(raw) → EvidenceEvent` in `app/integrations/mcp/calendar/adapter.py`. Real upcoming events power F9 leverage triggers and `GET /api/v1/calendar/plan-view` (replace the seeded repository). Pre-event intervention scheduling via C's Celery beat.
- **D4. GitHub connector (second — highest-value creation signal).** OAuth app; sync commits/PRs → `creation` evidence through the same pipeline, `simulated=False`. Backfill + incremental sync as Celery jobs (with C). Acceptance: a real commit by a connected account appears as real evidence and visibly moves the Gap score.
- **D5. Honesty flag audit.** Confirm `simulated` in `app/services/evidence/service.py` is provider-driven, not hardcoded; connector events are `False`, fixtures/simulator stay `True`.
- **D6. Frontend connections UI.** Settings/integrations page in `raghav/`: connect / status / disconnect per provider, reconnect prompts, honesty badges on evidence sources. Simulator panel demoted to dev/QA-only.

**Done when:** connect Calendar → real events in plan view; disconnect → ingest stops instantly; a live GitHub commit changes the Gap with no simulator inject; no plaintext token anywhere.

---

### Deferred (nobody picks these up until the above is merged)

- Qdrant + real embeddings + real Growth Partner Match (F10) — needs a real user base first.
- User-submitted Growth Stories, verified mentors, reputation (Wave D / P2).
- Notion / Drive / YouTube-history connectors, Neo4j graph.
- Browser extension / third-party DOM injection — still a hard non-goal.

---

## 1.5 Manual setup each person must do themselves (agents can't do these)

These are human-only steps: account creation, dashboard clicks, billing, and pasting secrets into your local `.env`. Your agent will pause and hand you a checklist when it hits one of these (see the prompt in §4, step 5) — but you can get ahead by doing them early. **All values go into your local gitignored `.env`; never into chat, commits, or `.env.example`.**

| Owner | Manual step | Produces (env vars) |
|---|---|---|
| **A** | Create a Clerk account + application; enable Google as a social connection in the Clerk dashboard; set allowed origins/redirects for local + prod | `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `CLERK_JWKS_URL` |
| **B** | Create Gemini API key(s) in Google AI Studio (make 2–3 keys for the rotation pool) | `GEMINI_API_KEY`, `GEMINI_API_KEYS` (pool) |
| **B** | (If we buy Bedrock) AWS account, enable Bedrock model access in the console, create IAM key | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| **C** | Create Tavily account + production API key | `TAVILY_API_KEY` |
| **C** | Google Cloud project: enable YouTube Data API v3, create API key | `YOUTUBE_API_KEY` |
| **D** | Same Google Cloud project: enable Calendar API, create OAuth client (web app), add the callback URL the code specifies, configure consent screen + scopes | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` |
| **D** | Register a GitHub OAuth App (Settings → Developer settings), set the callback URL the code specifies | `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET` |
| **D** | Generate a Fernet token-encryption key locally (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) and share it with A privately (password manager / DM, never git) | `TOKEN_ENCRYPTION_KEY` |

Exact scopes, redirect URLs, and any extra vars come from your agent when it implements the task — don't guess them ahead of time; the code defines them.

---

## 2. Suggested order & dependencies

```text
Week 1:  A1–A3 (auth core)   B1–B2 (Gemini live)   C1–C2, C4 (Tavily + worker)   D1–D2 (token infra, router)
Week 2:  A4–A6 (FE auth)     B3–B4 (failover+harden) C3, C5 (lenses, refresh)     D3 (Calendar)
Week 3:  A: merge captain     B5–B6                  C6                            D4–D6 (GitHub, FE)
```

Hard dependencies: **D3/D4 need A1–A2 merged** (real user rows). **C5 sync scheduling needs C4.** Everything else is parallel.

---

## 3. Branch / merge workflow

- Branch names: `feat/a1-clerk-jwt`, `feat/b3-bedrock-failover`, `feat/c4-celery-worker`, `feat/d3-calendar-oauth`, … (`feat/<task-id>-<slug>`).
- Everyone branches **from latest `main`**, pushes only to their feature branch, and opens a PR to `main`.
- **Person A is the only person who merges to `main`.** After each merge, A pulls `main` locally and runs the full build (`docker compose up --build`, pytest, `npm run build` in `raghav/`) to confirm the tree is green.
- B, C, D: `git pull origin main` at the start of every work session and before opening a PR (rebase your feature branch on `main` if it drifted).
- CI (existing lint + pytest workflow) must be green on the PR before A merges. Tests keep running on fake providers — never put real keys in CI.
- Never commit secrets. All real keys live in local `.env` (gitignored) and, later, the deploy platform's secret store.

---

## 4. CI/CD AGENT PROMPT (copy-paste this to your coding agent)

Replace `{PERSON}` and `{TASK_ID}` and paste the whole block:

```text
Read docs/work.md in this repo and follow it exactly.

I am Person {PERSON}. Implement task {TASK_ID} (e.g. A1, B3, C4, D2) from my section of work.md.

Process — do all of it, in order:

1. CONTEXT: Read docs/work.md fully, then read docs/prd.md, docs/milestones.md, and
   docs/guidelines.md §9 (hard engineering constraints — they all still apply).
   Inspect the current code in services/api and FRONTEND relevant to {TASK_ID}
   before writing anything.

2. BRANCH: git checkout main && git pull origin main, then create
   feat/{task-id-lowercase}-<short-slug> from main. All work happens on this branch.

3. IMPLEMENT: Only the scope of {TASK_ID} as written in work.md. Respect the ground
   rules in work.md §0: deterministic core untouched, providers/ adapters only,
   single EvidenceEvent pipeline, honest simulated/source badges, fakes stay the
   default for tests. No drive-by refactors of other people's tasks.

4. SECRETS: Never hardcode or commit API keys, OAuth client secrets, or tokens.
   Read them from environment settings; add placeholder entries to .env.example only.

5. MANUAL STEPS — ASK ME, DON'T ASSUME: Some parts of {TASK_ID} require things
   only a human can do (creating a Clerk account, generating a Gemini/Tavily API
   key, registering an OAuth app in Google Cloud / GitHub, enabling a social
   connection in the Clerk dashboard, AWS/Bedrock signup, adding secrets to my
   local .env). For each of these, follow this protocol:
   a. First check if you can do it yourself with your available tools — if you
      genuinely can, do it and tell me what you did.
   b. If you cannot, PAUSE and give me a numbered, step-by-step checklist of
      exactly what to do (which website, which buttons, which scopes/redirect
      URLs to enter — include the exact callback URL the code expects), and the
      exact .env variable names to paste each credential into.
   c. Then wait for me to confirm I've done it (or to paste the values into .env)
      before running any verification that depends on those credentials.
   d. Never invent placeholder credentials to fake a passing live test, and never
      echo real credential values back into chat, commits, or logs.
   Build and test as much as possible with fake providers first, so my manual
   setup is the last step, not a blocker for the whole task.

6. VERIFY: Run the backend test suite (pytest in services/api) and, if FRONTEND was
   touched, npm run build in FRONTEND. Add/extend tests for the new behavior using
   fake providers. Fix everything you broke. Show me the test output.

7. COMMIT & PUSH: Commit with message "[{TASK_ID}] <short imperative summary>"
   (body: what became real, which fake/seed path it replaced). Push the feature
   branch to origin. Do NOT push to main, do NOT merge, do NOT force-push.

8. PR: Open a pull request to main titled "[{TASK_ID}] <summary>" with a body
   containing: what was simulated before, what is real now, how to test it locally
   (exact commands + required env vars), and any new dependencies or migrations.
   Person A merges — you never merge.

9. REPORT: End with a short done-report: files changed, tests run, env vars the
   team must set, manual setup steps still pending on my side, and anything
   blocking (e.g. "needs A2 merged first").

If {TASK_ID} depends on an unmerged task (work.md §2), stop after the plan and
tell me instead of stubbing around it.
```

### For Person A after merging (local build ritual)

```text
git checkout main && git pull origin main
cd services/api && pip install -r requirements.txt && alembic upgrade head && pytest
cd ../../FRONTEND && npm install && npm run build
docker compose up --build   # full stack smoke: /healthz, sign-in, dashboard
```

### For B / C / D every session

```text
git checkout main && git pull origin main
git checkout <your-feature-branch> && git rebase main   # or merge main if rebase scares you
```

---

## 5. Definition of "real" (exit criteria for this whole file)

1. A new user Google-signs-in, completes the Mirror Interview, and sees a Gap score — **zero Aarav seed involved**.
2. The Identity Stack shows a **Live web** or **Cached web** badge in a normal session.
3. Connecting/disconnecting Calendar or GitHub changes evidence and the Gap without any simulator inject.
4. Weekly report and evolution proposals run on **Gemini** (Bedrock failover armed), grounded in that user's live DB state.
5. Staging/prod never run `AUTH_BYPASS=true` or fake providers as defaults; CI still does, on purpose.
6. Any remaining fallback data still carries honest badges — we label fallbacks, we don't fake liveness.
