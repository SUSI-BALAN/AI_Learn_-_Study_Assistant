"""Detect the requested reply language without generating response content."""

from __future__ import annotations

import re
from enum import Enum


class ReplyLanguage(str, Enum):
    ENGLISH = "English"
    TAMIL = "Tamil"
    THANGLISH = "Thanglish"


_THANGLISH_CUES = re.compile(
    r"\b(?:ah|aagum|enna|enakku|epdi|irukka|irukuma|konjam|na|pannu|pannunga|sollu|"
    r"sollunga|venum|venduma)\b",
    re.IGNORECASE,
)


def detect_reply_language(user_input: str) -> ReplyLanguage:
    if re.search(r"[\u0b80-\u0bff]", user_input):
        return ReplyLanguage.TAMIL
    if _THANGLISH_CUES.search(user_input):
        return ReplyLanguage.THANGLISH
    return ReplyLanguage.ENGLISH


def language_instruction(language: ReplyLanguage) -> str:
    if language is ReplyLanguage.TAMIL:
        return "Reply in natural Tamil. Preserve technical terms, code, commands, and notation."
    if language is ReplyLanguage.THANGLISH:
        return "Reply in natural Thanglish. Preserve technical terms, code, commands, and notation."
    return "Reply in English."
