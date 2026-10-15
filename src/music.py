"""The Ambience: chiptune loops for the menu and each Sector, and the ticks of tension. Independent of Tk.

A piece is a few bars of voices written on a grid of sixteenth notes and rendered
once, at startup, into 16-bit samples. A note that rings past the end of the loop
carries on at its start, so the loop is exactly one turn of the music playing
forever and repeats without a seam. Levels stay under the effects', so that the
mixer's sum of Ambience, tension and an effect never clips (ADR-0005).
"""

from array import array
from dataclasses import dataclass
import functools

from audio import NOISE, RATE, add

STEPS = 4                    # grid steps per beat: sixteenth notes
FULL = 2 ** 15 - 1
NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


@dataclass(frozen=True)
class Voice:
    """One line of a piece. `pattern` is a note per step ("A3", "F#4", "Bb2"), "." to rest or "-" to hold
    the note before; it repeats to fill the piece. `delay` shifts the line by steps, for echoes."""
    shape: str               # square, triangle or noise
    envelope: str            # pluck: fades from the start; pad: swells and fades; hit: a short knock
    volume: float
    pattern: str
    delay: int = 0


@dataclass(frozen=True)
class Piece:
    bpm: int
    bars: int
    voices: tuple


def bar(*notes):
    """A bar of four beats from (note, steps) pairs: each note is held for its steps."""
    tokens = []
    for note, steps in notes:
        tokens += [note] + ["-" if note != "." else "."] * (steps - 1)
    assert len(tokens) == 4 * STEPS, notes
    return " ".join(tokens)


def arpeggio(*chords):
    """Eighth notes up and down each chord, a bar per chord: root, third, fifth, octave, back down."""
    return " ".join(bar(*((n, 2) for n in (a, b, c, d, c, b, a, c))) for a, b, c, d in chords)


MENU_ARPEGGIO = arpeggio(("A3", "C4", "E4", "A4"), ("F3", "A3", "C4", "F4"),
                         ("G3", "B3", "D4", "G4"), ("E3", "G3", "B3", "E4"))
SHALLOW_BELLS = " ".join((bar(("E5", 8), ("B4", 8)), bar(("G5", 8), ("D5", 8)),
                          bar(("F#5", 8), ("B4", 8)), bar(("E5", 8), (".", 8))))
MIDDLE_BASS = " ".join((bar(*((n, 2) for n in ("D2", "D2", "F2", "D2", "D2", "C2", "D2", "A1"))),) * 2
                       + (bar(*((n, 2) for n in ("Bb1", "Bb1", "D2", "Bb1", "Bb1", "F2", "Bb1", "D2"))),
                          bar(*((n, 2) for n in ("C2", "C2", "E2", "C2", "C2", "G2", "C2", "E2")))))

