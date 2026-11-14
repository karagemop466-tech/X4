#!/usr/bin/env python3
"""
Diff a live capture of an official NFL.com page against the committed dataset.

The capture files live in research/verification/ and are verbatim excerpts of
the official page, fetched directly (never from a search snippet). This script
re-reads them and compares every field with the CSV the site publishes, so a
typo in a published number cannot survive a re-verification.

Usage:
    python3 tools/verify_live.py standings

Exit code 0 = the committed data matches the official source exactly.
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIF = os.path.join(ROOT, "research", "verification")

# The capture row is a markdown table row whose first cell holds the club logo
# markdown and the club name; the numeric columns follow, in the order the
# official page's own legend defines them: W, L, T, PCT, PF, PA, NET PTS.
ROW = re.compile(r"^\|\s*\[!\[[^\]]*\]\([^)]*\)\\?<br>\\?<br>(?P<name>[^<|]+?)<br>")
CELL = re.compile(r"(?<![\d.\-])\(?-?\d+(?:\.\d+)?\)?(?=\s*\|)")


def parse_capture(path):
    """Return {club name: (w, l, t, pct, pf, pa, net)} from a live capture file."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = ROW.match(line)
            if not m:
                continue
            name = m.group("name").strip()
            cells = [c.strip() for c in line.rstrip().rstrip("|").split("|")]
            # The first cell of a markdown row is empty; the second holds the
            # logo and the club name; the next seven are the official W, L, T,
            # PCT, PF, PA and NET PTS columns.
            nums = []
            for c in cells[2:]:
                c = c.strip()
                if re.fullmatch(r"-?\d+(?:\.\d+)?", c):
                    nums.append(c)
                elif re.fullmatch(r"\(-?\d+(?:\.\d+)?\)", c):
                    nums.append(c.strip("()"))
                else:
                    break
            if len(nums) < 7:
                raise SystemExit("capture row for %s has %d numeric cells, expected 7"
                                 % (name, len(nums)))
            out[name] = nums[:7]
    return out


def check_standings():
    live = parse_capture(os.path.join(VERIF, "standings-live-2026-11-14.md"))
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "standings-wk10-2026.csv"))))
    committed = {r["team"]: r for r in rows}

    problems = []
    checked = 0
    if len(live) != 32:
        problems.append("live capture holds %d clubs, expected 32" % len(live))
    if len(committed) != 32:
        problems.append("committed CSV holds %d clubs, expected 32" % len(committed))

    for name, vals in sorted(live.items()):
        c = committed.get(name)
        if c is None:
            problems.append("%s: on the official page but not in the committed CSV" % name)
            continue
        checked += 1
        fields = (("w", vals[0]), ("l", vals[1]), ("t", vals[2]), ("pct", vals[3]),
                  ("pf", vals[4]), ("pa", vals[5]), ("net_pts", vals[6]))
        for key, live_v in fields:
            got = c[key]
            if key == "pct":
                if abs(float(got) - float(live_v)) > 1e-9:
                    problems.append("%s: %s committed %s but official page says %s"
                                    % (name, key, got, live_v))
            elif int(got) != int(live_v):
                problems.append("%s: %s committed %s but official page says %s"
                                % (name, key, got, live_v))
        # internal arithmetic, proved on the official numbers
        if int(c["pf"]) - int(c["pa"]) != int(c["net_pts"]):
            problems.append("%s: net points is not points for minus points allowed" % name)

    for name in committed:
        if name not in live:
            problems.append("%s: in the committed CSV but not on the official page" % name)

    print("standings rows checked against the live NFL.com capture: %d" % checked)
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("RESULT: PASS - all 32 clubs match the official NFL.com standings on "
          "W, L, T, PCT, PF, PA and NET PTS.")
    return 0


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "standings"
    if what == "standings":
        return check_standings()
    raise SystemExit("unknown check %r" % what)


if __name__ == "__main__":
    sys.exit(main())
