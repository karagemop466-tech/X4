#!/usr/bin/env python3
"""Corpus statistics on the COMPLETE official 2026 game log, with a declared split.

Why this tool exists
---------------------
The published correlation table used to be read from
``research/computed_stats.json``, a snapshot generated on 2026-11-14 from
``research/data/games_weeks6-9_2026.csv`` - 57 games, weeks 6 to 9 - and that
snapshot was never regenerated.  The repository now holds the full verified
corpus in ``data/games-2026.csv``: 150 games, weeks 1 to 10, one official
nfl.com game URL per row, reproducing every official NFL.com standings total
exactly (tools/verify.py).  A statistic published next to a corpus that has
moved is a statistic with no window, and F-62 / F-63 are exactly that defect.

What this tool publishes
------------------------
Every descriptive statistic the site prints about the game log, recomputed from
the full corpus and reported **per window**, with the sample size on every
value:

    train       weeks 3-7    the window the walk-forward model is fitted on
    validation  week 8       one week, used to check, never to choose
    final       weeks 9-10   the most recent completed weeks
    full        weeks 1-10   the whole verified corpus
    frozen      weeks 6-9    the window the Week 11 pre-registration froze

The split is a **reporting** split for descriptive statistics.  It is NOT a
pristine holdout for the published strategies: weeks 9 and 10 are already part
of the 118-game evaluation the leaderboard reports, so they cannot be
re-labelled as untouched.  The next genuinely untouched window is Week 11
onward, which is registered forward in research/preregistration/wk11-forward-v1.md.
That limitation is stated on the page, not hidden.

Integrity checks (each one fails loudly, exit code 1)
-----------------------------------------------------
  1. every game row carries an https://www.nfl.com/games/... URL
  2. the standings derived from the corpus equal the official NFL.com
     standings for all 32 clubs (W, L, T, PF, PA)
  3. total points scored equals total points allowed; wins equal losses
  4. the neutral-site set equals the official International Games list
  5. no duplicated fixture; no score is negative

Usage
-----
    python3 tools/corpus_stats.py           # write data/output/corpus_stats.json
    python3 tools/corpus_stats.py --check   # re-derive and compare (publication gate)
"""
import csv
import json
import math
import os
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "output")
TARGET = os.path.join(OUT, "corpus_stats.json")

STANDINGS_FILE = "standings-wk10-2026.csv"
GAMES_FILE = "games-2026.csv"
INTERNATIONAL_FILE = "international-2026.csv"

OFFICIAL_STANDINGS = "https://www.nfl.com/standings/"
OFFICIAL_SCHEDULE = "https://www.nfl.com/schedules/2026/"

# The declared split. Weeks 1-2 are the walk-forward burn-in: the model never
# evaluates them (tools/build.py PARAMS["eval_first_week"] = 3), so they are
# reported as part of the corpus but are not a fitting window.
WINDOWS = [
    ("train", "Weeks 3-7 (fitting window)",
     "The window the walk-forward model is fitted on. Descriptive statistics "
     "here are what the model could legitimately have known."),
    ("validation", "Week 8 (check window)",
     "One week. Checked, never chosen on."),
    ("final", "Weeks 9-10 (most recent completed weeks)",
     "Already inside the 118-game published evaluation, so it is a reporting "
     "window and NOT an untouched holdout. The next untouched window is "
     "Week 11 onward (research/preregistration/wk11-forward-v1.md)."),
    ("full", "Weeks 1-10 (whole verified corpus)",
     "All 150 official games. This is the number to quote for 'this season so far'."),
    ("frozen", "Weeks 6-9 (frozen by the Week 11 pre-registration)",
     "The window the Week 11 forward pre-registration fixed before kickoff. "
     "Published unchanged so the registered model can be reproduced."),
]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pearson(xs, ys):
    """Pearson r with a Fisher-z 95% interval. n is the observation count."""
    n = len(xs)
    if n < 4:
        return {"n": n, "r": None, "ci95": [None, None], "note": "n < 4: not defined"}
    mx, my = st.mean(xs), st.mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return {"n": n, "r": None, "ci95": [None, None], "note": "zero variance"}
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    r = max(-0.999999, min(0.999999, r))
    z = math.atanh(r)
    se = 1 / math.sqrt(n - 3)
    return {"n": n, "r": r, "ci95": [math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)]}


