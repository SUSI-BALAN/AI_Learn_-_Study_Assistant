import tempfile
import unittest
from pathlib import Path

from app.database.sqlite_database import SQLiteDatabase
from app.memory.memory_manager import MemoryManager
from app.memory.short_term import ShortTermMemory


class ConversationSummaryTests(unittest.TestCase):
    def test_large_conversation_gets_compact_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteDatabase(Path(directory) / "assistant.db")
            database.connect()
            manager = MemoryManager(ShortTermMemory(max_turns=4), database.connection)
            try:
                manager.start()
                for index in range(42):
                    manager.add_turn(
                        f"Question about topic {index}",
                        f"Answer about topic {index}",
                    )
                row = database.connection.execute(
                    "SELECT summary FROM conversations WHERE id = ?",
                    (manager.conversation_id,),
                ).fetchone()
                self.assertIsNotNone(row["summary"])
                self.assertIn("Earlier discussion", row["summary"])
            finally:
                manager.finish()
                database.close()


if __name__ == "__main__":
    unittest.main()
