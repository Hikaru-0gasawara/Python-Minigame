"""Short sounds synthesised at startup and played through the system's own sound.

The sounds are written once to a cache folder. On Windows the standard sound
module plays the files, since it only plays from memory synchronously. On Linux
the first command-line player installed (PipeWire's, PulseAudio's, then ALSA's)
receives one endless stream of samples. Either way a new sound cuts the one
playing, and without any of them every call is a silent no-op.
"""

import array
import functools
import io
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import wave

try:
    import winsound
except ImportError:          # not Windows
    winsound = None
try:
    import fcntl
except ImportError:          # Windows
    fcntl = None

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


# Linux's stream: 16-bit stereo at the system's usual rate, written a chunk (about 5 ms) at a time.
OUT_RATE, CHUNK = 48000, 1024
PIPE_SIZE = 4096             # one page: about 21 ms of sound queued behind the player, never seconds
LINUX_PLAYERS = (            # in order of preference, each reading raw samples from its input
    ("pw-cat", "--playback", "--raw", "--format=s16", f"--rate={OUT_RATE}", "--channels=2",
     "--latency=20ms", "--media-role=Game", "-"),
    ("pacat", "--playback", "--raw", "--format=s16le", f"--rate={OUT_RATE}", "--channels=2",
     "--latency-msec=20", "--client-name=ECOS"),
    ("aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(OUT_RATE), "-c", "2", "--buffer-time=20000", "-"),
)


@functools.lru_cache(maxsize=None)
def stream_samples(path):
    """A cached sound as Linux's stream plays it: each 8-bit sample becomes 16-bit, on both channels."""
    with wave.open(path) as w:
        frames = w.readframes(w.getnframes())
    out = array.array("h")
    for i in range(len(frames) * OUT_RATE // RATE):
        v = (frames[i * RATE // OUT_RATE] - 128) * 256
        out.extend((v, v))
    if sys.byteorder == "big":
        out.byteswap()
    return out.tobytes()


class Stream:
    """What the Linux player gets next: the current sound, then silence. A new sound cuts the old one."""

    def __init__(self):
        self.lock = threading.Lock()
        self.sound, self.at = b"", 0

    def play(self, sound):
        with self.lock:
            self.sound, self.at = sound, 0

    def chunk(self, size=CHUNK):
        with self.lock:
            part = self.sound[self.at:self.at + size]
            self.at += len(part)
        return part + bytes(size - len(part))


class StreamPlayer:
    """Play a file by streaming it to a system player; None stops it.

    The player starts with the first sound and lives as long as the game, fed
    silence in between. Its input pipe is shrunk to one page, so a sound waits
    behind milliseconds of audio, not seconds. If the player quits (no sound
    server, say), the game goes on in silence.
    """

    def __init__(self, command):
        self.command, self.stream, self.process = command, Stream(), None

    def __call__(self, path):
        if self.process is None:
            self.process = self.start()
        self.stream.play(stream_samples(path) if path else b"")

    def start(self):
        try:
            process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, bufsize=0)
        except OSError:
            return False
        try:
            fcntl.fcntl(process.stdin, fcntl.F_SETPIPE_SZ, PIPE_SIZE)
        except (AttributeError, OSError):     # not Linux: a longer pipe, a later sound
            pass
        threading.Thread(target=self.feed, args=(process.stdin,), daemon=True).start()
        return process

    def feed(self, pipe):
        try:
            while True:
                pipe.write(self.stream.chunk())
        except (OSError, ValueError):         # the player quit
            pass


def linux_player(which=shutil.which):
    """A StreamPlayer for the first Linux player installed, or None."""
    command = next((c for c in LINUX_PLAYERS if which(c[0])), None)
    return command and StreamPlayer(command)


class Audio:
    def __init__(self, player=None, folder=None):
        """`player(path)` plays a file and `player(None)` stops; by default the system's own, if any."""
        self.player = player or windows_player() or linux_player()
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
