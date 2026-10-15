"""The Settings file, in a temporary folder; no display needed."""

from pathlib import Path
import tempfile
import unittest

from settings import Settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "ECOS" / "settings.json"

    def test_a_first_launch_has_sound_music_full_motion_and_portuguese(self):
        settings = Settings(self.path)
        self.assertEqual((settings.sound, settings.music, settings.motion, settings.language), (True, True, True, "pt"))

    def test_a_change_is_kept_for_the_next_session(self):
        Settings(self.path).change(music=False, language="en")
        again = Settings(self.path)
        self.assertEqual((again.sound, again.music, again.motion, again.language), (True, False, True, "en"))

    def test_a_corrupt_file_or_a_strange_value_falls_back_to_that_settings_default(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(Settings(self.path).language, "pt")
        self.path.write_text('{"sound": false, "music": "no", "language": "xx"}', encoding="utf-8")
        settings = Settings(self.path)
        self.assertEqual((settings.sound, settings.music, settings.language), (False, True, "pt"))
        self.path.write_text("[1, 2]", encoding="utf-8")
        self.assertTrue(Settings(self.path).sound)
        self.path.write_text('{"language": ["en"], "motion": {}}', encoding="utf-8")
        self.assertEqual((Settings(self.path).language, Settings(self.path).motion), ("pt", True))

    def test_a_failed_save_keeps_the_change_for_this_session_and_never_raises(self):
        self.path.mkdir(parents=True)                  # a folder where the file should be
        settings = Settings(self.path)
        settings.change(motion=False)
        self.assertFalse(settings.motion)
