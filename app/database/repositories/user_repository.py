"""Persistent single-user profile access."""

from datetime import datetime, timezone
from typing import Any

from pymongo.database import Database

from app.database.collections import USERS


class UserRepository:
    LOCAL_USER_KEY = "local"

    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self.collection = database[USERS]

    def get_or_create(self, language: str = "auto") -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        self.collection.update_one(
            {"local_user_key": self.LOCAL_USER_KEY},
            {"$setOnInsert": {
                "local_user_key": self.LOCAL_USER_KEY,
                "name": "Student",
                "preferred_language": language,
                "learning_preferences": {},
                "created_at": now,
                "updated_at": now,
            }},
            upsert=True,
        )
        return self.collection.find_one({"local_user_key": self.LOCAL_USER_KEY}) or {}
