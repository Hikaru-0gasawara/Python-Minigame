"""The game's icon, drawn by code; no display needed."""

import struct
import unittest

from icon import icon_png
from menu_art import CORE_SIZE


class IconTests(unittest.TestCase):
    def test_the_icon_is_a_png_of_the_core_at_any_whole_scale(self):
        for scale in (1, 4):
            data = icon_png(scale)
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack("!2I", data[16:24]), (CORE_SIZE * scale,) * 2)
