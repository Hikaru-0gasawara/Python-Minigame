"""Deterministic checks for timing, graph traversal, scoring and game endings."""

import random
import unittest

from dungeon import Dungeon, MODES


class DungeonTests(unittest.TestCase):
    def make_game(self, difficulty=1, players=1):
        self.now = 100.0
        return Dungeon(difficulty, players, random.Random(42), lambda: self.now)

    def solve(self, game):
        return game.submit(game.question["answer"])

    def test_three_exits_rejoin_and_every_route_reaches_boss(self):
        for mode in MODES:
            g = self.make_game(mode)
            frontier = {g.current.key}
            for depth in range(g.floors):
                next_frontier = set()
                for key in frontier:
                    g.current = g.rooms[key]
                    exits = g.exits()
                    self.assertEqual(len(exits), 3)
                    self.assertTrue(all(r.depth == depth + 1 for r in exits))
                    next_frontier.update(r.key for r in exits)
                frontier = next_frontier
            self.assertEqual(frontier, {(g.floors, 1)})

    def test_locked_room_cannot_be_skipped(self):
        g = self.make_game()
        self.assertTrue(g.enter(0))
        self.assertFalse(g.enter(1))
        self.assertFalse(g.back())

    def test_revisit_gives_no_extra_reward(self):
        g = self.make_game()
        g.enter(0)
        self.solve(g)
        score, lives, deadline = g.scores[:], g.lives, g.deadline
        self.assertTrue(g.back())
        self.assertTrue(g.enter(0))
        self.assertIsNone(g.question)
        self.assertIsNone(g.submit("anything"))
        self.assertEqual((g.scores, g.lives, g.deadline), (score, lives, deadline))

    def test_question_timeout_only_costs_one_life(self):
        g = self.make_game()
        g.enter(1)
        self.now = g.question_deadline
        # A click at the deadline must not swallow the timeout event.
        self.assertFalse(g.enter(0))
        self.assertFalse(g.back())
        result = g.tick()
        self.assertFalse(result["correct"])
        self.assertEqual(g.lives, 4)
        self.assertIsNone(g.tick())
        self.assertEqual(g.lives, 4)

    def test_late_correct_answer_is_timeout(self):
        g = self.make_game()
        g.enter(0)
        self.now = g.question_deadline + .01
        self.assertFalse(self.solve(g)["correct"])
        self.assertEqual(g.scores, [0])

    def test_expedition_timeout_while_choosing(self):
        g = self.make_game()
        self.now = g.deadline
        self.assertFalse(g.enter(0))
        self.assertIsNotNone(g.tick())
        self.assertEqual(g.status, "lost")
        self.assertIsNone(g.tick())

    def test_mistakes_reset_combo_and_end_run(self):
        g = self.make_game()
        g.enter(1)
        g.combo = 3
        for _ in range(5):
            g.ask()
            g.submit("definitely wrong")
        self.assertEqual((g.combo, g.lives, g.status), (0, 0, "lost"))

    def test_room_rewards_and_elite_time(self):
        for kind in ("clock", "sanctuary", "elite"):
            g = self.make_game()
            g.exits()[0].kind = kind
            g.lives = 3
            g.enter(0)
            if kind == "elite":
                self.assertEqual(g.question_duration, g.base_question_time * .75)
            deadline = g.deadline
            result = self.solve(g)
            if kind == "clock":
                self.assertEqual(g.deadline, deadline + 12)
            if kind == "sanctuary":
                self.assertEqual(g.lives, 4)
            if kind == "elite":
                self.assertEqual(result["points"], 4000)

    def test_speed_bonus_and_cooperative_rotation(self):
        g = self.make_game(players=2)
        g.exits()[0].kind = "combat"
        g.enter(0)
        self.now += g.question_duration / 2
        result = self.solve(g)
        self.assertEqual(result["points"], 1500)
        self.assertEqual(g.scores, [1500, 0])
        self.assertEqual(g.player, 1)
        self.assertEqual(g.combo, 1)

    def test_campaign_difficulty_and_time_progress(self):
        g = self.make_game(4)
        for depth, seconds, tier in ((1, 30, "Easy"), (6, 22, "Medium"), (12, 15, "Hard")):
            g.current = g.rooms[depth, 0]
            g.current.kind = "combat"
            g.question = None
            g.ask()
            self.assertEqual(g.question_duration, seconds)
            self.assertIn(g.question, getattr(g.bank, tier.lower() + "_bank").questions)

    def test_guardian_needs_three_hits_and_freezes_final_time(self):
        g = self.make_game()
        while g.current.depth < g.floors:
            self.assertTrue(g.enter(1))
            self.solve(g)
        self.assertEqual(g.current.hits, 1)
        self.assertEqual(g.status, "playing")
        for _ in range(2):
            g.ask()
            self.solve(g)
        self.assertEqual(g.status, "won")
        remaining = g.remaining
        self.now += 1000
        self.assertEqual(g.remaining, remaining)
        self.assertIsNone(g.tick())
        self.assertFalse(g.back())


if __name__ == "__main__":
    unittest.main()
