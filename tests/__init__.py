"""The tests import the game's modules by name, as the game does from inside src/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
