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
        self.patches = [
            mock.patch.object(capture, "ROOT", self.root),
            mock.patch.object(capture, "CAP_DIR", self.capture_dir),
            mock.patch.object(capture, "MANIFEST", self.manifest),
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
            return {"kind": kind, "fetched_utc": stamp, "http_status": 200,
                    "schema_ok": True, "file": "data/captures/" + kind.replace("/", "_") + ".gz"}

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


if __name__ == "__main__":
    unittest.main()
