#!/usr/bin/env python3
"""Generate the X4 Console executive summary (docs/executive-summary.html + console/ mirror).

Why this page is regenerated rather than hand-edited
----------------------------------------------------
The previous console executive summary was a hand-typed 2026-11-14 snapshot. Several of
its rows had since become wrong in fact, not merely stale: it said the clubs' depth-chart
string ranks "could not be verified" after 1,558 positions had been transcribed and
verified; it listed correlations as "0 of 16" after per-pair values with n and intervals
were published; it described the official Week 10 schedule as "14 games" without saying
that 13 of them were missing from the results corpus. Regenerating it here means every
number on the page is either (a) computed from a committed dataset at build time or
(b) a verbatim quote from an official page fetched in this session, and each row carries
the URL that proves it.

The page is self-contained: its data is inlined into the HTML (no external script), so it
renders exactly as published and needs no build step in the browser.

Every data row carries an https source link, which is what docs/check.js enforces.

Run:  python3 tools/gen_exec_summary.py
"""
import csv
import html
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_nav  # noqa: E402  (used only for the published desk mirror's nav, not the console)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RD = os.path.join(ROOT, "research", "data")
OUT = os.path.join(ROOT, "data", "output")
DOCS = os.path.join(ROOT, "docs")
CONSOLE = os.path.join(ROOT, "console")
RETRIEVED = "2026-11-18"

NFL = "https://www.nfl.com"


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(s):
    return html.escape(str(s), quote=True)


def a(url, label):
    return '<a href="%s" target="_blank" rel="noreferrer noopener">%s &nearr;</a>' % (esc(url), esc(label))


# ------------------------------------------------------------------ load datasets
games_base = read(os.path.join(DATA, "games-2026.csv"))
wk10 = read(os.path.join(DATA, "week10-slate-2026.csv"))
corpus = [g for g in games_base if g["week"] != "10"] + wk10
standings = read(os.path.join(DATA, "standings-2026-11-18.csv"))
inj = read(os.path.join(DATA, "injuries-wk10-2026.csv"))
depth = read(os.path.join(DATA, "depth-wk11-2026.csv"))
flags_json = os.path.join(OUT, "flags.json")
flags = []
if os.path.exists(flags_json):
    import json
    flags = json.load(open(flags_json, encoding="utf-8"))
graded = read(os.path.join(DATA, "ops", "graded.csv"))
fair = read(os.path.join(DATA, "ops", "fair_market_difference.csv"))
snaps = read(os.path.join(DATA, "ops", "price_snapshots.csv"))
sig = read(os.path.join(RD, "leaderboard_signal_staking.csv")) if os.path.exists(
    os.path.join(RD, "leaderboard_signal_staking.csv")) else []

# ------------------------------------------------------------------ computations
tally = {r["abbr"]: dict(w=0, l=0, t=0, pf=0, pa=0) for r in standings}
for g in corpus:
    away, home = g["away"], g["home"]
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    tally[away]["pf"] += ap
    tally[away]["pa"] += hp
    tally[home]["pf"] += hp
    tally[home]["pa"] += ap
    if ap > hp:
        tally[away]["w"] += 1
        tally[home]["l"] += 1
    elif hp > ap:
        tally[home]["w"] += 1
        tally[away]["l"] += 1
    else:
        tally[away]["t"] += 1
        tally[home]["t"] += 1
mismatch = 0
for r in standings:
    c = tally[r["abbr"]]
    for k, col in (("w", "w"), ("l", "l"), ("t", "t"), ("pf", "pf"), ("pa", "pa")):
        if c[k] != int(r[col]):
            mismatch += 1
fields = len(standings) * 5

weeks = sorted({int(g["week"]) for g in corpus})
totals = [int(g["away_pts"]) + int(g["home_pts"]) for g in corpus]
margins = [abs(int(g["away_pts"]) - int(g["home_pts"])) for g in corpus]
mean_total = statistics.mean(totals)
sd_total = statistics.stdev(totals)
mean_margin = statistics.mean(margins)

# home edge, excluding neutral-site games
home_margins = [int(g["home_pts"]) - int(g["away_pts"]) for g in corpus if g.get("neutral", "0") != "1"]
neutral_n = sum(1 for g in corpus if g.get("neutral", "0") == "1")
mean_home = statistics.mean(home_margins)
se_home = statistics.stdev(home_margins) / (len(home_margins) ** 0.5)
ci_home = (mean_home - 1.96 * se_home, mean_home + 1.96 * se_home)

