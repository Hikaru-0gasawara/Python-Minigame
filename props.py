"""Pixel art for what fills a room: kind props, decorations and their states. Independent of Tk.

Every sprite gets the same wear as the walls: chips, cracks and rust specks
chosen by a stable hash, so a prop always looks the same.
"""

import math

import font
from palette import CYAN, GREEN, METAL, RED, RUST, dither
from pixels import Pix, h32, poly_inside
from room_art import H, W, _project

CONCRETE = (1, 2, 3, 4, 5, 6, 7)
# Where each prop's sprite goes in the 320x200 frame (top-left corner).
PROP_AT = {"container": (138, 134), "mimic": (138, 134), "trap": (0, 0), "pod": (137, 70),
           "debris": (88, 126), "elevator": (118, 0), "gate": (127, 55), "elite": (130, 57)}
# Back-wall spots for screens and graffiti, clear of the back door (x 136-183).
SLOTS = {"left": (98, 64), "right": (186, 64)}
# Short enough for a back-wall slot.
GRAFFITI = ("FUJA", "MENTE", "NÃO!", "OUVE", "SAÍDA?", "|||| ||")


def wear(p, key, chips=.05, rust=.03):
    """Chip and rust an opaque sprite with a stable pattern."""
    for i, c in enumerate(p.px):
        if c is None:
            continue
        x, y = i % p.w, i // p.w
        roll = h32(key, x, y)
        if roll < chips:
            p.px[i] = 1
        elif roll < chips + rust:
            p.px[i] = RUST[1 + int(roll * 1000) % 2]


def _eye(p, cx, cy, state, half=3):
    """An almond eye: dark when dormant, cyan when listening, green once passed."""
    if state == "dormant":
        p.line(cx - half, cy, cx + half - 1, cy, 27)
        return
    rim, core = (CYAN, 30) if state == "listening" else (20, 21)
    p.line(cx - half - 1, cy, cx + half, cy, rim)
    p.line(cx - half, cy - 1, cx + half - 1, cy - 1, 29 if state == "listening" else 21)
    p.line(cx - half, cy + 1, cx + half - 1, cy + 1, 29 if state == "listening" else 21)
    p.line(cx - 1, cy, cx, cy, core)


