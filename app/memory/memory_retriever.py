"""Find small relevant SQLite memory snippets for a user question."""

from __future__ import annotations

import re
import sqlite3

from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.memory_repository import MemoryRepository


_STOP_WORDS = {
    "a", "an", "and", "are", "about", "am", "did", "do", "for", "i", "in",
    "is", "it", "me", "my", "of", "on", "the", "to", "was", "we", "what",
    "when", "where", "who", "why", "with", "you",
}


class MemoryRetriever:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.memory_repository = MemoryRepository(connection)
        self.conversation_repository = ConversationRepository(connection)

    def relevant_context(self, question: str, limit: int = 6) -> str:
        tokens = _tokens(question)
        facts = self.memory_repository.search_facts(tokens, limit=limit)
        messages = self.conversation_repository.search_messages(tokens, limit=limit)
        lines: list[str] = []
        if facts:
            lines.append("Relevant stored memory:")
            lines.extend(f"- {row['category']}: {row['value']}" for row in facts[:limit])
        if messages:
            lines.append("Relevant previous conversation:")
            for row in messages[:limit]:
                lines.append(f"- {row['role']}: {row['content']}")
        return "\n".join(lines)


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
        if len(token) > 2 and token not in _STOP_WORDS
    ][:8]
