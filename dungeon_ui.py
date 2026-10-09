"""Animated, dependency-free Tkinter dungeon crawler."""

import math
import random
import time
import tkinter as tk

from dungeon import Dungeon, ROOMS
from menu_ui import Setup
from room_scene import RoomScene, DOOR_BOUNDS
from motion import CanvasVeil, smooth, blend

BG = "#080e12"
PANEL = "#111e25"
TEXT = "#edf1f8"
MUTED = "#94a4bd"
GOLD = "#f3c66b"
TEAL = "#24e5dd"
RED = "#f57888"
FONT = "Segoe UI"
PLAYER_COLORS = ("#48e5dd", "#f6c777", "#c4a0ff", "#90dfab")

# Initial portal layout; relative_portals follows the player's current facing.
PORTALS = (("O", "OESTE", (-1, 0)), ("N", "NORTE", (0, -1)),
           ("L", "LESTE", (1, 0)), ("S", "SUL", (0, 1)))
COMPASS = (("N", "NORTE", (0, -1)), ("L", "LESTE", (1, 0)),
           ("S", "SUL", (0, 1)), ("O", "OESTE", (-1, 0)))
SYMBOLS = {"entrance": "E", "combat": "?", "treasure": "+", "elite": "!",
           "sanctuary": "V", "clock": "T", "boss": "X"}


def label(parent, text="", size=11, color=TEXT, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                    font=(FONT, size), **kwargs)


def button(parent, text, command, primary=False):
    return tk.Button(parent, text=text, command=command, font=(FONT, 11, "bold"),
                     bg=GOLD if primary else "#24334b", fg=BG if primary else TEXT,
                     activebackground=TEAL, activeforeground=BG,
                     disabledforeground="#65748a", relief="flat", bd=0,
                     padx=14, pady=9, cursor="hand2", takefocus=True)


class DungeonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Trivia • A Masmorra dos Ecos")
        self.geometry("1240x850")
        self.minsize(1000, 760)
        self.configure(bg=BG)
        self.screen = None
        self.effects = tk.BooleanVar(value=True)
        self.show_setup()

    def swap(self, screen):
        if self.screen:
            self.screen.destroy()
        self.screen = screen
        screen.pack(fill="both", expand=True)

    def show_setup(self):
        self.swap(Setup(self))

    def start(self, difficulty, players):
        self.swap(ExpeditionScreen(self, Dungeon(difficulty, players)))



