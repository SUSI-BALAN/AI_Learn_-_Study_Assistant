"""Offline local embedding generation for documents and queries."""

from __future__ import annotations

from collections.abc import Sequence

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


class EmbeddingError(RuntimeError):
    """A concise failure raised when local embedding generation fails."""


class LocalEmbeddingService:
    model_name = "all-MiniLM-L6-v2"

    def __init__(self) -> None:
        self._embedding_function = DefaultEmbeddingFunction()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        clean_texts = [text.strip() for text in texts]
        if not clean_texts or any(not text for text in clean_texts):
            raise EmbeddingError("Embedding input must contain non-empty text.")
        try:
            vectors = self._embedding_function(clean_texts)
        except Exception as exc:
            raise EmbeddingError(
                f"Local embedding model '{self.model_name}' is unavailable: {exc}"
            ) from exc
        result = [vector.tolist() for vector in vectors]
        if len(result) != len(clean_texts) or any(not vector for vector in result):
            raise EmbeddingError("Embedding generation returned incomplete vectors.")
        return result

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
