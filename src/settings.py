"""The player's Settings, kept between sessions beside the Records (ADR-0003). Independent of Tk.

A missing or unreadable file, or an unknown value, means that Setting's default;
a failed save keeps the change for this session only and never stops the game.
"""

import json
from pathlib import Path

from lang import LANGUAGES
from storage import data_folder, save_json

DEFAULTS = {"sound": True, "music": True, "motion": True, "language": "pt"}


def valid(name, value):
    return isinstance(value, str) and value in LANGUAGES if name == "language" else isinstance(value, bool)


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
        save_json(self.path, {name: getattr(self, name) for name in DEFAULTS})
