CREATE CONSTRAINT protein_id_unique IF NOT EXISTS
FOR (n:Protein)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT pathway_id_unique IF NOT EXISTS
FOR (n:Pathway)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT publication_id_unique IF NOT EXISTS
FOR (n:Publication)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS
FOR (n:Evidence)
REQUIRE n.id IS UNIQUE;

CREATE INDEX protein_uniprot_id IF NOT EXISTS
FOR (n:Protein)
ON (n.uniprot_id);

CREATE INDEX pathway_reactome_id IF NOT EXISTS
FOR (n:Pathway)
ON (n.reactome_id);

CREATE INDEX publication_pmid IF NOT EXISTS
FOR (n:Publication)
ON (n.pmid);

CALL db.awaitIndexes(300);
