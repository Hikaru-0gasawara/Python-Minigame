"""Scene model and pixel art, checked without a display."""

import unittest

from dungeon import EXIT_HITS, Expedition
from palette import PALETTE, SECTORS
from props import GRAFFITI, PROP_AT, decor_sprite, elite, prop_sprite
from palette import CYAN, RED
from room_art import (BACK_DOOR, BX1, DOOR_STEPS, DOOR_STYLES, GUARDIAN_STATES, H, LIGHTS, W, back_door,
                      build_background, guardian, side_door)
from scene import SECTOR_NAMES, decorations, portal_targets, scene_for, sector_of
from test_dungeon import make_combat


class SceneModelTests(unittest.TestCase):
    def make_game(self, players=1):
        self.now = 100.0
        return make_combat(Expedition(1, players, 42, lambda: self.now))

    def test_sectors_split_depth_into_thirds(self):
        g = self.make_game()
        exit_depth = g.dungeon.rooms[g.dungeon.exit_key].depth
        for room in g.dungeon.rooms.values():
            expected = SECTOR_NAMES[min(2, room.depth * 3 // exit_depth)]
            self.assertEqual(sector_of(g.dungeon, room), expected)
        self.assertEqual(sector_of(g.dungeon, g.dungeon.rooms[0, 0]), "shallow")
        self.assertEqual(sector_of(g.dungeon, g.dungeon.rooms[g.dungeon.exit_key]), "deep")

    def test_doors_match_the_facing_and_only_exist_where_passages_do(self):
        g = self.make_game()
        for room in g.dungeon.rooms.values():
            g.active.position = room.key
            g.active.cleared.add(room.key)
            for facing in range(4):
                scene = scene_for(g, facing)
                targets = portal_targets(g, facing)
                self.assertEqual([d.portal for d in scene.doors], [p for p, t in enumerate(targets) if t is not None])
                self.assertEqual(len(scene.doors), len(g.dungeon.connections[room.key]))
                self.assertFalse(any(d.locked for d in scene.doors))

    def test_doors_lock_before_a_guardian_and_during_a_question(self):
        g = self.make_game()
        g.enter(0)
        self.assertTrue(all(d.locked for d in scene_for(g, 0).doors))
        g.submit(g.question["answer"])
        self.assertFalse(any(d.locked for d in scene_for(g, 0).doors))

    def test_guardian_state_is_per_player(self):
        g = self.make_game(players=2)
        self.assertIsNone(scene_for(g, 0).guardian)            # the Entrance has none
        g.enter(0)
        self.assertEqual(scene_for(g, 0).guardian, "listening")
        g.submit(g.question["answer"])
        g.enter(0)                                             # Player 2 walks into the same room
        self.assertEqual(scene_for(g, 0).guardian, "listening")
        g.question_tier = "easy"
        g.submit("definitely wrong")
        g.player = 1
        self.assertEqual(scene_for(g, 0).guardian, "dormant")
        g.player = 0
        self.assertEqual(scene_for(g, 0).guardian, "cleared")


class RoomKindTests(unittest.TestCase):
    def make_game(self, players=1):
        return make_combat(Expedition(1, players, 42, lambda: 100.0))

    def stand_in(self, game, kind, visited=True):
        """Put the active player in a room of a kind, entered or (as after a Swap) not."""
        room = game.exits()[0]
        room.kind = kind
        game.active.position = room.key
        game.active.cleared.add(room.key)
        if visited:
            game.active.visited.add(room.key)
        return room

    def test_each_room_kind_shows_its_prop(self):
        expected = {"treasure": "container", "mimic": "mimic", "trap": "trap", "sanctuary": "pod",
                    "empty": "debris", "combat": None, "elite": None}
        for kind, prop in expected.items():
            g = self.make_game()
            self.stand_in(g, kind)
            scene = scene_for(g, 0)
            self.assertEqual(scene.prop[0] if scene.prop else None, prop, kind)
            self.assertEqual(scene.elite, kind == "elite")
        g = self.make_game()
        self.assertEqual(scene_for(g, 0).prop, ("elevator", None))

    def test_prop_states_follow_what_the_active_player_has_seen(self):
        for kind, unseen, seen in (("treasure", "closed", "open"), ("mimic", "closed", "revealed"),
                                   ("trap", "armed", "spent")):
            g = self.make_game()
            room = self.stand_in(g, kind, visited=False)
            self.assertEqual(scene_for(g, 0).prop[1], unseen, kind)
            g.active.visited.add(room.key)
            self.assertEqual(scene_for(g, 0).prop[1], seen, kind)

    def test_exit_locks_follow_each_players_hits_and_hide_behind_a_back_door(self):
        g = self.make_game(players=2)
        exit_room = g.dungeon.rooms[g.dungeon.exit_key]
        for player, hits in ((0, 2), (1, 0)):
            g.player = player
            g.active.position = exit_room.key
            g.active.exit_hits = hits
            facing = next(f for f in range(4) if portal_targets(g, f)[1] is None)
            self.assertEqual(scene_for(g, facing).prop, ("gate", hits))
        facing = next(f for f in range(4) if portal_targets(g, f)[1] is not None)
        self.assertIsNone(scene_for(g, facing).prop)

    def test_a_sanctuary_shows_healing_and_bubbles_right_after_it_heals(self):
        g = self.make_game()
        room = g.exits()[0]
        room.kind, room.effect = "sanctuary", "heal"
        g.active.lives = 1
        g.enter(0)
        g.player = 0
        scene = scene_for(g, 0)
        self.assertEqual(scene.prop, ("pod", "healing"))
        self.assertIn("bubbles", [e[0] for e in scene.emitters])

    def test_decorations_are_seeded_varied_and_fit_the_back_wall(self):
        seen = set()
        for i in range(60):
            first = decorations(42, (i, -i))
            self.assertEqual(first, decorations(42, (i, -i)))
            seen.add(first[0])
            for name, variant, x, y in first[0]:
                sprite = decor_sprite(name, variant)
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x + sprite.w, W)
                self.assertLessEqual(y + sprite.h, H)
                if name in ("screen", "graffiti"):
                    self.assertLessEqual(x + sprite.w, BX1 + 1, name)
                    self.assertTrue(x + sprite.w <= BACK_DOOR[0] or x > BACK_DOOR[2], name)
        self.assertGreater(len(seen), 10)
        g = make_combat(Expedition(1, 2, 42, lambda: 100.0))
        g.enter(0)
        g.player = 1
        self.assertEqual(scene_for(g, 0).decor, decorations(42, (0, 0))[0])   # the same for every player


class DoorTests(unittest.TestCase):
    def test_each_sector_has_its_own_door_style(self):
        self.assertEqual(set(DOOR_STYLES), set(SECTOR_NAMES))
        self.assertEqual(len(set(DOOR_STYLES.values())), 3)

    def test_doors_open_frame_by_frame_towards_the_open_frame(self):
        for sector in SECTOR_NAMES:
            for draw in (lambda s, sector=sector: back_door(sector, False, s).px,
                         lambda s, sector=sector: side_door(sector, "left", False, s).px):
                frames = [draw(step) for step in range(DOOR_STEPS + 1)]
                likeness = [sum(a == b for a, b in zip(frame, frames[-1])) for frame in frames]
                with self.subTest(sector=sector):
                    # Never closes again on the way; the vault's turning wheel may wobble a few pixels.
                    self.assertTrue(all(later >= earlier - 8 for earlier, later in zip(likeness, likeness[1:])))
                    self.assertLess(likeness[0], likeness[-1])
                    self.assertGreater(len({tuple(f) for f in frames}), DOOR_STEPS // 2)

    def test_a_locked_door_shows_red_and_an_opening_one_cyan(self):
        for sector in SECTOR_NAMES:
            self.assertEqual(back_door(sector, True).get(23, 3), RED)
            self.assertEqual(back_door(sector, False, 3).get(23, 3), CYAN)

    def test_side_doors_open_inside_their_closed_outline(self):
        for side in ("left", "right"):
            x0, y0, x1, y1 = side_door("deep", side, False).bbox()
            for step in range(1, DOOR_STEPS + 1):
                a0, b0, a1, b1 = side_door("deep", side, False, step).bbox()
                self.assertTrue(x0 <= a0 and y0 <= b0 and a1 <= x1 and b1 <= y1)


class PixelArtTests(unittest.TestCase):
    def test_a_closed_mimic_is_pixel_for_pixel_a_closed_container(self):
        self.assertEqual(prop_sprite("mimic", "closed").px, prop_sprite("container", "closed").px)
        self.assertNotEqual(prop_sprite("mimic", "revealed").px, prop_sprite("container", "open").px)

    def test_prop_states_are_distinct_sprites_within_the_palette(self):
        groups = [[prop_sprite("container", s) for s in ("closed", "open")],
                  [prop_sprite("trap", s) for s in ("armed", "spent")],
                  [prop_sprite("pod", s) for s in ("idle", "healing")],
                  [prop_sprite("gate", hits) for hits in range(EXIT_HITS + 1)],
                  [elite(s) for s in GUARDIAN_STATES],
                  [decor_sprite("screen", s) for s in ("eye", "static")],
                  [decor_sprite("graffiti", v) for v in range(len(GRAFFITI))]]
        for sprites in groups:
            self.assertEqual(len({tuple(p.px) for p in sprites}), len(sprites))
            for p in sprites:
                self.assertTrue({c for c in p.px if c is not None} <= set(range(len(PALETTE))))
        for name in PROP_AT:
            self.assertIn(name, ("container", "mimic", "trap", "pod", "debris", "elevator", "gate", "elite"))

    def test_backgrounds_are_deterministic_full_frames_within_the_palette(self):
        for sector in SECTORS:
            frames = build_background(7, (2, -1), sector)
            self.assertEqual(set(frames), set(LIGHTS))
            for buffer in frames.values():
                self.assertEqual(len(buffer), W * H)
                self.assertTrue(set(buffer) <= set(range(len(PALETTE))))
            build_background.cache_clear()
            self.assertEqual(build_background(7, (2, -1), sector), frames)
        self.assertNotEqual(build_background(7, (2, -1), "shallow")["on"], build_background(8, (2, -1), "shallow")["on"])
        self.assertNotEqual(build_background(7, (2, -1), "shallow")["on"], build_background(7, (2, -1), "deep")["on"])

    def test_dimmed_and_dark_variants_are_darker_versions(self):
        frames = build_background(3, (0, 1), "shallow")
        self.assertNotEqual(frames["on"], frames["dimmed"])
        self.assertLess(sum(frames["off"]), sum(frames["on"]))

    def test_side_doors_stay_on_their_own_wall(self):
        for side, half in (("left", range(W // 2)), ("right", range(W // 2, W))):
            box = side_door("shallow", side, False).bbox()
            self.assertIn(box[0], half)
            self.assertIn(box[2], half)
        self.assertNotEqual(side_door("shallow", "left", True).px, side_door("shallow", "left", False).px)

    def test_sprites_have_distinct_states_and_transparent_surroundings(self):
        statues = {state: guardian(state).px for state in GUARDIAN_STATES}
        self.assertEqual(len({tuple(px) for px in statues.values()}), len(GUARDIAN_STATES))
        for px in statues.values():
            self.assertIn(None, px)
            self.assertTrue({c for c in px if c is not None} <= set(range(len(PALETTE))))
        self.assertNotEqual(back_door("shallow", True).px, back_door("shallow", False).px)


if __name__ == "__main__":
    unittest.main()
