"""Animated, dependency-free Tkinter dungeon crawler."""

import math
import random
import time
import tkinter as tk

from dungeon import EFFECT_TEXT, EXIT_HITS, LIVES, PENALTIES, Expedition, ROOMS, format_seed
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
SYMBOLS = {"entrance": "E", "combat": "G", "elite": "!", "treasure": "$", "mimic": "M",
           "trap": "^", "sanctuary": "+", "empty": "·", "exit": "X", "unknown": ""}
RESULTS_DELAY = 2.0  # Seconds the winning room stays on screen.
TIER_NAMES = {"easy": "FÁCIL", "medium": "MÉDIA", "hard": "DIFÍCIL"}
POWER_NAMES = {"ward": "◆ ESCUDO", "hex": "◆ MALDIÇÃO", "swap": "◆ TROCA"}


def hearts(player):
    return "♥" * player.lives + "♡" * (LIVES - player.lives)


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

    def start(self, difficulty, players, seed=None):
        self.swap(ExpeditionScreen(self, Expedition(difficulty, players, seed)))

    def show_results(self, game):
        self.swap(ResultsScreen(self, game))


class ResultsScreen(tk.Frame):
    """Names the winner, shows the Seed, and offers a rematch on it or a fresh one."""

    def __init__(self, app, game):
        super().__init__(app, bg=BG)
        self.game = game
        box = tk.Frame(self, bg=PANEL, padx=40, pady=30, highlightthickness=1, highlightbackground=GOLD)
        box.place(relx=.5, rely=.5, anchor="center")
        winner = game.winner
        label(box, "MASMORRA CONQUISTADA", 14, GOLD).pack()
        self.winner_label = label(box, f"JOGADOR {winner+1} ESCAPOU", 30, PLAYER_COLORS[winner])
        self.winner_label.pack(pady=(6, 4))
        self.seed_label = label(box, f"{game.name.upper()}  ·  SEED {format_seed(game.seed)}", 12, TEXT)
        self.seed_label.pack()
        label(box, "Compartilhe a seed para desafiar alguém na mesma masmorra.", 9, MUTED).pack(pady=(2, 16))
        for i, player in enumerate(game.players):
            label(box, f"J{i+1}  {hearts(player)}   ·   {len(player.visited)} {'sala visitada' if len(player.visited) == 1 else 'salas visitadas'}   ·   "
                       f"núcleo {player.exit_hits}/{EXIT_HITS}",
                  11, PLAYER_COLORS[i] if i == winner else MUTED).pack(anchor="w")
        actions = tk.Frame(box, bg=PANEL)
        actions.pack(fill="x", pady=(20, 0))
        players = len(game.players)
        self.same_btn = button(actions, "REVANCHE · MESMA SEED",
                               lambda: app.start(game.difficulty, players, game.seed), True)
        self.new_btn = button(actions, "NOVA SEED", lambda: app.start(game.difficulty, players))
        self.menu_btn = button(actions, "MENU", app.show_setup)
        for btn in (self.same_btn, self.new_btn, self.menu_btn):
            btn.pack(side="left", padx=4)
            btn.bind("<Return>", lambda e, b=btn: b.invoke())
        self.same_btn.focus_set()



