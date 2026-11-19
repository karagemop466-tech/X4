"""Offline tests for tools/capture_alert.py (T68). No network, no clock: every time is injected."""
import datetime as dt
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tools import capture_alert as alert


def read(stamp, kind="injuries", schema_ok=True, http=200, coverage=None, error=None, **schema):
    entry = {"fetched_utc": stamp, "kind": kind, "http_status": http, "schema_ok": schema_ok,
             "sha256": "a" * 64 if schema_ok else None, "schema": dict(schema)}
    if coverage:
        entry["schema"]["coverage"] = coverage
    if error:
        entry["error"] = error
    return entry


NOW = dt.datetime(2026, 11, 19, 20, 0, 0)


class EvaluateTests(unittest.TestCase):
    def only(self, entries, max_hours=13.0, now=NOW):
        rows = alert.evaluate(entries, ["injuries"], max_hours, now)
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_fresh_valid_read_is_ok(self):
        row = self.only([read("2026-11-19T12:00:00Z")])
        self.assertEqual(row["status"], "OK")
        self.assertEqual(row["age_hours"], 8.0)

    def test_valid_but_partial_coverage_is_partial_not_failing(self):
        row = self.only([read("2026-11-19T12:00:00Z", coverage="partial",
                              games_published=12, games_scheduled=13)])
        self.assertEqual(row["status"], "PARTIAL")
        self.assertIn("12 of 13", row["detail"])
        self.assertNotIn(row["status"], alert.FAILING)

    def test_read_older_than_the_limit_is_stale(self):
        row = self.only([read("2026-11-19T06:00:00Z")])
        self.assertEqual(row["status"], "STALE")
        self.assertEqual(row["age_hours"], 14.0)

    def test_limit_is_inclusive_at_exactly_max_hours(self):
        self.assertEqual(self.only([read("2026-11-19T07:00:00Z")])["status"], "OK")

    def test_newest_attempt_failing_after_a_valid_read_is_failed_last(self):
        row = self.only([read("2026-11-19T12:00:00Z"),
                         read("2026-11-19T19:00:00Z", schema_ok=False, week="11")])
        self.assertEqual(row["status"], "FAILED_LAST")
        self.assertEqual(row["last_valid_utc"], "2026-11-19T12:00:00Z")
        self.assertFalse(row["last_attempt_ok"])

    def test_failed_attempt_older_than_a_newer_valid_read_is_not_failed_last(self):
        row = self.only([read("2026-11-18T07:37:40Z", schema_ok=False),
                         read("2026-11-19T12:00:00Z")])
        self.assertEqual(row["status"], "OK")

    def test_http_error_counts_as_a_failed_attempt(self):
        row = self.only([read("2026-11-19T12:00:00Z"),
                         read("2026-11-19T18:00:00Z", http=503, schema_ok=False)])
        self.assertEqual(row["status"], "FAILED_LAST")

    def test_no_valid_read_ever_is_missing(self):
        row = self.only([read("2026-11-19T12:00:00Z", schema_ok=False)])
        self.assertEqual(row["status"], "MISSING")
        self.assertIsNone(row["last_valid_utc"])

    def test_source_with_no_entries_at_all_is_missing(self):
        rows = alert.evaluate([], ["injuries", "depth/SEA"], 13.0, NOW)
        self.assertEqual([r["status"] for r in rows], ["MISSING", "MISSING"])

    def test_entries_for_other_sources_and_bad_stamps_are_ignored(self):
        rows = alert.evaluate([read("2026-11-19T12:00:00Z", kind="depth/SEA"),
                               read("not-a-time")], ["injuries"], 13.0, NOW)
        self.assertEqual(rows[0]["status"], "MISSING")

    def test_an_error_record_is_never_a_valid_read(self):
        row = self.only([read("2026-11-19T19:59:00Z", error="timeout")])
        self.assertEqual(row["status"], "MISSING")

    def test_a_read_stamped_after_now_is_stale_not_ok(self):
        row = self.only([read("2026-11-19T21:00:00Z")])
        self.assertEqual(row["status"], "STALE")


class ReportAndMainTests(unittest.TestCase):
    def test_report_lists_each_failing_source_with_its_status(self):
        rows = alert.evaluate([read("2026-11-19T06:00:00Z")], ["injuries"], 13.0, NOW)
        text = alert.render_report(rows, 13.0, NOW)
        self.assertIn("| injuries | STALE |", text)
        self.assertIn("1 of 1 sources failing", text)

    def test_main_exit_codes_and_manifest_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "manifest.jsonl")
            import json
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(read("2026-11-19T12:00:00Z")) + "\n")
            with mock.patch.object(alert.capture, "MANIFEST", path):
                with redirect_stdout(io.StringIO()):
                    ok = alert.main(["check", "--kind", "injuries", "--now", "2026-11-19T20:00:00Z"])
                    stale = alert.main(["check", "--kind", "injuries", "--now", "2026-11-20T08:00:00Z"])
            self.assertEqual(ok, 0)
            self.assertEqual(stale, 1)

    def test_main_returns_2_when_the_manifest_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(alert.capture, "MANIFEST", os.path.join(tmp, "missing", "x.jsonl")):
                with redirect_stdout(io.StringIO()):
                    # read_manifest returns [] for a missing file, so force an unreadable one
                    with mock.patch.object(alert.capture, "read_manifest", side_effect=OSError("boom")):
                        self.assertEqual(alert.main(["check", "--kind", "injuries"]), 2)

    def test_the_committed_manifest_is_readable_and_evaluates(self):
        entries = alert.capture.read_manifest()
        self.assertGreater(len(entries), 0)
        rows = alert.evaluate(entries, ["injuries"], 13.0, NOW)
        self.assertIn(rows[0]["status"], ("OK", "PARTIAL", "STALE", "FAILED_LAST", "MISSING"))


if __name__ == "__main__":
    unittest.main()
