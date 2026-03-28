UNWIND $rows AS row
MATCH (a:Protein {id: row.source_protein_id})
MATCH (b:Protein {id: row.target_protein_id})
MERGE (a)-[r:INTERACTS_WITH]->(b)
SET r.source = row.source,
    r.confidence = row.confidence,
    r.dataset_version = row.dataset_version;

