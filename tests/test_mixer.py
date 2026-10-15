"""The mixer: what the speakers get, chunk by chunk, built from tiny hand-made sounds; no speakers needed."""

from array import array
import unittest

from audio import Mixer


def tone(*values):
    return array("h", values)


class MixerTests(unittest.TestCase):
    def setUp(self):
        self.mixer = Mixer({"door": tone(7, 8, 9), "blip": tone(1, 1)},
                           {"shallow": tone(10, 20, 30), "deep": tone(100, 100), "tense": tone(5, 0)}, fade=0)

    def heard(self, frames):
        return list(self.mixer.chunk(frames))

    def test_nothing_playing_is_silence(self):
        self.assertEqual(self.heard(3), [0, 0, 0])

    def test_an_effect_plays_once_over_the_looping_ambience(self):
        self.mixer.ambience("shallow")
        self.mixer.play("door")
        self.assertEqual(self.heard(5), [17, 28, 39, 10, 20])
        self.assertEqual(self.heard(3), [30, 10, 20])

    def test_a_new_effect_cuts_the_effect_playing_but_never_the_music(self):
        self.mixer.ambience("deep")
        self.mixer.play("door")
        self.heard(1)
        self.mixer.play("blip")
        self.assertEqual(self.heard(3), [101, 101, 100])

    def test_a_new_ambience_fades_in_over_the_old_one(self):
        mixer = Mixer({}, {"shallow": tone(0, 0), "deep": tone(100, 100)}, fade=4)
        mixer.ambience("shallow")
        mixer.chunk(2)
        mixer.ambience("deep")
        self.assertEqual(list(mixer.chunk(6)), [0, 25, 50, 75, 100, 100])
        mixer.ambience("deep")                        # the same Ambience again changes nothing
        self.assertEqual(list(mixer.chunk(2)), [100, 100])

    def test_tension_ticks_over_the_ambience_and_stops_with_the_question(self):
        self.mixer.ambience("deep")
        self.mixer.tension("tense")
        self.assertEqual(self.heard(3), [105, 100, 105])
        self.mixer.tension(None)
        self.assertEqual(self.heard(2), [100, 100])

    def test_muted_is_silence_and_the_cut_effect_does_not_come_back(self):
        self.mixer.ambience("deep")
        self.mixer.play("door")
        self.mixer.muted = True
        self.assertEqual(self.heard(2), [0, 0])
        self.mixer.muted = False
        self.assertEqual(self.heard(2), [100, 100])

    def test_music_off_keeps_the_effects(self):
        self.mixer.ambience("deep")
        self.mixer.tension("tense")
        self.mixer.music_on = False
        self.mixer.play("blip")
        self.assertEqual(self.heard(3), [1, 1, 0])

    def test_an_ambience_not_composed_yet_is_silence(self):
        self.mixer.ambience("middle")
        self.mixer.play("blip")
        self.assertEqual(self.heard(3), [1, 1, 0])
