"""Shows a Scene on a Tk canvas: 320x200 pixel art at the largest integer zoom that fits.

Tk does the work per frame (alpha compositing with photo copy, then the zoom);
Python only computes pixels when a room or sprite is first built.
"""

import tkinter as tk

from pixels import png
from room_art import (BACK_DOOR, BEHIND_DOOR, GUARDIAN_ASIDE, GUARDIAN_AT, H, W,
                      back_door, build_background, fade_veil, guardian, side_door)


class PixelView:
    def __init__(self, canvas):
        self.canvas = canvas
        self.frame = tk.PhotoImage(master=canvas, width=W, height=H)
        self.display = None
        self.scale = 1
        self.origin = (0, 0)
        self._buffers = {}
        self._photos = {}
        left = side_door("shallow", "left", False).bbox()
        right = side_door("shallow", "right", False).bbox()
        # Native click regions in portal order: left, ahead, right, behind.
        self.regions = (left, BACK_DOOR, right, BEHIND_DOOR)

    def _photo(self, key, build):
        if key not in self._photos:
            self._photos[key] = tk.PhotoImage(master=self.canvas, data=build())
        return self._photos[key]

    def _background(self, scene, lights):
        key = (scene.seed, scene.room_key, scene.sector)
        if key not in self._buffers:
            self._buffers[key] = build_background(*key)
        return self._photo(("bg",) + key + (lights,), lambda: png(W, H, self._buffers[key][lights]))

    def _copy(self, photo, x=0, y=0):
        self.frame.tk.call(self.frame, "copy", photo, "-to", x, y)

    def draw(self, scene, fade=0, lights="on"):
        """Compose the scene, darken it by `fade` (0..4) and show it zoomed."""
        self._copy(self._background(scene, lights))
        for door in scene.doors:
            if door.portal == 1:
                photo = self._photo(("back", scene.sector, door.locked),
                                    lambda: back_door(scene.sector, door.locked).png())
                self._copy(photo, BACK_DOOR[0], BACK_DOOR[1])
            elif door.portal in (0, 2):
                side = "left" if door.portal == 0 else "right"
                self._copy(self._photo(("side", scene.sector, side, door.locked),
                                       lambda: side_door(scene.sector, side, door.locked).png()))
        if scene.guardian:
            x, y = GUARDIAN_AT
            photo = self._photo(("guardian", scene.guardian), lambda: guardian(scene.guardian).png())
            self._copy(photo, x + (GUARDIAN_ASIDE if scene.guardian == "cleared" else 0), y)
        if fade:
            self._copy(self._photo(("veil", fade), lambda: fade_veil(fade).png()))
        cw, ch = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        scale = max(1, min(cw // W, ch // H))
        if self.display is None or scale != self.scale:
            self.scale = scale
            self.display = tk.PhotoImage(master=self.canvas, width=W * scale, height=H * scale)
        self.origin = ((cw - W * scale) // 2, (ch - H * scale) // 2)
        self.display.tk.call(self.display, "copy", self.frame, "-zoom", scale)
        self.canvas.create_image(*self.origin, image=self.display, anchor="nw", tags="pixels")

    def to_native(self, x, y):
        nx, ny = (x - self.origin[0]) // self.scale, (y - self.origin[1]) // self.scale
        return (nx, ny) if 0 <= nx < W and 0 <= ny < H else None

    def to_canvas(self, x, y):
        return self.origin[0] + x * self.scale, self.origin[1] + y * self.scale

    def region_at(self, x, y):
        """The portal whose clickable region holds this canvas point, or None."""
        native = self.to_native(x, y)
        if native:
            for portal, (x0, y0, x1, y1) in enumerate(self.regions):
                if x0 <= native[0] <= x1 and y0 <= native[1] <= y1:
                    return portal
        return None
