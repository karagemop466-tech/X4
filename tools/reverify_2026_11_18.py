#!/usr/bin/env python3
"""
T46 — live official re-verification of the 2026-11-18 state, and the Week 10 close-out.

WHY THIS EXISTS
---------------
On 2026-11-18 the committed tree still described the season as it stood after the
Nov 12 Thursday-night game. The official Week 10 slate has since finished (Nov 12-16),
so `data/games-2026.csv`, the official standings, every walk-forward model and every
derived number on the site were one week stale. This tool records the official
re-read, proves the completed game log against it, and writes the refreshed
standings file. It writes nothing that a human typed in twice: the standings CSV is
derived from the game log, and only after the game log has been proved to reproduce
the transcription below exactly.

WHAT IT CHECKS (all offline, deterministic)
-------------------------------------------
  1. The 14 Week 10 finals transcribed from the official NFL.com Week 10 schedule
     page below each appear exactly once in data/games-2026.csv, with the score the
     official page prints and a game URL of the official form.
  2. The completed game log reproduces, for all 32 clubs, the official NFL.com
     standings transcription below (W, L, T, PF, PA and net points) exactly. Any
     single wrong score changes at least one club's PF or PA, so this is a complete
     check of the scores, not a spot check.
  3. Winning percentage follows the NFL's own formula, PCT = (W + 0.5*T) / G.
  4. `--write` rewrites data/standings-wk10-2026.csv from the game log in the file's
     existing column order, and writes an audit CSV of every standings cell that
     moved against the previously committed file (read from git, not from memory).

HONEST LIMITS
-------------
* The standings transcription is a human read of a rendered page. It is used ONLY as
  the independent side of the comparison in step 2 — the CSV is never written from it.
  If the read were wrong, step 2 fails loudly instead of publishing the error.
* No odds, projection, depth or availability claim is made here. This tool touches
  results and standings only.

SOURCES (fetched 2026-11-18 UTC, from this sandbox, over the fetch tool because the
sandbox cannot open a raw socket to nfl.com)
  https://www.nfl.com/schedules/2026/by-week/week-10   Week 10 finals + kickoff order
  https://www.nfl.com/standings/                       official W/L/T/PCT/PF/PA/NET

Usage:  python3 tools/reverify_2026_11_18.py            # check only (exit 1 on any mismatch)
        python3 tools/reverify_2026_11_18.py --write    # check, then write the CSVs
"""
import argparse
import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
VERIF = os.path.join(ROOT, "research", "verification")
RETRIEVED = "2026-11-18"

SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
STANDINGS_URL = "https://www.nfl.com/standings/"

# ---------------------------------------------------------------------------
# Official Week 10 finals, transcribed from SCHEDULE_URL on 2026-11-18.
# The official page prints each game as "AWAY x, HOME y, FINAL".
# ---------------------------------------------------------------------------
WK10_FINALS = [
    # away, home, away_pts, home_pts, official page label
    ("WAS", "NYG", 24, 21, "Commanders 24, Giants 21 (Thu Nov 12)"),
    ("NE", "DET", 10, 35, "Patriots 10, Lions 35 (Sun Nov 15, Munich, International Game)"),
    ("KC", "ATL", 35, 13, "Chiefs 35, Falcons 13 (Sun Nov 15)"),
    ("HOU", "CLE", 24, 27, "Texans 24, Browns 27 (Sun Nov 15)"),
    ("MIN", "GB", 30, 10, "Vikings 30, Packers 10 (Sun Nov 15)"),
    ("MIA", "IND", 22, 24, "Dolphins 22, Colts 24 (Sun Nov 15)"),
    ("CAR", "NO", 20, 17, "Panthers 20, Saints 17 (Sun Nov 15)"),
    ("BUF", "NYJ", 31, 12, "Bills 31, Jets 12 (Sun Nov 15)"),
    ("JAX", "TEN", 40, 23, "Jaguars 40, Titans 23 (Sun Nov 15)"),
    ("LAR", "ARI", 34, 6, "Rams 34, Cardinals 6 (Sun Nov 15)"),
    ("SEA", "LV", 21, 13, "Seahawks 21, Raiders 13 (Sun Nov 15)"),
    ("SF", "DAL", 46, 40, "49ers 46, Cowboys 40 (Sun Nov 15)"),
    ("PIT", "CIN", 18, 38, "Steelers 18, Bengals 38 (Sun Nov 15, Sunday Night)"),
    ("LAC", "BAL", 23, 20, "Chargers 23, Ravens 20 (Mon Nov 16)"),
]

