#!/usr/bin/env python3
"""Compute the change between two dated official captures of the Week 10 injury report.

Implements "publish the delta, never the level" and the weekly 'what changed' diff:

  capture A  research/verification/live-sweep-injuries-2026-11-14-e6ee28a8.csv
             345 rows read from the official NFL.com Week 10 report on 2026-11-14 (T33 sweep)
  capture B  data/injuries-wk10-2026.csv
             347 rows read from the same official report on 2026-11-15 (T37 recapture;
             the committed dataset was regenerated from that read)

Join key: (team, player, position). Nothing is inferred: a cell that moved is reported
with its value in capture A and its value in capture B. The 2026-11-15 capture is the
committed dataset, so a reviewer can check capture B cell by cell against
research/verification/official-injury-report-wk10-capture-2026-11-15.csv.

Output: research/data/injury-report-delta-wk10.csv (written by main(); the page builder
imports compute() so the published page is derived from the same computation).

Run:  python3 tools/injury_delta.py
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

A_PATH = os.path.join(ROOT, "research", "verification",
                      "live-sweep-injuries-2026-11-14-e6ee28a8.csv")
B_PATH = os.path.join(ROOT, "data", "injuries-wk10-2026.csv")
OUT_PATH = os.path.join(ROOT, "research", "data", "injury-report-delta-wk10.csv")

A_LABEL = "2026-11-14 official capture (T33 live sweep, 345 rows)"
B_LABEL = "2026-11-15 official capture (T37 full read, committed dataset)"


def _read_a():
    rows = {}
    urls = {}
    with open(A_PATH, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            key = r["key"].strip()
            tail_team, team = key.rsplit(" ", 1)
            url, name = tail_team.split(" ", 1)
            k = (team, name, r["pos"])
            rows[k] = (r["practice"], r["game_status"], r["injuries"])
            urls[k] = url
    return rows, urls


def _read_b():
    rows, urls = {}, {}
    with open(B_PATH, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k = (r["team"], r["player"], r["pos"])
            rows[k] = (r["practice"], r["game_status"], r["injuries"])
            urls[k] = r["player_url"]
    return rows, urls


def compute():
    a, urls_a = _read_a()
    b, urls_b = _read_b()
    fields = ("practice", "game_status", "injuries")
    added = sorted(b.keys() - a.keys())
    removed = sorted(a.keys() - b.keys())
    changed = []
    n_cells = 0
    for k in sorted(a.keys() & b.keys()):
        for i, f in enumerate(fields):
            if a[k][i] != b[k][i]:
                changed.append((k, f, a[k][i], b[k][i]))
                n_cells += 1
    meta = {
        "rows_a": len(a), "rows_b": len(b),
        "added": len(added), "removed": len(removed),
        "changed_rows": len({k for k, _, _, _ in changed}),
        "changed_cells": n_cells,
        "a_label": A_LABEL, "b_label": B_LABEL,
    }
    return added, removed, changed, urls_a, urls_b, meta


def delta_rows():
    """Flat row list for the CSV: one row per changed cell, one per added/removed player."""
    added, removed, changed, urls_a, urls_b, meta = compute()
    out = []
    for k in added:
        out.append(["player added", k[0], k[1], k[2], "row", "", "", A_LABEL, B_LABEL,
                    urls_b.get(k, "")])
    for k in removed:
        out.append(["player removed", k[0], k[1], k[2], "row", "", "", A_LABEL, B_LABEL,
                    urls_a.get(k, "")])
    for (team, player, pos), field, old, new in changed:
        out.append(["cell changed", team, player, pos, field, old, new, A_LABEL, B_LABEL,
                    urls_b.get((team, player, pos), "")])
    return out


def main():
    rows = delta_rows()
    _, _, _, _, _, meta = compute()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["change_type", "team", "player", "pos", "field",
                    "value_at_2026_11_14", "value_at_2026_11_15",
                    "capture_a", "capture_b", "player_url"])
        w.writerows(rows)
    print("wrote research/data/injury-report-delta-wk10.csv: %d delta rows" % len(rows))
    print("captures: A=%d rows, B=%d rows; added=%d removed=%d changed cells=%d on %d players"
          % (meta["rows_a"], meta["rows_b"], meta["added"], meta["removed"],
             meta["changed_cells"], meta["changed_rows"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
