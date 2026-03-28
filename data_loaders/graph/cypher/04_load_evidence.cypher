UNWIND $rows AS row
MERGE (n:Evidence {id: row.id})
SET n.text = row.text,
    n.evidence_type = row.evidence_type,
    n.source = row.source,
    n.confidence = row.confidence,
    n.publication_id = row.publication_id;

