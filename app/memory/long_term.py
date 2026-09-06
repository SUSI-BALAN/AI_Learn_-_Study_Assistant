"""High-level access to persistent student learning state."""

from typing import Any

from app.database.mongodb import MongoDatabase
from app.database.repositories.subject_repository import SubjectRepository
from app.database.repositories.user_repository import UserRepository


class LongTermMemory:
    def __init__(self, database: MongoDatabase) -> None:
        self.database = database

    def ensure_local_user(self, language: str = "auto") -> dict[str, Any]:
        return UserRepository(self.database.database).get_or_create(language)

    def remember_subject_topic(self, subject: str, topic: str) -> None:
        repository = SubjectRepository(self.database.database)
        subject_id = repository.ensure_subject(subject)
        repository.ensure_topic(subject_id, topic)
