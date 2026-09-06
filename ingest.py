"""Developer batch-indexing entry point built on the Phase 4 RAG services."""

from pathlib import Path

from app.loaders import DocumentLoadError
from app.rag.embeddings import EmbeddingError, LocalEmbeddingService
from app.rag.loader import supported_extensions
from app.rag.rag_service import RagService
from app.rag.vector_store import VectorStore, VectorStoreError
from config import Settings


def ingest_documents() -> None:
    settings = Settings.load()
    documents_path = settings.documents_path
    documents_path.mkdir(parents=True, exist_ok=True)
    candidates = [
        path for path in sorted(documents_path.iterdir())
        if path.is_file() and path.suffix.casefold() in supported_extensions()
    ]
    if not candidates:
        print(f"[WARNING] No supported documents found in {documents_path}.")
        return

    store = VectorStore(settings.chroma_path, settings.chroma_collection)
    service = RagService(
        store, LocalEmbeddingService(), settings.rag_chunk_size, settings.rag_chunk_overlap
    )
    indexed = 0
    try:
        for path in candidates:
            try:
                document_id, count = service.index_document(path)
                indexed += count
                print(f"[VERIFIED] {path.name}: {count} chunks ({document_id[:12]})")
            except (DocumentLoadError, EmbeddingError, VectorStoreError, OSError) as exc:
                print(f"[FAILED] {path.name}: {exc}")
        print(f"[VERIFIED] Total indexed chunks in this run: {indexed}")
    finally:
        store.close()


if __name__ == "__main__":
    ingest_documents()
