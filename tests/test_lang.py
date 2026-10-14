"""The chosen language: every on-screen text has its English, and both question banks line up."""

import ast
from pathlib import Path
import unittest

import dungeon
import font
import hud
import lang
import menu_ui
import props
import scene
from questions import TIERS, is_correct, load_tier

SRC = Path(__file__).resolve().parent.parent / "src"


def literals(node):
    """The string literals an expression can evaluate to: itself, or either side of an `a if x else b`."""
    if isinstance(node, ast.IfExp):
        return literals(node.body) | literals(node.orelse)
    return {node.value} if isinstance(node, ast.Constant) and isinstance(node.value, str) else set()


def translated_texts():
    """Every literal handed to t() in the code, plus the tables whose entries reach it through a variable."""
    texts = set()
    for path in SRC.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "t":
                texts |= literals(node.args[0])
    for name, hint, *_ in dungeon.ROOMS.values():
        texts |= {name, hint}
    texts |= {mode[0] for mode in dungeon.MODES.values()} | set(dungeon.EFFECT_TEXT.values())
    texts |= {line for lines in dungeon.TAUNTS.values() for line in lines}
    texts |= {text for letter, name, _ in scene.COMPASS for text in (letter, name)} | set(props.GRAFFITI)
    for table in (hud.SECTOR_NAMES, hud.TIER_NAMES, hud.POWER_NAMES, menu_ui.LABELS):
        texts |= set(table.values())
    return texts | set(hud.ACTIONS) | set(hud.PAUSE_ACTIONS) | {menu_ui.HINT}


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(setattr, lang, "current", lang.current)

    def test_every_on_screen_text_has_its_english(self):
        self.assertEqual(sorted(translated_texts() - set(lang.EN)), [])
        for line in (line for lines in dungeon.TAUNTS.values() for line in lines):
            self.assertLessEqual(font.measure(lang.EN[line]), hud.BOX_WIDTH - 8, line)   # one line in the box

    def test_an_expedition_speaks_the_chosen_language(self):
        lang.current = "en"
        game = dungeon.Expedition(dungeon.EASY, players=2, seed=42)
        self.assertEqual(game.name, "Adventurer")
        self.assertEqual(hud.badge(game).texts, ["P1 · ENTRANCE · SHALLOW"])
        lang.current = "pt"
        self.assertEqual(hud.badge(game).texts, ["J1 · ENTRADA · RASO"])

    def test_both_banks_ask_the_same_questions_in_the_same_order(self):
        for tier in TIERS:
            banks = []
            for lang.current in lang.LANGUAGES:
                questions, fallback = load_tier(tier)
                self.assertFalse(fallback)
                banks.append(questions)
            self.assertEqual(*map(len, banks))       # so a Seed asks the same things in either language
            for en, pt in zip(*reversed(banks)):
                self.assertEqual("options" in en, "options" in pt, en["question"])
                if "options" in en:
                    self.assertEqual(en["options"].index(en["answer"]), pt["options"].index(pt["answer"]))

    def test_answers_forgive_accents_and_multiple_choice_takes_a_letter(self):
        self.assertTrue(is_correct({"question": "?", "answer": "são tomé e príncipe"}, "Sao Tome e Principe"))
        self.assertTrue(is_correct({"question": "?", "answer": "beija-flor-abelha"}, "beija flor abelha"))
        self.assertTrue(is_correct({"question": "?", "answer": "67,5"}, "67.5"))
        self.assertFalse(is_correct({"question": "?", "answer": "-273,15"}, "273,15"))
        choice = {"question": "?", "options": ["cenoura", "maçã", "batata", "cebola"], "answer": "maçã"}
        self.assertTrue(is_correct(choice, "b"))
        self.assertTrue(is_correct(choice, "maca"))
        self.assertFalse(is_correct(choice, "a"))
        self.assertEqual(hud.asked_lines(choice), ["?", "A) cenoura   B) maçã   C) batata   D) cebola"])
