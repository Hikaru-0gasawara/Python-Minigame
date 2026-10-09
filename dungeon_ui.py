"""Animated, dependency-free Tkinter dungeon crawler."""

import math
import random
import sys
import time
import tkinter as tk

import font
import hud
from dungeon import EFFECT_TEXT, EXIT_HITS, Expedition, ROOMS, format_seed
from hud import hearts
from menu_ui import Setup
from motion import smooth
from palette import hex_color
from pixel_view import PixelView
from scene import portal_targets, relative_portals, scene_for

BG = "#080e12"
PANEL = "#111e25"
TEXT = "#edf1f8"
MUTED = "#94a4bd"
GOLD = "#f3c66b"
TEAL = "#24e5dd"
FONT = "Segoe UI"
PLAYER_COLORS = tuple(hex_color(ink) for ink in hud.PLAYER_INK)
# Alt is a different modifier bit on Windows; NumLock owns 0x8 there.
ALT_MASK = 0x20000 if sys.platform == "win32" else 0x8

# Initial portal layout; relative_portals follows the player's current facing.
PORTALS = (("O", "OESTE", (-1, 0)), ("N", "NORTE", (0, -1)),
           ("L", "LESTE", (1, 0)), ("S", "SUL", (0, 1)))
RESULTS_DELAY = 2.0  # Seconds the winning room stays on screen.


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
    """The whole window is the dungeon: one 320x200 pixel frame, HUD included."""

    def __init__(self, app, game):
        super().__init__(app, bg="#000000")
        self.app, self.game = app, game
        self.job = None
        self.resume_at = 0
        self.particles = []          # [x, y, vx, vy, life, ink, gravity] in native pixels
        self.popups = []
        self._scene = None
        self._flicker_until = self._glitch_until = 0
        self.facings = [0] * len(game.players)
        self.last_frame = time.monotonic()
        self.hover = None
        self.finished = False
        self.finished_at = None
        self.transition = None
        self.arrival_at = None
        self._active_player = None
        self.turn_changed_at = 0
        self.typed = ""
        self._shown_question = None
        self.message = "A entrada está segura. Escolha sua primeira porta."
        self.message_ink = hud.GOLD
        self.hud = {}
        self._layers = {}
        self.regions = []
        self.box_rect = None
        self.tab_rect = None
        self.map_positions, self.map_corridors, self.map_rivals, self.map_kinds = {}, set(), [], {}
        self.map_radius = 0
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0, takefocus=True)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<Leave>", lambda e: setattr(self, "hover", None))
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Configure>", lambda e: self.draw_scene(time.monotonic()))
        self.renderer = PixelView(self.canvas)
        self.edges = hud.edges()
        bindings = [(f"<Alt-{key}>", lambda e, p=portal: self.navigate(p))
                    for key, portal in (("Left", 0), ("Up", 1), ("Right", 2), ("Down", 3))]
        bindings += [(f"<Alt-{key}>", lambda e, d=turn: self.look(d)) for key, turn in (("q", -1), ("e", 1))]
        bindings += [("<Alt-r>", lambda e: self.back() or "break")]
        bindings += [(f"<Alt-Key-{i + 1}>", lambda e, t=i: self.use_buff(t) or "break") for i in range(len(game.players))]
        bindings += [("<Key>", self.on_key), ("<Escape>", lambda e: self.app.show_setup())]
        self.nav_bindings = [(sequence, app.bind(sequence, handler)) for sequence, handler in bindings]
        self.canvas.focus_set()
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

    # ---------------------------------------------------------------- actions

    def enter(self, door):
        g = self.game
        if self.transition or g.status != "playing" or g.question or not g.can_leave():
            return
        exits = g.exits()
        if not isinstance(door, int) or not 0 <= door < len(exits):
            return
        if self.app.effects.get():
            self.transition = {"type": "move", "start": time.monotonic(), "duration": .72,
                               "target": exits[door].key, "player": g.player,
                               "portal": self.portal_targets().index(door), "back": False}
            self.say("Abrindo passagem…", hud.PLAYER_INK[g.player])
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

    def say(self, text, ink):
        self.message, self.message_ink = text, ink

    def announce(self):
        """Say what the last move did: a Buff, a Debuff, a Guardian or nothing."""
        g, event = self.game, self.game.event
        if event:
            good = event["effect"] in ("haste", "insight", "heal", "ward", "hex", "swap")
            ink = hud.PLAYER_INK[event["player"] - 1] if good else hud.ALERT
            self.say(f"J{event['player']} · {event['text'][:1].upper()}{event['text'][1:]}", ink)
            self.popups.append([event["text"].upper(), ink, time.monotonic()])
        else:
            self.say(ROOMS[g.current.kind][1] if g.question else "Caminho livre. A vez passa adiante.", hud.MUTED)

    def relative_portals(self, facing=None):
        return relative_portals(self.facing if facing is None else facing)

    def portal_targets(self, facing=None):
        """Match visible portals to actual adjacent rooms, never to a lane."""
        return portal_targets(self.game, self.facing if facing is None else facing)

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

    def on_key(self, event):
        """Typing goes into the answer while a Guardian waits; Alt chords are shortcuts."""
        g = self.game
        if g.status != "playing" or g.question is None or event.state & ALT_MASK:
            return None
        if event.keysym in ("Return", "KP_Enter"):
            self.submit()
        elif event.keysym == "BackSpace":
            self.typed = self.typed[:-1]
        elif (len(event.char) == 1 and event.char.isprintable()
              and font.measure(f"> {self.typed}{event.char}_") <= hud.BOX_WIDTH - 8):
            self.typed += event.char
        else:
            return None
        self.refresh()
        return "break"

    def submit(self):
        if not self.game.question:
            return
        result = self.game.submit(self.typed)
        if result:
            self.result(result)

    def result(self, result):
        good = result["correct"]
        author = result.get("player")
        ink = hud.PLAYER_INK[author - 1] if good and author else hud.ALERT
        self.say((f"J{author} · " if author else "") + result["message"], ink)
        self.resume_at = time.monotonic() + (1.3 if good else 3.0)
        caption = f"J{author}  ✓" if good else EFFECT_TEXT[result["penalty"]].upper()
        self.popups.append([caption, ink, time.monotonic()])
        if good and self.app.effects.get():
            for _ in range(28):
                angle = random.random() * math.tau
                speed = random.uniform(20, 90)
                self.particles.append([160., 100., math.cos(angle) * speed, math.sin(angle) * speed,
                                       random.uniform(.5, 1.4), random.choice((ink, hud.TEXT)), 60])
        self.refresh()

    # ---------------------------------------------------------------- input regions

    def door_label(self, portal):
        """What the active player knows lies behind a door, or None for a wall."""
        target = self.portal_targets()[portal]
        if target is None:
            return None
        g = self.game
        room = g.exits()[target]
        kind = g.appearance(room)
        hint = "Liberada" if g.has_cleared(room) else ROOMS[kind][1]
        return f"{self.relative_portals()[portal][1]} · {ROOMS[kind][0]} · {hint}"

    def door_regions(self):
        """Native regions of the four portals: the three drawn doors and the 'behind' tab."""
        return list(self.renderer.regions) + [self.tab_rect or (-9, -9, -9, -9)]

    def _hits(self, rect, native):
        x0, y0, x1, y1 = rect
        return x0 <= native[0] <= x1 and y0 <= native[1] <= y1

    def _on_hud(self, native):
        return (any(self._hits(rect, native) for _, rect in self.regions)
                or (self.box_rect and self._hits(self.box_rect, native)) or native[1] >= hud.CARDS_TOP)

    def door_at(self, event):
        native = self.renderer.to_native(event.x, event.y)
        if native is None:
            return None
        for portal, rect in enumerate(self.door_regions()):
            if self._hits(rect, native) and (portal == 3 or not self._on_hud(native)):
                return portal if self.portal_targets()[portal] is not None else None
        return None

    def door_bounds(self):
        """Each portal's clickable region as fractions of the canvas."""
        w, h = max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1)
        bounds = []
        for x0, y0, x1, y1 in self.door_regions():
            (left, top), (right, bottom) = self.renderer.to_canvas(x0, y0), self.renderer.to_canvas(x1 + 1, y1 + 1)
            bounds.append((left / w, top / h, right / w, bottom / h))
        return bounds

    def region_centre(self, action):
        """Canvas coordinates of a HUD control, for clicks and tests."""
        for found, (x0, y0, x1, y1) in self.regions:
            if found == action:
                return self.renderer.to_canvas((x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2)
        return None

    def motion(self, event):
        self.hover = self.door_at(event)
        native = self.renderer.to_native(event.x, event.y)
        control = native is not None and any(self._hits(rect, native) for _, rect in self.regions)
        self.canvas.configure(cursor="hand2" if control or (self.hover is not None and self.game.can_leave()
                                                             and not self.transition) else "")

    def click(self, event):
        native = self.renderer.to_native(event.x, event.y)
        if native is None:
            return
        for action, rect in self.regions:
            if self._hits(rect, native):
                if action[0] == "look":
                    self.look(action[1])
                elif action[0] == "retreat":
                    self.back()
                elif action[0] == "buff":
                    self.use_buff(action[1])
                return
        if self.map_positions and self._hits(self.map_rect, native):
            self.map_click(event)
            return
        door = self.door_at(event)
        if door is not None:
            self.navigate(door)

    def map_click(self, event):
        for i, room in enumerate(self.game.exits()):
            position = self.map_positions.get(room.key)
            if position and max(abs(event.x - position[0]), abs(event.y - position[1])) <= self.map_radius:
                self.enter(i)
                return

    # ---------------------------------------------------------------- state and drawing

    def refresh(self):
        g = self.game
        playing = g.status == "playing"
        if g.question is not self._shown_question:
            self.typed = ""
            self._shown_question = g.question
        if not playing and not self.finished:
            self.finished_at = time.monotonic()
        if not playing:
            self.finished = True
            self.transition = None
            self.particles.clear()
            self.arrival_at = None
        self.update_players(time.monotonic())
        self.draw_scene(time.monotonic())

    def update_players(self, now):
        active = self.game.player if self.game.status == "playing" else None
        if active != self._active_player:
            self._active_player = active
            self.turn_changed_at = now

    def _layer(self, name, key, build):
        """A HUD piece and its photo, rebuilt only when its key changes."""
        cached = self._layers.get(name)
        if cached is None or cached[0] != key:
            piece = build()
            cached = self._layers[name] = (key, piece, tk.PhotoImage(master=self.canvas, data=piece.pix.png()))
        return cached[1], cached[2]

    def _put(self, name, key, build, y=None):
        piece, photo = self._layer(name, key, build)
        self.renderer.overlay(photo, piece.x, piece.y if y is None else y)
        return piece

    def _minimap(self):
        piece, centres, self.map_corridors, self.map_rivals, self.map_kinds, self._map_cell = hud.minimap(self.game)
        self._map_centres = centres
        return piece

    def draw_scene(self, now):
        g = self.game
        effects = self.app.effects.get()
        playing = g.status == "playing"
        facing, fade = self.facing, 0
        # A dithered fade stands in for the walk until doors and transitions get their own art.
        if self.transition:
            action = self.transition
            progress = min(1.0, max(0.0, (now - action["start"]) / action["duration"]))
            if action["type"] == "look":
                facing = action["from"] if progress < .5 else action["to"]
                fade = min(4, int((1 - abs(progress * 2 - 1)) * 5))
            else:
                fade = min(4, int(max(0., progress - .5) * 10))
        elif self.arrival_at is not None and effects:
            settle = (now - self.arrival_at) / .20
            fade = max(0, 4 - int(settle * 5))
            if settle >= 1:
                self.arrival_at = None
        view = self.renderer
        self.canvas.delete("all")
        scene = scene_for(g, facing)
        if self._scene is None or (scene.room_key, g.player) != (self._scene.room_key, self._scene_player):
            self.particles.clear()       # particles belong to the room they were born in
        self._scene, self._scene_player = scene, g.player
        lights = "dimmed" if effects and scene.flicker and now < self._flicker_until else "on"
        view.compose(scene, fade if effects else 0, lights, effects and now < self._glitch_until)
        can_retreat = playing and g.active.came_from is not None and not self.transition
        players = tuple((p.position, p.exit_hits, p.lives, p.skip_next, p.held) for p in g.players)
        self.regions = []
        for i, piece in enumerate(self.edges):
            self._put(f"edge{i}", None, lambda piece=piece: piece)
            self.regions += piece.regions if playing else []
        badge = self._put("badge", (g.player, g.status, g.current.key, facing),
                          lambda: hud.badge(g, facing))
        me = g.active
        mini = self._put("map", (g.player, frozenset(me.revealed), frozenset(me.visited), players),
                         self._minimap)
        self.map_rect = (mini.x, mini.y, mini.x + mini.pix.w - 1, mini.y + mini.pix.h - 1)
        self.map_positions = {key: view.to_canvas(*c) for key, c in self._map_centres.items()}
        self.map_radius = view.scale * max(1, self._map_cell // 2)
        cards = self._put("cards", (g.player, g.status, players, can_retreat), lambda: hud.cards(g, can_retreat))
        self.regions += cards.regions
        if g.question is not None and playing:
            lines = hud.question_lines(g, self.typed, int(now * 2) % 2 == 0)
        else:
            behind = self.door_label(self.hover) if self.hover is not None and playing else None
            lines = hud.message_lines(g, behind or self.message, hud.TEXT if behind else self.message_ink, can_retreat)
        bottom = hud.CARDS_TOP - 2
        border = hud.PLAYER_INK[g.player] if playing else hud.GOLD
        box = self._put("box", (tuple(lines), bottom, border), lambda: hud.answer_box(lines, bottom, border))
        self.box_rect = (box.x, box.y, box.x + box.pix.w - 1, box.y + box.pix.h - 1)
        self.tab_rect = None
        if playing and self.portal_targets(facing)[3] is not None:
            caption = f"↓ {self.relative_portals(facing)[3][0]} · ATRÁS"
            tab = self._put("tab", (caption, self.hover == 3), lambda: hud.behind_tab(caption, self.hover == 3))
            self.tab_rect = (tab.x, tab.y, tab.x + tab.pix.w - 1, tab.y + tab.pix.h - 1)
        if g.question is not None and playing and g.question_duration:
            left = g.question_remaining / g.question_duration
            ink = hud.ALERT if g.question_remaining <= 5 else hud.PLAYER_INK[g.player]
            view.fill(ink, box.x + 2, box.y + box.pix.h - 3, box.x + 2 + int((box.pix.w - 5) * left), box.y + box.pix.h - 3)
        if self.hover is not None and self.hover != 3 and g.can_leave() and not self.transition and playing:
            x0, y0, x1, y1 = view.regions[self.hover]
            ink = hud.PLAYER_INK[g.player]
            for rect in ((x0, y0, x1, y0), (x0, y1, x1, y1), (x0, y0, x0, y1), (x1, y0, x1, y1)):
                view.fill(ink, *rect)
        if len(g.players) > 1 and playing and effects and 0 < now - self.turn_changed_at < 1.25:
            lift = int(6 * (1 - smooth((now - self.turn_changed_at) / .25)))
            text = f"JOGADOR {g.player + 1} · SUA VEZ"
            self._put("turn", text, lambda: hud.banner([(text, hud.PLAYER_INK[g.player])], 0, hud.PLAYER_INK[g.player]),
                      y=50 - lift)
        if effects:
            for text, ink, born in self.popups:
                age = now - born
                self._put(f"popup:{text}", ink, lambda: hud.banner([(text, ink)], 0, ink), y=int(84 - age * 14))
            for x, y, _vx, _vy, _life, ink, _gravity in self.particles:
                view.fill(ink, int(x), int(y), int(x), int(y))
        if self.finished:
            winner = g.players[g.winner]
            ending = [("MASMORRA CONQUISTADA", hud.GOLD), (f"JOGADOR {g.winner + 1} ESCAPOU", hud.PLAYER_INK[g.winner]),
                      (f"SEED {format_seed(g.seed)} · {len(winner.visited)} SALAS", hud.MUTED)]
            self._put("finished", tuple(ending), lambda: hud.banner(ending, 60, hud.GOLD))
        view.present()
        self.hud = {"badge": badge.texts, "map": mini.texts, "cards": cards.texts, "box": [t for t, _ in lines],
                    "tab": self.tab_rect is not None}

    def ambience(self, now):
        """Spawn the room's ambient particles and stutter its broken tube and screens."""
        scene, rnd = self._scene, random.random
        for kind, x, y in scene.emitters:
            if kind == "dust" and sum(p[6] == 0 for p in self.particles) < 16:
                self.particles.append([rnd() * 320, 20 + rnd() * 150, rnd() * 4 - 2, rnd() * 3 - 1.5,
                                       3 + rnd() * 3, 6, 0])
            elif kind == "sparks" and rnd() < .04:
                for _ in range(5):
                    self.particles.append([x + rnd() * 6 - 3, y, rnd() * 40 - 20, rnd() * 10, .7, 17, 140])
            elif kind == "steam" and rnd() < .35:
                self.particles.append([x + rnd() * 10 - 5, y, rnd() * 6 - 3, -14 - rnd() * 8, 1.4, 9, -2])
            elif kind == "bubbles" and rnd() < .3:
                self.particles.append([x + rnd() * 20 - 10, y + 20, 0, -10 - rnd() * 6, 1.8, 21, -1])
        if scene.flicker and now >= self._flicker_until and rnd() < .02:
            self._flicker_until = now + .05 + rnd() * .25
        if any(d[0] == "screen" for d in scene.decor) and now >= self._glitch_until and rnd() < .01:
            self._glitch_until = now + .15

    def frame(self):
        now = time.monotonic()
        # Let the winning moment land on screen, then hand over to the results.
        if self.finished and now - self.finished_at >= RESULTS_DELAY:
            self.job = None
            self.app.show_results(self.game)
            return
        dt = min(.1, now - self.last_frame)
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
        self.update_players(now)
        if self.app.effects.get() and self._scene is not None:
            self.ambience(now)
        else:
            self.particles.clear()
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += p[6] * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]
        self.popups = [p for p in self.popups if now - p[2] < 1.6]
        self.draw_scene(now)
        # Account for drawing time instead of adding it to every frame interval.
        interval = 33 if self.app.effects.get() else 100
        self.job = self.after(max(8, interval - int((time.monotonic() - now) * 1000)), self.frame)


def main():
    DungeonApp().mainloop()


if __name__ == "__main__":
    main()
