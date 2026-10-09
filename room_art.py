"""Pixel art for rooms, drawn by code at 320x200 (ADR-0004). Independent of Tk.

A room is a one-point perspective box: side walls, floor and ceiling run from
the screen edges to the back wall. Every mark comes from the Seed and the Room,
so the same Dungeon always looks the same.
"""

from functools import lru_cache
import math
import random

from palette import BAYER, CYAN, METAL, RED, RUST, SECTORS, dither
from pixels import Pix, h32, poly_inside

W, H = 320, 200
CX, CY = 160, 95                  # vanishing point
NEAR_X, NEAR_Y = 160, 105         # half-extents of the room at the screen edge
BACK = .4                         # scale of the back wall
BX0, BX1 = int(CX - NEAR_X * BACK), int(CX + NEAR_X * BACK)
BY0, BY1 = int(CY - NEAR_Y * BACK), int(CY + NEAR_Y * BACK)
# Native-pixel regions the player can click, in portal order: left, back, right, behind.
BACK_DOOR = (136, BY1 - 72, 183, BY1 - 1)
BEHIND_DOOR = (128, 186, 191, 199)
GUARDIAN_AT = (136, 71)           # the statue stands in front of the back door
GUARDIAN_ASIDE = 58               # how far a Cleared Guardian steps to the side
SIDE_DOOR_U, SIDE_DOOR_V = (70, 150), (-55, 105)
LIGHTS = ("on", "dimmed", "off")


def _project(x, y):
    """Classify a screen pixel: surface, depth scale and world coordinates."""
    dx, dy = x - CX + .5, y - CY + .5
    sx, sy = abs(dx) / NEAR_X, abs(dy) / NEAR_Y
    if max(sx, sy) <= BACK:
        return "back", BACK, dx / BACK, dy / BACK
    if sx >= sy:
        return ("left" if dx < 0 else "right"), sx, (1 / sx - 1) * 160, dy / sx
    return ("floor" if dy > 0 else "ceiling"), sy, dx / sy, (1 / sy - 1) * 160


