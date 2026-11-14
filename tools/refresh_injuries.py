#!/usr/bin/env python3
"""
Regenerate data/injuries-wk10-2026.csv from the live capture of the official
NFL.com Week 10 injury report, and report every row that changes.

Why this exists
---------------
NFL clubs re-submit practice participation during the week, so the practice
column on https://www.nfl.com/injuries/ is revised between fetches. The
report as a whole is a dated snapshot, not a live feed. When a fresh fetch
disagrees with the stored copy, the stored copy is regenerated from the fresh
snapshot and the difference is published as an irregularity - the policy the
previous session applied when it found 55 such changes.

Usage
-----
    python3 tools/refresh_injuries.py            # rewrite the CSV
    python3 tools/refresh_injuries.py --check    # report only, non-zero if stale
    python3 tools/refresh_injuries.py --diff     # write the change record

The capture under research/verification/ is the evidence; the CSV is derived
from it and can always be rebuilt from it.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_live import read_injury_capture  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "injuries-wk10-2026.csv")
DIFF_PATH = os.path.join(ROOT, "research", "verification", "injuries-diff-2026-11-14.md")
FIELDS = ["team", "player", "pos", "injuries", "practice", "game_status", "player_url"]
SOURCE = "https://www.nfl.com/injuries/"


def read_committed():
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_committed(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def diff(old, new):
    """Return (changed, added, removed) rows keyed on team + player."""
    o = {(r["team"], r["player"]): r for r in old}
    n = {(r["team"], r["player"]): r for r in new}
    changed = []
    for k in sorted(set(o) & set(n)):
        fields = [f for f in FIELDS if o[k].get(f, "") != n[k].get(f, "")]
        if fields:
            changed.append((k, fields, o[k], n[k]))
    added = [n[k] for k in sorted(set(n) - set(o))]
    removed = [o[k] for k in sorted(set(o) - set(n))]
    return changed, added, removed


def write_diff(changed, added, removed):
    lines = [
        "# Change record - NFL.com Week 10 injury report",
        "",
        "Source: <%s> (fetched 2026-11-14 by session `arena/63f321d0-x4`).",
        "Stored snapshot: `data/injuries-wk10-2026.csv`.",
        "",
        "NFL clubs re-submit practice participation during the week, so the",
        "practice column on the league's own report is revised between fetches.",
        "This file records every row that changed between the snapshot committed by",
        "the previous session and the snapshot fetched by this session. Only the",
        "practice-participation column moved; position, injury description, game",
        "status and player URL are identical on every row.",
        "",
        "| # | Team | Player | Practice before | Practice now | Source |",
        "|---|---|---|---|---|---|",
    ]
    for i, (k, fields, o, n) in enumerate(changed, 1):
        assert fields == ["practice"], fields
        lines.append("| %d | %s | %s | %s | %s | [%s](%s) |"
                     % (i, k[0], k[1], o["practice"] or "-", n["practice"] or "-",
                        "nfl.com injury report", SOURCE))
    if added:
        lines += ["", "## Players added by the newer snapshot", "",
                  "| Team | Player | Position | Practice | Game status | Source |",
                  "|---|---|---|---|---|---|"]
        for r in added:
            lines.append("| %s | %s | %s | %s | %s | [nfl.com injury report](%s) |"
                         % (r["team"], r["player"], r["pos"], r["practice"],
                            r["game_status"] or "-", SOURCE))
    if removed:
        lines += ["", "## Players dropped by the newer snapshot", "",
                  "| Team | Player | Position | Practice | Game status | Source |",
                  "|---|---|---|---|---|---|"]
        for r in removed:
            lines.append("| %s | %s | %s | %s | %s | [nfl.com injury report](%s) |"
                         % (r["team"], r["player"], r["pos"], r["practice"],
                            r["game_status"] or "-", SOURCE))
    lines.append("")
    with open(DIFF_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    new = read_injury_capture()
    old = read_committed()
    changed, added, removed = diff(old, new)

    print("stored snapshot: %d rows" % len(old))
    print("live capture   : %d rows" % len(new))
    print("rows changed   : %d (fields moved: %s)"
          % (len(changed), ", ".join(sorted({f for _, fs, _, _ in changed for f in fs})) or "none"))
    print("rows added     : %d" % len(added))
    print("rows removed   : %d" % len(removed))
    for k, fields, o, n in changed[:10]:
        print("  - %s %s: %s -> %s" % (k[0], k[1], o["practice"], n["practice"]))
    if len(changed) > 10:
        print("  ... and %d more" % (len(changed) - 10))

    if mode == "--diff":
        write_diff(changed, added, removed)
        print("wrote %s" % os.path.relpath(DIFF_PATH, ROOT))
        return 0
    if mode == "--check":
        if changed or added or removed:
            print("\nRESULT: STALE - the stored snapshot no longer matches the live "
                  "capture. Run 'python3 tools/refresh_injuries.py'.")
            return 1
        print("\nRESULT: PASS - the stored snapshot matches the live capture exactly.")
        return 0
    if mode in ("--write", "--refresh"):
        write_committed(new)
        write_diff(changed, added, removed)
        print("\nrewrote %s (%d rows) and %s"
              % (os.path.relpath(CSV_PATH, ROOT), len(new),
                 os.path.relpath(DIFF_PATH, ROOT)))
        return 0
    raise SystemExit("unknown mode %r (expected --check, --diff or --write)" % mode)


if __name__ == "__main__":
    sys.exit(main())
