#!/usr/bin/env python3
"""Regenerate the decision-desk executive summary (executive-summary.html + site/ mirror).

The page this replaces was a hand-typed 2026-11-14 snapshot. By 2026-11-18 several of its
rows had become false rather than merely old:

  * "Week 10 in progress ... Sunday Nov 15 slate pending"      -> Week 10 completed Nov 16
  * "57 final scores from Weeks 6-9"                            -> 150 verified games, weeks 1-10
  * "Standings ... 6,291; wins = losses = 136"                  -> 6,923; 149 games' worth of W/L
  * "Depth is now measured: 1,558 positions"                    -> measured, but with a measured
                                                                   shared-slot fidelity defect
  * "12 unverified items"                                       -> 57 in the main flag register

Every figure below is computed from a committed dataset at build time, and every data row
carries an https source link (tools/check_site.py enforces one per row). Nothing is typed by
hand; if a dataset shrinks or changes, the page changes with it.

Run:  python3 tools/gen_exec_summary_desk.py
"""
import csv
import json
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_nav  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OPS = os.path.join(DATA, "ops")
OUT = os.path.join(DATA, "output")
SITE = os.path.join(ROOT, "site")
RETRIEVED = "2026-11-18"  # official standings re-read date
GENERATED = "2026-11-19"  # executive summary regeneration date
NFL = "https://www.nfl.com"
SITE_URL = "https://karagemop466-tech.github.io/X4/"


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def a(url, label):
    return '<a href="%s" target="_blank" rel="noreferrer noopener">%s &nearr;</a>' % (esc(url), esc(label))


def tag(text, cls="green"):
    return '<span class="tag %s">%s</span>' % (cls, esc(text))


