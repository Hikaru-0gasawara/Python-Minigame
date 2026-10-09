"""The game's 32 colours, per-Sector ramps and ordered dithering."""

# Concrete ramp, rust, amber, toxic green, alarm red, ECO cyan, and a light violet for player 3.
PALETTE = (
    "07090d", "0d1219", "141c25", "1c2833", "263744", "33495a", "46606f", "5d7a85",
    "7f9aa0", "a9bfc0", "d8e4e0", "2b1712", "4a2418", "73361f", "a2522a", "cc7a3a",
    "e3a857", "f4d38a", "12261c", "1f4a2e", "3f8a45", "8fd16a", "3a0c12", "6e1420",
    "b3202c", "ff4a4a", "0b3b45", "0f6b78", "19b3c2", "6ff3f0", "e0fffd", "b08cff",
)
RGB = tuple(tuple(int(c[i:i+2], 16) for i in (0, 2, 4)) for c in PALETTE)
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

CONCRETE = (1, 2, 3, 4, 5, 6, 7, 8, 9)
RUST = (11, 12, 13, 14)
METAL = (3, 4, 5, 6, 7, 8)
GREEN = (18, 19, 20, 21)
RED, CYAN, AMBER = 24, 28, 16

# Each ramp keeps one hue family, so dithering never flickers between hues.
SECTORS = {
    "shallow": dict(wall=CONCRETE, floor=(0, 1, 2, 3, 4, 5, 6), ceil=(0, 1, 2, 3, 4),
                    tube=(29, 30), rust=.08, fog=.35, accent=CYAN),
    "middle": dict(wall=(0, 11, 12, 13, 14, 15), floor=(0, 1, 11, 12, 13), ceil=(0, 1, 11, 12),
                   tube=(16, 17), rust=.3, fog=.45, accent=AMBER),
    "deep": dict(wall=(0, 1, 2, 3, 23, 24), floor=(0, 1, 22, 23), ceil=(0, 1, 22, 23),
                 tube=(24, 25), rust=.15, fog=.6, accent=RED),
}


def dither(ramp, value, x, y):
    """Map 0..1 to a ramp colour, blending neighbours with a 4x4 Bayer pattern."""
    v = max(0., min(.999, value)) * (len(ramp) - 1)
    i = int(v)
    return ramp[min(len(ramp) - 1, i + (BAYER[y & 3][x & 3] / 16 < v - i))]


def hex_color(index):
    return "#" + PALETTE[index]
