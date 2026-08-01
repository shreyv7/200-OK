# Environment matrix (A6)

Which flags are legal in which environment. Staging/prod must never run with local-only shortcuts.

| Variable | local | staging | prod |
|---|---|---|---|
| `ENV` | `local` | `staging` | `prod` |
| `AUTH_BYPASS` | `true` (pytest / smoke only) | **never** | **never** |
| `ALLOW_DEMO_SEED` | optional `true` for demos | **never** | **never** |
| `LLM_PROVIDER` | `fake` (default) or `gemini` | `gemini` | `gemini` |
| `SEARCH_PROVIDER` | `fake` (default) or `tavily` | `tavily` | `tavily` |
| `CLERK_*` | required when `AUTH_BYPASS=false` | required | required |
| `CORS_ORIGINS` | localhost FE ports | staging FE origin(s) | production FE origin(s) |
| `TOKEN_ENCRYPTION_KEY` | required for D connectors | required | required |
| `TAVILY_API_KEY` / `YOUTUBE_API_KEY` | optional | required for live badges | required |
| `GEMINI_API_KEY` | optional until Person B | required | required |
| `CELERY_TASK_ALWAYS_EAGER` | `true` in pytest only | **never** | **never** |

## Frontend (`raghav/`)

| Variable | local | staging / prod |
|---|---|---|
| `VITE_CLERK_PUBLISHABLE_KEY` | required | required |
| `VITE_API_BASE` | optional (`/api/v1` + Vite proxy → `:8002`) | absolute API origin + `/api/v1` |

## CORS

Backend `CORS_ORIGINS` is a comma-separated allow-list (credentials enabled). Do **not** use `*` in staging/prod.

Default local origins:

```
http://localhost:8080,http://127.0.0.1:8080,
http://localhost:5173,http://127.0.0.1:5173,
http://localhost:3000,http://127.0.0.1:3000
```
