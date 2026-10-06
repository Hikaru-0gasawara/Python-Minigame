"""Tk integration checks. Requires an available Tk display."""

import unittest

from dungeon_ui import DungeonApp


class DungeonUITests(unittest.TestCase):
    def setUp(self):
        self.app = DungeonApp()
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
        self.app.start(1, 1)
        self.app.update()
        screen = self.app.screen
        screen.enter(1)
        screen.answer.insert(0, screen.game.question["answer"])
        screen.submit()
        self.assertTrue(screen.game.current.cleared)
        screen.enter(0)
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


if __name__ == "__main__":
    unittest.main()
