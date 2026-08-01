# RAG Neo4j — Graph & Text RAG for Trellis

This folder contains the architecture, schema definitions, query specifications, and implementation code for Neo4j Graph & Text RAG in Trellis.

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
