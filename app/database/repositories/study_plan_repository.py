"""SQLite study-plan persistence."""

from __future__ import annotations

import sqlite3


class StudyPlanRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_plan(
        self,
        title: str,
        plan_text: str,
        *,
        subject_id: int | None = None,
        status: str = "active",
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO study_plans (subject_id, title, plan_text, status)
            VALUES (?, ?, ?, ?)
            """,
            (subject_id, title, plan_text, status),
        )
        self.connection.commit()
        return int(cursor.lastrowid)
