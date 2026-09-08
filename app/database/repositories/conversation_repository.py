"""SQLite conversation and message persistence."""

from __future__ import annotations

import sqlite3
from typing import Iterable


class ConversationRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def start(self, title: str | None = None) -> int:
        cursor = self.connection.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title,),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content),
        )
        self.connection.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish(self, conversation_id: int) -> None:
        self.connection.execute(
            """
            UPDATE conversations
            SET ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (conversation_id,),
        )
        self.connection.commit()

    def list_conversations(self, limit: int = 10) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT id, title, summary, started_at, updated_at, ended_at
            FROM conversations
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()

    def messages_for_conversation(self, conversation_id: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()

    def recent_messages(self, limit: int = 12) -> list[sqlite3.Row]:
        rows = self.connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE role IN ('user', 'assistant')
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()
        return list(reversed(rows))

    def message_count(self, conversation_id: int) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()
        return int(row["count"])

    def older_messages(self, conversation_id: int, keep_recent: int = 20) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
              AND id NOT IN (
                  SELECT id FROM messages
                  WHERE conversation_id = ?
                  ORDER BY id DESC
                  LIMIT ?
              )
            ORDER BY id ASC
            """,
            (conversation_id, conversation_id, max(1, keep_recent)),
        ).fetchall()

    def update_summary(self, conversation_id: int, summary: str) -> None:
        self.connection.execute(
            """
            UPDATE conversations
            SET summary = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (summary, conversation_id),
        )
        self.connection.commit()

    def search_messages(self, tokens: Iterable[str], limit: int = 8) -> list[sqlite3.Row]:
        token_list = [token for token in tokens if token]
        if not token_list:
            return []
        clauses = " OR ".join("content LIKE ?" for _ in token_list)
        params = [f"%{token}%" for token in token_list]
        return self.connection.execute(
            f"""
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE role IN ('user', 'assistant') AND ({clauses})
            ORDER BY id DESC
            LIMIT ?
            """,
            (*params, max(1, limit)),
        ).fetchall()
