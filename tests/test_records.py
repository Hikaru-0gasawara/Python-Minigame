"""The Records file, in a temporary folder; no display needed."""

from datetime import date
from pathlib import Path
import tempfile
import unittest

from dungeon import EASY, HARD
from records import Records


class RecordsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "ECOS" / "records.json"
        self.records = Records(self.path, today=lambda: date(2026, 10, 9))

    def test_a_missing_file_is_an_empty_scoreboard(self):
        self.assertEqual(self.records.top(EASY), [])

    def test_times_are_kept_sorted_with_seed_players_and_date(self):
        self.assertEqual(self.records.submit(EASY, 90.5, 42, 2), 1)
        self.assertEqual(self.records.submit(EASY, 60, 7, 1), 1)
        self.assertEqual(self.records.submit(EASY, 75, 9, 3), 2)
        again = Records(self.path)                   # read back from the file
        self.assertEqual(again.top(EASY), [
            {"seconds": 60, "seed": 7, "players": 1, "date": "2026-10-09"},
            {"seconds": 75, "seed": 9, "players": 3, "date": "2026-10-09"},
            {"seconds": 90.5, "seed": 42, "players": 2, "date": "2026-10-09"},
        ])

    def test_only_the_five_best_are_kept_and_a_slower_time_ranks_none(self):
        for seconds in (50, 40, 30, 20, 10):
            self.records.submit(EASY, seconds, 1, 1)
        self.assertIsNone(self.records.submit(EASY, 51, 1, 1))
        self.assertIsNone(self.records.submit(EASY, 50, 1, 1))  # a tie ranks behind the older time
        self.assertEqual(self.records.submit(EASY, 15, 2, 1), 2)
        self.assertEqual([r["seconds"] for r in self.records.top(EASY)], [10, 15, 20, 30, 40])

    def test_each_difficulty_has_its_own_records(self):
        self.records.submit(EASY, 100, 1, 1)
        self.assertEqual(self.records.submit(HARD, 200, 2, 1), 1)
        self.assertEqual([r["seconds"] for r in self.records.top(EASY)], [100])
        self.assertEqual([r["seconds"] for r in self.records.top(HARD)], [200])

    def test_a_corrupt_file_reads_as_empty_and_is_replaced_on_the_next_record(self):
        self.path.parent.mkdir(parents=True)
        for junk in ("{not json", "[1, 2]", '{"1": [{"seconds": "fast"}]}', '{"1": 5}',
                     '{"1": [{"seconds": NaN, "seed": 1, "players": 1, "date": "x"}]}',
                     '{"1": [{"seconds": 1e999, "seed": 1, "players": 1, "date": "x"}]}'):
            self.path.write_text(junk, encoding="utf-8")
            self.assertEqual(self.records.top(EASY), [], junk)
        self.assertEqual(self.records.submit(EASY, 30, 1, 1), 1)
        self.assertEqual(len(self.records.top(EASY)), 1)

    def test_a_failed_save_never_raises(self):
        self.path.parent.mkdir(parents=True)
        self.path.mkdir()                            # a folder where the file should be
        self.assertEqual(self.records.submit(EASY, 30, 1, 1), 1)
        self.assertEqual(self.records.top(EASY), [])
