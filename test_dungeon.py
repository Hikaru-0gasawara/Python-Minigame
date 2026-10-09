"""Deterministic checks for timing, graph traversal, scoring and game endings."""

import unittest
from collections import deque

from dungeon import CAMPAIGN, MODES, Expedition, format_seed, generate_dungeon, parse_seed
from dungeon_map import CARDINAL_DIRECTIONS, distances


class DungeonTests(unittest.TestCase):
    def make_game(self, difficulty=1, players=1):
        self.now = 100.0
        return Expedition(difficulty, players, 42, lambda: self.now)

    def solve(self, game):
        return game.submit(game.question["answer"])

    def path_to(self, game, target):
        queue = deque([(game.current.key, [])])
        visited = {game.current.key}
        while queue:
            key, path = queue.popleft()
            if key == target:
                return path
            for neighbor in sorted(game.dungeon.connections[key]):
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
                    g = Expedition(mode, seed=seed)
                    self.assertEqual(g.current.key, (0, 0))
                    self.assertEqual(len(g.dungeon.rooms), MODES[mode][1])
                    self.assertGreaterEqual(len(g.exits()), 2)
                    measured = distances(g.dungeon.connections)
                    self.assertEqual(set(measured), set(g.dungeon.rooms))
                    self.assertEqual({key: room.depth for key, room in g.dungeon.rooms.items()}, measured)
                    self.assertEqual(measured[g.dungeon.exit_key], max(measured.values()))
                    self.assertGreaterEqual(measured[g.dungeon.exit_key], 4)
                    self.assertEqual(len(g.dungeon.connections[g.dungeon.exit_key]), 1)
                    self.assertEqual(sum(r.kind == "exit" for r in g.dungeon.rooms.values()), 1)
                    self.assertTrue(any(len(edges) >= 3 for edges in g.dungeon.connections.values()))
                    self.assertTrue(any(len(edges) == 1 and key != g.dungeon.exit_key
                                        for key, edges in g.dungeon.connections.items()))
                    # A connected graph with at least V edges contains a cycle.
                    self.assertGreaterEqual(sum(map(len, g.dungeon.connections.values())) // 2, len(g.dungeon.rooms))
                    for key, edges in g.dungeon.connections.items():
                        self.assertNotIn(key, edges)
                        self.assertLessEqual(len(edges), 4)
                        for adjacent in edges:
                            self.assertIn(key, g.dungeon.connections[adjacent])
                            self.assertEqual(sum(abs(a - b) for a, b in zip(key, adjacent)), 1)
                    without_boss = {key: edges - {g.dungeon.exit_key} for key, edges in g.dungeon.connections.items()
                                    if key != g.dungeon.exit_key}
                    self.assertEqual(len(distances(without_boss)), len(g.dungeon.rooms) - 1)

    def test_seed_reproduces_layout_types_and_questions(self):
        first = self.make_game()
        second = self.make_game()
        self.assertEqual(first.dungeon.connections, second.dungeon.connections)
        self.assertEqual(first.dungeon.rooms, second.dungeon.rooms)
        first.enter(0)
        second.enter(0)
        self.assertEqual(first.question, second.question)
        other = Expedition(seed=43)
        self.assertNotEqual(first.dungeon.connections, other.dungeon.connections)

    def test_dungeon_depends_only_on_seed_and_difficulty(self):
        played = self.make_game()
        self.walk(played, [played.exits()[0].key])
        fresh = generate_dungeon(42, 1)
        self.assertEqual(played.dungeon.connections, fresh.connections)
        self.assertEqual({k: (r.kind, r.depth) for k, r in played.dungeon.rooms.items()},
                         {k: (r.kind, r.depth) for k, r in fresh.rooms.items()})
        self.assertEqual(fresh.exit_key, played.dungeon.exit_key)
        self.assertNotEqual(generate_dungeon(42, 1).connections, generate_dungeon(42, 3).connections)

    def test_seed_text_round_trips_and_rejects_garbage(self):
        for seed in (0, 42, 0xDEADBEEF, 16 ** 8 - 1):
            self.assertEqual(parse_seed(format_seed(seed)), seed)
        self.assertEqual(format_seed(0x3F9A12C0), "3F9A-12C0")
        self.assertEqual(parse_seed(" 3f9a 12c0 "), 0x3F9A12C0)
        for bad in ("", "-", "XYZ", "123456789", "+1", "0x10"):
            self.assertIsNone(parse_seed(bad))
        self.assertIsInstance(Expedition().seed, int)

    def test_compass_order_and_invalid_doors(self):
        g = self.make_game()
        for room in g.dungeon.rooms.values():
            g.current = room
            expected = [(room.x + dx, room.y + dy) for dx, dy in CARDINAL_DIRECTIONS
                        if (room.x + dx, room.y + dy) in g.dungeon.connections[room.key]]
            self.assertEqual([r.key for r in g.exits()], expected)
        g.current = g.dungeon.rooms[0, 0]
        for invalid in (-1, len(g.exits()), 100, None, "0"):
            self.assertFalse(g.enter(invalid))
            self.assertEqual(g.current.key, (0, 0))

    def test_fog_reveals_only_room_neighbors_and_back_tracks_history(self):
        g = self.make_game()
        self.assertEqual(g.revealed, {(0, 0)} | g.dungeon.connections[0, 0])
        self.assertEqual(g.visited, {(0, 0)})
        previous_reveal = g.revealed.copy()
        g.enter(0)
        first = g.current.key
        self.assertEqual(g.visited, {(0, 0), first})
        self.assertEqual(g.revealed, previous_reveal | g.dungeon.connections[first])
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
            for key in sorted(g.dungeon.connections[origin]):
                if key == g.dungeon.exit_key or key in g.visited:
                    continue
                self.walk(g, [key])
                visit()
                self.assertTrue(g.back())
                self.assertEqual(g.current.key, origin)

        visit()
        self.assertEqual(g.visited, set(g.dungeon.rooms) - {g.dungeon.exit_key})
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
        g = self.make_game(CAMPAIGN)
        floors = g.dungeon.rooms[g.dungeon.exit_key].depth
        for depth, seconds, tier in ((1, 30, "easy"), ((floors + 2) // 3, 22, "medium"),
                                    ((2 * floors + 2) // 3, 15, "hard")):
            g.current = next(room for room in g.dungeon.rooms.values() if room.depth == depth)
            g.current.kind = "combat"
            g.question = None
            g.ask()
            self.assertEqual(g.question_duration, seconds)
            self.assertIn(g.question, g.bank.tiers[tier])

    def test_guardian_needs_three_hits_and_freezes_final_time(self):
        g = self.make_game()
        self.walk(g, self.path_to(g, g.dungeon.exit_key))
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
