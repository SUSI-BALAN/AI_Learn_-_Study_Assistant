import tempfile
import unittest

from app.rag.chunker import TextChunk
from app.rag.vector_store import VectorStore


class ChromaVectorStoreTests(unittest.TestCase):
    def test_insert_query_filter_and_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            chunks = [
                TextChunk("doc-a:0", "database normalization", {
                    "document_id": "doc-a", "file_name": "dbms.txt", "file_type": "txt",
                    "subject": "DBMS", "chunk_index": 0, "chunk_text": "database normalization",
                }),
                TextChunk("doc-b:0", "plant photosynthesis", {
                    "document_id": "doc-b", "file_name": "biology.txt", "file_type": "txt",
                    "subject": "Biology", "chunk_index": 0, "chunk_text": "plant photosynthesis",
                }),
            ]
            store = VectorStore(directory, "phase_four_test")
            self.assertEqual(store.upsert(chunks, [[1.0, 0.0], [0.0, 1.0]]), 2)
            result = store.query([1.0, 0.0], top_k=1)
            self.assertEqual(result["documents"][0][0], "database normalization")
            filtered = store.query([0.0, 1.0], top_k=2, where={"subject": "Biology"})
            self.assertEqual(filtered["metadatas"][0][0]["file_name"], "biology.txt")
            store.close()
            restarted = VectorStore(directory, "phase_four_test")
            self.assertTrue(restarted.health().available)
            self.assertEqual(restarted.health().count, 2)
            restarted.close()

    def test_empty_collection_query_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = VectorStore(directory, "empty_test")
            result = store.query([1.0, 0.0])
            self.assertEqual(result["documents"], [[]])
            store.close()


if __name__ == "__main__":
    unittest.main()
