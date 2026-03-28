UNWIND $rows AS row
MATCH (a:Evidence {id: row.evidence_id})
MATCH (b:Protein {id: row.protein_id})
MERGE (a)-[r:SUPPORTS]->(b)
SET r.source = row.source,
    r.confidence = row.confidence,
    r.dataset_version = row.dataset_version;

