UNWIND $rows AS row
MERGE (n:Pathway {id: row.id})
SET n.reactome_id = row.reactome_id,
    n.name = row.name,
    n.species = row.species,
    n.source = row.source;
