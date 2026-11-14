#!/usr/bin/env python3
"""
Reconcile the two independently captured price stores (T31, integration).

Two sessions captured the same provider's prices for the same games, eighteen
minutes apart, in two different shapes:

  * `research/data/price_snapshots_2026.csv` - the integrity capture (session
    `arena/e8a1af1b-x4`): one row per game, with an opening, a current and a
    closing column for each market. 14 games.
  * `data/market-prices-2026.csv` - the price archive (session
    `arena/1b8b6e9e-x4`): one row per event, market and side, with an opening
    and a closing line and price. 29 games.

Both are transcriptions of the same ESPN odds resource. Neither is an official
NFL figure - the league publishes no betting lines (see F-01 / F-18 / F-36).

Why this tool exists
--------------------
Two stores of the same numbers are a drift risk: if one is edited or re-fetched
alone, the site starts publishing two different prices for the same game. This
tool re-derives the overlap from the CSVs and fails the build if the two
captures disagree.

It also measures, and publishes, the one genuine semantic difference between
them: **the word "close" means different things in the two stores.**

  * In the archive store, `close` is the last line the book was showing when
    the capture was taken. It is populated for every game, played or not.
  * In the integrity store, `current` holds that same quantity, and `close` is
    reserved for the closing line of a game that has actually been played, so
    it is empty for every game still to come.

That difference is a naming collision, not a data disagreement, and it is
recorded as flag F-38.

Run: python3 tools/reconcile_prices.py
Exit code 0 = the two captures agree on every comparable number.
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RESEARCH = os.path.join(ROOT, "research", "data")
OUT = os.path.join(RESEARCH, "price_capture_reconciliation.csv")
SUMMARY = os.path.join(DATA, "output", "price_reconciliation.json")

TOL = 1e-9

PROBLEMS = []


def num(x):
    if x is None:
        return None
    x = str(x).strip()
    if x == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def load_integrity():
    """One row per game: the integrity capture."""
    path = os.path.join(RESEARCH, "price_snapshots_2026.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_archive():
    """(event, market, side) -> row: the price archive."""
    path = os.path.join(DATA, "market-prices-2026.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {(r["event_id"], r["market"], r["side"]): r for r in rows}, rows


def compare(label, a, b, rows_out):
    """Compare two numbers, appending the outcome to the reconciliation rows."""
    av, bv = num(a), num(b)
    if av is None and bv is None:
        status = "both empty"
        ok = True
    elif av is None or bv is None:
        status = "one side empty"
        ok = False
    else:
        ok = abs(av - bv) <= TOL
        status = "match" if ok else "MISMATCH"
    if not ok:
        PROBLEMS.append("%s: %s is %r in one capture and %r in the other" % (label, label.split(":")[0], av, bv))
    rows_out.append(dict(comparison=label, capture_a=("" if av is None else av),
                         capture_b=("" if bv is None else bv), status=status))
    return ok


def main():
    integ = load_integrity()
    arch, arch_rows = load_archive()
    rows_out = []
    checked = 0
    games = 0

    for g in integ:
        key = (g["away"], g["home"])
        games += 1
        # the archive is keyed by event id; the integrity store carries the id
        ev = g.get("game_id") or ""
        pre = "%s @ %s" % key
        # The integrity store records the spread from the away side only, so
        # that is the only spread comparison the two stores can support.
        r = arch.get((ev, "spread", "away"))
        if r is None:
            PROBLEMS.append("%s: the archive has no spread row for the away side" % pre)
        else:
            for phase, afield in (("open", "spread_away_open"), ("close", "spread_away_current")):
                checked += 1
                compare("%s | spread | away | %s" % (pre, phase),
                        g.get(afield),
                        r.get("open_line") if phase == "open" else r.get("close_line"),
                        rows_out)

        # the total is a single number: both stores hold it once per game
        rt = arch.get((ev, "total", "over"))
        if rt is None:
            PROBLEMS.append("%s: the archive has no total row" % pre)
        else:
            for phase, afield in (("open", "total_open"), ("close", "total_current")):
                checked += 1
                compare("%s | total | %s" % (pre, phase),
                        g.get(afield),
                        rt.get("open_line") if phase == "open" else rt.get("close_line"),
                        rows_out)

        # the moneyline is a price, and both stores hold both sides
        for side, afields in (("away", ("ml_away_open", "ml_away_current")),
                              ("home", ("ml_home_open", "ml_home_current"))):
            rm = arch.get((ev, "moneyline", side))
            if rm is None:
                PROBLEMS.append("%s: the archive has no moneyline row for the %s side" % (pre, side))
                continue
            for phase, afield in (("open", afields[0]), ("close", afields[1])):
                checked += 1
                compare("%s | moneyline | %s | %s" % (pre, side, phase),
                        g.get(afield),
                        rm.get("open_price") if phase == "open" else rm.get("close_price"),
                        rows_out)

    # the closing phase of the integrity store is reserved for played games
    played = 0
    unplayed_with_close = 0
    for g in integ:
        if g.get("state") == "final":
            played += 1
        elif g.get("spread_away_close"):
            unplayed_with_close += 1
    if unplayed_with_close:
        PROBLEMS.append("%d games that have not been played carry a closing line in the integrity store"
                         % unplayed_with_close)

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["comparison", "capture_a", "capture_b", "status"])
        w.writeheader()
        w.writerows(rows_out)

    summary = dict(
        integrity_games=games,
        archive_games=len(set((r["away"], r["home"]) for r in arch_rows)),
        archive_rows=len(arch_rows),
        comparisons=checked,
        matches=sum(1 for r in rows_out if r["status"] == "match"),
        mismatches=sum(1 for r in rows_out if r["status"] == "MISMATCH"),
        both_empty=sum(1 for r in rows_out if r["status"] == "both empty"),
        one_empty=sum(1 for r in rows_out if r["status"] == "one side empty"),
        games_played_in_integrity_store=played,
        note=("The integrity store calls the last posted line 'current' and reserves 'close' "
              "for a played game; the archive store calls that same number 'close'. Flag F-38."),
    )
    with open(SUMMARY, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("integrity store: %d games   archive store: %d games (%d rows)"
          % (games, summary["archive_games"], summary["archive_rows"]))
    print("comparisons: %d   match: %d   mismatch: %d   both empty: %d   one empty: %d"
          % (checked, summary["matches"], summary["mismatches"],
             summary["both_empty"], summary["one_empty"]))
    print("wrote %s and %s" % (os.path.relpath(OUT, ROOT), os.path.relpath(SUMMARY, ROOT)))
    if PROBLEMS:
        print("PROBLEMS (%d):" % len(PROBLEMS))
        for p in PROBLEMS[:20]:
            print("  - %s" % p)
        return 1
    print("RESULT: PASS - the two captures agree on every comparable number")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
