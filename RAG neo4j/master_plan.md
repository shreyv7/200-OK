# Master Plan: Neo4j Graph & Text RAG for Trellis

## Objectives

1. Anchor curation on user bottlenecks and identity deficits rather than generic similarity.
2. Retrieve across all Identity Stack categories: media, knowledge, micro-missions, tools, mentors, growth stories, experiences, and outside voices.
3. Exclude resource families dismissed three or more times.
4. Supply graph-path facts for the mandatory Curator explanations.

## Graph model

Nodes: `User`, `IdentityAttribute`, `BehavioralMarker`, `Bottleneck`, `Resource`, `Domain`, and `HypothesisFamily`.

Relationships: `DECLARED`, `MANIFESTS_VIA`, `LIMITED_BY`, `TARGETS_BOTTLENECK`, `ADDRESSES_MARKER`, `HAS_DOMAIN`, `DISMISSED`, and `COMPLETED`.

## Retrieval pipeline

1. Extract active bottleneck, marker deficits, capacity tier, and ledger exclusions.
2. Run multi-hop graph retrieval.
3. Run Neo4j full-text retrieval for resource title and extract.
4. Format factual graph context.
5. Pass context to the Curator's structured output.

## Intended integration map

```text
services/api/app/
├── core/config.py                 # Neo4j URI/auth settings
├── providers/graph/               # interface, real driver, fake provider
├── repositories/graph_repository.py
├── services/graph/sync_service.py # PostgreSQL → Neo4j projection
└── services/recommendation/graph_rag.py
```

## Execution sequence

1. Add the Neo4j driver and environment variables.
2. Extract the prototype into production provider/repository modules.
3. Project relational identity, resource, and ledger changes to Neo4j idempotently.
4. Execute the provided schema and retrieval queries.
5. Add graph context to the knowledge/curation node.
6. Add unit tests with the fake provider and integration tests against Neo4j.
