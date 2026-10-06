"""Python Trivia Adventure - graphical launcher and legacy board.

A Tkinter front-end over the rules in core.py: the procedural board is drawn as
a winding path of tiles, players are pawns that walk it, and every prompt the
terminal version asks for (answers, fork paths, targets) becomes a widget.

Run the dungeon with python gui.py; use python gui.py --board for this board.
"""

import math
import tkinter as tk
from typing import Dict, List, Optional, Tuple

from core import Board, DifficultyHandler, Game, GameConfig, Player


# =========================
# Look and feel
# =========================

BG = "#141a22"           # window background
PANEL = "#1b232e"        # sidebar / cards
PANEL_EDGE = "#2b3644"
BOARD_BG = "#101720"
PATH = "#232e3c"
INK = "#e8eef6"          # primary text
INK_DIM = "#8b9bb0"      # secondary text
ACCENT = "#f2c14e"
GOOD = "#6ddba0"
BAD = "#ef6f6c"

TILE_COLORS = {
    "normal":     ("#2a3646", "#8ea2ba"),
    "bonus":      ("#1f7a4d", "#dffbe9"),
    "trap":       ("#8f2f3f", "#ffe0e3"),
    "mystery":    ("#5f3b96", "#ecdcff"),
    "quiz_boost": ("#1f6f8f", "#d8f4ff"),
    "swap":       ("#2f6f9f", "#dcefff"),
    "push_down":  ("#a05a2c", "#ffe6d0"),
    "lift_up":    ("#3f8f5f", "#e0ffe9"),
    "teleport":   ("#7a3f9f", "#f2e0ff"),
    "skip":       ("#4d5766", "#dfe6ef"),
    "double":     ("#a08a2c", "#fff6d6"),
    "steal":      ("#9f3f6f", "#ffdcee"),
    "fork":       ("#c2802a", "#fff1d8"),
}

PLAYER_COLORS = ["#f2c14e", "#6fc3df", "#ef6f6c", "#8ce99a"]

UI_FONT = "Segoe UI"
GLYPH_FONT = "Segoe UI Symbol"


def rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kwargs):
    """A rounded rectangle - the Tk canvas has no such primitive."""
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# =========================
# The board canvas
# =========================

