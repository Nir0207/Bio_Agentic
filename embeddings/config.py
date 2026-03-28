from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str
    batch_size: int
    device: str
    max_nodes: int
    write_batch_size: int
    publication_index_name: str
    evidence_index_name: str
    similarity_function: str
    force_reembed: bool

    @classmethod
    def from_settings(cls, settings: Settings) -> "EmbeddingConfig":
        return cls(
            model_name=settings.embedding_model_name,
            batch_size=max(1, settings.embedding_batch_size),
            device=settings.embedding_device,
            max_nodes=settings.embedding_max_nodes,
            write_batch_size=max(1, settings.embedding_write_batch_size),
            publication_index_name=settings.vector_index_name_publication,
            evidence_index_name=settings.vector_index_name_evidence,
            similarity_function=settings.vector_similarity_function.lower(),
            force_reembed=settings.force_reembed,
        )
