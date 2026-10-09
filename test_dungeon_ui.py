"""Tk integration checks. Requires an available Tk display."""

import unittest
import random
from types import SimpleNamespace

from dungeon import Dungeon
from dungeon_ui import DungeonApp, Expedition, PORTALS


class DungeonUITests(unittest.TestCase):
    def setUp(self):
        self.app = DungeonApp()
        self.app.effects.set(False)
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
        self.app.swap(Expedition(self.app, Dungeon(players=players, rng=random.Random(42))))
        self.app.update()
        return self.app.screen

    def solve(self, screen):
        screen.answer.insert(0, screen.game.question["answer"])
        screen.submit()
        self.app.update()

    def test_portals_match_compass_and_missing_doors_are_walls(self):
        screen = self.start_seeded()
        g = screen.game
        # Inspect every room, including branches, junctions and dead ends.
        for room in g.rooms.values():
            g.current = room
            room.cleared = True
            screen.refresh()
            self.app.update()
            for portal, (_, _, (dx, dy)) in enumerate(PORTALS):
                target = (room.x + dx, room.y + dy)
                exists = target in g.connections[room.key]
                self.assertEqual(str(screen.door_buttons[portal].cget("state")),
                                 "normal" if exists else "disabled")
                bounds = screen.door_bounds()[portal]
                event = SimpleNamespace(x=(bounds[0]+bounds[2])/2*screen.scene.winfo_width(),
                                        y=(bounds[1]+bounds[3])/2*screen.scene.winfo_height())
                self.assertEqual(screen.door_at(event), portal if exists else None)
                if exists:
                    self.assertEqual(g.exits()[screen.portal_targets()[portal]].key, target)
                else:
                    screen.navigate(portal)
                    self.assertEqual(g.current.key, room.key)

    def test_map_only_shows_discovered_passages_and_clicks_adjacent_rooms(self):
        screen = self.start_seeded()
        g = screen.game
        initial = g.current.key
        self.assertEqual(set(screen.map_positions), g.revealed)
        self.assertEqual(len(screen.map.find_withtag("room")), len(g.revealed))
        expected = sum(1 for k in g.revealed for n in g.connections[k]
                       if k < n and n in g.revealed and (k in g.visited or n in g.visited))
        self.assertEqual(len(screen.map.find_withtag("corridor")), expected)
        room = g.exits()[0]
        x, y = screen.map_positions[room.key]
        screen.map_click(SimpleNamespace(x=x, y=y))
        self.assertEqual(g.current.key, room.key)
        self.app.update()
        x, y = screen.map_positions[initial]
        screen.map_click(SimpleNamespace(x=x, y=y))
        self.assertEqual(g.current.key, room.key)  # Cannot flee an active quiz.
        self.solve(screen)
        score = g.scores[:]
        screen.map_click(SimpleNamespace(x=x, y=y))
        self.assertEqual(g.current.key, initial)
        self.assertEqual(g.scores, score)
        self.assertIsNone(g.question)
        self.assertFalse(set(g.rooms) == g.revealed)

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

    def test_long_question_keeps_controls_inside_minimum_window(self):
        screen = self.start_seeded(players=4)
        screen.enter(0)
        screen.game.question = {"question": "Which discovery changed the way we understand the universe, "
                               "and which scientist presented the explanation? " * 3,
                               "answer": "example"}
        screen.refresh()
        self.app.update()
        for widget in (screen.q_text, screen.answer, screen.submit_btn, screen.feedback,
                       *screen.door_buttons):
            with self.subTest(widget=str(widget)):
                self.assertTrue(widget.winfo_ismapped())
                self.assertGreaterEqual(widget.winfo_height(), widget.winfo_reqheight())
                self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                     self.app.winfo_rooty() + self.app.winfo_height())

    def test_four_player_controls_fit_minimum_window(self):
        self.app.start(1, 4)
        self.app.update()
        screen = self.app.screen
        for widget in screen.map.master.winfo_children():
            self.assertTrue(widget.winfo_ismapped())
            self.assertGreaterEqual(widget.winfo_height(), widget.winfo_reqheight())
        for widget in (screen.answer, screen.submit_btn, screen.feedback):
            bottom = widget.winfo_rooty() + widget.winfo_height()
            self.assertLessEqual(bottom, self.app.winfo_rooty() + self.app.winfo_height())

    def test_submission_retry_and_restart_cancel_callbacks(self):
        screen = self.start_seeded()
        screen.enter(1)
        self.solve(screen)
        self.assertTrue(screen.game.current.cleared)
        screen.enter(next(i for i, room in enumerate(screen.game.exits()) if not room.cleared))
        screen.game.question_deadline = screen.game.clock() - 1
        self.pump()
        self.assertEqual(screen.game.lives, 4)
        self.assertIsNone(screen.game.question)
        screen.resume_at = screen.game.clock() - 1
        self.pump()
        self.assertIsNotNone(screen.game.question)
        pending = screen.job
        self.app.show_setup()
        self.assertNotIn(pending, self.app.tk.call("after", "info"))
        self.app.start(3, 1)
        self.pump()

    def test_global_deadline_finishes_ui_once(self):
        self.app.start(1, 1)
        screen = self.app.screen
        screen.game.deadline = screen.game.clock() - 1
        self.pump()
        self.assertTrue(screen.finished)
        self.assertEqual(screen.game.status, "lost")
        self.assertEqual(str(screen.submit_btn.cget("state")), "disabled")
        self.assertEqual(screen.game.lives, 5)

    def test_looking_rotates_portals_without_moving_or_erasing_answer(self):
        screen = self.start_seeded()
        screen.enter(0)
        screen.answer.insert(0, "my unfinished answer")
        g = screen.game
        position, question, deadline = g.current.key, g.question, g.question_deadline
        for facing in (1, 2, 3, 0):
            screen.look(1)
            self.assertEqual(screen.facing, facing)
            self.assertEqual(g.current.key, position)
            self.assertIs(g.question, question)
            self.assertEqual(g.question_deadline, deadline)
            self.assertEqual(screen.answer.get(), "my unfinished answer")
            for i, (_, _, (dx, dy)) in enumerate(screen.relative_portals()):
                target = screen.portal_targets()[i]
                if target is not None:
                    self.assertEqual(g.exits()[target].key, (g.current.x+dx, g.current.y+dy))

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
        self.assertEqual(screen.game.history, [origin])
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
        self.app.effects.set(True)
        origin = screen.game.current.key
        screen.enter(0)
        screen.game.deadline = screen.game.clock() - 1
        self.pump()
        self.assertEqual(screen.game.status, "lost")
        self.assertEqual(screen.game.current.key, origin)
        self.assertIsNone(screen.transition)


if __name__ == "__main__":
    unittest.main()
