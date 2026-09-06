import unittest

from app.cli.commands import Command, parse_command
from app.memory.short_term import ShortTermMemory
from config import Settings


class PhaseOneTests(unittest.TestCase):
    def test_command_parser_is_allowlisted(self) -> None:
        self.assertEqual(parse_command(" /HELP "), Command.HELP)
        self.assertIsNone(parse_command("/delete"))

    def test_memory_is_bounded_by_turns(self) -> None:
        memory = ShortTermMemory(max_turns=2)
        for number in range(3):
            memory.add_turn(f"u{number}", f"a{number}")
        self.assertEqual([item["content"] for item in memory.messages()], ["u1", "a1", "u2", "a2"])
        memory.clear()
        self.assertEqual(memory.messages(), [])

    def test_relevant_memory_supports_thanglish_and_tamil_follow_ups(self) -> None:
        memory = ShortTermMemory(max_turns=3)
        memory.add_turn("Deadlock na enna?", "Deadlock என்பது circular wait.")
        self.assertEqual(len(memory.relevant_messages("adha innum explain pannunga")), 2)
        self.assertEqual(len(memory.relevant_messages("அதை மேலும் விளக்கவும்")), 2)

    def test_settings_have_offline_defaults(self) -> None:
        settings = Settings.load()
        self.assertFalse(settings.internet_search_enabled)
        self.assertEqual(settings.ollama_model, "qwen2.5:3b")
        self.assertEqual(settings.ollama_fallback_model, "tinyllama")


if __name__ == "__main__":
    unittest.main()
