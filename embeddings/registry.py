from __future__ import annotations

from functools import lru_cache
from typing import Protocol


class TextEmbeddingModel(Protocol):
    model_name: str
    embedding_dim: int | None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class SentenceTransformerEmbeddingModel:
    def __init__(self, model_name: str, device: str = "cpu") -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        resolved_device = None if device.lower() == "auto" else device
        self._model = SentenceTransformer(model_name, device=resolved_device)
        self.embedding_dim = self._model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,
        )
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()
        return [[float(value) for value in vector] for vector in vectors]


@lru_cache(maxsize=8)
def get_embedding_model(model_name: str, device: str) -> TextEmbeddingModel:
    return SentenceTransformerEmbeddingModel(model_name=model_name, device=device)
