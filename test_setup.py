"""Manual local-service health report using the application service boundaries."""

from app.ai.ollama_client import OllamaClient
from app.database.sqlite_database import SQLiteDatabase
from app.rag.vector_store import VectorStore, VectorStoreError
from config import Settings


def verify_setup() -> None:
    settings = Settings.load()
    ollama = OllamaClient(
        settings.ollama_host, settings.ollama_model, settings.ollama_fallback_model
    ).health()
    print(f"[{'VERIFIED' if ollama.reachable else 'FAILED'}] Ollama connection")
    print(f"[{'VERIFIED' if ollama.model_available else 'FAILED'}] Model: {ollama.active_model or settings.ollama_model}")

    database = SQLiteDatabase(settings.sqlite_path)
    sqlite = database.connect()
    print(f"[{'VERIFIED' if sqlite.available else 'FAILED'}] SQLite: {settings.sqlite_path}")
    database.close()

    try:
        store = VectorStore(settings.chroma_path, settings.chroma_collection)
        health = store.health()
        print(f"[{'VERIFIED' if health.available else 'FAILED'}] ChromaDB ({health.count} chunks)")
        store.close()
    except VectorStoreError as exc:
        print(f"[FAILED] ChromaDB: {exc}")

    print("[WARNING] Internet search disabled")


if __name__ == "__main__":
    verify_setup()
