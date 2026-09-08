"""SQLite repositories for profile and important memory facts."""

from __future__ import annotations

import sqlite3
from typing import Iterable


class MemoryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def profile(self) -> sqlite3.Row:
        row = self.connection.execute(
            """
            SELECT id, display_name, preferred_language, daily_study_minutes,
                   created_at, updated_at
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()
        if row is None:
            raise RuntimeError("Local user profile is missing")
        return row

    def update_profile(
        self,
        *,
        display_name: str | None = None,
        preferred_language: str | None = None,
        daily_study_minutes: int | None = None,
    ) -> None:
        current = dict(self.profile())
        self.connection.execute(
            """
            UPDATE user_profile
            SET display_name = ?,
                preferred_language = ?,
                daily_study_minutes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (
                display_name or current["display_name"],
                preferred_language or current["preferred_language"],
                daily_study_minutes
                if daily_study_minutes is not None
                else current["daily_study_minutes"],
            ),
        )
        self.connection.commit()

    def upsert_fact(
        self,
        category: str,
        stable_key: str,
        value: str,
        source_message_id: int | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO memory_facts (category, stable_key, value, source_message_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category, stable_key) DO UPDATE SET
                value = excluded.value,
                source_message_id = excluded.source_message_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (category, stable_key, value, source_message_id),
        )
        self.connection.commit()
        if cursor.lastrowid:
            return int(cursor.lastrowid)
        row = self.connection.execute(
            """
            SELECT id FROM memory_facts
            WHERE category = ? AND stable_key = ?
            """,
            (category, stable_key),
        ).fetchone()
        return int(row["id"])

    def list_facts(self, limit: int = 20) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT id, category, stable_key, value, created_at, updated_at
            FROM memory_facts
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()

    def facts_by_category(self, category: str) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT id, category, stable_key, value, created_at, updated_at
            FROM memory_facts
            WHERE category = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (category,),
        ).fetchall()

    def search_facts(self, tokens: Iterable[str], limit: int = 8) -> list[sqlite3.Row]:
        token_list = [token for token in tokens if token]
        if not token_list:
            return []
        clauses = " OR ".join("(stable_key LIKE ? OR value LIKE ?)" for _ in token_list)
        params: list[str] = []
        for token in token_list:
            params.extend((f"%{token}%", f"%{token}%"))
        return self.connection.execute(
            f"""
            SELECT id, category, stable_key, value, created_at, updated_at
            FROM memory_facts
            WHERE {clauses}
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (*params, max(1, limit)),
        ).fetchall()
