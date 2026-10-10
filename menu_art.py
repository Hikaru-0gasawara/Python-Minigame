"""The menu's pixel scene, independent of Tk: server towers in parallax, ECO's pulsing core and hanging cables.

Tower layers are 320 wide and wrap around, so scrolling them sideways never
shows a seam. Scanlines are baked in at build time: layers only ever move
sideways, so every odd row stays odd.
"""

import math

from palette import AMBER, dither
from pixels import Pix, h32
from props import cables
from room_art import H, W

HORIZON, FLOOR = 150, 176           # where far and near towers stand
CORE_AT, CORE_SIZE = (218, 26), 64  # top-left of ECO's core sprite: the right column, above the Records
CORE_FRAMES = 6
CABLES_AT = ((116, 0), (164, 0), (286, 0))          # between the title and the core, and past it
# One step darker along each colour's ramp; a ramp's darkest step falls to black.
DARKER = [0 if i in (0, 11, 18, 22, 26) else 30 if i == 31 else i - 1 for i in range(32)]
SEAM_ROWS = {round(3 * 1.7 ** k) for k in range(6)}
LEDS = ((26, 15, 23, 19), (28, 16, 24, 20))        # far (dim) and near: cyan, amber, red, green


def scanlines(p):
    for i, c in enumerate(p.px):
        if c is not None and (i // p.w) % 2:
            p.px[i] = DARKER[c]
    return p


def backdrop():
    """The opaque back layer: a dark hall fading to the horizon, and a floor running towards the core."""
    p = Pix(W, H)
    for y in range(H):
        for x in range(W):
            if y < HORIZON:
                p.set(x, y, dither((0, 1, 2), .15 + y / HORIZON * .55, x, y))
            else:
                depth = (y - HORIZON) / (H - HORIZON)
                # Floor seams: lines converging on the core, and rows spreading out towards the viewer.
                seam = abs(((x - CORE_AT[0] - CORE_SIZE / 2) / (depth + .15)) % 40 - 20) < 1.2 or y - HORIZON in SEAM_ROWS
                p.set(x, y, 27 if seam and depth > .1 else dither((0, 1, 2, 3), .2 + depth * .6, x, y))
    return scanlines(p)


def towers(layer):
    """Server racks across a wrapping strip; the far layer is lower, darker and denser."""
    far = layer == "far"
    ramp, base, leds = ((0, 1, 2), HORIZON, LEDS[0]) if far else ((0, 1, 2, 3, 4), FLOOR, LEDS[1])
    p = Pix(W, H)
    x, i = 0, 0
    while x < W:
        w = (14 if far else 24) + int(h32(layer, i, "w") * (10 if far else 18))
        top = base - (40 if far else 70) - int(h32(layer, i, "h") * (50 if far else 60))
        for col in range(w):
            for y in range(top, base):
                c = dither(ramp, .55 - col / w * .45 + (y == top) * .4, x + col, y)
                if col in (0, w - 1) or (y - top) % 9 == 0:
                    c = ramp[0]                      # rack seams
                elif 2 < col < w - 3 and (y - top) % 3 == 1 and col % 3 == 1 and h32(layer, i, col, y) < .22:
                    c = leds[int(h32("led", layer, i, col, y) * len(leds))]
                p.set((x + col) % W, y, c)          # the last rack wraps onto the first
        x += w + 2 + int(h32(layer, i, "gap") * (5 if far else 26))
        i += 1
    return scanlines(p)


def core(step):
    """ECO's core: a ringed eye whose glow swells over CORE_FRAMES steps."""
    pulse = step / (CORE_FRAMES - 1)
    p = Pix(CORE_SIZE, CORE_SIZE)
    c = (CORE_SIZE - 1) / 2
    glow = 17 + 4 * pulse
    for y in range(CORE_SIZE):
        for x in range(CORE_SIZE):
            d = math.hypot(x - c, y - c)
            if 27 <= d < 31:                       # the housing ring and its four struts
                p.set(x, y, dither((1, 2, 3, 4, 5), .7 - (y - c) / 60, x, y))
            elif d < 27 and min(abs(x - c), abs(y - c)) < 1 and d > glow:
                p.set(x, y, 3)
            elif d < glow:
                if abs(x - c) < 2 and d < 11:
                    p.set(x, y, 0)                 # the slit of ECO's eye
                else:
                    p.set(x, y, dither((26, 27, 28, 29, 30), (1 - d / glow) * (.55 + .45 * pulse) + .15, x, y))
    return scanlines(p)


def hanging_cables():
    """Cables down from the ceiling in front of everything, and where their copper ends spark."""
    p = Pix(W, H)
    for variant, (x, y) in enumerate(CABLES_AT):
        p.blit(cables(variant), x, y)
    sparks = [(i % W, i // W) for i, c in enumerate(p.px) if c == AMBER]
    return scanlines(p), sparks
