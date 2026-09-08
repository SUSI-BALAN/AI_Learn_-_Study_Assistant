import unittest

from app.cli.commands import Command, parse_command
from app.cli.formatter import help_text
from app.cli.setup_guide import setup_text
from app.memory.short_term import ShortTermMemory
from config import Settings


class PhaseOneTests(unittest.TestCase):
    def test_command_parser_is_allowlisted(self) -> None:
        self.assertEqual(parse_command(" /HELP "), Command.HELP)
        self.assertEqual(parse_command(" /setup "), Command.SETUP)
        self.assertEqual(parse_command(" /STATUS "), Command.STATUS)
        self.assertEqual(parse_command(" /memory "), Command.MEMORY)
        self.assertEqual(parse_command(" /history "), Command.HISTORY)
        self.assertEqual(parse_command(" /conversations "), Command.CONVERSATIONS)
        self.assertEqual(parse_command(" /profile "), Command.PROFILE)
        self.assertEqual(parse_command("bye"), Command.EXIT)
        self.assertEqual(parse_command("leave"), Command.EXIT)
        self.assertEqual(parse_command("goodbye"), Command.EXIT)
        self.assertEqual(parse_command("quit"), Command.EXIT)
        self.assertEqual(parse_command("close"), Command.EXIT)
        self.assertEqual(parse_command("exit"), Command.EXIT)
        self.assertIsNone(parse_command("/delete"))
        self.assertIsNone(parse_command("explain exit command"))

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
        self.assertEqual(settings.sqlite_path.as_posix(), "data/assistant.db")

    def test_beginner_setup_commands_are_visible(self) -> None:
        settings = Settings.load()
        self.assertIn("/setup", help_text())
        guide = setup_text(settings)
        self.assertIn("ollama serve", guide)
        self.assertIn("ollama pull qwen2.5:3b", guide)
        self.assertNotIn("mongod", guide.lower())


if __name__ == "__main__":
    unittest.main()
