"""Conversation-session and message persistence."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pymongo.database import Database

from app.database.collections import CONVERSATIONS, MESSAGES


class ConversationRepository:
    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self.conversations = database[CONVERSATIONS]
        self.messages = database[MESSAGES]

    def start(self) -> str:
        conversation_id = str(uuid4())
        self.conversations.insert_one({
            "conversation_id": conversation_id,
            "started_at": datetime.now(timezone.utc),
            "ended_at": None,
        })
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Unsupported conversation role")
        self.messages.insert_one({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        })

    def finish(self, conversation_id: str) -> None:
        self.conversations.update_one(
            {"conversation_id": conversation_id},
            {"$set": {"ended_at": datetime.now(timezone.utc)}},
        )

    def recent_messages(self, limit: int = 12) -> list[dict[str, str]]:
        cursor = self.messages.find({}, {"_id": 0, "role": 1, "content": 1}).sort(
            [("created_at", -1), ("_id", -1)]
        ).limit(max(1, limit))
        return list(reversed(list(cursor)))
