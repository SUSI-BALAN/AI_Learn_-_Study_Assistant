"""High-level Phase 4 document indexing and semantic retrieval coordinator."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from app.loaders.base import DocumentRecord
from app.rag.chunker import chunk_records
from app.rag.embeddings import LocalEmbeddingService
from app.rag.loader import load_document
from app.rag.retriever import RetrievedChunk, Retriever
from app.rag.vector_store import VectorStore


class RagService:
    def __init__(
        self,
        vector_store: VectorStore,
        embeddings: LocalEmbeddingService,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> None:
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retriever = Retriever(embeddings, vector_store)

    def index_document(
        self, path: str | Path, subject: str = "", topic: str = ""
    ) -> tuple[str, int]:
        resolved = Path(path).resolve(strict=True)
        digest = sha256(resolved.name.encode("utf-8") + b"\0" + resolved.read_bytes()).hexdigest()
        records = load_document(resolved)
        enriched: list[DocumentRecord] = []
        for record in records:
            metadata = dict(record.metadata)
            if subject.strip():
                metadata["subject"] = subject.strip()
            if topic.strip():
                metadata["topic"] = topic.strip()
            enriched.append(DocumentRecord(record.text, metadata))
        chunks = chunk_records(enriched, digest, self.chunk_size, self.chunk_overlap)
        vectors = self.embeddings.embed_documents([chunk.text for chunk in chunks])
        return digest, self.vector_store.upsert(chunks, vectors)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        minimum_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        return self.retriever.search(query, top_k, filters, minimum_score)