class ExpeditionScreen(tk.Frame):
    def __init__(self, app, game):
        super().__init__(app, bg=BG)
        self.app, self.game = app, game
        self.job = None
        self.resume_at = 0
        self.particles = []
        self.popups = []
        self.display_score = 0
        self.last_frame = time.monotonic()
        self.hover = None
        self.finished = False
        self.facing = 0
        self.transition = None
        self._shown_question = None
        self.arrival_at = None
        self._player_state = None
        self._active_player = None
        self.turn_changed_at = 0
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=22, pady=(16, 12))
        label(header, "ECOS / EXPEDIÇÃO", 17, TEAL).pack(side="left")
        self.player_badge = tk.Canvas(header, width=232, height=46, bg=BG, highlightthickness=0)
        self.player_badge.pack(side="left", padx=(24, 8))
        self.stats = label(header, "", 13)
        self.stats.pack(side="right")

        main = tk.Frame(self, bg=BG)
        main.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 18))
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        room_header = tk.Frame(main, bg=BG)
        room_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.room_title = label(room_header, "", 11, TEAL, anchor="w")
        self.room_title.pack(side="left", fill="x", expand=True)
        self.look_buttons = []
        for turn, text in ((-1, "↶ OLHAR"), (1, "OLHAR ↷")):
            btn = button(room_header, text, lambda d=turn: self.look(d))
            btn.configure(font=(FONT, 9, "bold"), padx=8, pady=5)
            btn.pack(side="left", padx=(4, 0))
            self.look_buttons.append(btn)
        self.scene = tk.Canvas(main, bg=BG, height=320, highlightthickness=1,
                               highlightbackground="#28364c")
        self.scene.grid(row=1, column=0, sticky="nsew")
        self.scene.bind("<Motion>", self.motion)
        self.scene.bind("<Leave>", lambda e: setattr(self, "hover", None))
        self.scene.bind("<Button-1>", self.scene_click)
        self.renderer = RoomScene(self.scene)
        self.veil = CanvasVeil(self.scene)

        doors = tk.Frame(main, bg=BG)
        doors.grid(row=2, column=0, sticky="ew", pady=8)
        self.door_buttons = []
        for i, (_, name, _) in enumerate(PORTALS):
            doors.columnconfigure(i, weight=1, uniform="door")
            btn = button(doors, name, lambda d=i: self.navigate(d))
            btn.configure(font=(FONT, 10, "bold"), padx=3)
            btn.grid(row=0, column=i, sticky="ew", padx=3)
            self.door_buttons.append(btn)

        challenge = self.challenge = tk.Frame(main, bg=PANEL, padx=16, pady=12,
                                              highlightthickness=1, highlightbackground=TEAL)
        challenge.grid(row=3, column=0, sticky="ew")
        self.q_meta = label(challenge, "", 10, TEAL, anchor="w")
        self.q_meta.pack(fill="x")
        self.q_text = label(challenge, "", 20, justify="left", anchor="w", wraplength=640)
        self.q_text.pack(fill="x", pady=(7, 8))
        challenge.bind("<Configure>", lambda e: self.q_text.configure(wraplength=max(250, e.width - 34)))
        answer_row = tk.Frame(challenge, bg=PANEL)
        answer_row.pack(fill="x")
        self.answer = tk.Entry(answer_row, bg="#0b1321", fg=TEXT, insertbackground=TEXT,
                               relief="flat", font=(FONT, 13), disabledbackground="#182237",
                               highlightthickness=1, highlightbackground="#294048", highlightcolor=TEAL)
        self.answer.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        self.answer.bind("<Return>", lambda e: self.submit())
        self.submit_btn = button(answer_row, "RESPONDER ↵", self.submit, True)
        self.submit_btn.pack(side="right")
        self.q_bar = tk.Canvas(challenge, height=4, bg="#263047", highlightthickness=0)
        self.q_bar.pack(fill="x", pady=(10, 0))
        self.feedback = label(main, "A entrada está segura. Escolha sua primeira porta.",
                              11, GOLD, anchor="w", justify="left", wraplength=680)
        self.feedback.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        main.bind("<Configure>", lambda e: self.feedback.configure(wraplength=max(250, e.width - 10)))

        side = tk.Frame(self, bg=PANEL, width=306, padx=16, pady=14)
        side.grid(row=1, column=1, sticky="ns", padx=(0, 20), pady=(0, 18))
        side.pack_propagate(False)
        label(side, "TEMPO DA EXPEDIÇÃO", 10, MUTED).pack(anchor="w")
        self.clock_label = label(side, "", 28, GOLD)
        self.clock_label.pack(anchor="w")
        label(side, "O tempo corre também entre as portas.", 9, MUTED).pack(anchor="w")
        self.score_label = label(side, "0", 26)
        self.score_label.pack(anchor="w", pady=(8, 0))
        self.combo_label = label(side, "PONTOS  /  COMBO ×1,00", 10, TEAL)
        self.combo_label.pack(anchor="w")
        self.map_title = label(side, "PLANTA / ÁREA EXPLORADA", 10, TEAL)
        self.map_title.pack(anchor="w", pady=(10, 4))
        self.map = tk.Canvas(side, width=258, height=220, bg="#0e1726", highlightthickness=0)
        self.map.pack(fill="x")
        self.map.bind("<Button-1>", self.map_click)
        self.map_positions = {}
        label(side, "Ciano: você · cheia: concluída · X: núcleo\nAlt + setas: mover · Alt + Q/E: olhar",
              9, MUTED, justify="left").pack(anchor="w", pady=6)
        self.roster = tk.Frame(side, bg=PANEL)
        self.roster.pack(fill="x", pady=(4, 6))
        self.player_cards = []
        for i in range(len(game.scores)):
            self.roster.columnconfigure(i % 2, weight=1, uniform="player")
            card = tk.Frame(self.roster, bg=BG, padx=7, pady=5,
                            highlightthickness=1, highlightbackground="#294048")
            card.grid(row=i//2, column=i%2, sticky="ew", padx=(0 if i%2 == 0 else 5, 0), pady=2)
            name = label(card, f"J{i+1}", 10, PLAYER_COLORS[i], anchor="w")
            name.pack(fill="x")
            score = label(card, "0 pts", 10, TEXT, anchor="w")
            score.pack(fill="x")
            self.player_cards.append((card, name, score))
        self.back_btn = button(side, "↶ Voltar pelo trajeto", self.back)
        self.back_btn.pack(fill="x", pady=4)
        tk.Checkbutton(side, text="Efeitos animados", variable=app.effects,
                       bg=PANEL, fg=MUTED, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT).pack(anchor="w", pady=5)
        button(side, "Nova expedição", app.show_setup).pack(fill="x", side="bottom")
        side.bind("<Configure>", self.resize_map)
        self.nav_bindings = []
        for key, portal in (("Left", 0), ("Up", 1), ("Right", 2), ("Down", 3)):
            sequence = f"<Alt-{key}>"
            binding = app.bind(sequence, lambda e, p=portal: self.navigate(p))
            self.nav_bindings.append((sequence, binding))
        for key, turn in (("q", -1), ("e", 1)):
            sequence = f"<Alt-{key}>"
            binding = app.bind(sequence, lambda e, d=turn: self.look(d))
            self.nav_bindings.append((sequence, binding))
        self.refresh()
        self.frame()

    def destroy(self):
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        for sequence, binding in self.nav_bindings:
            self.app.unbind(sequence, binding)
        super().destroy()

    def resize_map(self, event):
        side = self.map.master
        used = 28  # Sidebar's vertical padding.
        for widget in side.winfo_children():
            if widget is self.map:
                continue
            pad = widget.pack_info().get("pady", 0)
            used += widget.winfo_reqheight() + (sum(pad) if isinstance(pad, tuple) else 2*int(pad))
        self.map.configure(height=max(80, min(240, event.height-used)))

    def enter(self, door):
        g = self.game
        if self.transition or g.status != "playing" or g.remaining <= 0 or not g.current.cleared:
            return
        exits = g.exits()
        if not isinstance(door, int) or not 0 <= door < len(exits):
            return
        if self.app.effects.get():
            self.transition = {"type": "move", "start": time.monotonic(), "duration": .72,
                               "target": exits[door].key,
                               "portal": self.portal_targets().index(door), "back": False}
            self.feedback.configure(text="Abrindo passagem…", fg=TEAL)
            self.refresh()
        else:
            self._arrive(exits[door].key)

    def _arrive(self, target, back=False):
        exits = [room.key for room in self.game.exits()]
        moved = self.game.back() if back else self.game.enter(exits.index(target)) if target in exits else False
        if moved:
            self.arrival_at = time.monotonic() if self.app.effects.get() else None
            self.resume_at = 0
            self.feedback.configure(text=ROOMS[self.game.current.kind][1], fg=MUTED)
            self.refresh()

    def relative_portals(self, facing=None):
        direction = self.facing if facing is None else facing
        return [COMPASS[(direction+offset) % 4] for offset in (-1, 0, 1, 2)]

    def portal_targets(self, facing=None):
        """Match visible portals to actual adjacent rooms, never to a lane."""
        g = self.game
        exits = g.exits()
        return [next((i for i, room in enumerate(exits)
                      if room.key == (g.current.x + dx, g.current.y + dy)), None)
                for _, _, (dx, dy) in self.relative_portals(facing)]

    def look(self, turn):
        if self.transition or self.game.status != "playing" or self.game.remaining <= 0:
            return "break"
        target = (self.facing + turn) % 4
        if self.app.effects.get():
            self.transition = {"type": "look", "start": time.monotonic(), "duration": .42,
                               "from": self.facing, "to": target, "turn": turn}
        else:
            self.facing = target
        self.refresh()
        return "break"

    def advance_transition(self, now):
        transition = self.transition
        if not transition:
            return
        if self.game.status != "playing":
            self.transition = None
            return
        if self.app.effects.get() and now < transition["start"] + transition["duration"]:
            return
        self.transition = None
        if transition["type"] == "look":
            self.facing = transition["to"]
            self.refresh()
        else:
            self._arrive(transition["target"], transition["back"])

    def navigate(self, portal):
        target = self.portal_targets()[portal]
        if target is not None:
            self.enter(target)
        return "break"

    def map_click(self, event):
        for i, room in enumerate(self.game.exits()):
            position = self.map_positions.get(room.key)
            if position and max(abs(event.x-position[0]), abs(event.y-position[1])) <= self.map_radius + 3:
                self.enter(i)
                return

    def back(self):
        g = self.game
        if self.transition or not g.history or not g.current.cleared or g.status != "playing" or g.remaining <= 0:
            return
        target = g.history[-1]
        if self.app.effects.get():
            index = [room.key for room in g.exits()].index(target)
            self.transition = {"type": "move", "start": time.monotonic(), "duration": .72,
                               "target": target, "portal": self.portal_targets().index(index), "back": True}
            self.refresh()
        else:
            self._arrive(target, back=True)

    def submit(self):
        if not self.game.question:
            return
        result = self.game.submit(self.answer.get())
        if result:
            self.result(result)

    def result(self, result):
        good = result["correct"]
        author = result.get("player")
        self.feedback.configure(text=(f"J{author} · " if author else "") + result["message"],
                                fg=PLAYER_COLORS[author-1] if good and author else RED)
        self.resume_at = time.monotonic() + (1.3 if good else 3.0)
        caption = f"J{author}  +{result['points']:,}" if good else "−1 VIDA" if "answer" in result else "TEMPO ESGOTADO"
        self.popups.append([caption,
                            .5, .42, 1.6, PLAYER_COLORS[author-1] if good and author else RED])
        if good and self.app.effects.get():
            for _ in range(28):
                angle = random.random() * math.tau
                speed = random.uniform(.12, .6)
                self.particles.append([.5, .5, math.cos(angle)*speed,
                                       math.sin(angle)*speed, random.uniform(.5, 1.4),
                                       random.choice((PLAYER_COLORS[(author or 1)-1], "#dceeed"))])
        self.refresh()

    def refresh(self):
        g = self.game
        playing = g.status == "playing"
        ready = playing and g.current.cleared and not self.transition
        self.room_title.configure(text=f"SETOR {g.current.x:+d}, {g.current.y:+d}  /  "
                                  f"{ROOMS[g.current.kind][0].upper()}")
        exits = g.exits()
        targets = self.portal_targets()
        for i, btn in enumerate(self.door_buttons):
            direction = self.relative_portals()[i][1]
            room = exits[targets[i]] if targets[i] is not None else None
            hint = "Concluída" if room and room.cleared else ROOMS[room.kind][1] if room else "Sem passagem"
            if room and room.kind == "elite" and not room.cleared:
                hint = "×2 / tempo −25%"
            btn.configure(text=f"{direction}\n{ROOMS[room.kind][0] if room else 'PAREDE'}\n{hint}",
                          fg=ROOMS[room.kind][2] if room else MUTED,
                          state="normal" if ready and room else "disabled")
        self.back_btn.configure(state="normal" if ready and g.history else "disabled")
        for btn in self.look_buttons:
            btn.configure(state="normal" if playing and not self.transition else "disabled")
        self.answer.configure(state="normal" if g.question and playing else "disabled")
        self.submit_btn.configure(state="normal" if g.question and playing else "disabled")
        if g.question is None:
            self.answer.configure(state="normal")
            self.answer.delete(0, "end")
            self.answer.configure(state="disabled")
            self._shown_question = None
        if g.question:
            if self._shown_question is not g.question:
                self.answer.delete(0, "end")
                self._shown_question = g.question
            self.q_text.configure(text=g.question["question"])
            self.answer.focus_set()
        elif not playing:
            self.q_text.configure(text="Núcleo resolvido. Expedição concluída!" if g.status == "won"
                                  else "A expedição terminou. Uma nova rota espera por você.")
        elif g.current.cleared:
            self.q_text.configure(text="Área liberada. Explore uma passagem ou volte para outra rota.")
        else:
            self.q_text.configure(text="Prepare-se para o próximo desafio…")
        if not playing:
            self.finished = True
            self.transition = None
            self.particles.clear()
            self.arrival_at = None
        self.update_players(time.monotonic())
        self.draw_map()

    def update_players(self, now):
        g = self.game
        playing = g.status == "playing"
        active = g.player if playing else None
        if active != self._active_player:
            self._active_player = active
            self.turn_changed_at = now
        color = PLAYER_COLORS[g.player] if playing else MUTED
        state = (active, tuple(g.scores), g.status)
        if state != self._player_state:
            self._player_state = state
            self.challenge.configure(highlightbackground=color)
            self.answer.configure(highlightcolor=color, insertbackground=color)
            self.submit_btn.configure(bg=color, activebackground=blend(color, TEXT, .3))
            for i, (card, name, score) in enumerate(self.player_cards):
                selected = i == active
                card.configure(highlightbackground=PLAYER_COLORS[i] if selected else "#294048",
                               bg="#193038" if selected else BG)
                name.configure(text=f"J{i+1}  {'• SUA VEZ' if selected else '· FINAL' if not playing else '· ESPERA'}",
                               bg=card.cget("bg"), fg=PLAYER_COLORS[i] if selected else MUTED)
                score.configure(text=f"{g.scores[i]:,} pts", bg=card.cget("bg"))
        c = self.player_badge
        c.delete("all")
        c.create_rectangle(0, 0, 231, 45, fill="#12232b", outline="#294048")
        c.create_polygon(9, 11, 17, 5, 40, 5, 48, 13, 48, 36, 9, 36,
                         fill=color, outline="")
        c.create_text(29, 21, text=f"J{g.player+1}" if playing else "—", fill=BG,
                      font=(FONT, 12, "bold"))
        c.create_text(60, 11, text="NO CONTROLE" if playing else "EXPEDIÇÃO ENCERRADA",
                      fill=MUTED, font=(FONT, 8), anchor="w")
        c.create_text(60, 29, text=f"JOGADOR {g.player+1} · SUA VEZ" if playing else "PLACAR DA EQUIPE",
                      fill=color, font=(FONT, 11, "bold"), anchor="w", tags="active_player")
        fraction = smooth((now-self.turn_changed_at)/.5) if self.app.effects.get() else 1
        c.create_line(1, 44, 1+230*fraction, 44, fill=color, width=2)

    def draw_map(self):
        c, g = self.map, self.game
        c.delete("all")
        w = max(c.winfo_width(), 258)
        h = max(c.winfo_height(), 80)
        keys = g.revealed
        min_x, max_x = min(k[0] for k in keys), max(k[0] for k in keys)
        min_y, max_y = min(k[1] for k in keys), max(k[1] for k in keys)
        step = min(36, (w-42)/max(1, max_x-min_x), (h-42)/max(1, max_y-min_y))
        ox = w/2 - (min_x+max_x)*step/2
        oy = h/2 - (min_y+max_y)*step/2
        positions = {key: (ox + key[0]*step, oy + key[1]*step) for key in keys}
        self.map_positions = positions
        radius = self.map_radius = max(2, min(8, step*.26))
        for key, (x, y) in positions.items():
            for target in g.connections[key]:
                if target in positions and key < target and (key in g.visited or target in g.visited):
                    tx, ty = positions[target]
                    c.create_line(x, y, tx, ty, fill="#34535c", width=3, tags="corridor")
        for key, (x, y) in positions.items():
            room = g.rooms[key]
            current = key == g.current.key
            color = TEAL if current else ROOMS[room.kind][2]
            if current:
                c.create_rectangle(x-radius-3, y-radius-3, x+radius+3, y+radius+3, outline=TEAL, width=1)
            c.create_rectangle(x-radius, y-radius, x+radius, y+radius,
                               fill=color if room.cleared or current else BG, outline=color,
                               width=1, tags=("room", f"room:{key[0]}:{key[1]}"))
            if radius >= 5:
                c.create_text(x, y, text=("↑", "→", "↓", "←")[self.facing] if current else SYMBOLS[room.kind],
                              fill=BG if room.cleared or current else color, font=(FONT, 8, "bold"))
        c.create_text(w-8, 10, text="N ↑", anchor="ne", fill=MUTED, font=(FONT, 8))
        self.map_title.configure(text=f"PLANTA / {len(g.visited)} SALAS VISITADAS")

    def door_at(self, event):
        w, h = max(self.scene.winfo_width(), 1), max(self.scene.winfo_height(), 1)
        x, y = event.x / w, event.y / h
        for i, (left, top, right, bottom) in enumerate(self.door_bounds()):
            if left <= x <= right and top <= y <= bottom and self.portal_targets()[i] is not None:
                return i
        return None

    @staticmethod
    def door_bounds():
        return DOOR_BOUNDS

    def motion(self, event):
        self.hover = self.door_at(event)
        self.scene.configure(cursor="hand2" if self.hover is not None and self.game.current.cleared and not self.transition else "")

    def scene_click(self, event):
        door = self.door_at(event)
        if door is not None:
            self.navigate(door)

    def draw_scene(self, now):
        c, g = self.scene, self.game
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        def text(x, y, value, color=MUTED, size=10, **kw):
            return c.create_text(x*w, y*h, text=value, fill=color, font=(FONT, size), **kw)
        facing = self.facing
        opening = None
        camera = (1.0, 0.0, 0.0)
        shade = 0.0
        if self.transition:
            action = self.transition
            progress = min(1.0, max(0.0, (now-action["start"])/action["duration"]))
            if action["type"] == "look":
                half = progress*2 if progress < .5 else (1-progress)*2
                shift = smooth(half)*.075
                facing = action["from"] if progress < .5 else action["to"]
                # Overscan keeps the room covering the viewport throughout the turn.
                camera = (1.0 + 2*shift, -action["turn"]*shift if progress < .5 else action["turn"]*shift, 0.0)
                shade = smooth((half-.45)/.55)
            else:
                opening = (action["portal"], smooth(progress/.46))
                walk = max(0.0, (progress-.46)/.54)
                travel = smooth(walk)
                direction = action["portal"]
                zoom = 1 + travel*(.75 if direction != 3 else .04)
                # Steer the vanishing point toward the chosen doorway as we step.
                shift = (.25 if direction == 0 else -.25 if direction == 2 else 0)*travel
                camera = (zoom, shift, math.sin(walk*math.pi*2)*.005*math.sin(walk*math.pi))
                shade = smooth((walk-.50)/.50)
        elif self.arrival_at is not None and self.app.effects.get():
            settle = smooth((now-self.arrival_at)/.20)
            shade = 1-settle
            camera = (1+.025*(1-settle), 0., 0.)
            if settle >= 1:
                self.arrival_at = None
        exits = g.exits()
        targets = self.portal_targets(facing)
        compass = self.relative_portals(facing)
        portals = []
        for i, index in enumerate(targets):
            room = exits[index] if index is not None else None
            portals.append(None if room is None else {
                "label": ROOMS[room.kind][0], "compass": compass[i][0],
                "color": ROOMS[room.kind][2], "cleared": room.cleared})
        self.renderer.draw(room_key=g.current.key, kind=g.current.kind, portals=portals,
                           facing=COMPASS[facing][1], locked=not g.current.cleared,
                           opening=opening, camera=camera, now=now,
                           effects=self.app.effects.get(),
                           hovered=self.hover if not self.transition else None)
        if not g.current.cleared and g.status == "playing":
            color = ROOMS[g.current.kind][2]
            c.create_rectangle(w*.46,h*.43,w*.54,h*.60,fill="#10252e",outline=color,width=2)
            text(.5,.51,"?" if g.current.kind != "boss" else str(3-g.current.hits),color,20)
        if shade and self.app.effects.get():
            self.veil.draw(shade)
        if self.app.effects.get():
            for x, y, vx, vy, life, color in self.particles:
                r = max(1, life*3)
                c.create_oval(x*w-r,y*h-r,x*w+r,y*h+r,fill=color,outline="")
            for value, x, y, life, color in self.popups:
                text(x,y,value,blend(BG, color, min(1., life/.45)),26)
        if (len(g.scores) > 1 and g.status == "playing" and self.app.effects.get()
                and 0 < now-self.turn_changed_at < 1.25):
            color = PLAYER_COLORS[g.player]
            lift = 6*(1-smooth((now-self.turn_changed_at)/.25))
            c.create_rectangle(w*.30, h*.10+lift, w*.70, h*.10+lift+34,
                               fill=BG, outline=color, width=1)
            c.create_text(w*.5, h*.10+lift+17, text=f"JOGADOR {g.player+1}  ·  SUA VEZ",
                          fill=color, font=(FONT, 11, "bold"), tags="turn_notice")
        if self.finished:
            c.create_rectangle(w*.13,h*.25,w*.87,h*.75,fill=BG,outline=GOLD,width=2)
            won = g.status == "won"
            text(.5,.37,"MASMORRA CONQUISTADA" if won else "FIM DA EXPEDIÇÃO",GOLD if won else RED,22)
            text(.5,.50,f"{sum(g.scores):,} PONTOS",TEXT,30)
            text(.5,.63,f"Melhor combo: {g.best_combo}  ·  Salas visitadas: {len(g.visited)}",MUTED,11)

    def frame(self):
        now = time.monotonic()
        dt = min(.1, now-self.last_frame)
        self.last_frame = now
        result = self.game.tick()
        if result:
            self.result(result)
        self.advance_transition(now)
        if self.resume_at and now >= self.resume_at:
            self.resume_at = 0
            self.game.ask()
            self.refresh()
        g = self.game
        self.stats.configure(text=f"{'♥' * g.lives}{'♡' * (5-g.lives)}  /  {g.name.upper()}")
        seconds = math.ceil(g.remaining)
        self.clock_label.configure(text=f"{seconds//60:02}:{seconds%60:02}", fg=RED if seconds <= 30 else GOLD)
        target = sum(g.scores)
        self.display_score += (target-self.display_score)*(1-math.exp(-dt*12)) if self.app.effects.get() else target-self.display_score
        if abs(target-self.display_score) < 1:
            self.display_score = target
        self.score_label.configure(text=f"{int(self.display_score):,}")
        multiplier = 1 + min(max(g.combo-1, 0), 9)*.25
        self.combo_label.configure(text=f"COMBO {g.combo}  /  MULTIPLICADOR ×{multiplier:.2f}")
        self.update_players(now)
        qleft = g.question_remaining if g.question else 0
        meta = (f"JOGADOR {g.player+1} · SUA VEZ  /  {math.ceil(qleft)}s PARA RESPONDER" if g.question else
                f"JOGADOR {g.player+1} · ESCOLHA SUA ROTA" if g.current.cleared else
                f"JOGADOR {g.player+1} · PRÓXIMA RESPOSTA") if g.status == "playing" else "RESULTADO DA EQUIPE"
        if g.current.kind == "boss" and g.status == "playing":
            meta += f"  /  NÚCLEO {g.current.hits}/3"
        self.q_meta.configure(text=meta, fg=RED if g.question and qleft<5 else PLAYER_COLORS[g.player] if g.status == "playing" else MUTED)
        self.q_bar.delete("all")
        if g.question:
            self.q_bar.create_rectangle(0,0,self.q_bar.winfo_width()*qleft/g.question_duration,4,
                                        fill=RED if qleft<5 else PLAYER_COLORS[g.player],outline="")
        for p in self.particles:
            p[0] += p[2]*dt
            p[1] += p[3]*dt
            p[3] += .4*dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4]>0]
        for p in self.popups:
            p[2] -= .12*dt
            p[3] -= dt
        self.popups = [p for p in self.popups if p[3]>0]
        self.draw_scene(now)
        self.draw_map()
        # Account for drawing time instead of adding it to every frame interval.
        interval = 33 if self.app.effects.get() else 100
        self.job = self.after(max(8, interval-int((time.monotonic()-now)*1000)), self.frame)


def main():
    DungeonApp().mainloop()


if __name__ == "__main__":
    main()
