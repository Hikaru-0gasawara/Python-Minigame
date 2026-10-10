"""The pixel menu: options by keyboard and mouse, the Records panel, and the animation's lifecycle (Tk display)."""

from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from audio import Audio
from dungeon import CAMPAIGN, EASY, HARD
from dungeon_ui import DungeonApp
from menu_ui import ROWS
from questions import FALLBACK
from records import Records
from room_art import H, W


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.app = DungeonApp()
        self.app.geometry("1000x760+20000+20000")
        self.errors = []
        self.app.report_callback_exception = lambda *error: self.errors.append(error)
        self.app.audio = Audio(lambda path: None)
        folder = tempfile.TemporaryDirectory()      # never the player's own Records
        self.addCleanup(folder.cleanup)
        self.app.records = Records(Path(folder.name) / "records.json")
        self.app.show_setup()
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        self.assertEqual(self.errors, [])

    def key(self, keysym, char="", state=0):
        return self.app.screen.on_key(SimpleNamespace(keysym=keysym, char=char, state=state))

    def go_to(self, row):
        while ROWS[self.app.screen.focus] != row:
            self.key("Down")

    def click(self, action):
        x, y = self.app.screen.region_centre(action)
        self.app.screen.click(SimpleNamespace(x=x, y=y))

    def test_keyboard_picks_difficulty_and_players_and_starts_the_matching_expedition(self):
        menu = self.app.screen
        self.key("Left")                              # Difficulty wraps round to Campanha
        self.assertIn("CAMPANHA", menu.hud["column"][0])
        self.key("Tab")
        self.key("Right")
        self.key("Right")
        self.assertEqual((menu.difficulty, menu.players), (CAMPAIGN, 3))
        self.key("Tab", state=1)                      # Shift+Tab goes back
        self.assertEqual(ROWS[menu.focus], "difficulty")
        self.go_to("start")
        self.key("Return")
        self.app.update()
        game = self.app.screen.game
        self.assertEqual((game.difficulty, len(game.players)), (CAMPAIGN, 3))
        self.app.show_setup()
        self.app.update()
        self.assertEqual((self.app.screen.difficulty, self.app.screen.players), (CAMPAIGN, 3))

    def test_typed_seed_starts_that_dungeon_and_a_bad_one_a_random_seed(self):
        self.go_to("seed")
        for ch in "3f9a-12c0z":                       # not a Seed character: ignored
            self.key(ch, ch)
        self.key("x", "x")
        self.assertEqual(self.app.screen.hud["column"][2], "SEED 3F9A-12C0_")
        self.key("Return")
        self.app.update()
        screen = self.app.screen
        self.assertEqual(screen.game.seed, 0x3F9A12C0)
        self.assertIn("3F9A-12C0", screen.hud["map"])
        self.app.show_setup()
        self.app.update()
        self.go_to("seed")
        self.key("1", "1")
        self.key("BackSpace")
        self.key("-", "-")
        self.click(("row", ROWS.index("start")))
        self.app.update()
        self.assertIsInstance(self.app.screen.game.seed, int)

    def test_the_records_panel_shows_the_selected_difficultys_top_five(self):
        for seconds in (300, 61, 200, 100, 500, 400):
            self.app.records.submit(EASY, seconds, 42, 2)
        self.app.records.submit(HARD, 75, 7, 1)
        self.app.show_setup()
        self.app.update()
        menu = self.app.screen
        self.assertEqual(menu.hud["records"], ["RECORDES · AVENTUREIRO", "1. 1:01  2J  0000-002A",
                                               "2. 1:40  2J  0000-002A", "3. 3:20  2J  0000-002A",
                                               "4. 5:00  2J  0000-002A", "5. 6:40  2J  0000-002A"])
        self.key("Right")
        self.assertEqual(menu.hud["records"], ["RECORDES · GUERREIRO", "Nenhuma fuga ainda."])
        self.key("Right")
        self.assertEqual(menu.hud["records"], ["RECORDES · PESADELO", "1. 1:15  1J  0000-0007"])

    def test_the_records_file_is_read_once_per_difficulty(self):
        with mock.patch.object(self.app.records, "top", wraps=self.app.records.top) as top:
            for key in ("Down", "Down", "Up", "Up"):     # moving between rows redraws the menu
                self.key(key)
            self.assertEqual(top.call_count, 0)          # already read when the menu opened
            self.key("Right")
            self.key("Left")
            self.assertEqual(top.call_count, 1)          # Guerreiro once; Aventureiro was kept

    def test_mute_and_reduced_motion_toggle_from_the_column(self):
        menu = self.app.screen
        self.go_to("sound")
        self.key("Return")
        self.assertTrue(self.app.audio.muted)
        self.assertEqual(menu.hud["column"][3], "SOM ← MUDO →")
        self.key("space")
        self.assertFalse(self.app.audio.muted)
        self.go_to("motion")
        self.key("Right")
        self.assertFalse(self.app.effects.get())
        self.assertEqual(menu.hud["column"][4], "MOVIMENTO ← REDUZIDO →")
        self.assertIsNone(menu.animation_job)

    def test_hover_and_clicks_work_like_the_keyboard(self):
        menu = self.app.screen
        x, y = menu.region_centre(("row", 1))
        menu.motion(SimpleNamespace(x=x, y=y))
        self.assertEqual(ROWS[menu.focus], "players")
        self.click(("row", 1))
        self.click(("row", 0))
        self.assertEqual((menu.difficulty, menu.players), (2, 2))
        self.click(("help",))
        self.assertTrue(menu._help.winfo_exists())
        self.key("F1")                                # a second request only raises it
        menu._help.destroy()

    def test_a_question_file_that_fails_to_load_is_announced(self):
        self.assertIn("30s POR PERGUNTA · 15 SALAS", self.app.screen.hud["column"])
        with mock.patch("questions.load_tier", return_value=(FALLBACK, True)):
            self.app.show_setup()
        self.app.update()
        self.assertIn("BANCO DE PERGUNTAS INCOMPLETO", self.app.screen.hud["column"])

    def test_every_piece_fits_the_frame_and_the_panels_never_overlap(self):
        for seconds in range(5):
            self.app.records.submit(EASY, 3599 + seconds, 0xFFFFFFFF, 4)
        self.app.show_setup()
        self.app.update()
        menu = self.app.screen
        self.go_to("seed")
        for ch in "FFFF-FFFF":
            self.key(ch, ch)
        boxes = {}
        for name, piece in menu.pieces.items():
            x0, y0, x1, y1 = boxes[name] = piece.x, piece.y, piece.x + piece.pix.w, piece.y + piece.pix.h
            self.assertTrue(0 <= x0 and x1 <= W and 0 <= y0 and y1 <= H, name)
        column, records = boxes["column"], boxes["records"]
        self.assertTrue(column[2] <= records[0] or column[3] <= records[1])
        self.assertLessEqual(menu.title.width() * 4, W)

    def test_reduced_motion_stops_the_loop_and_leaving_cancels_every_callback(self):
        menu = self.app.screen
        self.assertIsNotNone(menu.animation_job)
        old_job = menu.animation_job
        self.app.effects.set(False)
        self.app.update()
        self.assertIsNone(menu.animation_job)
        self.assertNotIn(old_job, self.app.tk.call("after", "info"))
        self.app.effects.set(True)
        self.app.update()
        running_job = menu.animation_job
        self.assertIsNotNone(running_job)
        trace_count = len(self.app.effects.trace_info())
        self.go_to("start")
        self.key("Return")
        self.app.update()
        self.assertNotIn(running_job, self.app.tk.call("after", "info"))
        self.assertLess(len(self.app.effects.trace_info()), trace_count)
        self.app.effects.set(False)
        self.app.show_setup()
        self.app.update()
        self.assertIsNone(self.app.screen.animation_job)
        self.assertEqual(len(self.app.effects.trace_info()), trace_count)
