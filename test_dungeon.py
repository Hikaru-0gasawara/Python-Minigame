"""Deterministic checks for the race: generation, Turns, Guardians and the Exit."""

import unittest
from collections import deque

from dungeon import (BUFFS, CAMPAIGN, DEBUFFS, EXIT_HITS, HARD, LIVES, MODES, PLACED, Expedition,
                     format_seed, generate_dungeon, parse_seed)
from dungeon_map import CARDINAL_DIRECTIONS, distances


def make_combat(game):
    """Turn every ordinary Room into a Combat room, isolating Turn and Guardian rules."""
    for room in game.dungeon.rooms.values():
        if room.kind not in ("entrance", "exit"):
            room.kind, room.effect = "combat", None
    return game


class DungeonTests(unittest.TestCase):
    def make_game(self, difficulty=1, players=1, only_guardians=True):
        self.now = 100.0
        game = Expedition(difficulty, players, 42, lambda: self.now)
        if only_guardians:
            make_combat(game)
        return game

    def solve(self, game):
        return game.submit(game.question["answer"])

    def miss(self, game, tier="easy"):
        game.question_tier = tier  # Pin the Tier so the penalty is known.
        return game.submit("definitely wrong")

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

    def door_to(self, game, key):
        return [room.key for room in game.exits()].index(key)

    def walk(self, game, path):
        """Solo walk: each step is one Turn, answering any Guardian on the way."""
        for key in path:
            self.assertTrue(game.enter(self.door_to(game, key)))
            if game.question is not None:
                self.solve(game)

    def branching_door(self, game):
        """A door from the Entrance whose Room leads further than back."""
        return next(i for i, room in enumerate(game.exits())
                    if len(game.dungeon.connections[room.key]) > 1)

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
                    without_exit = {key: edges - {g.dungeon.exit_key} for key, edges in g.dungeon.connections.items()
                                    if key != g.dungeon.exit_key}
                    self.assertEqual(len(distances(without_exit)), len(g.dungeon.rooms) - 1)

    def test_dungeon_depends_only_on_seed_and_difficulty(self):
        played = self.make_game(only_guardians=False)
        self.walk(played, [played.exits()[0].key])
        fresh = generate_dungeon(42, 1)
        self.assertEqual(played.dungeon.connections, fresh.connections)
        self.assertEqual(played.dungeon.rooms, fresh.rooms)
        self.assertEqual(fresh.exit_key, played.dungeon.exit_key)
        self.assertNotEqual(generate_dungeon(42, 1).connections, generate_dungeon(42, 3).connections)

    def test_seed_reproduces_questions_and_differs_between_seeds(self):
        first, second = self.make_game(), self.make_game()
        first.enter(0)
        second.enter(0)
        self.assertEqual(first.question, second.question)
        self.assertNotEqual(first.dungeon.connections, Expedition(seed=43).dungeon.connections)

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
            expected = [(room.x + dx, room.y + dy) for dx, dy in CARDINAL_DIRECTIONS
                        if (room.x + dx, room.y + dy) in g.dungeon.connections[room.key]]
            self.assertEqual([r.key for r in g.exits(room)], expected)
        for invalid in (-1, len(g.exits()), 100, None, "0"):
            self.assertFalse(g.enter(invalid))
            self.assertEqual(g.current.key, (0, 0))

    def test_turns_rotate_in_fixed_order_one_move_each(self):
        g = self.make_game(players=3)
        first_room = g.exits()[0].key
        for expected in (0, 1, 2):
            self.assertEqual(g.player, expected)
            self.assertTrue(g.enter(0))
            self.assertIsNotNone(g.question)
            self.assertEqual(g.player, expected)  # The Guardian is part of the same Turn.
            self.solve(g)
        self.assertEqual(g.player, 0)
        self.assertEqual([p.position for p in g.players], [first_room] * 3)

    def test_moving_into_a_cleared_room_ends_the_turn_without_a_question(self):
        g = self.make_game(players=2)
        g.enter(0)
        self.solve(g)
        g.enter(1)
        g.retreat()  # Player 2 flees back to the Entrance.
        self.assertEqual(g.player, 0)
        self.assertTrue(g.enter(self.door_to(g, (0, 0))))
        self.assertIsNone(g.question)
        self.assertEqual(g.player, 1)

    def test_every_player_faces_a_guardian_someone_else_cleared(self):
        g = self.make_game(players=2)
        g.enter(0)
        first = g.question
        self.solve(g)
        room = g.players[0].position
        self.assertTrue(g.enter(0))
        self.assertEqual(g.players[1].position, room)
        self.assertIsNotNone(g.question)
        self.assertIsNot(g.question, first)
        self.assertIn(room, g.players[0].cleared)
        self.assertNotIn(room, g.players[1].cleared)

    def test_questions_never_repeat_within_an_expedition(self):
        g = self.make_game(players=4)
        seen = []
        for _ in range(12):
            if g.has_cleared(g.current):
                g.enter(0)
            else:
                g.ask()
            seen.append(id(g.question))
            self.miss(g)
        self.assertEqual(len(seen), len(set(seen)))

    def test_wrong_answer_ends_the_turn_and_the_player_must_answer_again(self):
        g = self.make_game(players=2)
        g.enter(0)
        room = g.current.key
        result = self.miss(g)
        self.assertFalse(result["correct"])
        self.assertEqual(result["player"], 1)
        self.assertEqual(g.player, 1)
        g.enter(0)
        self.solve(g)
        self.assertEqual(g.player, 0)
        self.assertEqual(g.players[0].position, room)
        self.assertFalse(g.enter(0))  # Still un-Cleared: answer or retreat.
        g.ask()
        self.assertIsNotNone(g.question)
        self.assertTrue(self.solve(g)["correct"])

    def test_question_timeout_counts_as_wrong_and_passes_the_turn(self):
        g = self.make_game(players=2)
        g.enter(0)
        self.now = g.question_deadline
        self.assertFalse(g.enter(1))
        g.question_tier = "easy"
        result = g.tick()
        self.assertFalse(result["correct"])
        self.assertEqual(g.player, 1)
        self.assertIsNone(g.tick())

    def test_late_correct_answer_is_a_timeout(self):
        g = self.make_game()
        g.enter(0)
        g.question_tier = "easy"
        self.now = g.question_deadline + .01
        self.assertFalse(self.solve(g)["correct"])
        self.assertFalse(g.has_cleared(g.current))

    def test_retreat_abandons_the_question_and_ends_the_turn(self):
        g = self.make_game(players=2)
        g.enter(0)
        self.assertTrue(g.retreat())
        self.assertIsNone(g.question)
        self.assertEqual(g.players[0].position, (0, 0))
        self.assertEqual(g.player, 1)
        self.assertFalse(g.retreat())  # Player 2 has not moved yet.

    def test_each_player_reveals_only_their_own_map(self):
        g = self.make_game(players=2)
        start = {(0, 0)} | g.dungeon.connections[0, 0]
        self.assertEqual([p.revealed for p in g.players], [start, start])
        g.enter(self.branching_door(g))
        first = g.current.key
        self.assertEqual(g.players[0].visited, {(0, 0), first})
        self.assertEqual(g.players[0].revealed, start | g.dungeon.connections[first])
        self.assertEqual((g.players[1].visited, g.players[1].revealed), ({(0, 0)}, start))

    def test_all_optional_rooms_can_be_explored_before_the_exit(self):
        g = self.make_game()

        def visit():
            origin = g.current.key
            for key in sorted(g.dungeon.connections[origin]):
                if key == g.dungeon.exit_key or key in g.active.visited:
                    continue
                self.walk(g, [key])
                visit()
                self.walk(g, [origin])

        visit()
        self.assertEqual(g.active.visited, set(g.dungeon.rooms) - {g.dungeon.exit_key})
        self.assertEqual(g.status, "playing")

    def plant(self, game, kind, effect=None):
        """Make the Room behind a branching Entrance door a given kind; return that door."""
        door = self.branching_door(game)
        room = game.exits()[door]
        room.kind, room.effect = kind, effect
        return door

    def test_room_kinds_and_effects_come_from_the_seed(self):
        kinds, dead_ends = set(), set()
        for seed in range(150):
            dungeon = generate_dungeon(seed, HARD)
            self.assertEqual(dungeon.rooms, generate_dungeon(seed, HARD).rooms)
            for key, room in dungeon.rooms.items():
                kinds.add(room.kind)
                if len(dungeon.connections[key]) == 1 and key != dungeon.exit_key:
                    dead_ends.add(room.kind)
                expected = (BUFFS if room.kind in ("treasure", "elite") else
                            DEBUFFS if room.kind in ("mimic", "trap") else
                            ("heal",) if room.kind == "sanctuary" else (None,))
                self.assertIn(room.effect, expected)
        self.assertEqual(kinds, set(PLACED) | {"entrance", "exit"})
        self.assertGreater(len(dead_ends), 4)  # A Dead End may hold any kind.

    def test_elite_asks_a_hard_question_and_grants_its_buff(self):
        g = self.make_game(players=2)
        door = self.plant(g, "elite", "insight")
        g.enter(door)
        self.assertEqual(g.question_tier, "hard")
        self.assertIn(g.question, g.bank.tiers["hard"])
        result = self.solve(g)
        self.assertIn("Prêmio", result["message"])
        self.assertEqual((g.event["player"], g.event["effect"]), (1, "insight"))

    def test_treasure_mimic_and_trap_fire_only_on_each_players_first_visit(self):
        for kind in ("treasure", "mimic", "trap"):
            with self.subTest(kind=kind):
                g = self.make_game()
                effect = "insight" if kind == "treasure" else "life"
                door = self.plant(g, kind, effect)
                room = g.exits()[door]
                self.assertEqual(g.appearance(room), "unknown" if kind == "trap" else "treasure")
                g.enter(door)
                self.assertIsNone(g.question)
                self.assertEqual(g.event["effect"], effect)
                self.assertEqual(g.appearance(room), kind)
                self.assertTrue(g.has_cleared(room))
                lives = g.active.lives
                g.retreat()
                g.enter(door)
                self.assertIsNone(g.event)
                self.assertEqual(g.active.lives, lives)

    def test_a_debuff_on_entry_retreats_skips_or_costs_a_life(self):
        g = self.make_game(players=2)
        door = self.plant(g, "trap", "retreat")
        g.enter(door)
        self.assertEqual((g.players[0].position, g.player), ((0, 0), 1))
        door = self.plant(g, "trap", "skip")  # Same Room, unvisited by Player 2.
        g.enter(door)
        self.assertTrue(g.players[1].skip_next)
        self.assertEqual(g.player, 0)

    def test_sanctuary_restores_one_life_on_every_visit_up_to_the_maximum(self):
        g = self.make_game()
        door = self.plant(g, "sanctuary", "heal")
        g.active.lives = 1
        g.enter(door)
        self.assertEqual(g.active.lives, 2)
        g.retreat()
        g.enter(door)
        g.retreat()
        g.enter(door)
        self.assertEqual(g.active.lives, LIVES)

    def test_empty_room_does_nothing_and_ends_the_turn(self):
        g = self.make_game(players=2)
        door = self.plant(g, "empty")
        g.enter(door)
        self.assertEqual((g.event, g.question, g.player, g.players[0].lives), (None, None, 1, LIVES))

    def test_haste_grants_exactly_one_extra_move(self):
        g = self.make_game(players=2)
        door = self.plant(g, "treasure", "haste")
        g.enter(door)
        self.assertEqual(g.player, 0)
        self.assertTrue(g.enter(self.door_to(g, (0, 0))))
        self.assertEqual(g.player, 1)
        self.assertEqual(g.players[0].extra_moves, 0)

    def test_insight_reveals_two_passages_for_that_player_only(self):
        g = self.make_game(players=2)
        door = self.plant(g, "treasure", "insight")
        room = g.exits()[door].key
        g.enter(door)
        ring = {room}
        within = set()
        for _ in range(2):
            ring = {n for key in ring for n in g.dungeon.connections[key]}
            within |= ring
        self.assertLessEqual(within, g.players[0].revealed)
        self.assertFalse(within <= g.players[1].revealed)

    def test_tier_frequencies_follow_each_difficulty(self):
        for difficulty, (_name, _rooms, seconds, weights) in MODES.items():
            g = self.make_game(difficulty)
            g.active.position = next(k for k, r in g.dungeon.rooms.items() if r.kind == "combat")
            counts = {"easy": 0, "medium": 0, "hard": 0}
            for _ in range(3000):
                g.question = None
                g.ask()
                counts[g.question_tier] += 1
                self.assertIn(g.question, g.bank.tiers[g.question_tier])
                self.assertEqual(g.question_duration, seconds)
            with self.subTest(difficulty=difficulty):
                for (tier, count), weight in zip(counts.items(), weights):
                    self.assertAlmostEqual(count / 3000, weight / 100, delta=.03)
        campaign, easy = MODES[CAMPAIGN][3], MODES[1][3]
        self.assertGreater(campaign[0], easy[0])

    def test_missing_easy_costs_a_life_and_keeps_the_player_in_place(self):
        g = self.make_game(players=2)
        g.enter(0)
        room = g.current.key
        result = self.miss(g, "easy")
        self.assertEqual((result["tier"], result["penalty"]), ("easy", "life"))
        self.assertIn("−1 vida", result["message"])
        self.assertIn(result["answer"], result["message"])
        self.assertEqual((g.players[0].lives, g.players[0].position, g.player), (LIVES - 1, room, 1))

    def test_missing_medium_skips_the_next_turn_once(self):
        g = self.make_game(players=2)
        g.enter(0)
        self.assertEqual(self.miss(g, "medium")["penalty"], "skip")
        self.assertTrue(g.players[0].skip_next)
        self.assertEqual(g.player, 1)
        g.enter(0)
        self.solve(g)
        self.assertEqual(g.player, 1)  # Player 1's Turn was passed over.
        self.assertFalse(g.players[0].skip_next)
        g.enter(next(i for i, room in enumerate(g.exits()) if not g.has_cleared(room)))
        self.solve(g)
        self.assertEqual(g.player, 0)

    def test_solo_skip_simply_clears(self):
        g = self.make_game()
        g.enter(0)
        self.miss(g, "medium")
        self.assertEqual(g.player, 0)
        self.assertFalse(g.active.skip_next)

    def test_missing_hard_retreats_and_ends_the_turn(self):
        g = self.make_game(players=2)
        g.enter(0)
        room = g.current.key
        self.assertEqual(self.miss(g, "hard")["penalty"], "retreat")
        self.assertEqual((g.players[0].position, g.players[0].came_from), ((0, 0), room))
        self.assertEqual((g.players[0].lives, g.player), (LIVES, 1))

    def test_losing_the_last_life_returns_to_the_entrance_with_progress_kept(self):
        g = self.make_game()
        g.enter(self.branching_door(g))
        self.solve(g)
        cleared, visited = set(g.active.cleared), set(g.active.visited)
        g.enter(next(i for i, r in enumerate(g.exits()) if not g.has_cleared(r)))
        for life in range(LIVES - 1, -1, -1):
            result = self.miss(g, "easy")
            if life:
                self.assertEqual(g.active.lives, life)
                g.ask()
        self.assertEqual(result["penalty"], "entrance")
        self.assertEqual((g.active.position, g.active.lives, g.active.came_from), ((0, 0), LIVES, None))
        self.assertLessEqual(cleared, g.active.cleared)
        self.assertLessEqual(visited, g.active.visited)
        self.assertFalse(g.retreat())

    def test_timeout_applies_the_tier_penalty(self):
        g = self.make_game(players=2)
        g.enter(0)
        g.question_tier = "medium"
        self.now = g.question_deadline
        self.assertEqual(g.tick()["penalty"], "skip")
        self.assertTrue(g.players[0].skip_next)

    def test_exit_needs_three_hits_across_turns_and_progress_survives_leaving(self):
        g = self.make_game()
        exit_key = g.dungeon.exit_key
        self.walk(g, self.path_to(g, exit_key))
        self.assertEqual((g.active.position, g.active.exit_hits), (exit_key, 1))
        self.assertFalse(g.has_cleared(g.current))
        self.assertTrue(g.retreat())
        self.walk(g, [exit_key])
        self.assertEqual(g.active.exit_hits, 2)
        g.ask()
        self.solve(g)
        self.assertEqual((g.status, g.winner, g.active.exit_hits), ("won", 0, EXIT_HITS))
        self.assertIsNone(g.question)
        for action in (lambda: g.enter(0), g.retreat, g.tick, lambda: g.submit("x")):
            self.assertFalse(action())

    def test_the_first_player_to_clear_the_exit_wins(self):
        g = self.make_game(players=2)
        exit_key = g.dungeon.exit_key
        # Teleport both racers next to the Exit; only the race to it matters here.
        neighbour = next(iter(g.dungeon.connections[exit_key]))
        for player in g.players:
            player.position = neighbour
            player.cleared.add(neighbour)
        for turn in range(EXIT_HITS * 2):
            if g.has_cleared(g.current):
                g.enter(self.door_to(g, exit_key))
            else:
                g.ask()
            if g.player == 1:
                self.solve(g)
            else:
                self.miss(g)
            if g.status == "won":
                break
        self.assertEqual((g.winner, g.players[1].exit_hits, g.players[0].exit_hits), (1, EXIT_HITS, 0))

if __name__ == "__main__":
    unittest.main()
