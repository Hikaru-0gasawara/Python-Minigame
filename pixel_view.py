"""Shows a Scene on a Tk canvas: 320x200 pixel art at the largest integer zoom that fits.

Tk does the work per frame (alpha compositing with photo copy, then the zoom);
Python only computes pixels when a room or sprite is first built, and the room
a player is walking into is painted a slice per frame while its door opens (a
worker thread would fight the main thread for the GIL and stall every frame).
The HUD lives on its own layer, so a walk-through zooms the room but not the HUD.
"""

import math
from pathlib import Path
import tempfile
import time
import tkinter as tk

from palette import BAYER, PLAYER_INK, hex_color
from pixels import png
from props import PROP_AT, decor_sprite, elite, prop_sprite
from room_art import (BACK_DOOR, GUARDIAN_ASIDE, GUARDIAN_AT, H, LIGHTS, W,
                      back_door, guardian, paint_background, side_door)

ZOOM_STEPS = (1, 4 / 3, 5 / 3, 2, 8 / 3, 10 / 3)   # x3, x4, x5, x6, x8, x10 at the usual scale


def _veil(level, scale):
    """The stipple for an XBM covering level/4 of the screen in a Bayer dither, one art pixel per cell.

    Tk only takes custom stipples from files, so they are written once to the temp folder.
    """
    path = Path(tempfile.gettempdir()) / "ecos-veils" / f"veil-{level}-{scale}.xbm"
    try:
        if not path.exists():
            size = 4 * scale
            data = []
            for y in range(size):
                bits = [BAYER[y // scale % 4][x // scale % 4] < level * 4 for x in range(size)]
                data += [sum(bit << i for i, bit in enumerate(bits[at:at + 8])) for at in range(0, size, 8)]
            path.parent.mkdir(exist_ok=True)
            hex_bytes = ", ".join(f"0x{b:02x}" for b in data)
            path.write_text(f"#define v_width {size}\n#define v_height {size}\n"
                            f"static unsigned char v_bits[] = {{ {hex_bytes} }};\n")
    except OSError:     # no writable temp folder: Tk's own stipples, finer, but never a frozen frame
        return ("", "gray25", "gray50", "gray75", "")[level]
    return "@" + path.as_posix()


class PixelView:
    def __init__(self, canvas):
        self.canvas = canvas
        self.frame = tk.PhotoImage(master=canvas, width=W, height=H)
        self.other = tk.PhotoImage(master=canvas, width=W, height=H)    # the incoming view of a pan
        self.hud = tk.PhotoImage(master=canvas, width=W, height=H)
        self.display = None
        self.scale = 1
        self.origin = (0, 0)
        self._ready = {}          # background PNG bytes per (seed, room, sector)
        self._jobs = {}           # rooms being painted a slice at a time
        self._photos = {}
        left = side_door("shallow", "left", False).bbox()
        right = side_door("shallow", "right", False).bbox()
        # Native click regions of the doors drawn in the room: left, ahead, right.
        self.regions = (left, BACK_DOOR, right)

    def _photo(self, key, build):
        if key not in self._photos:
            self._photos[key] = tk.PhotoImage(master=self.canvas, data=build())
        return self._photos[key]

    def _paint(self, key):
        """Paint and encode one room, yielding between slices; stores the PNGs when done."""
        buffers = yield from paint_background(*key)
        encoded = {}
        for lights in LIGHTS:
            # shortcut: one PNG per slice is ~10 ms, a little over budget; chunk it if frames stutter.
            encoded[lights] = png(W, H, buffers[lights])
            yield
        self._ready[key] = encoded

    def prepare(self, seed, room_key, sector):
        """Start painting a room someone is about to enter; `work` advances it each frame."""
        key = (seed, room_key, sector)
        if key not in self._ready and key not in self._jobs:
            self._jobs[key] = self._paint(key)

    def work(self, budget=.012):
        """Spend up to `budget` seconds of this frame painting prepared rooms."""
        end = time.perf_counter() + budget
        for key, job in list(self._jobs.items()):
            for _ in job:
                if time.perf_counter() >= end:
                    return
            del self._jobs[key]

    def _background(self, scene, lights):
        key = (scene.seed, scene.room_key, scene.sector)
        if key not in self._ready:
            for _ in self._jobs.pop(key, None) or self._paint(key):   # finish it now if it is not ready
                pass
        return self._photo(("bg",) + key + (lights,), lambda: self._ready[key][lights])

    def _sprite(self, target, key, build, x=0, y=0):
        target.tk.call(target, "copy", self._photo(key, lambda: build().png()), "-to", x, y)

    def compose(self, scene, lights="on", glitch=False, opening=None, target=None, aside=None):
        """Draw the room into a native frame, back to front.

        Layers: wall decorations, doors and the core gate, floor props, the
        Guardian, then cables hanging in front of everything. `opening` is
        (portal, step) for a door caught mid-way open; `aside` is how far a
        Guardian has stepped out of the way (by default, all the way once Cleared).
        """
        target = target or self.frame
        target.tk.call(target, "copy", self._background(scene, lights))
        hanging = []
        for name, variant, x, y in scene.decor:
            if name == "cables":
                hanging.append((variant, x, y))
                continue
            if name == "screen" and glitch:
                variant = "static"
            self._sprite(target, ("decor", name, variant), lambda: decor_sprite(name, variant), x, y)
        for door in scene.doors:
            step = opening[1] if opening and opening[0] == door.portal else 0
            locked = door.locked and not step
            if door.portal == 1:
                self._sprite(target, ("back", scene.sector, locked, step),
                             lambda: back_door(scene.sector, locked, step), BACK_DOOR[0], BACK_DOOR[1])
            elif door.portal in (0, 2):
                side = "left" if door.portal == 0 else "right"
                self._sprite(target, ("side", scene.sector, side, locked, step),
                             lambda: side_door(scene.sector, side, locked, step))
        if scene.prop:
            name, state = scene.prop
            self._sprite(target, ("prop", name, state), lambda: prop_sprite(name, state), *PROP_AT[name])
        if scene.guardian:
            ink = PLAYER_INK[scene.player]
            if aside is None:
                aside = GUARDIAN_ASIDE if scene.guardian == "cleared" else 0
            draw, (x, y) = (elite, PROP_AT["elite"]) if scene.elite else (guardian, GUARDIAN_AT)
            self._sprite(target, (draw.__name__, scene.guardian, ink), lambda: draw(scene.guardian, ink), x + aside, y)
        for variant, x, y in hanging:
            self._sprite(target, ("decor", "cables", variant), lambda: decor_sprite("cables", variant), x, y)

    def clear_hud(self):
        self.hud.blank()

    def overlay(self, photo, x, y):
        self.hud.tk.call(self.hud, "copy", photo, "-to", x, y)

    def fill(self, ink, x0, y0, x1, y1):
        """Paint a palette colour over a native rectangle of the HUD layer, edges included."""
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W - 1, x1), min(H - 1, y1)
        if x1 >= x0 and y1 >= y0:
            self.hud.put(hex_color(ink), to=(x0, y0, x1 + 1, y1 + 1))

    def zoom_steps(self):
        """Integer zooms for a walk-through at the current scale, from the scale itself upward."""
        return sorted({max(self.scale, round(self.scale * f)) for f in ZOOM_STEPS})

    def present(self, zoom=None, centre=(W // 2, H // 2), fade=0, pan=None):
        """Show the frame at the largest integer zoom that fits, centred on black.

        `zoom` magnifies the room around `centre` for a walk-through; `pan` is
        (offset, turn) sliding `other` in from that side; `fade` (0..4) darkens
        the room with a dither one art pixel wide. The HUD always sits on top, unzoomed.
        """
        cw, ch = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        scale = max(1, min(cw // W, ch // H))
        if self.display is None or scale != self.scale:
            self.scale = scale
            self.display = tk.PhotoImage(master=self.canvas, width=W * scale, height=H * scale)
            self.hud_display = tk.PhotoImage(master=self.canvas, width=W * scale, height=H * scale)
        self.origin = ((cw - W * scale) // 2, (ch - H * scale) // 2)
        show = self.display.tk.call
        if pan:
            offset, turn = pan
            # (photo, from x, to x, drawn at x): turning right slides the new view in from the right.
            if turn > 0:
                parts = ((self.frame, offset, W, 0), (self.other, 0, offset, W - offset))
            else:
                parts = ((self.other, W - offset, W, 0), (self.frame, 0, W - offset, offset))
            for photo, x0, x1, at in parts:
                if x1 > x0:
                    show(self.display, "copy", photo, "-from", x0, 0, x1, H, "-zoom", scale, "-to", at * scale, 0)
        elif zoom and zoom > scale:
            width, height = math.ceil(W * scale / zoom), math.ceil(H * scale / zoom)
            x0 = min(max(0, centre[0] - width // 2), W - width)
            y0 = min(max(0, centre[1] - height // 2), H - height)
            show(self.display, "copy", self.frame, "-from", x0, y0, x0 + width, y0 + height, "-zoom", zoom, "-to", 0, 0)
        else:
            show(self.display, "copy", self.frame, "-zoom", scale)
        x, y = self.origin
        self.canvas.create_image(x, y, image=self.display, anchor="nw", tags="pixels")
        if fade:
            # A stippled rectangle, not a dithered photo: Tk builds photo masks pixel by pixel,
            # so a checkerboard of transparency costs seconds; GDI draws a stipple in microseconds.
            self.canvas.create_rectangle(x, y, x + W * scale, y + H * scale, fill="#000000", outline="",
                                         stipple=_veil(fade, scale), offset=f"{x},{y}", tags="pixels")
        self.hud_display.blank()
        self.hud_display.tk.call(self.hud_display, "copy", self.hud, "-zoom", scale)
        self.canvas.create_image(x, y, image=self.hud_display, anchor="nw", tags="pixels")

    def to_native(self, x, y):
        nx, ny = (x - self.origin[0]) // self.scale, (y - self.origin[1]) // self.scale
        return (nx, ny) if 0 <= nx < W and 0 <= ny < H else None

    def to_canvas(self, x, y):
        return self.origin[0] + x * self.scale, self.origin[1] + y * self.scale

    def centre(self, rect):
        """Canvas coordinates of a native rectangle's centre, for clicks and tests."""
        x0, y0, x1, y1 = rect
        return self.to_canvas((x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2)
