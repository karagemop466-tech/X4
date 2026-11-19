import datetime as dt
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from tools import capture_official as capture


class CaptureOfficialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = self.temp.name
        self.capture_dir = os.path.join(self.root, "data", "captures")
        self.manifest = os.path.join(self.capture_dir, "manifest.jsonl")
        self.raw_dir = os.path.join(self.root, "private-raw-store")
        self.patches = [
            mock.patch.object(capture, "ROOT", self.root),
            mock.patch.object(capture, "CAP_DIR", self.capture_dir),
            mock.patch.object(capture, "MANIFEST", self.manifest),
            mock.patch.object(capture, "RAW_DIR", None),   # default: raw bytes are not retained
        ]
        for patcher in self.patches:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp.cleanup()

    def test_all_capture_skips_image_only_houston_and_visits_other_structured_sources(self):
        calls = []

        def get(url):
            calls.append(url)
            return 200, b"synthetic offline test page"

        with mock.patch.object(capture, "http_get", side_effect=get), \
                mock.patch.object(capture, "schema_injuries", return_value=(True, {})), \
                mock.patch.object(capture, "schema_depth", return_value=(True, {})):
            self.assertEqual(capture.fetch("all"), 0)

        self.assertEqual(len(calls), len(capture.expected_kinds("all")))
        self.assertEqual(len(calls), 32)  # injury report + 31 structured charts
        self.assertNotIn("", calls)
        self.assertNotIn("depth/HOU", [e["kind"] for e in capture.read_manifest()])
        self.assertEqual(capture.freshness(13), 0)

    def test_fetch_error_is_written_to_manifest_and_does_not_stop_later_sources(self):
        calls = []

        def get(url):
            calls.append(url)
            if url == capture.INJURY_URL:
                raise urllib.error.URLError("synthetic unavailable")
            return 200, b"synthetic chart"

        with mock.patch.object(capture, "http_get", side_effect=get), \
                mock.patch.object(capture, "schema_depth", return_value=(True, {})):
            self.assertEqual(capture.fetch("all"), 2)

        entries = capture.read_manifest()
        failed = [entry for entry in entries if entry.get("error")]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["kind"], "injuries")
        self.assertEqual(len(calls), 32)
        self.assertEqual(capture.freshness(13), 1)

    def test_freshness_ignores_recent_failure_and_schema_invalid_rows(self):
        now = dt.datetime(2026, 11, 17, 12, 0, 0)
        good = {
            "kind": "injuries", "fetched_utc": "2026-11-17T11:00:00Z",
            "http_status": 200, "schema_ok": True, "file": "data/captures/injury.gz",
        }
        failure = {
            "kind": "depth/ARI", "fetched_utc": "2026-11-17T11:59:00Z",
            "http_status": None, "schema_ok": False, "error": "offline",
        }
        schema_bad = {
            "kind": "depth/BUF", "fetched_utc": "2026-11-17T11:59:00Z",
            "http_status": 200, "schema_ok": False, "file": "data/captures/buf.gz",
        }
        self.assertEqual(capture.freshness(13, ["injuries", "depth/ARI", "depth/BUF"],
                                            [good, failure, schema_bad], now), 1)

    def test_freshness_rejects_stale_valid_capture_and_accepts_complete_fresh_set(self):
        now = dt.datetime(2026, 11, 17, 12, 0, 0)
        def entry(kind, stamp):
            return {"kind": kind, "fetched_utc": stamp, "http_status": 200, "schema_ok": True,
                    "sha256": capture.sha256(kind.encode())}

        entries = [entry("injuries", "2026-11-17T11:00:00Z"),
                   entry("depth/ARI", "2026-11-17T10:00:00Z")]
        self.assertEqual(capture.freshness(13, ["injuries", "depth/ARI"], entries, now), 0)
        entries[1] = entry("depth/ARI", "2026-11-16T22:00:00Z")
        self.assertEqual(capture.freshness(13, ["injuries", "depth/ARI"], entries, now), 1)

    def test_previous_hash_is_from_same_source_not_last_global_manifest_entry(self):
        first = capture.store("injuries", capture.INJURY_URL, b"injury-v1", 200,
                              True, {}, [])
        other = capture.store("depth/ARI", "https://club.example/depth", b"depth-v1", 200,
                              True, {}, [first])
        changed = capture.store("injuries", capture.INJURY_URL, b"injury-v2", 200,
                                True, {}, [first, other])
        self.assertEqual(changed["previous_sha256"], first["sha256"])


