import tempfile
import unittest
from pathlib import Path

from app.database.sqlite_database import SQLiteDatabase
from app.memory.long_term import LongTermMemory


class LongTermMemoryTests(unittest.TestCase):
    def test_preference_updates_without_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteDatabase(Path(directory) / "assistant.db")
            database.connect()
            memory = LongTermMemory(database.connection)
            try:
                conversation_id = memory.start_conversation()
                first_id = memory.add_message(conversation_id, "user", "I prefer English.")
                memory.classify_and_store("I prefer English.", first_id)
                second_id = memory.add_message(
                    conversation_id, "user", "From now answer me in Thanglish."
                )
                memory.classify_and_store("From now answer me in Thanglish.", second_id)

                profile = dict(memory.memories.profile())
                self.assertEqual(profile["preferred_language"], "thanglish")
                facts = memory.memories.facts_by_category("PREFERENCE")
                self.assertEqual(len(facts), 1)
                self.assertEqual(facts[0]["stable_key"], "preferred_language")
                self.assertEqual(facts[0]["value"], "thanglish")
            finally:
                database.close()

    def test_greeting_is_not_important_fact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteDatabase(Path(directory) / "assistant.db")
            database.connect()
            memory = LongTermMemory(database.connection)
            try:
                conversation_id = memory.start_conversation()
                message_id = memory.add_message(conversation_id, "user", "hi")
                memory.classify_and_store("hi", message_id)
                self.assertEqual(memory.memories.list_facts(), [])
            finally:
                database.close()


if __name__ == "__main__":
    unittest.main()
