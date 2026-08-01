# RAG Neo4j — Graph & Text RAG for Trellis

**Production wiring now lives in `services/api`:**

- `app/providers/graph/` — Fake + Neo4j providers
- `app/repositories/graph_repository.py` — multi-hop retrieval
- `app/services/graph/sync_service.py` — Postgres → Neo4j projection
- `app/services/recommendation/graph_rag.py` — Curator context
- `app/api/graph.py` — `GET /graph/status`, `POST /graph/sync`, `GET /graph/retrieve`

Enable with `GRAPH_DB_PROVIDER=neo4j` and `docker compose up neo4j`.

This folder keeps the architecture, schema definitions, query specifications, and the original self-contained prototype.

## Folder contents

- [master_plan.md](master_plan.md) — technical implementation plan.
- [schema.cypher](schema.cypher) — graph schema, constraints, and full-text index.
- [queries.cypher](queries.cypher) — core multi-hop retrieval queries.
- [graph_rag.py](graph_rag.py) — self-contained provider, repository, and context-builder prototype.

## Architecture

```text
User Identity Twin → bottleneck and marker deficits → Neo4j Graph RAG
                                                    ├─ full-text retrieval
                                                    └─ ledger rejection filter
                                                               ↓
                                             Curator LLM / Identity Stack
```

The graph models users, identity attributes, behavioral markers, bottlenecks,
resources, domains, and hypothesis families. Its multi-hop retrieval connects
the current deficit to resources across the Identity Stack. Dismissed families
are excluded, while graph path facts provide evidence for the curator's
“Why this?”, “Why now?”, and “How does this close the gap?” explanations.