class InjurySchemaTests(unittest.TestCase):
    """Schema markers, tested on synthetic markup and on one immutable real capture."""

    def test_relative_and_absolute_player_links_are_both_counted(self):
        head = b"Injuries - WEEK 10 " + b"Practice Status Game Status " * 28
        ok, detail = capture.schema_injuries(head + b'<a href="/players/a/">' * 130 + b'<a href="https://www.nfl.com/players/b/">' * 130)
        self.assertTrue(ok)
        self.assertEqual(detail["player_links"], 260)
        ok, detail = capture.schema_injuries(head + b'<a href="/teams/x/">' * 300)
        self.assertFalse(ok)
        self.assertEqual(detail["player_links"], 0)

    def test_pinned_real_week10_capture_passes_the_schema(self):
        # Runs only where the owner's private raw store is configured (X4_CAPTURE_RAW_DIR).
        # Raw official bytes are never committed, so a plain checkout skips this test.
        raw_dir = os.environ.get("X4_CAPTURE_RAW_DIR")
        path = os.path.join(raw_dir or "", "injuries", "20261118T034010Z_1d896816da9a.html.gz")
        if not raw_dir or not os.path.exists(path):
            self.skipTest("pinned private capture not configured in this environment")
        import gzip
        with gzip.open(path, "rb") as f:
            raw = f.read()
        ok, detail = capture.schema_injuries(raw)
        self.assertTrue(ok, detail)
        self.assertEqual(detail["week"], "10")
        self.assertEqual(detail["practice_status_headers"], 28)
        self.assertEqual(detail["player_links"], 347)  # the 347 body rows of the official Week 10 report