class BoardView(tk.Canvas):
    """Draws the procedural path and animates the pawns along it."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=BOARD_BG, highlightthickness=0, **kwargs)
        self.game: Optional[Game] = None
        self.centers: List[Tuple[float, float]] = []
        self.cell = 40.0
        self.tokens: Dict[int, Tuple[int, int]] = {}   # player id -> (oval, label)
        self.on_tile_hover = lambda text: None
        self._redraw_job = None
        self._animating = False
        self.bind("<Configure>", self._on_resize)

    # ---- setup -------------------------------------------------------

    def set_game(self, game: Game) -> None:
        self.game = game
        self.redraw()

    def _on_resize(self, _event=None):
        if self._redraw_job:
            self.after_cancel(self._redraw_job)
        self._redraw_job = self.after(60, self.redraw)

    # ---- geometry ----------------------------------------------------

    def _layout(self) -> None:
        """Snake the tiles across the canvas, with a gentle wave so the path
        looks hand-drawn instead of like a spreadsheet."""
        size = self.game.board.size
        w = max(self.winfo_width(), 420)
        h = max(self.winfo_height(), 320)
        pad = 34

        best_cols, best_cell = 8, 0.0
        for cols in range(6, 22):
            rows = math.ceil(size / cols)
            cell = min((w - 2 * pad) / cols, (h - 2 * pad) / rows)
            if cell > best_cell:
                best_cols, best_cell = cols, cell

        cols = best_cols
        rows = math.ceil(size / cols)
        self.cell = min(best_cell, 86)

        ox = (w - self.cell * cols) / 2 + self.cell / 2
        oy = (h - self.cell * rows) / 2 + self.cell / 2

        self.centers = []
        for i in range(size):
            row, col = divmod(i, cols)
            if row % 2:                      # serpentine: odd rows run backwards
                col = cols - 1 - col
            x = ox + col * self.cell
            y = oy + row * self.cell + math.sin(i * 0.8) * self.cell * 0.09
            self.centers.append((x, y))

    def _crowd(self, player: Player) -> List[Player]:
        """Everyone sharing a tile with this player, so pawns can make room."""
        last = len(self.centers) - 1
        idx = min(max(player.position, 0), last)
        return [p for p in self.game.players
                if min(max(p.position, 0), last) == idx]

    def _token_radius(self, player: Player) -> float:
        return self.cell * (0.19 if len(self._crowd(player)) <= 2 else 0.15)

    def _token_xy(self, player: Player) -> Tuple[float, float]:
        last = len(self.centers) - 1
        idx = min(max(player.position, 0), last)
        x, y = self.centers[idx]
        sharing = self._crowd(player)
        if len(sharing) > 1:
            slot = sharing.index(player)
            angle = -math.pi / 2 + slot * (2 * math.pi / len(sharing))
            r = self.cell * 0.21
            x += math.cos(angle) * r
            y += math.sin(angle) * r
        return x, y

    def token_snapshot(self) -> Dict[int, Tuple[float, float]]:
        if self.game is None or not self.centers:
            return {}
        return {p.id: self._token_xy(p) for p in self.game.players}

    # ---- painting ----------------------------------------------------

    def redraw(self) -> None:
        self._redraw_job = None
        if self.game is None or self._animating:
            return
        self.delete("all")
        self._layout()
        self._draw_path()
        self._draw_tiles()
        self._draw_tokens()
        if self.game.winner:
            self._draw_banner("Player {} wins!".format(self.game.winner.id))

    def _draw_path(self) -> None:
        flat = [c for xy in self.centers for c in xy]
        if len(flat) >= 4:
            self.create_line(*flat, fill=PATH, width=self.cell * 0.62,
                             capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)

    def _draw_tiles(self) -> None:
        board = self.game.board
        r = self.cell * 0.40
        glyph_size = max(8, int(self.cell * 0.29))
        num_size = max(6, int(self.cell * 0.155))
        current_pos = self.game.current_player.position
        last = len(self.centers) - 1

        for i, (x, y) in enumerate(self.centers):
            fill, ink = TILE_COLORS[board.kind_at(i)]
            outline, width = PANEL_EDGE, 1
            if i in (0, last):                       # the two tiles that matter most
                outline, width = "#e8eef6" if i == 0 else ACCENT, 2
            if i == current_pos and not self.game.winner:
                outline, width = ACCENT, 3

            tag = "tile{}".format(i)
            rounded_rect(self, x - r, y - r, x + r, y + r, r * 0.4,
                         fill=fill, outline=outline, width=width, tags=tag)
            self.create_text(x, y - r * 0.18, text=board.symbol_at(i), fill=ink,
                             font=(GLYPH_FONT, glyph_size, "bold"), tags=tag)

            # Footer line inside the tile: its index, or START / GOAL at the ends.
            footer = {0: "START", last: "GOAL"}.get(i, str(i) if self.cell > 30 else "")
            if footer:
                end_tile = i in (0, last)
                self.create_text(
                    x, y + r * 0.58, text=footer,
                    fill=ACCENT if end_tile else ink,
                    font=(UI_FONT, max(6, int(num_size * (0.85 if end_tile else 1))),
                          "bold" if end_tile else "normal"),
                    tags=tag)

            label = "Tile {} - {}".format(i, board.name_at(i))
            self.tag_bind(tag, "<Enter>", lambda _e, t=label: self.on_tile_hover(t))
            self.tag_bind(tag, "<Leave>", lambda _e: self.on_tile_hover(""))

    def _draw_tokens(self) -> None:
        self.tokens = {}
        for player in self.game.players:
            r = self._token_radius(player)
            x, y = self._token_xy(player)
            color = PLAYER_COLORS[(player.id - 1) % len(PLAYER_COLORS)]
            oval = self.create_oval(x - r, y - r, x + r, y + r,
                                    fill=color, outline=BOARD_BG, width=2)
            text = self.create_text(x, y, text="P{}".format(player.id), fill="#101720",
                                    font=(UI_FONT, max(6, int(r * 0.9)), "bold"))
            self.tokens[player.id] = (oval, text)

    def _draw_banner(self, message: str) -> None:
        w, h = self.winfo_width(), self.winfo_height()
        rounded_rect(self, w / 2 - 200, h / 2 - 46, w / 2 + 200, h / 2 + 46, 18,
                     fill=PANEL, outline=ACCENT, width=2)
        self.create_text(w / 2, h / 2, text=message, fill=ACCENT, font=(UI_FONT, 22, "bold"))

    # ---- animation ---------------------------------------------------

    def animate_to(self, start_xy: Dict[int, Tuple[float, float]], done=None) -> None:
        """Glide every pawn from where it was to where it now belongs."""
        if self.game is None or not self.tokens:
            if done:
                done()
            return

        targets = {p.id: self._token_xy(p) for p in self.game.players}
        frames = 14
        self._animating = True

        def step(frame: int):
            t = frame / frames
            ease = t * t * (3 - 2 * t)          # smoothstep
            for pid, (oval, text) in self.tokens.items():
                sx, sy = start_xy.get(pid, targets[pid])
                tx, ty = targets[pid]
                x, y = sx + (tx - sx) * ease, sy + (ty - sy) * ease
                cx, cy = self._center_of(oval)
                self.move(oval, x - cx, y - cy)
                self.move(text, x - cx, y - cy)
            if frame < frames:
                self.after(18, step, frame + 1)
            else:
                self._animating = False
                self.redraw()
                if done:
                    done()

        step(1)

    def _center_of(self, item: int) -> Tuple[float, float]:
        x1, y1, x2, y2 = self.coords(item)
        return (x1 + x2) / 2, (y1 + y2) / 2


# =========================
# Dice widget
# =========================

class DiceView(tk.Canvas):
    """A six-sided die drawn with pips, with a little tumble animation."""

    PIPS = {
        1: [(0.5, 0.5)],
        2: [(0.28, 0.28), (0.72, 0.72)],
        3: [(0.26, 0.26), (0.5, 0.5), (0.74, 0.74)],
        4: [(0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)],
        5: [(0.27, 0.27), (0.73, 0.27), (0.5, 0.5), (0.27, 0.73), (0.73, 0.73)],
        6: [(0.28, 0.24), (0.72, 0.24), (0.28, 0.5), (0.72, 0.5), (0.28, 0.76), (0.72, 0.76)],
    }

    def __init__(self, master, size=84):
        super().__init__(master, width=size, height=size, bg=PANEL, highlightthickness=0)
        self.size = size
        self.show(None)

    def show(self, value: Optional[int]) -> None:
        self.delete("all")
        s, pad = self.size, 8
        rounded_rect(self, pad, pad, s - pad, s - pad, 14,
                     fill="#f4f6fa", outline="#c8d0dc", width=2)
        if value is None:
            self.create_text(s / 2, s / 2, text="?", fill="#8ea2ba",
                             font=(UI_FONT, int(s * 0.34), "bold"))
            return
        r = s * 0.055
        for fx, fy in self.PIPS[value]:
            x = pad + (s - 2 * pad) * fx
            y = pad + (s - 2 * pad) * fy
            self.create_oval(x - r, y - r, x + r, y + r, fill="#1b232e", outline="")

    def roll_to(self, value: int, done=None, frames: int = 9) -> None:
        import random as _random

        def step(n: int):
            if n >= frames:
                self.show(value)
                if done:
                    done()
                return
            self.show(_random.randint(1, 6))
            self.after(55, step, n + 1)

        step(0)


# =========================
# Small styled widgets
# =========================

def make_button(master, text, command, primary=False, **kwargs):
    fg = "#101720" if primary else INK
    bg = ACCENT if primary else "#2a3646"
    active = "#ffd677" if primary else "#36445a"
    btn = tk.Button(master, text=text, command=command, fg=fg, bg=bg,
                    activeforeground=fg, activebackground=active,
                    font=(UI_FONT, 10, "bold"), relief="flat", bd=0,
                    padx=14, pady=8, cursor="hand2",
                    disabledforeground="#5d6b7d", **kwargs)
    return btn


def set_enabled(button: tk.Button, enabled: bool, primary: bool = False) -> None:
    """Tk keeps a disabled flat button fully coloured, so dim it by hand."""
    button.configure(state="normal" if enabled else "disabled")
    if primary:
        button.configure(bg=ACCENT if enabled else "#2a3646",
                         activebackground="#ffd677" if enabled else "#2a3646",
                         fg="#101720" if enabled else "#5d6b7d")


def card(master, **kwargs):
    return tk.Frame(master, bg=PANEL, highlightbackground=PANEL_EDGE,
                    highlightthickness=1, **kwargs)


# =========================
# Modal choices (fork / target)
# =========================

class ModalChoice(tk.Toplevel):
    """Blocking little dialog used by the rule callbacks."""

    def __init__(self, master, title: str, subtitle: str):
        super().__init__(master, bg=PANEL)
        self.result = None
        self.title(title)
        self.configure(padx=22, pady=18)
        self.resizable(False, False)
        self.transient(master)
        tk.Label(self, text=title, bg=PANEL, fg=ACCENT,
                 font=(UI_FONT, 14, "bold")).pack(anchor="w")
        tk.Label(self, text=subtitle, bg=PANEL, fg=INK_DIM, justify="left",
                 font=(UI_FONT, 10)).pack(anchor="w", pady=(2, 12))
        self.body = tk.Frame(self, bg=PANEL)
        self.body.pack(fill="both", expand=True)

    def choose(self, value):
        self.result = value
        self.destroy()

    def run(self):
        self.update_idletasks()
        master = self.master
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 3
        self.geometry("+{}+{}".format(max(x, 0), max(y, 0)))
        self.protocol("WM_DELETE_WINDOW", lambda: None)   # a choice must be made
        self.grab_set()
        self.wait_window()
        return self.result


def ask_fork(master, branch_a: List[str], branch_b: List[str]) -> str:
    dialog = ModalChoice(master, "Fork in the road",
                         "Two paths open up. One is kinder than the other.")

    def path_row(letter: str, flavour: str, tiles: List[str], color: str):
        frame = tk.Frame(dialog.body, bg=PANEL)
        frame.pack(fill="x", pady=6)
        tk.Label(frame, text="Path {} - {} ({} tiles)".format(letter, flavour, len(tiles)),
                 bg=PANEL, fg=color, font=(UI_FONT, 11, "bold")).pack(anchor="w")
        strip = tk.Frame(frame, bg=PANEL)
        strip.pack(anchor="w", pady=4)
        for kind in tiles:
            fill, ink = TILE_COLORS[kind]
            tk.Label(strip, text=Board.TILE_SYMBOLS[kind], bg=fill, fg=ink, width=3,
                     font=(GLYPH_FONT, 12, "bold")).pack(side="left", padx=2, ipady=4)
        make_button(frame, "Take Path {}".format(letter),
                    lambda: dialog.choose(letter.lower()),
                    primary=(letter == "A")).pack(anchor="w", pady=(4, 0))

    path_row("A", "safer", branch_a, GOOD)
    path_row("B", "riskier", branch_b, BAD)
    return dialog.run() or "a"


def ask_target(master, player: Player, candidates: List[Player]) -> Optional[Player]:
    if not candidates:
        return None
    dialog = ModalChoice(master, "Choose a target",
                         "Player {}, pick who this tile hits.".format(player.id))
    for candidate in candidates:
        color = PLAYER_COLORS[(candidate.id - 1) % len(PLAYER_COLORS)]
        row = tk.Frame(dialog.body, bg=PANEL)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="  ", bg=color).pack(side="left", padx=(0, 8), ipady=6)
        tk.Label(row, text="Player {} - tile {}".format(candidate.id, candidate.position),
                 bg=PANEL, fg=INK, font=(UI_FONT, 11)).pack(side="left")
        make_button(row, "Target", lambda c=candidate: dialog.choose(c)).pack(side="right")
    return dialog.run()


# =========================
# Setup screen
# =========================

class SetupScreen(tk.Frame):
    def __init__(self, master, on_start):
        super().__init__(master, bg=BG)
        self.on_start = on_start
        self.players = tk.IntVar(value=2)
        self.difficulty = tk.IntVar(value=1)

        wrap = tk.Frame(self, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrap, text="Python Trivia Adventure", bg=BG, fg=INK,
                 font=(UI_FONT, 30, "bold")).pack()
        tk.Label(wrap, text="Roll, answer, and survive a board that plays dirty.",
                 bg=BG, fg=INK_DIM, font=(UI_FONT, 12)).pack(pady=(4, 26))

        players_card = card(wrap)
        players_card.pack(fill="x", pady=(0, 14), ipady=12, ipadx=16)
        tk.Label(players_card, text="PLAYERS", bg=PANEL, fg=INK_DIM,
                 font=(UI_FONT, 9, "bold")).pack(anchor="w", padx=16, pady=(10, 6))
        row = tk.Frame(players_card, bg=PANEL)
        row.pack(padx=16, anchor="w")
        self.player_buttons = []
        for n in range(GameConfig.MIN_PLAYERS, GameConfig.MAX_PLAYERS + 1):
            btn = tk.Button(row, text=str(n), width=4, relief="flat", bd=0, cursor="hand2",
                            font=(UI_FONT, 13, "bold"), padx=6, pady=6,
                            command=lambda v=n: self._set_players(v))
            btn.pack(side="left", padx=4)
            self.player_buttons.append((n, btn))

        diff_card = card(wrap)
        diff_card.pack(fill="x", pady=(0, 20), ipady=12)
        tk.Label(diff_card, text="DIFFICULTY", bg=PANEL, fg=INK_DIM,
                 font=(UI_FONT, 9, "bold")).pack(anchor="w", padx=16, pady=(10, 6))
        grid = tk.Frame(diff_card, bg=PANEL)
        grid.pack(padx=16, anchor="w")
        blurbs = {
            1: "36 tiles - friendly board",
            2: "46 tiles - balanced board",
            3: "56 tiles - punishing board",
            4: "123 tiles - forks, all powers",
        }
        self.diff_buttons = []
        for i, (level, name) in enumerate(sorted(GameConfig.DIFFICULTY_NAMES.items())):
            btn = tk.Button(grid, text="{}\n{}".format(name, blurbs[level]), width=30,
                            justify="left", anchor="w", relief="flat", bd=0, cursor="hand2",
                            font=(UI_FONT, 10), padx=12, pady=10,
                            command=lambda v=level: self._set_difficulty(v))
            btn.grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="ew")
            self.diff_buttons.append((level, btn))

        make_button(wrap, "Start game", self._start, primary=True).pack(fill="x", ipady=4)

        self._set_players(2)
        self._set_difficulty(1)

    def _paint(self, buttons, selected):
        for value, btn in buttons:
            on = value == selected
            btn.configure(bg=ACCENT if on else "#2a3646",
                          fg="#101720" if on else INK,
                          activebackground="#ffd677" if on else "#36445a",
                          activeforeground="#101720" if on else INK)

    def _set_players(self, value):
        self.players.set(value)
        self._paint(self.player_buttons, value)

    def _set_difficulty(self, value):
        self.difficulty.set(value)
        self._paint(self.diff_buttons, value)

    def _start(self):
        self.on_start(self.players.get(), self.difficulty.get())


# =========================
# Game screen
# =========================

class GameScreen(tk.Frame):
    def __init__(self, master, game: Game, on_new_game):
        super().__init__(master, bg=BG)
        self.game = game
        self.on_new_game = on_new_game
        self.question: Optional[Dict[str, str]] = None
        self.roll_value = 0
        self.busy = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        board_wrap = tk.Frame(self, bg=BG)
        board_wrap.grid(row=0, column=0, sticky="nsew", padx=(14, 7), pady=14)
        board_wrap.rowconfigure(0, weight=1)
        board_wrap.columnconfigure(0, weight=1)

        self.board_view = BoardView(board_wrap)
        self.board_view.grid(row=0, column=0, sticky="nsew")
        self.board_view.on_tile_hover = self._on_tile_hover
        self.board_view.set_game(game)

        self.hover_label = tk.Label(board_wrap, text=self._legend_text(), bg=BG, fg=INK_DIM,
                                    font=(UI_FONT, 9), anchor="w", justify="left",
                                    wraplength=600)
        self.hover_label.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        board_wrap.bind("<Configure>",
                        lambda e: self.hover_label.configure(wraplength=max(e.width - 8, 200)))

        self._build_sidebar()
        self.after(120, self.start_turn)

    # ---- sidebar -----------------------------------------------------

    def _build_sidebar(self):
        side = tk.Frame(self, bg=BG, width=330)
        side.grid(row=0, column=1, sticky="ns", padx=(7, 14), pady=14)
        side.grid_propagate(False)

        header = tk.Frame(side, bg=BG)
        header.pack(fill="x")
        tk.Label(header, text="Python Trivia Adventure", bg=BG, fg=INK,
                 font=(UI_FONT, 13, "bold")).pack(anchor="w")
        self.mode_label = tk.Label(
            header, bg=BG, fg=INK_DIM, font=(UI_FONT, 9),
            text="{} mode - first to tile {}".format(
                GameConfig.DIFFICULTY_NAMES[self.game.difficulty], self.game.win_position))
        self.mode_label.pack(anchor="w", pady=(0, 10))

        # players
        players_card = card(side)
        players_card.pack(fill="x", pady=(0, 10))
        self.player_rows = {}
        for player in self.game.players:
            color = PLAYER_COLORS[(player.id - 1) % len(PLAYER_COLORS)]
            row = tk.Frame(players_card, bg=PANEL)
            row.pack(fill="x", padx=10, pady=5)
            dot = tk.Label(row, text="  ", bg=color)
            dot.pack(side="left", padx=(0, 8), ipady=6)
            name = tk.Label(row, text="Player {}".format(player.id), bg=PANEL, fg=INK,
                            font=(UI_FONT, 10, "bold"))
            name.pack(side="left")
            info = tk.Label(row, text="", bg=PANEL, fg=INK_DIM, font=(UI_FONT, 9))
            info.pack(side="right")
            bar = tk.Canvas(players_card, height=5, bg="#232e3c", highlightthickness=0)
            bar.pack(fill="x", padx=10, pady=(0, 6))
            self.player_rows[player.id] = (row, name, info, bar, color)

        # turn / dice
        turn_card = card(side)
        turn_card.pack(fill="x", pady=(0, 10))
        self.turn_label = tk.Label(turn_card, text="", bg=PANEL, fg=ACCENT,
                                   font=(UI_FONT, 12, "bold"))
        self.turn_label.pack(anchor="w", padx=12, pady=(10, 0))
        dice_row = tk.Frame(turn_card, bg=PANEL)
        dice_row.pack(fill="x", padx=12, pady=10)
        self.dice = DiceView(dice_row)
        self.dice.pack(side="left")
        actions = tk.Frame(dice_row, bg=PANEL)
        actions.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self.roll_button = make_button(actions, "Roll dice", self.on_roll, primary=True)
        self.roll_button.pack(fill="x")
        self.tile_label = tk.Label(actions, text="", bg=PANEL, fg=INK_DIM, wraplength=170,
                                   justify="left", font=(UI_FONT, 9))
        self.tile_label.pack(anchor="w", pady=(8, 0))

        # question
        q_card = card(side)
        q_card.pack(fill="x", pady=(0, 10))
        self.q_tier = tk.Label(q_card, text="QUESTION", bg=PANEL, fg=INK_DIM,
                               font=(UI_FONT, 9, "bold"))
        self.q_tier.pack(anchor="w", padx=12, pady=(10, 4))
        self.q_label = tk.Label(q_card, text="Roll the dice to draw a question.", bg=PANEL,
                                fg=INK, wraplength=280, justify="left", font=(UI_FONT, 11))
        self.q_label.pack(anchor="w", padx=12)
        self.answer_var = tk.StringVar()
        self.answer_entry = tk.Entry(q_card, textvariable=self.answer_var, bg="#111823",
                                     fg=INK, insertbackground=INK, relief="flat",
                                     disabledbackground="#161d27",
                                     font=(UI_FONT, 11), state="disabled")
        self.answer_entry.pack(fill="x", padx=12, pady=(10, 0), ipady=6)
        self.answer_entry.bind("<Return>", lambda _e: self.on_submit())
        self.submit_button = make_button(q_card, "Submit answer", self.on_submit)
        self.submit_button.pack(fill="x", padx=12, pady=10)
        self.submit_button.configure(state="disabled")

        # log
        log_card = card(side)
        log_card.pack(fill="both", expand=True, pady=(0, 10))
        self.log = tk.Text(log_card, bg=PANEL, fg=INK_DIM, relief="flat", height=8,
                           wrap="word", font=(UI_FONT, 9), state="disabled",
                           padx=10, pady=8, highlightthickness=0)
        self.log.pack(fill="both", expand=True)
        self.log.tag_configure("good", foreground=GOOD)
        self.log.tag_configure("bad", foreground=BAD)
        self.log.tag_configure("turn", foreground=ACCENT)

        make_button(side, "New game", self.on_new_game).pack(fill="x")

        if self.game.difficulty_handler.using_fallback():
            self.write_log("Some question files were missing - using built-in questions.")
        self.refresh_players()

    def _legend_text(self) -> str:
        order = ["normal", "bonus", "trap", "mystery", "quiz_boost", "swap",
                 "push_down", "lift_up", "teleport", "skip", "double", "steal", "fork"]
        # Non-breaking space keeps a symbol glued to its name when the line wraps.
        return "   ".join("{} {}".format(Board.TILE_SYMBOLS[k], Board.TILE_NAMES[k])
                          for k in order)

    def _on_tile_hover(self, text: str):
        self.hover_label.configure(text=text or self._legend_text(),
                                   fg=INK if text else INK_DIM)

    # ---- turn flow ---------------------------------------------------

    def start_turn(self):
        if self.game.winner:
            return
        player = self.game.current_player
        color = PLAYER_COLORS[(player.id - 1) % len(PLAYER_COLORS)]
        self.turn_label.configure(text="Player {}'s turn".format(player.id), fg=color)
        self.refresh_players()
        self.board_view.redraw()

        if self.game.consume_skip():
            self.write_log("Player {} skips this turn.".format(player.id), "bad")
            self.set_question_ui("Skipping a turn...", "")
            self.after(1100, self.next_turn)
            return

        self.dice.show(None)
        self.tile_label.configure(
            text="Standing on: {}".format(self.game.board.name_at(player.position)))
        self.set_question_ui("Roll the dice to draw a question.", "QUESTION")
        set_enabled(self.roll_button, True, primary=True)
        self.roll_button.focus_set()

    def on_roll(self):
        if self.busy or self.game.winner:
            return
        self.busy = True
        set_enabled(self.roll_button, False, primary=True)
        self.roll_value = self.game.roll_dice()
        self.dice.roll_to(self.roll_value, done=self.show_question)

    def show_question(self):
        player = self.game.current_player
        self.question = self.game.pick_question()
        tier = self.game.difficulty_handler.tier_name(player.position)
        self.write_log("Player {} rolled {}.".format(player.id, self.roll_value), "turn")
        self.set_question_ui(self.question["question"], "QUESTION - {}".format(tier.upper()))
        self.answer_var.set("")
        self.answer_entry.configure(state="normal")
        self.submit_button.configure(state="normal")
        self.answer_entry.focus_set()
        self.busy = False

    def set_question_ui(self, text: str, tier: str):
        self.q_label.configure(text=text)
        self.q_tier.configure(text=tier)
        self.answer_entry.configure(state="disabled")
        self.submit_button.configure(state="disabled")

    def on_submit(self):
        if self.question is None or self.busy or self.game.winner:
            return
        self.busy = True
        answer = self.answer_var.get()
        correct = DifficultyHandler.is_correct(self.question, answer)
        self.set_question_ui(self.q_label.cget("text"), self.q_tier.cget("text"))

        if correct:
            self.write_log("Correct: {}".format(self.question["answer"]), "good")
        else:
            self.write_log("Wrong - the answer was {}.".format(self.question["answer"]), "bad")

        before = self.board_view.token_snapshot()
        messages = self.game.resolve_turn(
            correct, self.roll_value,
            choose_target=lambda player, candidates: ask_target(self.winfo_toplevel(),
                                                                player, candidates),
            choose_fork=lambda a, b: ask_fork(self.winfo_toplevel(), a, b),
        )
        for message in messages:
            self.write_log(message)

        self.question = None
        self.refresh_players()
        self.board_view.animate_to(before, done=self.after_move)

    def after_move(self):
        self.refresh_players()
        if self.game.winner:
            self.finish()
            return
        self.busy = False
        self.after(700, self.next_turn)

    def next_turn(self):
        self.busy = False
        self.game.next_turn()
        self.start_turn()

    def finish(self):
        winner = self.game.winner
        self.turn_label.configure(text="Player {} wins!".format(winner.id), fg=ACCENT)
        self.set_question_ui("Game over. Player {} reached tile {}.".format(
            winner.id, winner.position), "RESULT")
        set_enabled(self.roll_button, False, primary=True)
        self.board_view.redraw()

    # ---- sidebar refresh ---------------------------------------------

    def refresh_players(self):
        current = self.game.current_player
        for player in self.game.players:
            row, name, info, bar, color = self.player_rows[player.id]
            active = player is current and not self.game.winner
            name.configure(fg=color if active else INK_DIM,
                           font=(UI_FONT, 10, "bold" if active else "normal"))
            status = "tile {}/{}".format(min(player.position, self.game.win_position),
                                         self.game.win_position)
            if player.skip_next:
                status += "  (skips next)"
            info.configure(text=status)

            bar.delete("all")
            width = max(bar.winfo_width(), 1)
            pct = min(player.position / self.game.win_position, 1.0)
            bar.create_rectangle(0, 0, width * pct, 6, fill=color, outline="")

    def write_log(self, message: str, tag: str = ""):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")


# =========================
# Application shell
# =========================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Trivia Adventure")
        self.configure(bg=BG)
        self.geometry("1180x760")
        self.minsize(940, 620)
        self.screen: Optional[tk.Frame] = None
        self.show_setup()

    def _swap(self, frame: tk.Frame):
        if self.screen is not None:
            self.screen.destroy()
        self.screen = frame
        frame.pack(fill="both", expand=True)

    def show_setup(self):
        self._swap(SetupScreen(self, self.start_game))

    def start_game(self, num_players: int, difficulty: int):
        game = Game(num_players, difficulty)
        self._swap(GameScreen(self, game, self.show_setup))


def main():
    import sys
    if "--board" in sys.argv:
        App().mainloop()
    else:
        from dungeon_ui import main as dungeon_main
        dungeon_main()


if __name__ == "__main__":
    main()
