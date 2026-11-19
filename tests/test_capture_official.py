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

    def test_current_week_partial_two_club_report_passes(self):
        # The official report is published progressively. An early snapshot with
        # one matchup (two club tables) is a valid point-in-time capture, not a
        # malformed full-week report. Fixture markup is synthetic; no player rows
        # or raw official page content are stored in this repository.
        raw = (b"<h2>Injuries - WEEK 11</h2>"
               + b"<table><th>Practice Status</th><th>Game Status</th></table>" * 2
               + b'<a href="/players/test-player/">Player</a>' * 26)
        ok, detail = capture.schema_injuries(raw)
        self.assertTrue(ok, detail)
        self.assertEqual(detail["week"], "11")
        self.assertEqual(detail["practice_status_headers"], 2)
        self.assertEqual(detail["game_status_headers"], 2)
        self.assertEqual(detail["player_links"], 26)

    def test_empty_or_single_table_week_shell_fails_closed(self):
        heading = b"Injuries - WEEK 11 "
        one_table = heading + b"Practice Status Game Status " + b'<a href="/players/test/">x</a>' * 30
        empty = heading + b"Practice Status Game Status " * 28
        self.assertFalse(capture.schema_injuries(one_table)[0])
        self.assertFalse(capture.schema_injuries(empty)[0])

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
