"""Deterministic text chunking that preserves source metadata."""

from __future__ import annotations

from dataclasses import dataclass

from app.loaders.base import DocumentRecord, MetadataValue


@dataclass(frozen=True)
class TextChunk:
    id: str
    text: str
    metadata: dict[str, MetadataValue]


def chunk_records(
    records: list[DocumentRecord], document_id: str, chunk_size: int = 800, overlap: int = 120
) -> list[TextChunk]:
    if chunk_size < 1:
        raise ValueError("Chunk size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Chunk overlap must be non-negative and smaller than chunk size")
    chunks: list[TextChunk] = []
    chunk_index = 0
    for record in records:
        start = 0
        while start < len(record.text):
            end = min(len(record.text), start + chunk_size)
            if end < len(record.text):
                boundary = record.text.rfind(" ", start + chunk_size // 2, end)
                if boundary > start:
                    end = boundary
            text = record.text[start:end].strip()
            if text:
                metadata = {
                    **record.metadata,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "chunk_text": text,
                }
                chunks.append(TextChunk(f"{document_id}:{chunk_index}", text, metadata))
                chunk_index += 1
            if end >= len(record.text):
                break
            start = max(start + 1, end - overlap)
    return chunks
