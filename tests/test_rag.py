import tempfile
import unittest
from pathlib import Path

from app.loaders.base import DocumentRecord
from app.rag.chunker import chunk_records
from app.rag.rag_service import RagService
from app.rag.vector_store import VectorStore


class FakeEmbeddingService:
    @staticmethod
    def _vector(text: str) -> list[float]:
        lowered = text.casefold()
        return [float("database" in lowered or "normalization" in lowered),
                float("plant" in lowered or "photosynthesis" in lowered)]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class RagFoundationTests(unittest.TestCase):
    def test_chunker_preserves_metadata_and_overlap(self) -> None:
        records = [DocumentRecord("one two three four five six", {"file_name": "notes.txt", "file_type": "txt"})]
        chunks = chunk_records(records, "doc-1", chunk_size=15, overlap=4)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["document_id"], "doc-1")
        self.assertEqual(chunks[0].metadata["chunk_index"], 0)
        self.assertEqual(chunks[0].metadata["chunk_text"], chunks[0].text)

    def test_index_and_semantic_retrieval_with_metadata_filter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dbms = root / "dbms.txt"
            biology = root / "biology.txt"
            dbms.write_text("Database normalization reduces redundant data.", encoding="utf-8")
            biology.write_text("Plant photosynthesis converts light into energy.", encoding="utf-8")
            store = VectorStore(root / "chroma", "rag_test")
            service = RagService(store, FakeEmbeddingService(), chunk_size=200, chunk_overlap=20)
            document_id, count = service.index_document(dbms, subject="DBMS", topic="Normalization")
            service.index_document(biology, subject="Biology", topic="Photosynthesis")
            self.assertEqual(count, 1)
            self.assertEqual(len(document_id), 64)
            result = service.search("How does normalization help databases?", top_k=2)
            self.assertEqual(result[0].metadata["file_name"], "dbms.txt")
            self.assertEqual(result[0].metadata["topic"], "Normalization")
            filtered = service.search("energy", filters={"subject": "Biology"})
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0].metadata["file_name"], "biology.txt")
            store.close()


if __name__ == "__main__":
    unittest.main()
