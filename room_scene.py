"""Retained-material dungeon illustration for a Tk Canvas.

All art is drawn locally. A room's surface marks are deterministic and cached;
only the camera, door leaves and a gentle light pulse change between frames.
"""

import math
import random
import zlib


DOOR_BOUNDS = ((.04, .19, .255, .87), (.39, .27, .61, .70),
               (.745, .19, .96, .87), (.39, .91, .61, .985))
DOOR_BOUNDS4 = DOOR_BOUNDS
FONT = "Segoe UI"


def _color(hex_color, factor):
    return "#" + "".join(f"{max(0, min(255, round(int(hex_color[i:i+2], 16)*factor))):02x}"
                         for i in (1, 3, 5))


def _point(quad, u, v):
    """Bilinear mapping in clockwise TL, TR, BR, BL quads."""
    a, b, c, d = quad
    return ((1-v)*((1-u)*a[0]+u*b[0])+v*((1-u)*d[0]+u*c[0]),
            (1-v)*((1-u)*a[1]+u*b[1])+v*((1-u)*d[1]+u*c[1]))


def _quad(quad, u0, v0, u1, v1):
    return [_point(quad, u0, v0), _point(quad, u1, v0),
            _point(quad, u1, v1), _point(quad, u0, v1)]


class RoomScene:
    """Render the world only; caller owns timers, input and challenge overlays."""

    def __init__(self, canvas):
        self.canvas = canvas
        self._key = None
        self._material = []
        self.w = self.h = 1
        self.camera = (1., 0., 0.)

    def _xy(self, point):
        zoom, dx, bob = self.camera
        return ((.5+(point[0]-.5)*zoom+dx)*self.w,
                (.48+(point[1]-.48)*zoom+bob)*self.h)

    def _poly(self, points, fill, outline="", width=1):
        return self.canvas.create_polygon(
            *[v for p in points for v in self._xy(p)], fill=fill,
            outline=outline, width=width, tags="world")

    def _line(self, points, color, width=1):
        return self.canvas.create_line(
            *[v for p in points for v in self._xy(p)], fill=color,
            width=width, tags="world")

    def _text(self, point, value, color="#becac8", size=9, **kw):
        return self.canvas.create_text(*self._xy(point), text=value, fill=color,
                                       font=(FONT, size, "bold"), tags="world", **kw)

    def _tile_surface(self, rng, quad, rows, columns, base, *, floor=False):
        """Store slabs, worn bevels and occasional stains in local coordinates."""
        for row in range(rows):
            # Nonuniform floor depths make distant tiles smaller.
            v0 = (row/rows)**1.65 if floor else row/rows
            v1 = ((row+1)/rows)**1.65 if floor else (row+1)/rows
            stagger = .5 if row % 2 and not floor else 0
            for column in range(-1 if stagger else 0, columns):
                u0 = max(0, (column+stagger)/columns)
                u1 = min(1, (column+1+stagger)/columns)
                if u1-u0 < .001:
                    continue
                gap = .005
                slab = _quad(quad, u0+gap, v0+gap, u1-gap, v1-gap)
                shade = rng.uniform(.91, 1.09)
                self._material.append(("p", slab, _color(base, shade), 1))
                self._material.append(("l", slab[:2], _color(base, shade*1.17), 1))
                if rng.random() < .30:
                    # Irregular chipped patch, never a flashing per-frame noise.
                    u = rng.uniform(u0+.01, max(u0+.011, u1-.03))
                    v = rng.uniform(v0+.012, max(v0+.013, v1-.025))
                    points = [_point(quad, u, v), _point(quad, u+.016, v-.006),
                              _point(quad, u+.027, v+.007), _point(quad, u+.009, v+.012)]
                    self._material.append(("p", points, _color(base, .72), 1))
                if rng.random() < .12:
                    u = (u0+u1)/2
                    points = [_point(quad, u, v0+.01), _point(quad, u-.009, (v0+v1)/2),
                              _point(quad, u+.004, v1-.025)]
                    self._material.append(("l", points, _color(base, .52), 1))

    def _build_material(self, room_key, kind):
        rng = random.Random(zlib.crc32(repr((room_key, kind)).encode("utf-8")))
        self._material = []
        # Muted mineral colors retain physical texture beneath colored lighting.
        base = {"elite": "#51504e", "boss": "#514a50", "sanctuary": "#4b5752",
                "treasure": "#575347"}.get(kind, "#4b5556")
        self._tile_surface(rng, [(0, 0), (.30, .20), (.30, .70), (0, 1)], 5, 4,
                           _color(base, .79))
        self._tile_surface(rng, [(.70, .20), (1, 0), (1, 1), (.70, .70)], 5, 4,
                           _color(base, .65))
        self._tile_surface(rng, [(.30, .20), (.70, .20), (.70, .70), (.30, .70)],
                           5, 7, base)
        self._tile_surface(rng, [(.30, .70), (.70, .70), (1.15, 1.18), (-.15, 1.18)],
                           5, 7, "#303d40", floor=True)
        self._tile_surface(rng, [(0, 0), (1, 0), (.70, .20), (.30, .20)],
                           3, 6, "#222d30")

    def _mapped_line(self, quad, points, color, width=1):
        self._line([_point(quad, u, v) for u, v in points], color, width)

    def _door_leaf(self, inner, offset, right=False):
        """Translate a rigid half-door, clipping its details at the jamb.

        Everything uses the original leaf's coordinates, so handles and panels
        disappear behind the frame instead of being squeezed as the door opens.
        """
        def plate(u0, v0, u1, v1, fill):
            x0, x1 = max(0., offset+u0*.5), min(1., offset+u1*.5)
            if x1 > x0:
                self._poly(_quad(inner, x0, v0, x1, v1), fill)

        def line(points, color, width=1):
            for (u0, v0), (u1, v1) in zip(points, points[1:]):
                x0, x1 = offset+u0*.5, offset+u1*.5
                delta = x1-x0
                if abs(delta) < 1e-8:
                    if 0 <= x0 <= 1:
                        self._mapped_line(inner, [(x0, v0), (x1, v1)], color, width)
                    continue
                a, b = sorted(((0-x0)/delta, (1-x0)/delta))
                a, b = max(0., a), min(1., b)
                if b > a:
                    self._mapped_line(inner, [(x0+delta*a, v0+(v1-v0)*a),
                                               (x0+delta*b, v0+(v1-v0)*b)], color, width)

        plate(0, 0, 1, 1, "#34464b")
        plate(.045, .02, .955, .98, "#3c5156")
        plate(.12, .09, .88, .445, "#1e3037")
        plate(.15, .11, .85, .435, "#2a3e46")
        plate(.12, .60, .88, .90, "#23343b")
        line([(.12, .445), (.88, .445)], "#68817e")
        line([(.12, .90), (.88, .90)], "#607674")
        line([(.055, .03), (.055, .97)], "#617a7b")
        line([(.945, .03), (.945, .97)], "#1a2c32", 2)
        for v in (.65, .68, .71):
            line([(.22, v), (.76, v)], "#14272e", 2)
        line([(.20, .82), (.73, .79)], "#182b32")
        line([(.27, .85), (.65, .83)], "#4b6469")
        # The warm metal grip stays the same size throughout the translation.
        grip = .19 if right else .69
        plate(grip-.04, .465, grip+.13, .58, "#172a31")
        plate(grip, .48, grip+.065, .565, "#adb6aa")
        plate(grip, .48, grip+.065, .49, "#e0dac6")
        plate(.82 if right else .08, .49, .90 if right else .16, .535, "#597778")

    def _door(self, index, portal, locked, progress, pulse, hovered=False):
        # Side door edges follow the same depth directions as their walls.
        quads = [((.04, .19), (.255, .305), (.255, .745), (.04, .87)),
                 ((.39, .27), (.61, .27), (.61, .70), (.39, .70)),
                 ((.745, .305), (.96, .19), (.96, .87), (.745, .745))]
        q = quads[index]
        accent = "#e27461" if locked else portal.get("color", "#62d8ca")
        # Outside shadow, outer cast frame, inner bevel and thick recessed jamb.
        self._poly(_quad(q, -.03, -.018, 1.04, 1.04), "#101a1c")
        self._poly(q, "#4e615f", "#80928b")
        self._poly(_quad(q, .04, .035, .96, .985), "#262e30", "#343e40")
        self._poly(_quad(q, .075, .07, .925, .96), "#070e12")
        self._poly([_point(q, .04, .035), _point(q, .075, .07),
                    _point(q, .075, .96), _point(q, .04, .985)], "#101a1c")
        self._poly([_point(q, .925, .07), _point(q, .96, .035),
                    _point(q, .96, .985), _point(q, .925, .96)], "#727975")
        inner = _quad(q, .085, .08, .915, .95)
        # A real corridor is progressively uncovered by the two sliding leaves.
        self._poly(inner, "#0c171b")
        end = _quad(inner, .33, .25, .67, .73)
        self._poly([inner[0], end[0], end[3], inner[3]], "#253236")
        self._poly([end[1], inner[1], inner[2], end[2]], "#19282d")
        self._poly([inner[3], end[3], end[2], inner[2]], "#172326")
        self._poly(end, "#101d22")
        self._mapped_line(inner, [(0, 1), (.33, .73), (.67, .73), (1, 1)], "#3d7978")
        self._poly(_quad(inner, .42, .26, .58, .285), "#8fc5bb")
        p = max(0., min(1., progress))
        if p < 1.:
            self._door_leaf(inner, -.5*p)
            self._door_leaf(inner, .5+.5*p, right=True)
        # Hardware stays on the frame, including rail and bolts.
        self._mapped_line(q, [(.06, .05), (.94, .05)], "#a0aaa0", 2)
        self._mapped_line(q, [(.06, .975), (.94, .975)], "#929384", 3)
        for u in (.022, .978):
            for v in (.12, .86):
                self._poly(_quad(q, u-.007, v-.008, u+.007, v+.008), "#abb1a0")
        self._poly(_quad(q, .02, .22, .045, .62), _color(accent, pulse))
        self._poly(_quad(q, .955, .22, .98, .62), _color(accent, .76))
        if hovered and not locked:
            self._mapped_line(q, [(0, .15), (0, 0), (.25, 0)], accent, 2)
            self._mapped_line(q, [(.75, 0), (1, 0), (1, .15)], accent, 2)
            self._mapped_line(q, [(0, .85), (0, 1), (.25, 1)], accent, 2)
            self._mapped_line(q, [(.75, 1), (1, 1), (1, .85)], accent, 2)
        if locked:
            self._poly(_quad(q, .16, .465, .84, .505), "#69423b", "#bf7a5e")
            self._poly(_quad(q, .455, .44, .545, .535), "#c56a52")
        # Small nameplate above each actual opening, never on a solid wall.
        self._poly(_quad(q, .09, -.12, .91, -.025), "#101e24", accent if hovered and not locked else "#536867")
        label = str(portal.get("label", "Passagem")).upper()
        if len(label) > 18:
            label = label[:17] + "…"
        self._text(_point(q, .5, -.073), f"{portal.get('compass', '')}  {label}", accent, 8)

    def draw(self, *, room_key, kind, portals, facing, locked, opening=None,
             camera=(1., 0., 0.), now=0., effects=True, hovered=None):
        self.canvas.delete("world")
        self.w = max(1, self.canvas.winfo_width())
        self.h = max(1, self.canvas.winfo_height())
        self.camera = camera
        key = (room_key, kind)
        if key != self._key:
            self._key = key
            self._build_material(room_key, kind)
        self._poly([(-1, -1), (2, -1), (2, 2), (-1, 2)], "#152225")
        for operation, points, color, width in self._material:
            if operation == "p":
                self._poly(points, color)
            else:
                self._line(points, color, width)
        # Recessed ceiling edges and stepped cornices give surfaces thickness.
        self._poly([(0, .07), (.30, .23), (.70, .23), (1, .07),
                    (1, .105), (.70, .258), (.30, .258), (0, .105)], "#253437")
        self._line([(0, .07), (.30, .23), (.70, .23), (1, .07)], "#61706b", 2)
        self._line([(0, .105), (.30, .258), (.70, .258), (1, .105)], "#182629", 3)
        # Load-bearing columns and metal skirting anchor the room geometry.
        for x in (.30, .70):
            self._poly([(x-.017, .195), (x+.017, .195),
                        (x+.017, .715), (x-.017, .715)], "#1b2b2f")
            self._poly([(x-.010, .195), (x+.010, .195),
                        (x+.010, .705), (x-.010, .705)], "#35484b")
            self._line([(x-.01, .20), (x-.01, .70)], "#687d77")
            for y in (.29, .62):
                self._poly([(x-.014, y), (x+.014, y),
                            (x+.014, y+.021), (x-.014, y+.021)], "#506763")
        self._line([(0, .965), (.30, .695), (.70, .695), (1, .965)], "#151f22", 8)
        accent = {"elite": "#d99466", "boss": "#bf92c4", "sanctuary": "#83cba9",
                  "treasure": "#e0c27d"}.get(kind, "#6bbdbb")
        pulse = .93 + .07*math.sin(now*1.5) if effects else 1.
        # Physical ceiling girders and luminous recessed strip housings.
        for offset in (0, .10):
            self._poly([(offset, 0), (1-offset, 0), (.71-offset*.3, .17-offset*.2),
                        (.29+offset*.3, .17-offset*.2)], "#1b282b", "#46514c")
        for x0, x1 in ((.13, .36), (.87, .64)):
            self._line([(x0, 0), (x1, .185)], "#0a161b", 9)
            self._line([(x0, 0), (x1, .185)], _color(accent, .65), 4)
            self._line([(x0, 0), (x1, .185)], _color(accent, pulse), 2)
        # Low industrial guide lights are inset into the floor at the wall seam.
        self._line([(.025, .982), (.305, .708)], "#284542", 5)
        self._line([(.975, .982), (.695, .708)], "#284542", 5)
        self._line([(.025, .982), (.305, .708)], _color(accent, .65), 1)
        self._line([(.975, .982), (.695, .708)], _color(accent, .65), 1)
        for i, portal in enumerate(portals[:3]):
            if portal is not None:
                progress = opening[1] if opening and opening[0] == i else 0.
                self._door(i, portal, locked, progress, pulse, hovered == i)
        # These small overlays remain screen-fixed while the camera moves.
        self.camera = (1., 0., 0.)
        self._poly([(0, 0), (1, 0), (1, .083), (0, .083)], "#0b171d")
        self._text((.025, .039), f"OLHANDO {facing}", "#9ccecc", 9, anchor="w")
        self._text((.975, .039), "PORTAS TRAVADAS" if locked else "EXPLORAÇÃO LIVRE",
                   "#d69980" if locked else "#becac8", 8, anchor="e")
        if len(portals) > 3 and portals[3] is not None:
            x0, y0, x1, y1 = DOOR_BOUNDS[3]
            self._poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#10232a",
                       "#8ddbd3" if hovered == 3 and not locked else "#587977")
            self._text(((x0+x1)/2, (y0+y1)/2),
                       f"↓  {portals[3].get('compass', '')} · ATRÁS", "#b9d4ce", 9)
