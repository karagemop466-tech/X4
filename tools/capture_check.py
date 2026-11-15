#!/usr/bin/env python3
"""
Drift alarm for the Week 10 official injury report.

WHAT IT CHECKS
--------------
The committed dataset data/injuries-wk10-2026.csv must equal the line-by-line
transcription of the official NFL.com injury report held in
research/verification/official-injury-report-wk10-capture-2026-11-15.csv.

  * same set of (team, player) keys in both files - no row added or dropped;
  * identical position, injury text, practice status and game status for every row;
  * the row count and team count are PINNED below, so a changed report fails the
    build loudly instead of quietly publishing a stale or partial table;
  * every practice status is one of Full / Limited / DNP and every game status is
    blank, Questionable, Doubtful or Out (the report's own vocabulary).

Exit status 0 = consistent, 1 = drift or schema failure (the build must stop).

To accept a newer official read: re-transcribe the page into the capture file,
run this script, then regenerate the dataset through the normal pipeline and
update the pinned counts in the same commit. Never patch one side by hand.

Usage:  python3 tools/capture_check.py
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURE = os.path.join(ROOT, "research", "verification",
                       "official-injury-report-wk10-capture-2026-11-15.csv")
COMMITTED = os.path.join(ROOT, "data", "injuries-wk10-2026.csv")

# Pinned from the official read of 2026-11-15 (see F-41).
EXPECTED_ROWS = 347
EXPECTED_TEAMS = 28
PRACTICE = {"Full", "Limited", "DNP"}
GAME = {"", "Questionable", "Doubtful", "Out"}
FIELDS = ("pos", "injuries", "practice", "game_status")


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def key_of(team, player):
    return (team, player)


def main():
    failures = []
    cap = load(CAPTURE)
    com = load(COMMITTED)

    # the official page calls Arizona "AZ"; the dataset uses the standard "ARI"
    for r in cap:
        if r["team"] == "AZ":
            r["team"] = "ARI"

    if len(cap) != EXPECTED_ROWS:
        failures.append("capture holds %d rows, pinned %d" % (len(cap), EXPECTED_ROWS))
    if len(com) != EXPECTED_ROWS:
        failures.append("committed dataset holds %d rows, pinned %d" % (len(com), EXPECTED_ROWS))
    teams = {r["team"] for r in cap}
    if len(teams) != EXPECTED_TEAMS:
        failures.append("capture covers %d teams, pinned %d" % (len(teams), EXPECTED_TEAMS))

    cap_k = {}
    for r in cap:
        k = key_of(r["team"], r["player"])
        if k in cap_k:
            failures.append("duplicate capture row %s %s" % k)
        cap_k[k] = r
    com_k = {}
    for r in com:
        k = key_of(r["team"], r["player"])
        if k in com_k:
            failures.append("duplicate committed row %s %s" % k)
        com_k[k] = r

    for k in sorted(set(cap_k) - set(com_k)):
        failures.append("official row missing from dataset: %s %s" % k)
    for k in sorted(set(com_k) - set(cap_k)):
        failures.append("dataset row not on official report: %s %s" % k)

    cells = 0
    for k in sorted(set(cap_k) & set(com_k)):
        a, b = cap_k[k], com_k[k]
        for f in FIELDS:
            cells += 1
            if a[f] != b[f]:
                failures.append("%s %s: %s official=%r dataset=%r" % (k[0], k[1], f, a[f], b[f]))

    for r in cap:
        if r["practice"] not in PRACTICE:
            failures.append("unknown practice status %r for %s %s" % (r["practice"], r["team"], r["player"]))
        if r["game_status"] not in GAME:
            failures.append("unknown game status %r for %s %s" % (r["game_status"], r["team"], r["player"]))

    print("official capture rows:   %d (%d teams)" % (len(cap), len(teams)))
    print("committed dataset rows:  %d" % len(com))
    print("field comparisons:       %d" % cells)
    if failures:
        print("RESULT: FAIL - %d difference(s)" % len(failures))
        for line in failures[:60]:
            print("  - " + line)
        if len(failures) > 60:
            print("  ... %d more" % (len(failures) - 60))
        return 1
    print("RESULT: PASS - the committed injury dataset matches the official capture cell for cell")
    return 0


if __name__ == "__main__":
    sys.exit(main())
