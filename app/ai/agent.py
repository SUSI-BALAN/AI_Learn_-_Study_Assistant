"""Route-aware chat orchestration for normal and grounded responses."""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.context_builder import build_normal_chat_context, build_rag_context
from app.ai.language_detector import (
    detect_reply_language,
    language_instruction,
)
from app.ai.ollama_client import OllamaClient
from app.ai.response_validator import (
    has_requested_structure,
    is_near_duplicate,
    is_safe_response,
    mentions_unrequested_internal_topic,
    requested_structure_count,
    shape_normal_response,
)
from app.ai.response_style import detect_response_style, generation_options, response_instruction
from app.ai.router import Intent, is_greeting, route_intent
from app.memory.memory_manager import MemoryManager
from app.memory.short_term import ShortTermMemory
from app.rag.citations import format_citation
from app.rag.rag_service import RagService
from app.tools.calculator import CalculationError, calculate, format_result

INSUFFICIENT_EVIDENCE = "I couldn't find enough information about that in your uploaded materials."


@dataclass(frozen=True)
class AgentResponse:
    text: str
    intent: Intent


class LearningAgent:
    def __init__(
        self,
        client: OllamaClient,
        memory: ShortTermMemory | MemoryManager,
        rag_service: RagService | None = None,
        relevant_history_turns: int = 4,
    ) -> None:
        self.client = client
        self.memory = memory
        self.rag_service = rag_service
        self.relevant_history_turns = max(1, relevant_history_turns)

    def respond(self, user_input: str) -> AgentResponse:
        intent = route_intent(user_input)
        if intent is Intent.CALCULATOR:
            return self._calculate(user_input)
        if intent is Intent.MEMORY_SEARCH:
            return self._memory_search(user_input)
        if intent is Intent.NORMAL_CHAT:
            return self._normal_chat(user_input)
        return self._rag_chat(user_input)

    def _normal_chat(self, user_input: str) -> AgentResponse:
        style = detect_response_style(user_input, greeting=is_greeting(user_input))
        relevant_history = self.memory.relevant_messages(
            user_input, max_turns=self.relevant_history_turns
        )
        long_term_context = _long_term_context(self.memory, user_input)
        language = detect_reply_language(user_input)
        model_input = (
            f"{user_input}\n\n"
            f"Response format: {response_instruction(style, user_input)} "
            f"{language_instruction(language)} "
            "Silently check technical facts and code before answering; omit uncertain claims."
        )
        messages = build_normal_chat_context(
            model_input, relevant_history, long_term_context
        )
        options = generation_options(style)
        response = self.client.chat(messages, options=options)
        required_count = requested_structure_count(user_input, style)
        if required_count is not None and not has_requested_structure(response, style, required_count):
            unit = "non-empty lines" if style.value == "summary" else "list items"
            retry_messages = messages + [
                {"role": "assistant", "content": response},
                {
                    "role": "user",
                    "content": (
                        f"Rewrite that answer as exactly {required_count} {unit}. "
                        "Keep it accurate and complete. Return only the rewritten answer."
                    ),
                },
            ]
            response = self.client.chat(retry_messages, options=options)
        response = shape_normal_response(response, user_input, style)
        if not is_safe_response(response) or mentions_unrequested_internal_topic(response, user_input):
            response = "I'm not confident that response addressed your question. Please rephrase it."
        elif is_near_duplicate(response, self.memory.messages()):
            response = "I've already answered that. Ask me if you want a different explanation."
        return AgentResponse(response, Intent.NORMAL_CHAT)

    def _calculate(self, expression: str) -> AgentResponse:
        try:
            result = format_result(calculate(expression))
        except CalculationError as exc:
            result = str(exc)
        return AgentResponse(result, Intent.CALCULATOR)

    def _memory_search(self, user_input: str) -> AgentResponse:
        if isinstance(self.memory, MemoryManager):
            return AgentResponse(self.memory.answer_memory_question(user_input), Intent.MEMORY_SEARCH)
        return AgentResponse("Long-term memory is unavailable.", Intent.MEMORY_SEARCH)

    def _rag_chat(self, user_input: str) -> AgentResponse:
        if self.rag_service is None or self.rag_service.vector_store.health().count == 0:
            return AgentResponse(INSUFFICIENT_EVIDENCE, Intent.RAG_SEARCH)
        chunks = self.rag_service.search(user_input, top_k=4, minimum_score=0.25)
        if not chunks:
            return AgentResponse(INSUFFICIENT_EVIDENCE, Intent.RAG_SEARCH)
        messages = build_rag_context(
            user_input,
            self.memory.messages(),
            chunks,
            _long_term_context(self.memory, user_input),
        )
        response = self.client.chat(messages)
        if not is_safe_response(response):
            return AgentResponse(INSUFFICIENT_EVIDENCE, Intent.RAG_SEARCH)
        sources = list(dict.fromkeys(format_citation(chunk.metadata) for chunk in chunks))
        source_text = "\n".join(f"- {source}" for source in sources)
        return AgentResponse(f"{response}\n\nSources:\n{source_text}", Intent.RAG_SEARCH)


def _long_term_context(memory: ShortTermMemory | MemoryManager, user_input: str) -> str:
    if isinstance(memory, MemoryManager):
        return memory.relevant_long_term_context(user_input)
    return ""
