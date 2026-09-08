"""Beginner-friendly local service setup guidance."""

from __future__ import annotations

from app.ai.ollama_client import OllamaHealth
from app.database.sqlite_database import SQLiteHealth
from app.rag.vector_store import VectorStoreHealth
from config import Settings


def setup_text(settings: Settings) -> str:
    """Return copy-pasteable setup steps for the configured local stack."""
    return f"""Local setup checklist:
1. Install Ollama from https://ollama.com/download
2. Start Ollama in a separate terminal:
   ollama serve
3. Download the primary chat model:
   ollama pull {settings.ollama_model}
4. Download the fallback chat model:
   ollama pull {settings.ollama_fallback_model}
5. SQLite memory is created automatically at:
   {settings.sqlite_path}
6. Start this assistant:
   python main.py

Ollama and one configured model are required for AI answers. SQLite stores structured memory locally."""


def recovery_text(
    settings: Settings,
    health: OllamaHealth,
    sqlite_health: SQLiteHealth,
    vector_health: VectorStoreHealth,
) -> str:
    """Return only the recovery actions needed for failed or degraded services."""
    messages: list[str] = []
    if not health.reachable:
        messages.append(
            "[FAILED] Ollama is not running.\n"
            "Open a second terminal and run:\n"
            "  ollama serve"
        )
        messages.append(
            "If Ollama is not installed, install it first, then run:\n"
            f"  ollama pull {settings.ollama_model}\n"
            f"  ollama pull {settings.ollama_fallback_model}"
        )
    elif not health.model_available:
        messages.append(
            f"[FAILED] No configured chat model is available.\n"
            f"Run:\n"
            f"  ollama pull {settings.ollama_model}\n"
            f"  ollama pull {settings.ollama_fallback_model}"
        )
    if not sqlite_health.available:
        messages.append(
            "[FAILED] SQLite memory could not start.\n"
            f"Check that this folder is writable and restart the app:\n"
            f"  {settings.sqlite_path.parent}\n"
            f"Detail: {sqlite_health.detail}"
        )
    if not vector_health.available:
        messages.append(f"[FAILED] ChromaDB is unavailable: {vector_health.detail}")
    if not messages:
        return "All required local services are ready."
    return "\n\n".join(messages) + "\n\nType /setup anytime to see the full beginner setup checklist."


def unavailable_ai_text(settings: Settings, health: OllamaHealth) -> str:
    """Return a short chat-loop message when AI generation cannot run."""
    if not health.reachable:
        return (
            "Local AI is unavailable because Ollama is not running.\n"
            "Start it in another terminal with: ollama serve\n"
            "Then restart this app with: python main.py\n"
            "Type /setup for the full beginner checklist."
        )
    if not health.model_available:
        return (
            "Local AI is unavailable because the configured model is missing.\n"
            f"Install it with: ollama pull {settings.ollama_model}\n"
            f"Fallback option: ollama pull {settings.ollama_fallback_model}\n"
            "Then restart this app with: python main.py"
        )
    return "Local AI is unavailable. Type /setup for recovery steps."
