UNWIND $rows AS row
CALL {
  WITH row
  WHERE row.kind = "interacts"
  MATCH (a:Protein {id: row.source_protein_id})
  MATCH (b:Protein {id: row.target_protein_id})
  MERGE (a)-[r:INTERACTS_WITH]->(b)
  SET r.source = row.source,
      r.confidence = row.confidence,
      r.dataset_version = row.dataset_version
  RETURN count(*) AS _
  UNION ALL
  WITH row
  WHERE row.kind = "participates"
  MATCH (a:Protein {id: row.protein_id})
  MATCH (b:Pathway {id: row.pathway_id})
  MERGE (a)-[r:PARTICIPATES_IN]->(b)
  SET r.source = row.source,
      r.confidence = row.confidence,
      r.dataset_version = row.dataset_version
  RETURN count(*) AS _
  UNION ALL
  WITH row
  WHERE row.kind = "mentions"
  MATCH (a:Publication {id: row.publication_id})
  MATCH (b:Protein {id: row.protein_id})
  MERGE (a)-[r:MENTIONS]->(b)
  SET r.source = row.source,
      r.confidence = row.confidence,
      r.dataset_version = row.dataset_version
  RETURN count(*) AS _
  UNION ALL
  WITH row
  WHERE row.kind = "has_evidence"
  MATCH (a:Publication {id: row.publication_id})
  MATCH (b:Evidence {id: row.evidence_id})
  MERGE (a)-[r:HAS_EVIDENCE]->(b)
  SET r.source = row.source,
      r.confidence = row.confidence,
      r.dataset_version = row.dataset_version
  RETURN count(*) AS _
  UNION ALL
  WITH row
  WHERE row.kind = "supports"
  MATCH (a:Evidence {id: row.evidence_id})
  MATCH (b:Protein {id: row.protein_id})
  MERGE (a)-[r:SUPPORTS]->(b)
  SET r.source = row.source,
      r.confidence = row.confidence,
      r.dataset_version = row.dataset_version
  RETURN count(*) AS _
  UNION ALL
  WITH row
  WHERE row.kind = "parent_of"
  MATCH (a:Pathway {id: row.parent_pathway_id})
  MATCH (b:Pathway {id: row.child_pathway_id})
  MERGE (a)-[r:PARENT_OF]->(b)
  SET r.source = row.source,
      r.confidence = row.confidence,
      r.dataset_version = row.dataset_version
  RETURN count(*) AS _
}
RETURN count(*);

