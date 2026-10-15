"""The five best escape times per Difficulty, kept between sessions (ADR-0003). Independent of Tk.

A Record is {"seconds", "seed", "players", "date"}. The file lives in the
user's data folder; a missing or unreadable one is an empty scoreboard, and a
failed save loses the new Record but never the game.
"""

from datetime import date
import json
import math
from pathlib import Path

from storage import data_folder, save_json

KEEP = 5


def default_path():
    return data_folder() / "records.json"


class Records:
    def __init__(self, path=None, today=date.today):
        self.path = Path(path) if path else default_path()
        self.today = today

    def _load(self):
        """Every Difficulty's Records, sorted; anything malformed makes the whole file read as empty."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            board = {int(difficulty): sorted(({"seconds": float(r["seconds"]), "seed": int(r["seed"]),
                                               "players": int(r["players"]), "date": str(r["date"])}
                                              for r in records), key=lambda r: r["seconds"])[:KEEP]
                     for difficulty, records in data.items()}
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            return {}
        # Python's JSON reads NaN, Infinity and 1e999 as floats; none of them is a time.
        return board if all(math.isfinite(r["seconds"]) for records in board.values() for r in records) else {}

    def top(self, difficulty):
        return self._load().get(difficulty, [])

    def submit(self, difficulty, seconds, seed, players):
        """Keep a finished time if it is among the five best; returns its rank (1-5) or None."""
        board = self._load()
        record = {"seconds": seconds, "seed": seed, "players": players, "date": self.today().isoformat()}
        records = board.setdefault(difficulty, [])
        records.append(record)
        records.sort(key=lambda r: r["seconds"])      # stable: a tie ranks behind the older time
        del records[KEEP:]
        if not any(r is record for r in records):
            return None
        save_json(self.path, board)
        return next(i for i, r in enumerate(records) if r is record) + 1
