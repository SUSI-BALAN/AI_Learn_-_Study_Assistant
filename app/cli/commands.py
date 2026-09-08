"""Allowlisted Phase 1 slash-command parsing."""

from enum import Enum


class Command(str, Enum):
    HELP = "/help"
    SETUP = "/setup"
    STATUS = "/status"
    MEMORY = "/memory"
    HISTORY = "/history"
    CONVERSATIONS = "/conversations"
    PROFILE = "/profile"
    CLEAR = "/clear"
    EXIT = "/exit"


_EXIT_ALIASES = {"exit", "quit", "close", "bye", "goodbye", "leave"}


def parse_command(text: str) -> Command | None:
    normalized = text.strip().lower()
    if normalized in _EXIT_ALIASES:
        return Command.EXIT
    try:
        return Command(normalized)
    except ValueError:
        return None
