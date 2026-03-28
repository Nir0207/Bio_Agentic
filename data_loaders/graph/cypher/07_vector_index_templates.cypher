// Run these only after semantic embeddings exist on nodes.
// Replace dimensions if your configured embedding model differs.

CREATE VECTOR INDEX publication_semantic_embedding_idx IF NOT EXISTS
FOR (n:Publication) ON (n.semantic_embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
};

CREATE VECTOR INDEX evidence_semantic_embedding_idx IF NOT EXISTS
FOR (n:Evidence) ON (n.semantic_embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
};