def window_games(games, weeks):
    return [g for g in games if g["week"] in weeks]


def stats_for(games, neutral_pairs):
    """Every published descriptive statistic for one window."""
    non_neutral = [g for g in games
                   if (g["away"], g["home"]) not in neutral_pairs]
    margins = [g["home_pts"] - g["away_pts"] for g in non_neutral]
    totals = [g["home_pts"] + g["away_pts"] for g in games]
    away = [g["away_pts"] for g in games]
    home = [g["home_pts"] for g in games]
    all_margins = [g["home_pts"] - g["away_pts"] for g in non_neutral]
    all_totals = [g["home_pts"] + g["away_pts"] for g in non_neutral]

    out = {
        "games_n": len(games),
        "games_n_non_neutral": len(non_neutral),
        "neutral_games": len(games) - len(non_neutral),
        "home_margin": {"n": len(margins), "mean": None, "sd": None, "se": None,
                        "ci95": [None, None], "home_win_pct": None},
        "margin_vs_total": pearson(all_margins, all_totals),
        "away_vs_home_scores": pearson(away, home),
        "scoring": {"n": len(totals), "mean_total": None, "sd_total": None},
    }
    if len(margins) >= 2:
        mean = st.mean(margins)
        sd = st.stdev(margins)
        se = sd / math.sqrt(len(margins))
        out["home_margin"] = {
            "n": len(margins), "mean": mean, "sd": sd, "se": se,
            "ci95": [mean - 1.96 * se, mean + 1.96 * se],
            "home_win_pct": sum(1 for m in margins if m > 0) / len(margins),
        }
    if len(totals) >= 2:
        out["scoring"] = {"n": len(totals), "mean_total": st.mean(totals),
                          "sd_total": st.stdev(totals)}
    return out


def published_rows(cs):
    """The rows the site publishes, in order, as (window, statistic, value, ci, n).

    Kept in step with tools/pages.py::corpus_window_table.  The publication gate
    compares the rendered page against this list, so a page that prints a number
    the artifact does not contain fails the build instead of being published.
    """
    windows = cs.get("windows", {})
    out = []
    for key in ["train", "validation", "final", "full", "frozen"]:
        w = windows.get(key)
        if not w:
            continue
        s = w["stats"]
        label = w["label"].split(" (")[0]
        hm = s["home_margin"]
        mv = s["margin_vs_total"]
        ah = s["away_vs_home_scores"]
        out.append((label, "Home margin (international games excluded)",
                    "%+.2f pts" % hm["mean"],
                    "[%+.2f, %+.2f]" % tuple(hm["ci95"]), hm["n"]))
        out.append((label, "Winning margin vs game total (parlay-relevant)",
                    "%+.4f" % mv["r"],
                    "[%+.4f, %+.4f]" % tuple(mv["ci95"]), mv["n"]))
        out.append((label, "Away score vs home score, same game",
                    "%+.4f" % ah["r"],
                    "[%+.4f, %+.4f]" % tuple(ah["ci95"]), ah["n"]))
    sc = windows.get("full", {}).get("stats", {}).get("scoring", {})
    if sc.get("mean_total") is not None:
        out.append(("Full corpus", "Mean combined score (all games)",
                    "%.2f pts" % sc["mean_total"], "sd %.2f" % sc["sd_total"], sc["n"]))
    labels = {
        "net_points_vs_win_pct": "Team net points vs winning percentage",
        "pts_per_game_vs_pts_allowed_per_game":
            "A club's scoring rate vs its own allowing rate",
    }
    for key, c in cs.get("standings_scope", {}).get("correlations", {}).items():
        out.append(("Standings", labels.get(key, key.replace("_", " ")),
                    "%+.4f" % c["r"], "[%+.4f, %+.4f]" % tuple(c["ci95"]), c["n"]))
    return out


