"""Persistent ChromaDB storage using caller-supplied local embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.rag.chunker import TextChunk


class VectorStoreError(RuntimeError):
    """A concise ChromaDB initialization or operation failure."""


@dataclass(frozen=True)
class VectorStoreHealth:
    available: bool
    count: int = 0
    detail: str = ""


class VectorStore:
    def __init__(self, path: str | Path, collection_name: str = "study_materials") -> None:
        self.path = Path(path)
        self.collection_name = collection_name
        try:
            self.path.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.path))
            self.collection: Collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=None,
                metadata={"hnsw:space": "cosine", "embedding_model": "all-MiniLM-L6-v2"},
            )
        except Exception as exc:
            raise VectorStoreError(f"Could not initialize ChromaDB: {exc}") from exc

    def health(self) -> VectorStoreHealth:
        try:
            return VectorStoreHealth(True, self.collection.count())
        except Exception as exc:
            return VectorStoreHealth(False, detail=type(exc).__name__)

    def upsert(self, chunks: list[TextChunk], embeddings: list[list[float]]) -> int:
        if not chunks:
            raise VectorStoreError("No document chunks were provided for indexing.")
        if len(chunks) != len(embeddings):
            raise VectorStoreError("Chunk and embedding counts do not match.")
        try:
            self.collection.upsert(
                ids=[chunk.id for chunk in chunks],
                documents=[chunk.text for chunk in chunks],
                metadatas=[chunk.metadata for chunk in chunks],
                embeddings=embeddings,
            )
        except Exception as exc:
            raise VectorStoreError(f"Could not store document vectors: {exc}") from exc
        return len(chunks)

    def query(
        self, embedding: list[float], top_k: int = 5, where: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        try:
            count = self.collection.count()
            if count == 0:
                return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            return self.collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, count),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise VectorStoreError(f"Could not search document vectors: {exc}") from exc

    def delete_document(self, document_id: str) -> None:
        if not document_id.strip():
            raise ValueError("document_id cannot be empty")
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as exc:
            raise VectorStoreError(f"Could not delete document vectors: {exc}") from exc

    def close(self) -> None:
        """Release ChromaDB files, which is required before cleanup on Windows."""
        self.client.close()
