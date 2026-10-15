"""The player's Settings, kept between sessions beside the Records (ADR-0003). Independent of Tk.

A missing or unreadable file, or an unknown value, means that Setting's default;
a failed save keeps the change for this session only and never stops the game.
"""

import json
import os
from pathlib import Path

from lang import LANGUAGES
from records import data_folder

DEFAULTS = {"sound": True, "music": True, "motion": True, "language": "pt"}


def valid(name, value):
    return value in LANGUAGES if name == "language" else isinstance(value, bool)


class Settings:
    """`sound`, `music`, `motion` (full or reduced) and `language`, read once and saved on every change."""

    def __init__(self, path=None):
        self.path = Path(path) if path else data_folder() / "settings.json"
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        if not isinstance(saved, dict):
            saved = {}
        for name, default in DEFAULTS.items():
            setattr(self, name, saved[name] if valid(name, saved.get(name)) else default)

    def change(self, **values):
        for name, value in values.items():
            setattr(self, name, value)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps({name: getattr(self, name) for name in DEFAULTS}, indent=1),
                                 encoding="utf-8")
            os.replace(temporary, self.path)          # never leave a half-written file behind
        except OSError:
            pass
