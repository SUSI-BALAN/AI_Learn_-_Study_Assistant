"""Allowlisted Phase 1 slash-command parsing."""

from enum import Enum


class Command(str, Enum):
    HELP = "/help"
    CLEAR = "/clear"
    EXIT = "/exit"


def parse_command(text: str) -> Command | None:
    normalized = text.strip().lower()
    try:
        return Command(normalized)
    except ValueError:
        return None
