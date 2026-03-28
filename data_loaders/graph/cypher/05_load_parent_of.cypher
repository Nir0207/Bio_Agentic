UNWIND $rows AS row
MATCH (a:Pathway {id: row.parent_pathway_id})
MATCH (b:Pathway {id: row.child_pathway_id})
MERGE (a)-[r:PARENT_OF]->(b)
SET r.source = row.source,
    r.confidence = row.confidence,
    r.dataset_version = row.dataset_version;

