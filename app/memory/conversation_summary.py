"""Lightweight deterministic summaries for long conversation history."""

from __future__ import annotations

import sqlite3


def should_summarize(message_count: int, threshold: int = 80) -> bool:
    """Return whether a conversation is large enough for future summarization."""
    return message_count > threshold


def summarize_messages(messages: list[sqlite3.Row], max_items: int = 8) -> str:
    """Create a compact extractive summary without calling the language model."""
    user_lines = [
        row["content"].strip()
        for row in messages
        if row["role"] == "user" and row["content"].strip()
    ]
    if not user_lines:
        return ""
    selected = user_lines[-max_items:]
    return "Earlier discussion:\n" + "\n".join(f"- {line}" for line in selected)