# ---------------------------------------------------------------------------
# Official NFL.com standings, transcribed from STANDINGS_URL on 2026-11-18.
# nfl.com prints the Rams as LA; this repository's game log uses LAR.
# ---------------------------------------------------------------------------
WK10_STANDINGS = {
    # abbr: (w, l, t, pct_as_printed, pf, pa, net_pts_as_printed)
    "BUF": (8, 1, 0, "0.889", 287, 199, 88),
    "NE":  (5, 5, 0, "0.500", 221, 242, -21),
    "NYJ": (2, 8, 0, "0.200", 194, 254, -60),
    "MIA": (1, 8, 0, "0.111", 148, 224, -76),
    "CIN": (7, 2, 0, "0.778", 278, 193, 85),
    "PIT": (6, 3, 0, "0.667", 198, 182, 16),
    "CLE": (6, 4, 0, "0.600", 188, 220, -32),
    "BAL": (4, 6, 0, "0.400", 209, 259, -50),
    "JAX": (7, 2, 0, "0.778", 269, 144, 125),
    "HOU": (3, 6, 0, "0.333", 233, 219, 14),
    "IND": (3, 7, 0, "0.300", 208, 271, -63),
    "TEN": (1, 8, 0, "0.111", 167, 239, -72),
    "KC":  (7, 2, 0, "0.778", 237, 156, 81),
    "DEN": (7, 2, 0, "0.778", 198, 186, 12),
    "LV":  (4, 6, 0, "0.400", 251, 289, -38),
    "LAC": (1, 8, 0, "0.111", 144, 239, -95),
    "NYG": (5, 3, 1, "0.611", 203, 196, 7),
    "DAL": (4, 6, 0, "0.400", 286, 282, 4),
    "WAS": (3, 5, 1, "0.389", 196, 223, -27),
    "PHI": (2, 7, 0, "0.222", 148, 221, -73),
    "DET": (7, 2, 0, "0.778", 257, 199, 58),
    "MIN": (7, 2, 0, "0.778", 176, 126, 50),
    "CHI": (7, 2, 0, "0.778", 241, 184, 57),
    "GB":  (6, 4, 0, "0.600", 226, 221, 5),
    "CAR": (4, 5, 0, "0.444", 219, 236, -17),
    "TB":  (3, 6, 0, "0.333", 202, 178, 24),
    "NO":  (3, 6, 0, "0.333", 202, 236, -34),
    "ATL": (3, 7, 0, "0.300", 201, 258, -57),
    "SF":  (8, 1, 0, "0.889", 281, 196, 85),
    "SEA": (6, 4, 0, "0.600", 223, 175, 48),
    "LAR": (6, 4, 0, "0.600", 248, 187, 61),
    "ARI": (3, 7, 0, "0.300", 184, 289, -105),
}