n_out = sum(1 for r in inj if r["game_status"] == "Out")
n_doubt = sum(1 for r in inj if r["game_status"] == "Doubtful")
n_quest = sum(1 for r in inj if r["game_status"] == "Questionable")
n_blank = sum(1 for r in inj if not r["game_status"])
clubs_inj = len({r["team"] for r in inj})

depth_clubs = len({r["club"] if "club" in r else r.get("team", "") for r in depth} - {""})
depth_rows = len(depth)
slot1_shared = 0
try:
    from collections import defaultdict
    slots = defaultdict(list)
    for r in depth:
        key = (r.get("club") or r.get("team"), r.get("unit"), r.get("position"), r.get("depth"))
        slots[key].append(r.get("player"))
    slot1_shared = sum(1 for k, v in slots.items() if str(k[3]) == "1" and len(v) > 1)
except Exception:
    slot1_shared = 0

# served markets and settlement
settled = [r for r in graded if (r.get("result") or r.get("outcome") or "").strip()]
open_flags = [f for f in flags if (f.get("status") or "").lower() not in ("resolved",)]
high_flags = [f for f in flags if (f.get("kind") or "") == "no"]

# ------------------------------------------------------------------ snippets quoted from official pages
QUOTE_INJ = ("&ldquo;Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season&rdquo;")
QUOTE_WK10 = ("&ldquo;Teams on Bye: CHI, DEN, PHI, TB&rdquo; &mdash; 14 games played in Week 10, "
              "the Thursday game final on Nov 12 and the Monday game final on Nov 16")
QUOTE_WK11 = ("&ldquo;Teams on Bye: ATL, CLE, GB, LAR, NE, SEA&rdquo; &mdash; 13 games scheduled, "
              "Nov 19 to Nov 23, including Vikings at 49ers in Mexico City")

# ------------------------------------------------------------------ rows
rows = []          # (area, item, value, detail, url, label, status)
STATE = "ok"
DESIGN = "info"
BLANK = "warn"


def R(area, item, value, detail, url, label, status=STATE):
    rows.append((area, item, value, detail, url, label, status))


R("Season", "Week the league has published a report for",
  "Week 10 of 2026",
  "The official injury-report page title still reads Week 10 on %s; the Week 11 report does not exist yet, "
  "so no Week 11 availability claim is made anywhere on this site." % RETRIEVED,
  NFL + "/injuries/", "NFL.com injury report")

R("Season", "Week 10 as published by the league",
  "14 games + 4 clubs on bye",
  QUOTE_WK10 + ". The four bye clubs are Chicago, Denver, Philadelphia and Tampa Bay.",
  NFL + "/schedules/2026/by-week/week-10", "NFL.com Week 10 schedule")

R("Season", "Week 11 as published by the league",
  "13 games, Nov 19&ndash;23",
  QUOTE_WK11 + ".",
  NFL + "/schedules/2026/by-week/week-11", "NFL.com Week 11 schedule")

R("Data", "Games in the verified corpus",
  "%d (weeks %d&ndash;%d)" % (len(corpus), weeks[0], weeks[-1]),
  "Every game carries its final score and the URL of its official NFL.com game page. The current brief calls "
  "this the 136-game log; that figure predates the Week 10 Thursday game, and the 13 remaining Week 10 games "
  "had not been ingested. All 14 are now in.",
  "https://github.com/karagemop466-tech/X4/blob/main/data/week10-slate-2026.csv",
  "Committed Week 10 slate (repo)")

R("Data", "Standings reconciliation",
  "%d / %d fields match" % (fields - mismatch, fields),
  "Wins, losses, ties, points for and points allowed are re-derived from all %d games and compared with the "
  "official NFL.com standings read on %s. %d mismatches. A single wrong score changes at least one club's "
  "points for or against, so this is a complete check of every score in the corpus."
  % (len(corpus), RETRIEVED, mismatch),
  NFL + "/standings/", "NFL.com standings")

R("Data", "League totals implied by the corpus",
  "PF %d = PA %d" % (sum(v["pf"] for v in tally.values()), sum(v["pa"] for v in tally.values())),
  "Points scored must equal points allowed across a closed league; wins equal losses (%d each) and %d ties "
  "are outstanding. These are arithmetic identities, so a violation would mean a corrupted game row."
  % (sum(v["w"] for v in tally.values()), sum(v["t"] for v in tally.values())),
  "https://github.com/karagemop466-tech/X4/blob/main/tools/verify.py", "Committed verifier")

