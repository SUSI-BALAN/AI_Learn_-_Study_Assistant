"""SQLite progress, subject, topic, and weak-topic persistence."""

from __future__ import annotations

import sqlite3


class ProgressRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def ensure_subject(self, name: str) -> int:
        normalized = _normalize(name)
        self.connection.execute(
            """
            INSERT INTO subjects (name, normalized_name)
            VALUES (?, ?)
            ON CONFLICT(normalized_name) DO UPDATE SET
                name = excluded.name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (name.strip(), normalized),
        )
        self.connection.commit()
        row = self.connection.execute(
            "SELECT id FROM subjects WHERE normalized_name = ?",
            (normalized,),
        ).fetchone()
        return int(row["id"])

    def ensure_topic(self, subject_id: int, name: str, status: str = "active") -> int:
        normalized = _normalize(name)
        self.connection.execute(
            """
            INSERT INTO topics (subject_id, name, normalized_name, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(subject_id, normalized_name) DO UPDATE SET
                name = excluded.name,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (subject_id, name.strip(), normalized, status),
        )
        self.connection.commit()
        row = self.connection.execute(
            """
            SELECT id FROM topics
            WHERE subject_id = ? AND normalized_name = ?
            """,
            (subject_id, normalized),
        ).fetchone()
        return int(row["id"])

    def mark_progress(self, subject: str, topic: str, completion_percent: float) -> None:
        subject_id = self.ensure_subject(subject)
        topic_id = self.ensure_topic(subject_id, topic, status="completed")
        self.connection.execute(
            """
            INSERT INTO learning_progress (subject_id, topic_id, completion_percent)
            VALUES (?, ?, ?)
            ON CONFLICT(subject_id, topic_id) DO UPDATE SET
                completion_percent = excluded.completion_percent,
                updated_at = CURRENT_TIMESTAMP
            """,
            (subject_id, topic_id, completion_percent),
        )
        self.connection.commit()

    def list_progress(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT s.name AS subject, t.name AS topic, p.completion_percent, p.updated_at
            FROM learning_progress p
            JOIN subjects s ON s.id = p.subject_id
            LEFT JOIN topics t ON t.id = p.topic_id
            ORDER BY p.updated_at DESC
            """
        ).fetchall()


def _normalize(value: str) -> str:
    return " ".join(value.casefold().strip().split())
