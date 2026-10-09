"""The launch screen: an animated pixel scene with the ECOS title, a column of options and the Records."""

import functools
import math
import random
import time
import tkinter as tk

import font
import hud
import menu_art
from dungeon import MODES, format_seed, parse_seed
from palette import hex_color
from pixel_view import PixelView
from pixels import Pix
from room_art import H, W

ROWS = ("difficulty", "players", "seed", "sound", "motion", "start")
LABELS = {"difficulty": "DIFICULDADE", "players": "JOGADORES", "seed": "SEED", "sound": "SOM", "motion": "MOVIMENTO"}
SEED_CHARS = "0123456789abcdefABCDEF-"
SEED_LENGTH = 9                     # 3F9A-12C0
COLUMN_AT, VALUE_X = (6, 64), 77
TITLE_ZOOM = 4
FAR, NEAR = 3, 9                    # parallax: how many pixels per second each tower layer slides
FOOTER = "↑↓ ESCOLHE · ←→ MUDA · F1 AJUDA"

# The help dialog is a plain Tk window.
PANEL, TEXT, GOLD, TEAL, CARD, LINE, FONT = "#0d1a21", "#edf8f8", "#efc788", "#56eee5", "#13262e", "#25414a", "Segoe UI"


@functools.cache
def art():
    """Every layer encoded once per run, as the menu comes back after each Expedition."""
    cables, sparks = menu_art.hanging_cables()
    title = Pix(font.measure("ECOS") + 1, font.HEIGHT + 1)
    font.draw(title, 0, 0, "ECOS", 29, shadow=0)
    return {"backdrop": menu_art.backdrop().png(), "far": menu_art.towers("far").png(),
            "near": menu_art.towers("near").png(), "cables": cables.png(), "title": title.png(),
            "cores": [menu_art.core(i).png() for i in range(menu_art.CORE_FRAMES)], "sparks": sparks}