class ExpeditionScreen(tk.Frame):
    def __init__(self, app, game):
        super().__init__(app, bg=BG)
        self.app, self.game = app, game
        self.job = None
        self.resume_at = 0
        self.particles = []
        self.popups = []
        self.facings = [0] * len(game.players)
        self.last_frame = time.monotonic()
        self.hover = None
        self.finished = False
        self.finished_at = None
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
        self.map_title = label(side, "PLANTA / ÁREA EXPLORADA", 10, TEAL)
        self.map_title.pack(anchor="w", pady=(0, 4))
        self.map = tk.Canvas(side, width=258, height=220, bg="#0e1726", highlightthickness=0)
        self.map.pack(fill="x")
        self.map.bind("<Button-1>", self.map_click)
        self.map_positions = {}
        label(side, "$ baú · ! elite · ^ armadilha · + santuário · ● rivais\nAlt + setas: mover · Alt + Q/E: olhar",
              9, MUTED, justify="left").pack(anchor="w", pady=6)
        self.roster = tk.Frame(side, bg=PANEL)
        self.roster.pack(fill="x", pady=(4, 6))
        self.player_cards = []
        for i in range(len(game.players)):
            self.roster.columnconfigure(i % 2, weight=1, uniform="player")
            card = tk.Frame(self.roster, bg=BG, padx=7, pady=5,
                            highlightthickness=1, highlightbackground="#294048")
            card.grid(row=i//2, column=i%2, sticky="ew", padx=(0 if i%2 == 0 else 5, 0), pady=2)
            name = label(card, f"J{i+1}", 10, PLAYER_COLORS[i], anchor="w")
            name.pack(fill="x")
            status = label(card, "", 10, TEXT, anchor="w")
            status.pack(fill="x")
            self.player_cards.append((card, name, status))
        self.back_btn = button(side, "↶ Recuar pelo trajeto", self.back)
        self.back_btn.pack(fill="x", pady=4)
        power = tk.Frame(side, bg=PANEL)
        power.pack(fill="x", pady=(2, 4))
        self.power_label = label(power, "", 9, MUTED, anchor="w")
        self.power_label.grid(row=0, column=0, columnspan=4, sticky="ew")
        self.target_buttons = []
        for i in range(len(game.players)):
            power.columnconfigure(i, weight=1, uniform="target")
            btn = button(power, f"J{i+1}", lambda t=i: self.use_buff(t))
            btn.configure(font=(FONT, 9, "bold"), fg=PLAYER_COLORS[i], padx=4, pady=3)
            btn.grid(row=1, column=i, sticky="ew", padx=(0, 4), pady=(3, 0))
            self.target_buttons.append(btn)
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

    @property
    def facing(self):
        """Each racer keeps their own camera between Turns."""
        return self.facings[self.game.player]

    @facing.setter
    def facing(self, value):
        self.facings[self.game.player] = value

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
        if self.transition or g.status != "playing" or g.question or not g.has_cleared(g.current):
            return
        exits = g.exits()
        if not isinstance(door, int) or not 0 <= door < len(exits):
            return
        if self.app.effects.get():
            self.transition = {"type": "move", "start": time.monotonic(), "duration": .72,
                               "target": exits[door].key, "player": g.player,
                               "portal": self.portal_targets().index(door), "back": False}
            self.feedback.configure(text="Abrindo passagem…", fg=TEAL)
            self.refresh()
        else:
            self._arrive(exits[door].key)

    def _arrive(self, target, back=False):
        exits = [room.key for room in self.game.exits()]
        moved = self.game.retreat() if back else self.game.enter(exits.index(target)) if target in exits else False
        if moved:
            self.arrival_at = time.monotonic() if self.app.effects.get() else None
            self.resume_at = 0
            self.announce()
            self.refresh()

    def announce(self):
        """Say what the last move did: a Buff, a Debuff, a Guardian or nothing."""
        g, event = self.game, self.game.event
        if event:
            good = event["effect"] in ("haste", "insight", "heal", "ward", "hex", "swap")
            color = PLAYER_COLORS[event["player"]-1] if good else RED
            self.feedback.configure(text=f"J{event['player']} · {event['text'][:1].upper()}{event['text'][1:]}", fg=color)
            self.popups.append([event["text"].upper(), .5, .42, 1.6, color])
        else:
            self.feedback.configure(text=ROOMS[g.current.kind][1] if g.question
                                    else "Caminho livre. A vez passa adiante.", fg=MUTED)

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
        if self.transition or self.game.status != "playing":
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
        # A timeout may pass the Turn mid-walk; the walk belonged to the old racer.
        if self.game.status != "playing" or transition.get("player", self.game.player) != self.game.player:
            self.transition = None
            self.refresh()
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
        if self.transition or g.active.came_from is None or g.status != "playing":
            return
        target = g.active.came_from
        if self.app.effects.get():
            index = [room.key for room in g.exits()].index(target)
            self.transition = {"type": "move", "start": time.monotonic(), "duration": .72, "player": g.player,
                               "target": target, "portal": self.portal_targets().index(index), "back": True}
            self.refresh()
        else:
            self._arrive(target, back=True)

    def use_buff(self, target):
        if not self.transition and self.game.use_buff(target):
            self.announce()
            self.refresh()

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
        caption = f"J{author}  ✓" if good else EFFECT_TEXT[result["penalty"]].upper()
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
        here = g.has_cleared(g.current)
        ready = playing and here and g.question is None and not self.transition
        self.room_title.configure(text=f"SETOR {g.current.x:+d}, {g.current.y:+d}  /  "
                                  f"{ROOMS[g.current.kind][0].upper()}")
        exits = g.exits()
        targets = self.portal_targets()
        for i, btn in enumerate(self.door_buttons):
            direction = self.relative_portals()[i][1]
            room = exits[targets[i]] if targets[i] is not None else None
            kind = g.appearance(room) if room else None
            hint = "Liberada" if room and g.has_cleared(room) else ROOMS[kind][1] if room else "Sem passagem"
            btn.configure(text=f"{direction}\n{ROOMS[kind][0] if room else 'PAREDE'}\n{hint}",
                          fg=ROOMS[kind][2] if room else MUTED,
                          state="normal" if ready and room else "disabled")
        self.back_btn.configure(state="normal" if playing and g.active.came_from and not self.transition else "disabled")
        held = g.active.held if playing else None
        aimed = held in ("hex", "swap")
        self.power_label.configure(text=f"J{g.player+1}: {POWER_NAMES[held]} · " +
                                   ("USAR EM:" if aimed else "anula a próxima penalidade")
                                   if held else "Sem poder guardado")
        for i, btn in enumerate(self.target_buttons):
            usable = aimed and i != g.player and g.question is None and not self.transition
            btn.configure(state="normal" if usable else "disabled")
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
            self.q_text.configure(text=f"Jogador {g.winner+1} escapou da masmorra!")
        elif here:
            self.q_text.configure(text="Área liberada. Escolha uma passagem.")
        else:
            self.q_text.configure(text="O guardião aguarda. Responda ou recue pelo trajeto.")
        if not playing and not self.finished:
            self.finished_at = time.monotonic()
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
        color = PLAYER_COLORS[g.player if playing else g.winner]
        state = (active, tuple((p.position, p.exit_hits, p.lives, p.skip_next, p.held) for p in g.players), g.status)
        if state != self._player_state:
            self._player_state = state
            self.challenge.configure(highlightbackground=color)
            self.answer.configure(highlightcolor=color, insertbackground=color)
            self.submit_btn.configure(bg=color, activebackground=blend(color, TEXT, .3))
            for i, (card, name, status) in enumerate(self.player_cards):
                selected = i == active
                card.configure(highlightbackground=PLAYER_COLORS[i] if selected else "#294048",
                               bg="#193038" if selected else BG)
                player = g.players[i]
                tag = ('• SUA VEZ' if selected else '★ ESCAPOU' if i == g.winner
                       else '⏸ PULA' if player.skip_next else '· ESPERA')
                name.configure(text=f"J{i+1} {hearts(player)}  {tag}", bg=card.cget("bg"),
                               fg=PLAYER_COLORS[i] if selected or i == g.winner else MUTED)
                status.configure(text=f"PROF. {g.dungeon.rooms[player.position].depth}"
                                 f"  ·  X {player.exit_hits}/{EXIT_HITS}\n"
                                 f"{POWER_NAMES.get(player.held, '· sem poder')}", bg=card.cget("bg"),
                                 justify="left")
        c = self.player_badge
        c.delete("all")
        c.create_rectangle(0, 0, 231, 45, fill="#12232b", outline="#294048")
        c.create_polygon(9, 11, 17, 5, 40, 5, 48, 13, 48, 36, 9, 36,
                         fill=color, outline="")
        c.create_text(29, 21, text=f"J{(g.player if playing else g.winner)+1}", fill=BG,
                      font=(FONT, 12, "bold"))
        c.create_text(60, 11, text="NO CONTROLE" if playing else "CORRIDA ENCERRADA",
                      fill=MUTED, font=(FONT, 8), anchor="w")
        c.create_text(60, 29, text=f"JOGADOR {g.player+1} · SUA VEZ" if playing else f"JOGADOR {g.winner+1} VENCEU",
                      fill=color, font=(FONT, 11, "bold"), anchor="w", tags="active_player")
        fraction = smooth((now-self.turn_changed_at)/.5) if self.app.effects.get() else 1
        c.create_line(1, 44, 1+230*fraction, 44, fill=color, width=2)

    def draw_map(self):
        c, g = self.map, self.game
        c.delete("all")
        w = max(c.winfo_width(), 258)
        h = max(c.winfo_height(), 80)
        # Only the active racer's Map, plus where every rival stands.
        me = g.active
        rivals = [(i, p.position) for i, p in enumerate(g.players) if i != g.player]
        keys = me.revealed | {position for _, position in rivals}
        min_x, max_x = min(k[0] for k in keys), max(k[0] for k in keys)
        min_y, max_y = min(k[1] for k in keys), max(k[1] for k in keys)
        step = min(36, (w-42)/max(1, max_x-min_x), (h-42)/max(1, max_y-min_y))
        ox = w/2 - (min_x+max_x)*step/2
        oy = h/2 - (min_y+max_y)*step/2
        positions = {key: (ox + key[0]*step, oy + key[1]*step) for key in keys}
        self.map_positions = {key: positions[key] for key in me.revealed}
        radius = self.map_radius = max(2, min(8, step*.26))
        for key in me.revealed:
            x, y = positions[key]
            for target in g.dungeon.connections[key]:
                if target in me.revealed and key < target and (key in me.visited or target in me.visited):
                    tx, ty = positions[target]
                    c.create_line(x, y, tx, ty, fill="#34535c", width=3, tags="corridor")
        color_here = PLAYER_COLORS[g.player]
        for key in me.revealed:
            x, y = positions[key]
            kind = g.appearance(g.dungeon.rooms[key])
            current = key == g.current.key
            cleared = key in me.cleared
            color = color_here if current else ROOMS[kind][2]
            if current:
                c.create_rectangle(x-radius-3, y-radius-3, x+radius+3, y+radius+3, outline=color_here, width=1)
            c.create_rectangle(x-radius, y-radius, x+radius, y+radius,
                               fill=color if cleared or current else BG, outline=color,
                               dash=(2, 2) if kind == "unknown" else None,
                               width=1, tags=("room", f"room:{key[0]}:{key[1]}", f"kind:{kind}"))
            if radius >= 5:
                c.create_text(x, y, text=("↑", "→", "↓", "←")[self.facing] if current else SYMBOLS[kind],
                              fill=BG if cleared or current else color, font=(FONT, 8, "bold"))
        for i, key in rivals:
            x, y = positions[key]
            # Rivals sharing a Room fan out so every dot stays visible.
            dx = (i - 1.5) * max(2, radius*.6)
            c.create_oval(x+dx-3, y+radius+1, x+dx+3, y+radius+7, fill=PLAYER_COLORS[i], outline=BG, tags="rival")
        c.create_text(w-8, 10, text="N ↑", anchor="ne", fill=MUTED, font=(FONT, 8))
        self.map_title.configure(text=f"PLANTA J{g.player+1} / {len(me.visited)} SALAS · SEED {format_seed(g.seed)}")

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
        self.scene.configure(cursor="hand2" if self.hover is not None and self.game.has_cleared(self.game.current) and not self.transition else "")

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
            kind = None if room is None else g.appearance(room)
            portals.append(None if room is None else {
                "label": ROOMS[kind][0], "compass": compass[i][0],
                "color": ROOMS[kind][2], "cleared": g.has_cleared(room)})
        here = g.has_cleared(g.current)
        self.renderer.draw(room_key=g.current.key, kind=g.current.kind, portals=portals,
                           facing=COMPASS[facing][1], locked=not here,
                           opening=opening, camera=camera, now=now,
                           effects=self.app.effects.get(),
                           hovered=self.hover if not self.transition else None)
        if not here and g.status == "playing":
            color = ROOMS[g.current.kind][2]
            c.create_rectangle(w*.46,h*.43,w*.54,h*.60,fill="#10252e",outline=color,width=2)
            text(.5,.51,"?" if g.current.kind != "exit" else str(EXIT_HITS-g.active.exit_hits),color,20)
        if shade and self.app.effects.get():
            self.veil.draw(shade)
        if self.app.effects.get():
            for x, y, vx, vy, life, color in self.particles:
                r = max(1, life*3)
                c.create_oval(x*w-r,y*h-r,x*w+r,y*h+r,fill=color,outline="")
            for value, x, y, life, color in self.popups:
                text(x,y,value,blend(BG, color, min(1., life/.45)),26)
        if (len(g.players) > 1 and g.status == "playing" and self.app.effects.get()
                and 0 < now-self.turn_changed_at < 1.25):
            color = PLAYER_COLORS[g.player]
            lift = 6*(1-smooth((now-self.turn_changed_at)/.25))
            c.create_rectangle(w*.30, h*.10+lift, w*.70, h*.10+lift+34,
                               fill=BG, outline=color, width=1)
            c.create_text(w*.5, h*.10+lift+17, text=f"JOGADOR {g.player+1}  ·  SUA VEZ",
                          fill=color, font=(FONT, 11, "bold"), tags="turn_notice")
        if self.finished:
            c.create_rectangle(w*.13,h*.25,w*.87,h*.75,fill=BG,outline=GOLD,width=2)
            text(.5,.37,"MASMORRA CONQUISTADA",GOLD,22)
            text(.5,.50,f"JOGADOR {g.winner+1} ESCAPOU",PLAYER_COLORS[g.winner],30)
            text(.5,.63,f"Seed {format_seed(g.seed)}  ·  Salas visitadas: {len(g.players[g.winner].visited)}",MUTED,11)

    def frame(self):
        now = time.monotonic()
        # Let the winning moment land on screen, then hand over to the results.
        if self.finished and now - self.finished_at >= RESULTS_DELAY:
            self.job = None
            self.app.show_results(self.game)
            return
        dt = min(.1, now-self.last_frame)
        self.last_frame = now
        result = self.game.tick()
        if result:
            self.result(result)
        self.advance_transition(now)
        if self.resume_at and now >= self.resume_at:
            self.resume_at = 0
        if not self.resume_at and not self.transition and self.game.question is None:
            # Whoever stands before an un-Cleared Guardian faces it once results are read.
            self.game.ask()
            if self.game.question is not None:
                self.refresh()
        g = self.game
        self.stats.configure(text=f"J{g.player+1} {hearts(g.active)}  /  {g.name.upper()}" if g.status == "playing"
                             else g.name.upper())
        self.update_players(now)
        qleft = g.question_remaining if g.question else 0
        miss = ("ESCUDO ANULA" if g.active.held == "ward" else
                EFFECT_TEXT[PENALTIES[g.question_tier]].upper()) if g.question else ""
        meta = (f"JOGADOR {g.player+1}  /  {TIER_NAMES.get(g.question_tier)} · ERRO: {miss}  /  "
                f"{math.ceil(qleft)}s" if g.question else
                f"JOGADOR {g.player+1} · ESCOLHA SUA ROTA" if g.has_cleared(g.current) else
                f"JOGADOR {g.player+1} · RESPONDA OU RECUE") if g.status == "playing" else "FIM DA CORRIDA"
        if g.current.kind == "exit" and g.status == "playing":
            meta += f"  /  NÚCLEO {g.active.exit_hits}/{EXIT_HITS}"
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
