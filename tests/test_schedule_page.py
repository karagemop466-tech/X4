"""Offline tests for tools/schedule_page.py (T72). No network: they run on the committed data."""
import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import schedule_page as sp  # noqa: E402


class ScheduleAnnouncementTests(unittest.TestCase):
    def setUp(self):
        self.rows = sp.load_announcement()

    def test_committed_announcement_is_valid(self):
        sp.validate_announcement(self.rows)

    def test_row_count_is_pinned(self):
        self.assertEqual(len(self.rows), sp.EXPECTED_ANNOUNCEMENT_ROWS)

    def test_every_row_quotes_the_official_release(self):
        for r in self.rows:
            self.assertEqual(r["source_url"], sp.ANNOUNCEMENT_URL, r["id"])
            self.assertTrue(r["verbatim_excerpt"].strip(), r["id"])

    def test_weekday_mismatch_fails(self):
        bad = copy.deepcopy(self.rows)
        for r in bad:
            if r["iso_date"]:
                r["weekday"] = "Monday"
                break
        with self.assertRaises(sp.ValidationError):
            sp.validate_announcement(bad)

    def test_non_official_host_fails(self):
        bad = copy.deepcopy(self.rows)
        bad[0]["source_url"] = "https://example.com/schedule"
        with self.assertRaises(sp.ValidationError):
            sp.validate_announcement(bad)

    def test_blank_required_field_fails(self):
        bad = copy.deepcopy(self.rows)
        bad[2]["verbatim_excerpt"] = ""
        with self.assertRaises(sp.ValidationError):
            sp.validate_announcement(bad)

    def test_row_count_drift_fails(self):
        with self.assertRaises(sp.ValidationError):
            sp.validate_announcement(self.rows[:-1])

    def test_known_dates_match_the_calendar(self):
        dated = {r["iso_date"]: r["weekday"] for r in self.rows if r["iso_date"]}
        self.assertEqual(dated["2026-09-09"], "Wednesday")
        self.assertEqual(dated["2027-01-09"], "Saturday")
        self.assertEqual(dated["2027-01-10"], "Sunday")


class Week11Tests(unittest.TestCase):
    def test_committed_week11_is_valid(self):
        sp.validate_week11(sp.load_week11())

    def test_week11_row_count_is_pinned(self):
        self.assertEqual(len(sp.load_week11()), sp.EXPECTED_WEEK11_ROWS)

    def test_week11_missing_link_fails(self):
        rows = copy.deepcopy(sp.load_week11())
        rows[0]["nfl_url"] = ""
        with self.assertRaises(sp.ValidationError):
            sp.validate_week11(rows)


class PageTests(unittest.TestCase):
    def test_page_renders_both_columns_and_the_open_item(self):
        body = sp.build_body(sp.validate_announcement(sp.load_announcement()),
                             sp.validate_week11(sp.load_week11()))
        self.assertIn("Dated announcement", body)
        self.assertIn("Live schedule", body)
        self.assertIn("Not yet published by the league", body)
        self.assertIn(sp.ANNOUNCEMENT_URL, body)


if __name__ == "__main__":
    unittest.main()
