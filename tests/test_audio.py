"""Sounds synthesised into a cache folder and played through an injected player; no speakers needed."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import wave

import audio
from audio import SOUNDS, Audio, Stream, StreamPlayer


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

    def test_without_a_system_player_every_call_is_a_silent_no_op(self):
        with mock.patch.object(audio, "winsound", None), mock.patch.object(audio, "linux_player", lambda: None):
            sound = Audio(folder=self.folder / "never")
        sound.play("chest")
        sound.toggle_mute()
        sound.toggle_mute()
        self.assertIsNone(sound.player)
        self.assertFalse((self.folder / "never").exists())  # nothing is written either


class LinuxStreamTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)

    def test_linux_uses_the_first_player_installed(self):
        installed = {"pacat", "aplay"}
        player = audio.linux_player(lambda name: name in installed and f"/usr/bin/{name}")
        self.assertEqual(player.command[0], "pacat")
        self.assertIsNone(audio.linux_player(lambda name: None))

    def test_a_sound_plays_through_then_silence_and_a_new_sound_cuts_the_old(self):
        stream = Stream()
        self.assertEqual(stream.chunk(4), bytes(4))
        stream.play(b"abcdef")
        self.assertEqual(stream.chunk(4) + stream.chunk(4), b"abcdef" + bytes(2))
        stream.play(b"123456")
        stream.chunk(2)
        stream.play(b"xy")                                   # cut halfway
        self.assertEqual(stream.chunk(4), b"xy" + bytes(2))
        stream.play(b"")                                     # a stop is silence at once
        self.assertEqual(stream.chunk(4), bytes(4))

    def test_samples_are_16_bit_stereo_at_the_stream_rate(self):
        path = audio.cache(self.folder)["door"]
        with wave.open(path) as w:
            frames = w.getnframes()
        data = audio.stream_samples(path)
        self.assertEqual(len(data), frames * audio.OUT_RATE // audio.RATE * 4)
        self.assertEqual(data[:2], data[2:4])                 # both channels alike

    def test_the_player_streams_the_sound_into_the_system_player(self):
        path, heard = audio.cache(self.folder)["chest"], self.folder / "heard.raw"
        sound = audio.stream_samples(path)
        wanted = 2 ** 16 + 2 * len(sound)                    # enough to hold any silence before the sound
        fake = (sys.executable, "-c", "import sys; open(sys.argv[1], 'wb').write(sys.stdin.buffer.read(int(sys.argv[2])))",
                str(heard), str(wanted))
        player = StreamPlayer(fake)
        player(path)
        self.addCleanup(player.process.stdin.close)
        player.process.wait(timeout=10)
        self.assertIn(sound, heard.read_bytes())

    def test_a_player_that_quits_leaves_the_game_silent_not_broken(self):
        path = audio.cache(self.folder)["blip"]
        player = StreamPlayer((sys.executable, "-c", "pass"))
        player(path)
        self.addCleanup(player.process.stdin.close)
        player.process.wait(timeout=10)
        player(path)                                         # writing into nothing raises nowhere
        player(None)
