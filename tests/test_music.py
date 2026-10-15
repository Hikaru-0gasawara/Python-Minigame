"""The Ambience, composed by code: deterministic loops that repeat without a seam and never drown the effects."""

import unittest

import music
from audio import RATE, effects


class MusicTests(unittest.TestCase):
    def test_there_is_a_menu_ambience_one_per_sector_and_two_speeds_of_tension(self):
        self.assertEqual(set(music.PIECES), {"menu", "shallow", "middle", "deep", "tense", "urgent"})

    def test_each_loop_lasts_its_bars_and_comes_out_the_same_every_time(self):
        for name, piece in music.PIECES.items():
            loop = music.compose(name)
            seconds = piece.bars * 4 * 60 / piece.bpm
            self.assertEqual(len(loop), round(seconds * RATE), name)
            self.assertEqual(loop, music.render(piece), name)

    def test_a_loop_is_exactly_one_turn_of_the_music_playing_forever(self):
        for name, piece in music.PIECES.items():
            loop, twice = music.render(piece), music.render(piece, repeats=2)
            self.assertEqual(twice[len(loop):], loop, name)      # tails that cross the end carry on at the start

    def test_the_music_stays_under_the_effects_so_ambience_tension_and_an_effect_never_clip(self):
        loudest = {name: max(map(abs, music.compose(name))) for name in music.PIECES}
        effect = max(max(map(abs, sound)) for sound in effects().values())
        ambience = max(loudest[name] for name in ("menu", "shallow", "middle", "deep"))
        tension = max(loudest["tense"], loudest["urgent"])
        self.assertLess(ambience, effect)
        self.assertLess(ambience + tension + effect, 2 ** 15)
