"""The game's sound: short effects and the Ambience, mixed here and streamed to the system (ADR-0005).

Effects are synthesised at startup; the Ambience is composed by `music`, on a
thread, so the menu never waits for it. Everything is summed in Python into one
endless stream: on Windows through waveOut, on Linux through the first
command-line player installed (PipeWire's, PulseAudio's, then ALSA's). A new
effect cuts the previous effect, never the music. Without a way out, the game is
silent but otherwise the same.
"""

import array
import ctypes
import functools
import operator
import random
import shutil
import subprocess
import sys
import threading

try:
    import fcntl
except ImportError:          # Windows
    fcntl = None

RATE = 22050                 # the mixer's samples: 16-bit mono
FADE = RATE // 2             # a new Ambience fades in over half a second
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


@functools.cache
def effects():
    """Every effect as 16-bit samples, made once per run."""
    return {name: array.array("h", (int(v * (2 ** 15 - 1)) for v in samples(notes))) for name, notes in SOUNDS.items()}


def add(out, part):
    """Sum `part` into the start of `out`; levels are set so that the sum never clips."""
    n = len(part)
    out[:n] = array.array("h", map(operator.add, out[:n], part))


def looped(sound, at, frames):
    """`frames` of a loop from position `at`, wrapping round to its start."""
    reps = (at % len(sound) + frames) // len(sound) + 1
    start = at % len(sound)
    return (sound * reps)[start:start + frames]


class Mixer:
    """What the speakers get next, one chunk of RATE samples at a time: the Ambience, its tension and one effect.

    A new effect cuts the previous effect, never the music. A new Ambience fades in
    over the old one for `fade` samples. Loops not composed yet are silence.
    """

    def __init__(self, effects, loops, fade=0):
        self.effects, self.loops, self.fade = effects, loops, fade
        self.lock = threading.Lock()
        self.muted, self.music_on = False, True
        self.effect, self.effect_at = None, 0
        self.music, self.music_at = None, 0
        self.fading, self.fading_at, self.faded = None, 0, 0     # the old Ambience, where it was, how far gone
        self.ticks, self.ticks_at = None, 0

    def play(self, name):
        with self.lock:
            self.effect, self.effect_at = self.effects[name], 0

    def ambience(self, name):
        with self.lock:
            if name != self.music:
                self.fading, self.fading_at, self.faded = self.music, self.music_at, 0
                self.music, self.music_at = name, 0

    def tension(self, level):
        with self.lock:
            if level != self.ticks:
                self.ticks, self.ticks_at = level, 0

    def chunk(self, frames):
        with self.lock:
            out = array.array("h", bytes(2 * frames))
            if self.muted:
                self.effect = None
                return out
            if self.music_on:
                add(out, self._music(frames))
                if self.loops.get(self.ticks):
                    add(out, looped(self.loops[self.ticks], self.ticks_at, frames))
            self.music_at += frames
            self.ticks_at += frames
            if self.effect is not None:
                part = self.effect[self.effect_at:self.effect_at + frames]
                add(out, part)
                self.effect_at += len(part)
                if self.effect_at >= len(self.effect):
                    self.effect = None
            return out

    def _music(self, frames):
        new = self._loop(self.music, self.music_at, frames)
        if self.faded >= self.fade:
            return new
        old = self._loop(self.fading, self.fading_at, frames)
        n = min(frames, self.fade - self.faded)
        mixed = array.array("h", (int(a + (b - a) * (self.faded + i) / self.fade)
                                  for i, (a, b) in enumerate(zip(old[:n], new[:n]))))
        self.fading_at += frames
        self.faded += n
        return mixed + new[n:]

    def _loop(self, name, at, frames):
        loop = self.loops.get(name)
        return looped(loop, at, frames) if loop else array.array("h", bytes(2 * frames))


# The stream leaves as 16-bit stereo at twice the mixer's rate, each sample repeated: what every system takes.
OUT_RATE, OUT_FRAME = 2 * RATE, 4


def widen(chunk):
    """The mixer's mono samples as the stream's bytes: four 16-bit values (two frames, two channels) each."""
    out = array.array("h", bytes(2 * OUT_FRAME * len(chunk)))
    for k in range(OUT_FRAME):
        out[k::OUT_FRAME] = chunk
    if sys.byteorder == "big":
        out.byteswap()
    return out.tobytes()


# Linux: the stream goes down a pipe into a player, written about 6 ms at a time.
PIPE_SIZE = 4096             # one page: about 23 ms queued behind the player, never seconds
LINUX_PLAYERS = (            # in order of preference, each reading raw samples from its input
    ("pw-cat", "--playback", "--raw", "--format=s16", f"--rate={OUT_RATE}", "--channels=2",
     "--latency=20ms", "--media-role=Game", "-"),
    ("pacat", "--playback", "--raw", "--format=s16le", f"--rate={OUT_RATE}", "--channels=2",
     "--latency-msec=20", "--client-name=ECOS"),
    ("aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(OUT_RATE), "-c", "2", "--buffer-time=20000", "-"),
)


def pipe_output(command):
    """Start `command` and feed it `source(samples)` on a thread, for as long as the game runs.

    The pipe is shrunk to one page, so a sound waits behind milliseconds of audio.
    If the player cannot start or quits (no sound server, say), the game goes on in silence.
    """
    def start(source):
        try:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, bufsize=0)
        except OSError:
            return None
        try:
            fcntl.fcntl(process.stdin, fcntl.F_SETPIPE_SZ, PIPE_SIZE)
        except (AttributeError, OSError):     # not Linux: a longer pipe, a later sound
            pass

        def feed():
            try:
                while True:
                    process.stdin.write(source(128))
            except (OSError, ValueError):     # the player quit
                pass
        threading.Thread(target=feed, daemon=True).start()
        return process
    return start


