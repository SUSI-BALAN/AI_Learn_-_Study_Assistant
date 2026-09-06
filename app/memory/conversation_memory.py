"""Persistent conversation facade used by the terminal application."""

from app.database.mongodb import MongoDatabase
from app.database.repositories.conversation_repository import ConversationRepository


class ConversationMemory:
    def __init__(self, database: MongoDatabase) -> None:
        self.database = database

    def _repository(self) -> ConversationRepository:
        return ConversationRepository(self.database.database)

    def start(self) -> str:
        return self._repository().start()

    def add_turn(self, conversation_id: str, user_message: str, assistant_message: str) -> None:
        repository = self._repository()
        repository.add_message(conversation_id, "user", user_message)
        repository.add_message(conversation_id, "assistant", assistant_message)

    def finish(self, conversation_id: str) -> None:
        self._repository().finish(conversation_id)

    def recent(self, limit: int = 12) -> list[dict[str, str]]:
        return self._repository().recent_messages(limit)