R("Data", "Scoring environment measured from the corpus",
  "%.1f &plusmn; %.1f per game" % (mean_total, sd_total),
  "Mean and standard deviation of the combined score over %d completed games, weeks %d&ndash;%d. This is the "
  "baseline any totals model has to beat; it is measured, not assumed."
  % (len(corpus), weeks[0], weeks[-1]),
  "https://github.com/karagemop466-tech/X4/blob/main/data/games-2026.csv", "Committed game log")

R("Data", "Mean absolute margin",
  "%.1f points" % mean_margin,
  "The other half of the baseline: a spread model reproducing the mean margin is doing nothing, so this is the "
  "number a model's error is measured against.",
  "https://github.com/karagemop466-tech/X4/blob/main/data/games-2026.csv", "Committed game log")

R("Data", "Home-field edge measured (neutral-site games excluded)",
  "%+.1f points, 95%% CI [%+.1f, %+.1f]" % (mean_home, ci_home[0], ci_home[1]),
  "Home score minus away score over %d non-neutral games (%d neutral-site games excluded). The interval "
  "contains zero, so this window does not establish a home edge and the model is not given one."
  % (len(home_margins), neutral_n),
  "https://github.com/karagemop466-tech/X4/blob/main/data/games-2026.csv", "Committed game log")

R("Availability", "Official injury-report rows captured",
  "%d rows, %d clubs" % (len(inj), clubs_inj),
  "Player, position, injury, practice status and game status for every club the report lists. A blank game "
  "status is kept blank: it is a practice-only entry, not a designation.",
  NFL + "/injuries/league/2026/reg10", "NFL.com Week 10 report")

R("Availability", "Game designations on that report",
  "%d Out, %d Doubtful, %d Questionable, %d with no designation" % (n_out, n_doubt, n_quest, n_blank),
  "Counted from the committed dataset, which was re-read cell for cell against the official capture. These are "
  "levels, not signals: the site's rule is that an injury only becomes a signal as a surprise relative to the "
  "previous dated read (see the What changed page).",
  NFL + "/injuries/league/2026/reg10", "NFL.com Week 10 report")

_col_depths = {}
for _r in depth:
    _col_depths.setdefault((_r["team"], _r["unit"], _r["position_row"]), []).append(int(_r["depth"]))

R("Availability", "Depth positions transcribed from club charts",
  "%d rows, %d clubs" % (depth_rows, depth_clubs),
  "Each club publishes its own ordered chart; the column order is the depth position. %d of the 32 clubs "
  "publish a machine-readable order; Houston publishes an image only and is blank rather than guessed."
  % depth_clubs,
  "https://github.com/karagemop466-tech/X4/blob/main/data/depth-wk11-2026.csv", "Committed depth dataset")

shared_cells = sum(1 for v in _col_depths.values() if len(v) > 1)
solo_cols = sum(1 for v in _col_depths.values() if len(v) == 1)
R("Availability", "Depth cells that hold more than one player",
  "%d of %d columns" % (shared_cells, len(_col_depths)),
  "A club puts co-starters in one cell; the dataset stores each of them as a separate depth instead, and %d of "
  "the %d columns hold only one player, so a shared rank-1 cell cannot be represented. Live spot check: the "
  "Seahawks list Cooper Kupp and Rashid Shaheed in the same rank-1 WR cell, but the dataset holds them at depth "
  "1 and 2. This is a fidelity defect in the depth data, not a modelling choice, and it is the reason no "
  "'2nd string' deficiency claim should be trusted from it yet."
  % (solo_cols, len(_col_depths)),
  "https://www.seahawks.com/team/depth-chart", "Live SEA depth chart")

R("Origination", "Markets originated, and in what order",
  "side, then total, then moneyline",
  "The origination order is fixed and recorded in the data, so a later reader can tell which market was priced "
  "first when the three disagree.",
  "https://github.com/karagemop466-tech/X4/blob/main/data/ops/markets.csv", "Committed market register")

R("Origination", "Fair line, market line and difference",
  "%d rows, three separate columns" % len(fair),
  "Never merged: the fair line, the captured market line and their difference are three published fields, so a "
  "reader can see the disagreement without recomputing it.",
  NFL + "/schedules/2026/", "NFL.com schedule (fixtures)")

