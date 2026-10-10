"""Tk integration checks for the full-window pixel screen. Requires a Tk display."""

import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock
from types import SimpleNamespace

from audio import Audio
import font
import hud
import pixel_view
from dungeon import DEBUFFS, EXIT_HITS, Expedition
from menu_ui import Setup
from records import Records
from scene import sector_of
from test_dungeon import make_combat
from dungeon_ui import (ALT_MASK, ARRIVE, MESSAGE_TIME, OPEN, REACT, STEP, STEP_ASIDE, TURN_FADE, WALK, DungeonApp,
                        ExpeditionScreen, PORTALS, ResultsScreen)
from room_art import DOOR_STEPS, GUARDIAN_ASIDE, H, W


class DungeonUITests(unittest.TestCase):
    def setUp(self):
        self.app = DungeonApp()
        self.app.effects.set(False)
        self.sounds = []          # the names played; None is a stop
        self.app.audio = Audio(lambda path: self.sounds.append(path and Path(path).stem))
        folder = tempfile.TemporaryDirectory()      # never the player's own Records
        self.addCleanup(folder.cleanup)
        self.app.records = Records(Path(folder.name) / "records.json")
        # Keep the test window off the user's visible desktop.
        self.app.geometry("1000x760+20000+20000")
        self.errors = []
        self.app.report_callback_exception = lambda *error: self.errors.append(error)
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        self.assertEqual(self.errors, [])

    def pump(self):
        self.app.after(120, self.app.quit)
        self.app.mainloop()

    def start_seeded(self, players=1):
        self.app.swap(ExpeditionScreen(self.app, make_combat(Expedition(players=players, seed=42))))
        self.app.update()
        return self.app.screen

    def key(self, screen, char="", keysym=None, state=0):
        return screen.on_key(SimpleNamespace(char=char, keysym=keysym or char, state=state))

    def type(self, screen, text):
        for ch in text:
            self.key(screen, ch, "space" if ch == " " else ch)

    def solve(self, screen):
        self.type(screen, screen.game.question["answer"])
        self.key(screen, "\r", "Return")
        self.app.update()

    def miss(self, screen, tier="easy"):
        screen.game.question_tier = tier  # Pin the Tier so the penalty is known.
        self.type(screen, "definitely wrong")
        self.key(screen, "\r", "Return")

    def click(self, screen, action):
        x, y = screen.region_centre(action)
        screen.click(SimpleNamespace(x=x, y=y))

    def win(self, screen):
        """Put the active racer one Room from the Exit with one hit left, then finish."""
        g = screen.game
        exit_key = g.dungeon.exit_key
        neighbour = next(iter(g.dungeon.connections[exit_key]))
        g.active.position = neighbour
        g.active.cleared.add(neighbour)
        g.active.exit_hits = EXIT_HITS - 1
        screen.enter([room.key for room in g.exits()].index(exit_key))
        self.solve(screen)

    # ---------------------------------------------------------------- the frame

    def test_frame_fills_the_window_at_an_integer_scale_with_black_bars(self):
        screen = self.start_seeded()
        view = screen.renderer
        self.assertEqual(view.scale, 3)
        self.assertEqual((view.display.width(), view.display.height()), (960, 600))
        self.assertEqual(view.origin, ((screen.canvas.winfo_width() - 960) // 2,
                                       (screen.canvas.winfo_height() - 600) // 2))
        self.app.geometry("1300x900+20000+20000")
        self.app.update()
        screen.refresh()
        self.assertEqual(view.scale, 4)
        self.assertEqual(view.display.width(), 1280)

    def test_every_hud_piece_stays_inside_the_frame_with_four_players(self):
        screen = self.start_seeded(players=4)
        screen.enter(0)
        for name, (_key, piece, _photo) in screen._layers.items():
            with self.subTest(piece=name):
                self.assertGreaterEqual(piece.x, 0)
                self.assertLessEqual(piece.x + piece.pix.w, hud.W)
                self.assertGreaterEqual(piece.y, 0)
                self.assertLessEqual(piece.y + piece.pix.h, hud.H)
        narrow = (hud.W - 4 - 112 - 3 * 3) // 3
        for i, lines in enumerate(screen.hud["cards"]):
            limit = 112 - 8 if i == screen.game.player else narrow - 8
            self.assertTrue(all(font.measure(line) <= limit for line in lines), lines)

    def test_every_question_in_the_bank_fits_the_box_and_long_ones_are_capped(self):
        root = Path(__file__).parent
        for tier in ("easy", "medium", "hard"):
            for q in json.loads((root / f"{tier}_questions.json").read_text(encoding="utf-8")):
                self.assertLessEqual(len(font.wrap(q["question"], hud.BOX_WIDTH - 8)), 2, q["question"])
        screen = self.start_seeded(players=4)
        screen.enter(0)
        screen.game.question = {"question": "Which discovery changed the way we understand the universe, "
                                            "and which scientist presented the explanation? " * 4,
                                "answer": "example"}
        screen.refresh()
        taunt = len(hud.spoken_lines(screen.game)[0])
        self.assertEqual(len(screen.hud["box"]), 1 + taunt + hud.MAX_QUESTION_LINES + 1)
        self.assertTrue(screen.hud["box"][taunt + hud.MAX_QUESTION_LINES].endswith("…"))
        badge_bottom = screen._layers["badge"][1].y + screen._layers["badge"][1].pix.h
        self.assertGreater(screen.box_rect[1], badge_bottom)

    # ---------------------------------------------------------------- movement

    def test_the_hud_stays_slim_and_notes_fade_to_leave_the_scene_clear(self):
        screen = self.start_seeded(players=2)
        self.assertEqual(len(screen.hud["badge"]), 1)
        cards = screen._layers["cards"][1]
        self.assertEqual((cards.pix.h, cards.y), (font.LINE + 3, H - font.LINE - 3))   # one line: nothing to do yet
        self.assertTrue(screen.hud["box"])                                             # the opening note...
        screen.message_at -= MESSAGE_TIME
        screen.refresh()
        self.assertEqual((screen.hud["box"], screen.box_rect), ([], None))             # ...fades away
        screen.enter(0)
        self.miss(screen)
        screen.game.players[1].held = "ward"
        screen.refresh()
        self.assertEqual(screen.hud["cards"][1], ["→ J2 ♥♥♥ ↓0", "◆ ESCUDO"])         # actions on a second line

    def test_escape_pauses_the_clocks_and_hides_the_question(self):
        screen = self.start_seeded()
        screen.enter(0)
        g, room = screen.game, screen.game.current.key
        left, elapsed, real = g.question_remaining, g.elapsed, time.monotonic()
        with mock.patch("dungeon_ui.time.monotonic", return_value=real):
            screen.toggle_pause()
        self.assertEqual(screen.hud, {"pause": ["PAUSA", f"{g.name.upper()} · SEED 0000-002A · 0:00", "",
                                                "CONTINUAR", "SAIR PARA O MENU"]})
        self.type(screen, "abc")                                   # typing waits for the game
        screen.navigate(1)
        self.assertEqual((screen.typed, g.current.key), ("", room))
        with mock.patch("dungeon_ui.time.monotonic", return_value=real + 60):
            self.assertAlmostEqual(g.question_remaining, left, delta=.5)   # a minute paused costs nothing
            self.click(screen, ("pause", 0))                          # CONTINUAR
            self.assertIsNone(screen.paused_at)
            self.assertAlmostEqual(g.question_remaining, left, delta=.5)
            self.assertAlmostEqual(g.elapsed, elapsed, delta=.5)
        self.assertIn("box", screen.hud)

    def test_the_pause_menu_leaves_for_the_menu_by_keyboard(self):
        screen = self.start_seeded()
        screen.toggle_pause()
        self.key(screen, keysym="Down")
        self.assertEqual(screen.pause_choice, 1)
        pending = screen.job
        self.key(screen, keysym="Return")
        self.app.update()
        self.assertIsInstance(self.app.screen, Setup)
        self.assertNotIn(pending, self.app.tk.call("after", "info"))

    def test_portals_match_compass_and_missing_doors_are_walls(self):
        screen = self.start_seeded()
        g = screen.game
        # Inspect every room, including branches, junctions and dead ends.
        for room in g.dungeon.rooms.values():
            g.active.position = room.key
            g.active.cleared.add(room.key)
            screen.refresh()
            for portal, (_, _, (dx, dy)) in enumerate(PORTALS):
                target = (room.x + dx, room.y + dy)
                exists = target in g.dungeon.connections[room.key]
                self.assertEqual(screen.door_label(portal) is not None, exists)
                bounds = screen.door_bounds()[portal]
                event = SimpleNamespace(x=(bounds[0]+bounds[2])/2*screen.canvas.winfo_width(),
                                        y=(bounds[1]+bounds[3])/2*screen.canvas.winfo_height())
                self.assertEqual(screen.door_at(event), portal if exists else None)
                if exists:
                    self.assertEqual(g.exits()[screen.portal_targets()[portal]].key, target)
                else:
                    screen.navigate(portal)
                    self.assertEqual(g.current.key, room.key)

    def test_edge_arrows_look_and_the_card_retreats(self):
        screen = self.start_seeded()
        g = screen.game
        self.click(screen, ("look", 1))
        self.assertEqual(screen.facing, 1)
        self.click(screen, ("look", -1))
        self.assertEqual(screen.facing, 0)
        self.assertIsNone(screen.region_centre(("retreat",)))
        screen.enter(0)
        self.click(screen, ("retreat",))
        self.assertEqual(g.current.key, (0, 0))

    def test_hovering_a_door_says_what_lies_behind_it(self):
        screen = self.start_seeded()
        portal = next(p for p in range(4) if screen.door_label(p))
        screen.hover = portal
        screen.refresh()
        self.assertEqual(screen.hud["box"][0], screen.door_label(portal))

    def test_map_only_shows_discovered_passages_and_clicks_adjacent_rooms(self):
        screen = self.start_seeded()
        g = screen.game
        initial = g.current.key
        me = g.active
        self.assertEqual(set(screen.map_positions), me.revealed)
        self.assertEqual(set(screen.map_kinds), me.revealed)
        expected = {(k, n) for k in me.revealed for n in g.dungeon.connections[k]
                    if k < n and n in me.revealed and (k in me.visited or n in me.visited)}
        self.assertEqual(screen.map_corridors, expected)
        room = g.exits()[0]
        x, y = screen.map_positions[room.key]
        screen.map_click(SimpleNamespace(x=x, y=y))
        self.assertEqual(g.current.key, room.key)
        x, y = screen.map_positions[initial]
        screen.map_click(SimpleNamespace(x=x, y=y))
        self.assertEqual(g.current.key, room.key)  # Cannot flee an active quiz.
        self.solve(screen)
        screen.map_click(SimpleNamespace(x=x, y=y))
        self.assertEqual(g.current.key, initial)
        self.assertIsNone(g.question)
        self.assertFalse(set(g.dungeon.rooms) == me.revealed)

    def test_map_shows_only_the_active_players_view_and_every_rival(self):
        screen = self.start_seeded(players=3)
        g = screen.game
        screen.enter(next(i for i, room in enumerate(g.exits()) if len(g.dungeon.connections[room.key]) > 1))
        self.solve(screen)
        self.assertEqual(g.player, 1)
        self.assertEqual(set(screen.map_positions), g.players[1].revealed)
        self.assertNotEqual(g.players[0].revealed, g.players[1].revealed)
        self.assertEqual([i for i, _ in screen.map_rivals], [0, 2])
        self.assertTrue(screen.hud["badge"][0].startswith("J2"))
        self.assertIn("0000-002A", screen.hud["map"])

    def test_shortcuts_are_removed_and_rebound_when_restarting(self):
        screen = self.start_seeded()
        old_bindings = screen.nav_bindings[:]
        for sequence, binding in old_bindings:
            self.assertIn(binding, self.app.bind(sequence))
        self.app.show_setup()
        for sequence, binding in old_bindings:
            self.assertNotIn(binding, self.app.bind(sequence))
        new = self.start_seeded()
        for sequence, binding in new.nav_bindings:
            self.assertIn(binding, self.app.bind(sequence))

    # ---------------------------------------------------------------- typing answers

    def test_typing_backspace_and_enter_answer_the_question(self):
        screen = self.start_seeded()
        g = screen.game
        self.type(screen, "ação")
        self.assertEqual(screen.typed, "")                      # nothing to answer yet
        screen.enter(0)
        self.type(screen, "ação 1")
        self.assertEqual(screen.typed, "ação 1")
        self.assertTrue(screen.hud["box"][-1].startswith("> ação 1"))
        self.key(screen, "", "BackSpace")
        self.assertEqual(screen.typed, "ação ")
        self.key(screen, "x", "x", state=ALT_MASK)               # Alt chords are shortcuts
        self.assertEqual(screen.typed, "ação ")
        self.type(screen, "w" * 80)
        self.assertLessEqual(font.measure(f"> {screen.typed}_"), hud.BOX_WIDTH - 8)
        for _ in screen.typed:
            self.key(screen, "", "BackSpace")
        self.solve(screen)
        self.assertTrue(g.has_cleared(g.current))
        self.assertEqual(screen.typed, "")

    def test_submission_retry_and_restart_cancel_callbacks(self):
        screen = self.start_seeded()
        g = screen.game
        screen.enter(next(i for i, room in enumerate(g.exits()) if len(g.dungeon.connections[room.key]) > 1))
        self.solve(screen)
        self.assertTrue(g.has_cleared(g.current))
        screen.enter(next(i for i, room in enumerate(g.exits()) if not g.has_cleared(room)))
        screen.game.question_deadline = screen.game.clock() - 1
        self.pump()
        self.assertIsNone(screen.game.question)
        screen.resume_at = screen.game.clock() - 1
        self.pump()
        self.assertIsNotNone(screen.game.question)
        pending = screen.job
        self.app.show_setup()
        self.assertNotIn(pending, self.app.tk.call("after", "info"))
        self.app.start(3, 1)
        self.pump()

    def test_winning_finishes_ui_once(self):
        screen = self.start_seeded()
        self.win(screen)
        self.pump()
        self.assertTrue(screen.finished)
        self.assertEqual((screen.game.status, screen.game.winner), ("won", 0))
        self.assertIsNone(self.key(screen, "a"))
        self.assertEqual(screen.regions, [])
        self.assertIn("escapou", screen.hud["box"][0].lower())

    def test_looking_rotates_portals_without_moving_or_erasing_answer(self):
        screen = self.start_seeded()
        screen.enter(0)
        self.type(screen, "my unfinished answer")
        g = screen.game
        position, question, deadline = g.current.key, g.question, g.question_deadline
        for facing in (1, 2, 3, 0):
            screen.look(1)
            self.assertEqual(screen.facing, facing)
            self.assertEqual(g.current.key, position)
            self.assertIs(g.question, question)
            self.assertEqual(g.question_deadline, deadline)
            self.assertEqual(screen.typed, "my unfinished answer")
            for i, (_, _, (dx, dy)) in enumerate(screen.relative_portals()):
                target = screen.portal_targets()[i]
                if target is not None:
                    self.assertEqual(g.exits()[target].key, (g.current.x+dx, g.current.y+dy))

    # ---------------------------------------------------------------- transitions

    def test_door_and_walk_transition_only_enters_once_at_arrival(self):
        screen = self.start_seeded()
        self.app.effects.set(True)
        origin = screen.game.current.key
        target = screen.game.exits()[0].key
        screen.enter(0)
        action = screen.transition
        self.assertEqual(action["type"], "move")
        self.assertEqual(screen.game.current.key, origin)
        self.assertIsNone(screen.game.question)
        screen.enter(1)
        screen.look(1)
        screen.back()
        self.assertIs(screen.transition, action)
        for fraction in (.1, .5, .9):
            screen.draw_scene(action["start"] + action["duration"]*fraction)
        screen.advance_transition(action["start"] + action["duration"] + .01)
        self.assertEqual(screen.game.current.key, target)
        self.assertIsNotNone(screen.game.question)
        self.assertEqual(screen.game.active.came_from, origin)
        self.assertIsNone(screen.transition)

    def test_motion_toggle_completes_turn_and_timeout_cancels_movement(self):
        screen = self.start_seeded()
        self.app.effects.set(True)
        screen.look(-1)
        action = screen.transition
        screen.draw_scene(action["start"] + .1)
        screen.draw_scene(action["start"] + .25)
        self.app.effects.set(False)
        screen.advance_transition(action["start"])
        self.assertEqual(screen.facing, 3)
        self.assertIsNone(screen.transition)

    def test_timeout_that_passes_the_turn_cancels_the_retreat_walk(self):
        screen = self.start_seeded(players=2)
        g = screen.game
        screen.enter(0)
        room = g.current.key
        self.app.effects.set(True)
        screen.back()
        self.assertEqual(screen.transition["player"], 0)
        g.question_deadline = g.clock() - 1
        self.pump()
        self.assertIsNone(screen.transition)
        self.assertEqual((g.player, g.players[0].position), (1, room))

    def walk_in(self, screen, portal=None):
        """Start walking through a door that leads on; return the transition."""
        self.app.effects.set(True)
        door = screen.portal_targets()[portal] if portal is not None else next(
            t for p, t in enumerate(screen.portal_targets()) if t is not None and p != 3)
        screen.enter(door)
        return screen.transition

    def test_walk_opens_the_door_then_zooms_in_steps_and_fades(self):
        screen = self.start_seeded()
        action = self.walk_in(screen)
        start, portal = action["start"], action["portal"]
        steps = []
        for t in (0, OPEN / 3, OPEN * 2 / 3, OPEN - .001):
            screen.draw_scene(start + t)
            self.assertIsNone(screen.presented["zoom"])
            steps.append(screen.presented["opening"][1])
        self.assertEqual(steps, sorted(steps))
        self.assertEqual((steps[0], screen.presented["opening"][0]), (0, portal))
        zooms = screen.renderer.zoom_steps()
        self.assertEqual(zooms, [3, 4, 5, 6, 8, 10])
        x0, y0, x1, y1 = screen.renderer.regions[portal]
        for k, zoom in enumerate(zooms):
            screen.draw_scene(start + OPEN + k * STEP + .001)
            self.assertEqual(screen.presented["opening"], (portal, DOOR_STEPS))
            self.assertEqual(screen.presented["zoom"], zoom)
            self.assertEqual(screen.presented["fade"], max(0, min(4, k - 1)))
            self.assertEqual(screen.presented["centre"], ((x0 + x1) // 2, (y0 + y1) // 2))
        self.assertAlmostEqual(action["duration"], WALK)

    def test_arrival_shows_the_walkers_room_dark_then_lit_before_the_turn_passes(self):
        screen = self.start_seeded(players=2)
        g = screen.game
        action = self.walk_in(screen)
        g.active.cleared.add(action["target"])         # an already-Cleared room ends the Turn at once
        screen.advance_transition(action["start"] + WALK + .01)
        self.assertEqual(g.player, 1)
        arrived = screen.arrival_at
        screen.draw_scene(arrived + .01)
        self.assertEqual((screen.presented["viewer"], screen.presented["lights"]), (0, "off"))
        self.assertEqual((screen.presented["zoom"], screen.presented["fade"]), (4, 4))
        self.assertEqual(screen._scene.room_key, action["target"])
        screen.draw_scene(arrived + .45)
        self.assertEqual((screen.presented["lights"], screen.presented["fade"]), ("dimmed", 0))
        self.assertIsNone(screen.region_centre(("look", 1)) and screen.look(1) and None)
        self.assertEqual(screen.facing, 0)                  # nobody turns while the walker arrives
        screen.draw_scene(arrived + ARRIVE + .01)
        self.assertIsNone(screen.arrival_at)
        self.assertEqual(screen.presented["viewer"], 1)
        self.assertEqual(screen.presented["fade"], 4)       # then a quick fade to the next player's room
        screen.draw_scene(arrived + ARRIVE + TURN_FADE + .02)
        self.assertEqual(screen.presented["fade"], 0)

    def test_a_booting_guardian_wakes_only_after_the_lights(self):
        screen = self.start_seeded()
        action = self.walk_in(screen)
        screen.advance_transition(action["start"] + WALK + .01)
        self.assertIsNotNone(screen.game.question)
        screen.draw_scene(screen.arrival_at + .3)
        self.assertEqual(screen.presented["guardian"], "dormant")
        screen.draw_scene(screen.arrival_at + .58)
        self.assertEqual(screen.presented["guardian"], "listening")

    def test_looking_pans_from_one_facing_to_the_next(self):
        screen = self.start_seeded()
        self.app.effects.set(True)
        screen.look(1)
        action = screen.transition
        offsets = []
        for t in (.05, .2, .4):
            screen.draw_scene(action["start"] + t)
            offset, turn = screen.presented["pan"]
            self.assertEqual((turn, offset % 16), (1, 0))
            offsets.append(offset)
        self.assertEqual(offsets, sorted(offsets))
        screen.advance_transition(action["start"] + action["duration"] + .01)
        self.assertEqual(screen.facing, 1)

    def test_every_room_the_next_move_can_reach_is_painted_ahead(self):
        screen = self.start_seeded()
        g, view = screen.game, screen.renderer
        reachable = {(g.seed, room.key, sector_of(g.dungeon, room)) for room in g.exits()}
        self.assertLessEqual(reachable, set(view._jobs) | set(view._ready))
        view.work(budget=60)                          # idle frames finish them, so arriving never stalls
        self.assertLessEqual(reachable, set(view._ready))

    def test_the_next_room_is_built_while_the_door_opens(self):
        screen = self.start_seeded()
        action = self.walk_in(screen)
        g = screen.game
        room = g.dungeon.rooms[action["target"]]
        key = (g.seed, room.key, sector_of(g.dungeon, room))
        self.assertIn(key, screen.renderer._jobs)
        for _ in range(400):                                   # a frame's worth of painting at a time
            if key in screen.renderer._ready:
                break
            screen.renderer.work()
        self.assertIn(key, screen.renderer._ready)
        self.assertNotIn(key, screen.renderer._jobs)

    def test_an_unwritable_temp_folder_falls_back_to_tks_own_veils(self):
        screen = self.start_seeded()
        with tempfile.NamedTemporaryFile(delete=False) as blocker:   # a file where the folder should be
            pass
        self.addCleanup(Path(blocker.name).unlink)
        with mock.patch("pixel_view.tempfile.gettempdir", return_value=blocker.name):
            self.assertEqual(pixel_view._veil(2, 7), "gray50")
            screen.renderer.present(fade=2)                          # draws instead of raising

    def test_reduced_motion_cuts_every_transition(self):
        screen = self.start_seeded(players=2)
        g = screen.game
        screen.enter(0)
        self.assertIsNone(screen.transition)
        self.assertIsNone(screen.arrival_at)
        self.assertEqual({k: screen.presented[k] for k in ("zoom", "fade", "opening", "pan")},
                         {"zoom": None, "fade": 0, "opening": None, "pan": None})
        screen.look(1)
        self.assertEqual((screen.facing, screen.presented["pan"]), (1, None))
        self.miss(screen)
        self.assertEqual((g.player, screen.presented["fade"]), (1, 0))

    def face_guardian(self, players=1):
        """With effects on, put the active player before a Guardian without a walk."""
        screen = self.start_seeded(players=players)
        self.app.effects.set(True)
        screen.game.enter(0)
        screen.refresh()
        return screen

    def test_the_guardian_speaks_letter_by_letter_and_the_clock_waits(self):
        screen = self.face_guardian()
        g = screen.game
        voiced = []
        screen.on_voice = voiced.append
        start = screen.dialogue.start
        screen.draw_scene(start + .1)
        taunt, question = hud.spoken_lines(g)
        box = screen.hud["box"]
        self.assertTrue(taunt[0].startswith(box[1]) and box[1] != taunt[0])   # the Taunt is still arriving
        self.assertEqual(box[-1], "")                                          # no answer line yet
        self.assertIsNone(g.question_deadline)
        self.key(screen, "\r", "Return")                                      # Enter finishes the lines...
        self.assertIsNotNone(g.question_deadline)                              # ...and starts the clock
        self.assertIsNotNone(g.question)                                       # without answering
        self.assertEqual(screen.hud["box"][1:-1], taunt + question)
        self.assertTrue(screen.hud["box"][-1].startswith("> "))
        self.assertGreater(sum(voiced), 0)
        self.solve(screen)
        self.assertTrue(g.has_cleared(g.current))

    def test_a_click_finishes_the_guardians_lines_without_moving(self):
        screen = self.face_guardian()
        g = screen.game
        room = g.current.key
        x0, y0, x1, y1 = screen.renderer.regions[1]
        x, y = screen.renderer.to_canvas((x0 + x1) // 2, (y0 + y1) // 2)
        screen.click(SimpleNamespace(x=x, y=y))
        self.assertTrue(screen.dialogue.done(0))
        self.assertIsNotNone(g.question_deadline)
        self.assertEqual(g.current.key, room)

    def test_reduced_motion_shows_every_word_and_starts_the_clock(self):
        screen = self.start_seeded()
        screen.enter(0)
        g = screen.game
        taunt, question = hud.spoken_lines(g)
        self.assertEqual(screen.hud["box"][1:-1], taunt + question)
        self.assertIsNotNone(g.question_deadline)

    def test_a_listening_guardians_eye_takes_the_answering_players_colour(self):
        screen = self.start_seeded(players=2)
        g = screen.game
        screen.enter(0)
        self.miss(screen)
        screen.enter(0)
        self.assertEqual((g.player, screen._scene.player, screen.presented["guardian"]), (1, 1, "listening"))
        self.assertIn(("guardian", "listening", hud.PLAYER_INK[1]), screen.renderer._photos)

    def test_a_miss_glitches_the_guardian_in_the_answerers_room_before_the_turn_passes(self):
        screen = self.face_guardian(players=2)
        g = screen.game
        room = g.current.key
        self.miss(screen)
        self.assertEqual(g.player, 1)
        start = screen.reaction["start"]
        screen.draw_scene(start + .1)
        self.assertEqual((screen.presented["viewer"], screen.presented["guardian"]), (0, "glitch"))
        self.assertEqual(screen._scene.room_key, room)
        self.assertTrue(screen.busy())
        screen.draw_scene(start + .7)
        self.assertEqual(screen.presented["guardian"], "dormant")
        screen.draw_scene(start + REACT + .01)
        self.assertIsNone(screen.reaction)
        self.assertEqual((screen.presented["viewer"], screen.presented["fade"]), (1, 4))

    def test_a_cleared_guardian_steps_aside(self):
        screen = self.face_guardian()
        screen.dialogue.complete()
        self.solve(screen)
        start = screen.reaction["start"]
        asides = []
        for t in (0, .1, .25, .39):
            screen.draw_scene(start + t)
            asides.append(screen.presented["aside"])
        self.assertEqual(asides, sorted(asides))
        self.assertEqual((asides[0], screen.presented["guardian"]), (0, "cleared"))
        screen.draw_scene(start + STEP_ASIDE + .05)
        self.assertEqual(screen.presented["aside"], GUARDIAN_ASIDE)

    # ---------------------------------------------------------------- sound

    def test_the_guardian_blips_as_its_letters_appear(self):
        screen = self.face_guardian()
        start = screen.dialogue.start
        self.sounds.clear()
        screen._speak(start + .5)
        screen._speak(start + .5)                     # no new letters, no blip
        self.assertEqual(self.sounds, ["blip"])

    def test_moves_chests_and_traps_play_their_sounds(self):
        g = make_combat(Expedition(players=1, seed=42))
        chest, trap = g.exits()[:2]
        chest.kind, chest.effect = "treasure", "ward"
        trap.kind, trap.effect = "trap", "life"
        self.app.swap(ExpeditionScreen(self.app, g))
        screen = self.app.screen
        screen.enter(0)
        screen.back()
        screen.enter(1)
        screen.back()
        screen.enter(0)                               # a chest only opens on the first visit
        self.assertEqual(self.sounds, ["door", "chest", "door", "door", "trap", "door", "door"])

    def test_answers_play_correct_or_wrong(self):
        screen = self.start_seeded()
        g = screen.game
        screen.enter(0)
        self.solve(screen)
        screen.enter(next(i for i, room in enumerate(g.exits()) if room.kind == "combat"))
        self.miss(screen)
        # Reduced motion shows the Guardian's lines at once: one blip for all of them.
        self.assertEqual(self.sounds, ["door", "blip", "correct", "door", "blip", "wrong"])

    def test_the_hud_mute_toggle_silences_everything_at_once(self):
        screen = self.face_guardian()
        self.assertEqual(screen.hud["mute"], ["SOM ●"])
        self.sounds.clear()
        self.click(screen, ("mute",))
        self.assertEqual((self.app.audio.muted, screen.hud["mute"]), (True, ["SOM ○"]))
        self.assertFalse(screen.dialogue.done(time.monotonic()))   # muting does not skip the Guardian's lines
        screen._speak(screen.dialogue.start + .5)
        self.app.effects.set(False)                   # no Guardian reaction holding the next move
        self.solve(screen)
        screen.enter(0)
        self.assertEqual(self.sounds, [None])        # the stop, then silence
        self.click(screen, ("mute",))
        self.assertEqual(screen.hud["mute"], ["SOM ●"])
        self.assertIn("<Alt-m>", [sequence for sequence, _ in screen.nav_bindings])

    def test_ambient_particles_live_only_with_effects_and_in_their_room(self):
        screen = self.start_seeded()
        self.pump()
        self.assertEqual(screen.particles, [])                 # reduced motion: nothing drifts
        self.app.effects.set(True)
        self.pump()
        self.assertTrue(screen.particles)                      # dust, at least, fills the air
        screen.enter(0)
        screen.advance_transition(screen.transition["start"] + 1)
        screen.draw_scene(0)
        self.assertEqual(screen.particles, [])                 # a new room starts clean
        self.app.effects.set(False)
        self.pump()
        self.assertEqual(screen.particles, [])

    # ---------------------------------------------------------------- players and HUD texts

    def active_cards(self, screen):
        return [i for i, lines in enumerate(screen.hud["cards"]) if lines[0].startswith("→")]

    def test_player_identity_tracks_full_rotation_and_result_author(self):
        screen = self.start_seeded(players=4)
        g = screen.game
        for player in range(4):
            screen.enter(0)
            self.assertEqual(g.player, player)
            self.assertEqual(self.active_cards(screen), [player])
            self.assertTrue(screen.hud["badge"][0].startswith(f"J{player+1} · "))
            self.assertTrue(screen.hud["box"][0].startswith(f"J{player+1} ·"))
            self.miss(screen)  # An easy miss: a medium one would skip this player's next Turn.
            self.assertTrue(screen.message.startswith(f"J{player+1} ·"))
            self.assertEqual(g.player, (player+1) % 4)
        self.assertEqual(screen.game.player, 0)

    def test_unvisited_rooms_are_silhouettes_and_chests_hide_mimics(self):
        g = make_combat(Expedition(players=1, seed=42))
        doors = g.exits()
        doors[0].kind, doors[0].effect = "mimic", "life"
        doors[1].kind = "trap"
        self.app.swap(ExpeditionScreen(self.app, g))
        self.app.update()
        screen = self.app.screen
        self.assertEqual(set(screen.map_kinds.values()) - {"entrance"}, {"treasure", "unknown"})
        labels = [screen.door_label(p) for p in range(4) if screen.door_label(p)]
        self.assertTrue(any("Tesouro" in text for text in labels))
        self.assertTrue(any("Desconhecida" in text for text in labels))
        self.assertFalse(any("Mímico" in text or "Armadilha" in text for text in labels))
        screen.enter(0)
        self.assertIn("J1 · −1 vida", screen.message)
        self.assertIn("MÍMICO", screen.hud["badge"][0])

    def test_held_buffs_show_on_cards_and_targets_are_opponents_only(self):
        screen = self.start_seeded(players=3)
        g = screen.game
        self.assertIsNone(screen.region_centre(("buff", 1)))
        g.players[0].held, g.players[2].held = "swap", "ward"
        screen.refresh()
        self.assertIn("◆ TROCA", screen.hud["cards"][0][-1])
        self.assertIn("◆", screen.hud["cards"][2][0])
        self.assertIsNone(screen.region_centre(("buff", 0)))
        self.assertIsNotNone(screen.region_centre(("buff", 1)))
        target = g.players[2].position = g.exits()[0].key
        self.click(screen, ("buff", 2))
        self.assertEqual(g.players[0].position, target)
        self.assertIn("J1 · Trocou de lugar com J3", screen.message)

    def test_a_player_left_before_a_guardian_is_asked_at_the_start_of_their_turn(self):
        screen = self.start_seeded(players=2)
        g = screen.game
        screen.enter(0)
        self.miss(screen)
        screen.resume_at = 0
        neighbour = g.exits()[0]
        g.active.cleared.add(neighbour.key)
        screen.enter(0)  # Player 2 walks into a Room already Cleared: no result to wait for.
        self.assertEqual((g.player, g.question), (0, None))
        self.pump()
        self.assertIsNotNone(g.question)

    def test_alone_a_lost_turn_shows_as_a_life_and_an_armed_room_is_marked(self):
        screen = self.start_seeded()
        g = screen.game
        screen.enter(0)
        room = g.current.key
        g.question_tier = "medium"
        screen.refresh()
        self.assertIn("ERRO: −1 VIDA", screen.hud["box"][0])
        self.miss(screen, "hard")
        screen.refresh()
        door = next(p for p, target in enumerate(screen.portal_targets())
                    if target is not None and g.exits()[target].key == room)
        self.assertTrue(screen.door_label(door).endswith("Armada!"))
        self.sounds.clear()
        draw = g.rng.choice                                                    # pin the sprung Debuff
        g.rng.choice = lambda options: "life" if options == DEBUFFS else draw(options)
        screen.enter(screen.portal_targets()[door])
        self.assertIn("trap", self.sounds)                                     # the Armed room springs
        self.assertIn("Sala armada: −1 vida", screen.message)

    def test_tier_lives_and_penalties_are_shown(self):
        screen = self.start_seeded(players=2)
        g = screen.game
        screen.enter(0)
        g.question_tier = "medium"
        self.pump()
        self.assertIn("MÉDIA · ERRO: PERDE A PRÓXIMA VEZ", screen.hud["box"][0])
        self.assertIn("J1 ♥♥♥", screen.hud["cards"][0][0])
        answer = g.question["answer"]
        self.miss(screen, "easy")
        self.assertIn(f"Resposta: {answer} · −1 vida", screen.message)
        self.assertIn("♥♥♡", screen.hud["cards"][0][0])
        screen.enter(0)
        self.miss(screen, "medium")
        self.assertIn("⏸", screen.hud["cards"][1][0])

    def test_correct_answer_credits_the_answerer_and_highlights_next(self):
        screen = self.start_seeded(players=2)
        screen.enter(0)
        self.solve(screen)
        self.assertIn(screen.game.players[0].position, screen.game.players[0].cleared)
        self.assertIn("J1", screen.message)
        self.assertTrue(screen.hud["badge"][0].startswith("J2"))
        self.assertEqual(self.active_cards(screen), [1])
        self.assertEqual(screen.typed, "")

    def test_timeout_rotates_identity_and_finished_run_has_no_active_player(self):
        screen = self.start_seeded(players=2)
        screen.enter(0)
        screen.game.question_deadline = screen.game.clock() - 1
        self.pump()
        self.assertEqual(screen.game.player, 1)
        self.assertEqual(self.active_cards(screen), [1])
        self.win(screen)
        self.pump()
        self.assertIsNone(screen._active_player)
        self.assertEqual(self.active_cards(screen), [])
        self.assertIn("★", screen.hud["cards"][1][0])
        self.assertEqual(screen.hud["badge"][0], "J2 VENCEU")

    # ---------------------------------------------------------------- results

    def finish_and_show_results(self, players=2):
        screen = self.start_seeded(players=players)
        self.win(screen)
        self.pump()
        self.assertIs(self.app.screen, screen)  # The winning room stays up for a moment.
        pending = screen.job
        screen.finished_at -= 10
        self.pump()
        self.assertNotIn(pending, self.app.tk.call("after", "info"))
        return screen.game, self.app.screen

    def test_results_name_the_winner_in_their_colour_with_difficulty_seed_and_players(self):
        game, results = self.finish_and_show_results(players=4)
        self.assertIsInstance(results, ResultsScreen)
        panel = results.panel
        self.assertEqual(panel.texts[1], "JOGADOR 1 ESCAPOU")
        self.assertIn(f"{game.name.upper()} · SEED 0000-002A", panel.texts[2])  # Seed 42.
        winner_row = {panel.pix.get(x, y) for x in range(panel.pix.w) for y in range(2 + font.LINE, 2 + 2 * font.LINE)}
        self.assertIn(hud.PLAYER_INK[0], winner_row)
        self.assertEqual(sum(text.startswith(f"J{i + 1} ") for text in panel.texts for i in range(4)), 4)
        self.assertTrue(0 <= panel.x and panel.x + panel.pix.w <= W and 0 <= panel.y and panel.y + panel.pix.h <= H)

    def test_a_winning_time_becomes_a_record_with_its_rank(self):
        game, results = self.finish_and_show_results()
        self.assertIn("★ NOVO RECORDE · #1", results.panel.texts)
        best = self.app.records.top(game.difficulty)[0]
        self.assertEqual((best["seed"], best["players"]), (42, 2))
        self.assertAlmostEqual(best["seconds"], game.elapsed)

    def test_a_slower_time_announces_no_record(self):
        for _ in range(5):
            self.app.records.submit(Expedition().difficulty, 0, 1, 1)
        game, results = self.finish_and_show_results()
        self.assertIsNone(results.rank)
        self.assertFalse(any("RECORDE" in text for text in results.panel.texts))

    def test_rematch_on_the_same_seed_rebuilds_the_same_dungeon(self):
        game, results = self.finish_and_show_results(players=3)
        results.on_key(SimpleNamespace(keysym="Return"))      # the rematch is picked first
        self.app.update()
        rematch = self.app.screen.game
        self.assertEqual((rematch.seed, rematch.difficulty, len(rematch.players)), (42, game.difficulty, 3))
        self.assertEqual(rematch.dungeon.connections, game.dungeon.connections)
        self.assertEqual(rematch.status, "playing")

    def test_new_seed_by_click_leaves_no_old_callbacks(self):
        game, results = self.finish_and_show_results()
        x, y = results.region_centre(1)
        results.motion(SimpleNamespace(x=x, y=y))
        self.assertEqual(results.selected, 1)
        results.click(SimpleNamespace(x=x, y=y))
        self.app.update()
        self.assertNotEqual(self.app.screen.game.seed, game.seed)
        pending = self.app.screen.job
        self.app.show_setup()
        self.app.update()
        self.assertNotIn(pending, self.app.tk.call("after", "info"))

    def test_the_menu_is_reached_by_keyboard(self):
        game, results = self.finish_and_show_results()
        for keysym, selected in (("Right", 1), ("Tab", 2), ("Right", 0), ("Left", 2)):
            results.on_key(SimpleNamespace(keysym=keysym))
            self.assertEqual(results.selected, selected)
        results.on_key(SimpleNamespace(keysym="Return"))
        self.app.update()
        self.assertIsInstance(self.app.screen, Setup)


if __name__ == "__main__":
    unittest.main()
