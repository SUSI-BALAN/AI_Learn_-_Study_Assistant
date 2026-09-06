"""Bounded, in-memory conversation context for the current session."""

from __future__ import annotations

from collections import deque
import re


_STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "does", "explain", "for", "how",
    "i", "in", "is", "it", "me", "of", "on", "please", "the", "to", "what",
    "when", "where", "who", "why", "with", "you",
}
_FOLLOW_UP_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:it|that|this|those|them)\b",
        r"\b(?:more|again|continue|further|how so)\b",
        r"^\s*why\s*[?!.]*$",
        r"\b(?:adha|adhu|idha|idhu|innum|konjam more|continue pannunga)\b",
        r"(?:அது|இது|இதை|மேலும்|தொடர்ந்து)",
    )
)


class ShortTermMemory:
    def __init__(self, max_turns: int = 6) -> None:
        self._messages: deque[dict[str, str]] = deque(maxlen=max_turns * 2)

    def add_turn(self, user_message: str, assistant_message: str) -> None:
        self._messages.append({"role": "user", "content": user_message})
        self._messages.append({"role": "assistant", "content": assistant_message})

    def messages(self) -> list[dict[str, str]]:
        return list(self._messages)

    def relevant_messages(self, current_input: str, max_turns: int = 2) -> list[dict[str, str]]:
        """Return only recent turns that can help answer the current input."""
        if max_turns < 1 or not self._messages:
            return []
        messages = list(self._messages)
        turns = [(messages[index], messages[index + 1]) for index in range(0, len(messages) - 1, 2)]
        if not turns:
            return []

        if any(pattern.search(current_input) for pattern in _FOLLOW_UP_PATTERNS):
            selected = [turns[-1]]
            anchor_tokens = _meaningful_tokens(turns[-1][0]["content"])
            for turn in reversed(turns[:-1]):
                if anchor_tokens & _meaningful_tokens(turn[0]["content"]):
                    selected.append(turn)
                    if len(selected) == max_turns:
                        break
            selected.reverse()
        else:
            current_tokens = _meaningful_tokens(current_input)
            selected = []
            for turn in reversed(turns):
                if current_tokens & _meaningful_tokens(turn[0]["content"]):
                    selected.append(turn)
                    if len(selected) == max_turns:
                        break
            selected.reverse()
        return [message.copy() for turn in selected for message in turn]

    def clear(self) -> None:
        self._messages.clear()


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
        if len(token) > 1 and token not in _STOP_WORDS
    }
