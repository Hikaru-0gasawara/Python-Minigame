"""Animated, dependency-free Tkinter dungeon crawler."""

import ctypes
from dataclasses import replace
import math
import random
import sys
import time
import tkinter as tk

from audio import Audio
import font
import hud
from dialogue import Dialogue
from dungeon import BUFFS, EFFECT_TEXT, Expedition, ROOMS, format_seed
from menu_ui import Setup
from motion import smooth
from pixel_view import PixelView
from records import Records
from room_art import DOOR_STEPS, GUARDIAN_ASIDE, H, W
from scene import portal_targets, relative_portals, scene_for, sector_of

BG = "#080e12"
# Alt is a different modifier bit on Windows; NumLock owns 0x8 there.
ALT_MASK = 0x20000 if sys.platform == "win32" else 0x8

RESULTS_DELAY = 2.0  # Seconds the winning room stays on screen.
MESSAGE_TIME = 4.0   # Seconds a note stays above the cards before the scene is left clear.
OPEN, STEP = .30, .07          # a walk: the door opens, then each zoom step into the doorway
WALK = OPEN + 6 * STEP
ARRIVE, TURN_FADE = .6, .25
REACT, GLITCH, STEP_ASIDE = .9, .5, .4   # after an answer: how long the Guardian's reaction holds the view
# An arrival's tubes: (seconds since arriving, lights) - dark, a stutter, then on.
ARRIVAL_LIGHTS = ((.25, "off"), (.32, "on"), (.40, "off"), (.50, "dimmed"), (math.inf, "on"))


class DungeonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Trivia • A Masmorra dos Ecos")
        self.geometry("960x600")             # exactly 320x200 at x3: no black bars at the start
        self.minsize(960, 600)
        self.configure(bg=BG)
        self.screen = None
        self.effects = tk.BooleanVar(value=True)
        self.audio = Audio()
        self.records = Records()
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
        rank = self.records.submit(game.difficulty, game.elapsed, game.seed, len(game.players))
        self.swap(ResultsScreen(self, game, rank))


class ResultsScreen(tk.Frame):
    """The winner's room, dimmed behind a pixel panel: who escaped, how fast, a new Record, and what next."""

    def __init__(self, app, game, rank=None):
        super().__init__(app, bg="#000000")
        self.app, self.game, self.rank = app, game, rank
        self.selected = 0
        players = len(game.players)
        # In the order of hud.ACTIONS: rematch on the same Seed, a new Seed, the menu.
        self.actions = (lambda: app.start(game.difficulty, players, game.seed),
                        lambda: app.start(game.difficulty, players), app.show_setup)
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0, takefocus=True)
        self.canvas.pack(fill="both", expand=True)
        self.renderer = PixelView(self.canvas)
        room = game.dungeon.rooms[game.players[game.winner].position]
        facing = next((f for f in range(4) if portal_targets(game, f, room)[1] is None), 0)  # face the core gate
        self.renderer.compose(scene_for(game, facing, game.winner), "dimmed")
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Key>", self.on_key)     # canvas bindings die with the screen
        self.canvas.focus_set()
        self.draw()

    def draw(self):
        self.panel = hud.results(self.game, self.rank, self.selected)
        self._photo = tk.PhotoImage(master=self.canvas, data=self.panel.pix.png())
        self.renderer.clear_hud()
        self.renderer.overlay(self._photo, self.panel.x, self.panel.y)
        self.canvas.delete("all")
        self.renderer.present(fade=2)

    def action_at(self, event):
        action = hud.hit(self.panel.regions, self.renderer.to_native(event.x, event.y))
        return None if action is None else action[1]

    def region_centre(self, i):
        """Canvas coordinates of an action, for clicks and tests."""
        return self.renderer.centre(self.panel.regions[i][1])

    def motion(self, event):
        i = self.action_at(event)
        self.canvas.configure(cursor="" if i is None else "hand2")
        if i is not None and i != self.selected:
            self.selected = i
            self.draw()

    def click(self, event):
        i = self.action_at(event)
        if i is not None:
            self.actions[i]()

    def on_key(self, event):
        """Arrows and Tab pick an action, Enter or space takes it, Escape goes to the menu."""
        if event.keysym in ("Return", "KP_Enter", "space"):
            self.actions[self.selected]()
        elif event.keysym == "Escape":
            self.app.show_setup()
        elif event.keysym in ("Left", "Up", "Right", "Down", "Tab"):
            self.selected = (self.selected + (-1 if event.keysym in ("Left", "Up") else 1)) % len(self.actions)
            self.draw()
        else:
            return None
        return "break"


