# RAG Neo4j — Graph & Text RAG for Trellis

This folder contains the complete architecture, schema definitions, query specifications, and implementation code for **Neo4j Graph & Text RAG** in Trellis.

---

## Folder Contents

- [`master_plan.md`](file:///c:/Users/jaina/OneDrive/Desktop/HBTM/Project/200-OK/RAG%20neo4j/master_plan.md) — Comprehensive technical implementation master plan.
- [`schema.cypher`](file:///c:/Users/jaina/OneDrive/Desktop/HBTM/Project/200-OK/RAG%20neo4j/schema.cypher) — Neo4j node/edge labels, constraints, and full-text indexes.
- [`queries.cypher`](file:///c:/Users/jaina/OneDrive/Desktop/HBTM/Project/200-OK/RAG%20neo4j/queries.cypher) — Core multi-hop graph retrieval queries for the Curator agent.

---

## Architecture Overview

```
                          +-------------------+
                          | User Identity Twin |
                          +---------+---------+
                                    |
                        (Bottleneck & Gap Deficit)
                                    v
                          +-------------------+
                          | Neo4j Graph RAG   |
                          | (Multi-Hop Path)  |
                          +---------+---------+
                                    |
               +--------------------+--------------------+
               |                                         |
               v                                         v
   +-----------------------+                 +-----------------------+
   | Full-Text Index RAG   |                 | Trust Ledger Filter   |
   | (Extract & Title)     |                 | (Exclude Dismissed)   |
   +-----------+-----------+                 +-----------+-----------+
               |                                         |
               +--------------------+--------------------+
                                    v
                          +-------------------+
                          | Curator Agent LLM |
                          | (Identity Stack)  |
                          +-------------------+
```

1. **Graph Nodes**: `User`, `IdentityAttribute`, `BehavioralMarker`, `Bottleneck`, `Resource`, `Domain`, `HypothesisFamily`.
2. **Multi-Hop Traversal**: Connects user deficit state to curated growth resources across 8 categories (Media, Knowledge, MicroMission, Tool, Mentor, GrowthStory, Experience, OutsideVoice).
3. **Trust Ledger Integration**: Filters out rejected hypothesis families via `:DISMISSED` negative edges.
4. **Structured RAG Explanation**: Passes graph path facts to the LLM to generate `Why this? Why now? How does this close the Identity Gap?`.
