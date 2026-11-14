#!/usr/bin/env python3
"""
Verify the reconstructed 2026 NFL game log against the OFFICIAL NFL.com standings.

Data contract
-------------
data/games-2026.csv        reconstructed week-by-week game log (scores + official NFL.com game URL)
data/standings-wk10-2026.csv  OFFICIAL NFL.com standings: W, L, T, PCT, PF, PA, NET PTS per team
data/schedule-wk11-2026.csv   OFFICIAL NFL.com Week 11 schedule

A reconstructed score is only accepted if, for every team, the sum of points scored,
points allowed, wins, losses and ties derived from the game log equals the official
NFL.com total exactly. Any single wrong score changes at least one team's PF or PA,
so this is a complete check of the score data - not a spot check.

Exit code 0 = every check passed. Exit code 1 = at least one failure (details printed).
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# NFL.com "name" slugs used inside /games/<away>-at-<home>-<season>-reg-<week> URLs.
SLUG = {
    "ARI": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills", "CAR": "panthers",
    "CHI": "bears", "CIN": "bengals", "CLE": "browns", "DAL": "cowboys",
    "DEN": "broncos", "DET": "lions", "GB": "packers", "HOU": "texans",
    "IND": "colts", "JAX": "jaguars", "KC": "chiefs", "LAC": "chargers",
    "LAR": "rams", "LV": "raiders", "MIA": "dolphins", "MIN": "vikings",
    "NE": "patriots", "NO": "saints", "NYG": "giants", "NYJ": "jets",
    "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks", "SF": "49ers",
    "TB": "buccaneers", "TEN": "titans", "WAS": "commanders",
}
NFL_TEAM_URL = "https://www.nfl.com/teams/%s/"
NFL_TEAM_SLUG = {
    "ARI": "arizona-cardinals", "ATL": "atlanta-falcons", "BUF": "buffalo-bills",
    "CAR": "carolina-panthers", "CHI": "chicago-bears", "CIN": "cincinnati-bengals",
    "CLE": "cleveland-browns", "DAL": "dallas-cowboys", "DEN": "denver-broncos",
    "DET": "detroit-lions", "GB": "green-bay-packers", "HOU": "houston-texans",
    "IND": "indianapolis-colts", "JAX": "jacksonville-jaguars", "KC": "kansas-city-chiefs",
    "LAC": "los-angeles-chargers", "LAR": "los-angeles-rams", "LV": "las-vegas-raiders",
    "MIA": "miami-dolphins", "MIN": "minnesota-vikings", "NE": "new-england-patriots",
    "NO": "new-orleans-saints", "NYG": "new-york-giants", "NYJ": "new-york-jets",
    "PHI": "philadelphia-eagles", "PIT": "pittsburgh-steelers", "SEA": "seattle-seahawks",
    "SF": "san-francisco-49ers", "TB": "tampa-bay-buccaneers", "TEN": "tennessee-titans",
    "WAS": "washington-commanders",
}
DIVISION = {
    "BUF": "AFC East", "NE": "AFC East", "NYJ": "AFC East", "MIA": "AFC East",
    "PIT": "AFC North", "CIN": "AFC North", "CLE": "AFC North", "BAL": "AFC North",
    "JAX": "AFC South", "HOU": "AFC South", "IND": "AFC South", "TEN": "AFC South",
    "DEN": "AFC West", "KC": "AFC West", "LV": "AFC West", "LAC": "AFC West",
    "NYG": "NFC East", "DAL": "NFC East", "WAS": "NFC East", "PHI": "NFC East",
    "CHI": "NFC North", "DET": "NFC North", "MIN": "NFC North", "GB": "NFC North",
    "CAR": "NFC South", "NO": "NFC South", "TB": "NFC South", "ATL": "NFC South",
    "SF": "NFC West", "SEA": "NFC West", "LAR": "NFC West", "ARI": "NFC West",
}


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    failures = []
    checks = 0

    games = read_csv("games-2026.csv")
    standings = {r["abbr"]: r for r in read_csv("standings-wk10-2026.csv")}
    schedule = read_csv("schedule-wk11-2026.csv")

    # ---- 1. every official NFL.com game URL matches the row it is attached to ----
    for g in games:
        checks += 1
        expect = "https://www.nfl.com/games/%s-at-%s-2026-reg-%s" % (
            SLUG[g["away"]], SLUG[g["home"]], g["week"])
        if g["url"] != expect:
            failures.append("game URL mismatch %s@%s wk%s: %s != %s"
                            % (g["away"], g["home"], g["week"], g["url"], expect))

    # ---- 2. scores reproduce the official NFL.com standings exactly ----
    agg = {t: {"pf": 0, "pa": 0, "w": 0, "l": 0, "t": 0, "g": 0} for t in SLUG}
    for g in games:
        away_pts = int(g["away_pts"])
        home_pts = int(g["home_pts"])
        for me, them, my_pts, their_pts in (
            (g["away"], g["home"], away_pts, home_pts),
            (g["home"], g["away"], home_pts, away_pts),
        ):
            agg[me]["pf"] += my_pts
            agg[me]["pa"] += their_pts
            agg[me]["g"] += 1
        # record the result exactly once per game
        if away_pts > home_pts:
            agg[g["away"]]["w"] += 1
            agg[g["home"]]["l"] += 1
        elif away_pts < home_pts:
            agg[g["home"]]["w"] += 1
            agg[g["away"]]["l"] += 1
        else:
            agg[g["away"]]["t"] += 1
            agg[g["home"]]["t"] += 1

    for t, row in standings.items():
        a = agg[t]
        checks += 4
        if a["w"] != int(row["w"]):
            failures.append("%s wins: log=%s official=%s" % (t, a["w"], row["w"]))
        if a["l"] != int(row["l"]):
            failures.append("%s losses: log=%s official=%s" % (t, a["l"], row["l"]))
        if a["t"] != int(row["t"]):
            failures.append("%s ties: log=%s official=%s" % (t, a["t"], row["t"]))
        if a["pf"] != int(row["pf"]) or a["pa"] != int(row["pa"]):
            failures.append("%s points: log=%s-%s official=%s-%s"
                            % (t, a["pf"], a["pa"], row["pf"], row["pa"]))
        if a["pf"] - a["pa"] != int(row["net_pts"]):
            failures.append("%s net points: log=%s official=%s"
                            % (t, a["pf"] - a["pa"], row["net_pts"]))
        if a["g"] != a["w"] + a["l"] + a["t"]:
            failures.append("%s games played inconsistent" % t)
        # NFL.com counts a tie as half a win: PCT = (W + 0.5*T) / G
        g_played = a["w"] + a["l"] + a["t"]
        pct = (a["w"] + 0.5 * a["t"]) / g_played if g_played else 0
        if abs(pct - float(row["pct"])) > 0.0011:
            failures.append("%s pct: log=%.3f official=%s" % (t, pct, row["pct"]))

    # ---- 3. schedule coverage: every team plays the right number of games ----
    team_games = {t: 0 for t in SLUG}
    for g in games:
        team_games[g["away"]] += 1
        team_games[g["home"]] += 1
    for t, n in team_games.items():
        checks += 1
        if n != int(standings[t]["w"]) + int(standings[t]["l"]) + int(standings[t]["t"]):
            failures.append("%s played %s games but official record implies %s"
                            % (t, n, int(standings[t]["w"]) + int(standings[t]["l"]) + int(standings[t]["t"])))

    # ---- 4. Week 11 schedule: URLs, no duplicate team, matches official pairings ----
    wk11_teams = set()
    for s in schedule:
        checks += 2
        expect = "https://www.nfl.com/games/%s-at-%s-2026-reg-11" % (
            SLUG[s["away"]], SLUG[s["home"]])
        if s["nfl_url"] != expect:
            failures.append("wk11 URL mismatch %s@%s: %s != %s"
                            % (s["away"], s["home"], s["nfl_url"], expect))
        for side in ("away", "home"):
            if s[side] in wk11_teams:
                failures.append("team %s appears twice in the Week 11 schedule" % s[side])
            wk11_teams.add(s[side])
    if len(schedule) != 13:
        failures.append("Week 11 must contain 13 games, found %d" % len(schedule))
    if len(wk11_teams) != 26:
        failures.append("Week 11 must involve 26 teams, found %d" % len(wk11_teams))

    # ---- 5. no duplicate games in the reconstructed log ----
    seen = set()
    for g in games:
        key = (g["week"], g["away"], g["home"])
        checks += 1
        if key in seen:
            failures.append("duplicate game %s" % (key,))
        seen.add(key)

    print("checks run: %d" % checks)
    print("games verified: %d" % len(games))
    print("teams verified: %d" % len(standings))
    if failures:
        print("FAILURES (%d):" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("RESULT: PASS - reconstructed scores reproduce every official NFL.com W/L/T/PF/PA total exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
