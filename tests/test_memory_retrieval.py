import tempfile
import unittest
from pathlib import Path

from app.database.sqlite_database import SQLiteDatabase
from app.memory.memory_manager import MemoryManager
from app.memory.short_term import ShortTermMemory


class MemoryRetrievalTests(unittest.TestCase):
    def test_relevant_context_uses_matching_facts_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteDatabase(Path(directory) / "assistant.db")
            database.connect()
            manager = MemoryManager(ShortTermMemory(), database.connection)
            try:
                manager.start()
                manager.add_turn("I prefer Thanglish.", "Okay, I will use Thanglish.")
                manager.add_turn("What are Python loops?", "Loops repeat code.")
                context = manager.relevant_long_term_context("What did we discuss about Python loops?")
                self.assertIn("Python loops", context)
                self.assertIn("previous conversation", context)

                self.assertIn("thanglish", manager.profile_text().casefold())
                self.assertIn("PREFERENCE", manager.memory_text())
            finally:
                manager.finish()
                database.close()


if __name__ == "__main__":
    unittest.main()
