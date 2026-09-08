"""Build the smallest route-appropriate model context."""

from __future__ import annotations

from app.ai.prompts import NORMAL_CHAT_PROMPT, RAG_PROMPT
from app.rag.retriever import RetrievedChunk


def build_normal_chat_context(
    user_input: str,
    conversation_history: list[dict[str, str]],
    long_term_context: str = "",
) -> list[dict[str, str]]:
    messages = [
        {"role": "system", "content": NORMAL_CHAT_PROMPT},
    ]
    if long_term_context.strip():
        messages.append({
            "role": "system",
            "content": f"Relevant stored memory. Use only if helpful:\n{long_term_context.strip()}",
        })
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})
    return messages


def build_rag_context(
    user_input: str,
    conversation_history: list[dict[str, str]],
    chunks: list[RetrievedChunk],
    long_term_context: str = "",
) -> list[dict[str, str]]:
    if not chunks:
        raise ValueError("RAG context requires at least one retrieved chunk")
    material = "\n\n".join(
        f"[MATERIAL {index}]\n{chunk.text}" for index, chunk in enumerate(chunks, start=1)
    )
    messages = [
        {"role": "system", "content": RAG_PROMPT},
    ]
    if long_term_context.strip():
        messages.append({
            "role": "system",
            "content": f"Relevant stored learning memory. Use only if it helps interpret the question:\n{long_term_context.strip()}",
        })
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": f"{material}\n\nQUESTION:\n{user_input}"})
    return messages
