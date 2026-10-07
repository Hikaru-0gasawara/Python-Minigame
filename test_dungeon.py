"""Deterministic checks for timing, graph traversal, scoring and game endings."""

import random
import unittest
from collections import deque

from dungeon import Dungeon, MODES
from dungeon_map import CARDINAL_DIRECTIONS, distances


class DungeonTests(unittest.TestCase):
    def make_game(self, difficulty=1, players=1):
        self.now = 100.0
        return Dungeon(difficulty, players, random.Random(42), lambda: self.now)

    def solve(self, game):
        return game.submit(game.question["answer"])

    def path_to(self, game, target):
        queue = deque([(game.current.key, [])])
        visited = {game.current.key}
        while queue:
            key, path = queue.popleft()
            if key == target:
                return path
            for neighbor in sorted(game.connections[key]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        self.fail("Target room is unreachable")

    def walk(self, game, path):
        for key in path:
            index = [room.key for room in game.exits()].index(key)
            self.assertTrue(game.enter(index))
            if game.question is not None:
                self.solve(game)

    def test_spatial_graph_invariants_across_seeds_and_modes(self):
        for mode in MODES:
            for seed in range(100):
                with self.subTest(mode=mode, seed=seed):
                    g = Dungeon(mode, rng=random.Random(seed))
                    self.assertEqual(g.current.key, (0, 0))
                    self.assertEqual(len(g.rooms), g.room_count)
                    self.assertGreaterEqual(len(g.exits()), 2)
                    measured = distances(g.connections)
                    self.assertEqual(set(measured), set(g.rooms))
                    self.assertEqual({key: room.depth for key, room in g.rooms.items()}, measured)
                    self.assertEqual(g.floors, measured[g.boss_key])
                    self.assertGreaterEqual(g.floors, 4)
                    self.assertEqual(len(g.connections[g.boss_key]), 1)
                    self.assertEqual(sum(r.kind == "boss" for r in g.rooms.values()), 1)
                    self.assertTrue(any(len(edges) >= 3 for edges in g.connections.values()))
                    self.assertTrue(any(len(edges) == 1 and key != g.boss_key
                                        for key, edges in g.connections.items()))
                    # A connected graph with at least V edges contains a cycle.
                    self.assertGreaterEqual(sum(map(len, g.connections.values())) // 2, len(g.rooms))
                    for key, edges in g.connections.items():
                        self.assertNotIn(key, edges)
                        self.assertLessEqual(len(edges), 4)
                        for adjacent in edges:
                            self.assertIn(key, g.connections[adjacent])
                            self.assertEqual(sum(abs(a - b) for a, b in zip(key, adjacent)), 1)
                    without_boss = {key: edges - {g.boss_key} for key, edges in g.connections.items()
                                    if key != g.boss_key}
                    self.assertEqual(len(distances(without_boss)), len(g.rooms) - 1)

    def test_seed_reproduces_layout_types_and_questions(self):
        first = self.make_game()
        second = self.make_game()
        self.assertEqual(first.connections, second.connections)
        self.assertEqual(first.rooms, second.rooms)
        first.enter(0)
        second.enter(0)
        self.assertEqual(first.question, second.question)
        other = Dungeon(rng=random.Random(43))
        self.assertNotEqual(first.connections, other.connections)

    def test_compass_order_and_invalid_doors(self):
        g = self.make_game()
        for room in g.rooms.values():
            g.current = room
            expected = [(room.x + dx, room.y + dy) for dx, dy in CARDINAL_DIRECTIONS
                        if (room.x + dx, room.y + dy) in g.connections[room.key]]
            self.assertEqual([r.key for r in g.exits()], expected)
        g.current = g.rooms[0, 0]
        for invalid in (-1, len(g.exits()), 100, None, "0"):
            self.assertFalse(g.enter(invalid))
            self.assertEqual(g.current.key, (0, 0))

    def test_fog_reveals_only_room_neighbors_and_back_tracks_history(self):
        g = self.make_game()
        self.assertEqual(g.revealed, {(0, 0)} | g.connections[0, 0])
        self.assertEqual(g.visited, {(0, 0)})
        previous_reveal = g.revealed.copy()
        g.enter(0)
        first = g.current.key
        self.assertEqual(g.visited, {(0, 0), first})
        self.assertEqual(g.revealed, previous_reveal | g.connections[first])
        self.solve(g)
        origin_door = [r.key for r in g.exits()].index((0, 0))
        self.assertTrue(g.enter(origin_door))
        self.assertIsNone(g.question)
        self.assertTrue(g.back())
        self.assertEqual(g.current.key, first)
        self.assertTrue(g.back())
        self.assertEqual(g.current.key, (0, 0))
        self.assertFalse(g.back())

    def test_all_optional_rooms_can_be_explored_before_boss(self):
        g = self.make_game()

        def visit():
            origin = g.current.key
            for key in sorted(g.connections[origin]):
                if key == g.boss_key or key in g.visited:
                    continue
                self.walk(g, [key])
                visit()
                self.assertTrue(g.back())
                self.assertEqual(g.current.key, origin)

        visit()
        self.assertEqual(g.visited, set(g.rooms) - {g.boss_key})
        self.assertEqual(g.status, "playing")
        self.assertEqual(g.current.key, (0, 0))

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
        for depth, seconds, tier in ((1, 30, "Easy"), ((g.floors + 2) // 3, 22, "Medium"),
                                    ((2 * g.floors + 2) // 3, 15, "Hard")):
            g.current = next(room for room in g.rooms.values() if room.depth == depth)
            g.current.kind = "combat"
            g.question = None
            g.ask()
            self.assertEqual(g.question_duration, seconds)
            self.assertIn(g.question, getattr(g.bank, tier.lower() + "_bank").questions)

    def test_guardian_needs_three_hits_and_freezes_final_time(self):
        g = self.make_game()
        self.walk(g, self.path_to(g, g.boss_key))
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
