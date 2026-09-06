import unittest

import mongomock

from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.subject_repository import SubjectRepository
from app.database.repositories.user_repository import UserRepository


class MongoRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = mongomock.MongoClient()
        self.database = self.client["ai_learning_assistant_test"]

    def tearDown(self) -> None:
        self.client.close()

    def test_local_user_is_created_once_and_survives_repository_restart(self) -> None:
        first = UserRepository(self.database).get_or_create("auto")
        second = UserRepository(self.database).get_or_create("tamil")
        self.assertEqual(first["_id"], second["_id"])
        self.assertEqual(second["preferred_language"], "auto")
        self.assertEqual(self.database.user.count_documents({}), 1)

    def test_conversation_and_messages_survive_repository_restart(self) -> None:
        repository = ConversationRepository(self.database)
        conversation_id = repository.start()
        repository.add_message(conversation_id, "user", "Explain normalization")
        repository.add_message(conversation_id, "assistant", "Normalization organizes data.")
        repository.finish(conversation_id)

        restarted = ConversationRepository(self.database)
        messages = restarted.recent_messages()
        self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
        self.assertIsNotNone(
            self.database.conversations.find_one({"conversation_id": conversation_id})["ended_at"]
        )

    def test_subject_and_topic_upserts_are_idempotent(self) -> None:
        repository = SubjectRepository(self.database)
        subject_id = repository.ensure_subject("DBMS")
        duplicate_subject_id = repository.ensure_subject("dbms")
        first_topic_id = repository.ensure_topic(subject_id, "Normalization")
        duplicate_topic_id = repository.ensure_topic(subject_id, "normalization")
        self.assertEqual(subject_id, duplicate_subject_id)
        self.assertEqual(first_topic_id, duplicate_topic_id)
        self.assertEqual(self.database.subjects.count_documents({}), 1)
        self.assertEqual(self.database.topics.count_documents({}), 1)


if __name__ == "__main__":
    unittest.main()
