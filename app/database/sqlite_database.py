"""SQLite connection and startup health boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from app.database.schema import initialize_schema


class SQLiteDatabaseError(RuntimeError):
    """A user-recoverable SQLite initialization or operation failure."""


@dataclass(frozen=True)
class SQLiteHealth:
    available: bool
    path: Path
    detail: str = ""


class SQLiteDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._connection: sqlite3.Connection | None = None
        self._health = SQLiteHealth(False, self.path, "Not connected")

    def connect(self) -> SQLiteHealth:
        connection: sqlite3.Connection | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            initialize_schema(connection)
            self._connection = connection
            self._health = SQLiteHealth(True, self.path)
        except sqlite3.Error as exc:
            self._health = SQLiteHealth(False, self.path, type(exc).__name__)
            if connection is not None:
                connection.close()
            self._connection = None
        except OSError as exc:
            self._health = SQLiteHealth(False, self.path, str(exc))
        return self._health

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise SQLiteDatabaseError("SQLite is unavailable")
        return self._connection

    def health(self) -> SQLiteHealth:
        if self._connection is None:
            return self._health
        try:
            self._connection.execute("SELECT 1").fetchone()
            return SQLiteHealth(True, self.path)
        except sqlite3.Error as exc:
            self._health = SQLiteHealth(False, self.path, type(exc).__name__)
            return self._health

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
