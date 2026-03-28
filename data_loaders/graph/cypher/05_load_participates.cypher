UNWIND $rows AS row
MATCH (a:Protein {id: row.protein_id})
MATCH (b:Pathway {id: row.pathway_id})
MERGE (a)-[r:PARTICIPATES_IN]->(b)
SET r.source = row.source,
    r.confidence = row.confidence,
    r.dataset_version = row.dataset_version;

