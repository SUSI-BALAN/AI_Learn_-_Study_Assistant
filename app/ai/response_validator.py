"""Validate and shape model output according to the detected response style."""

from __future__ import annotations

import re

from app.ai.response_style import ResponseStyle

_LEAKAGE_MARKERS = (
    "adaptive system prompt",
    "end system prompt",
    "use only the material below",
    "system prompt says",
    "my system instructions",
)


def is_safe_response(response: str) -> bool:
    normalized = response.strip().casefold()
    return bool(normalized) and not any(marker in normalized for marker in _LEAKAGE_MARKERS)


def mentions_unrequested_internal_topic(response: str, user_input: str) -> bool:
    topics = ("rag", "mongodb", "chromadb", "system prompt", "internal prompt", "uploaded document")
    answer = response.casefold()
    question = user_input.casefold()
    return any(topic in answer and topic not in question for topic in topics)


def shape_normal_response(
    response: str, user_input: str, style: ResponseStyle
) -> str:
    text = _normalize_typography(response.strip())
    if not text:
        return ""
    if style is ResponseStyle.SINGLE_WORD:
        return text.split()[0]
    if style is ResponseStyle.SUMMARY:
        requested_lines = re.search(r"\b(?:in|using)\s+(\d+)\s+lines?\b", user_input, re.IGNORECASE)
        if requested_lines:
            count = int(requested_lines.group(1))
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if len(lines) >= count:
                return "\n".join(lines[:count])
            clauses = [
                clause.strip()
                for clause in re.split(r"(?<=[.!?])\s+|[;,]\s*", " ".join(lines))
                if clause.strip()
            ]
            if len(clauses) >= count:
                return "\n".join(clauses[:count])
            words = text.split()
            if len(words) >= count:
                boundaries = [round(index * len(words) / count) for index in range(count + 1)]
                return "\n".join(
                    " ".join(words[boundaries[index]:boundaries[index + 1]])
                    for index in range(count)
                )
        return text
    if style in {
        ResponseStyle.DETAILED,
        ResponseStyle.STEPS,
        ResponseStyle.LIST,
        ResponseStyle.CODE,
        ResponseStyle.COMPARISON,
        ResponseStyle.RECOMMENDATION,
    }:
        return text
    if style is ResponseStyle.EXPLANATION and (
        "```" in text or re.search(r"(?m)^\s*(?:[-*]|\d+[.)])\s+", text)
    ):
        return text

    kept_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if kept_lines and re.match(
            r"^(?:tips?\s*:|study tips?\s*:|additional(?:ly)?\b|you can also\b)",
            stripped,
            re.IGNORECASE,
        ):
            break
        kept_lines.append(stripped)
    compact = " ".join(kept_lines) or text
    verdict_question = _is_verdict_question(user_input)
    if verdict_question:
        compact = re.sub(r"^yes\s*[,.:;-]?\s*", "Correct. ", compact, flags=re.IGNORECASE)
        compact = re.sub(r"^no\s*[,.:;-]?\s*", "Wrong. ", compact, flags=re.IGNORECASE)
    sentences = re.split(r"(?<=[.!?])\s+", compact)
    if verdict_question:
        sentences = [
            sentence for sentence in sentences
            if not re.search(r"\b(?:correct or wrong|right or wrong)\b", sentence, re.IGNORECASE)
        ]
    limit = 3 if style is ResponseStyle.SIMPLE else 6
    return " ".join(sentences[:limit]).strip()


def requested_structure_count(user_input: str, style: ResponseStyle) -> int | None:
    if style not in {ResponseStyle.SUMMARY, ResponseStyle.LIST}:
        return None
    match = re.search(
        r"\b(\d+)\s+(?:lines?|questions?|items?|points?)\b",
        user_input,
        re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def has_requested_structure(response: str, style: ResponseStyle, count: int) -> bool:
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    if style is ResponseStyle.SUMMARY:
        return len(lines) == count
    list_items = [line for line in lines if re.match(r"^(?:[-*]|\d+[.)])\s+", line)]
    return len(list_items) == count


def is_near_duplicate(response: str, previous_messages: list[dict[str, str]]) -> bool:
    response_tokens = _tokens(response)
    if not response_tokens:
        return False
    for message in previous_messages:
        if message.get("role") != "assistant":
            continue
        previous_tokens = _tokens(message.get("content", ""))
        union = response_tokens | previous_tokens
        if union and len(response_tokens & previous_tokens) / len(union) >= 0.9:
            return True
    return False


def _is_verdict_question(user_input: str) -> bool:
    return bool(re.search(
        r"\b(?:correct or wrong|right or wrong|true or false)\??$",
        user_input,
        re.IGNORECASE,
    ))


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold(), flags=re.UNICODE))


def _normalize_typography(text: str) -> str:
    return text.translate(str.maketrans({
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
    }))
