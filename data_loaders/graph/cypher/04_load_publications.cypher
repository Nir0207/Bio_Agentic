UNWIND $rows AS row
MERGE (n:Publication {id: row.id})
SET n.pmid = row.pmid,
    n.title = row.title,
    n.abstract = row.abstract,
    n.pub_year = row.pub_year,
    n.source = row.source;