def check_page(cs, page_path):
    """Every published statistic on the page must equal the computed artifact."""
    import html as _html
    import re as _re
    if not os.path.exists(page_path):
        print("FAIL: %s does not exist" % page_path)
        return 1
    with open(page_path, encoding="utf-8") as fh:
        doc = fh.read()
    start = doc.find("Corpus statistics")
    if start < 0:
        print("FAIL: the corpus-statistics section is not on %s" % page_path)
        return 1
    seg = doc[start:start + 40000]
    tables = _re.findall(r"<table.*?</table>", seg, _re.S)
    if not tables:
        print("FAIL: no corpus-statistics table found on %s" % page_path)
        return 1
    rows = _re.findall(r"<tr[^>]*>(.*?)</tr>", tables[0], _re.S)
    parsed = []
    for r in rows:
        cells = [_html.unescape(_re.sub(r"<[^>]+>", "", c)).strip()
                 for c in _re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, _re.S)]
        if len(cells) >= 5 and cells[0] != "Window":
            parsed.append(cells)
    expected = published_rows(cs)
    failures = []
    if len(parsed) != len(expected):
        failures.append("the page publishes %d corpus rows, the artifact holds %d"
                        % (len(parsed), len(expected)))
    for i, exp in enumerate(expected):
        if i >= len(parsed):
            break
        got = parsed[i]
        label, stat, value, ci, n = exp
        for field, want, have in (("statistic", stat, got[1]),
                                  ("value", value, got[2]),
                                  ("interval", ci, got[3]),
                                  ("n", str(n), got[4])):
            if want != have:
                failures.append("row %d (%s / %s): %s is %r, the artifact holds %r"
                                % (i + 1, label, stat, field, have, want))
    for f in failures:
        print("  - %s" % f)
    if failures:
        return 1
    print("corpus statistics on the page: %d rows match the artifact exactly" % len(parsed))
    return 0