PIECES = {
    # The computer breathing: a slow arpeggio in A minor over a soft square pad, with an echo.
    "menu": Piece(72, 4, (
        Voice("triangle", "pluck", .10, MENU_ARPEGGIO),
        Voice("triangle", "pluck", .04, MENU_ARPEGGIO, delay=3),
        Voice("square", "pad", .05, " ".join(bar((n, 16)) for n in ("A2", "F2", "G2", "E2"))),
    )),
    # Shallow: cold and sparse, long bell notes ringing in a metal hall over a low E.
    "shallow": Piece(60, 4, (
        Voice("triangle", "pluck", .11, SHALLOW_BELLS),
        Voice("triangle", "pluck", .05, SHALLOW_BELLS, delay=3),
        Voice("triangle", "pluck", .025, SHALLOW_BELLS, delay=6),
        Voice("triangle", "pad", .07, " ".join(bar(("E2", 16)) for _ in range(4))),
    )),
    # Middle: rust and amber, a bass line that never stops, hiss on the off-beats, a lead now and then.
    "middle": Piece(92, 4, (
        Voice("square", "pluck", .10, MIDDLE_BASS),
        Voice("noise", "hit", .04, bar((".", 2), ("C9", 2), (".", 2), ("C9", 2), (".", 2), ("C9", 2), (".", 2), ("C9", 2))),
        Voice("square", "pluck", .06, " ".join((bar((".", 16)), bar(("A4", 4), ("F4", 4), ("E4", 8)),
                                                bar((".", 16)), bar(("D5", 4), ("C5", 4), ("A4", 8))))),
    )),
    # Deep: alarm red, a low drone that slips a semitone and a two-tone siren, knocks on the beat.
    "deep": Piece(100, 4, (
        Voice("square", "pad", .07, " ".join((bar(("C2", 16)),) * 2 + (bar(("Db2", 16)),) * 2)),
        Voice("square", "pad", .05, bar(("C5", 8), ("F#5", 8))),
        Voice("noise", "hit", .08, bar(("C3", 4), ("C3", 4), ("C3", 4), ("C3", 4))),
    )),
    # Tension, over any Ambience: a clock ticking every beat, and twice as fast when time runs short.
    "tense": Piece(120, 1, (Voice("triangle", "hit", .07, bar(*(("C7", 4),) * 4)),)),
    "urgent": Piece(120, 1, (Voice("triangle", "hit", .07, bar(*(("C7", 2),) * 8)),)),
}


def frequency(note):
    """Hz of a note name such as A4 (440), F#5 or Bb1."""
    pitch = NAMES[note[0]] + note[1:].count("#") - note[1:].count("b")
    return 440 * 2 ** ((pitch + 12 * (int(note.lstrip("ABCDEFG#b")) + 1) - 69) / 12)


def notes(voice, steps):
    """(start step, length in steps, note) for each note of a voice across `steps` steps."""
    tokens = voice.pattern.split()
    line = [tokens[i % len(tokens)] for i in range(steps)]
    found = []
    for i, token in enumerate(line):
        if token == "-" and found:
            start, length, note = found[-1]
            found[-1] = (start, length + 1, note)
        elif token not in ".-":
            found.append((i + voice.delay, 1, token))
    return found


@functools.lru_cache(maxsize=None)
def tone(note, frames, shape, envelope, volume):
    """One note, rendered once however often it is played."""
    out, phase, step = array("h", bytes(2 * frames)), 0., frequency(note) / RATE
    for i in range(frames):
        t = i / frames
        phase += step
        if shape == "square":
            v = 1 if phase % 1 < .5 else -1
        elif shape == "triangle":
            v = 4 * abs(phase % 1 - .5) - 1
        else:
            v = NOISE[int(phase) % len(NOISE)]
        if envelope == "pluck":
            level = (1 - t) ** 2
        elif envelope == "pad":
            level = min(1, t / .15, (1 - t) / .3)
        else:
            level = (1 - t) ** 6
        out[i] = int(v * level * volume * FULL)
    return out


def render(piece, repeats=1):
    """The piece's samples, played `repeats` times; whatever rings past the end carries on at the start."""
    step = RATE * 60 / piece.bpm / STEPS
    loop = round(piece.bars * 4 * STEPS * step)
    out = array("h", bytes(2 * loop * repeats))
    for repeat in range(repeats):
        for voice in piece.voices:
            for start, length, note in notes(voice, piece.bars * 4 * STEPS):
                sound = tone(note, round(length * step), voice.shape, voice.envelope, voice.volume)
                at = (repeat * loop + round(start * step)) % len(out)
                head = min(len(sound), len(out) - at)
                part = out[at:at + head]
                add(part, sound[:head])
                out[at:at + head] = part
                if head < len(sound):
                    tail = out[:len(sound) - head]
                    add(tail, sound[head:])
                    out[:len(sound) - head] = tail
    return out


@functools.lru_cache(maxsize=None)
def compose(name):
    return render(PIECES[name])
