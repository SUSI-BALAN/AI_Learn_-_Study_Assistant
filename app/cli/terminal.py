"""Main terminal conversation loop."""

from __future__ import annotations

from app.ai.agent import LearningAgent
from app.ai.ollama_client import OllamaClient, OllamaError
from app.cli.commands import Command, parse_command
from app.cli.formatter import banner, help_text
from app.database.mongodb import MongoDatabase
from app.memory.conversation_memory import ConversationMemory
from app.memory.long_term import LongTermMemory
from app.memory.short_term import ShortTermMemory
from app.rag.embeddings import LocalEmbeddingService
from app.rag.rag_service import RagService
from app.rag.vector_store import VectorStore, VectorStoreHealth
from config import Settings
from pymongo.errors import PyMongoError


class TerminalApplication:
    def __init__(
        self,
        settings: Settings,
        client: OllamaClient,
        database: MongoDatabase,
        vector_health: VectorStoreHealth,
        vector_store: VectorStore | None,
    ) -> None:
        self.settings = settings
        self.client = client
        self.database = database
        self.vector_health = vector_health
        self.memory = ShortTermMemory(settings.conversation_turns)
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
        self.long_term = LongTermMemory(database)
        self.conversations = ConversationMemory(database)

    def run(self) -> None:
        health = self.client.health()
        mongo_health = self.database.health()
        print(banner(self.settings, health, mongo_health, self.vector_health))
        if not health.reachable:
            print("\n[FAILED] Ollama is not available. Start it with: ollama serve")
        elif not health.model_available:
            print(f"\n[FAILED] Model '{self.settings.ollama_model}' is unavailable. {health.detail}")
        if not mongo_health.connected:
            print("\n[WARNING] MongoDB is unavailable; chat will continue without persistence.")
            print("Start MongoDB and restart the application to enable long-term memory.")
        if not self.vector_health.available:
            print(f"\n[FAILED] ChromaDB is unavailable: {self.vector_health.detail}")

        conversation_id = None
        if mongo_health.connected:
            try:
                self.long_term.ensure_local_user(self.settings.default_language)
                conversation_id = self.conversations.start()
            except PyMongoError:
                print("\n[WARNING] MongoDB initialization failed; continuing without persistence.")

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                self._finish_conversation(conversation_id)
                print("\nGoodbye.")
                return
            if not user_input:
                continue
            command = parse_command(user_input)
            if command is Command.EXIT:
                self._finish_conversation(conversation_id)
                print("Goodbye.")
                return
            if command is Command.CLEAR:
                self.memory.clear()
                print("Conversation memory cleared.")
                continue
            if command is Command.HELP:
                print(help_text())
                continue
            if user_input.startswith("/"):
                print("Unknown command. Type /help to see available commands.")
                continue
            if not health.reachable or not health.model_available:
                print("Assistant: Local AI is unavailable. Resolve the startup failure and try again.")
                continue
            try:
                answer = self.agent.respond(user_input).text
            except OllamaError as exc:
                print(f"Assistant: [FAILED] Ollama request failed: {exc}")
                continue
            self.memory.add_turn(user_input, answer)
            if conversation_id:
                try:
                    self.conversations.add_turn(conversation_id, user_input, answer)
                except PyMongoError:
                    print("[WARNING] This turn could not be saved to MongoDB.")
            print(f"Assistant: {answer}")

    def _finish_conversation(self, conversation_id: str | None) -> None:
        if not conversation_id:
            return
        try:
            self.conversations.finish(conversation_id)
        except PyMongoError:
            print("[WARNING] MongoDB could not mark this conversation as finished.")
