# Architecture & Tech Stack Audit

**Document Date:** August 1, 2026  
**Source of Truth Comparison:** `docs/techstack.md` vs Actual Codebase Implementation  

---

## Executive Summary

No, the implementation has **not strictly followed `docs/techstack.md` across the entire stack**. 

While the core agent architecture (LangGraph), API layer (FastAPI + Pydantic), search integration (Tavily), and deterministic engines are **real and followed**, several infrastructure and vendor dependencies were simplified or mocked for local development:

- **Framework**: Used **Vite + TanStack Start** instead of **Next.js**.
- **Database**: Used **SQLite** (`dev.db`) instead of **PostgreSQL**, and completely omitted **Neo4j** and **Qdrant**.
- **Authentication**: Completely **bypassed Clerk** using a hardcoded mock user setup (`AUTH_BYPASS=true`).
- **AI Infrastructure & Embeddings**: Defaults to a **Fake LLM** (`FakeLLMProvider`) and **SHA-256 string hash embeddings** (`FakeEmbeddingProvider`). Single-key Gemini works when enabled; Amazon Bedrock failover and Gemini key-rotation pool are stubs/unbuilt.
- **Background Workers**: Omitted **Celery**; tasks run in-process or via FastAPI `BackgroundTasks`.
- **MCP Integrations**: **GitHub & Google Calendar** have real OAuth/API adapters; all other MCP connectors (YouTube, Drive, Notion, Cursor, VS Code) use **mock fixtures**.

---

## Tech Stack Audit Matrix

| Component / Layer | Followed `techstack.md`? | Status (Mock / Real) | Actual Implementation / Details |
|---|---|---|---|
| **Frontend Framework** | **NO** | **REAL** | Built with **Vite + TanStack Start** (`@tanstack/react-start` in `raghav/package.json`) instead of Next.js App Router. |
| **Frontend UI Stack** | **YES** | **REAL** | React 19, TypeScript, TailwindCSS v4, Radix UI (shadcn primitives), Motion (`framer-motion`), React Query, React Hook Form, Zod. |
| **API Layer** | **YES** | **REAL** | FastAPI (Python 3.12), Pydantic v2, Uvicorn in `services/api/app/main.py`. |
| **Authentication** | **NO** | **MOCK** | Bypassed via `AUTH_BYPASS=true` and `DEMO_USER_ID=demo-user-aarav` in `services/api/.env`. Clerk SDK is not installed. |
| **Relational Database** | **PARTIAL** | **REAL** | SQLAlchemy + Alembic ORM schemas are real, but configured to local **SQLite** (`dev.db`) instead of PostgreSQL in `.env`. |
| **Graph Database (Neo4j)** | **NO** | **MOCK / MISSING** | Neo4j is omitted. Graph traversals are not implemented. |
| **Vector Database (Qdrant)** | **YES** | **REAL** | Fully integrated with Qdrant Cloud (`QdrantVectorStore`), supporting catalog vector indexing, semantic search endpoints (`GET /api/v1/search/semantic`), and Growth Partner vector matching. |

| **Cache Layer (Redis)** | **PARTIAL** | **MOCK / HYBRID** | Configured in settings, but in-memory Python data structures are used for local dev. |
| **LLM Provider (Gemini)** | **PARTIAL** | **HYBRID** | Default is `FakeLLMProvider` (`llm_provider=fake`). Single-key Gemini is real when configured, but **Key Rotation Pool** is missing. |
| **LLM Failover (Bedrock)** | **NO** | **MOCK** | Bedrock provider is a stub raising `NotImplementedError` in `services/api/app/providers/llm/bedrock.py`. |
| **Embedding Provider** | **NO** | **MOCK** | `FakeEmbeddingProvider` uses deterministic SHA-256 string hashing into 32-dim vectors instead of BGE-large or Google Embeddings. |
| **Search Provider (Tavily)** | **YES** | **REAL** | `TavilySearchProvider` is fully implemented using `tavily-python` SDK. |
| **Agent Orchestration** | **YES** | **REAL** | Built using **LangGraph** `StateGraph` in `services/api/app/agents/graphs/coordinator.py` with node pipelines. |
| **Background Processing** | **NO** | **MOCK** | Celery is missing. Tasks run in-process or via FastAPI `BackgroundTasks`. |
| **MCP Integrations** | **PARTIAL** | **HYBRID** | **GitHub & Google Calendar** have **REAL** OAuth & API adapters in `services/api/app/integrations/mcp/`. YouTube, Drive, Notion, Cursor, VS Code use **MOCK fixtures**. |
| **Decision & Scoring Engine** | **YES** | **REAL** | Deterministic pure-Python scoring logic (Gap formula, bottleneck analysis, moment rules). |
