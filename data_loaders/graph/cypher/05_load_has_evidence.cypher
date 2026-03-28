UNWIND $rows AS row
MATCH (a:Publication {id: row.publication_id})
MATCH (b:Evidence {id: row.evidence_id})
MERGE (a)-[r:HAS_EVIDENCE]->(b)
SET r.source = row.source,
    r.confidence = row.confidence,
    r.dataset_version = row.dataset_version;

