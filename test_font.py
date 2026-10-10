"""Bitmap font coverage, measuring, wrapping and drawing; no display needed."""

import ast
import json
from pathlib import Path
import unicodedata
import unittest

import font
from pixels import Pix

ROOT = Path(__file__).parent
SCREEN_MODULES = ("dungeon.py", "dungeon_ui.py", "menu_ui.py", "questions.py", "scene.py")


def used_characters():
    """Every character of the question bank and of every string literal the screens use."""
    chars = set()
    for tier in ("easy", "medium", "hard"):
        for q in json.loads((ROOT / f"{tier}_questions.json").read_text(encoding="utf-8")):
            chars |= set(q["question"]) | set(q["answer"])
    for name in SCREEN_MODULES:
        for node in ast.walk(ast.parse((ROOT / name).read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                chars |= set(node.value)
    return {c for c in chars if c.isprintable()}


class FontTests(unittest.TestCase):
    def test_every_used_character_has_a_glyph(self):
        missing = sorted(c for c in used_characters() if not font.known(c))
        self.assertEqual(missing, [])

    def test_portuguese_letters_are_composed_with_their_accents(self):
        for ch in "áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ":
            with self.subTest(ch=ch):
                plain = unicodedata.normalize("NFD", ch)[0]
                self.assertTrue(font.known(ch))
                self.assertNotEqual(font.glyph(ch)[1], font.glyph(plain)[1])
        self.assertNotEqual(font.glyph("ã")[1], font.glyph("á")[1])

    def test_accents_never_touch_their_letter(self):
        for ch in "ÁÃÊÍÕÚáãêíõú":
            _, pixels = font.glyph(ch)
            rows = {y for _, y in pixels}
            gap = font.TOP - 1 if ch.isupper() else font.TOP + 1
            self.assertNotIn(gap, rows, ch)
        self.assertEqual(max(y for _, y in font.glyph("ç")[1]), font.HEIGHT - 1)

    def test_unknown_characters_draw_a_visible_box(self):
        self.assertFalse(font.known("☃"))
        width, pixels = font.glyph("☃")
        self.assertGreater(width, 0)
        self.assertTrue(pixels)
        font.draw(Pix(20, font.HEIGHT), 0, 0, "☃", 5)

    def test_measure_adds_one_pixel_between_glyphs(self):
        self.assertEqual(font.measure(""), 0)
        self.assertEqual(font.measure("a"), font.glyph("a")[0])
        self.assertEqual(font.measure("ab"), font.glyph("a")[0] + 1 + font.glyph("b")[0])

    def test_wrap_keeps_every_line_within_the_width_and_every_word(self):
        text = ("Which discovery changed the way we understand the universe, and which scientist "
                "presented the explanation? Pneumonoultramicroscopicsilicovolcanoconiosis ok\nNova linha")
        for width in (40, 100, 200, 308):
            with self.subTest(width=width):
                lines = font.wrap(text, width)
                self.assertTrue(all(font.measure(line) <= width for line in lines))
                self.assertEqual("".join("".join(lines).split()), "".join(text.split()))
        self.assertEqual(font.wrap("um dois\ntrês", 500), ["um dois", "três"])
        long_word = font.wrap("x" * 40, 30)
        self.assertGreater(len(long_word), 1)

    def test_draw_uses_only_the_given_colours_and_offsets_the_shadow(self):
        pix = Pix(80, font.HEIGHT + 1)
        width = font.draw(pix, 2, 0, "Ação!", 10, shadow=1)
        self.assertEqual(width, font.measure("Ação!"))
        self.assertEqual({c for c in pix.px if c is not None}, {1, 10})
        lit = {(i % pix.w, i // pix.w) for i, c in enumerate(pix.px) if c == 10}
        shade = {(i % pix.w, i // pix.w) for i, c in enumerate(pix.px) if c == 1}
        self.assertTrue(all((x + 1, y + 1) in lit | shade for x, y in lit))


if __name__ == "__main__":
    unittest.main()
