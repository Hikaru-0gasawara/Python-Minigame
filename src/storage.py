"""Where what outlives a session is kept: the Records and the Settings (ADR-0003). Independent of Tk."""

import json
import os
from pathlib import Path


def data_folder():
    """The game's folder among the user's data: %APPDATA% on Windows; elsewhere XDG's data folder,
    ~/.local/share unless $XDG_DATA_HOME says otherwise."""
    base = os.environ.get("APPDATA") or os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "ECOS"


def save_json(path, data):
    """Write `data` as JSON without ever leaving a half-written file; a failure is silent."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        pass
