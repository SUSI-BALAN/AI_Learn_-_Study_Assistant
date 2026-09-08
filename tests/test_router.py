import unittest

from app.ai.agent import INSUFFICIENT_EVIDENCE, LearningAgent
from app.ai.language_detector import ReplyLanguage, detect_reply_language
from app.ai.prompts import NORMAL_CHAT_PROMPT, RAG_PROMPT
from app.ai.response_style import ResponseStyle, detect_response_style
from app.ai.router import Intent, route_intent
from app.database.sqlite_database import SQLiteDatabase
from app.memory.memory_manager import MemoryManager
from app.memory.short_term import ShortTermMemory
from app.rag.retriever import RetrievedChunk


class FakeClient:
    def __init__(self, response: str = "A direct answer.") -> None:
        self.response = response
        self.calls: list[list[dict[str, str]]] = []
        self.options: list[dict[str, object] | None] = []

    def chat(
        self, messages: list[dict[str, str]], options: dict[str, object] | None = None
    ) -> str:
        self.calls.append(messages)
        self.options.append(options)
        return self.response


class SequenceClient(FakeClient):
    def __init__(self, responses: list[str]) -> None:
        super().__init__()
        self.responses = iter(responses)

    def chat(
        self, messages: list[dict[str, str]], options: dict[str, object] | None = None
    ) -> str:
        self.calls.append(messages)
        self.options.append(options)
        return next(self.responses)


class FakeHealth:
    def __init__(self, count: int) -> None:
        self.count = count


class FakeStore:
    def __init__(self, count: int) -> None:
        self.count = count

    def health(self) -> FakeHealth:
        return FakeHealth(self.count)


class FakeRagService:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.vector_store = FakeStore(len(chunks))
        self.queries: list[str] = []

    def search(self, query: str, **_: object) -> list[RetrievedChunk]:
        self.queries.append(query)
        return self.chunks