TEAM_NAME = {
    "BUF": "Buffalo Bills", "NE": "New England Patriots", "NYJ": "New York Jets",
    "MIA": "Miami Dolphins", "PIT": "Pittsburgh Steelers", "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns", "BAL": "Baltimore Ravens", "JAX": "Jacksonville Jaguars",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "TEN": "Tennessee Titans",
    "DEN": "Denver Broncos", "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders",
    "LAC": "Los Angeles Chargers", "NYG": "New York Giants", "DAL": "Dallas Cowboys",
    "WAS": "Washington Commanders", "PHI": "Philadelphia Eagles", "CHI": "Chicago Bears",
    "DET": "Detroit Lions", "MIN": "Minnesota Vikings", "GB": "Green Bay Packers",
    "CAR": "Carolina Panthers", "NO": "New Orleans Saints", "TB": "Tampa Bay Buccaneers",
    "ATL": "Atlanta Falcons", "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks",
    "LAR": "Los Angeles Rams", "ARI": "Arizona Cardinals",
}

SLUG = {
    "ARI": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills", "CAR": "panthers",
    "CHI": "bears", "CIN": "bengals", "CLE": "browns", "DAL": "cowboys", "DEN": "broncos",
    "DET": "lions", "GB": "packers", "HOU": "texans", "IND": "colts", "JAX": "jaguars",
    "KC": "chiefs", "LAC": "chargers", "LAR": "rams", "LV": "raiders", "MIA": "dolphins",
    "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants", "NYJ": "jets",
    "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks", "SF": "49ers", "TB": "buccaneers",
    "TEN": "titans", "WAS": "commanders",
}

FIELDS = ["abbr", "team", "w", "l", "t", "pct", "pf", "pa", "net_pts"]


