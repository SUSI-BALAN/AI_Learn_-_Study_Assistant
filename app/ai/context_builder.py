"""Build the smallest route-appropriate model context."""

from __future__ import annotations

from app.ai.prompts import NORMAL_CHAT_PROMPT, RAG_PROMPT
from app.rag.retriever import RetrievedChunk


def build_normal_chat_context(
    user_input: str, conversation_history: list[dict[str, str]]
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": NORMAL_CHAT_PROMPT},
        *conversation_history,
        {"role": "user", "content": user_input},
    ]


def build_rag_context(
    user_input: str,
    conversation_history: list[dict[str, str]],
    chunks: list[RetrievedChunk],
) -> list[dict[str, str]]:
    if not chunks:
        raise ValueError("RAG context requires at least one retrieved chunk")
    material = "\n\n".join(
        f"[MATERIAL {index}]\n{chunk.text}" for index, chunk in enumerate(chunks, start=1)
    )
    return [
        {"role": "system", "content": RAG_PROMPT},
        *conversation_history,
        {"role": "user", "content": f"{material}\n\nQUESTION:\n{user_input}"},
    ]
