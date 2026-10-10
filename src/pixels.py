"""A tiny indexed-colour canvas for drawing pixel art, independent of Tk."""

import struct
import zlib

from palette import RGB, dither


def h32(*values):
    """A stable 0..1 hash: the same values give the same number in every run."""
    return zlib.crc32(repr(values).encode()) / 0xFFFFFFFF


def png(w, h, pixels):
    """Encode palette indices (None = transparent) as an RGBA PNG for Tk."""
    rows = bytearray()
    clear = bytes(4)
    colours = [bytes((*rgb, 255)) for rgb in RGB]
    for y in range(h):
        rows.append(0)
        for c in pixels[y * w:(y + 1) * w]:
            rows += clear if c is None else colours[c]

    def chunk(kind, data):
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!2I5B", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(rows), 3)) + chunk(b"IEND", b""))


def poly_inside(points):
    """Even-odd test against a polygon, sampled at pixel centres."""
    edges = list(zip(points, points[1:] + points[:1]))

    def inside(x, y):
        x, y, hit = x + .5, y + .5, False
        for (x0, y0), (x1, y1) in edges:
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                hit = not hit
        return hit
    return inside


class Pix:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.px = [fill] * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c

    def get(self, x, y):
        return self.px[y * self.w + x] if 0 <= x < self.w and 0 <= y < self.h else None

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.px[y * self.w + x] = c

    def shade(self, inside, ramp, light):
        """Fill where `inside(x, y)`, dithering `light(x, y)` (0..1) along `ramp`."""
        for y in range(self.h):
            for x in range(self.w):
                if inside(x, y):
                    self.px[y * self.w + x] = dither(ramp, light(x, y), x, y)

    def line(self, x0, y0, x1, y1, c):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            self.set(round(x0 + (x1 - x0) * i / steps), round(y0 + (y1 - y0) * i / steps), c)

    def outline(self, c):
        """Ring every opaque shape with a 1-pixel outer outline."""
        grown = self.px[:]
        for y in range(self.h):
            for x in range(self.w):
                if self.get(x, y) is None and any(self.get(x + dx, y + dy) is not None
                                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    grown[y * self.w + x] = c
        self.px = grown

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y * other.w + x]
                if c is not None:
                    self.set(ox + x, oy + y, c)

    def bbox(self):
        """The smallest (x0, y0, x1, y1) holding every opaque pixel, or None."""
        xs = [i % self.w for i, c in enumerate(self.px) if c is not None]
        if not xs:
            return None
        ys = [i // self.w for i, c in enumerate(self.px) if c is not None]
        return min(xs), min(ys), max(xs), max(ys)

    def png(self):
        return png(self.w, self.h, self.px)