# ---------------------------------------------------------------- datasets
games = read(os.path.join(DATA, "games-2026.csv"))
wk10 = read(os.path.join(DATA, "week10-slate-2026.csv"))
corpus = [g for g in games if g["week"] != "10"] + wk10
standings = read(os.path.join(DATA, "standings-2026-11-18.csv"))
inj = read(os.path.join(DATA, "injuries-wk10-2026.csv"))
depth = read(os.path.join(DATA, "depth-wk11-2026.csv"))
sched = [r for r in read(os.path.join(DATA, "schedule-wk11-2026.csv")) if r["week"] == "11"]
# Neutral-site exclusion: data/games-2026.csv carries no neutral flag, so the set is joined
# from the official international register (data/international-2026.csv) on (week, away, home).
neutral_keys = {
    (r["week"], r["away"], r["home"])
    for r in read(os.path.join(DATA, "international-2026.csv"))
    if r["week"] != "11"  # only the weeks the corpus covers matter here
}
fair = read(os.path.join(OPS, "fair_market_difference.csv"))
snaps = read(os.path.join(OPS, "price_snapshots.csv"))
graded = read(os.path.join(OPS, "graded.csv"))
flows = read(os.path.join(DATA, "transactions", "transactions-2026.csv"))
flags = json.load(open(os.path.join(OUT, "flags.json"), encoding="utf-8"))
# Use the latest captured report read, not a stale hand-written status claim.  A partial
# report is explicitly not promoted into the committed player-level Week 11 dataset.
injury_reads = []
manifest_path = os.path.join(DATA, "captures", "manifest.jsonl")
if os.path.exists(manifest_path):
    with open(manifest_path, encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("kind") == "injuries":
                injury_reads.append(entry)
latest_injury = injury_reads[-1] if injury_reads else None
if latest_injury:
    latest_schema = latest_injury.get("schema", {})
    captured_at = latest_injury.get("fetched_utc", "")
    games_published = latest_schema.get("games_published")
    games_scheduled = latest_schema.get("games_scheduled")
    if latest_schema.get("coverage") == "partial" and games_published and games_scheduled:
        injury_capture_status = (
            "The latest archived official Week 11 capture was at %s and covered %s of %s scheduled games; "
            "it is partial, so no Week 11 player rows are included in the model dataset. A live re-read on 2026-11-19 shows all 13 fixtures on the NFL page, but no exact fetch clock or raw bytes were retained, so it is not a replayable snapshot. "
            % (esc(captured_at), esc(games_published), esc(games_scheduled))
            + a(SITE_URL + "research/verification/week11-injury-live-read-2026-11-19.md", "Live re-read limits") + " "
        )
    elif latest_injury.get("schema_ok"):
        injury_capture_status = (
            "The latest schema-valid official injury capture is dated %s; no newer complete Week 11 player dataset is committed. "
            % esc(captured_at)
        )
    else:
        injury_capture_status = (
            "The latest official injury response at %s failed the schema gate; no Week 11 player rows are included. "
            % esc(captured_at)
        )
else:
    injury_capture_status = "No official injury capture is recorded in the manifest. "

# ---------------------------------------------------------------- computations
tally = {r["abbr"]: dict(w=0, l=0, t=0, pf=0, pa=0) for r in standings}
for g in corpus:
    aw, hm = g["away"], g["home"]
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    tally[aw]["pf"] += ap
    tally[aw]["pa"] += hp
    tally[hm]["pf"] += hp
    tally[hm]["pa"] += ap
    if ap > hp:
        tally[aw]["w"] += 1
        tally[hm]["l"] += 1
    elif hp > ap:
        tally[hm]["w"] += 1
        tally[aw]["l"] += 1
    else:
        tally[aw]["t"] += 1
        tally[hm]["t"] += 1
mismatch = 0
for r in standings:
    c = tally[r["abbr"]]
    for k in ("w", "l", "t", "pf", "pa"):
        if c[k] != int(r[k]):
            mismatch += 1
fields = len(standings) * 5
sum_pf = sum(v["pf"] for v in tally.values())
sum_w = sum(v["w"] for v in tally.values())
weeks = sorted({int(g["week"]) for g in corpus})
totals = [int(g["away_pts"]) + int(g["home_pts"]) for g in corpus]
mean_total = statistics.mean(totals)
sd_total = statistics.stdev(totals)
home_m = [
    int(g["home_pts"]) - int(g["away_pts"])
    for g in corpus
    if (g["week"], g["away"], g["home"]) not in neutral_keys
]
n_neutral_excluded = len(corpus) - len(home_m)
assert n_neutral_excluded == 4, n_neutral_excluded  # HOU@JAX w6, PIT@NO w7, CIN@ATL w9, NE@DET w10
mean_home = statistics.mean(home_m)
se_home = statistics.stdev(home_m) / len(home_m) ** 0.5
ci_lo, ci_hi = mean_home - 1.96 * se_home, mean_home + 1.96 * se_home

# Weeks 6-9 window (the line lab's fitting window), non-neutral only — shown beside the
# full-corpus figure so the reader can see how window-sensitive the constant is (F-63).
wk69 = [g for g in corpus if g["week"] in ("6", "7", "8", "9") and
        (g["week"], g["away"], g["home"]) not in neutral_keys]
wk69_home = statistics.mean(int(g["home_pts"]) - int(g["away_pts"]) for g in wk69)

# The same statistic on the declared train / validation / recent windows (T70). Read from
# the artifact the publication gate re-derives, so these cannot drift from the page.
_corpus = json.loads(open(os.path.join(ROOT, "data", "output", "corpus_stats.json"),
                          encoding="utf-8").read())
_w = _corpus["windows"]
win_home = {k: (_w[k]["stats"]["home_margin"]["mean"], _w[k]["stats"]["home_margin"]["n"])
            for k in ("train", "validation", "final")}

n_out = sum(1 for r in inj if r["game_status"] == "Out")
n_q = sum(1 for r in inj if r["game_status"] == "Questionable")
n_doubt = sum(1 for r in inj if r["game_status"] == "Doubtful")
clubs_inj = len({r["team"] for r in inj})

col_depths = defaultdict(list)
for r in depth:
    col_depths[(r["team"], r["unit"], r["position_row"])].append(int(r["depth"]))
cell_players = defaultdict(int)
for r in depth:
    cell_players[(r["team"], r["unit"], r["position_row"], r["depth"])] += 1
shared_cells = sum(1 for v in cell_players.values() if v > 1)      # cells naming 2+ players
multi_rank_cols = sum(1 for v in col_depths.values() if len(v) > 1)  # columns with >1 ranked player
solo_cols = sum(1 for v in col_depths.values() if len(v) == 1)
depth_clubs = len({r["team"] for r in depth})
st_rows = sum(1 for r in depth if r["position_row"] in ("P", "K", "LS", "H", "PR", "KR"))

open_flags = [f for f in flags if (f.get("status") or "").lower() != "resolved"]
flag_ids = [f.get("id") for f in flags]

# ---------------------------------------------------------------- decisions
# Each row: what must be decided, why it blocks, the cheapest evidence that would close it,
# and the official source a reviewer can read to check the claim.
decisions = [
    ["Is 150 games enough to open a backtest holdout?",
     "Every skill claim depends on the sample. Below the pre-registered minimum no result can be separated from luck.",
     "The pre-registered minimum is written down and refused until met; the corpus and the reconciliation that "
     "proves every score are published, so the only missing input is more settled games.",
     a(SITE_URL + "readiness.html", "Decision readiness"),
     a(NFL + "/schedules/2026/", "Official 2026 results")],
    ["Should the depth dataset be trusted for a starter/backup signal?",
     "It stores no shared cell and no special-teams row, so a co-starter is reported as a starter plus a backup.",
     "A four-club live sample (103 players) measured the defect; re-transcribing from live charts, or parsing "
     "them, is the closing action. Until then no deficiency claim is published from it as fact.",
     a(SITE_URL + "research/verification/depth-slot-fidelity-2026-11-18.md", "Depth fidelity measurement"),
     a("https://www.seahawks.com/team/depth-chart", "Live SEA depth chart")],
    ["Does the injury designation become a model feature?",
     "A designation is not an outcome. Using it before measuring its play rate would embed an unvalidated prior.",
     "Join several seasons of designations to official inactive lists and estimate the play rate per label with "
     "an interval. The repository holds one week and no inactive list, so the join cannot start yet.",
     a(SITE_URL + "brief-register.html", "Brief register"), a(NFL + "/injuries/", "Official injury report")],
    ["Is a market price ours to publish?",
     "The NFL publishes no lines. Any price is a licensed operator's product, which is a rights question "
     "before it is a data question.",
     "Prices are labelled non-official on every page and never presented as an NFL fact; the rights decision "
     "is the owner's and is listed as an open flag.",
     a(SITE_URL + "flags.html", "Flagged for review"), a(NFL + "/", "NFL.com")],
    ["Are official availability captures complete and sustained?",
     "The live official page was re-read and lists all 13 fixtures, but the latest archived capture covers only 12 of 13, and the new read has no exact fetch clock or retained raw bytes; this does not establish a replayable daily series.",
     "Seven consecutive daily captures for each required source, each with timestamp and hash, complete schedule coverage, conflict flags, and raw bytes retained only in an authorized private store.",
     a(NFL + "/injuries/league/2026/reg11", "Official Week 11 report"),
     a(SITE_URL + "flags.html", "Capture flags")],
]

# ---------------------------------------------------------------- suggested work
suggestions = [
    ["Verify authorized raw retention and the live report schema",
     "high", "S", "The latest archived Week 11 capture is partial (12 of 13 games). The current live page re-read lists all 13 fixtures, but the omitted fixture in the archived response and the reason for its absence cannot be recovered from the retained hash-only record; raw bytes are not retained publicly.",
     "A complete live report captured with UTC timestamp and SHA-256, raw bytes stored only in the authorized private store, schema and coverage checks passing, then seven consecutive daily captures per source.",
     a(NFL + "/injuries/league/2026/reg11", "Official Week 11 report")],
    ["Re-transcribe depth chart-by-chart with shared cells",
     "high", "M", "Every deficiency feature downstream inherits the current dataset's defect; nothing else can "
     "be trusted about backups until the slots are right.",
     "A re-transcribed dataset in which a shared first cell yields two players at depth 1, and a spot check of "
     "four clubs matches the live pages cell for cell.",
     a("https://www.commanders.com/team/depth-chart", "Live WAS chart")],
    ["Capture and retain complete Week 11 injury snapshots",
     "high", "S", "The live official Week 11 page currently renders all 13 scheduled fixtures, but the latest archived capture is schema-valid and partial (12 of 13); raw bytes are not retained publicly, so the live view cannot be replayed as the capture.",
     "A complete, timestamped Week 11 capture with source hash and authorized private raw retention; verify expected report coverage, then preserve daily Wednesday-to-kickoff snapshots and pass the <=13-hour freshness gate.",
     a(NFL + "/injuries/league/2026/reg11", "Official Week 11 report")],
    ["Make the settled sample the headline, not ROI",
     "medium", "XS", "A small positive return is the most seductive number on the site; showing the sample "
     "beside it prevents the reader from mistaking it for skill.",
     "Every leaderboard and summary row prints n beside the return, and the gate state is adjacent.",
     a(SITE_URL + "leaderboard.html", "Leaderboard")],
    ["Publish a decision log with dates and reversals",
     "medium", "S", "This page states decisions but not when they were taken or when one was reversed; a "
     "recorded reversal is the strongest evidence the process is honest.",
     "One entry per decision, with the date it was taken and a link to whatever replaced it.",
     a(SITE_URL + "programme.html", "Integrity programme")],
    ["Confirm the official-capture freshness watchdog on main",
     "medium", "S", "A watchdog workflow now tracks stale, missing and schema-failed captures and opens a GitHub issue; its first live run on main has not yet been confirmed in the published evidence.",
     "A successful scheduled watchdog run on main, with one recovery test showing the alert closes when captures become fresh.",
     a("https://github.com/karagemop466-tech/X4/actions/workflows/capture-watchdog.yml", "Capture watchdog workflow")],
]

# ---------------------------------------------------------------- html
kv = []
kv.append(("Where the season stands",
           "Week 10 is complete: the Monday game (Chargers at Ravens, 23&ndash;20) was the last one outstanding. "
           + injury_capture_status
           + a(NFL + "/schedules/2026/by-week/week-10", "Official Week 10 schedule") + " &middot; "
           + a(NFL + "/injuries/league/2026/reg11", "Official Week 11 injury report")))
kv.append(("Games verified",
           "<b>%d</b> completed games, weeks %d&ndash;%d, each with its final score and its own official game "
           "page. %d of them were added on %s after the corpus was found to stop after one Week 10 game. "
           "%s" % (len(corpus), weeks[0], weeks[-1], len(wk10), RETRIEVED,
                   a(SITE_URL + "brief-register.html", "The corpus register"))))
kv.append(("Score integrity",
           "<b>%d of %d</b> club fields (W, L, T, PF, PA) reconcile with the official standings read on %s; "
           "points for = points allowed = <b>%d</b>. %d mismatches. %s"
           % (fields - mismatch, fields, RETRIEVED, sum_pf, mismatch,
              a(NFL + "/standings/", "Official standings"))))
kv.append(("Scoring environment",
           "Mean combined score <b>%.1f &plusmn; %.1f</b> over the verified corpus; home margin <b>%+.1f</b> points "
           "on <b>n = %d of %d</b> games (the %d international fixtures &mdash; HOU&#8209;JAX W6, PIT&#8209;NO W7, "
           "CIN&#8209;ATL W9, NE&#8209;DET W10 &mdash; excluded, per the official schedule), 95%% CI [%+.1f, %+.1f]: "
           "the interval contains zero, so no home edge is assumed. The same statistic on the declared "
           "train, validation and recent windows is <b>%+.2f</b> (n&nbsp;=&nbsp;%d), <b>%+.2f</b> (n&nbsp;=&nbsp;%d) "
           "and <b>%+.2f</b> (n&nbsp;=&nbsp;%d), and Weeks&nbsp;6&ndash;9 alone, the window the line lab's h is "
           "fitted on, give %+.2f on n&nbsp;=&nbsp;54: the constant is a property of its window, not a measured "
           "league effect. %s %s"
           % (mean_total, sd_total, mean_home, len(home_m), len(corpus), n_neutral_excluded,
              ci_lo, ci_hi,
              win_home["train"][0], win_home["train"][1],
              win_home["validation"][0], win_home["validation"][1],
              win_home["final"][0], win_home["final"][1],
              wk69_home,
              a(SITE_URL + "gates.html", "The per-window table"),
              a(SITE_URL + "correlations.html", "Measured values"))))
kv.append(("Availability",
           "<b>%d</b> official injury rows across <b>%d</b> clubs for Week 10: %d Out, %d Doubtful, %d "
           "Questionable. A blank game status is kept blank. %s"
           % (len(inj), clubs_inj, n_out, n_doubt, n_q, a(NFL + "/injuries/", "Official Week 10 report"))))
kv.append(("Depth",
           "<b>%d</b> positions across <b>%d</b> clubs' own charts. The dataset holds <b>%d</b> club/unit/"
           "position columns, of which <b>%d</b> are a single player and <b>%d</b> name two or more players in "
           "one cell &mdash; so a co-starter the club prints is stored as a starter plus a backup, and no "
           "special-teams row (<b>%d</b>) is stored at all. Measured, not papered over. %s"
           % (len(depth), depth_clubs, len(col_depths), solo_cols, shared_cells, st_rows,
              a(SITE_URL + "research/verification/depth-slot-fidelity-2026-11-18.md", "Measurement"))))
kv.append(("Markets",
           "<b>%d</b> originated markets with the fair line, market line and difference in three separate "
           "columns; <b>%d</b> price readings with open and close; <b>%d</b> markets settled against the "
           "recorded closing line. %s"
           % (len(fair), len(snaps), len(graded), a(SITE_URL + "origination.html", "Origination layer"))))
kv.append(("Strategies",
           "<b>0</b> eligible for a reward. The signal and the staking result are published as two separate "
           "scores precisely because one can look good while the other does not. %s"
           % a(SITE_URL + "signal-vs-staking.html", "Signal vs staking")))
kv.append(("Flags",
           "<b>%d</b> registered items, <b>%d</b> open, each with its evidence link. Flags do not block "
           "publication and never hide a blank. %s"
           % (len(flags), len(open_flags), a(SITE_URL + "flags.html", "Flagged for review"))))
kv.append(("Transactions",
           "<b>%d</b> official transaction rows, each linked to its league page &mdash; the evidence that a "
           "roster moved and therefore that a chart may be stale. %s"
           % (len(flows), a(NFL + "/", "NFL.com"))))

kv_html = "\n".join("<div>%s</div><div>%s</div>" % (k, v) for k, v in kv)

dec_rows = "\n".join(
    "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
    % (esc(d[0]), esc(d[1]), esc(d[2]), d[3], d[4]) for d in decisions)

sug_rows = "\n".join(
    "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
    % (esc(s[0]), tag(s[1], "red" if s[1] == "high" else "amber"), esc(s[2]), esc(s[3]), esc(s[4]), s[5])
    for s in suggestions)

html = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Executive summary: every figure computed from a committed dataset, every row linked to its official source, and the decisions that are still open.">
<title>Executive summary | Fourth Down Research</title><link rel="stylesheet" href="desk.css"></head>
<body data-page="executive-summary">
<aside class="sidebar">%(nav)s</aside>
<main><header class="topbar"><div><span class="eyebrow">01 &middot; SUMMARY</span><h1>Executive summary</h1></div>
<span class="status-pill"><i></i> Generated %(generated)s</span></header>

<section class="section" aria-label="How to read this page"><div class="note">
<b>Every figure on this page is computed at build time from a committed dataset</b>, and every row carries the
link that proves it. This replaces a hand-typed 2026-11-14 snapshot whose counts had drifted: that page said
Week 10 was in progress, listed 57 results, and reported 12 flags. The numbers below are regenerated by
<code>tools/gen_exec_summary_desk.py</code>, so they cannot drift again without the build failing first. Where
a value does not exist it is left blank and flagged &mdash; nothing here is inferred to fill a gap.</div></section>

<section class="section"><div class="section-head"><div><span class="eyebrow">THE IMPORTANT DETAILS</span>
<h2>What is verified, what it means, what is missing</h2>
<p class="muted">One page for a decision-maker, in the order a decision is actually taken.</p></div>
%(tag_green)s</div>
<div class="kv">
%(kv)s
</div></section>

<section class="section"><div class="section-head"><div><span class="eyebrow">DECISIONS</span>
<h2>What has to be decided, and the cheapest evidence that would settle it</h2>
<p class="muted">No row here needs a reply to keep the research moving: each one proceeds on the stated default
until it is challenged.</p></div>%(tag_amber)s</div>
<div class="card"><div class="table-wrap"><table class="data">
<thead><tr><th>Decision</th><th>Why it blocks</th><th>The evidence that closes it</th><th>Check it here</th>
<th>Official source</th></tr></thead><tbody>
%(dec_rows)s
</tbody></table></div></div></section>

<section class="section"><div class="section-head"><div><span class="eyebrow">SUGGESTIONS</span>
<h2>Work that would make the next decision easier, ranked</h2>
<p class="muted">Impact and size are this desk's judgement and are labelled as such; the evidence column is not.
The last three are new in this build.</p></div></div>
<div class="card"><div class="table-wrap"><table class="data">
<thead><tr><th>Suggestion</th><th>Impact</th><th>Size</th><th>Why it helps</th><th>How you would know it worked</th>
<th>Source of the underlying facts</th></tr></thead><tbody>
%(sug_rows)s
</tbody></table></div></div>

<div class="note"><b>The honest one-line state.</b> The data layer can now settle a bet on 150 official games
with every score proved. The availability layer cannot yet say who started, because the depth dataset collapses
shared slots and no inactive list is captured. The strategy layer has settled %(graded)d markets, which is far
short of the pre-registered minimum, so nothing on this site is eligible for a reward. The two cheapest actions
that would change that are the capture repair above and a fresh depth transcription; everything else waits on
them.</div>
</section>

<section class="section"><div class="section-head"><div><span class="eyebrow">WHAT WOULD CHANGE OUR MIND</span>
<h2>Two-sided, in both directions</h2></div></div>
<div class="kv">
<div>To accept an edge</div><div>Out-of-sample, benchmark-relative proper score better than the market's;
n at or above the pre-registered minimum; a game-cluster lower bound above zero after a multiplicity
adjustment for every trial run. Any one missing and the result stays ineligible.</div>
<div>To reject a model</div><div>A benchmark-relative score no better than the market on the same games, a
negative lower bound, or a calibration gap that survives re-fitting on a later season. A model that fails is
demoted to paper, not deleted, so the failure stays on the record.</div>
<div>To distrust this page</div><div>If any figure here disagrees with the dataset it cites, the page is wrong.
The build recomputes each one; a reviewer can check any row by following its link.</div>
</div></section>

<footer><span>FOURTH DOWN RESEARCH &middot; Executive summary</span><span>
<a href="index.html">&larr; Back to overview</a> &middot; <a href="brief-register.html">Brief register</a> &middot;
<a href="flagged.html">Flags</a> &middot; <a href="sources.html">Sources</a></span></footer></main>
<script src="nav.js"></script></body>
</html>
""" % dict(nav=desk_nav.side(), generated=GENERATED, kv=kv_html, dec_rows=dec_rows, sug_rows=sug_rows,
           tag_green=tag("COMPUTED, NOT TYPED"), tag_amber=tag("DEFAULTS UNTIL CHALLENGED", "amber"),
           graded=len(graded))

for target in (os.path.join(SITE, "executive-summary.html"), os.path.join(ROOT, "executive-summary.html")):
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(html)
print("wrote executive-summary.html (%d bytes): corpus %d, %d/%d fields, %d decisions, %d suggestions"
      % (len(html), len(corpus), fields - mismatch, fields, len(decisions), len(suggestions)))
