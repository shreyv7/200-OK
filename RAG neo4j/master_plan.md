# Master Plan: Neo4j Graph & Text RAG for Trellis

This master plan details the design, pipeline, data models, and backend code structure for executing **Graph-Augmented Retrieval (Graph & Text RAG)** using Neo4j in Trellis, adhering strictly to `docs/prd.md`, `docs/techstack.md`, and `docs/milestones.md`.

---

## 1. System Objectives

1. **Bottleneck-Driven Curation**: Move beyond generic semantic similarity by anchoring retrieval on `(:User)-[:LIMITED_BY]->(:Bottleneck)` and `(:User)-[:DECLARED]->(:IdentityAttribute)`.
2. **Multi-Category Resource Graph**: Retrieve curated items across all 8 Identity Stack categories:
   - **Media** & **Knowledge**
   - **Micro-Missions** & **Tools**
   - **Mentors** & **Growth Stories**
   - **Real-World Experiences**
   - **Outside Voice** (Cross-domain structural analogies)
3. **Trust Ledger Filtering**: Exclude resource families where `(:User)-[:DISMISSED {count >= 3}]->(:HypothesisFamily)`.
4. **Graph-Enriched RAG Prompting**: Feed Cypher path facts directly to the Curator LLM to satisfy PRD §8 mandatory explanation requirements:
   - *Why this?*
   - *Why now?*
   - *How does this close the Identity Gap?*

---

## 2. Graph Schema (Cypher Specifications)

### Nodes
- `(:User {id: STRING, demo_mode: BOOLEAN})`
- `(:IdentityAttribute {id: STRING, name: STRING, target_points: FLOAT})`
- `(:BehavioralMarker {id: STRING, name: STRING, category: STRING})`
- `(:Bottleneck {id: STRING, type: STRING, title: STRING, description: STRING})`
- `(:Resource {id: STRING, title: STRING, category: STRING, type: STRING, difficulty_tier: STRING, url: STRING, extract: STRING, summary: STRING})`
- `(:Domain {id: STRING, name: STRING})`
- `(:HypothesisFamily {id: STRING, lens_type: STRING})`

### Relationships
- `(:User)-[:DECLARED {weight: FLOAT}]->(:IdentityAttribute)`
- `(:IdentityAttribute)-[:MANIFESTS_VIA]->(:BehavioralMarker)`
- `(:User)-[:LIMITED_BY {confidence: FLOAT}]->(:Bottleneck)`
- `(:Resource)-[:TARGETS_BOTTLENECK]->(:Bottleneck)`
- `(:Resource)-[:ADDRESSES_MARKER]->(:BehavioralMarker)`
- `(:Resource)-[:HAS_DOMAIN]->(:Domain)`
- `(:User)-[:DISMISSED {count: INT, last_dismissed_at: STRING}]->(:HypothesisFamily)`
- `(:User)-[:COMPLETED {timestamp: STRING}]->(:Resource)`

---

## 3. RAG Retrieval Pipeline Architecture

```
[Trigger / State Change Event]
             │
             ▼
[Stage 1: Extract Active User Context]
 ├─ Active Bottleneck (e.g., "Confidence")
 ├─ Deficit Markers (e.g., "Public Speaking")
 ├─ Capacity Tier (Full / Light / Micro)
 └─ Ledger Blacklisted Lens Types
             │
             ▼
[Stage 2: Neo4j Graph Retrieval Query]
 ├─ Multi-Hop Cypher Traversal
 └─ Filter out (:User)-[:DISMISSED]->(:HypothesisFamily)
             │
             ▼
[Stage 3: Neo4j Full-Text Search RAG]
 └─ Search Resource.extract & Resource.title for keywords
             │
             ▼
[Stage 4: Format Graph Context Payload]
 └─ Render Cypher paths into plain-text facts
             │
             ▼
[Stage 5: Curator LLM Execution]
 └─ Structured generation via LLMProvider with Graph Facts
```

---

## 4. Module Map & Backend Integration

The implementation code will be structured cleanly across the codebase:

```text
services/api/app/
├── core/
│   └── config.py               # Neo4j URI/auth settings
├── providers/
│   └── graph/
│       ├── base.py              # GraphProvider interface
│       ├── neo4j.py             # Real Neo4j Bolt driver implementation
│       └── fake.py              # In-memory graph stub for tests
├── repositories/
│   └── graph_repository.py      # Cypher query functions
├── services/
│   ├── graph/
│   │   └── sync_service.py      # Postgres -> Neo4j idempotent sync
│   └── recommendation/
│       └── graph_rag.py         # Multi-hop RAG context builder
└── agents/
    └── nodes/
        └── knowledge/
            └── node.py          # Knowledge node wired to Graph RAG
```

---

## 5. Execution Steps

1. **Dependencies & Environment**: Add `neo4j` driver to `requirements.txt` and `.env`.
2. **Provider & Repository Layer**: Create `GraphProvider` interface, `Neo4jGraphProvider`, `FakeGraphProvider`, and `GraphRepository`.
3. **Graph Sync**: Implement `GraphSyncService` to project relational Postgres entities into Neo4j nodes/edges.
4. **Cypher Queries**: Put standard retrieval queries in `queries.cypher`.
5. **Graph RAG Service**: Implement `GraphRAGService` to merge graph path results + full-text search into Curator prompt context.
6. **Testing & Verification**: Add pytest unit and integration tests under `tests/graph/`.
