"""Effects, the Audio the screens use, and the Linux stream, through fake players; no speakers needed."""

from array import array
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import audio
from audio import SOUNDS, Audio, Mixer, effects, widen


class AudioTests(unittest.TestCase):
    def test_every_effect_is_made_once_as_16_bit_samples_at_most_half_loud(self):
        made = effects()
        self.assertEqual(set(made), set(SOUNDS))
        for name, sound in made.items():
            self.assertGreater(len(sound), 0, name)
            self.assertLessEqual(max(map(abs, sound)), 2 ** 14, name)
        self.assertIs(effects(), made)

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
        heard, chest = self.folder / "heard.raw", widen(effects()["chest"])
        fake = (sys.executable, "-c", "import sys; open(sys.argv[1], 'wb').write(sys.stdin.buffer.read(int(sys.argv[2])))",
                str(heard), str(len(chest) + 4096))
        mixer = Mixer(effects(), {})
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
