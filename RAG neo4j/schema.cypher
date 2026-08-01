// TRELLIS NEO4J GRAPH SCHEMA & CONSTRAINTS

CREATE CONSTRAINT c_user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT c_attribute_id IF NOT EXISTS FOR (a:IdentityAttribute) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT c_marker_id IF NOT EXISTS FOR (m:BehavioralMarker) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT c_bottleneck_id IF NOT EXISTS FOR (b:Bottleneck) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT c_resource_id IF NOT EXISTS FOR (r:Resource) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT c_domain_id IF NOT EXISTS FOR (d:Domain) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT c_hypothesis_family_id IF NOT EXISTS FOR (hf:HypothesisFamily) REQUIRE hf.id IS UNIQUE;

CREATE INDEX idx_resource_type IF NOT EXISTS FOR (r:Resource) ON (r.type);
CREATE INDEX idx_resource_category IF NOT EXISTS FOR (r:Resource) ON (r.category);
CREATE INDEX idx_resource_difficulty IF NOT EXISTS FOR (r:Resource) ON (r.difficulty_tier);
CREATE INDEX idx_bottleneck_type IF NOT EXISTS FOR (b:Bottleneck) ON (b.type);

CREATE FULLTEXT INDEX resource_fulltext_idx IF NOT EXISTS
FOR (r:Resource) ON EACH [r.title, r.extract, r.summary];
