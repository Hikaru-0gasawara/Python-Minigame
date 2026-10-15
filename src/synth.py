"""What the effects and the Ambience are made of: the sample rate, wave shapes, noise and the sum of
two sounds. Independent of Tk."""

import array
import operator
import random

RATE = 22050                 # 16-bit mono samples, for effects, Ambience and the mixer alike
FULL = 2 ** 15 - 1
_rng = random.Random(7)
NOISE = [_rng.uniform(-1, 1) for _ in range(4096)]


def wave(shape, phase):
    """A square, triangle or noise wave at `phase` cycles; noise is pitched by how fast it steps through a table."""
    if shape == "square":
        return 1 if phase % 1 < .5 else -1
    if shape == "triangle":
        return 4 * abs(phase % 1 - .5) - 1
    return NOISE[int(phase) % len(NOISE)]


def add(out, part):
    """Sum `part` into the start of `out`; levels are set so that the sum never clips (ADR-0005)."""
    n = len(part)
    out[:n] = array.array("h", map(operator.add, out[:n], part))
