#!/usr/bin/env python3
"""Audit the game log against an independent official-standings capture.

This is the check tools/verify.py structurally cannot make: verify.py
reconciles data/games-2026.csv against data/standings-wk10-2026.csv, which
are the same pair that went jointly stale on 2026-11-18 (flag F-58). This
script rebuilds every club's W/L/T/PF/PA from the game log and compares them
to a standings capture taken directly from the official page at a known date,
so a stale log can no longer agree with a stale snapshot and pass.

Usage:
  python3 tools/audit_score_staleness.py [capture.csv]

capture.csv defaults to the newest research/verification/standings-live-*.csv.
Each row needs: abbr,w,l,t,pf,pa. Exit code 0 = every club reproduces exactly.
"""
import csv
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES = os.path.join(ROOT, "data", "games-2026.csv")


def default_capture():
    files = sorted(glob.glob(os.path.join(ROOT, "research", "verification",
                                          "standings-live-*.csv")))
    return files[-1] if files else None


def rebuild():
    w, l, t, pf, pa = {}, {}, {}, {}, {}
    with open(GAMES, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            a, h = r["away"], r["home"]
            ap, hp = int(r["away_pts"]), int(r["home_pts"])
            for team, scored, allowed in ((a, ap, hp), (h, hp, ap)):
                pf[team] = pf.get(team, 0) + scored
                pa[team] = pa.get(team, 0) + allowed
                w[team] = w.get(team, 0)
                l[team] = l.get(team, 0)
                t[team] = t.get(team, 0)
            if ap > hp:
                w[a] += 1; l[h] += 1
            elif ap < hp:
                w[h] += 1; l[a] += 1
            else:
                t[a] += 1; t[h] += 1
    return w, l, t, pf, pa


def main():
    capture = sys.argv[1] if len(sys.argv) > 1 else default_capture()
    if not capture or not os.path.exists(capture):
        print("no standings capture found; pass a path to one")
        return 2
    w, l, t, pf, pa = rebuild()
    bad = []
    with open(capture, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            team = r["abbr"]
            if team not in pf:
                bad.append("%s: present in capture, no games in log" % team)
                continue
            checks = [("W", w[team], int(r["w"])), ("L", l[team], int(r["l"])),
                      ("T", t[team], int(r["t"])), ("PF", pf[team], int(r["pf"])),
                      ("PA", pa[team], int(r["pa"]))]
            for name, got, want in checks:
                if got != want:
                    bad.append("%s %s: log %d vs capture %d" % (team, name, got, want))
    print("capture: %s" % os.path.relpath(capture, ROOT))
    print("clubs checked: %d" % len(set(pf)))
    if bad:
        print("RESULT: FAIL - the log does not reproduce the capture:")
        for line in bad:
            print("  " + line)
        return 1
    print("RESULT: PASS - the log reproduces every club's W/L/T/PF/PA in the capture.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