class ExpeditionScreen(tk.Frame):
    """The whole window is the dungeon: one 320x200 pixel frame, HUD included."""

    def __init__(self, app, game):
        super().__init__(app, bg="#000000")
        self.app, self.game = app, game
        self.paused_at, self.paused_total, self.pause_choice = None, 0., 0
        game.clock = self.now                # the Question's time and the escape time stop while paused
        self.job = None
        self.resume_at = 0
        self.particles = []          # [x, y, vx, vy, life, ink, gravity] in native pixels
        self.popups = []
        self._scene = None
        self._flicker_until = self._glitch_until = 0
        self.facings = [0] * len(game.players)
        self.last_frame = self.now()
        self.hover = None
        self.finished = False
        self.finished_at = None
        self.transition = None
        self.arrival_at, self.arrival_player = None, 0
        self.presented = {}
        self.dialogue, self._voiced = None, 0
        self.reaction = None                 # {"player", "kind", "start"} right after an answer
        # The Guardian's voice: one blip per batch of letters, as a new sound cuts the previous one anyway.
        self.on_voice = lambda letters: self.app.audio.play("blip")
        self._active_player = None
        self.turn_changed_at = 0
        self.typed = ""
        self._shown_question = None
        self.say("A entrada está segura. Clique numa porta ou use Alt + setas.", hud.GOLD)
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
        self.canvas.bind("<Configure>", lambda e: self.draw_scene(self.now()))
        self.renderer = PixelView(self.canvas)
        self.edges = hud.edges()
        bindings = [(f"<Alt-{key}>", lambda e, p=portal: self.navigate(p))
                    for key, portal in (("Left", 0), ("Up", 1), ("Right", 2), ("Down", 3))]
        bindings += [(f"<Alt-{key}>", lambda e, d=turn: self.look(d)) for key, turn in (("q", -1), ("e", 1))]
        bindings += [("<Alt-r>", lambda e: self.back() or "break"), ("<Alt-m>", lambda e: self.toggle_mute() or "break")]
        bindings += [(f"<Alt-Key-{i + 1}>", lambda e, t=i: self.use_buff(t) or "break") for i in range(len(game.players))]
        bindings += [("<Key>", self.on_key), ("<Escape>", lambda e: self.toggle_pause() or "break")]
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

    def now(self):
        """The screen's clock, shared with the Expedition: it stands still while the game is paused."""
        return (time.monotonic() if self.paused_at is None else self.paused_at) - self.paused_total

    def toggle_pause(self):
        if self.paused_at is not None:
            self.paused_total += time.monotonic() - self.paused_at
            self.paused_at = None
        elif not self.finished:
            self.paused_at, self.pause_choice, self.hover = time.monotonic(), 0, None
        self.refresh()

    def pause_action(self, choice):
        """Take a pause menu entry: carry on, or leave the Expedition for the menu."""
        if hud.PAUSE_ACTIONS[choice] == "CONTINUAR":
            self.toggle_pause()
        else:
            self.app.show_setup()

    def pause_key(self, event):
        """While paused the keys only move through the pause menu."""
        key = event.keysym
        if key in ("Return", "KP_Enter", "space"):
            self.pause_action(self.pause_choice)
            return "break"
        if key in ("Up", "Down", "Tab", "Left", "Right"):
            step = -1 if key in ("Up", "Left") else 1
            self.pause_choice = (self.pause_choice + step) % len(hud.PAUSE_ACTIONS)
            self.refresh()
        return "break"

    @property
    def facing(self):
        """Each racer keeps their own camera between Turns."""
        return self.facings[self.game.player]

    @facing.setter
    def facing(self, value):
        self.facings[self.game.player] = value

    # ---------------------------------------------------------------- actions

    def busy(self):
        """A walk, a look, an arrival, a Guardian's reaction or the pause is on screen; movement waits for it."""
        return (self.transition is not None or self.arrival_at is not None or self.reaction is not None
                or self.paused_at is not None)

    def _speak(self, now):
        """Advance the Guardian's lines: voice the new letters, start the clock once all are shown."""
        if self.dialogue is None:
            return
        letters = self.dialogue.voiced(self._voiced, now)
        self._voiced = self.dialogue.count(now)
        if letters:
            self.on_voice(letters)
        if self.dialogue.done(now):
            self.game.start_clock()

    def _walk(self, target, back):
        """Start walking towards a neighbouring room; its background is built meanwhile."""
        g = self.game
        index = [room.key for room in g.exits()].index(target)
        self.transition = {"type": "move", "start": self.now(), "duration": WALK, "target": target,
                           "player": g.player, "portal": self.portal_targets().index(index), "back": back}
        self.renderer.prepare(g.seed, target, sector_of(g.dungeon, g.dungeon.rooms[target]))

    def enter(self, door):
        g = self.game
        if self.busy() or g.status != "playing" or g.question or not g.can_leave():
            return
        exits = g.exits()
        if not isinstance(door, int) or not 0 <= door < len(exits):
            return
        self.app.audio.play("door")
        if self.app.effects.get():
            self._walk(exits[door].key, back=False)
            self.say("Abrindo passagem…", hud.PLAYER_INK[g.player])
            self.refresh()
        else:
            self._arrive(exits[door].key)

    def _arrive(self, target, back=False):
        exits = [room.key for room in self.game.exits()]
        mover = self.game.player
        moved = self.game.retreat() if back else self.game.enter(exits.index(target)) if target in exits else False
        if moved:
            event = self.game.event               # a chest's Buff, or a Trap, Mimic or Armed room's Debuff
            if event and event["effect"] != "heal":
                self.app.audio.play("chest" if event["effect"] in BUFFS else "trap")
            if self.app.effects.get():
                self.arrival_at, self.arrival_player = self.now(), mover
            self.resume_at = 0
            self.announce()
            self.refresh()

    def say(self, text, ink):
        self.message, self.message_ink, self.message_at = text, ink, self.now()

    def announce(self):
        """Say what the last move did: a Buff, a Debuff, a Guardian or nothing."""
        g, event = self.game, self.game.event
        if event:
            good = event["effect"] in ("haste", "insight", "heal", "ward", "hex", "swap")
            ink = hud.PLAYER_INK[event["player"] - 1] if good else hud.ALERT
            self.say(f"J{event['player']} · {event['text'][:1].upper()}{event['text'][1:]}", ink)
            self.popups.append([event["text"].upper(), ink, self.now()])
        else:
            self.say(ROOMS[g.current.kind][1] if g.question else "Caminho livre. A vez passa adiante.", hud.MUTED)

    def relative_portals(self, facing=None):
        return relative_portals(self.facing if facing is None else facing)

    def portal_targets(self, facing=None):
        """Match visible portals to actual adjacent rooms, never to a lane."""
        return portal_targets(self.game, self.facing if facing is None else facing)

    def look(self, turn):
        if self.busy() or self.game.status != "playing":
            return "break"
        target = (self.facing + turn) % 4
        if self.app.effects.get():
            self.transition = {"type": "look", "start": self.now(), "duration": .42,
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
        if self.busy() or g.active.came_from is None or g.status != "playing":
            return
        target = g.active.came_from
        self.app.audio.play("door")
        if self.app.effects.get():
            self._walk(target, back=True)
            self.refresh()
        else:
            self._arrive(target, back=True)

    def toggle_mute(self):
        self.app.audio.toggle_mute()
        self.refresh()

    def use_buff(self, target):
        if not self.busy() and self.game.use_buff(target):
            self.announce()
            self.refresh()

    def on_key(self, event):
        """Typing goes into the answer while a Guardian waits; Alt chords are shortcuts."""
        g = self.game
        if self.paused_at is not None:
            return self.pause_key(event)
        if g.status != "playing" or g.question is None or event.state & ALT_MASK:
            return None
        now = self.now()
        if self.dialogue and not self.dialogue.done(now):
            self.dialogue.complete()          # any key finishes the Guardian's lines at once
            self._speak(now)
            if event.keysym in ("Return", "KP_Enter"):
                self.refresh()
                return "break"
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
        self.app.audio.play("correct" if good else "wrong")
        author = result.get("player")
        ink = hud.PLAYER_INK[author - 1] if good and author else hud.ALERT
        if self.app.effects.get() and author:
            self.reaction = {"player": author - 1, "kind": "hit" if good else "miss", "start": self.now()}
        self.say((f"J{author} · " if author else "") + result["message"], ink)
        self.resume_at = self.now() + (1.3 if good else 3.0)
        caption = f"J{author}  ✓" if good else EFFECT_TEXT[result["penalty"]].upper()
        self.popups.append([caption, ink, self.now()])
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
        hint = "Armada!" if room.key in g.active.armed else "Liberada" if g.has_cleared(room) else ROOMS[kind][1]
        return f"{self.relative_portals()[portal][1]} · {ROOMS[kind][0]} · {hint}"

    def door_regions(self):
        """Native regions of the four portals: the three drawn doors and the 'behind' tab."""
        return list(self.renderer.regions) + [self.tab_rect or (-9, -9, -9, -9)]

    def _on_hud(self, native):
        return (hud.hit(self.regions, native) is not None
                or (self.box_rect and hud.inside(self.box_rect, native)) or native[1] >= self.cards_top)

    def door_at(self, event):
        native = self.renderer.to_native(event.x, event.y)
        if native is None:
            return None
        for portal, rect in enumerate(self.door_regions()):
            if hud.inside(rect, native) and (portal == 3 or not self._on_hud(native)):
                return portal if self.portal_targets()[portal] is not None else None
        return None

    def region_centre(self, action):
        """Canvas coordinates of a HUD control, for clicks and tests."""
        rect = dict(self.regions).get(action)
        return None if rect is None else self.renderer.centre(rect)

    def motion(self, event):
        if self.paused_at is not None:
            choice = self.pause_choice_at(event)
            self.canvas.configure(cursor="" if choice is None else "hand2")
            if choice is not None and choice != self.pause_choice:
                self.pause_choice = choice
                self.refresh()
            return
        self.hover = self.door_at(event)
        control = hud.hit(self.regions, self.renderer.to_native(event.x, event.y)) is not None
        self.canvas.configure(cursor="hand2" if control or (self.hover is not None and self.game.can_leave()
                                                             and not self.transition) else "")

    def pause_choice_at(self, event):
        action = hud.hit(self.regions, self.renderer.to_native(event.x, event.y))   # only the pause menu's while paused
        return None if action is None else action[1]

    def click(self, event):
        if self.paused_at is not None:
            choice = self.pause_choice_at(event)
            if choice is not None:
                self.pause_action(choice)
            return
        native = self.renderer.to_native(event.x, event.y)
        if native is None:
            return
        action = hud.hit(self.regions, native)
        if action == ("mute",):
            self.toggle_mute()                # even while the Guardian talks: muting must not skip its lines
            return
        now = self.now()
        if self.dialogue and not self.dialogue.done(now):
            self.dialogue.complete()          # a click finishes the Guardian's lines, like any key
            self._speak(now)
            self.refresh()
            return
        if action:
            if action[0] == "look":
                self.look(action[1])
            elif action[0] == "retreat":
                self.back()
            elif action[0] == "buff":
                self.use_buff(action[1])
            return
        if self.map_positions and hud.inside(self.map_rect, native):
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
            self.dialogue, self._voiced = None, 0
            if g.question is not None:
                taunt, question = hud.spoken_lines(g)
                # The Guardian starts talking once an arrival has settled, never in the dark.
                start = self.now() if self.arrival_at is None else self.arrival_at + ARRIVE
                self.dialogue = Dialogue(taunt + question, start)
                if not self.app.effects.get():
                    self.dialogue.complete()
        self._speak(self.now())
        if playing:     # paint every room the next move can reach while the screen is idle
            for room in g.exits():
                self.renderer.prepare(g.seed, room.key, sector_of(g.dungeon, room))
        if not playing and not self.finished:
            self.finished_at = self.now()
        if not playing:
            self.finished = True
            self.transition = None
            self.particles.clear()
            self.arrival_at = self.reaction = None
        self.update_players(self.now())
        self.draw_scene(self.now())

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

    def _minimap(self, facing):
        piece, centres, self.map_corridors, self.map_rivals, self.map_kinds, self._map_cell = hud.minimap(self.game, facing)
        self._map_centres = centres
        return piece

    def draw_scene(self, now):
        g = self.game
        effects = self.app.effects.get()
        playing = g.status == "playing"
        view = self.renderer
        if self.arrival_at is not None and (not effects or now - self.arrival_at >= ARRIVE):
            self.arrival_at = None
            if self.arrival_player != g.player:
                self.turn_changed_at = now   # only now fade over to whoever plays next
        if self.reaction is not None and (not effects or now - self.reaction["start"] >= REACT):
            if self.reaction["player"] != g.player:
                self.turn_changed_at = now
            self.reaction = None
        viewer, facing = g.player, self.facing
        opening = pan = zoom = lights = aside = None
        centre, fade, booting = (W // 2, H // 2), 0, False
        action = self.transition if effects else None
        if action and action["type"] == "look":
            pan = (min(W, int((now - action["start"]) / action["duration"] * W) // 16 * 16), action["turn"])
        elif action and action["portal"] == 3:
            fade = min(4, max(0, int((now - action["start"]) / action["duration"] * 5)))  # nothing to zoom into behind
        elif action:
            elapsed = now - action["start"]
            opening = (action["portal"], min(DOOR_STEPS, max(0, int(elapsed / OPEN * DOOR_STEPS))))
            step = int((elapsed - OPEN) / STEP) if elapsed >= OPEN else -1
            if step >= 0:
                steps = view.zoom_steps()
                zoom, fade = steps[min(step, len(steps) - 1)], max(0, min(4, step - 1))
                x0, y0, x1, y1 = view.regions[action["portal"]]
                centre = ((x0 + x1) // 2, (y0 + y1) // 2)
        elif self.arrival_at is not None:
            # The walker's new room arrives dark and one step in, then its tubes stutter on.
            age = max(0., now - self.arrival_at)
            viewer, facing = self.arrival_player, self.facings[self.arrival_player]
            zoom = view.zoom_steps()[min(1, len(view.zoom_steps()) - 1)] if age < .15 else None
            fade = max(0, 4 - int(age / .05))
            lights = next(state for until, state in ARRIVAL_LIGHTS if age < until)
            booting = age < .55
        elif self.reaction is not None:
            # The Guardian answers the answer in the room it happened, before anyone else plays.
            age = now - self.reaction["start"]
            viewer = self.reaction["player"]
            facing = self.facings[viewer]
        elif effects and now - self.turn_changed_at < TURN_FADE:
            fade = max(0, 4 - int((now - self.turn_changed_at) / TURN_FADE * 5))
        self.canvas.delete("all")
        scene = scene_for(g, facing, viewer)
        if booting and scene.guardian in ("dormant", "listening"):
            scene = replace(scene, guardian="dormant")
        if self.reaction is not None and scene.guardian:
            if self.reaction["kind"] == "miss" and scene.guardian != "cleared" and age < GLITCH:
                scene = replace(scene, guardian="glitch")
            elif self.reaction["kind"] == "hit" and scene.guardian == "cleared":
                aside = int(GUARDIAN_ASIDE * smooth(age / STEP_ASIDE))
        if self._scene is None or (scene.room_key, viewer) != (self._scene.room_key, self._scene_player):
            self.particles.clear()       # particles belong to the room they were born in
        self._scene, self._scene_player = scene, viewer
        lights = lights or ("dimmed" if effects and scene.flicker and now < self._flicker_until else "on")
        glitch = effects and now < self._glitch_until
        view.compose(scene, lights, glitch, opening, aside=aside)
        if pan:
            view.compose(scene_for(g, action["to"], viewer), lights, glitch, target=view.other)
        self.presented = {"viewer": viewer, "opening": opening, "zoom": zoom, "centre": centre, "fade": fade,
                          "pan": pan, "lights": lights, "guardian": scene.guardian, "aside": aside}
        view.clear_hud()
        if self.paused_at is not None:
            # The paused room stays behind a veil with only the pause menu over it, Question hidden.
            pause = self._put("pause", (self.pause_choice, g.player), lambda: hud.pause_panel(g, self.pause_choice))
            self.regions, self.box_rect, self.tab_rect = pause.regions, None, None
            view.present(None, centre, 3)
            self.hud = {"pause": pause.texts}
            return
        can_retreat = playing and g.active.came_from is not None and not self.transition
        players = tuple((p.position, p.exit_hits, p.lives, p.skip_next, p.held) for p in g.players)
        self.regions = []
        for i, piece in enumerate(self.edges):
            self._put(f"edge{i}", None, lambda piece=piece: piece)
            self.regions += piece.regions if playing else []
        badge = self._put("badge", (g.player, g.status, g.current.key), lambda: hud.badge(g))
        me = g.active
        mini = self._put("map", (g.player, frozenset(me.revealed), frozenset(me.visited), players, facing),
                         lambda: self._minimap(facing))
        self.map_rect = (mini.x, mini.y, mini.x + mini.pix.w - 1, mini.y + mini.pix.h - 1)
        self.map_positions = {key: view.to_canvas(*c) for key, c in self._map_centres.items()}
        self.map_radius = view.scale * max(1, self._map_cell // 2)
        muted = self.app.audio.muted
        mute = self._put("mute", muted, lambda: hud.mute_toggle(muted, mini.y + mini.pix.h + 2))
        self.regions += mute.regions if playing else []
        cards = self._put("cards", (g.player, g.status, players, can_retreat), lambda: hud.cards(g, can_retreat))
        self.regions += cards.regions
        self.cards_top = cards.y
        width = hud.BOX_WIDTH                   # a Question keeps the full width for typing; a note fits its text
        if g.question is not None and playing:
            revealing = self.dialogue is not None and not self.dialogue.done(now)
            lines = hud.question_lines(g, self.typed, int(now * 2) % 2 == 0,
                                       self.dialogue.shown(now) if revealing else None)
        else:
            width = None
            behind = self.door_label(self.hover) if self.hover is not None and playing else None
            # Hovering a door says what is behind it; otherwise the last note fades, leaving the room clear.
            lines = (hud.message_lines(behind, hud.TEXT) if behind
                     else hud.message_lines(self.message, self.message_ink) if now - self.message_at < MESSAGE_TIME
                     else [])
        bottom = cards.y - 2
        border = hud.PLAYER_INK[g.player] if playing else hud.GOLD
        box = self.box_rect = None
        if lines:
            box = self._put("box", (tuple(lines), bottom, border, width), lambda: hud.answer_box(lines, bottom, border, width))
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
        view.present(zoom, centre, fade, pan)
        self.hud = {"badge": badge.texts, "map": mini.texts, "cards": cards.texts, "box": [t for t, _ in lines],
                    "mute": mute.texts,
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
        now = self.now()
        # Let the winning moment land on screen, then hand over to the results.
        if self.finished and now - self.finished_at >= RESULTS_DELAY:
            self.job = None
            self.app.show_results(self.game)
            return
        if self.paused_at is not None:      # a frozen frame: no clock, no Guardian, no particles
            self.job = self.after(100, self.frame)
            return
        dt = min(.1, now - self.last_frame)
        self.last_frame = now
        self._speak(now)
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
        self.renderer.work()
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
        self.job = self.after(max(8, interval - int((self.now() - now) * 1000)), self.frame)


def main():
    try:    # without this, Windows stretches the window on displays scaled above 100% and blurs every pixel
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):       # not Windows, or older than Windows 8.1
        pass
    DungeonApp().mainloop()


if __name__ == "__main__":
    main()
