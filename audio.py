"""Short sounds synthesised at startup and played through Windows' standard sound module.

The sounds are written once to a cache folder, since Windows only plays from
memory synchronously. A new sound cuts the one playing. Without Windows sound
support every call is a silent no-op.
"""

import io
from pathlib import Path
import random
import tempfile
import wave

try:
    import winsound
except ImportError:          # not Windows
    winsound = None

RATE = 22050
_rng = random.Random(7)
NOISE = [_rng.uniform(-1, 1) for _ in range(4096)]

# Each sound is notes played one after another: (start Hz, end Hz, seconds, shape, volume).
SOUNDS = {
    "blip": [(330, 330, .035, "square", .3)],
    "door": [(2400, 500, .3, "noise", .35), (70, 45, .1, "square", .3)],
    "chest": [(523, 523, .06, "square", .3), (659, 659, .06, "square", .3),
              (784, 784, .06, "square", .3), (1047, 1047, .2, "square", .3)],
    "trap": [(900, 120, .25, "square", .35), (3000, 300, .2, "noise", .4)],
    "correct": [(660, 660, .08, "triangle", .5), (990, 990, .22, "triangle", .5)],
    "wrong": [(220, 220, .12, "square", .35), (147, 140, .3, "square", .35)],
}


def samples(notes):
    """Each note sweeps its pitch and fades out; noise is pitched by how fast it steps through a table."""
    out = []
    for f0, f1, seconds, shape, volume in notes:
        n, phase = int(RATE * seconds), 0.
        for i in range(n):
            t = i / n
            phase += (f0 + (f1 - f0) * t) / RATE
            if shape == "square":
                v = 1 if phase % 1 < .5 else -1
            elif shape == "triangle":
                v = 4 * abs(phase % 1 - .5) - 1
            else:
                v = NOISE[int(phase) % len(NOISE)]
            out.append(v * volume * (1 - t))
    return out


def wav(notes):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)        # 8-bit samples are unsigned, centred on 128
        w.setframerate(RATE)
        w.writeframes(bytes(round(128 + 127 * v) for v in samples(notes)))
    return buffer.getvalue()


def cache(folder=None):
    """Write every sound to the cache folder, unless an identical file is already there."""
    folder = Path(folder or Path(tempfile.gettempdir()) / "ecos-sounds")
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, notes in SOUNDS.items():
        path, data = folder / f"{name}.wav", wav(notes)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        files[name] = str(path)
    return files


def windows_player():
    """Play a file asynchronously, cutting the previous sound; None stops it. None without winsound."""
    if winsound is None:
        return None
    flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT

    def play(path):
        try:
            winsound.PlaySound(path, flags if path else 0)
        except RuntimeError:      # no output device: stay silent
            pass
    return play


class Audio:
    def __init__(self, player=None, folder=None):
        """`player(path)` plays a file and `player(None)` stops; by default Windows' own, if any."""
        self.player = player or windows_player()
        self.muted = False
        self.files = {}
        if self.player:
            try:
                self.files = cache(folder)
            except OSError:       # an unwritable cache folder means a silent game, not a crash
                self.player = None

    def play(self, name):
        if self.player and not self.muted:
            self.player(self.files[name])

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted and self.player:
            self.player(None)     # silence what is already playing
