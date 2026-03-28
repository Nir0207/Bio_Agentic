UNWIND $rows AS row
MERGE (n:Protein {id: row.id})
SET n.uniprot_id = row.uniprot_id,
    n.name = row.name,
    n.organism = row.organism,
    n.source = row.source,
    n.reviewed = row.reviewed;