def elite(state):
    """The Elite Guardian: taller, armoured, crested, with ECO's emblem on its chest."""
    p = Pix(60, 100)

    def lit(cx, w):
        return lambda x, y: .72 - (x - cx) / w * .5 - y / 320 + (h32("elite", x // 3, y // 3) - .5) * .12
    p.shade(lambda x, y: 5 <= x <= 54 and 84 <= y <= 99, CONCRETE, lambda x, y: .5 - (x - 5) / 120 + (y < 87) * .25)
    p.shade(poly_inside([(17, 30), (43, 30), (53, 85), (7, 85)]), CONCRETE, lit(30, 50))
    for x0, x1 in ((22, 16), (30, 30), (38, 44)):
        p.line(x0, 60, x1, 84, 1)
    p.shade(poly_inside([(18, 33), (42, 33), (40, 57), (30, 64), (20, 57)]), METAL, lambda x, y: .72 - y / 160 - (x - 30) / 90)
    p.line(18, 33, 30, 64, 2)
    p.line(42, 33, 30, 64, 2)
    _eye(p, 30, 46, state, 4)
    p.shade(poly_inside([(4, 28), (21, 23), (24, 37), (7, 42)]), METAL + (9,), lambda x, y: .78 - y / 110)
    p.shade(poly_inside([(36, 23), (56, 28), (53, 42), (36, 37)]), (2,) + METAL[:-1], lambda x, y: .5 - y / 140)
    for x, y in ((8, 31), (15, 28), (42, 28), (50, 32)):
        p.set(x, y, 9)
    p.shade(lambda x, y: ((x - 29.5) / 13) ** 2 + ((y - 17) / 15) ** 2 <= 1, CONCRETE, lit(29.5, 34))
    for x0 in (21, 29, 37):                       # the crest
        p.line(x0, 5, x0 + (x0 - 29) // 4, 0, 6)
    p.shade(lambda x, y: ((x - 29.5) / 9) ** 2 + ((y - 19) / 10) ** 2 <= 1, (0, 1), lambda x, y: .2)
    p.rect(23, 13, 36, 24, 2)
    for y in range(13, 25, 2):
        p.line(23, y, 36, y, 3)
    p.line(33, 13, 30, 24, 1)
    _eye(p, 29, 18, state, 3)
    for x0, y0, x1, y1 in ((15, 20, 8, 84), (44, 20, 51, 84)):
        p.line(x0, y0, x1, y1, 1)
        p.line(x0 + 1, y0, x1 + 1, y1, 4)
    wear(p, ("elite", state), .04, .03)
    p.outline(0)
    return p


def container(state):
    """An armoured data container; open, it spills cyan light and data shards."""
    p = Pix(44, 36)
    p.shade(lambda x, y: 4 <= x <= 39 and 16 <= y <= 35, METAL, lambda x, y: .62 - (x - 4) / 90 - (y - 16) / 80)
    p.rect(8, 19, 35, 26, 3)
    p.shade(lambda x, y: 9 <= x <= 34 and 20 <= y <= 25, METAL, lambda x, y: .4 - (x - 9) / 120)
    for x in range(4, 40):
        p.set(x, 29, 16 if (x // 3) % 2 else 0)
        p.set(x, 30, 16 if ((x + 1) // 3) % 2 else 0)
    for x, y in ((6, 18), (37, 18), (6, 33), (37, 33)):
        p.set(x, y, 9)
    if state == "closed":
        p.shade(poly_inside([(4, 16), (39, 16), (36, 11), (7, 11)]), METAL, lambda x, y: .75 - (x - 4) / 100)
        p.rect(20, 21, 23, 23, 16)                  # amber lock light
    else:
        p.shade(lambda x, y: 6 <= x <= 37 and 13 <= y <= 16, (26, 27, CYAN, 29, 30), lambda x, y: .9 - abs(x - 21.5) / 30)
        p.shade(poly_inside([(6, 13), (37, 13), (40, 1), (9, 3)]), METAL, lambda x, y: .55 - (x - 6) / 80 + (y < 5) * .15)
        for x, y in ((14, 8), (21, 6), (28, 9), (18, 10), (31, 4)):
            p.set(x, y, 29)
        p.rect(20, 21, 23, 23, 21)                  # unlocked: green
    wear(p, ("container", state), .04, .04)
    p.outline(0)
    return p


def mimic():
    """The Mimic revealed: the container's lid is a jaw of steel teeth."""
    p = container("open")
    p.shade(lambda x, y: 7 <= x <= 36 and 12 <= y <= 17, (22, 23), lambda x, y: .4)
    p.shade(lambda x, y: ((x - 21.5) / 8) ** 2 + ((y - 15) / 3) ** 2 <= 1, (23, 24, 25), lambda x, y: .6)
    for x in range(8, 35, 4):                       # teeth: up from the lip, down from the lid
        p.rect(x, 16, x + 2, 16, 10)
        p.set(x + 1, 15, 10)
        p.rect(x + 1, 11, x + 3, 11, 9)
        p.set(x + 2, 12, 9)
    for x in (14, 28):
        p.rect(x, 7, x + 1, 8, 25)                  # red eyes on the lid
    p.outline(0)
    return p


def trap(state):
    """Pressure plates in the floor and emitters on both walls, armed or spent."""
    p = Pix(W, H)
    for y in range(60, H):
        for x in range(W):
            surf, sc, u, v = _project(x, y)
            if surf == "floor" and -66 < u < 66 and 30 < v < 140:
                pu, pv = (u + 66) % 44, (v - 30) % 55
                if pu < 3 or pv < 3:
                    p.set(x, y, 0)
                    continue
                if state == "armed":
                    c = dither(METAL[:4], .55 - v / 400, x, y)
                    if abs(pu - 22) < 4 and abs(pv - 27) < 5:
                        c = RED if (x + y) % 3 else 25          # warning lights
                else:
                    c = dither((0, 1, 2, 3), .45 - v / 400 + (h32("scorch", x // 4, y // 3) - .5) * .5, x, y)
                p.set(x, y, c)
            elif surf in ("left", "right") and 30 < u < 58 and -20 < v < 18:
                du, dv = u - 30, v + 20
                c = dither(METAL, .5 - dv / 90, x, y)
                if 8 < du < 20 and 12 < dv < 26:            # the lens
                    c = (25 if du < 14 else RED) if state == "armed" else (1 if (x + y) % 2 else 2)
                p.set(x, y, c)
    if state == "spent":
        for x0, y0 in ((126, 160), (176, 168), (150, 150)):  # cracks across spent plates
            for i in range(10):
                p.set(x0 + i, y0 + (i * 7) % 3, 0)
    return p


def pod(state):
    """A repair pod: green fluid behind cracked glass, brighter while healing."""
    p = Pix(46, 86)
    p.shade(lambda x, y: ((x - 22.5) / 22) ** 2 + ((y - 14) / 14) ** 2 <= 1 or (1 <= x <= 44 and 14 <= y <= 74),
            METAL, lambda x, y: .6 - (x - 1) / 100 - y / 400)
    p.shade(lambda x, y: 6 <= x <= 39 and 12 <= y <= 66, (6, 7), lambda x, y: .3)   # the glass frame
    bright = .85 if state == "healing" else .45
    p.shade(lambda x, y: 8 <= x <= 37 and 14 <= y <= 64, GREEN, lambda x, y: bright - abs(x - 22.5) / 40 - (64 - y) / 300)
    for x in (13, 21, 30):
        for y in range(20 + x % 5, 62, 7):
            p.set(x, y, 21 if state == "healing" else 20)
    p.line(29, 18, 25, 40, 9)                       # a crack in the glass
    p.line(25, 40, 27, 52, 9)
    p.shade(lambda x, y: 4 <= x <= 41 and 74 <= y <= 85, CONCRETE, lambda x, y: .5 - (x - 4) / 80 + (y < 77) * .2)
    plus = 21 if state == "healing" else 19
    p.rect(21, 2, 23, 8, plus)
    p.rect(19, 4, 25, 6, plus)
    wear(p, ("pod", state), .03, .03)
    p.outline(0)
    return p


def debris(variant):
    """A fallen server rack, loose cables and scattered parts."""
    p = Pix(144, 52)
    p.shade(poly_inside([(14, 34), (92, 8), (104, 20), (26, 47)]), (1, 2, 3, 4, 5), lambda x, y: .6 - y / 90 - x / 400)
    p.shade(poly_inside([(26, 47), (104, 20), (106, 26), (28, 51)]), (0, 1, 2), lambda x, y: .5)
    for i in range(10):                             # dead and dying LEDs
        x, y = 30 + i * 7, 38 - i * 2.4
        p.set(int(x), int(y), (CYAN, RED, 16, 1, 1)[int(h32("led", variant, i) * 5)])
    for x0, y0, x1, y1 in ((96, 12, 132, 44), (60, 20, 70, 50), (100, 22, 120, 50)):
        sag = 6
        for i in range(21):
            t = i / 20
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)
            p.set(int(x), int(y), 0)
            p.set(int(x), int(y) - 1, 4)
    for x, y, w in ((112, 40, 10), (4, 44, 8), (124, 30, 6)):
        p.shade(lambda px, py, x=x, y=y, w=w: x <= px <= x + w and y <= py <= y + w * .6, METAL, lambda px, py: .5 - py / 120)
    wear(p, ("debris", variant), .05, .04)
    p.outline(0)
    if variant:
        p.px = [p.px[y * p.w + (p.w - 1 - x)] for y in range(p.h) for x in range(p.w)]
    return p


def elevator():
    """The platform the racers came down on, hanging from cables into the dark."""
    p = Pix(84, 172)
    for x in (12, 70):
        p.line(x, 0, x, 150, 1)
        p.line(x + 1, 0, x + 1, 150, 4)
    p.shade(poly_inside([(4, 150), (80, 150), (84, 168), (0, 168)]), METAL, lambda x, y: .6 - abs(x - 42) / 120)
    for x in range(0, 84):
        p.set(x, 167, 16 if (x // 4) % 2 else 0)
        p.set(x, 168, 16 if ((x + 1) // 4) % 2 else 0)
    for x in (8, 74):
        p.rect(x, 128, x + 2, 150, 3)
        p.rect(x, 126, x + 2, 127, 16)              # amber post lamps
    wear(p, "elevator", .04, .05)
    p.outline(0)
    return p


def gate(hits):
    """The core gate: a vault door with three locks that light as the Exit is answered."""
    p = Pix(66, 82)
    p.shade(lambda x, y: 0 <= x <= 65 and 0 <= y <= 81, CONCRETE[:5], lambda x, y: .45 - y / 250)
    p.shade(lambda x, y: ((x - 32.5) / 30) ** 2 + ((y - 40) / 30) ** 2 <= 1, METAL, lambda x, y: .7 - (x - 2) / 120 - (y - 10) / 150)
    p.shade(lambda x, y: ((x - 32.5) / 19) ** 2 + ((y - 40) / 19) ** 2 <= 1, (2, 3, 4, 5), lambda x, y: .5 - (y - 21) / 90)
    for a in range(0, 360, 30):                     # bolts around the rim
        x, y = 32.5 + 25 * math.cos(math.radians(a)), 40 + 25 * math.sin(math.radians(a))
        p.set(int(x), int(y), 9)
    _eye(p, 33, 40, "listening" if hits < 3 else "cleared", 6)
    for i, (x, y) in enumerate(((5, 38), (30, 4), (56, 38))):
        lit = i < hits
        p.rect(x, y, x + 4, y + 4, 0)
        p.rect(x + 1, y + 1, x + 3, y + 3, (21 if lit else RED))
    wear(p, ("gate", hits), .03, .04)
    return p


def eco_screen(mode):
    """ECO's propaganda screen: its eye on a scanline field, or static."""
    p = Pix(28, 20)
    p.rect(0, 0, 27, 19, 1)
    p.rect(1, 1, 26, 18, 2)
    for y in range(3, 17):
        for x in range(3, 25):
            if mode == "static":
                p.set(x, y, (26, 27, 1, 3, 29)[int(h32("static", x, y) * 5)])
            else:
                p.set(x, y, 26 if y % 2 else 27)
    if mode == "eye":
        for x in range(6, 22):
            t = (x - 13.5) / 7.5
            half = int(4 * math.sqrt(max(0, 1 - t * t)))
            for y in range(10 - half, 10 + half + 1):
                p.set(x, y, 29 if abs(y - 10) < half else CYAN)
        p.rect(12, 8, 15, 11, 0)
        p.set(13, 8, 30)
    p.line(1, 19, 26, 19, 0)
    wear(p, ("screen", mode), .02, .02)
    return p


def graffiti(variant):
    """A message scrawled by someone who did not escape."""
    word = GRAFFITI[variant % len(GRAFFITI)]
    ink = (16, 25, 9, 21)[variant % 4]
    p = Pix(font.measure(word) + 4, font.HEIGHT + 6)
    x = 2
    for i, ch in enumerate(word):
        lift = int(h32("scrawl", variant, i) * 3) - 1
        width, pixels = font.glyph(ch)
        for gx, gy in pixels:
            p.set(x + gx, gy + 1 + lift, ink)
        if h32("drip", variant, i) < .35:           # paint running down
            for d in range(int(h32("len", variant, i) * 5) + 2):
                p.set(x + width // 2, font.HEIGHT + lift + d, ink)
        x += width + 1
    return p


def cables(variant):
    """Cables hanging from a broken ceiling panel."""
    p = Pix(48, 70)
    for i in range(3):
        end = 34 + int(h32("cable", variant, i) * 30)
        x0 = 6 + i * 14
        for y in range(end):
            sway = int(3 * math.sin(y / 9 + i + variant))
            p.set(x0 + sway, y, 1)
            p.set(x0 + sway + 1, y, 4 if i % 2 else 3)
        p.rect(x0 - 1, end, x0 + 2, end + 2, 16 if i == 1 else 8)   # frayed copper ends
    return p


def vent():
    """A floor vent that breathes steam."""
    p = Pix(34, 10)
    p.shade(poly_inside([(4, 0), (30, 0), (34, 9), (0, 9)]), METAL[:4], lambda x, y: .5 - y / 30)
    for x in range(4, 31, 3):
        p.line(x, 1, x - 1, 8, 0)
    p.outline(0)
    return p


def prop_sprite(name, state):
    """The sprite for a scene prop; a closed Mimic is exactly a closed Treasure container."""
    if name == "container" or (name == "mimic" and state == "closed"):
        return container(state)
    return {"mimic": lambda: mimic(), "trap": lambda: trap(state), "pod": lambda: pod(state),
            "debris": lambda: debris(state), "elevator": elevator, "gate": lambda: gate(state)}[name]()


def decor_sprite(name, variant):
    return {"screen": lambda: eco_screen(variant), "graffiti": lambda: graffiti(variant),
            "cables": lambda: cables(variant), "vent": vent}[name]()
