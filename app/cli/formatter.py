"""Consistent terminal output formatting."""

from app.ai.ollama_client import OllamaHealth
from app.database.sqlite_database import SQLiteHealth
from app.rag.vector_store import VectorStoreHealth
from config import Settings


def banner(
    settings: Settings,
    health: OllamaHealth,
    sqlite_health: SQLiteHealth,
    vector_health: VectorStoreHealth,
) -> str:
    ollama = "VERIFIED" if health.reachable else "FAILED"
    model = "VERIFIED" if health.model_available else "FAILED"
    model_name = health.active_model or settings.ollama_model
    if health.using_fallback:
        model = "WARNING - fallback"
    sqlite = "VERIFIED" if sqlite_health.available else "FAILED"
    memory = "VERIFIED" if sqlite_health.available else "WARNING - session only"
    chroma = f"VERIFIED ({vector_health.count} chunks)" if vector_health.available else "FAILED"
    return f"""========================================================
       AI LEARNING & STUDY ASSISTANT
       LOCAL CHAT + VECTOR SEARCH - PHASE 4
========================================================

Python      : VERIFIED
Ollama      : {ollama}
Model       : {model_name} ({model})
SQLite      : {sqlite}
ChromaDB    : {chroma}
Memory      : {memory}
Language    : {settings.default_language}

Type /help to view commands."""


def help_text() -> str:
    return """Commands:
  /help   Show this help
  /setup  Show beginner setup steps for Ollama and local models
  /status Show current startup health again
  /memory Show important stored memory facts
  /history Show recent persisted conversation messages
  /conversations Show previous conversation sessions
  /profile Show the stored local user profile
  /clear  Clear current conversation memory
  /exit   Exit safely

You can also type bye, goodbye, leave, quit, exit, or close to exit.

Or type any learning question to chat with the local model."""
