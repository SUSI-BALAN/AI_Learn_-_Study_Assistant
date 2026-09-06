"""Subject and topic persistence foundations."""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from app.database.collections import SUBJECTS, TOPICS


class SubjectRepository:
    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self.subjects = database[SUBJECTS]
        self.topics = database[TOPICS]

    def ensure_subject(self, name: str, description: str = "") -> ObjectId:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Subject name cannot be empty")
        normalized = clean_name.casefold()
        now = datetime.now(timezone.utc)
        self.subjects.update_one(
            {"normalized_name": normalized},
            {"$setOnInsert": {
                "name": clean_name, "normalized_name": normalized,
                "description": description.strip(), "progress": 0,
                "status": "active", "created_at": now, "updated_at": now,
            }},
            upsert=True,
        )
        record = self.subjects.find_one({"normalized_name": normalized})
        if record is None:
            raise RuntimeError("MongoDB did not return the stored subject")
        return record["_id"]

    def ensure_topic(self, subject_id: ObjectId, name: str) -> ObjectId:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Topic name cannot be empty")
        normalized = clean_name.casefold()
        now = datetime.now(timezone.utc)
        self.topics.update_one(
            {"subject_id": subject_id, "normalized_name": normalized},
            {"$setOnInsert": {
                "subject_id": subject_id, "name": clean_name,
                "normalized_name": normalized, "status": "not_started",
                "confidence": 0, "quiz_average": None,
                "created_at": now, "updated_at": now,
            }},
            upsert=True,
        )
        record = self.topics.find_one({"subject_id": subject_id, "normalized_name": normalized})
        if record is None:
            raise RuntimeError("MongoDB did not return the stored topic")
        return record["_id"]