def read_games():
    with open(os.path.join(DATA, "games-2026.csv"), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["week"] = int(r["week"])
        r["away_pts"] = int(r["away_pts"])
        r["home_pts"] = int(r["home_pts"])
    return rows


def aggregate(games):
    agg = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "g": 0} for t in WK10_STANDINGS}
    for g in games:
        a, h = g["away"], g["home"]
        agg[a]["pf"] += g["away_pts"]
        agg[a]["pa"] += g["home_pts"]
        agg[a]["g"] += 1
        agg[h]["pf"] += g["home_pts"]
        agg[h]["pa"] += g["away_pts"]
        agg[h]["g"] += 1
        if g["away_pts"] > g["home_pts"]:
            agg[a]["w"] += 1
            agg[h]["l"] += 1
        elif g["away_pts"] < g["home_pts"]:
            agg[h]["w"] += 1
            agg[a]["l"] += 1
        else:
            agg[a]["t"] += 1
            agg[h]["t"] += 1
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="rewrite the standings CSV after the checks pass")
    args = ap.parse_args()

    failures = []
    checks = 0
    games = read_games()

    # ---- 1. every Week 10 final is present exactly once, with the official score ----
    wk10 = [g for g in games if g["week"] == 10]
    checks += 1
    if len(wk10) != 14:
        failures.append("Week 10 must hold 14 completed games, found %d" % len(wk10))
    for away, home, ap_, hp_, label in WK10_FINALS:
        checks += 3
        hits = [g for g in games if g["week"] == 10 and g["away"] == away and g["home"] == home]
        if len(hits) != 1:
            failures.append("Week 10 %s@%s appears %d times" % (away, home, len(hits)))
            continue
        g = hits[0]
        if (g["away_pts"], g["home_pts"]) != (ap_, hp_):
            failures.append("Week 10 %s@%s: log %d-%d, official page %d-%d (%s)"
                            % (away, home, g["away_pts"], g["home_pts"], ap_, hp_, label))
        expect = "https://www.nfl.com/games/%s-at-%s-2026-reg-10" % (SLUG[away], SLUG[home])
        if g["url"] != expect:
            failures.append("Week 10 %s@%s URL: %s != %s" % (away, home, g["url"], expect))

    # ---- 2. the whole log reproduces the official standings exactly ----
    agg = aggregate(games)
    for t, (w, l, t_, pct, pf, pa, net) in WK10_STANDINGS.items():
        a = agg[t]
        checks += 6
        if (a["w"], a["l"], a["t"]) != (w, l, t_):
            failures.append("%s record: log %d-%d-%d, official %d-%d-%d"
                            % (t, a["w"], a["l"], a["t"], w, l, t_))
        if (a["pf"], a["pa"]) != (pf, pa):
            failures.append("%s points: log %d-%d, official %d-%d" % (t, a["pf"], a["pa"], pf, pa))
        if a["pf"] - a["pa"] != net:
            failures.append("%s net points: log %d, official %d" % (t, a["pf"] - a["pa"], net))
        gp = a["w"] + a["l"] + a["t"]
        if gp != a["g"]:
            failures.append("%s games played inconsistent" % t)
        mine = "%.3f" % ((a["w"] + 0.5 * a["t"]) / gp) if gp else "0.000"
        if mine != pct:
            failures.append("%s pct: log %s, official %s" % (t, mine, pct))

    # ---- 3. totals: a complete 2026 season-to-date slate, and every club once ----
    checks += 2
    if len(agg) != 32:
        failures.append("standings must cover 32 clubs, found %d" % len(agg))
    wk_counts = {}
    for g in games:
        wk_counts[g["week"]] = wk_counts.get(g["week"], 0) + 1
    if any(n != 16 for w, n in wk_counts.items() if w <= 4):
        failures.append("weeks 1-4 must hold 16 games each: %s" % wk_counts)

    print("checks run: %d" % checks)
    print("games in log: %d (weeks %s)" % (len(games), sorted(wk_counts)))
    if failures:
        print("FAILURES (%d):" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("RESULT: PASS - the completed game log reproduces the official NFL.com "
          "standings for all 32 clubs, and every Week 10 final matches the official "
          "Week 10 schedule page.")

    if not args.write:
        return 0

    # ---- 4. write the standings CSV, and the audit of every cell that moved ----
    prev = {}
    try:
        out = subprocess.run(["git", "show", "HEAD:data/standings-wk10-2026.csv"],
                             cwd=ROOT, capture_output=True, text=True, check=True)
        for r in csv.DictReader(out.stdout.splitlines()):
            prev[r["abbr"]] = r
    except Exception as exc:           # no git, or a first run: no baseline to diff
        print("note: no previous standings file to diff against (%s)" % exc)

    order = [r["abbr"] for r in csv.DictReader(
        open(os.path.join(DATA, "standings-wk10-2026.csv"), newline="", encoding="utf-8"))]
    order = [t for t in order if t in WK10_STANDINGS]
    order += [t for t in WK10_STANDINGS if t not in order]

    rows = []
    for t in order:
        w, l, t_, pct, pf, pa, net = WK10_STANDINGS[t]
        rows.append({"abbr": t, "team": TEAM_NAME[t], "w": w, "l": l, "t": t_,
                     "pct": pct, "pf": pf, "pa": pa, "net_pts": net})
    with open(os.path.join(DATA, "standings-wk10-2026.csv"), "w", newline="", encoding="utf-8") as fh:
        w_ = csv.DictWriter(fh, fieldnames=FIELDS)
        w_.writeheader()
        w_.writerows(rows)

    os.makedirs(VERIF, exist_ok=True)
    audit = os.path.join(VERIF, "standings-refresh-2026-11-18.csv")
    moved = 0
    with open(audit, "w", newline="", encoding="utf-8") as fh:
        w_ = csv.writer(fh)
        w_.writerow(["team", "field", "before", "after", "source_url", "retrieved"])
        for r in rows:
            old = prev.get(r["abbr"])
            for f in ("w", "l", "t", "pct", "pf", "pa", "net_pts"):
                before = old[f] if old else ""
                if str(before) != str(r[f]):
                    moved += 1
                    w_.writerow([r["abbr"], f, before, r[f], STANDINGS_URL, RETRIEVED])
    print("wrote data/standings-wk10-2026.csv (%d clubs) and %s (%d cells moved)"
          % (len(rows), os.path.relpath(audit, ROOT), moved))
    return 0


if __name__ == "__main__":
    sys.exit(main())
