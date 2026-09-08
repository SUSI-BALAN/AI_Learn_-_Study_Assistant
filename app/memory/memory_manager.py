"""Coordinate RAM, SQLite, and semantic memory boundaries."""

from __future__ import annotations

import sqlite3

from app.memory.long_term import LongTermMemory
from app.memory.short_term import ShortTermMemory


class MemoryManager:
    def __init__(self, short_term: ShortTermMemory, connection: sqlite3.Connection | None) -> None:
        self.short_term = short_term
        self.long_term = LongTermMemory(connection) if connection is not None else None
        self.conversation_id: int | None = None

    def start(self) -> None:
        if self.long_term is not None:
            self.conversation_id = self.long_term.start_conversation()

    def finish(self) -> None:
        if self.long_term is not None and self.conversation_id is not None:
            self.long_term.finish_conversation(self.conversation_id)

    def add_turn(self, user_message: str, assistant_message: str) -> None:
        self.short_term.add_turn(user_message, assistant_message)
        if self.long_term is None or self.conversation_id is None:
            return
        user_message_id = self.long_term.add_message(
            self.conversation_id, "user", user_message
        )
        self.long_term.classify_and_store(user_message, user_message_id)
        self.long_term.add_message(self.conversation_id, "assistant", assistant_message)
        self.long_term.maybe_summarize(self.conversation_id)

    def clear_short_term(self) -> None:
        self.short_term.clear()

    def messages(self) -> list[dict[str, str]]:
        return self.short_term.messages()

    def relevant_messages(self, current_input: str, max_turns: int = 2) -> list[dict[str, str]]:
        return self.short_term.relevant_messages(current_input, max_turns)

    def relevant_long_term_context(self, current_input: str) -> str:
        if self.long_term is None:
            return ""
        return self.long_term.relevant_context(current_input)

    def memory_text(self) -> str:
        if self.long_term is None:
            return "SQLite memory is unavailable."
        return self.long_term.memory_text()

    def profile_text(self) -> str:
        if self.long_term is None:
            return "SQLite profile is unavailable."
        return self.long_term.profile_text()

    def history_text(self) -> str:
        if self.long_term is None:
            return "SQLite conversation history is unavailable."
        return self.long_term.history_text()

    def conversations_text(self) -> str:
        if self.long_term is None:
            return "SQLite conversations are unavailable."
        return self.long_term.conversations_text()

    def answer_memory_question(self, question: str) -> str:
        if self.long_term is None:
            return "SQLite memory is unavailable."
        return self.long_term.answer_memory_question(question)