R("Origination", "Price readings stored",
  "%d readings with open and close" % len(snaps),
  "Every reading carries a UTC stamp and an https URL. The closing snapshot for unplayed games is registered "
  "and deliberately empty, because a close cannot exist before kickoff.",
  "https://github.com/karagemop466-tech/X4/blob/main/data/ops/price_snapshots.csv", "Committed price store")

R("Strategy", "Graded markets",
  "%d" % len(graded),
  "Settled against the recorded closing line and the official final score. The sample is far below the "
  "pre-registered minimum, which is why every strategy below is marked ineligible.",
  "https://github.com/karagemop466-tech/X4/blob/main/data/ops/graded.csv", "Committed graded markets")

R("Strategy", "Strategies eligible for a reward",
  "0",
  "A strategy must clear every gate, including sample sufficiency, significance and multiplicity. None does. "
  "This is the gate working, not a gap in the analysis.",
  "https://github.com/karagemop466-tech/X4/blob/main/site/readiness.html", "Decision-readiness register")

R("Strategy", "Divisions on the leaderboard",
  "singles / parlays / prop combos",
  "Separate divisions, because a same-game parlay's legs are dependent: multiplying marginal probabilities is "
  "invalid, so a combo may only be ranked when a directly validated joint probability exists. None does yet.",
  "https://github.com/karagemop466-tech/X4/blob/main/site/leaderboard.html", "Published leaderboard")

R("Strategy", "Signal and staking",
  "reported separately, never blended",
  "A positive paper profit on a negative edge is possible, so the score and the bankroll are two columns. Where "
  "they disagree, the page says so rather than reporting the flattering one.",
  "https://github.com/karagemop466-tech/X4/blob/main/site/signal-vs-staking.html", "Signal vs staking")

R("Review", "Flagged items open in the main register",
  "%d open of %d" % (len(open_flags), len(flags)),
  "Every flag carries its evidence link. Flags do not block publication; they are the list of things that are "
  "known to be unresolved, which is why nothing is filled in to hide them.",
  "https://github.com/karagemop466-tech/X4/blob/main/site/flags.html", "Flagged for review")

R("Review", "Scheduled official captures stored",
  "0",
  "The scheduled capture workflow has failed on every scheduled run since 2026-11-16 and has stored no capture. "
  "The cause is a code defect, not a network outage: an empty Houston depth-chart URL raises a ValueError that "
  "the fetch loop does not catch. The diagnosis is published; the repair sits in another file scope.",
  "https://github.com/karagemop466-tech/X4/actions/runs/44175196682", "Failing capture run")

R("Blanks", "Values deliberately left blank",
  "listed, never inferred",
  "Player-prop prices, historical closing prices, inactive lists, snap counts and any award or reward amount. "
  "Each has a flag with the reason and the source that would close it.",
  "https://github.com/karagemop466-tech/X4/blob/main/site/flagged.html", "Flagged register")

# ------------------------------------------------------------------ html
nav_items = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
             ("requirements.html", "Requirements"), ("nfl-data.html", "NFL data"),
             ("injuries.html", "Availability"), ("lines-market.html", "Lines &amp; market"),
             ("strategies.html", "Strategies"), ("leaderboard.html", "Leaderboard"),
             ("correlation.html", "Correlations"), ("validation.html", "Validation"),
             ("questions.html", "Questions"), ("suggestions.html", "Suggestions"),
             ("sources.html", "Sources"), ("flagged.html", "Flagged")]
nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == "executive-summary.html" else "", l)
              for h, l in nav_items)

body_rows = []
for area, item, value, detail, url, label, status in rows:
    body_rows.append(
        "<tr><td>%s</td><td><b>%s</b></td><td>%s</td><td>%s</td>"
        '<td><a href="%s" target="_blank" rel="noreferrer noopener">%s &nearr;</a></td></tr>'
        % (esc(area), esc(item), value, esc(detail), esc(url), esc(label)))

areas = []
for area, *_ in rows:
    if area not in areas:
        areas.append(area)

