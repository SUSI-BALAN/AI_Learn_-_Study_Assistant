import unittest

from app.memory.memory_classifier import MemoryCategory, classify_memory


class MemoryClassifierTests(unittest.TestCase):
    def test_ignores_greetings(self) -> None:
        self.assertEqual(classify_memory("hi").category, MemoryCategory.IGNORE)

    def test_detects_language_preferences(self) -> None:
        classified = classify_memory("I prefer Thanglish.")
        self.assertEqual(classified.category, MemoryCategory.PREFERENCE)
        self.assertEqual(classified.stable_key, "preferred_language")
        self.assertEqual(classified.value, "thanglish")

        updated = classify_memory("From now answer me in English.")
        self.assertEqual(updated.stable_key, "preferred_language")
        self.assertEqual(updated.value, "english")

    def test_detects_progress_goal_and_weak_topic(self) -> None:
        self.assertEqual(
            classify_memory("I finished DBMS normalization.").category,
            MemoryCategory.PROGRESS,
        )
        self.assertEqual(
            classify_memory("My exam is September 25.").category,
            MemoryCategory.GOAL,
        )
        self.assertEqual(
            classify_memory("I am weak in nested loops.").category,
            MemoryCategory.WEAK_TOPIC,
        )


if __name__ == "__main__":
    unittest.main()
