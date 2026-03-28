// Neo4j vector indexes are intentionally deferred.
// Create these only after embedding properties exist on nodes.

// Publication embeddings
// CREATE VECTOR INDEX publication_semantic_embedding_idx IF NOT EXISTS
// FOR (n:Publication) ON (n.semantic_embedding)
// OPTIONS {
//   indexConfig: {
//     `vector.dimensions`: 1536,
//     `vector.similarity_function`: 'cosine'
//   }
// };

// Evidence embeddings
// CREATE VECTOR INDEX evidence_semantic_embedding_idx IF NOT EXISTS
// FOR (n:Evidence) ON (n.semantic_embedding)
// OPTIONS {
//   indexConfig: {
//     `vector.dimensions`: 1536,
//     `vector.similarity_function`: 'cosine'
//   }
// };
