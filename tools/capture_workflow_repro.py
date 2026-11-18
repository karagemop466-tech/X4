#!/usr/bin/env python3
"""Offline regression test for the official-capture control flow (flags F-68 / F-65).

WHY THIS EXISTS
---------------
Four scheduled runs of .github/workflows/capture.yml (2026-11-16 to 2026-11-17) failed
at the fetch step and committed no capture, so the multi-day availability series could
never start. The GitHub Actions job log could not be retrieved (the log blob returns
EOF), so the defect was diagnosed from the step outcome, the run duration, the workflow
source and the reproduction below.

THE DEFECT, AS IT STOOD (F-68)
------------------------------
The Texans publish their depth chart as an image, so tools/depth.py registers their
chart as the empty string. `fetch --kind all` passed that empty string to
urllib.request, which raises ValueError, and ValueErrror was not caught. Even after the
guard against the empty URL was added, the guard set `failed = True`, so `fetch` still
exited non-zero on every run. Because the workflow ran that step without
`continue-on-error`, the hash-verify, freshness and commit steps were all skipped: a
permanently unavailable source (by design, flag F-24) was indistinguishable from a
transient outage, so **no capture could ever be committed**.

THE CONTRACT THIS TEST NOW ENFORCES
-----------------------------------
Repaired by T50 (session arena/cc97fdb0-x4, PR #98), which rebuilt capture_official.py.
With every fetch mocked to return 200 and pass schema, all of the following must hold:

  * every expected structured source is attempted (32: the injury report + 31 charts);
  * the empty Houston URL is never passed to the network layer;
  * `fetch` exits **0**, so the workflow proceeds to verify, freshness and commit;
  * `verify` exits 0 (every stored hash recomputes);
  * `freshness` exits 0 for every expected source.

No network access and no NFL bytes are used: the pages are synthetic. What is exercised
is the control flow, not any published value.

RUN
---
    python3 tools/capture_workflow_repro.py
    echo $?

Exit 0 = the repaired contract still holds. Exit 1 = it has regressed, or the tool has
changed shape again; re-read flags F-65 and F-68 and this test together before shipping.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_official as C  # noqa: E402

# Relative hrefs, exactly the form the official page's raw HTML uses (see PLAYER_LINK
# in capture_official.py). Absolute player URLs are accepted by that pattern too.
INJURY_PAGE = (b"<h2>Injuries - WEEK 11</h2>" + b"Practice Status" * 30
               + b"Game Status" * 30 + b'href="/players/x/"' * 260)
DEPTH_PAGE = b"<table>" + b"synthetic-depth-page" * 200 + b"</table>"


def main():
    root = tempfile.mkdtemp(prefix="capture-repro-")
    C.ROOT = root
    C.CAP_DIR = os.path.join(root, "data", "captures")
    C.MANIFEST = os.path.join(C.CAP_DIR, "manifest.jsonl")

    calls = []

    def fake_http_get(url):
        calls.append(url)
        return (200, INJURY_PAGE if url == C.INJURY_URL else DEPTH_PAGE)

    C.http_get = fake_http_get
    try:
        expected = C.expected_kinds("all")
        fetch_rc = C.fetch("all")
        verify_rc = C.verify()
        freshness_rc = C.freshness(13.0)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("expected structured sources  : %d" % len(expected))
    print("targets attempted            : %d" % len(calls))
    print("blank URL sent to the network: %s" % any(u == "" for u in calls))
    print("fetch exit                   : %d  (must be 0 so the workflow continues)" % fetch_rc)
    print("verify exit                  : %d" % verify_rc)
    print("freshness exit               : %d" % freshness_rc)

    checks = [
        ("every expected source attempted", len(calls) == len(expected)),
        ("no blank URL reached the network", not any(u == "" for u in calls)),
        ("fetch exits 0 so verify/freshness/commit run", fetch_rc == 0),
        ("every stored hash recomputes", verify_rc == 0),
        ("freshness passes for every expected source", freshness_rc == 0),
    ]
    failed = [name for name, ok in checks if not ok]
    print()
    for name, ok in checks:
        print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
    if failed:
        print("\nREGRESSION: %d check(s) failed. Flags F-65 and F-68 were repaired by T50 "
              "(PR #98); this test is the guard on that repair." % len(failed))
        return 1
    print("\nF-68 STAYS FIXED: a declared-unavailable source (Houston's image-only chart) "
          "no longer fails the run, so the workflow reaches its commit step and the "
          "multi-day availability series can accumulate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