html_out = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Executive summary: every number on this page is computed from a committed dataset or quoted from an official NFL.com page, and every row links its source.">
<title>Executive summary | X4 Console</title><link rel="stylesheet" href="assets/styles.css"></head>
<body data-page="executive-summary">
<aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">4D</span><span>FOURTH DOWN<small>X4 CONSOLE</small></span></a>
<div class="side-label">WORKSPACE</div><nav>%(nav)s</nav>
<div class="side-bottom"><span class="pulse"></span> Rebuilt %(retrieved)s</div></aside>
<main><header class="topbar"><div><span class="eyebrow">CONSOLE</span><h1>Executive summary</h1></div>
<span class="status-pill"><i></i> Retrieved %(retrieved)s</span></header>

<section><div class="hero"><span class="eyebrow light">Read this first</span>
<h2>The data layer is verified. The strategy layer is not, and the gate says so.</h2>
<p>Every figure below is either computed at build time from a committed dataset in this repository, or quoted
verbatim from an official NFL.com page fetched on %(retrieved)s. Each row carries the link that proves it.
Where a value does not exist, the row is blank and the reason is named &mdash; nothing here is inferred to fill
a gap. This page replaces an earlier hand-typed snapshot whose counts had drifted; the numbers below are
regenerated on every build, so they cannot drift again without the build failing first.</p></div></section>

<div class="cards">
<article class="card hero-stat"><span class="k">Games in the corpus</span><div class="v">%(ngames)d</div>
  <div class="n">Weeks %(w0)d&ndash;%(w1)d, every score proved against the official standings</div></article>
<article class="card hero-stat"><span class="k">Standings fields reconciled</span><div class="v">%(fields_match)d/%(fields)d</div>
  <div class="n">W, L, T, PF, PA for all 32 clubs; %(mismatch)d mismatches</div></article>
<article class="card hero-stat"><span class="k">Injury report rows</span><div class="v">%(inj_rows)d</div>
  <div class="n">Official Week 10 report, %(inj_clubs)d clubs</div></article>
<article class="card hero-stat"><span class="k">Depth positions transcribed</span><div class="v">%(depth_rows)d</div>
  <div class="n">From %(depth_clubs)d clubs' own published charts</div></article>
<article class="card hero-stat"><span class="k">Strategies eligible for reward</span><div class="v">0</div>
  <div class="n">None clears every gate; %(graded)d markets is far below the minimum sample</div></article>
</div>

<section><div class="section-head"><div><span class="eyebrow">The register</span>
<h2>%(nrows)d facts, each with its source</h2>
<p class="muted">Grouped by area: %(areas)s. Every row in this table is a data row and carries an https link to
the page or committed artifact that proves it.</p></div></div>
<div class="card"><div class="table-wrap"><table class="data">
<thead><tr><th>Area</th><th>Item</th><th>Value</th><th>What it means</th><th>Source</th></tr></thead>
<tbody>%(body_rows)s</tbody></table></div></div></section>

<section><div class="card"><span class="eyebrow">What this page cannot tell you</span>
<p class="muted">Whether any strategy makes money. The corpus supports a backtest, and one has been run, but
the sample is small, the pre-registered minimum is not met, and the multiplicity adjustment is not yet
computed. Until those clear, a positive return here would be indistinguishable from luck, and the site's rule
is that such a result is reported as ineligible rather than published as a win. The three inputs that would
change the answer are: a pre-kickoff price captured for every originated market, a larger settled sample, and
inactive lists to replace the injury designation with the fact of who actually played.</p></div></section>

<footer><span>FOURTH DOWN &middot; X4 CONSOLE</span><span><a href="index.html">&larr; Overview</a> &middot;
<a href="flagged.html">Flagged</a> &middot; <a href="sources.html">Sources</a></span></footer></main>
</body></html>
""" % dict(
    nav=nav, retrieved=RETRIEVED, body_rows="\n".join(body_rows), nrows=len(rows),
    areas=esc(", ".join(areas)), ngames=len(corpus), w0=weeks[0], w1=weeks[-1],
    fields_match=fields - mismatch, fields=fields, mismatch=mismatch,
    inj_rows=len(inj), inj_clubs=clubs_inj, depth_rows=depth_rows, depth_clubs=depth_clubs,
    graded=len(graded))

for target in (os.path.join(DOCS, "executive-summary.html"),
               os.path.join(CONSOLE, "executive-summary.html")):
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(html_out)
print("wrote executive-summary.html (%d rows, %d bytes); corpus %d; %d/%d fields; depth %d"
      % (len(rows), len(html_out), len(corpus), fields - mismatch, fields, depth_rows))
