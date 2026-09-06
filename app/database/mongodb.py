"""The application's single MongoDB client and health-check boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.database import collections


@dataclass(frozen=True)
class MongoHealth:
    connected: bool
    detail: str = ""


class MongoDatabase:
    def __init__(self, uri: str, database_name: str, timeout_ms: int = 2000) -> None:
        self.uri = uri
        self.database_name = database_name
        self.timeout_ms = timeout_ms
        self._client: MongoClient[dict[str, Any]] | None = None
        self._database: Database[dict[str, Any]] | None = None
        self._health = MongoHealth(False, "Not connected")

    def connect(self) -> MongoHealth:
        try:
            client: MongoClient[dict[str, Any]] = MongoClient(
                self.uri, serverSelectionTimeoutMS=self.timeout_ms
            )
            client.admin.command("ping")
            self._client = client
            self._database = client[self.database_name]
            self._ensure_indexes()
            self._health = MongoHealth(True)
        except PyMongoError as exc:
            self.close()
            self._health = MongoHealth(False, type(exc).__name__)
        return self._health

    def _ensure_indexes(self) -> None:
        database = self.database
        database[collections.USERS].create_index("local_user_key", unique=True)
        database[collections.CONVERSATIONS].create_index("started_at")
        database[collections.MESSAGES].create_index(
            [("conversation_id", ASCENDING), ("created_at", ASCENDING)]
        )
        database[collections.SUBJECTS].create_index("normalized_name", unique=True)
        database[collections.TOPICS].create_index(
            [("subject_id", ASCENDING), ("normalized_name", ASCENDING)], unique=True
        )

    @property
    def database(self) -> Database[dict[str, Any]]:
        if self._database is None:
            raise RuntimeError("MongoDB is unavailable")
        return self._database

    def health(self) -> MongoHealth:
        return self._health

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._database = None
