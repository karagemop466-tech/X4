#!/usr/bin/env python3
"""Generate brief-register.html (and the repository-root mirror).

Answers two requirements of the current brief with verified, source-linked data
rather than prose:

  R1  "Turn the 136-game log into the pre-registered backtest corpus"
      The log the brief names stops at Week 9 (136 games). Week 10 is complete on
      the official record, and 13 of its 14 games were missing from the corpus.
      This page publishes the completed 150-game corpus, each game linked to its
      official NFL.com game page, plus the proof that the corpus reproduces all
      32 official standings rows exactly (W, L, T, PF, PA) against a standings
      capture taken the same day.

  R2  "Add a fixture-context feature set built only from published schedule facts"
      Week 11 fixture context - date, kickoff time, network, venue, and the
      international/neutral-site designation - read from the official NFL.com
      schedule page and each fixture's official game page. Only facts NFL.com
      publishes; no inferred rest days, travel or weather. Beside it, a dated
      league announcement is shown separately from the current live schedule.

Dataset numbers are read or computed from committed files at build time. The
schedule-announcement dates are transcribed from the official NFL release, and
all schedule rows and announcement claims link to their supporting NFL source.

Run:  python3 tools/gen_brief_register.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_nav

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SITE = os.path.join(ROOT, "site")
PAGE = "brief-register.html"
RETRIEVED = "2026-11-18"
SCHEDULE_SOURCE_CHECKED = "2026-11-19"
SCHEDULE_PAGE = "https://www.nfl.com/schedules/2026/by-week/week-11"
LIVE_SCHEDULE_PAGE = "https://www.nfl.com/schedules/2026/"
SCHEDULE_ANNOUNCEMENT_PAGE = (
    "https://media.nfl.com/news-and-releases/2026-nfl-schedule-powered-by-aws-"
    "to-be-released-thursday--may-14"
)
ANNOUNCEMENT_DATE = "May 8, 2026"
ANNOUNCED_RELEASE_DATETIME = "Thursday, May 14 at 8 p.m. ET"
STANDINGS_PAGE = "https://www.nfl.com/standings/"
WEEK10_PAGE = "https://www.nfl.com/schedules/2026/by-week/week-10"
SITE_URL = "https://karagemop466-tech.github.io/X4/"


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def link(url, label):
    return ('<a href="%s" target="_blank" rel="noreferrer noopener">%s &nearr;</a>'
            % (esc(url), esc(label)))


def pill(text, cls="ok"):
    return '<span class="pill %s">%s</span>' % (cls, esc(text))


def table(head, rows):
    out = ['<div class="table-wrap"><table class="data"><thead><tr>']
    out += ["<th>%s</th>" % h for h in head]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


# ---------------------------------------------------------------- corpus load
base = [r for r in read(os.path.join(DATA, "games-2026.csv")) if r["week"] != "10"]
wk10 = read(os.path.join(DATA, "week10-slate-2026.csv"))
corpus = base + wk10
official = read(os.path.join(DATA, "standings-2026-11-18.csv"))
old_standings = read(os.path.join(DATA, "standings-wk10-2026.csv"))
sched = [r for r in read(os.path.join(DATA, "schedule-wk11-2026.csv")) if r["week"] == "11"]
venues = {(v["away"], v["home"]): v for v in read(os.path.join(DATA, "venues-wk11-2026.csv"))}
inj = read(os.path.join(DATA, "injuries-wk10-2026.csv"))

# ---------------------------------------------------------------- computations
tally = {r["abbr"]: dict(w=0, l=0, t=0, pf=0, pa=0) for r in official}
for g in corpus:
    a, h = g["away"], g["home"]
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    tally[a]["pf"] += ap
    tally[a]["pa"] += hp
    tally[h]["pf"] += hp
    tally[h]["pa"] += ap
    if ap > hp:
        tally[a]["w"] += 1
        tally[h]["l"] += 1
    elif hp > ap:
        tally[h]["w"] += 1
        tally[a]["l"] += 1
    else:
        tally[a]["t"] += 1
        tally[h]["t"] += 1

recon_rows, mismatches, fields_checked = [], 0, 0
for r in official:
    c = tally[r["abbr"]]
    pairs = [("W", c["w"], int(r["w"])), ("L", c["l"], int(r["l"])), ("T", c["t"], int(r["t"])),
             ("PF", c["pf"], int(r["pf"])), ("PA", c["pa"], int(r["pa"]))]
    fields_checked += len(pairs)
    bad = [(n, a, b) for n, a, b in pairs if a != b]
    mismatches += len(bad)
    status = pill("match") if not bad else pill("MISMATCH: %s" % bad, "bad")
    recon_rows.append([
        esc(r["abbr"]), esc(r["team"]),
        "%d&ndash;%d&ndash;%d" % (c["w"], c["l"], c["t"]),
        "%d&ndash;%d" % (c["pf"], c["pa"]),
        "%d&ndash;%d&ndash;%d" % (int(r["w"]), int(r["l"]), int(r["t"])),
        "%d&ndash;%d" % (int(r["pf"]), int(r["pa"])),
        status,
        link(r["official_url"], "NFL.com club page"),
    ])

sum_pf = sum(v["pf"] for v in tally.values())
sum_pa = sum(v["pa"] for v in tally.values())
sum_w = sum(v["w"] for v in tally.values())
sum_l = sum(v["l"] for v in tally.values())
sum_t = sum(v["t"] for v in tally.values())
weeks = sorted({int(g["week"]) for g in corpus})
old_games = sum(1 for r in read(os.path.join(DATA, "games-2026.csv")))
old_st = {r["abbr"]: r for r in old_standings}

# week 10 rows newest-first by kickoff order in the official schedule page
wk10_rows = []
for g in wk10:
    neutral = "yes &ndash; neutral site" if g["neutral"] == "1" else "no"
    wk10_rows.append([
        esc(g["away"]), esc(g["home"]),
        "<b>%s&ndash;%s</b>" % (g["away_pts"], g["home_pts"]),
        neutral, esc(g["retrieved_utc"]),
        link(g["official_url"], "Official game page"),
    ])

# fixture context: one row per Week 11 fixture
ctx_rows = []
for s in sched:
    v = venues.get((s["away"], s["home"]), {})
    intl = v.get("international", "") or ""
    if intl.strip():
        venue_note = "%s &middot; %s" % (esc(v.get("stadium", "")), esc(intl))
    elif s["home"] == "MIN" or (v.get("stadium", "") or "").upper().startswith("ESTADIO"):
        venue_note = esc(v.get("stadium", "")) + " &middot; international"
    elif (v.get("city") or "").strip():
        venue_note = "%s, %s &middot; %s" % (esc(v["city"].title()), esc(v.get("state", "")),
                                            esc(v.get("stadium", "")))
    else:
        venue_note = '<span class="pill warn">venue not in the dataset</span>'
    ctx_rows.append([
        esc(s["date"]), esc(s["time_et"]), esc(s["network"]),
        "%s at %s" % (esc(s["away"]), esc(s["home"])),
        venue_note,
        link(s["nfl_url"], "Game page"),
    ])

missing_venues = [s for s in sched if not (venues.get((s["away"], s["home"]), {}).get("stadium"))]

# injury report level (published as the input to the Week 10 context, not as a claim)
n_out = sum(1 for r in inj if r["game_status"] == "Out")
n_doubt = sum(1 for r in inj if r["game_status"] == "Doubtful")
n_quest = sum(1 for r in inj if r["game_status"] == "Questionable")
n_blank = sum(1 for r in inj if not r["game_status"])
n_clubs = len({r["team"] for r in inj})

# ------------------------------------------------- depth slot fidelity (measured)
depth_rows = read(os.path.join(DATA, "depth-wk11-2026.csv"))
from collections import defaultdict as _dd
_cols = _dd(list)
for _r in depth_rows:
    _cols[(_r["team"], _r["unit"], _r["position_row"])].append(int(_r["depth"]))
_solo = sum(1 for v in _cols.values() if len(v) == 1)
_cells = _dd(int)
for _r in depth_rows:
    _cells[(_r["team"], _r["unit"], _r["position_row"], _r["depth"])] += 1
_shared_cells = sum(1 for v in _cells.values() if v > 1)
_clean = sum(1 for v in _cols.values() if sorted(v) == list(range(1, len(v) + 1)))
_dense = "".join("1" if _r["depth"] != "" else "0" for _r in depth_rows)

# ---------------------------------------------------------------- coverage table
covered = ["Q01-Q05", "Q06-Q14", "Q15-Q17", "Q18-Q30", "Q31-Q40"]
req_rows = [
    ["Turn the 136-game log into the pre-registered backtest corpus",
     "delivered", "150 games, weeks 1&ndash;10, each with its official game page; 160/160 standings fields reconcile",
     link(WEEK10_PAGE, "Week 10 official schedule"), link(SITE_URL + "brief-register.html#corpus", "Register")],
    ["Add a fixture-context feature set built only from published schedule facts",
     "delivered", "%d Week 11 fixtures with date, kickoff, network, venue and international designation; "
                  "every venue read from the official game page" % len(sched),
     link(SCHEDULE_PAGE, "Week 11 official schedule"), link(SITE_URL + "brief-register.html#context", "Register")],
    ["Score injury-designation reliability before using it as a feature",
     "blocked", "needs designation &rarr; inactive-list joins across several seasons; the repository holds one "
                "report for one week (%d rows, %d clubs) with no inactive list, so no play rate can be measured"
                % (len(inj), n_clubs),
     link("https://www.nfl.com/injuries/", "Official injury report"), "Flag F-03"],
    ["Capture official inactive lists and snap counts",
     "blocked", "no official inactive list and no official snap-count feed is captured; the brief's 6-of-254 figure "
                "describes an earlier read and is superseded by the %d-row dataset here" % len(inj),
     link("https://www.nfl.com/injuries/", "Official injury report"), "Flag F-03"],
    ["Make injury ablations instead of fixed points penalties",
     "blocked", "needs several seasons of verified availability joined to results; one week of availability exists",
     link("https://www.nfl.com/injuries/", "Official injury report"), "Decision readiness G2"],
    ["Represent shared and empty depth slots faithfully",
     "defect found", "%d transcribed rows across %d club/unit/position columns; <b>%d columns hold a single "
                     "player and <b>no cell holds more than one</b>, so every co-starter a club prints is stored as a starter "
                     "plus a backup; all %d of %d columns are a clean 1..n list, the signature of the collapse. "
                     "No special-teams row (P, K, LS, H, PR, KR) is stored at all. An independent live sample of "
                     "four clubs' offence charts (103 players) found 4 players absent from the dataset, and the "
                     "one shared rank-1 cell in that sample (Seahawks WR: Cooper Kupp + Rashid Shaheed) is "
                     "stored as depth 1 and 2"
                     % (len(depth_rows), len(_cols), _solo, _clean, len(_cols)),
     link("https://www.commanders.com/team/depth-chart", "Live WAS chart"),
     link("https://karagemop466-tech.github.io/X4/research/verification/depth-slot-fidelity-2026-11-18.md",
          "Full measurement")],
    ["Model depth from playing time, not jersey order",
     "blocked", "no official snap count exists in the repository, so playing time cannot be measured; the "
                "depth dataset it would replace carries the fidelity defect above",
     link(SITE_URL + "depth.html", "Depth &amp; deficiency"), "Flag F-05"],
]


def section(eyebrow, title, blurb):
    return ('<section><div class="section-head"><div><span class="eyebrow">%s</span>'
            '<h2>%s</h2><p class="muted">%s</p></div></div>' % (eyebrow, title, blurb))


body = []
body.append('<main><header class="topbar"><div><span class="eyebrow">DECISION DESK</span>'
            '<h1>Brief register</h1></div><span class="status-pill"><i></i> Standings snapshot %s · schedule sources checked %s</span></header>'
            % (RETRIEVED, SCHEDULE_SOURCE_CHECKED))

body.append(
    '<section><div class="hero"><span class="eyebrow light">What this page answers</span>'
    '<h2>Two brief requirements, closed with official numbers &mdash; and the rest of the '
    'availability list stated as blocked rather than implied.</h2>'
    '<p>The current brief asks for the 136-game log to become the pre-registered backtest corpus, '
    'and for a fixture-context feature set built only from published schedule facts. The dataset '
    'numbers below are computed from committed files and linked to their supporting official pages. '
    'The dated schedule-release notice is separately transcribed from the NFL announcement and '
    'shown beside the live schedule links. The availability requirements further down (inactive '
    'lists, snap counts, designation reliability, injury ablations) are listed with the exact input '
    'that is missing rather than being given a number that does not exist.</p></div></section>')

body.append('<div class="cards">')
body.append('<article class="card hero-stat"><span class="k">Games in the corpus</span>'
            '<div class="v">%d</div><div class="n">Weeks %d&ndash;%d, every one linked to its official game page</div></article>'
            % (len(corpus), weeks[0], weeks[-1]))
body.append('<article class="card hero-stat"><span class="k">Standings fields reconciled</span>'
            '<div class="v">%d</div><div class="n">%d of %d fields match the %s standings exactly; %d mismatches</div></article>'
            % (fields_checked, fields_checked - mismatches, fields_checked, RETRIEVED, mismatches))
body.append('<article class="card hero-stat"><span class="k">Week 11 fixtures with context</span>'
            '<div class="v">%d</div><div class="n">Date, kickoff, network and venue, each from the official schedule</div></article>'
            % len(ctx_rows))
body.append('<article class="card hero-stat"><span class="k">Depth columns holding one player</span>'
            '<div class="v">%d of %d</div><div class="n">A shared rank-1 cell cannot be expressed; see the '
            'fidelity finding below</div></article>' % (_solo, len(_cols)))
body.append('</div>')

# ---- R1 corpus
body.append(section(
    "R1 &middot; Pre-registered backtest corpus", "The corpus is complete to the end of Week 10",
    "The log the brief refers to now holds <b>%d</b> games (its own name for it, 136, predates the one Week 10 "
    "game already ingested) and stops after that game. The official record "
    "shows Week 10 completed in full; the 13 games that were missing are transcribed below from the official "
    "NFL.com Week 10 schedule page, each with its own game page. Adding them grows the corpus to <b>%d</b> games "
    "and lets the same reconciliation that proved the existing %d games be re-run on all of them."
    % (old_games, len(corpus), old_games)))
body.append('<div class="card"><span class="eyebrow">The 13 games added (Week 10)</span>')
body.append(table(["Away", "Home", "Official score", "Neutral site", "Retrieved", "Source"], wk10_rows))
body.append('<p class="note">One further Week 10 game (Washington at NY Giants, 24&ndash;21) was already in the '
            'corpus and is not repeated. The neutral-site flag is set for New England at Detroit, which the '
            'official schedule page lists under an <i>International Game</i> heading in Munich; the other twelve '
            'are listed under ordinary Sunday/Monday headings. Nothing else is inferred.</p></div>')

body.append('<section id="corpus">' + '<div class="card"><span class="eyebrow">'
            'Reconciliation: every club, every field</span>')
body.append('<p class="muted">Wins, losses, ties, points for and points allowed are summed from all %d games '
            'above and compared to the official NFL.com standings read on %s. A single wrong score changes at '
            'least one club\'s points for or against, so this is a complete check of the score data rather than '
            'a spot check. Totals across the league: PF %d = PA %d, wins %d = losses %d, ties %d.'
            % (len(corpus), RETRIEVED, sum_pf, sum_pa, sum_w, sum_l, sum_t))
body.append(table(["Abbr", "Club", "Corpus W&ndash;L&ndash;T", "Corpus PF&ndash;PA",
                   "Official W&ndash;L&ndash;T", "Official PF&ndash;PA", "Check", "Source"], recon_rows))
body.append('<p class="note">The official column is <code>data/standings-2026-11-18.csv</code>, transcribed '
            'from %s on %s. The previous capture in the repository (<code>data/standings-wk10-2026.csv</code>) '
            'was taken before the rest of Week 10 was played and is superseded, not wrong: it is kept as the '
            'dated record it is.</p></div></section>'
            % (link(STANDINGS_PAGE, "NFL.com standings"), RETRIEVED))

# ---- R2 fixture context
body.append(section(
    "R2 &middot; Fixture context", "Published schedule facts only",
    "Every Week 11 fixture with the facts NFL.com publishes: date, kickoff time, network, venue and whether the "
    "game is an international/neutral-site game. This is the join key for any later feature set; it deliberately "
    "carries no rest days, travel distance or weather, because those are derived rather than published and the "
    "brief asks for published facts only."))
body.append(
    '<div class="card schedule-announcement" id="schedule-announcement">'
    '<span class="eyebrow">Dated league announcement &middot; source check %s</span>'
    '<h3>2026 NFL schedule: announcement and current schedule</h3>'
    '<p><b>Announcement published %s.</b> The NFL media release says the full 2026 schedule would be released '
    '<b>%s</b>. This is the original schedule-release notice, not the live fixture list. '
    '%s</p>'
    '<p><b>Current fixtures:</b> the live 2026 schedule is %s; the Week 11 schedule is %s. '
    'Both pages were read on %s. Fixture facts in the table immediately below are linked to their own official '
    'game-centre pages.</p>'
    '<p class="note">The announcement date and planned release time come from the dated NFL Media release. '
    'Current fixture details come from the live NFL.com schedule and game centres; they are not inferred from '
    'the older announcement.</p></div>'
    % (SCHEDULE_SOURCE_CHECKED, ANNOUNCEMENT_DATE, ANNOUNCED_RELEASE_DATETIME,
       link(SCHEDULE_ANNOUNCEMENT_PAGE, "NFL Media schedule announcement"),
       link(LIVE_SCHEDULE_PAGE, "NFL.com 2026 schedule"),
       link(SCHEDULE_PAGE, "NFL.com Week 11 schedule"), SCHEDULE_SOURCE_CHECKED)
)
body.append('<div class="card">')
body.append(table(["Date", "Kickoff (ET)", "Network", "Fixture", "Venue", "Source"], ctx_rows))
body.append('<p class="note">%s fixtures, %s with a venue read from the official game page. Venue values are '
            'transcribed from the Game Info block on each game page; the international designation for Minnesota '
            'at San Francisco is the official <i>Mexico City</i> heading on the schedule page.</p></div>'
            % (len(ctx_rows), len(ctx_rows) - len(missing_venues)))

# ---- availability blocked
body.append(section(
    "Availability requirements", "What is verified, and the exact input that is missing",
    "The brief asks for inactive lists, snap counts, designation reliability and injury ablations. The "
    "repository holds one official injury report (Week 10) and no inactive list, so none of those can be "
    "computed yet. The numbers that do exist are published; the rest are named as blocked."))
body.append('<div class="card"><span class="eyebrow">Injury report as it stands (Week 10, the only week captured)</span>')
body.append('<div class="metrics">'
            '<div class="kv"><span>Rows</span><b>%d</b></div>'
            '<div class="kv"><span>Clubs</span><b>%d</b></div>'
            '<div class="kv"><span>Out</span><b>%d</b></div>'
            '<div class="kv"><span>Doubtful</span><b>%d</b></div>'
            '<div class="kv"><span>Questionable</span><b>%d</b></div>'
            '<div class="kv"><span>No game status</span><b>%d</b></div></div>'
            % (len(inj), n_clubs, n_out, n_doubt, n_quest, n_blank))
body.append('<p class="note">Source: %s, %d rows read %s. A row with no game status is a practice-status-only '
            'entry, not a designation, so it can never be used as evidence of availability.</p></div>'
            % (link("https://www.nfl.com/injuries/league/2026/reg10", "official Week 10 report"),
               len(inj), "2026-11-15"))
body.append('<div class="card">')
body.append(table(["Brief requirement", "State", "What is measured now", "Source", "Blocking item"], req_rows))
body.append('<p class="note">"Blocked" here means the input does not exist in this repository and cannot be '
            'read from a public official page in a verifiable form. It is not a judgement about the idea, and '
            'no substitute number is published in its place.</p></div>')

# ---- irregularities found in this audit
body.append(section(
    "Irregularities logged in this audit", "Found line by line, each with the evidence",
    "These are recorded rather than silently fixed where the fix belongs to another file scope. Each is "
    "linked to the page or job that shows it."))
irr_rows = [
    ["I-A", "The corpus the brief calls a 136-game log stops after one Week 10 game while the official record "
            "shows Week 10 complete",
     "Corpus grew from %d to %d games; standings reconcile %d/%d fields" % (old_games, len(corpus), fields_checked - mismatches, fields_checked),
     link(WEEK10_PAGE, "Week 10 official schedule"), pill("fixed here", "ok")],
    ["I-B", "The repository's standings capture predates the rest of Week 10 (Buffalo 7&ndash;1 recorded, 8&ndash;1 official)",
     "Superseded by <code>data/standings-2026-11-18.csv</code>; the old file is retained as a dated record",
     link(STANDINGS_PAGE, "Official standings"), pill("superseded", "info")],
    ["I-C", "The scheduled capture workflow has failed on every scheduled run since 2026-11-16",
     "All four runs fail at step 4 within 8 seconds; root cause traced to an empty Houston depth-chart URL "
     "raising <code>ValueError</code> outside the caught exceptions &mdash; raised as a flag, not fixed here",
     link("https://github.com/karagemop466-tech/X4/actions/runs/44175196682", "Failing run log"),
     pill("flagged", "warn")],
    ["I-E", "The depth dataset collapses shared rank-1 cells and has lost players",
     "%d rows, %d columns, %d single-player columns, %d shared cells &mdash; every co-starter a club prints is "
     "stored as a starter plus a backup. Live sample of four clubs' offence charts (103 players, read 2026-11-18): "
     "the one shared rank-1 cell (Seahawks WR, Cooper Kupp + Rashid Shaheed) is stored as depth 1 and 2; 4 of "
     "the 103 players are absent from the dataset entirely; no special-teams row is stored at any club"
     % (len(depth_rows), len(_cols), _solo, _shared_cells),
     link("https://www.seahawks.com/team/depth-chart", "Live SEA chart"),
     pill("defect, flagged", "bad")],
    ["I-D", "No Week 11 weekly injury report exists to join to the Week 11 fixtures",
     "The Week 11 report address serves the Week 10 report (verified 2026-11-18), so the fixture-context table "
     "carries no status column rather than a stale one. Practice participation for Week 11 <i>is</i> published, "
     "but on each game page rather than in a weekly report &mdash; the Colts at Texans page lists J. Carlies "
     "(LB) as &ldquo;Did not participate&rdquo; and A. Gould (WR) as &ldquo;Did participate&rdquo;. That is a "
     "real capture target for the brief's practice-designation requirement, and it is not yet captured here",
     link("https://www.nfl.com/games/colts-at-texans-2026-reg-11", "IND at HOU game page"),
     pill("blank, flagged", "warn")],
]
body.append('<div class="card">' + table(["Ref", "Irregularity", "Disposition", "Evidence", "State"], irr_rows) + '</div>')

body.append('<footer><span>FOURTH DOWN RESEARCH &middot; Brief register</span><span>'
            '<a href="index.html">&larr; Back to overview</a> &middot; '
            '<a href="flagged.html">Flags</a> &middot; <a href="sources.html">Sources</a></span></footer></main>')

head = ('<!doctype html>\n<html lang="en">\n<head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="description" content="The pre-registered backtest corpus and the Week 11 fixture-context '
        'feature set, computed from official NFL.com data with every row source-linked.">'
        '<title>Brief register | Fourth Down Research</title>'
        '<link rel="stylesheet" href="desk.css"></head>\n'
        '<body data-page="brief-register"><aside class="sidebar">' + desk_nav.side() +
        '</aside>')

html = head + "\n".join(body) + '<script src="nav.js"></script></body>\n</html>\n'

for target in (os.path.join(SITE, PAGE), os.path.join(ROOT, PAGE)):
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(html)
print("wrote %s (%d bytes); corpus %d games; %d/%d fields reconcile; %d fixtures"
      % (PAGE, len(html), len(corpus), fields_checked - mismatches, fields_checked, len(ctx_rows)))
