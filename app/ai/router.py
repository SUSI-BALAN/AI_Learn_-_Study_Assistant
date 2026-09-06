"""Deterministic routing for normal chat and explicit material-based questions."""

from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    NORMAL_CHAT = "NORMAL_CHAT"
    RAG_SEARCH = "RAG_SEARCH"
    CALCULATOR = "CALCULATOR"


_RAG_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\baccording to (?:my |the )?(?:uploaded )?(?:notes?|materials?|documents?|pdf)\b",
        r"\bfrom (?:my |the )?(?:uploaded )?(?:notes?|materials?|documents?|pdf)\b",
        r"\bin (?:my |the )?(?:uploaded )?(?:notes?|materials?|documents?|pdf)\b",
        r"\bbased on (?:my |the )?(?:uploaded )?(?:notes?|materials?|documents?|pdf)\b",
        r"\bsearch (?:in )?(?:my |the )?(?:uploaded )?(?:notes?|materials?|documents?|pdf)\b",
        r"\bwhat does (?:my |the )?(?:uploaded )?syllabus say\b",
    )
)

_GREETINGS = {
    "hi", "hi there", "hello", "hello there", "hey", "hey there",
    "good morning", "good afternoon", "good evening", "how are you",
}

_ASSISTANT_STATUS_QUESTIONS = {
    "what are you doing", "what do you do", "what are you here for",
}


def route_intent(text: str) -> Intent:
    if any(pattern.search(text) for pattern in _RAG_PATTERNS):
        return Intent.RAG_SEARCH
    if _is_arithmetic_expression(text):
        return Intent.CALCULATOR
    return Intent.NORMAL_CHAT


def is_greeting(text: str) -> bool:
    return _normalize(text) in _GREETINGS


def is_assistant_status_question(text: str) -> bool:
    return _normalize(text) in _ASSISTANT_STATUS_QUESTIONS


def _normalize(text: str) -> str:
    normalized = re.sub(r"[^\w\s]", "", text.casefold())
    return " ".join(normalized.split())


def _is_arithmetic_expression(text: str) -> bool:
    candidate = text.strip()
    return bool(
        candidate
        and re.fullmatch(r"[\d\s.+\-*/%()]+", candidate)
        and re.search(r"[+\-*/%]", candidate)
    )
