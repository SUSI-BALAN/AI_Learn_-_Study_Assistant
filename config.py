"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without overriding the process environment."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    ollama_host: str
    ollama_model: str
    ollama_fallback_model: str
    sqlite_path: Path
    chroma_path: Path
    chroma_collection: str
    documents_path: Path
    rag_chunk_size: int
    rag_chunk_overlap: int
    conversation_turns: int
    relevant_history_turns: int
    internet_search_enabled: bool
    default_language: str

    @classmethod
    def load(cls, env_path: Path | None = None) -> "Settings":
        _load_dotenv(env_path or Path(".env"))
        turns_text = os.getenv("CONVERSATION_TURNS", "6")
        try:
            turns = max(1, int(turns_text))
        except ValueError:
            turns = 6
        chunk_size = _positive_int("RAG_CHUNK_SIZE", 800)
        chunk_overlap = _nonnegative_int("RAG_CHUNK_OVERLAP", 120)
        if chunk_overlap >= chunk_size:
            chunk_overlap = min(120, chunk_size - 1)
        return cls(
            ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            ollama_fallback_model=os.getenv("OLLAMA_FALLBACK_MODEL", "tinyllama"),
            sqlite_path=Path(os.getenv("SQLITE_PATH", "./data/assistant.db")),
            chroma_path=Path(os.getenv("CHROMA_PATH", "./data/chroma")),
            chroma_collection=os.getenv("CHROMA_COLLECTION", "study_materials"),
            documents_path=Path(os.getenv("DOCUMENTS_PATH", "./data/documents")),
            rag_chunk_size=chunk_size,
            rag_chunk_overlap=chunk_overlap,
            conversation_turns=turns,
            relevant_history_turns=_positive_int("RELEVANT_HISTORY_TURNS", 4),
            internet_search_enabled=os.getenv("INTERNET_SEARCH_ENABLED", "false").lower() == "true",
            default_language=os.getenv("DEFAULT_LANGUAGE", "auto"),
        )


def _positive_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _nonnegative_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, str(default))))
    except ValueError:
        return default
