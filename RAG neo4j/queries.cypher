// Candidate resources for a user's active bottleneck and deficit markers.
MATCH (u:User {id: $userId})-[:LIMITED_BY]->(b:Bottleneck {type: $bottleneckType})
MATCH (r:Resource)-[:TARGETS_BOTTLENECK]->(b)
WHERE NOT EXISTS {
    MATCH (u)-[d:DISMISSED]->(hf:HypothesisFamily)
    WHERE d.count >= 3 AND r.type = hf.lens_type
}
OPTIONAL MATCH (r)-[:ADDRESSES_MARKER]->(m:BehavioralMarker)<-[:MANIFESTS_VIA]-(a:IdentityAttribute)<-[:DECLARED]-(u)
RETURN r.id AS resource_id, r.title AS title, r.type AS type,
       r.category AS category, r.difficulty_tier AS difficulty_tier,
       r.extract AS extract, b.title AS bottleneck_title,
       collect(DISTINCT m.name) AS addressed_markers,
       collect(DISTINCT a.name) AS aligned_attributes
ORDER BY size(addressed_markers) DESC, r.title ASC
LIMIT 10;

// Structural-analogy retrieval for the Outside Voice lens.
MATCH (u:User {id: $userId})-[:DECLARED]->(a:IdentityAttribute)-[:MANIFESTS_VIA]->(m:BehavioralMarker)
MATCH (r:Resource {type: 'outside_voice'})-[:ADDRESSES_MARKER]->(m)
MATCH (r)-[:HAS_DOMAIN]->(d:Domain)
RETURN r.id AS resource_id, r.title AS title, r.extract AS extract,
       d.name AS domain_name, a.name AS target_attribute, m.name AS structural_marker
LIMIT 5;

// Full-text RAG enriched by the resource's bottleneck link.
CALL db.index.fulltext.queryNodes("resource_fulltext_idx", $searchQuery) YIELD node AS r, score
MATCH (r)-[:TARGETS_BOTTLENECK]->(b:Bottleneck)
RETURN r.id AS resource_id, r.title AS title, r.type AS type,
       r.extract AS extract, b.title AS bottleneck, score
ORDER BY score DESC
LIMIT 10;
