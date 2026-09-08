"""SQLite quiz result persistence."""

from __future__ import annotations

import sqlite3


class QuizRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_result(
        self,
        score: int,
        total: int,
        *,
        subject_id: int | None = None,
        topic_id: int | None = None,
        difficulty: str | None = None,
    ) -> int:
        percentage = 0.0 if total <= 0 else round((score / total) * 100, 2)
        cursor = self.connection.execute(
            """
            INSERT INTO quiz_results
                (subject_id, topic_id, difficulty, score, total, percentage)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (subject_id, topic_id, difficulty, score, total, percentage),
        )
        self.connection.commit()
        return int(cursor.lastrowid)
