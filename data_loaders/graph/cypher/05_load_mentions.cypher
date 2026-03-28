UNWIND $rows AS row
MATCH (a:Publication {id: row.publication_id})
MATCH (b:Protein {id: row.protein_id})
MERGE (a)-[r:MENTIONS]->(b)
SET r.source = row.source,
    r.confidence = row.confidence,
    r.dataset_version = row.dataset_version;

