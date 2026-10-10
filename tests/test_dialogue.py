"""The Guardian's lines revealed letter by letter; no display needed."""

import unittest

from dialogue import CHARS_PER_SECOND, Dialogue


class DialogueTests(unittest.TestCase):
    def test_letters_appear_over_time_and_lines_keep_their_places(self):
        d = Dialogue(["Mais um.", "What is 2 + 2?"], start=10)
        self.assertEqual(d.shown(10), ["", ""])
        self.assertEqual(d.shown(10 + 5 / CHARS_PER_SECOND), ["Mais ", ""])
        self.assertEqual(d.shown(10 + 11 / CHARS_PER_SECOND), ["Mais um.", "Wha"])
        self.assertFalse(d.done(10 + 11 / CHARS_PER_SECOND))
        self.assertEqual(d.shown(1000), ["Mais um.", "What is 2 + 2?"])
        self.assertTrue(d.done(1000))
        self.assertEqual(d.shown(0), ["", ""])                  # nothing before it starts

    def test_completing_shows_everything_at_once(self):
        d = Dialogue(["Uma frase.", "Outra."], start=10)
        d.complete()
        self.assertTrue(d.done(10))
        self.assertEqual(d.shown(10), ["Uma frase.", "Outra."])

    def test_voice_counts_only_new_letters_not_spaces(self):
        d = Dialogue(["ab cd"], start=0)
        self.assertEqual(d.voiced(0, 3 / CHARS_PER_SECOND), 2)  # "ab " has two letters
        self.assertEqual(d.voiced(3, 1), 2)                     # then "cd"
        self.assertEqual(d.voiced(5, 2), 0)
