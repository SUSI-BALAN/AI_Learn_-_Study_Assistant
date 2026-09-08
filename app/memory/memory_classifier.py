"""Deterministic classification for permanent memory facts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class MemoryCategory(str, Enum):
    PROFILE = "PROFILE"
    PREFERENCE = "PREFERENCE"
    SUBJECT = "SUBJECT"
    GOAL = "GOAL"
    PROGRESS = "PROGRESS"
    WEAK_TOPIC = "WEAK_TOPIC"
    IMPORTANT_FACT = "IMPORTANT_FACT"
    IGNORE = "IGNORE"


@dataclass(frozen=True)
class ClassifiedMemory:
    category: MemoryCategory
    stable_key: str = ""
    value: str = ""


def classify_memory(text: str) -> ClassifiedMemory:
    normalized = " ".join(text.strip().split())
    lowered = normalized.casefold()
    if not normalized or lowered in {"hi", "hello", "hey", "thanks", "thank you"}:
        return ClassifiedMemory(MemoryCategory.IGNORE)

    language = _detect_language_preference(lowered)
    if language:
        return ClassifiedMemory(MemoryCategory.PREFERENCE, "preferred_language", language)

    name = _match_value(normalized, r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,50})\b")
    if name:
        return ClassifiedMemory(MemoryCategory.PROFILE, "display_name", name.strip())

    daily_time = _match_value(lowered, r"\b(?:i can study|daily study time is|study daily)\s+(\d+)\s*(?:hours?|hrs?|minutes?|mins?)")
    if daily_time:
        return ClassifiedMemory(MemoryCategory.PREFERENCE, "daily_study_time", normalized)

    finished = _match_value(
        normalized,
        r"\b(?:i finished|completed|i completed|finished)\s+(.{2,80})",
    )
    if finished:
        subject, topic = _split_subject_topic(finished)
        key = f"completed:{_key(subject)}:{_key(topic)}"
        return ClassifiedMemory(MemoryCategory.PROGRESS, key, f"Completed {finished.strip()}")

    weak = _match_value(
        normalized,
        r"\b(?:weak in|struggling with|problem with|difficulty in)\s+(.{2,80})",
    )
    if weak:
        return ClassifiedMemory(MemoryCategory.WEAK_TOPIC, f"weak_topic:{_key(weak)}", weak.strip())

    learning = _match_value(
        normalized,
        r"\b(?:i am learning|currently learning|studying|i study)\s+(.{2,80})",
    )
    if learning:
        return ClassifiedMemory(MemoryCategory.SUBJECT, "current_subject", learning.strip())

    goal = _match_value(
        normalized,
        r"\b(?:exam is|test is|my exam is|goal is|target is)\s+(.{2,100})",
    )
    if goal:
        return ClassifiedMemory(MemoryCategory.GOAL, "current_goal", goal.strip())

    if lowered.startswith(("remember that ", "note that ")):
        value = re.sub(r"^(remember|note) that\s+", "", normalized, flags=re.IGNORECASE)
        return ClassifiedMemory(MemoryCategory.IMPORTANT_FACT, f"fact:{_key(value)[:60]}", value)

    return ClassifiedMemory(MemoryCategory.IGNORE)


def _detect_language_preference(lowered: str) -> str:
    if re.search(r"\b(?:prefer|answer me in|from now answer.*in|reply in)\s+thanglish\b", lowered):
        return "thanglish"
    if re.search(r"\b(?:prefer|answer me in|from now answer.*in|reply in)\s+tamil\b", lowered):
        return "tamil"
    if re.search(r"\b(?:prefer|answer me in|from now answer.*in|reply in)\s+english\b", lowered):
        return "english"
    return ""


def _match_value(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip(" .") if match else ""


def _split_subject_topic(value: str) -> tuple[str, str]:
    parts = value.strip().split(None, 1)
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], parts[1]


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
