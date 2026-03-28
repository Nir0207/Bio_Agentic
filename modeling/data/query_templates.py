from __future__ import annotations

PROTEIN_FEATURE_ROWS_QUERY = """
MATCH (p:Protein)
OPTIONAL MATCH (p)-[iw:INTERACTS_WITH]-(:Protein)
WITH p, count(iw) AS interaction_count
OPTIONAL MATCH (p)-[:PARTICIPATES_IN]->(pathway:Pathway)
WITH p, interaction_count, count(DISTINCT pathway) AS pathway_count
OPTIONAL MATCH (e:Evidence)-[supports:SUPPORTS]->(p)
WITH
  p,
  interaction_count,
  pathway_count,
  count(DISTINCT e) AS evidence_count,
  avg(coalesce(supports.confidence, e.confidence, 0.0)) AS avg_evidence_confidence,
  max(coalesce(supports.confidence, e.confidence, 0.0)) AS max_evidence_confidence,
  avg(coalesce(e['semantic_similarity'], e['semantic_score'], 0.0)) AS semantic_similarity_avg
OPTIONAL MATCH (pub:Publication)-[:MENTIONS]->(p)
WITH
  p,
  interaction_count,
  pathway_count,
  evidence_count,
  avg_evidence_confidence,
  max_evidence_confidence,
  semantic_similarity_avg,
  count(DISTINCT pub) AS publication_count
OPTIONAL MATCH (p)-[sim:SIMILAR_TO]-(:Protein)
WITH
  p,
  interaction_count,
  pathway_count,
  evidence_count,
  publication_count,
  avg_evidence_confidence,
  max_evidence_confidence,
  semantic_similarity_avg,
  count(sim) AS similar_to_neighbor_count,
  avg(coalesce(sim['score'], sim['similarity'], 0.0)) AS avg_similarity_score
RETURN
  p.id AS protein_id,
  p.community_id AS community_id,
  p.graph_embedding AS graph_embedding,
  toFloat(interaction_count) AS interaction_count,
  toFloat(pathway_count) AS pathway_count,
  toFloat(evidence_count) AS evidence_count,
  toFloat(publication_count) AS publication_count,
  toFloat(coalesce(avg_evidence_confidence, 0.0)) AS avg_evidence_confidence,
  toFloat(coalesce(max_evidence_confidence, 0.0)) AS max_evidence_confidence,
  toFloat(interaction_count) AS degree_centrality_like_count,
  toFloat(coalesce(similar_to_neighbor_count, 0.0)) AS similar_to_neighbor_count,
  toFloat(coalesce(avg_similarity_score, 0.0)) AS avg_similarity_score,
  toFloat(coalesce(semantic_similarity_avg, 0.0)) AS semantic_similarity_avg
ORDER BY protein_id
SKIP $skip
LIMIT $limit
""".strip()


PROTEIN_FEATURE_ROW_BY_ID_QUERY = """
MATCH (p:Protein {id: $protein_id})
OPTIONAL MATCH (p)-[iw:INTERACTS_WITH]-(:Protein)
WITH p, count(iw) AS interaction_count
OPTIONAL MATCH (p)-[:PARTICIPATES_IN]->(pathway:Pathway)
WITH p, interaction_count, count(DISTINCT pathway) AS pathway_count
OPTIONAL MATCH (e:Evidence)-[supports:SUPPORTS]->(p)
WITH
  p,
  interaction_count,
  pathway_count,
  count(DISTINCT e) AS evidence_count,
  avg(coalesce(supports.confidence, e.confidence, 0.0)) AS avg_evidence_confidence,
  max(coalesce(supports.confidence, e.confidence, 0.0)) AS max_evidence_confidence,
  avg(coalesce(e['semantic_similarity'], e['semantic_score'], 0.0)) AS semantic_similarity_avg
OPTIONAL MATCH (pub:Publication)-[:MENTIONS]->(p)
WITH
  p,
  interaction_count,
  pathway_count,
  evidence_count,
  avg_evidence_confidence,
  max_evidence_confidence,
  semantic_similarity_avg,
  count(DISTINCT pub) AS publication_count
OPTIONAL MATCH (p)-[sim:SIMILAR_TO]-(:Protein)
WITH
  p,
  interaction_count,
  pathway_count,
  evidence_count,
  publication_count,
  avg_evidence_confidence,
  max_evidence_confidence,
  semantic_similarity_avg,
  count(sim) AS similar_to_neighbor_count,
  avg(coalesce(sim['score'], sim['similarity'], 0.0)) AS avg_similarity_score
RETURN
  p.id AS protein_id,
  p.community_id AS community_id,
  p.graph_embedding AS graph_embedding,
  toFloat(interaction_count) AS interaction_count,
  toFloat(pathway_count) AS pathway_count,
  toFloat(evidence_count) AS evidence_count,
  toFloat(publication_count) AS publication_count,
  toFloat(coalesce(avg_evidence_confidence, 0.0)) AS avg_evidence_confidence,
  toFloat(coalesce(max_evidence_confidence, 0.0)) AS max_evidence_confidence,
  toFloat(interaction_count) AS degree_centrality_like_count,
  toFloat(coalesce(similar_to_neighbor_count, 0.0)) AS similar_to_neighbor_count,
  toFloat(coalesce(avg_similarity_score, 0.0)) AS avg_similarity_score,
  toFloat(coalesce(semantic_similarity_avg, 0.0)) AS semantic_similarity_avg
""".strip()
