"""The game's icon: ECO's core at its brightest, drawn by code like everything else (ADR-0004). Independent of Tk.

`python3 src/icon.py <file>` writes it as a PNG; instalar.sh does so for the Linux app menu.
"""

from pathlib import Path
import sys

from menu_art import CORE_FRAMES, CORE_SIZE, core
from pixels import png


def icon_png(scale=1):
    """The core as a PNG, each of its pixels a `scale`-wide square."""
    art, size = core(CORE_FRAMES - 1), CORE_SIZE * scale
    return png(size, size, [art.px[y // scale * CORE_SIZE + x // scale] for y in range(size) for x in range(size)])


if __name__ == "__main__":
    Path(sys.argv[1]).write_bytes(icon_png(4))
