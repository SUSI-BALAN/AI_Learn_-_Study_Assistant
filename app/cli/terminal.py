"""Main terminal conversation loop."""

from __future__ import annotations

from app.ai.agent import LearningAgent
from app.ai.ollama_client import OllamaClient, OllamaError
from app.ai.router import Intent, route_intent
from app.cli.commands import Command, parse_command
from app.cli.formatter import banner, help_text
from app.cli.setup_guide import recovery_text, setup_text, unavailable_ai_text
from app.database.sqlite_database import SQLiteDatabase, SQLiteHealth
from app.memory.memory_manager import MemoryManager
from app.memory.short_term import ShortTermMemory
from app.rag.embeddings import LocalEmbeddingService
from app.rag.rag_service import RagService
from app.rag.vector_store import VectorStore, VectorStoreHealth
from config import Settings


class TerminalApplication:
    def __init__(
        self,
        settings: Settings,
        client: OllamaClient,
        sqlite_database: SQLiteDatabase,
        sqlite_health: SQLiteHealth,
        vector_health: VectorStoreHealth,
        vector_store: VectorStore | None,
    ) -> None:
        self.settings = settings
        self.client = client
        self.sqlite_database = sqlite_database
        self.sqlite_health = sqlite_health
        self.vector_health = vector_health
        connection = sqlite_database.connection if sqlite_health.available else None
        self.memory = MemoryManager(
            ShortTermMemory(settings.conversation_turns), connection
        )
        rag_service = None
        if vector_store is not None and vector_health.available:
            rag_service = RagService(
                vector_store,
                LocalEmbeddingService(),
                settings.rag_chunk_size,
                settings.rag_chunk_overlap,
            )
        self.agent = LearningAgent(
            client, self.memory, rag_service, settings.relevant_history_turns
        )

    def run(self) -> None:
        health = self.client.health()
        print(banner(self.settings, health, self.sqlite_health, self.vector_health))
        if (
            not health.reachable
            or not health.model_available
            or not self.sqlite_health.available
            or not self.vector_health.available
        ):
            print(f"\n{recovery_text(self.settings, health, self.sqlite_health, self.vector_health)}")
        self.memory.start()

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                self.memory.finish()
                print("\nGoodbye.")
                return
            if not user_input:
                continue
            command = parse_command(user_input)
            if command is Command.EXIT:
                self.memory.finish()
                print("Goodbye.")
                return
            if command is Command.CLEAR:
                self.memory.clear_short_term()
                print("Current conversation memory cleared. Stored SQLite history was not deleted.")
                continue
            if command is Command.HELP:
                print(help_text())
                continue
            if command is Command.SETUP:
                print(setup_text(self.settings))
                continue
            if command is Command.STATUS:
                health = self.client.health()
                print(banner(self.settings, health, self.sqlite_health, self.vector_health))
                print(f"\n{recovery_text(self.settings, health, self.sqlite_health, self.vector_health)}")
                continue
            if command is Command.MEMORY:
                print(self.memory.memory_text())
                continue
            if command is Command.HISTORY:
                print(self.memory.history_text())
                continue
            if command is Command.CONVERSATIONS:
                print(self.memory.conversations_text())
                continue
            if command is Command.PROFILE:
                print(self.memory.profile_text())
                continue
            if user_input.startswith("/"):
                print("Unknown command. Type /help to see available commands.")
                continue
            if (
                not health.reachable or not health.model_available
            ) and route_intent(user_input) is not Intent.CALCULATOR:
                print(f"Assistant: {unavailable_ai_text(self.settings, health)}")
                continue
            try:
                answer = self.agent.respond(user_input).text
            except OllamaError as exc:
                print(f"Assistant: [FAILED] Ollama request failed: {exc}")
                continue
            self.memory.add_turn(user_input, answer)
            print(f"Assistant: {answer}")
