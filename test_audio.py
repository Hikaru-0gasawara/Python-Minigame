"""Sounds synthesised into a cache folder and played through an injected player; no speakers needed."""

from pathlib import Path
import tempfile
import unittest
from unittest import mock
import wave

import audio
from audio import SOUNDS, Audio


class AudioTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.calls = []

    def test_every_sound_is_generated_once_as_a_wav_file(self):
        Audio(self.calls.append, self.folder)
        files = sorted(self.folder.iterdir())
        self.assertEqual([f.stem for f in files], sorted(SOUNDS))
        for f in files:
            with wave.open(str(f)) as w:
                self.assertEqual((w.getnchannels(), w.getframerate()), (1, audio.RATE))
                self.assertGreater(w.getnframes(), 0)
        written = {f: f.stat().st_mtime_ns for f in files}
        Audio(self.calls.append, self.folder)
        self.assertEqual({f: f.stat().st_mtime_ns for f in files}, written)
        self.assertEqual(self.calls, [])                     # nothing plays at startup

    def test_play_hands_the_file_to_the_player(self):
        sound = Audio(self.calls.append, self.folder)
        sound.play("door")
        self.assertEqual(self.calls, [str(self.folder / "door.wav")])

    def test_mute_stops_what_plays_and_silences_everything_until_unmuted(self):
        sound = Audio(self.calls.append, self.folder)
        sound.toggle_mute()
        for name in SOUNDS:
            sound.play(name)
        self.assertEqual(self.calls, [None])                 # only the stop
        sound.toggle_mute()
        sound.play("blip")
        self.assertEqual(self.calls, [None, str(self.folder / "blip.wav")])

    def test_without_windows_sound_every_call_is_a_silent_no_op(self):
        with mock.patch.object(audio, "winsound", None):
            sound = Audio(folder=self.folder / "never")
        sound.play("chest")
        sound.toggle_mute()
        sound.toggle_mute()
        self.assertIsNone(sound.player)
        self.assertFalse((self.folder / "never").exists())  # nothing is written either


if __name__ == "__main__":
    unittest.main()
