"""Consistent terminal output formatting."""

from app.ai.ollama_client import OllamaHealth
from app.database.mongodb import MongoHealth
from app.rag.vector_store import VectorStoreHealth
from config import Settings


def banner(
    settings: Settings,
    health: OllamaHealth,
    mongo_health: MongoHealth,
    vector_health: VectorStoreHealth,
) -> str:
    ollama = "VERIFIED" if health.reachable else "FAILED"
    model = "VERIFIED" if health.model_available else "FAILED"
    model_name = health.active_model or settings.ollama_model
    if health.using_fallback:
        model = "WARNING - fallback"
    internet = "WARNING - disabled" if not settings.internet_search_enabled else "WARNING - enabled"
    mongodb = "VERIFIED" if mongo_health.connected else "WARNING - unavailable"
    chroma = f"VERIFIED ({vector_health.count} chunks)" if vector_health.available else "FAILED"
    return f"""========================================================
       AI LEARNING & STUDY ASSISTANT
       LOCAL CHAT + VECTOR SEARCH - PHASE 4
========================================================

Python      : VERIFIED
Ollama      : {ollama}
Model       : {model_name} ({model})
MongoDB     : {mongodb}
ChromaDB    : {chroma}
Internet    : {internet}
Language    : {settings.default_language}

Type /help to view commands."""


def help_text() -> str:
    return """Commands:
  /help   Show this help
  /clear  Clear current conversation memory
  /exit   Exit safely

Or type any learning question to chat with the local model."""
