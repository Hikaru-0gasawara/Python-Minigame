"""Scene model and pixel art, checked without a display."""

import unittest

from dungeon import Expedition
from palette import PALETTE, SECTORS
from room_art import GUARDIAN_STATES, H, LIGHTS, W, back_door, build_background, guardian, side_door
from scene import SECTOR_NAMES, portal_targets, scene_for, sector_of
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


class PixelArtTests(unittest.TestCase):
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