@lru_cache(maxsize=64)
def build_background(seed, room_key, sector):
    """Three 320x200 buffers of palette indices: lights on, one tube broken, lights off.

    Cached: a rematch on the same Seed reuses its rooms. Callers must not modify the buffers.
    """
    s = SECTORS[sector]
    rng = random.Random(f"{seed}:{room_key}")
    puddles = [(rng.uniform(-120, 120), rng.uniform(20, 220), rng.uniform(12, 30))
               for _ in range(rng.randint(0, 3))]
    cracks = [(rng.choice(("back", "left", "right")), rng.random(), rng.random()) for _ in range(rng.randint(2, 5))]
    key = (seed, room_key)
    on, dimmed, off = ([0] * (W * H) for _ in range(3))
    seam = [0] * (W * H)
    tiles = [None] * (W * H)
    for y in range(H):
        for x in range(W):
            k = y * W + x
            surf, sc, u, v = _project(x, y)
            extra = None
            if surf == "back":
                ramp, tile = s["wall"], ("b", int((u + 400) // 40), int((v + 400) // 30))
                light = .62 - abs(v + 40) / 260
            elif surf in ("left", "right"):
                ramp, tile = s["wall"], (surf, int(u // 48), int((v + 400) // 30))
                light = .58 - abs(v + 30) / 280 - (.06 if surf == "right" else 0)
                if -80 < v < -66:                    # a rusted pipe along each side wall
                    t = (v + 80) / 14
                    extra = dither((11, 12, 13, 14, 15, 16), .2 + .75 * math.sin(math.pi * t) - (u % 60 < 4) * .3, x, y)
            elif surf == "floor":
                ramp, tile = s["floor"], ("f", int((u + 400) // 48), int(v // 48))
                light = .55 * sc + .1
                if (tile[1] + tile[2]) % 2 and (int(u) + int(v)) % 7 == 0:
                    light -= .25                     # grated plates
                for pu, pv, pr in puddles:
                    if (u - pu) ** 2 + ((v - pv) * 1.6) ** 2 < pr * pr:
                        extra = dither((18, 19, 20, 21), .35 + .4 * sc + (h32(key, x // 2, y) < .08) * .4, x, y)
            else:
                ramp, tile = s["ceil"], ("c", int((u + 400) // 64), int(v // 40))
                light = .5 * sc
            fog = (1 - s["fog"]) + s["fog"] * (sc - BACK) / (1 - BACK)
            tiles[k] = tile
            light += (h32(key, tile) - .5) * .14 + (h32(key, x // 3, y // 3) - .5) * .08
            if surf in ("back", "left", "right") and extra is None and h32(key, tile, "rust") < s["rust"]:
                if (v + 400) % 30 < h32(key, tile, x // 2) * 22:
                    ramp = RUST                      # rust bleeding down from a seam
            value = light * fog
            seam[k] = dither(ramp, value - .3, x, y) if extra is None else 0
            base = dither(ramp, value, x, y) if extra is None else extra
            on[k] = dimmed[k] = base
            off[k] = dither(ramp, value * .45, x, y) if extra is None else dither((0, 1, 2), .5, x, y)
            if surf == "ceiling":                    # two fluorescent tubes
                for side, tx in ((0, -70), (1, 70)):
                    if abs(u - tx) < 8 and v < 230:
                        lit = s["tube"][1] if abs(u - tx) < 3.5 else s["tube"][0]
                        housing = 0 if abs(u - tx) > 6 else lit
                        on[k] = housing
                        dimmed[k] = housing if side == 0 else (0 if abs(u - tx) > 6 else 2)
                        off[k] = 0 if abs(u - tx) > 6 else 2
            elif surf in ("left", "right") and v < -86 and extra is None:
                on[k] = dither(ramp, value + .25, x, y)   # tube glow on the wall tops
                dimmed[k] = on[k] if surf == "left" else base
    # Panel seams, with a lighter bevel just below them when the lights are on.
    for y in range(H - 1, 0, -1):
        for x in range(W - 1, 0, -1):
            k = y * W + x
            if tiles[k] != tiles[k - W] or tiles[k] != tiles[k - 1]:
                on[k] = dimmed[k] = seam[k]
                off[k] = 0
            elif y > 1 and tiles[k - W] != tiles[k - 2 * W] and on[k] < 10:
                on[k] += 1
    for surf, a, b in cracks:                        # cracks as short random walks
        x = int(BX0 + 10 + a * 100) if surf == "back" else int(8 + a * 70) if surf == "left" else int(W - 8 - a * 70)
        y = int(60 + b * 60)
        for _ in range(rng.randint(14, 30)):
            for buf in (on, dimmed, off):
                buf[y * W + x] = 0
                buf[y * W + x + 1] = 1 if buf is off else 3
            x = max(1, min(W - 2, x + rng.choice((-1, 0, 1))))
            y = min(H - 2, y + 1)
    return {"on": on, "dimmed": dimmed, "off": off}


def side_door(sector, side, locked):
    """A closed blast door on a side wall, drawn in the wall's perspective."""
    wall = SECTORS[sector]["wall"]
    p = Pix(W, H)
    columns = range(W // 2) if side == "left" else range(W // 2, W)
    for y in range(H):
        for x in columns:
            surf, sc, u, v = _project(x, y)
            if surf != side or not (SIDE_DOOR_U[0] < u < SIDE_DOOR_U[1] and SIDE_DOOR_V[0] < v < SIDE_DOOR_V[1]):
                continue
            du, dv = u - SIDE_DOOR_U[0], v - SIDE_DOOR_V[0]
            if du < 6 or du > 74 or dv < 8:
                c = dither(wall, .3 + (dv < 8) * .1, x, y)
            elif du < 9 or du > 71 or dv < 11:
                c = 0
            elif dv > 140:
                c = 16 if int((du + dv) // 7) % 2 else 0          # hazard stripes
            else:
                c = dither(METAL, .5 + .25 * (int(du) % 9 < 2) - abs(du - 40) / 160, x, y)
                if h32("door", sector, int(du) // 6, int(dv) // 9) < .12:
                    c = RUST[1 + (BAYER[y & 3][x & 3] > 7)]       # rust patches on the leaves
                if abs(du - 40) < 1.2 / sc * 1.4:
                    c = 0
            if 34 < du < 46 and -55 < v < -45:
                c = RED if locked else CYAN  # lock lamp
            p.set(x, y, c)
    return p


def back_door(sector, locked):
    """The blast door in the back wall, 48x72, with its corridor hidden behind."""
    wall = SECTORS[sector]["wall"]
    p = Pix(48, 72)
    p.shade(lambda x, y: True, wall, lambda x, y: .7 - x / 160 - y / 400)
    for x in (2, 45):
        for y in (10, 36, 62):
            p.set(x, y, 8)
    p.rect(5, 7, 42, 71, 0)
    for side in (0, 1):
        for y in range(8, 72):
            for lx in range(18):
                x = 6 + lx + side * 18
                c = dither((2, 3, 4, 5, 6), .55 + (lx % 5 == 1) * .2 - side * .12 - y / 300, x, y)
                if y > 60:
                    c = 16 if (lx + y + side * 3) // 3 % 2 else 0
                elif h32("back", sector, x // 4, y // 6) < .1:
                    c = RUST[1 + (BAYER[y & 3][x & 3] > 7)]
                if (side, lx) in ((0, 17), (1, 0)):
                    c = 0
                p.set(x, y, c)
    p.line(10, 30, 14, 34, 2)                         # scratches
    p.line(31, 44, 35, 41, 2)
    p.rect(20, 2, 27, 5, 1)
    p.rect(21, 3, 26, 4, RED if locked else CYAN)
    return p


GUARDIAN_STATES = ("dormant", "listening", "cleared")


def guardian(state):
    """The Guardian: a hooded concrete sentinel whose face is a cracked screen."""
    concrete = (1, 2, 3, 4, 5, 6, 7, 8)
    p = Pix(48, 86)

    def lit(cx, w):
        return lambda x, y: .78 - (x - cx) / w * .55 - y / 260 + (h32("statue", x // 3, y // 3) - .5) * .12
    p.shade(lambda x, y: 6 <= x <= 41 and 72 <= y <= 85, concrete, lambda x, y: .55 - (x - 6) / 90 + (y < 75) * .25)
    p.shade(poly_inside([(15, 27), (33, 27), (40, 72), (7, 72)]), concrete, lit(23.5, 40))
    for x0, x1 in ((19, 15), (24, 24), (29, 33)):     # robe folds
        p.line(x0, 34, x1, 71, 1)
        p.line(x0 - 1, 35, x1 - 1, 71, 5)
    p.shade(poly_inside([(10, 25), (22, 23), (22, 31), (9, 33)]), METAL + (9,), lambda x, y: .75 - y / 120)
    p.shade(poly_inside([(25, 23), (37, 25), (38, 33), (25, 31)]), (2,) + METAL[:-1], lambda x, y: .45 - y / 160)
    for x, y in ((12, 27), (19, 26), (28, 26), (35, 28)):
        p.set(x, y, 9)
    p.shade(lambda x, y: ((x - 23.5) / 11) ** 2 + ((y - 15) / 13) ** 2 <= 1, concrete, lit(23.5, 30))
    p.shade(lambda x, y: ((x - 23.5) / 7.5) ** 2 + ((y - 17) / 8.5) ** 2 <= 1, (0, 1), lambda x, y: .2)
    p.rect(18, 12, 29, 21, 2)
    for y in range(12, 22, 2):
        p.line(18, y, 29, y, 3)
    p.line(27, 12, 24, 21, 1)                         # the crack across the screen
    if state == "dormant":
        p.line(21, 16, 26, 16, 27)
    elif state == "listening":
        p.line(20, 16, 27, 16, CYAN)
        p.line(21, 15, 26, 15, 29)
        p.line(21, 17, 26, 17, 29)
        p.line(22, 16, 25, 16, 30)
        for x, y in ((17, 16), (30, 16), (23, 13), (24, 20)):
            p.set(x, y, CYAN)
    else:
        p.line(21, 16, 26, 16, 20)
        p.line(22, 16, 25, 16, 21)
    for x0, y0, x1, y1 in ((14, 18, 8, 72), (33, 18, 39, 72)):   # cables down its back
        p.line(x0, y0, x1, y1, 1)
        p.line(x0 + 1, y0, x1 + 1, y1, 4)
    # The same wear as the walls: chips, cracks and rust bleeding from the pedestal.
    for x, y in ((20, 45), (21, 46), (21, 47), (30, 58), (31, 59), (13, 52), (34, 40), (35, 41)):
        p.set(x, y, 1)
    for x, y in ((16, 8), (17, 7), (29, 9)):
        p.set(x, y, 2)
    for x in range(9, 39, 5):
        for y in range(76, 76 + int(h32("pedestal", x) * 8)):
            p.set(x, y, 13)
    for x in range(12, 36, 7):
        p.set(x, 73, 12)
    p.outline(0)
    return p


def fade_veil(level):
    """An ordered-dither veil of black covering level/4 of the frame (level 1..4)."""
    p = Pix(W, H)
    for y in range(H):
        for x in range(W):
            if BAYER[y & 3][x & 3] < level * 4:
                p.px[y * W + x] = 0
    return p