class AdaptiveRouterTests(unittest.TestCase):
    def test_route_selection_covers_normal_rag_and_calculator(self) -> None:
        for message in ("hi", "what is IP?", "explain deadlock", "give me 5 DBMS questions"):
            self.assertEqual(route_intent(message), Intent.NORMAL_CHAT)
        for message in (
            "according to my uploaded notes explain deadlock",
            "search my document for deadlock",
            "what does my syllabus say",
        ):
            self.assertEqual(route_intent(message), Intent.RAG_SEARCH)
        for message in (
            "what am I currently learning?",
            "what did we discuss about Python loops?",
            "what is my weakest topic?",
        ):
            self.assertEqual(route_intent(message), Intent.MEMORY_SEARCH)
        self.assertEqual(route_intent("2 + 5 * 10"), Intent.CALCULATOR)

    def test_question_styles_are_adaptive(self) -> None:
        cases = {
            "hi": ResponseStyle.SIMPLE,
            "what is IP?": ResponseStyle.SIMPLE,
            "explain for loop": ResponseStyle.EXPLANATION,
            "explain for loop in detail": ResponseStyle.DETAILED,
            "how to create a Python program?": ResponseStyle.STEPS,
            "give me 5 DBMS questions": ResponseStyle.LIST,
            "summarize OS in 3 lines": ResponseStyle.SUMMARY,
            "Python or C which is better?": ResponseStyle.COMPARISON,
            "what is the best programming language?": ResponseStyle.RECOMMENDATION,
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(detect_response_style(question, greeting=question == "hi"), expected)

    def test_normal_answers_are_model_driven_not_hardcoded(self) -> None:
        cases = (
            ("hi", "Hi! How can I help you today?"),
            ("what are you doing?", "I'm here to answer questions and help you learn."),
            ("what is IP?", "IP stands for Internet Protocol. It supports network communication."),
            ("what is Python?", "Python is a readable general-purpose programming language."),
        )
        for question, model_answer in cases:
            with self.subTest(question=question):
                client = FakeClient(model_answer)
                response = LearningAgent(client, ShortTermMemory()).respond(question)
                self.assertEqual(response.text, model_answer)
                self.assertEqual(len(client.calls), 1)
                self.assertEqual(client.calls[0][0]["content"], NORMAL_CHAT_PROMPT)

    def test_language_selection_supports_english_tamil_and_thanglish(self) -> None:
        self.assertEqual(detect_reply_language("what is IP?"), ReplyLanguage.ENGLISH)
        self.assertEqual(detect_reply_language("IP என்றால் என்ன?"), ReplyLanguage.TAMIL)
        self.assertEqual(detect_reply_language("Python easy ah irukuma?"), ReplyLanguage.THANGLISH)

    def test_normal_chat_uses_only_relevant_history(self) -> None:
        memory = ShortTermMemory(max_turns=6)
        memory.add_turn("What is Python?", "Python is a programming language.")
        memory.add_turn("What is photosynthesis?", "Plants convert light into chemical energy.")

        unrelated = FakeClient("IP is Internet Protocol.")
        LearningAgent(unrelated, memory).respond("what is IP?")
        self.assertEqual(len(unrelated.calls[0]), 2)

        follow_up = FakeClient("Python is easy to read because its syntax is clear.")
        LearningAgent(follow_up, memory).respond("Why is Python easy to learn?")
        contents = [message["content"] for message in follow_up.calls[0]]
        self.assertIn("What is Python?", contents)
        self.assertNotIn("What is photosynthesis?", contents)

    def test_response_length_and_structured_requests(self) -> None:
        simple = LearningAgent(
            FakeClient("One. Two. Three. Four."), ShortTermMemory()
        ).respond("what is testing?")
        self.assertEqual(simple.text, "One. Two. Three.")

        normal = LearningAgent(
            FakeClient("One. Two. Three. Four. Five. Six. Seven."), ShortTermMemory()
        ).respond("Tell me about testing")
        self.assertEqual(normal.text, "One. Two. Three. Four. Five. Six.")

        detailed_text = "Intro.\n1. First detail\n2. Second detail\n3. Third detail"
        detailed = LearningAgent(FakeClient(detailed_text), ShortTermMemory()).respond(
            "Explain testing in detail"
        )
        self.assertEqual(detailed.text, detailed_text)

        list_text = "- Mainframe\n- Supercomputer\n- Personal computer"
        listed = LearningAgent(FakeClient(list_text), ShortTermMemory()).respond(
            "what are the types of computer?"
        )
        self.assertEqual(listed.text, list_text)

        summary_client = FakeClient("First point.\nSecond point.\nThird point.")
        summary = LearningAgent(summary_client, ShortTermMemory()).respond(
            "summarize testing in 3 lines"
        )
        self.assertEqual(summary.text.count("\n"), 2)
        self.assertEqual(len(summary_client.calls), 1)

        retry_client = SequenceClient([
            "First point. Second point.",
            "First point.\nSecond point.\nThird point.",
        ])
        retried = LearningAgent(retry_client, ShortTermMemory()).respond(
            "summarize testing in 3 lines"
        )
        self.assertEqual(retried.text.count("\n"), 2)
        self.assertEqual(len(retry_client.calls), 2)

        semicolon_client = SequenceClient([
            "One point; second point; third point.",
            "One point; second point; third point.",
        ])
        semicolon_summary = LearningAgent(semicolon_client, ShortTermMemory()).respond(
            "summarize testing in 3 lines"
        )
        self.assertEqual(semicolon_summary.text.splitlines(), [
            "One point", "second point", "third point."
        ])

    def test_calculator_is_deterministic_and_does_not_call_model(self) -> None:
        client = FakeClient("wrong")
        response = LearningAgent(client, ShortTermMemory()).respond("2 + 5 * 10")
        self.assertEqual(response.intent, Intent.CALCULATOR)
        self.assertEqual(response.text, "52")
        self.assertEqual(client.calls, [])

    def test_memory_search_is_deterministic_and_does_not_call_model(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            database = SQLiteDatabase(Path(directory) / "assistant.db")
            database.connect()
            manager = MemoryManager(ShortTermMemory(), database.connection)
            try:
                manager.start()
                manager.add_turn("I am learning DBMS.", "Stored.")
                client = FakeClient("wrong")
                response = LearningAgent(client, manager).respond("What am I currently learning?")
                self.assertEqual(response.intent, Intent.MEMORY_SEARCH)
                self.assertIn("DBMS", response.text)
                self.assertEqual(client.calls, [])
            finally:
                manager.finish()
                database.close()

    def test_empty_rag_store_sends_no_context_to_model(self) -> None:
        client = FakeClient()
        rag = FakeRagService([])
        response = LearningAgent(client, ShortTermMemory(), rag).respond(
            "according to my uploaded notes explain deadlock"
        )
        self.assertEqual(response.intent, Intent.RAG_SEARCH)
        self.assertEqual(response.text, INSUFFICIENT_EVIDENCE)
        self.assertEqual(client.calls, [])
        self.assertEqual(rag.queries, [])

    def test_rag_prompt_and_material_remain_separate(self) -> None:
        client = FakeClient("Deadlock is a circular wait.")
        chunk = RetrievedChunk(
            "A deadlock is a circular wait.",
            {"file_name": "os_notes.pdf", "file_type": "pdf", "page_number": 4},
            0.8,
        )
        response = LearningAgent(client, ShortTermMemory(), FakeRagService([chunk])).respond(
            "according to my uploaded notes explain deadlock"
        )
        self.assertEqual(response.intent, Intent.RAG_SEARCH)
        self.assertEqual(client.calls[0][0]["content"], RAG_PROMPT)
        self.assertNotEqual(client.calls[0][0]["content"], NORMAL_CHAT_PROMPT)
        self.assertIn("os_notes.pdf — Page 4", response.text)

    def test_multilingual_output_and_duplicate_guard_are_preserved(self) -> None:
        tamil = "IP என்பது Internet Protocol. இது network தொடர்புக்கு பயன்படுகிறது."
        self.assertEqual(
            LearningAgent(FakeClient(tamil), ShortTermMemory()).respond("IP என்றால் என்ன?").text,
            tamil,
        )
        memory = ShortTermMemory()
        previous = "Python is a readable programming language."
        memory.add_turn("What is Python?", previous)
        repeated = LearningAgent(FakeClient(previous), memory).respond("Explain Python")
        self.assertEqual(
            repeated.text, "I've already answered that. Ask me if you want a different explanation."
        )


if __name__ == "__main__":
    unittest.main()
