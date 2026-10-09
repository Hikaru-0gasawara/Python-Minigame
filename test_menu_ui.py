"""Menu integration: configuration, layout and animation lifecycle (Tk display)."""

import tkinter as tk
import unittest
from unittest.mock import patch

from dungeon_ui import DungeonApp


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.app = DungeonApp()
        self.app.geometry("1000x760+20000+20000")
        self.errors = []
        self.app.report_callback_exception = lambda *error: self.errors.append(error)
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        self.assertEqual(self.errors, [])

    def test_selected_mode_and_team_start_the_matching_expedition(self):
        menu = self.app.screen
        menu.mode_buttons[3].invoke()
        menu.player_buttons[2].invoke()
        self.assertEqual((menu.level.get(), menu.players.get()), (4, 3))
        menu.start_btn.invoke()
        self.app.update()
        game = self.app.screen.game
        self.assertEqual((game.difficulty, len(game.scores)), (4, 3))
        self.app.show_setup()
        self.app.update()
        self.assertEqual((self.app.screen.level.get(), self.app.screen.players.get()), (4, 3))

    def test_controls_remain_visible_at_minimum_window(self):
        menu = self.app.screen
        for mode in menu.mode_buttons:
            mode.invoke()
            self.app.update()
            for widget in (menu.start_btn, menu.effects_toggle,
                           *menu.mode_buttons, *menu.player_buttons):
                with self.subTest(widget=str(widget), mode=menu.level.get()):
                    self.assertTrue(widget.winfo_ismapped())
                    self.assertGreaterEqual(widget.winfo_height(), widget.winfo_reqheight())
                    self.assertGreaterEqual(widget.winfo_rootx(), self.app.winfo_rootx())
                    self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(),
                                         self.app.winfo_rootx() + self.app.winfo_width())
                    self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                         self.app.winfo_rooty() + self.app.winfo_height())

    def test_reduced_motion_stops_loop_and_destroy_removes_jobs(self):
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
        menu.start_btn.invoke()
        self.app.update()
        self.assertNotIn(running_job, self.app.tk.call("after", "info"))
        self.assertLess(len(self.app.effects.trace_info()), trace_count)
        self.app.effects.set(False)
        self.app.show_setup()
        self.app.update()
        self.assertIsNone(self.app.screen.animation_job)
        self.assertEqual(len(self.app.effects.trace_info()), trace_count)

    def test_art_is_local_and_missing_art_has_playable_fallback(self):
        self.assertTrue(self.app.screen.art_loaded)
        with patch("menu_ui.tk.PhotoImage", side_effect=tk.TclError("unavailable image")):
            self.app.show_setup()
            self.app.update()
        menu = self.app.screen
        self.assertFalse(menu.art_loaded)
        menu.start_btn.invoke()
        self.assertEqual(self.app.screen.game.status, "playing")


if __name__ == "__main__":
    unittest.main()
