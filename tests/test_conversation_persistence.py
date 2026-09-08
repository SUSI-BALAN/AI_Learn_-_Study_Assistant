import tempfile
import unittest
from pathlib import Path

from app.database.sqlite_database import SQLiteDatabase
from app.memory.memory_manager import MemoryManager
from app.memory.short_term import ShortTermMemory


class ConversationPersistenceTests(unittest.TestCase):
    def test_conversation_survives_database_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assistant.db"
            first_db = SQLiteDatabase(path)
            first_db.connect()
            first = MemoryManager(ShortTermMemory(), first_db.connection)
            first.start()
            first.add_turn("What is Python?", "Python is a programming language.")
            first.finish()
            first_db.close()

            second_db = SQLiteDatabase(path)
            second_db.connect()
            second = MemoryManager(ShortTermMemory(), second_db.connection)
            try:
                history = second.history_text()
                self.assertIn("What is Python?", history)
                self.assertIn("Python is a programming language.", history)
                self.assertIn("Conversation", second.conversations_text())
            finally:
                second_db.close()

    def test_clear_removes_short_term_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteDatabase(Path(directory) / "assistant.db")
            database.connect()
            manager = MemoryManager(ShortTermMemory(), database.connection)
            try:
                manager.start()
                manager.add_turn("What is Python?", "Python is a language.")
                manager.clear_short_term()
                self.assertEqual(manager.messages(), [])
                self.assertIn("What is Python?", manager.history_text())
            finally:
                manager.finish()
                database.close()


if __name__ == "__main__":
    unittest.main()
