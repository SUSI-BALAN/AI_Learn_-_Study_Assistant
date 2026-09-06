"""Ranked semantic retrieval with metadata filters and score thresholding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.loaders.base import MetadataValue
from app.rag.embeddings import LocalEmbeddingService
from app.rag.vector_store import VectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    metadata: dict[str, MetadataValue]
    score: float


class Retriever:
    def __init__(self, embeddings: LocalEmbeddingService, vector_store: VectorStore) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        minimum_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        result = self.vector_store.query(self.embeddings.embed_query(query), top_k, filters)
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        retrieved = []
        for text, metadata, distance in zip(documents, metadatas, distances, strict=True):
            score = max(-1.0, min(1.0, 1.0 - float(distance)))
            if score >= minimum_score:
                retrieved.append(RetrievedChunk(text or "", metadata or {}, score))
        return retrieved
