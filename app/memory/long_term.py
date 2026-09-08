"""SQLite-backed long-term memory facade."""

from __future__ import annotations

import sqlite3

from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.memory_repository import MemoryRepository
from app.database.repositories.progress_repository import ProgressRepository
from app.memory.conversation_summary import should_summarize, summarize_messages
from app.memory.memory_classifier import MemoryCategory, classify_memory
from app.memory.memory_retriever import MemoryRetriever


class LongTermMemory:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.conversations = ConversationRepository(connection)
        self.memories = MemoryRepository(connection)
        self.progress = ProgressRepository(connection)
        self.retriever = MemoryRetriever(connection)

    def start_conversation(self) -> int:
        return self.conversations.start()

    def finish_conversation(self, conversation_id: int) -> None:
        self.conversations.finish(conversation_id)

    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        return self.conversations.add_message(conversation_id, role, content)

    def classify_and_store(self, user_text: str, source_message_id: int | None = None) -> None:
        classified = classify_memory(user_text)
        if classified.category is MemoryCategory.IGNORE:
            return
        if classified.category is MemoryCategory.PROFILE:
            if classified.stable_key == "display_name":
                self.memories.update_profile(display_name=classified.value)
        elif classified.category is MemoryCategory.PREFERENCE:
            if classified.stable_key == "preferred_language":
                self.memories.update_profile(preferred_language=classified.value)
        elif classified.category is MemoryCategory.SUBJECT:
            self.progress.ensure_subject(classified.value)
        elif classified.category is MemoryCategory.PROGRESS:
            subject, topic = _progress_subject_topic(classified.value)
            self.progress.mark_progress(subject, topic, 100)
        elif classified.category is MemoryCategory.WEAK_TOPIC:
            subject_id = self.progress.ensure_subject("General")
            topic_id = self.progress.ensure_topic(subject_id, classified.value)
            self.connection.execute(
                """
                INSERT INTO weak_topics (subject_id, topic_id, weakness_score, reason)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(subject_id, topic_id) DO UPDATE SET
                    weakness_score = excluded.weakness_score,
                    reason = excluded.reason,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (subject_id, topic_id, 1.0, classified.value),
            )
            self.connection.commit()
        self.memories.upsert_fact(
            classified.category.value,
            classified.stable_key,
            classified.value,
            source_message_id,
        )

    def relevant_context(self, question: str) -> str:
        return self.retriever.relevant_context(question)

    def maybe_summarize(self, conversation_id: int) -> None:
        count = self.conversations.message_count(conversation_id)
        if not should_summarize(count):
            return
        summary = summarize_messages(self.conversations.older_messages(conversation_id))
        if summary:
            self.conversations.update_summary(conversation_id, summary)

    def answer_memory_question(self, question: str) -> str:
        lowered = question.casefold()
        if "currently learning" in lowered or "currently studying" in lowered or "am i learning" in lowered:
            facts = self.memories.facts_by_category("SUBJECT")
            if facts:
                return f"You are currently learning: {facts[0]['value']}"
            return "I do not have a current subject stored yet."
        if "weakest" in lowered or "weak" in lowered:
            facts = self.memories.facts_by_category("WEAK_TOPIC")
            if facts:
                return "Your stored weak topics:\n" + "\n".join(f"- {row['value']}" for row in facts)
            return "No weak topics are stored yet."
        if "profile" in lowered or "preference" in lowered:
            return self.profile_text()
        context = self.relevant_context(question)
        if context:
            return context
        return "I do not have relevant stored memory for that yet."

    def memory_text(self, limit: int = 20) -> str:
        facts = self.memories.list_facts(limit)
        if not facts:
            return "No important memory facts stored yet."
        return "\n".join(
            f"- {row['category']} | {row['stable_key']}: {row['value']}"
            for row in facts
        )

    def profile_text(self) -> str:
        profile = self.memories.profile()
        return (
            f"Name: {profile['display_name']}\n"
            f"Preferred language: {profile['preferred_language']}\n"
            f"Daily study minutes: {profile['daily_study_minutes'] or 'not set'}"
        )

    def history_text(self, limit: int = 12) -> str:
        messages = self.conversations.recent_messages(limit)
        if not messages:
            return "No conversation history stored yet."
        return "\n".join(f"- {row['role']}: {row['content']}" for row in messages)

    def conversations_text(self, limit: int = 10) -> str:
        conversations = self.conversations.list_conversations(limit)
        if not conversations:
            return "No previous conversations stored yet."
        lines = []
        for row in conversations:
            title = row["title"] or f"Conversation {row['id']}"
            ended = row["ended_at"] or "active"
            lines.append(f"- #{row['id']} {title} | updated {row['updated_at']} | ended {ended}")
        return "\n".join(lines)


def _progress_subject_topic(value: str) -> tuple[str, str]:
    cleaned = value.removeprefix("Completed ").strip()
    parts = cleaned.split(None, 1)
    if len(parts) == 1:
        return "General", parts[0]
    return parts[0], parts[1]
