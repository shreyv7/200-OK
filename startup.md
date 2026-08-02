# Trellis local startup

How to run the **frontend** (`raghav`) and **backend** (`services/api`) for local development.

| Service | Directory | Default URL |
|--------|-----------|-------------|
| Frontend (Vite / TanStack Start) | `raghav/` | http://localhost:8080 |
| Backend (FastAPI / Uvicorn) | `services/api/` | http://localhost:8002 |
| API docs | — | http://localhost:8002/docs |

The frontend proxies `/api/v1` → `http://localhost:8002` when `VITE_API_BASE` is unset.

---

## Prerequisites

- **Node.js** 20+ and npm
- **Python** 3.11+ (3.12–3.14 also work with the project venv)
- **Postgres** on `localhost:5432` (user/db/password: `trellis` / `trellis` / `trellis` by default)
- Optional: **Redis** on `localhost:6379` if you use workers / queues

Quick infra via Docker (from repo root):

```bash
docker compose up -d
```

Check `docker-compose.yml` for the exact Postgres/Redis services.

---

## One-time setup

### 1. Backend

```bash
cd services/api

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional, for tests

# Env file
cp .env.example .env               # if you don't already have .env
# Edit .env: DATABASE_URL, Clerk keys (if not using AUTH_BYPASS), Gemini, etc.

# Apply DB migrations
alembic upgrade head
```

Useful local `.env` flags (see `services/api/.env.example` and `docs/env-matrix.md`):

```bash
ENV=local
AUTH_BYPASS=false         # keep false for real multi-user sessions (Clerk → Postgres)
DATABASE_URL=postgresql+psycopg://trellis:trellis@localhost:5432/trellis
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
CLERK_JWKS_URL=https://YOUR_CLERK/.well-known/jwks.json
CLERK_ISSUER=https://YOUR_CLERK
CLERK_SECRET_KEY=sk_test_...
CLERK_AUTHORIZED_PARTIES=http://localhost:8080,http://127.0.0.1:8080
```

**Sessions:** With `AUTH_BYPASS=false`, each signed-in user gets a Clerk JWT; the API verifies it and upserts a row in Postgres `users` (via `GET /api/v1/me` and every authenticated request). Identity, onboarding, evidence, stack, ledger, and integrations are stored under that `user.id`.

`AUTH_BYPASS=true` is for pytest/smoke only — it collapses every request onto `DEMO_USER_ID` and must not be used for real product login.

### 2. Frontend

```bash
cd raghav

npm install

# Env file
cp .env.example .env               # if you don't already have .env
```

Minimum `raghav/.env`:

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
# Leave VITE_API_BASE unset to use the Vite proxy → localhost:8002
# VITE_API_BASE=http://localhost:8002/api/v1
```

---

## Everyday start (two terminals)

### Terminal A — backend (port 8002)

```bash
cd services/api
source .venv/bin/activate

# If schema changed since last pull:
alembic upgrade head

uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

Or without activating the venv:

```bash
cd services/api
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

Healthy check:

```bash
curl -s http://localhost:8002/docs | head -c 200
# or open http://localhost:8002/docs in a browser
```

### Terminal B — frontend (port 8080)

```bash
cd raghav
npm run dev -- --host 127.0.0.1 --port 8080 --strictPort
```

Open: **http://localhost:8080**

---

## Restart when something dies

Free the ports, then start again:

```bash
# macOS / Linux
for port in 8002 8080; do
  for pid in $(lsof -tiTCP:$port -sTCP:LISTEN 2>/dev/null); do
    kill "$pid" 2>/dev/null || true
  done
done
```

Then re-run Terminal A and Terminal B commands above.

If the port still shows “Address already in use”:

```bash
lsof -iTCP:8002 -sTCP:LISTEN
lsof -iTCP:8080 -sTCP:LISTEN
kill -9 <PID>
```

---

## Common failures

| Symptom | Fix |
|--------|-----|
| Frontend: “Missing `VITE_CLERK_PUBLISHABLE_KEY`” | Put a Clerk publishable key in `raghav/.env`, restart Vite |
| Frontend loads but API calls fail | Confirm API on `:8002`; leave `VITE_API_BASE` unset so the proxy is used |
| `Address already in use` on 8002/8080 | Kill old process (commands above), then restart |
| API DB errors / missing columns | `cd services/api && .venv/bin/alembic upgrade head` |
| Postgres connection refused | `docker compose up -d` (or start local Postgres) |
| OAuth / Calendar redirect wrong host | Ensure `CORS_ORIGINS` / `CLERK_AUTHORIZED_PARTIES` include `http://localhost:8080` |

---

## Optional: API with auth bypass (smoke / scripts only)

```bash
cd services/api
AUTH_BYPASS=true ENV=local .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Do **not** use `AUTH_BYPASS=true` outside local/dev.

---

## Quick copy-paste (after one-time setup)

```bash
# Terminal 1
cd services/api && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Terminal 2
cd raghav && npm run dev -- --host 127.0.0.1 --port 8080 --strictPort
```

Then open http://localhost:8080 and http://localhost:8002/docs.
