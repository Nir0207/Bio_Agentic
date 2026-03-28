MATCH (n) RETURN labels(n) AS labels, count(*) AS count ORDER BY count DESC;

MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS count ORDER BY count DESC;

MATCH (p:Publication)
WHERE NOT (p)-[:HAS_EVIDENCE]->()
RETURN count(p) AS orphan_publications;

MATCH (e:Evidence)
WHERE NOT ()-[:HAS_EVIDENCE]->(e)
RETURN count(e) AS orphan_evidence;

MATCH (p:Protein)
WHERE NOT (p)-[:PARTICIPATES_IN]->(:Pathway)
RETURN count(p) AS proteins_without_pathways;

MATCH (p:Protein)
RETURN p.id AS protein_id, count { (p)-[r]-() WHERE type(r) = "INTERACTS_WITH" } AS degree
ORDER BY degree DESC, protein_id
LIMIT 10;

MATCH (p:Protein)
WITH p ORDER BY p.id LIMIT 1
OPTIONAL MATCH (p)-[r1]-(other:Protein)
WHERE type(r1) = "INTERACTS_WITH"
OPTIONAL MATCH (p)-[r2]->(pathway:Pathway)
WHERE type(r2) = "PARTICIPATES_IN"
RETURN p, r1, other, r2, pathway
LIMIT 25;
