from __future__ import annotations

DEFAULT_NODE_LABELS = ["Protein", "Pathway"]
DEFAULT_RELATIONSHIP_TYPES = ["INTERACTS_WITH", "PARTICIPATES_IN", "PARENT_OF"]

GRAPH_EMBEDDING_PROPERTY = "graph_embedding"
GRAPH_EMBEDDING_MODEL_PROPERTY = "graph_embedding_model"
GRAPH_EMBEDDING_DIM_PROPERTY = "graph_embedding_dim"
GRAPH_EMBEDDING_CREATED_AT_PROPERTY = "graph_embedding_created_at"

COMMUNITY_ID_PROPERTY = "community_id"
COMMUNITY_ALGORITHM_PROPERTY = "community_algorithm"
COMMUNITY_CREATED_AT_PROPERTY = "community_created_at"

KNN_SCORE_PROPERTY = "score"
KNN_SOURCE_PROPERTY = "source"
KNN_SOURCE_VALUE = "gds_knn"
KNN_EMBEDDING_MODEL_PROPERTY = "embedding_model"
KNN_CREATED_AT_PROPERTY = "created_at"

FASTRP_MODEL_NAME = "fastrp"
LEIDEN_ALGORITHM_NAME = "leiden"

SUPPORTED_PROJECTION_MODES = {"auto", "native", "cypher"}