def round_floats(obj, places=9):
    """Same normalisation as tools/build.py, so the output is byte-stable."""
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        r = round(obj, places)
        return 0.0 if r == 0 else r
    if isinstance(obj, dict):
        return dict((k, round_floats(v, places)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return [round_floats(v, places) for v in obj]
    return obj


def derive():
    games_raw = read_csv(os.path.join(DATA, GAMES_FILE))
    games = []
    for g in games_raw:
        games.append({
            "week": int(g["week"]), "away": g["away"], "home": g["home"],
            "away_pts": int(g["away_pts"]), "home_pts": int(g["home_pts"]),
            "ot": (g.get("ot") or "").strip(), "url": g["url"].strip(),
        })
    standings = {r["abbr"]: r for r in read_csv(os.path.join(DATA, STANDINGS_FILE))}
    intl = read_csv(os.path.join(DATA, INTERNATIONAL_FILE))

    failures = []
    checks = 0

    # 1. every row carries an official NFL.com game URL
    for g in games:
        checks += 1
        if not g["url"].startswith("https://www.nfl.com/games/"):
            failures.append("no official game URL: %s@%s wk%s"
                            % (g["away"], g["home"], g["week"]))
        if g["away_pts"] < 0 or g["home_pts"] < 0:
            failures.append("negative score: %s@%s wk%s"
                            % (g["away"], g["home"], g["week"]))
    seen = set()
    for g in games:
        key = (g["week"], g["away"], g["home"])
        checks += 1
        if key in seen:
            failures.append("duplicated fixture %s" % (key,))
        seen.add(key)

    # 2. derived standings == official NFL.com standings, club by club
    agg = {}
    for g in games:
        for me, them, mine, theirs in ((g["away"], g["home"], g["away_pts"], g["home_pts"]),
                                        (g["home"], g["away"], g["home_pts"], g["away_pts"])):
            a = agg.setdefault(me, {"pf": 0, "pa": 0, "w": 0, "l": 0, "t": 0})
            a["pf"] += mine
            a["pa"] += theirs
        if g["away_pts"] > g["home_pts"]:
            agg[g["away"]]["w"] += 1
            agg[g["home"]]["l"] += 1
        elif g["away_pts"] < g["home_pts"]:
            agg[g["home"]]["w"] += 1
            agg[g["away"]]["l"] += 1
        else:
            agg[g["away"]]["t"] += 1
            agg[g["home"]]["t"] += 1
    pf_total = sum(a["pf"] for a in agg.values())
    pa_total = sum(a["pa"] for a in agg.values())
    wins = sum(a["w"] for a in agg.values())
    losses = sum(a["l"] for a in agg.values())
    ties = sum(a["t"] for a in agg.values()) // 2
    checks += 1
    if pf_total != pa_total:
        failures.append("points scored %d != points allowed %d" % (pf_total, pa_total))
    checks += 1
    if wins != losses:
        failures.append("wins %d != losses %d" % (wins, losses))
    for abbr, row in sorted(standings.items()):
        a = agg.get(abbr)
        checks += 4
        if a is None:
            failures.append("club %s missing from the corpus" % abbr)
            continue
        for field in ("w", "l", "t"):
            if a[field] != int(row[field]):
                failures.append("%s %s: corpus=%d official=%s"
                                % (abbr, field, a[field], row[field]))
        if a["pf"] != int(row["pf"]) or a["pa"] != int(row["pa"]):
            failures.append("%s points: corpus=%d-%d official=%s-%s"
                            % (abbr, a["pf"], a["pa"], row["pf"], row["pa"]))

    # 4. the neutral-site set is exactly the official International Games.
    #    An International Game that has not been played yet (Week 11) is not in
    #    the corpus and must not be counted as a neutral game of a window.
    weeks = sorted(set(g["week"] for g in games))
    last_played_week = max(weeks)
    neutral_pairs = set()
    scheduled_intl = []
    for r in intl:
        w = int(r["week"])
        if w <= last_played_week:
            neutral_pairs.add((r["away"], r["home"]))
        else:
            scheduled_intl.append("%s W%d %s at %s (%s)"
                                  % (r["city"], w, r["away"], r["home"], r["country"]))
    corpus_pairs = set((g["away"], g["home"]) for g in games)
    missing = sorted(p for p in neutral_pairs if p not in corpus_pairs)
    checks += 1
    if missing:
        failures.append("international fixtures absent from the corpus: %s" % (missing,))

    # ---- the current official standings capture, for the two team-level
    #      correlations (n = 32 clubs) ---------------------------------------
    standings_current = read_csv(os.path.join(DATA, "standings-2026-11-18.csv"))
    wpct, net, pfpg, papg = [], [], [], []
    for r in standings_current:
        g = int(r["w"]) + int(r["l"]) + int(r["t"])
        wpct.append((int(r["w"]) + 0.5 * int(r["t"])) / g)
        net.append(int(r["net_pts"]))
        pfpg.append(int(r["pf"]) / g)
        papg.append(int(r["pa"]) / g)
    standings_scope = {
        "file": "data/standings-2026-11-18.csv",
        "clubs": len(standings_current),
        "retrieved": "2026-11-18",
        "official_url": OFFICIAL_STANDINGS,
        "correlations": {
            "net_points_vs_win_pct": pearson(net, wpct),
            "pts_per_game_vs_pts_allowed_per_game": pearson(pfpg, papg),
        },
    }

    window_defs = {
        "train": [w for w in weeks if 3 <= w <= 7],
        "validation": [8],
        "final": [9, 10],
        "full": weeks,
        "frozen": [6, 7, 8, 9],
    }
    windows = {}
    for key, label, note in WINDOWS:
        wks = window_defs[key]
        subset = window_games(games, wks)
        windows[key] = {
            "label": label,
            "note": note,
            "weeks": wks,
            "stats": stats_for(subset, neutral_pairs),
        }

    out = {
        "generated": "2026-11-19",
        "standings_scope": standings_scope,
        "corpus": {
            "file": "data/games-2026.csv",
            "games": len(games),
            "weeks": weeks,
            "source": "Official NFL.com game pages, one URL per row; the corpus "
                      "reproduces every official NFL.com standings total exactly "
                      "(tools/verify.py).",
            "standings_capture": "data/standings-wk10-2026.csv (nfl.com/standings)",
            "official_standings_url": OFFICIAL_STANDINGS,
            "official_schedule_url": OFFICIAL_SCHEDULE,
        },
        "split": {
            "declared": "2026-11-19 (this tool), before any Week 11 result existed",
            "train": "weeks 3-7",
            "validation": "week 8",
            "final_holdout": "weeks 9-10 (already inside the published 118-game "
                             "evaluation, therefore a reporting window and not an "
                             "untouched holdout; the next untouched window is "
                             "Week 11 onward)",
            "burn_in": "weeks 1-2 (the walk-forward never evaluates them)",
            "limitations": [
                "One season cannot give three seasons. The brief asks for train, "
                "validation and final holdout SEASONS; what is published here is "
                "the week-level analogue inside the single 2026 season.",
                "Weeks 9-10 have already been seen by the published strategies, so "
                "they are a reporting window, not a holdout.",
                "The pre-registered Week 11 window (research/preregistration/"
                "wk11-forward-v1.md) is the first untouched window.",
            ],
        },
        "integrity": {
            "checks": checks,
            "failures": failures,
            "status": "all checks passed" if not failures else "FAILED",
            "sum_points_for": pf_total,
            "sum_points_against": pa_total,
            "total_wins": wins,
            "total_losses": losses,
            "total_ties": ties,
            "neutral_games": sorted(list(neutral_pairs)),
            "international_games_scheduled_not_played": scheduled_intl,
            "games_with_official_url": sum(1 for g in games
                                           if g["url"].startswith("https://www.nfl.com/games/")),
        },
        "windows": windows,
    }
    return out


def main():
    out = round_floats(derive())
    if "--check-page" in sys.argv:
        return check_page(out, os.path.join(ROOT, "site", "gates.html"))
    if "--check" in sys.argv:
        if not os.path.exists(TARGET):
            print("FAIL: %s does not exist" % TARGET)
            return 1
        with open(TARGET, encoding="utf-8") as fh:
            committed = json.load(fh)
        if committed != out:
            print("FAIL: the committed corpus statistics differ from a fresh derivation")
            print("  committed keys: %s" % sorted(committed.keys()))
            for key in sorted(set(list(committed.get("windows", {}).keys())
                                   + list(out.get("windows", {}).keys()))):
                c = committed.get("windows", {}).get(key, {})
                n = out.get("windows", {}).get(key, {})
                if c != n:
                    print("  window %s differs" % key)
                    print("    committed: %s" % json.dumps(c.get("stats", {}), sort_keys=True))
                    print("    derived : %s" % json.dumps(n.get("stats", {}), sort_keys=True))
            return 1
        if out["integrity"]["status"] != "all checks passed":
            print("FAIL: integrity checks did not pass: %s"
                  % out["integrity"]["failures"])
            return 1
        print("corpus statistics: %d games, %d checks, all windows reproduce byte-for-byte"
              % (out["corpus"]["games"], out["integrity"]["checks"]))
        return 0

    if out["integrity"]["status"] != "all checks passed":
        print("INTEGRITY FAILURES:")
        for f in out["integrity"]["failures"]:
            print("  - %s" % f)
        return 1
    os.makedirs(OUT, exist_ok=True)
    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, sort_keys=True))
        fh.write("\n")
    print("wrote %s" % os.path.relpath(TARGET, ROOT))
    for key, _label, _note in WINDOWS:
        s = out["windows"][key]["stats"]
        hm = s["home_margin"]
        mv = s["margin_vs_total"]
        print("  %-11s games=%3d  home margin %+6.2f (n=%3d)   margin~total r=%+.4f (n=%3d)"
              % (key, s["games_n"], hm["mean"] or 0.0, hm["n"],
                 mv["r"] or 0.0, mv["n"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
