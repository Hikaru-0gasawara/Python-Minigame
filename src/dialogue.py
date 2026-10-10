"""A Guardian's lines revealed letter by letter, independent of Tk."""

import math

CHARS_PER_SECOND = 40


class Dialogue:
    """Paces already-wrapped lines; every line keeps its place while it fills in."""

    def __init__(self, lines, start):
        self.lines, self.start = list(lines), start
        self.total = sum(len(line) for line in self.lines)

    def count(self, now):
        letters = (now - self.start) * CHARS_PER_SECOND     # infinite once completed
        return self.total if letters >= self.total else max(0, int(letters))

    def done(self, now):
        return self.count(now) >= self.total

    def complete(self):
        self.start = -math.inf

    def shown(self, now):
        """Each line cut to the letters revealed so far."""
        left, out = self.count(now), []
        for line in self.lines:
            out.append(line[:max(0, left)])
            left -= len(line)
        return out

    def voiced(self, before, now):
        """How many letters (not spaces) appeared since `before` letters were shown, for voice blips."""
        text = "".join(self.lines)
        return sum(not ch.isspace() for ch in text[before:self.count(now)])
