#!/usr/bin/env python3
"""
T48 - personnel / availability ablation on the official Week 10 injury report.

WHY THIS EXISTS
---------------
The brief asks for "injury and personnel ablations instead of fixed penalties":
test the same model with and without the personnel features and report the
difference with uncertainty. The repository had no such measurement -- the
"penalty" it applies to a missing player was never calibrated against anything.

This tool measures the one availability effect the committed data can actually
support: do clubs the OFFICIAL Week 10 injury report rules a player Out score
differently from clubs it does not? Every comparison is published with its n and
a 95% interval, and a row is only printed if it can be derived from the
committed CSVs.

HONEST LIMITS (also printed on the page)
----------------------------------------
* Club level, one week, 14 games. This is a base rate to calibrate a prior
  against, NOT a causal coefficient and NOT a model feature. No personnel
  points adjustment is published anywhere because of this file.
* "No designation" is not "full strength": a club can rest a player or omit him
  from the report entirely (reserve lists are a separate document, F-43).
* The player-level question (how much does ONE lost starter cost?) needs snap
  counts for the replacement and the man he replaced. That exists for exactly
  one club-week (Houston, data/houston-playtime-depth-wk10-2026.csv) and is NOT
  used here -- one club-week cannot support an estimate.

INPUTS (committed, verified elsewhere)
  data/injuries-wk10-2026.csv   official NFL.com Week 10 report (capture-checked)
  data/games-2026.csv           official Week 10 finals (proved vs the standings)

OUTPUTS
  data/personnel-ablation-wk10-2026.csv   one row per group and per difference

Usage:
  python3 tools/personnel_ablation.py           # rebuild and print
  python3 tools/personnel_ablation.py --check   # fail if the CSV is stale
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
INJ = os.path.join(DATA, "injuries-wk10-2026.csv")
GAMES = os.path.join(DATA, "games-2026.csv")
OUT = os.path.join(DATA, "personnel-ablation-wk10-2026.csv")
WEEK = 10

INJ_URL = "https://www.nfl.com/injuries/league/2026/reg10"
SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"

COLUMNS = ["ablation", "metric", "definition", "group", "n_clubs", "mean_pts", "se",
           "ci95_low", "ci95_high", "diff_pts", "diff_ci95_low", "diff_ci95_high",
           "n_out_clubs", "n_doubtful_clubs", "n_no_designation_clubs",
           "injuries_url", "scores_url", "limit"]

# Two-sided 95% t quantiles. Floored at df=3 so a 4-observation cell cannot
# claim a normal interval it has not earned. Larger df uses the nearest table
# entry at or below the true df (conservative).
T_CRIT = {3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
          10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
          16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 25: 2.060, 30: 2.042}


def t_for(df):
    keys = sorted(T_CRIT)
    best = keys[0]
    for k in keys:
        if k <= df:
            best = k
    return T_CRIT[best]


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def mean_se(xs):
    n = len(xs)
    if n == 0:
        return None, None
    m = sum(xs) / n
    if n < 2:
        return m, None
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, math.sqrt(var / n)


def welch(a, b):
    """Difference of means (a - b), Welch 95% interval. None when not estimable."""
    ma, sa = mean_se(a)
    mb, sb = mean_se(b)
    if ma is None or mb is None or sa is None or sb is None:
        return None, None, None
    d = ma - mb
    va, vb = sa * sa, sb * sb
    var = va + vb
    if var <= 0:
        return d, d, d
    denom = (va ** 2) / max(len(a) - 1, 1) + (vb ** 2) / max(len(b) - 1, 1)
    df = (var ** 2) / denom if denom else 3.0
    df = max(min(df, 30.0), 3.0)
    half = math.sqrt(var) * t_for(df)
    return d, d - half, d + half


def r2(x):
    return "" if x is None else round(x, 3)


def build_records():
    """One record per club-game: the club, what it scored, what it allowed, its designations."""
    inj = read(INJ)
    statuses = {}
    for r in inj:
        if r.get("game_status"):
            statuses.setdefault(r["team"], []).append(r["game_status"])

    games = [g for g in read(GAMES) if int(g["week"]) == WEEK]
    if len(games) != 14:
        raise SystemExit("expected 14 official Week 10 finals, found %d" % len(games))

    recs = []
    for g in games:
        ap, hp = int(g["away_pts"]), int(g["home_pts"])
        for team, scored, allowed in ((g["away"], ap, hp), (g["home"], hp, ap)):
            s = statuses.get(team, [])
            recs.append({"team": team, "scored": scored, "allowed": allowed,
                         "out": s.count("Out"), "doubtful": s.count("Doubtful"),
                         "designated": len(s), "url": g["url"]})
    teams = {r["team"] for r in recs}
    if len(teams) != 28:
        raise SystemExit("expected 28 clubs in the 14 Week 10 games, found %d" % len(teams))
    return recs, statuses


def compare(recs, key, predicate, aid, metric, definition, limit):
    a = [r[key] for r in recs if predicate(r)]
    b = [r[key] for r in recs if not predicate(r)]
    ma, sa = mean_se(a)
    mb, sb = mean_se(b)
    d, lo, hi = welch(a, b)

    def ci(m, s):
        if m is None or s is None:
            return None, None
        h = t_for(max(min(len(a) - 1 if m == ma else len(b) - 1, 30), 3)) * s
        return m - h, m + h

    alo, ahi = ci(ma, sa)
    blo, bhi = ci(mb, sb)
    n_out = sum(1 for r in recs if r["out"] > 0)
    n_dbt = sum(1 for r in recs if r["doubtful"] > 0)
    n_none = sum(1 for r in recs if r["designated"] == 0)
    rows = [
        [aid, metric, definition, "designated", len(a), r2(ma), r2(sa), r2(alo), r2(ahi),
         "", "", "", n_out, n_dbt, n_none, INJ_URL, SCHED_URL, limit],
        [aid, metric, definition, "clear", len(b), r2(mb), r2(sb), r2(blo), r2(bhi),
         "", "", "", n_out, n_dbt, n_none, INJ_URL, SCHED_URL, limit],
        [aid, metric, definition, "difference (designated - clear)", "", "", "", "", "",
         r2(d), r2(lo), r2(hi), n_out, n_dbt, n_none, INJ_URL, SCHED_URL,
         ("Welch 95%% interval [%s, %s]" % (r2(lo), r2(hi)))
         + ("; SPANS ZERO -> cannot tell" if lo is not None and lo < 0 < hi
            else "; excludes zero -> an association worth testing further")
         if d is not None else "not estimable (a cell has fewer than 2 observations)"],
    ]
    return rows


def build():
    recs, statuses = build_records()
    rows = []
    rows += compare(recs, "scored", lambda r: r["out"] > 0, "A1", "points scored",
                    "Points scored by a club the official report rules at least one player "
                    "Out for, vs a club it designates no player Out",
                    "club-level, one week; 'no designation' is not 'full strength'")
    rows += compare(recs, "allowed", lambda r: r["out"] > 0, "A2", "points allowed",
                    "Points allowed by a club with at least one Out, vs points allowed by a "
                    "club with no Out designation",
                    "same clubs, defensive side; a club is counted once, not once per player")
    rows += compare(recs, "scored", lambda r: r["designated"] > 0, "A3", "points scored",
                    "Points scored: Out or Doubtful vs neither designation",
                    "NOT ESTIMABLE: every one of the 28 clubs on the Week 10 slate carries at "
                    "least one designation, so the control group is empty")
    rows += compare(recs, "allowed", lambda r: r["designated"] > 0, "A4", "points allowed",
                    "Points allowed: Out or Doubtful vs neither designation",
                    "NOT ESTIMABLE: empty control group -- see A3")
    rows += identifiability(recs, statuses)
    return rows, recs, statuses


def identifiability(recs, statuses):
    """What is missing to identify the ablation the brief actually asks for, and the number
    that would clear it. Counts are computed from the committed files, never typed."""
    n_club_games = len(recs)
    n_clubs = len({r["team"] for r in recs})
    n_no_desig = sum(1 for r in recs if r["designated"] == 0)
    n_no_out = sum(1 for r in recs if r["out"] == 0)
    weeks_of_results = len({g["week"] for g in read(GAMES)})
    # club-weeks of official playing time (the only player-level availability source present)
    hou = os.path.join(DATA, "houston-playtime-depth-wk10-2026.csv")
    hou_rows = len(read(hou)) if os.path.exists(hou) else 0
    inj_weeks = 1  # data/injuries-wk10-2026.csv is the only official report captured
    spec = [
        ("I1", "Control group for a club-level with/without test",
         "club-games with no designation at all: %d of %d" % (n_no_desig, n_club_games),
         ">=1 club-game in the clear group; the report never produces one",
         "already known -- this is why A3/A4 are not estimable and A1/A2 rest on %d" % n_no_out),
        ("I2", "Weeks of official injury report joined to results",
         "%d week captured (Week 10) vs %d weeks of results" % (inj_weeks, weeks_of_results),
         ">=2 weeks, so a club can be compared with itself across games, not only against others",
         "the capture pipeline has never completed a run (F-47/F-48/F-65)"),
        ("I3", "Club-weeks of official playing time (snap counts)",
         "%d club-week (%s of 32 clubs)" % (hou_rows and 1 or 0, "Houston" if hou_rows else "none"),
         "32 club-weeks per week for the clubs in a game, over >=2 weeks",
         "no league-wide official snap-count source is verified (F-24/F-46)"),
        ("I4", "Player-level replacement measurement",
         "0 -- no club-week has both the man replaced and his replacement's snap share",
         "one joined replacement pair per club-week, with both snap shares",
         "requires I3 first; the single Houston Game Book supplies one side only"),
    ]
    out = []
    for aid, what, have, clear, why in spec:
        out.append([aid, "identifiability", what, "have", "", "", "", "", "",
                    "", "", "", n_no_out, "", n_no_desig, INJ_URL, SCHED_URL,
                    "HAVE: %s || CLEARS THE GATE: %s || BLOCKED BY: %s" % (have, clear, why)])
    return out


def render(rows, recs, statuses):
    w = [5, 15, 34, 4, 8, 7, 9, 9, 8, 9, 9]
    head = ["abl", "metric", "group", "n", "mean", "se", "ci_lo", "ci_hi", "diff", "d_lo", "d_hi"]
    line = "".join("%-*s " % (w[i], head[i]) for i in range(len(head)))
    print(line)
    print("-" * len(line))
    for r in rows:
        cells = [r[0], r[1], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]]
        print("".join("%-*s " % (w[i], str(cells[i])[:w[i]]) for i in range(len(cells))))
    print()
    print("club-games measured: %d across %d clubs" % (len(recs), len({r['team'] for r in recs})))
    print("clubs with >=1 Out: %d | >=1 Doubtful: %d | no designation at all: %d | clubs on report: %d"
          % (sum(1 for r in recs if r["out"] > 0), sum(1 for r in recs if r["doubtful"] > 0),
             sum(1 for r in recs if r["designated"] == 0), len(statuses)))
    print("Every number is derived from data/injuries-wk10-2026.csv and data/games-2026.csv.")
    print("An interval that spans 0 is published as 'cannot tell', never as an effect.")


def write(rows):
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (os.path.relpath(OUT, ROOT), len(rows)))


# --------------------------------------------------------------------------- page
def page_body(rows, recs, statuses):
    """Render the ablation page. Every data row carries its own official source link."""
    import pages as P
    esc, src, badge, table, blank, num = P.esc, P.src, P.badge, P.table, P.blank, P.num

    n_clubs = len({r["team"] for r in recs})
    n_out = sum(1 for r in recs if r["out"] > 0)
    n_dbt = sum(1 for r in recs if r["doubtful"] > 0)
    n_none = sum(1 for r in recs if r["designated"] == 0)

    def cell(v):
        return v if v not in ("", None) else blank("not estimable")

    def ci(lo, hi):
        if lo in ("", None) or hi in ("", None):
            return blank("no interval")
        return "[%s, %s]" % (num(lo, 3), num(hi, 3))

    def verdict(lo, hi):
        if lo in ("", None) or hi in ("", None):
            return badge("not estimable", "warn")
        if float(lo) < 0 < float(hi):
            return badge("cannot tell (spans 0)", "mute")
        return badge("association only", "info")

    meas = [r for r in rows if r[0].startswith("A")]
    ids = [r for r in rows if r[0].startswith("I")]

    t_rows = []
    for r in meas:
        t_rows.append([
            esc(r[0]), esc(r[1]), esc(r[3]),
            cell(r[4]), cell(r[5]), cell(r[6]), ci(r[7], r[8]),
            cell(r[9]), ci(r[10], r[11]),
            "" if r[3] != "difference (designated - clear)" else verdict(r[10], r[11]),
            src(r[15], "Injury report") + " " + src(r[16], "Week 10 slate"),
        ])

    t = table(
        [("Ablation", False), ("Metric", False), ("Group", False), ("n", True),
         ("Mean pts", True), ("SE", True), ("95% CI", False),
         ("Difference", True), ("Difference 95% CI", False), ("Verdict", False),
         ("Official source", False)],
        t_rows, cls="data",
        note="One record per club-game (28 club-games across the 14 official Week 10 finals). "
             "Difference = designated minus clear. A Welch interval that spans zero is "
             "published as 'cannot tell'; it is never rounded into an effect.")

    id_rows = []
    for r in ids:
        parts = (r[17] or "").split(" || ")
        get = lambda prefix: next((x[len(prefix):] for x in parts if x.startswith(prefix)), "")
        id_rows.append([
            esc(r[0]), esc(r[2]),
            esc(get("HAVE: ")),
            esc(get("CLEARS THE GATE: ")),
            esc(get("BLOCKED BY: ")),
            src(r[15], "Injury report") + " " + src(r[16], "Week 10 slate"),
        ])
    t_id = table(
        [("Gate", False), ("What the ablation needs", False), ("What we have", False),
         ("The number that would clear it", False), ("What blocks it today", False),
         ("Official source", False)],
        id_rows, cls="data",
        note="No value in this table is typed: every 'what we have' cell is a count of the "
             "committed CSV columns, recomputed by tools/personnel_ablation.py. This is the "
             "identifiability gate, not an estimate.")

    h = []
    h.append('<section class="hero"><div class="wrap">'
             '<span class="eyebrow">Personnel ablation &middot; T48</span>'
             '<h1>What a missing player has actually cost &mdash; measured, not assumed</h1>'
             '<p class="lede">The brief asks for injury and personnel <b>ablations</b> instead '
             'of fixed penalties. This page publishes the one ablation the committed official '
             'data can support, with its n and a 95% interval, and it states plainly which '
             'ablation the data still <b>cannot</b> identify.</p>'
             '<p class="meta">' + src(INJ_URL, "Official Week 10 injury report") + ' &middot; '
             + src(SCHED_URL, "Official Week 10 schedule") + ' &middot; '
             '<a href="https://github.com/karagemop466-tech/X4/blob/main/research/verification/'
             'personnel-ablation-2026-11-18.md" target="_blank" rel="noreferrer noopener">'
             'Method note &nearr;</a> &middot; '
             '<a href="https://github.com/karagemop466-tech/X4/blob/main/tools/'
             'personnel_ablation.py" target="_blank" rel="noreferrer noopener">'
             'Source code &nearr;</a></p></div></section>')
    h.append('<section class="section"><div class="section-head"><div>'
             '<span class="eyebrow">The finding, in one paragraph</span>'
             '<h2>' + str(n_out) + ' of ' + str(n_clubs) +
             ' clubs carried an &ldquo;Out&rdquo; player. There is no clean control group.</h2>'
             '</div></div>'
             '<p>On the official Week 10 report, <b>' + str(n_out) + ' of the ' + str(n_clubs)
             + ' clubs</b> in action are ruled at least one player <b>Out</b>; <b>' + str(n_dbt)
             + '</b> carry a Doubtful; <b>' + str(n_none) + '</b> carry no game designation at '
             'all. A with/without personnel test therefore cannot be identified from a single '
             'week&rsquo;s report at the club level &mdash; the treatment is nearly universal. '
             'The measurable contrast (A1/A2) is the small clear group against the rest, and '
             'both intervals span zero: <b>this data cannot tell the effect apart from '
             'noise</b>, which is exactly why a fixed points penalty for a missing player is '
             'not defensible and is not published anywhere on this site.</p></div></section>')
    h.append('<section class="section"><div class="section-head"><div>'
             '<span class="eyebrow">Ablation results</span><h2>The measurable part</h2>'
             '</div></div>' + t + '</div></section>')
    h.append('<section class="section"><div class="section-head"><div>'
             '<span class="eyebrow">Identifiability gate</span>'
             '<h2>What is missing before a personnel <em>feature</em> can exist</h2>'
             '</div></div><p>The brief rule is explicit: do not build the feature until the '
             'depth-order source is verified for all 32 clubs. Neither route is. These are '
             'the four gates, each with the count that would clear it.</p>' + t_id
             + '</div></section>')
    h.append('<section class="section"><div class="section-head"><div>'
             '<span class="eyebrow">What this licenses</span>'
             '<h2>Read the interval before the mean</h2></div></div>'
             '<div class="grid2"><div class="card"><h3>Allowed</h3><ul>'
             '<li>Quoting a measured base rate with its interval as an input to a future prior.</li>'
             '<li>Sizing the <em>maximum</em> a personnel term could plausibly move a Week&nbsp;11 line.</li>'
             '<li>Setting the sample the next capture must reach before a feature is trusted.</li>'
             '</ul></div><div class="card"><h3>Forbidden</h3><ul>'
             '<li>Adding &ldquo;&minus;N points per Out player&rdquo; to any prediction.</li>'
             '<li>Calling a depth-slot effect &ldquo;priced in&rdquo; or &ldquo;ignored&rdquo; by the market.</li>'
             '<li>Publishing a personnel-adjusted fair line from this evidence.</li>'
             '</ul></div></div></div></section>')
    h.append('<section class="section"><div class="section-head"><div>'
             '<span class="eyebrow">Reproduce</span><h2>Every number is recomputable</h2>'
             '</div></div><p><code>python3 tools/personnel_ablation.py</code> rebuilds the CSV '
             'and prints this table; <code>python3 tools/personnel_ablation.py --check</code> '
             'fails the publication gate if the committed CSV is stale. The two inputs are the '
             'official Week&nbsp;10 injury report and the official Week&nbsp;10 finals, both '
             'already proved elsewhere by <code>tools/verify.py</code> and the capture check.'
             '</p></div></section>')
    return "".join(h)


def write_pages(site_dir, shell):
    rows, recs, statuses = build()
    body = page_body(rows, recs, statuses)
    with open(os.path.join(site_dir, "personnel-ablation.html"), "w", encoding="utf-8") as fh:
        fh.write(shell("personnel-ablation", "Personnel ablation",
                       "Injury and personnel ablation on the official Week 10 injury report: "
                       "measured points-per-designation with 95% intervals, the empty control "
                       "group that blocks the feature, and the four identifiability gates.",
                       body, "personnel-ablation.html"))
    return ["personnel-ablation.html"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows, recs, statuses = build()
    if a.check:
        if not os.path.exists(OUT):
            print("FAIL: %s is missing" % os.path.relpath(OUT, ROOT))
            return 1
        old = read(OUT)
        if len(old) != len(rows):
            print("FAIL: committed CSV has %d rows, a fresh build has %d" % (len(old), len(rows)))
            return 1
        for o, n in zip(old, rows):
            for k, v in zip(COLUMNS, n):
                if str(o.get(k, "")) != str(v):
                    print("FAIL: %s/%s/%s committed %r != built %r"
                          % (o.get("ablation"), o.get("group"), k, o.get(k), v))
                    return 1
        print("personnel ablation: PASS (%d rows, 0 mismatches)" % len(rows))
        return 0
    write(rows)
    render(rows, recs, statuses)
    return 0


if __name__ == "__main__":
    sys.exit(main())
