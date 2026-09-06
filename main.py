"""Application entry point for the AI Learning & Study Assistant."""

import sys

from app.ai.ollama_client import OllamaClient
from app.cli.terminal import TerminalApplication
from app.database.mongodb import MongoDatabase
from app.rag.vector_store import VectorStore, VectorStoreError, VectorStoreHealth
from config import Settings


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    settings = Settings.load()
    client = OllamaClient(
        settings.ollama_host, settings.ollama_model, settings.ollama_fallback_model
    )
    database = MongoDatabase(settings.mongodb_uri, settings.mongodb_database)
    vector_store = None
    try:
        vector_store = VectorStore(settings.chroma_path, settings.chroma_collection)
        vector_health = vector_store.health()
    except VectorStoreError as exc:
        vector_health = VectorStoreHealth(False, detail=str(exc))
    try:
        database.connect()
        TerminalApplication(settings, client, database, vector_health, vector_store).run()
    finally:
        database.close()
        if vector_store is not None:
            vector_store.close()


if __name__ == "__main__":
    main()
