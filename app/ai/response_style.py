"""Classify requested answer shape without supplying answer content."""

from __future__ import annotations

import re
from enum import Enum


class ResponseStyle(str, Enum):
    SINGLE_WORD = "single_word"
    SIMPLE = "simple"
    NORMAL = "normal"
    EXPLANATION = "explanation"
    DETAILED = "detailed"
    STEPS = "steps"
    LIST = "list"
    SUMMARY = "summary"
    CODE = "code"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"


def detect_response_style(user_input: str, greeting: bool = False) -> ResponseStyle:
    text = " ".join(user_input.casefold().split())
    if "single word" in text or "one word" in text:
        return ResponseStyle.SINGLE_WORD
    if re.search(r"\b(?:in detail|detailed|deep dive|elaborate)\b|(?:விரிவாக)", text):
        return ResponseStyle.DETAILED
    if re.search(r"\b(?:step by step|steps)\b|^(?:how to|how do i|how can i)\b", text):
        return ResponseStyle.STEPS
    if re.search(r"\b(?:write|show|give).{0,25}\b(?:code|program|example)\b", text):
        return ResponseStyle.CODE
    if re.search(r"\b(?:recommend|recommendation|best programming language)\b", text):
        return ResponseStyle.RECOMMENDATION
    if re.search(
        r"\b(?:compare|difference between|versus|vs\.?|which (?:is )?better|which should)\b|"
        r"\b\w+\s+or\s+\w+.*\bwhich\b",
        text,
    ):
        return ResponseStyle.COMPARISON
    if re.search(r"^(?:list|give me \d+)|\btypes of\b", text):
        return ResponseStyle.LIST
    if re.search(r"\b(?:summarize|summary)\b", text):
        return ResponseStyle.SUMMARY
    if re.search(r"\b(?:give|show).{0,20}\bexample\b", text):
        return ResponseStyle.CODE if _looks_like_programming(text) else ResponseStyle.EXPLANATION
    if text.startswith("explain"):
        return ResponseStyle.EXPLANATION
    if greeting or re.search(
        r"^(?:what (?:is|are)|who is|why |are you|do you|can you)|"
        r"\b(?:correct or wrong|right or wrong|true or false)\??$|^(?:என்ன|யார்)\b",
        text,
    ) or "na enna" in text or "ah irukuma" in text or "என்றால் என்ன" in text:
        return ResponseStyle.SIMPLE
    return ResponseStyle.NORMAL


def generation_options(style: ResponseStyle) -> dict[str, int | float]:
    token_limits = {
        ResponseStyle.SINGLE_WORD: 16,
        ResponseStyle.SIMPLE: 112,
        ResponseStyle.NORMAL: 192,
        ResponseStyle.EXPLANATION: 224,
        ResponseStyle.DETAILED: 640,
        ResponseStyle.STEPS: 320,
        ResponseStyle.LIST: 256,
        ResponseStyle.SUMMARY: 192,
        ResponseStyle.CODE: 320,
        ResponseStyle.COMPARISON: 192,
        ResponseStyle.RECOMMENDATION: 224,
    }
    return {"temperature": 0.2, "num_predict": token_limits[style]}


def response_instruction(style: ResponseStyle, user_input: str = "") -> str:
    instructions = {
        ResponseStyle.SINGLE_WORD: "Reply with only the requested word.",
        ResponseStyle.SIMPLE: (
            "Reply directly in 1 to 3 sentences. Define only the requested concept and do not "
            "conflate it with related concepts."
        ),
        ResponseStyle.NORMAL: "Reply directly in 2 to 6 sentences.",
        ResponseStyle.EXPLANATION: (
            "Give a complete beginner-friendly explanation in 3 to 6 sentences. For a technical "
            "concept, state the correct definition before any analogy and ensure the analogy matches it. "
            "Use one short example only if useful; do not start a long list."
        ),
        ResponseStyle.DETAILED: (
            "Give a detailed, structured answer with one representative example. Maximum 220 words. "
            "Prioritize core behavior and finish the answer; omit advanced tangents unless requested. "
            "Do not invent hidden implementation steps that are not visible in the example. If a "
            "programming language is not named, explain generically and say that exact syntax varies. "
            "For iterator-based loops, do not invent C-style initialization, condition, or increment steps."
        ),
        ResponseStyle.STEPS: (
            "Give no more than 6 practical numbered steps. Start with required setup, include the "
            "minimal working action, and end with how to run or verify it. Omit unnecessary steps."
        ),
        ResponseStyle.LIST: "Give only the requested concise list without unrelated advice.",
        ResponseStyle.SUMMARY: "Follow the requested summary length exactly, with no heading.",
        ResponseStyle.CODE: (
            "Give one small runnable example and explain only its important lines briefly."
        ),
        ResponseStyle.COMPARISON: (
            "Use at most 120 words total: compare each option with no more than 3 short points, "
            "then give one goal-based recommendation."
        ),
        ResponseStyle.RECOMMENDATION: (
            "Give a concise goal-based recommendation. If there is no universal best choice, say so, "
            "then list only the most relevant options in one short line each."
        ),
    }
    instruction = instructions[style]
    requested_count = re.search(r"\b(\d+)\s+(?:lines?|questions?|items?|points?)\b", user_input, re.IGNORECASE)
    if requested_count and style in {ResponseStyle.SUMMARY, ResponseStyle.LIST}:
        noun = "non-empty lines" if style is ResponseStyle.SUMMARY else "items"
        instruction += f" Return exactly {requested_count.group(1)} {noun}."
    return instruction


def _looks_like_programming(text: str) -> bool:
    return any(term in text for term in ("python", "java", "javascript", " c ", "code", "loop"))