class RawBytePolicyTests(unittest.TestCase):
    """Raw official bytes are kept only in a private store outside the repository."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = self.temp.name
        self.capture_dir = os.path.join(self.root, "data", "captures")
        self.raw_dir = os.path.join(self.root, "..private-raw-store")
        self.patches = [
            mock.patch.object(capture, "ROOT", self.root),
            mock.patch.object(capture, "CAP_DIR", self.capture_dir),
            mock.patch.object(capture, "MANIFEST", os.path.join(self.capture_dir, "manifest.jsonl")),
        ]
        for patcher in self.patches:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp.cleanup()

    def test_default_keeps_hash_and_metadata_but_no_raw_bytes(self):
        with mock.patch.object(capture, "RAW_DIR", None):
            entry = capture.store("injuries", capture.INJURY_URL, b"official-bytes", 200, True, {}, [])
        self.assertEqual(entry["sha256"], capture.sha256(b"official-bytes"))
        self.assertFalse(entry["raw_retained"])
        self.assertNotIn("file", entry)
        self.assertFalse(os.path.exists(self.capture_dir))  # nothing written under the repository

    def test_private_store_receives_bytes_outside_the_repository(self):
        with mock.patch.object(capture, "RAW_DIR", self.raw_dir):
            entry = capture.store("depth/ARI", "https://club.example/depth", b"chart", 200, True, {}, [])
            self.assertTrue(entry["raw_retained"])
            self.assertEqual(entry["raw_store"], "private")
            self.assertTrue(os.path.exists(os.path.join(self.raw_dir, entry["file"])))
            self.assertFalse(os.path.exists(self.capture_dir))
            self.assertEqual(capture.verify(), 0)

    def test_hash_only_entries_are_counted_not_failed(self):
        os.makedirs(self.capture_dir, exist_ok=True)
        with open(os.path.join(self.capture_dir, "manifest.jsonl"), "w", encoding="utf-8") as f:
            f.write('{"kind": "injuries", "sha256": "%s", "schema_ok": true, "http_status": 200, '
                    '"fetched_utc": "2026-11-18T03:40:10Z"}\n' % capture.sha256(b"x"))
            f.write('{"kind": "depth/ARI", "error": "offline", "schema_ok": false}\n')
        self.assertEqual(capture.verify(), 0)

    def test_referenced_but_absent_legacy_file_is_reported_not_failed(self):
        os.makedirs(self.capture_dir, exist_ok=True)
        with open(os.path.join(self.capture_dir, "manifest.jsonl"), "w", encoding="utf-8") as f:
            f.write('{"kind": "injuries", "sha256": "%s", "schema_ok": true, "http_status": 200, '
                    '"fetched_utc": "2026-11-18T03:39:04Z", "file": "data/captures/injuries/x.html.gz"}\n'
                    % capture.sha256(b"x"))
        self.assertEqual(capture.verify(), 0)

if __name__ == "__main__":
    unittest.main()


def _report(week, club_tables, links_per_table=12):
    """Synthetic official-report markup: one heading, one practice and one game header per club table,
    and player links. Shapes mirror the manifest counts recorded in data/captures/manifest.jsonl."""
    parts = [b"Injuries - WEEK " + str(week).encode() + b"\n"]
    for _ in range(club_tables):
        parts.append(b"<th>Practice Status</th><th>Game Status</th>\n")
        parts.append(b'<a href="/players/p/">' * links_per_table)
    return b"".join(parts)


class PartialReportSchemaTests(unittest.TestCase):
    """T60: a legitimate partial report is a snapshot with a coverage field, not a schema failure."""

    def test_week11_one_game_read_from_manifest_is_partial_and_valid(self):
        # Manifest 2026-11-18T07:37:40Z and 20:37:55Z: week 11, 2 headers, 26 player links.
        raw = _report(11, 2, links_per_table=13)
        ok, detail = capture.schema_injuries(raw)
        self.assertTrue(ok, detail)
        self.assertEqual(detail["week"], "11")
        self.assertEqual(detail["player_links"], 26)
        self.assertEqual(detail["games_scheduled"], 13)   # data/schedule-wk11-2026.csv
        self.assertEqual(detail["games_published"], 1)
        self.assertEqual(detail["coverage"], "partial")

    def test_week11_full_report_is_complete(self):
        ok, detail = capture.schema_injuries(_report(11, 26))
        self.assertTrue(ok, detail)
        self.assertEqual(detail["coverage"], "complete")

    def test_week10_full_report_is_complete_against_fourteen_scheduled_games(self):
        ok, detail = capture.schema_injuries(_report(10, 28))
        self.assertTrue(ok, detail)
        self.assertEqual(detail["games_scheduled"], 14)
        self.assertEqual(detail["coverage"], "complete")

    def test_more_club_tables_than_scheduled_games_fails(self):
        ok, detail = capture.schema_injuries(_report(11, 28))   # 14 games published for a 13-game week
        self.assertFalse(ok)
        self.assertEqual(detail["coverage"], "over")

    def test_page_with_no_player_rows_fails_even_with_full_headers(self):
        # Manifest 2026-11-18T03:39:04Z: week 10, 28 headers, 0 player links (unexplained; stays a failure).
        raw = b"Injuries - WEEK 10 " + b"<th>Practice Status</th><th>Game Status</th>" * 28
        ok, detail = capture.schema_injuries(raw)
        self.assertFalse(ok)
        self.assertEqual(detail["player_links"], 0)

    def test_odd_or_unpaired_table_count_fails(self):
        self.assertFalse(capture.schema_injuries(_report(11, 3))[0])
        raw = _report(11, 2) + b"<th>Practice Status</th>"   # practice headers no longer equal game headers
        self.assertFalse(capture.schema_injuries(raw)[0])

    def test_missing_week_heading_fails(self):
        raw = _report(11, 2).replace(b"Injuries - WEEK 11", b"Injuries")
        ok, detail = capture.schema_injuries(raw)
        self.assertFalse(ok)
        self.assertIsNone(detail["week"])

    def test_week_without_committed_schedule_has_unknown_coverage_not_a_guess(self):
        ok, detail = capture.schema_injuries(_report(99, 2))
        self.assertTrue(ok, detail)
        self.assertIsNone(detail["games_scheduled"])
        self.assertEqual(detail["coverage"], "unknown")


class DeltaWeekFilterTests(unittest.TestCase):
    """tools/capture_delta.py must never diff a Week 11 capture against the Week 10 dataset."""

    def test_newest_valid_capture_is_restricted_to_the_committed_week(self):
        import json
        from tools import capture_delta as delta
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        manifest = os.path.join(temp.name, "manifest.jsonl")
        week10 = {"kind": "injuries", "schema_ok": True, "file": "injuries/w10.html.gz", "http_status": 200,
                  "schema": {"week": "10"}, "fetched_utc": "2026-11-18T03:40:10Z"}
        week11 = dict(week10, file="injuries/w11.html.gz", schema={"week": "11"},
                      fetched_utc="2026-11-18T20:37:55Z")
        with open(manifest, "w", encoding="utf-8") as f:
            for entry in (week10, week11):
                f.write(json.dumps(entry) + "\n")
        with mock.patch.object(delta, "MANIFEST", manifest):
            self.assertEqual(delta.latest_valid_capture()["file"], "injuries/w10.html.gz")