def column(difficulty, players, seed, muted, effects, focus):
    """The options, one row each, with the focused one lit; regions are (("row", i), rect)."""
    name, rooms, seconds, _tiers = MODES[difficulty]
    values = {"difficulty": name.upper(), "players": "1 · SOLO" if players == 1 else str(players),
              "seed": seed + "_" if ROWS[focus] == "seed" else seed or "ALEATÓRIA",
              "sound": "MUDO" if muted else "LIGADO", "motion": "COMPLETO" if effects else "REDUZIDO"}
    width = VALUE_X + font.measure("← AVENTUREIRO →") + 6
    p = hud.panel(width, (len(ROWS) + 1) * font.LINE + 6)
    x0, y0 = COLUMN_AT
    piece = hud.Piece(p, x0, y0)
    for i, row in enumerate(ROWS):
        y, lit = 2 + i * font.LINE, i == focus
        if lit:
            p.rect(1, y, width - 2, y + font.LINE - 1, hud.EDGE)
        if row == "start":
            text = "ENTRAR →"
            font.draw(p, (width - font.measure(text)) // 2, y, text, hud.GOLD if lit else hud.TEXT, shadow=0)
        else:
            value = f"← {values[row]} →" if lit and row != "seed" else values[row]
            font.draw(p, 6, y, LABELS[row], hud.TEXT if lit else hud.MUTED, shadow=0)
            font.draw(p, VALUE_X, y, value, hud.GOLD if lit else hud.TEXT, shadow=0)
            text = f"{LABELS[row]} {value}"
        piece.texts.append(text)
        piece.regions.append((("row", i), (x0 + 1, y0 + y, x0 + width - 2, y0 + y + font.LINE - 1)))
    stats = f"{seconds}s POR PERGUNTA · {rooms} SALAS"
    font.draw(p, (width - font.measure(stats)) // 2, 4 + len(ROWS) * font.LINE, stats, hud.MUTED, shadow=0)
    piece.texts.append(stats)
    return piece


def records_panel(records, difficulty):
    """Bottom-right: the five best escapes of the selected Difficulty."""
    lines = [(f"RECORDES · {MODES[difficulty][0].upper()}", hud.GOLD)]
    lines += [(f"{i}. {hud.duration(r['seconds'])}  {r['players']}J  {format_seed(r['seed'])}",
               hud.TEXT if i == 1 else hud.MUTED) for i, r in enumerate(records, 1)]
    if not records:
        lines.append(("Nenhuma fuga ainda.", hud.MUTED))
    piece = hud.text_panel(lines, 0, 0)
    piece.x, piece.y = W - piece.pix.w - 4, H - piece.pix.h - 4
    return piece


def caption(text, ink, y, x=None):
    """A line of text on the scene itself, with a shadow instead of a panel."""
    p = Pix(font.measure(text) + 1, font.HEIGHT + 1)
    font.draw(p, 0, 0, text, ink, shadow=0)
    return hud.Piece(p, (W - p.w) // 2 if x is None else x, y, [text])


class Setup(tk.Frame):
    """All animation and bindings belong to this screen and die with it."""

    def __init__(self, app):
        super().__init__(app, bg="#000000")
        self.app = app
        self.difficulty = getattr(app, "menu_difficulty", 1)
        self.players = getattr(app, "menu_players", 1)
        self.seed = ""
        self.focus = 0
        self.animation_job = None
        self._dead = False
        self._help = None
        self.started = self._last = time.monotonic()
        self.sparks = []                # [x, y, vx, vy, life] in native pixels
        self._glitch_until = 0
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0, takefocus=True)
        self.canvas.pack(fill="both", expand=True)
        self.view = PixelView(self.canvas)
        png = art()

        def photo(data):
            return tk.PhotoImage(master=self.canvas, data=data)
        self.backdrop, self.cables, self.title = photo(png["backdrop"]), photo(png["cables"]), photo(png["title"])
        self.layers = [(photo(png["far"]), FAR), (photo(png["near"]), NEAR)]
        self.cores = [photo(data) for data in png["cores"]]
        self.canvas.bind("<Configure>", lambda e: self.draw(time.monotonic()))
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Key>", self.on_key)     # canvas bindings die with the screen
        self.canvas.focus_set()
        self.effects_trace = app.effects.trace_add("write", self._effects_changed)
        self._effects_changed()

    # ---------------------------------------------------------------- choices

    def change(self, row, step=1):
        """Step a row: Difficulty and players cycle, sound and motion toggle, the Seed and ENTRAR start."""
        if row == "difficulty":
            self.difficulty = (self.difficulty - 1 + step) % len(MODES) + 1
        elif row == "players":
            self.players = (self.players - 1 + step) % 4 + 1
        elif row == "sound":
            self.app.audio.toggle_mute()
        elif row == "motion":
            self.app.effects.set(not self.app.effects.get())    # its trace redraws the menu
            return
        else:
            self.start()
            return
        self.refresh()

    def start(self):
        self.app.menu_difficulty, self.app.menu_players = self.difficulty, self.players
        self.app.start(self.difficulty, self.players, parse_seed(self.seed))

    def on_key(self, event):
        """Up, Down and Tab move between rows; Left and Right change a value; Enter takes the row; F1 helps."""
        row, key = ROWS[self.focus], event.keysym
        if key == "F1":
            self._show_help()
        elif key in ("Up", "Down", "Tab", "ISO_Left_Tab"):
            back = key in ("Up", "ISO_Left_Tab") or (key == "Tab" and event.state & 1)
            self.focus = (self.focus + (-1 if back else 1)) % len(ROWS)
            self.refresh()
        elif key in ("Left", "Right"):
            if row not in ("seed", "start"):
                self.change(row, -1 if key == "Left" else 1)
        elif key in ("Return", "KP_Enter") or (key == "space" and row != "seed"):
            self.change(row)
        elif row == "seed" and key == "BackSpace":
            self.seed = self.seed[:-1]
            self.refresh()
        elif row == "seed" and event.char and event.char in SEED_CHARS and len(self.seed) < SEED_LENGTH:
            self.seed += event.char.upper()
            self.refresh()
        else:
            return None
        return "break"

    def control_at(self, event):
        native = self.view.to_native(event.x, event.y)
        for action, (x0, y0, x1, y1) in self.regions:
            if native and x0 <= native[0] <= x1 and y0 <= native[1] <= y1:
                return action
        return None

    def region_centre(self, action):
        """Canvas coordinates of a control, for clicks and tests."""
        x0, y0, x1, y1 = dict(self.regions)[action]
        return self.view.to_canvas((x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2)

    def motion(self, event):
        action = self.control_at(event)
        self.canvas.configure(cursor="" if action is None else "hand2")
        if action and action[0] == "row" and action[1] != self.focus:
            self.focus = action[1]
            self.refresh()

    def click(self, event):
        action = self.control_at(event)
        if action == ("help",):
            self._show_help()
        elif action:
            self.focus = action[1]
            if ROWS[self.focus] == "seed":
                self.refresh()                # a click only puts the cursor in the Seed
            else:
                self.change(ROWS[self.focus])

    # ---------------------------------------------------------------- drawing

    def refresh(self):
        """Rebuild the overlay: the title, the options, the Records and the footer."""
        if self._dead:
            return
        view = self.view
        view.clear_hud()
        x = (W - self.title.width() * TITLE_ZOOM) // 2
        view.hud.tk.call(view.hud, "copy", self.title, "-zoom", TITLE_ZOOM, "-to", x, 0)
        footer = caption(FOOTER, hud.MUTED, H - font.LINE - 5, x=COLUMN_AT[0])
        footer.regions.append((("help",), (footer.x, footer.y, footer.x + footer.pix.w - 1, footer.y + footer.pix.h - 1)))
        pieces = {"subtitle": caption("A MASMORRA DOS ECOS", hud.GOLD, 46),
                  "column": column(self.difficulty, self.players, self.seed, self.app.audio.muted,
                                   self.app.effects.get(), self.focus),
                  "records": records_panel(self.app.records.top(self.difficulty), self.difficulty),
                  "footer": footer}
        self._photos = [tk.PhotoImage(master=self.canvas, data=piece.pix.png()) for piece in pieces.values()]
        for piece, photo in zip(pieces.values(), self._photos):
            view.overlay(photo, piece.x, piece.y)
        self.pieces = pieces
        self.regions = [region for piece in pieces.values() for region in piece.regions]
        self.hud = {name: piece.texts for name, piece in pieces.items()}
        self.draw(time.monotonic())

    def draw(self, now):
        """Compose the scene: backdrop, towers sliding at two speeds, the core, cables, sparks and a glitch."""
        if self._dead:
            return
        t = now - self.started if self.app.effects.get() else 0
        frame = self.view.frame
        copy = frame.tk.call
        copy(frame, "copy", self.backdrop)
        for photo, speed in self.layers:
            dx = int(t * speed) % W
            copy(frame, "copy", photo, "-from", dx, 0, W, H, "-to", 0, 0)
            if dx:
                copy(frame, "copy", photo, "-from", 0, 0, dx, H, "-to", W - dx, 0)
        pulse = (math.sin(t * 2.4) + 1) / 2
        copy(frame, "copy", self.cores[round(pulse * (len(self.cores) - 1))], "-to", *menu_art.CORE_AT)
        copy(frame, "copy", self.cables)
        for x, y, *_rest, life in self.sparks:
            frame.put(hex_color(17 if life > .4 else 15), to=(int(x), int(y), int(x) + 1, int(y) + 1))
        if now < self._glitch_until:
            other = self.view.other
            copy(other, "copy", frame)
            rnd = random.Random(int(now * 15))          # the torn bands hold for a few frames
            for _ in range(4):
                y, h, shift = rnd.randrange(H - 10), rnd.randrange(2, 10), rnd.choice((-7, -3, 4, 8))
                copy(frame, "copy", other, "-from", max(0, -shift), y, W - max(0, shift), y + h, "-to", max(0, shift), y)
        self.canvas.delete("all")
        self.view.present()

    def _effects_changed(self, *_args):
        if self._dead:
            return
        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.sparks.clear()
        self._glitch_until = 0
        self.refresh()                        # the motion row shows the new state
        if self.app.effects.get():
            self._last = time.monotonic()
            self._animate()

    def _animate(self):
        self.animation_job = None
        if self._dead or not self.app.effects.get():
            return
        now = time.monotonic()
        dt, self._last = min(.1, now - self._last), now
        rnd = random.random
        sources = art()["sparks"]
        if rnd() < .2:
            x, y = random.choice(sources)
            self.sparks.append([x, y + 2, rnd() * 24 - 12, -rnd() * 20, .5 + rnd() * .5])
        for spark in self.sparks:
            spark[0] += spark[2] * dt
            spark[1] += spark[3] * dt
            spark[3] += 160 * dt
            spark[4] -= dt
        self.sparks = [s for s in self.sparks if s[4] > 0]
        if now >= self._glitch_until and rnd() < .006:
            self._glitch_until = now + .12
        self.draw(now)
        self.animation_job = self.after(33, self._animate)

    # ---------------------------------------------------------------- help

    def _show_help(self):
        if self._help is not None and self._help.winfo_exists():
            self._help.lift()
            return
        dialog = self._help = tk.Toplevel(self)
        dialog.title("Como jogar · ECOS")
        dialog.configure(bg=PANEL, padx=26, pady=24)
        dialog.transient(self.app)
        dialog.resizable(False, False)

        def label(text, size, color, **kwargs):
            return tk.Label(dialog, text=text, bg=PANEL, fg=color, font=(FONT, size), **kwargs)
        label("CADA RESPOSTA ABRE UM CAMINHO", 16, TEAL).pack(anchor="w", pady=(0, 18))
        for title, detail in (
            ("01  EXPLORE", "Um movimento por turno; seu mapa mostra só o que você descobriu.\nAlt + setas: mover. Alt + Q/E: olhar para os lados."),
            ("02  RESPONDA", "Cada guardião pergunta a todo jogador que entra. Você tem 3 vidas.\nErrar fácil: −1 vida · média: perde a vez · difícil: recua."),
            ("03  ESCAPE PRIMEIRO", "Acerte 3 perguntas do núcleo, uma por turno.\nO primeiro jogador a escapar vence a corrida."),
        ):
            label(title, 10, GOLD).pack(anchor="w")
            label(detail, 11, TEXT, justify="left").pack(anchor="w", pady=(5, 17))
        close = tk.Button(dialog, text="ENTENDI   →", command=dialog.destroy, bg=CARD, fg=TEXT,
                          activebackground="#23434b", activeforeground=TEXT, relief="flat", bd=0,
                          highlightthickness=1, highlightbackground=LINE, highlightcolor=TEAL,
                          cursor="hand2", font=(FONT, 10, "bold"), padx=12, pady=8)
        close.pack(fill="x", pady=(5, 0))
        for key in ("<Escape>", "<Return>"):
            dialog.bind(key, lambda event: dialog.destroy())
        dialog.grab_set()
        close.focus_set()

    def destroy(self):
        if self._dead:
            return
        self._dead = True
        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.app.effects.trace_remove("write", self.effects_trace)
        if self._help is not None and self._help.winfo_exists():
            self._help.destroy()
        super().destroy()
