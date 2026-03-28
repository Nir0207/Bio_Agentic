-- name: node_counts_by_label
MATCH (n)
UNWIND labels(n) AS label
RETURN label, count(*) AS count
ORDER BY count DESC;

-- name: relationship_counts_by_type
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(*) AS count
ORDER BY count DESC;

-- name: duplicate_ids_by_label
CALL {
  MATCH (n:Protein)
  WITH n.id AS id, count(*) AS id_count
  WHERE id_count > 1
  RETURN 'Protein' AS label, count(*) AS duplicate_ids

  UNION ALL

  MATCH (n:Pathway)
  WITH n.id AS id, count(*) AS id_count
  WHERE id_count > 1
  RETURN 'Pathway' AS label, count(*) AS duplicate_ids

  UNION ALL

  MATCH (n:Publication)
  WITH n.id AS id, count(*) AS id_count
  WHERE id_count > 1
  RETURN 'Publication' AS label, count(*) AS duplicate_ids

  UNION ALL

  MATCH (n:Evidence)
  WITH n.id AS id, count(*) AS id_count
  WHERE id_count > 1
  RETURN 'Evidence' AS label, count(*) AS duplicate_ids
}
RETURN label, duplicate_ids
ORDER BY label;

-- name: orphan_publications
MATCH (p:Publication)
WHERE NOT (p)-[:HAS_EVIDENCE]->(:Evidence)
RETURN count(p) AS orphan_publications;

-- name: orphan_evidence
MATCH (e:Evidence)
WHERE NOT (:Publication)-[:HAS_EVIDENCE]->(e)
RETURN count(e) AS orphan_evidence;

-- name: proteins_without_pathway
MATCH (p:Protein)
WHERE NOT (p)-[:PARTICIPATES_IN]->(:Pathway)
RETURN count(p) AS proteins_without_pathway;

-- name: top_proteins_by_interaction_degree
MATCH (p:Protein)
RETURN p.id AS protein_id,
       count { (p)-[:INTERACTS_WITH]-(:Protein) } AS interaction_degree
ORDER BY interaction_degree DESC, protein_id
LIMIT 10;

-- name: sample_subgraph_around_protein
WITH $sample_protein_id AS requested_id
MATCH (candidate:Protein)
WITH requested_id, collect(candidate.id)[0] AS fallback_id
WITH coalesce(requested_id, fallback_id) AS selected_id
MATCH (p:Protein {id: selected_id})
OPTIONAL MATCH (p)-[:INTERACTS_WITH]-(neighbor:Protein)
OPTIONAL MATCH (p)-[:PARTICIPATES_IN]->(pathway:Pathway)
RETURN p.id AS protein_id,
       collect(DISTINCT neighbor.id)[0..20] AS interacting_protein_ids,
       collect(DISTINCT pathway.id)[0..20] AS pathway_ids,
       count(DISTINCT neighbor) AS interacting_protein_count,
       count(DISTINCT pathway) AS pathway_count;

-- name: publications_with_empty_abstract
MATCH (p:Publication)
WHERE p.abstract IS NULL OR trim(toString(p.abstract)) = ''
RETURN count(p) AS empty_abstract_publications;

-- name: relationship_endpoint_label_mismatches
CALL {
  MATCH (a)-[r:INTERACTS_WITH]->(b)
  WHERE NOT (a:Protein AND b:Protein)
  RETURN 'INTERACTS_WITH' AS relationship, count(r) AS bad_rows

  UNION ALL

  MATCH (a)-[r:PARTICIPATES_IN]->(b)
  WHERE NOT (a:Protein AND b:Pathway)
  RETURN 'PARTICIPATES_IN' AS relationship, count(r) AS bad_rows

  UNION ALL

  MATCH (a)-[r:MENTIONS]->(b)
  WHERE NOT (a:Publication AND b:Protein)
  RETURN 'MENTIONS' AS relationship, count(r) AS bad_rows

  UNION ALL

  MATCH (a)-[r:HAS_EVIDENCE]->(b)
  WHERE NOT (a:Publication AND b:Evidence)
  RETURN 'HAS_EVIDENCE' AS relationship, count(r) AS bad_rows

  UNION ALL

  MATCH (a)-[r:SUPPORTS]->(b)
  WHERE NOT (a:Evidence AND b:Protein)
  RETURN 'SUPPORTS' AS relationship, count(r) AS bad_rows

  UNION ALL

  MATCH (a)-[r:PARENT_OF]->(b)
  WHERE NOT (a:Pathway AND b:Pathway)
  RETURN 'PARENT_OF' AS relationship, count(r) AS bad_rows
}
RETURN relationship, bad_rows
ORDER BY relationship;
