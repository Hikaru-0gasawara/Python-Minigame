"""Small deterministic motion curves and a native Tk alpha veil."""

import base64
from collections import OrderedDict
import struct
import tkinter as tk
import zlib


def smooth(value):
    """Quintic ease with zero velocity and acceleration at both ends."""
    t = max(0.0, min(1.0, value))
    return t*t*t*(t*(t*6-15)+10)


def blend(first, second, amount):
    t = max(0.0, min(1.0, amount))
    return "#" + "".join(f"{round(int(first[i:i+2], 16)*(1-t)+int(second[i:i+2], 16)*t):02x}"
                         for i in (1, 3, 5))


class CanvasVeil:
    """Cache bounded, translucent PNG planes; no Pillow or screenshot capture."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.images = OrderedDict()

    def draw(self, opacity):
        alpha = round(max(0., min(1., opacity))*32)*255//32
        if alpha <= 0:
            return
        w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        key = w, h, alpha
        if key not in self.images:
            def chunk(kind, data):
                return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind+data))
            png = (b"\x89PNG\r\n\x1a\n" +
                   chunk(b"IHDR", struct.pack("!2I5B", 1, 1, 8, 6, 0, 0, 0)) +
                   chunk(b"IDAT", zlib.compress(bytes((0, 8, 14, 18, alpha)))) + chunk(b"IEND", b""))
            pixel = tk.PhotoImage(master=self.canvas, data=base64.b64encode(png))
            self.images[key] = pixel.zoom(w, h)
            while len(self.images) > 12:
                self.images.popitem(last=False)
        self.images.move_to_end(key)
        self.canvas.create_image(0, 0, image=self.images[key], anchor="nw", tags="motion_veil")