def linux_command(which=shutil.which):
    """The first Linux player installed, as the command that streams to it, or None."""
    return next((c for c in LINUX_PLAYERS if which(c[0])), None)


def linux_output():
    command = linux_command()
    return command and pipe_output(command)


# Windows: waveOut, a few small buffers refilled as each one finishes.
BUFFERS, BUFFER_SAMPLES = 6, 256          # about 70 ms queued in all
WAVE_MAPPER, CALLBACK_EVENT, WHDR_DONE = 0xFFFFFFFF, 0x50000, 1


class WAVEFORMATEX(ctypes.Structure):
    _fields_ = [("wFormatTag", ctypes.c_ushort), ("nChannels", ctypes.c_ushort), ("nSamplesPerSec", ctypes.c_uint32),
                ("nAvgBytesPerSec", ctypes.c_uint32), ("nBlockAlign", ctypes.c_ushort),
                ("wBitsPerSample", ctypes.c_ushort), ("cbSize", ctypes.c_ushort)]


class WAVEHDR(ctypes.Structure):
    _fields_ = [("lpData", ctypes.c_void_p), ("dwBufferLength", ctypes.c_uint32), ("dwBytesRecorded", ctypes.c_uint32),
                ("dwUser", ctypes.c_size_t), ("dwFlags", ctypes.c_uint32), ("dwLoops", ctypes.c_uint32),
                ("lpNext", ctypes.c_void_p), ("reserved", ctypes.c_size_t)]


def windows_output():
    try:
        winmm, kernel32 = ctypes.WinDLL("winmm"), ctypes.WinDLL("kernel32")
    except (AttributeError, OSError):         # not Windows
        return None
    winmm.waveOutOpen.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint, ctypes.POINTER(WAVEFORMATEX),
                                  ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
    for name in ("waveOutPrepareHeader", "waveOutWrite"):
        getattr(winmm, name).argtypes = [ctypes.c_void_p, ctypes.POINTER(WAVEHDR), ctypes.c_uint]
    kernel32.CreateEventW.restype = ctypes.c_void_p
    kernel32.CreateEventW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p]
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]

    def start(source):
        size = BUFFER_SAMPLES * 2 * OUT_FRAME
        event = kernel32.CreateEventW(None, False, False, None)
        handle = ctypes.c_void_p()
        fmt = WAVEFORMATEX(1, 2, OUT_RATE, OUT_RATE * 4, 4, 16, 0)       # PCM, stereo, 16-bit
        if not event or winmm.waveOutOpen(ctypes.byref(handle), WAVE_MAPPER, ctypes.byref(fmt), event, None,
                                          CALLBACK_EVENT):
            return None                       # no output device: a silent game
        buffers = [ctypes.create_string_buffer(size) for _ in range(BUFFERS)]
        headers = [WAVEHDR(ctypes.cast(b, ctypes.c_void_p), size) for b in buffers]

        def write(header, buffer):
            ctypes.memmove(buffer, source(BUFFER_SAMPLES), size)
            winmm.waveOutWrite(handle, ctypes.byref(header), ctypes.sizeof(WAVEHDR))

        def feed():
            for header, buffer in zip(headers, buffers):
                winmm.waveOutPrepareHeader(handle, ctypes.byref(header), ctypes.sizeof(WAVEHDR))
                write(header, buffer)
            while True:
                kernel32.WaitForSingleObject(event, 100)
                for header, buffer in zip(headers, buffers):
                    if header.dwFlags & WHDR_DONE:
                        write(header, buffer)
        threading.Thread(target=feed, daemon=True).start()
        return handle
    return start


def system_output():
    """How this system takes the stream: a function that starts it from `source(samples)`, or None."""
    return windows_output() or linux_output()


class Audio:
    """What the screens play: effects, the Ambience and its tension, with sound and music switched by the Settings.

    `silent` keeps everything off the speakers (the tests); `listener(name)` hears each effect
    that sounds, and `listener(None)` each time muting cuts it.
    """

    def __init__(self, silent=False, listener=None):
        self.mixer = Mixer(effects(), {}, fade=FADE)
        self.listener = listener
        start = None if silent else system_output()
        if start and start(lambda samples: widen(self.mixer.chunk(samples))):
            threading.Thread(target=self._compose, daemon=True).start()

    def _compose(self):
        import music                          # music builds on this module's synthesis
        for name in ("menu", "shallow", "middle", "deep", "tense", "urgent"):
            self.mixer.loops[name] = music.compose(name)

    @property
    def muted(self):
        return self.mixer.muted

    @muted.setter
    def muted(self, muted):
        if muted and not self.mixer.muted and self.listener:
            self.listener(None)
        self.mixer.muted = muted

    @property
    def music(self):
        return self.mixer.music_on

    @music.setter
    def music(self, on):
        self.mixer.music_on = on

    def play(self, name):
        if not self.mixer.muted:
            self.mixer.play(name)
            if self.listener:
                self.listener(name)

    def ambience(self, name):
        """"menu", or the Sector of the player whose Turn it is."""
        self.mixer.ambience(name)

    def tension(self, level):
        """None, "tense" while a Question is open, "urgent" in its last seconds."""
        self.mixer.tension(level)
