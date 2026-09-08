import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.schema import SCHEMA_VERSION
from app.database.sqlite_database import SQLiteDatabase


class SQLiteFoundationTests(unittest.TestCase):
    def test_database_initializes_schema_and_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assistant.db"
            database = SQLiteDatabase(path)
            try:
                health = database.connect()
                self.assertTrue(health.available)
                self.assertTrue(path.is_file())

                tables = {
                    row["name"]
                    for row in database.connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                self.assertIn("user_profile", tables)
                self.assertIn("conversations", tables)
                self.assertIn("messages", tables)
                self.assertIn("memory_facts", tables)
                self.assertIn("documents", tables)

                profile = database.connection.execute(
                    "SELECT display_name, preferred_language FROM user_profile WHERE id = 1"
                ).fetchone()
                self.assertEqual(dict(profile), {
                    "display_name": "Student",
                    "preferred_language": "auto",
                })
                user_version = database.connection.execute("PRAGMA user_version").fetchone()[0]
                self.assertEqual(user_version, SCHEMA_VERSION)
            finally:
                database.close()

    def test_foreign_keys_are_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteDatabase(Path(directory) / "assistant.db")
            try:
                database.connect()
                with self.assertRaises(sqlite3.IntegrityError):
                    database.connection.execute(
                        """
                        INSERT INTO messages (conversation_id, role, content)
                        VALUES (999, 'user', 'orphan')
                        """
                    )
            finally:
                database.close()

    def test_health_reports_unavailable_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            blocked = Path(directory) / "blocked"
            blocked.write_text("not a directory", encoding="utf-8")
            database = SQLiteDatabase(blocked / "assistant.db")
            health = database.connect()
            self.assertFalse(health.available)
            self.assertTrue(health.detail)


if __name__ == "__main__":
    unittest.main()
