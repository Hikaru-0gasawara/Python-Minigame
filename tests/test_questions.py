"""Question bank: Tier files, fallback and draws without repeats."""

import random
import unittest

from questions import FALLBACK, TIERS, QuestionBank, is_correct, load_tier


class QuestionBankTests(unittest.TestCase):
    def test_every_tier_loads_from_its_file(self):
        bank = QuestionBank()
        self.assertFalse(bank.fallback)
        for tier in TIERS:
            self.assertGreater(len(bank.tiers[tier]), len(FALLBACK))
            self.assertTrue(all({"question", "answer"} <= set(q) for q in bank.tiers[tier]))

    def test_missing_file_falls_back_to_builtin_questions(self):
        self.assertEqual(load_tier("missing"), (FALLBACK, True))

    def test_draws_never_repeat_until_the_tier_is_exhausted(self):
        bank = QuestionBank()
        rng = random.Random(7)
        pool = bank.tiers["easy"]
        drawn = [bank.draw("easy", rng) for _ in pool]
        self.assertEqual(sorted(map(id, drawn)), sorted(map(id, pool)))
        self.assertIn(bank.draw("easy", rng), pool)
        self.assertEqual(len(bank.tiers["easy"]), len(pool))

    def test_answers_ignore_case_and_surrounding_spaces(self):
        question = {"question": "?", "answer": " Python "}
        self.assertTrue(is_correct(question, "python  "))
        self.assertFalse(is_correct(question, "java"))
