"""Effects, the mixer (chunk by chunk, from tiny hand-made sounds), the Audio the screens use,
and the Linux stream through fake players; no speakers needed."""

from array import array
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import audio
from audio import SOUNDS, Audio, Mixer, effect_samples, widen


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
        mixer.chunk(4)                                # shallow has faded in from silence
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

    def test_a_change_during_a_fade_waits_for_it_instead_of_cutting_the_sound(self):
        mixer = Mixer({}, {"shallow": tone(0, 0), "deep": tone(100, 100), "middle": tone(40, 40)}, fade=4)
        mixer.ambience("shallow")
        mixer.chunk(4)
        mixer.ambience("deep")
        self.assertEqual(list(mixer.chunk(2)), [0, 25])
        mixer.ambience("middle")                      # mid-fade: deep finishes coming in, then middle
        self.assertEqual(list(mixer.chunk(8)), [50, 75, 100, 85, 70, 55, 40, 40])


class AudioTests(unittest.TestCase):
    def test_every_effect_is_made_once_as_16_bit_samples_at_most_half_loud(self):
        made = effect_samples()
        self.assertEqual(set(made), set(SOUNDS))
        for name, sound in made.items():
            self.assertGreater(len(sound), 0, name)
            self.assertLessEqual(max(map(abs, sound)), 2 ** 14, name)
        self.assertIs(effect_samples(), made)

    def test_effects_sound_until_muted_and_muting_cuts_what_plays(self):
        heard = []
        sound = Audio(silent=True, listener=heard.append)
        sound.play("door")
        sound.muted = True
        sound.play("chest")
        sound.muted = False
        sound.play("blip")
        self.assertEqual(heard, ["door", None, "blip"])

    def test_the_stream_repeats_each_sample_on_two_frames_and_two_channels(self):
        self.assertEqual(widen(array("h", (1, -2))), struct.pack("<8h", 1, 1, 1, 1, -2, -2, -2, -2))


class LinuxStreamTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)

    def test_linux_streams_to_the_first_player_installed(self):
        installed = {"pacat", "aplay"}
        self.assertEqual(audio.linux_command(lambda name: name in installed and f"/usr/bin/{name}")[0], "pacat")
        self.assertIsNone(audio.linux_command(lambda name: None))

    def test_the_mixed_stream_flows_into_the_system_player(self):
        heard, chest = self.folder / "heard.raw", widen(effect_samples()["chest"])
        fake = (sys.executable, "-c", "import sys; open(sys.argv[1], 'wb').write(sys.stdin.buffer.read(int(sys.argv[2])))",
                str(heard), str(len(chest) + 4096))
        mixer = Mixer(effect_samples(), {})
        mixer.play("chest")
        process = audio.pipe_output(fake)(lambda samples: widen(mixer.chunk(samples)))
        self.addCleanup(process.stdin.close)
        process.wait(timeout=10)
        self.assertTrue(heard.read_bytes().startswith(chest))

    def test_a_player_that_quits_leaves_the_game_silent_not_broken(self):
        process = audio.pipe_output((sys.executable, "-c", "pass"))(lambda samples: bytes(4 * 2 * samples))
        self.addCleanup(process.stdin.close)
        process.wait(timeout=10)
        self.assertIsNone(audio.pipe_output(("no-such-player-anywhere",))(lambda samples: b""))
