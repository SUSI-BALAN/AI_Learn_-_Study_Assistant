"""Central loading for route-specific prompt templates."""

from pathlib import Path

_PROMPT_DIRECTORY = Path(__file__).resolve().parents[2] / "prompts"


def _load_prompt(file_name: str) -> str:
    return (_PROMPT_DIRECTORY / file_name).read_text(encoding="utf-8").strip()


NORMAL_CHAT_PROMPT = _load_prompt("normal_chat.txt")
RAG_PROMPT = _load_prompt("rag.txt")
