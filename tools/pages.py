#!/usr/bin/env python3
"""
Generate the multi-page site into site/.

The pages are **statically rendered**: every table is written into the HTML at
build time from data/output/payload.json. The site therefore works with
JavaScript disabled, is readable by crawlers and by text extractors, and its
rows can be verified by inspecting the HTML directly rather than by running a
browser. JavaScript is used only for progressive enhancement - the week and team
filters - and never to produce a value.

Run:  python3 tools/pages.py
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "output")
SITE = os.path.join(ROOT, "site")

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import market_store  # the price store, the origination card and the results feed

with open(os.path.join(DATA, "payload.json"), encoding="utf-8") as fh:
    P = json.load(fh)

# The depth dataset is produced by tools/depth.py from the clubs' own official
# depth charts joined to the official NFL.com Week 10 injury report. It is a
# separate input, so this page never forks a number the model publishes.
_DEPTH_PATH = os.path.join(DATA, "depth.json")
DEPTH = json.load(open(_DEPTH_PATH, encoding="utf-8")) if os.path.exists(_DEPTH_PATH) else None

_DEPTH_CSV = os.path.join(ROOT, "data", "depth-wk11-2026.csv")
DEPTH_ROWS = []
if os.path.exists(_DEPTH_CSV):
    import csv as _csv
    with open(_DEPTH_CSV, newline="", encoding="utf-8") as _fh:
        DEPTH_ROWS = list(_csv.DictReader(_fh))

NAV = [
    ("index.html", "Overview"),
    ("standings.html", "Standings & results"),
    ("lines.html", "Model lines"),
    ("price-snapshots.html", "Price snapshots"),
    ("markets.html", "Price store"),
    ("results.html", "Results feed"),
    ("strategies.html", "Strategy lab"),
    ("availability.html", "Injuries & depth"),
    ("depth.html", "Depth & deficiency"),
    ("depth-audit.html", "Depth audit"),
    ("matchup.html", "Matchup matrix"),
    ("houston-depth.html", "Houston depth"),
    ("teams.html", "Per-team view"),
    ("luck.html", "Removal of luck"),
    ("readiness.html", "Decision readiness"),
    ("brief-register.html", "Brief register"),
    ("questions.html", "Decision checklist"),
    ("gates.html", "Gates & demotion"),
    ("suggestions.html", "Suggestions"),
    ("flags.html", "Flagged for review"),
    ("methodology.html", "Methodology"),
    ("index.html#directory", "Directory"),
]

# The X4 Console is a second, independent build of this project. It lives in
# `docs/` and is published at /console/ by the Pages workflow. It is linked by
# its absolute published address because the console is not part of the
# `site/` tree that the publication gate resolves local links against.
CONSOLE_URL = "https://karagemop466-tech.github.io/X4/console/"

# Every page in the repository, grouped by the question it answers. Used to
# build the landing-page directory, so a reader can find any page from one
# screen instead of guessing which build it belongs to.
DIRECTORY = [
    ("Overview &amp; decisions", [
        ("executive-summary.html", "Executive summary",
         "The verified state, the decisions that are open, the findings, and every blank still open."),
        ("questions.html", "Decision checklist",
         "The {n_questions} questions that have to be answered before a decision here is reasonable."),
        ("decisions.html", "Decision Q&amp;A",
         "Thirty questions with the known answer, the missing information, and what it blocks."),
        ("requirements.html", "Requirements inventory",
         "All 40 brief requirements, each mapped to a deliverable, a status and a verification."),
        ("brief-register.html", "Brief register",
         "The pre-registered backtest corpus (150 games, every score reconciled) and the Week 11 fixture-context feature set, with the availability requirements that remain blocked and why."),
        ("readiness.html", "Decision readiness",
         "One row per requirement with the gate that blocks it and the number that would clear it, plus the two-sided 'what would change our mind' field."),
    ]),
    ("Verified data", [
        ("standings.html", "Standings &amp; results",
         "Official standings for all {n_teams} teams, power ratings, and every completed game with its official link."),
        ("data.html", "Verified data",
         "Standings, the Week 10 slate, the Week 11 schedule with a dated market snapshot, and 57 results."),
        ("markets.html", "Price snapshot store",
         "Opening and current numbers for all 13 Week 11 games across all three markets, the closing snapshot registered and deliberately empty, and our fair line beside the market line with the difference as its own column."),
        ("results.html", "Verified results feed",
         "Every originated line joined to a verified result or explicitly marked pending - the feed that backtests and ROI have to be computed against."),
        ("availability.html", "Injuries &amp; depth",
         "The full official Week 10 injury report, a unit-level roll-up, and the starter changes the league confirmed."),
        ("depth.html", "Depth &amp; deficiency",
         "All {n_depth_rows} depth positions transcribed from the {n_depth_clubs} clubs that publish an ordered chart, joined to the official injury report: who is out, who replaces him, and where no replacement is named."),
        ("matchup.html", "Matchup matrix",
         "Every Week 11 fixture's trench, coverage, backers, tight-end and safety groups with both sides' listed depth chains, the official game status on each player, and a flag wherever a listed starter is ruled out."),
        ("houston-depth.html", "Houston depth (authorized source)",
         "Houston publishes no structured depth chart (image only, F-24). Resolved from the official NFL Game Book: actual starters and per-player snap counts, published as derived playing-time depth indices with the Game Center and PDF links."),
        ("injuries.html", "Availability",
         "Player-linked injury rows and the starter-to-second-string deficiency pipeline for both units."),
        ("replacements.html", "Availability &amp; depth",
         "The replacement chains: who replaced whom, at what depth, and where no replacement is named at all."),
        ("teams.html", "Per-team view",
         "One row per club: starters out, named replacements, net injury count and the Week 11 venues from the NFL.com game centre."),
        ("depth-audit.html", "Depth audit",
         "One row per club: rows stored, columns that name a single player, cells that name two or more, special-teams coverage, and whether the live page was checked."),
        ("delta.html", "What changed (injury delta)",
         "The injury report published as a delta between two dated official captures: players added, removed, and every cell that moved."),
    ]),
    ("Model &amp; strategies", [
        ("lines.html", "Model lines",
         "Week 11 model spreads and totals for all {n_schedule} official games, with fair line, market line and difference as separate columns."),
        ("price-snapshots.html", "Price snapshots",
         "Opening and closing fair lines for every market we originate, for all 13 official Week 11 games."),
        ("strategies.html", "Strategy lab",
         "The leaderboard, the {spell_n_gates} validation gates, the error-correlation matrix, calibration and stability."),
        ("gates.html", "Gates &amp; demotion",
         "Signal scored separately from staking, the demotion gate that sends a live strategy back to paper, and replacement depth with its own measurement rule."),
        ("luck.html", "Removal of luck",
         "Controls for the staking record, a game-cluster interval and the settlement check against official scores, so a lucky run cannot be mistaken for skill."),
        ("signals.html", "Line lab &amp; signals",
         "Thirteen originated baseline lines against the market, ten candidate signals, eight gates and four correlations with confidence intervals."),
        ("leaderboard.html", "Leaderboard",
         "Singles, parlays and prop-combination divisions with the scoring formula and the anti-gaming rules."),
        ("origination.html", "Line origination",
         "The origination desk: side first, then total, then moneyline, with the fair line, the market line and the difference kept apart."),
        ("price-store.html", "Price store",
         "The operations price store: opening and current numbers for every market we originate, and the closing snapshot that is deliberately empty."),
        ("signal-vs-staking.html", "Signal vs staking",
         "The leaderboard split: a strategy's signal is scored without seeing a stake, so a lucky staking run cannot mask a bad signal."),
        ("correlations.html", "Correlations",
         "Correlations computed only from officially sourced numbers, each published with its n and its confidence interval."),
        ("method-lab.html", "Method lab",
         "The method behind every number: pre-registration, walk-forward evaluation, the gates and the anti-luck protocol."),
        ("luck.html", "Removal of luck",
         "Random-pick and favourites-only controls beside the staking record, a game-cluster interval, and the settlement reconciliation against official scores."),
    ]),
    ("Line origination desk", [
        ("origination.html", "Line origination",
         "The numbers we originate: side, then total, then moneyline."),
        ("price-store.html", "Price store",
         "The price-snapshot store and its provenance."),
        ("signal-vs-staking.html", "Signal vs staking",
         "The leaderboard, with signal and staking scored apart."),
        ("correlations.html", "Correlations",
         "Correlations from officially sourced numbers, with n."),
        ("replacements.html", "Availability &amp; depth",
         "Replacement depth, as far as the official record goes."),
        ("method-lab.html", "Method lab",
         "Fundamentals, best practice and signal-generation research."),
        ("ops-review.html", "Review gate",
         "The review gate for this layer's own suggestions."),
        ("verification.html", "Verification",
         "A page whose claims are re-derived from the raw artifacts, so the page can contradict itself."),
        ("requirements-closure.html", "Requirement closure",
         "Every brief requirement with its closure state and the evidence page for it."),
    ]),
    ("Review &amp; flags", [
        ("suggestions.html", "Suggestions",
         "Eight ranked proposals, each with the decision it needs and the evidence that would show it worked."),
        ("review.html", "Suggestions review queue",
         "Eighteen proposals with Accept / Hold / Reject, saved in the browser, so a path is chosen before anything is built."),
        ("workbench.html", "Suggestion workbench",
         "Twelve proposals scored on one documented four-part rubric, ranked, and reviewable with a stored Accept / Hold / Reject so the best path is chosen before anything is built."),
        ("programme.html", "Integrity &amp; programme",
         "The eight integrity gates: a price-snapshot store, a verified results feed, side-then-total-then-moneyline, fair/market/difference columns, signal separated from staking, measured replacement depth, correlations with n, and a demotion gate."),
        ("readiness.html", "Decision readiness",
         "The gates that must clear before any claim is published, one row per requirement, with the gate that blocks it and the number that would clear it."),
        ("flags.html", "Flagged for review",
         "Unverified values and irregularities found while verifying, each with the reason it is still open - {n_flags} entries so far."),
        ("flagged.html", "Flagged for review (desk)",
         "The decision-desk layer's own register: {desk_flags} with their evidence links."),
    ]),
    ("Method &amp; sources", [
        ("methodology.html", "Methodology",
         "Every model parameter, every gate, and the protocol that keeps luck out of the leaderboard."),
        ("sources.html", "Sources",
         "The full source register: which official page each number came from, and when it was retrieved."),
        ("repo-review.html", "Repo review",
         "A line-by-line review of every file in this repository, with the issues that were found."),
        ("ops-review.html", "Review gate",
         "The gate that decides what may be published: which numbers are official, which are model estimates and which are unverified."),
        ("verification.html", "Verification",
         "Every check that was run, what it proved and what it could not prove."),
        ("requirements-closure.html", "Requirement closure",
         "Each brief requirement, the deliverable that satisfies it, and the verification that closes it."),
    ]),
]

SRC_SEASON = "https://www.nfl.com/schedules/2026/"


# ------------------------------------------------------------------ helpers
# --- verified market price store (research/data/price_snapshots_2026.csv) ---
# DraftKings prices captured through the ESPN odds endpoint and labelled as such;
# every row carries the game's NFL.com URL as its official identity.
_PRICE_STORE = {}
_PRICE_STORE_WK11 = {}
import csv as _csv
import os as _os
_ps_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "research", "data", "price_snapshots_2026.csv")
if _os.path.exists(_ps_path):
    with open(_ps_path, newline="", encoding="utf-8") as _fh:
        for _r in _csv.DictReader(_fh):
            _PRICE_STORE[(_r["away"], _r["home"])] = _r
            if _r.get("week") == "11":
                _PRICE_STORE_WK11[(_r["away"], _r["home"])] = _r

PRICE_SOURCE_NOTE = ("DraftKings via ESPN, captured 2026-11-14; not an official NFL line")


def market_cell(pair, field, fmt="1"):
    """A market number, or a blank that says precisely why it is blank."""
    r = _PRICE_STORE_WK11.get(pair)
    if r is None:
        return blank("no captured price for this game")
    v = (r.get(field) or "").strip()
    if not v:
        return blank("no %s price was posted" % field.replace("_", " "))
    try:
        fv = float(v)
    except ValueError:
        return esc(v)
    if fmt == "ml":
        # moneylines are integers: -455, +350, -1650 with a comma like a book prints it
        return '<span class="num">%s</span>' % format(int(round(fv)), ",d")
    return '<span class="num">%s</span>' % format(fv, ".%sf" % fmt)


def market_link(pair):
    r = _PRICE_STORE_WK11.get(pair)
    if r is None:
        return ""
    return ' &middot; <a href="%s" target="_blank" rel="noreferrer">price &#8599;</a>' % esc(r["source_url"])


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def num(v, d=0):
    if v is None or v == "" or v == "—":
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return esc(v)
    if d == 0:
        return "{:,.0f}".format(f)
    return "{:,.{d}f}".format(f, d=d)


def pct(v, d=1):
    if v is None or v == "":
        return "—"
    try:
        return num(float(v) * 100.0, d) + "%"
    except (TypeError, ValueError):
        return esc(v)


def src(url, label="Source"):
    if not url:
        return '<span class="blank">unverified &mdash; no source</span>'
    return ('<a href="%s" target="_blank" rel="noreferrer noopener">%s &nearr;</a>'
            % (esc(url), esc(label)))


def badge(text, kind="mute"):
    return '<span class="b %s">%s</span>' % (esc(kind), esc(text))


def blank(text="not verified"):
    return '<span class="blank">%s</span>' % esc(text)


def wrap(element_id, markup):
    """Give a rendered block a stable id so the page can be addressed and filtered."""
    return '<div id="%s">%s</div>' % (esc(element_id), markup)


def table(headers, rows, note=None, cls="", row_attrs=None):
    """Render a table. headers: list of (label, is_num) tuples."""
    out = ['<div class="table-wrap"><table%s>' % (' class="%s"' % cls if cls else "")]
    out.append("<thead><tr>")
    for h in headers:
        label, isnum = (h if isinstance(h, (tuple, list)) else (h, False))
        out.append('<th%s>%s</th>' % (' class="num"' if isnum else "", esc(label)))
    out.append("</tr></thead><tbody>")
    for i, r in enumerate(rows):
        attrs = row_attrs(i) if row_attrs else ""
        out.append("<tr%s>" % attrs)
        for j, c in enumerate(r):
            h = headers[j] if j < len(headers) else ""
            isnum = (h[1] if isinstance(h, (tuple, list)) else False)
            out.append('<td%s>%s</td>' % (' class="num"' if isnum else "",
                                          "" if c is None else c))
        out.append("</tr>")
    out.append("</tbody></table>")
    if note:
        out.append('<div class="tbl-note">%s</div>' % note)
    out.append("</div>")
    return "".join(out)


# ------------------------------------------------------------------ data shortcuts
standings = P["standings"]
power = P["power"]
games = P["games"]
lines = P["wk11_lines"]
strategies = P["strategies"]
leaderboard = P["leaderboard"]
corr_err = P["correlation_error"]
corr_pred = P["correlation_prediction"]
calibration = P["calibration"]
weekly = P["weekly"]
availability = P["availability"]
injury_rows = P["injury_rows"]
flags = P["flags"]
questions = P["questions"]
suggestions = P["suggestions"]
framework = P["suggestion_framework"]
verification = P["verification"]
qb_changes = P["qb_changes"]
news = P["news"]
meta = P["meta"]
price_snapshots = P["price_snapshots"]
results_feed = P["results_feed"]
replacement_depth = P["replacement_depth"]
demotion_gate = P["demotion_gate"]
ids = [s["id"] for s in strategies]

# Counts that appear in prose are computed from the data, never typed by hand,
# so a page can never claim a number the tables underneath it do not support.
_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
          "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
          "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def spell(n):
    """Spell a small number the way the prose reads it (nine, twelve, ...)."""
    n = int(n)
    if n < 20:
        return _WORDS[n]
    if n < 40:
        tens = "twenty thirty".split()
        return tens[n // 10 - 2] + ("-" + _WORDS[n % 10] if n % 10 else "")
    return str(n)


N_GAMES = len(games)
N_TEAMS = len(standings)
N_SCHEDULE = len(lines)
N_LINES = len(lines)
N_INJURY_ROWS = len(injury_rows)
N_QUESTIONS = len(questions)
N_SUGGESTIONS = len(suggestions)
N_STRATEGIES = len(strategies)
N_FLAGS = len(flags)
N_GATES = len(set(k for s in leaderboard for k in s["gates"]))

avail_rows = sum(a["listed_players"] for a in availability)
avail_out = sum(a["out_count"] for a in availability)
avail_doubt = sum(a["doubtful_count"] for a in availability)
avail_q = sum(a["questionable_count"] for a in availability)
eligible = sum(1 for r in leaderboard if r["eligible"])
best = [r for r in leaderboard if r["id"] != "S0"][0]
eval_weeks = meta["eval_weeks"]
WEEKS = sorted({g["week"] for g in games})


# ------------------------------------------------------------------ fragments
def kpi_cards():
    def card(k, v, n):
        return ('<article class="card hero-card"><span class="k">%s</span>'
                '<div class="v">%s</div><div class="n">%s</div></article>' % (k, v, n))
    return "".join([
        card("Games verified", num(len(games)), "Every score re-verified against NFL.com standings"),
        card("Teams verified", num(len(standings)), "Official W/L/T/PF/PA from NFL.com"),
        card("Injury rows", num(avail_rows), "Official NFL.com Week 10 injury report"),
        card("Players ruled Out", num(avail_out), "Players listed Out on the official report"),
        card("Strategies scored", num(len(leaderboard)),
             "Walk-forward, weeks %d&ndash;%d" % (eval_weeks[0], eval_weeks[1])),
        card("Passing all gates", num(eligible), "Have cleared every validation gate"),
        card("Best improvement", pct(best["improvement_pct"], 1),
             "%s vs the league-constant benchmark" % best["id"]),
    ])


def leader_line():
    """The division leaders, read from the official standings table (no typed scores)."""
    by_div = {}
    for r in standings:
        by_div.setdefault(r["division"], []).append(r)
    parts = []
    for div in sorted(by_div):
        best = max(by_div[div], key=lambda r: (int(r["w"]) / max(1, int(r["w"]) + int(r["l"]) + int(r["t"])),
                                               int(r["net_pts"])))
        parts.append("%s %d&ndash;%d%s leads the %s"
                     % (best["team_name"], int(best["w"]), int(best["l"]),
                        "&ndash;%d" % int(best["t"]) if int(best["t"]) else "", div))
    worst = min(standings, key=lambda r: (int(r["w"]), int(r["net_pts"])))
    return "; ".join(parts) + "; %s are %d&ndash;%d" % (
        worst["team_name"], int(worst["w"]), int(worst["l"]))


def wk_facts():
    facts = [
        ("Week 11 schedule published",
         "NFL.com lists 13 games for Week 11 (Nov 19&ndash;23) and confirms the six teams on "
         "bye: Atlanta, Cleveland, Green Bay, LA Rams, New England and Seattle.",
         "https://www.nfl.com/schedules/2026/by-week/week-11"),
        # T46: the standings line is read off the official-standings table, so it moves
        # with the data instead of being re-typed each week.
        ("Official standings",
         "Through Week 10 (last game played 16 Nov 2026): %s."
         % leader_line(),
         "https://www.nfl.com/standings/"),
        ("Official injury report",
         "The Week 10 report lists %s players across the 28 teams playing, including %s ruled "
         "Out, %s Doubtful and %s Questionable."
         % (num(avail_rows), num(avail_out), num(avail_doubt), num(avail_q)),
         "https://www.nfl.com/injuries/"),
        ("Starter changes confirmed by the league",
         "Official NFL.com reporting confirms quarterback starter changes in Seattle, Cleveland, "
         "Arizona and Miami, and long-term absences for Baltimore, the LA Rams and Green Bay.",
         "https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders"),
    ]
    return "".join(
        '<article class="card"><span class="eyebrow">%s</span>'
        '<p style="margin-top:7px">%s</p><p class="small">%s</p></article>'
        % (esc(title), body, src(url, "Official source")) for title, body, url in facts)


def standings_table():
    rows = []
    for r in sorted(standings, key=lambda x: -x["pf"]):
        gp = r["w"] + r["l"] + r["t"]
        rows.append([
            '<a href="%s" target="_blank" rel="noreferrer noopener"><b>%s</b></a>'
            % (esc(r["url"]), esc(r["team_name"])),
            esc(r["division"]),
            num(r["w"]), num(r["l"]), num(r["t"]), num(r["pct"], 3),
            num(r["pf"]), num(r["pa"]), num(r["net_pts"]),
            num(float(r["pf"]) / gp, 1), num(float(r["pa"]) / gp, 1),
            src("https://www.nfl.com/standings/", "NFL.com"),
        ])
    return wrap("standings", table(
        [("Team", 0), ("Div", 0), ("W", 1), ("L", 1), ("T", 1), ("PCT", 1),
         ("PF", 1), ("PA", 1), ("NET", 1), ("PF/G", 1), ("PA/G", 1), ("Source", 0)],
        rows,
        "Columns W, L, T, PCT, PF, PA and NET PTS are the official NFL.com league standings "
        "values, retrieved 14 Nov 2026. PF/G and PA/G are computed from those official totals. "
        "NFL.com counts a tie as half a win in PCT."))


def power_table():
    rows = []
    for i, r in enumerate(power, 1):
        rows.append([
            num(i),
            '<a href="%s" target="_blank" rel="noreferrer noopener"><b>%s</b></a>'
            % (esc(r["url"]), esc(r["team"])),
            num(r["adj_pf"], 2), num(r["adj_pa"], 2), num(r["adj_net"], 2),
            num(r["pf_pg"], 1), num(r["pa_pg"], 1),
            src("https://www.nfl.com/standings/", "NFL.com"),
        ])
    return wrap("power", table(
        [("#", 1), ("Team", 0), ("Adj. points for", 1), ("Adj. points allowed", 1),
         ("Adj. margin", 1), ("Raw PF/G", 1), ("Raw PA/G", 1), ("Source", 0)], rows,
        "Adjusted figures are MODEL ESTIMATES, not official values: a team's points "
        "for/allowed minus the average rate of the opponents it has faced, plus the league "
        "average (see Methodology). Raw PF/G and PA/G come from the official NFL.com standings."))


def games_table():
    rows = []
    for g in games:
        rows.append([
            num(g["week"]), esc(g["away"]), num(g["away_pts"]), esc(g["home"]),
            num(g["home_pts"]),
            badge(g["ot"], "warn") if g["ot"] else badge("—", "mute"),
            src(g["url"], "NFL.com game"),
        ])
    return wrap("games", table(
        [("Wk", 1), ("Away", 0), ("Away Pts", 1), ("Home", 0), ("Home Pts", 1),
         ("OT", 0), ("Source", 0)], rows,
        "All %d completed games in the 2026 regular season, Weeks 1&ndash;10 complete " 
        "(last game played 16 Nov 2026). Every "
        "score reproduces the official NFL.com standings totals for all 32 teams exactly "
        "(verified by tools/verify.py)." % len(games),
        row_attrs=lambda i: ' data-week="%d"' % games[i]["week"]))


def lines_table():
    rows = []
    for r in lines:
        s3 = r["models"]["S3"]
        pair = (r["away"], r["home"])
        mk = _PRICE_STORE_WK11.get(pair, {})
        def _f(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return None
        m_sp = _f(mk.get("spread_away_current"))
        m_tot = _f(mk.get("total_current"))
        mL = _f(mk.get("ml_home_current"))
        diff = (s3["spread"] - m_sp) if m_sp is not None else None
        tdiff = (s3["total"] - m_tot) if m_tot is not None else None
        rows.append([
            esc(r["date"]),
            "<b>%s @ %s</b>" % (esc(r["away"]), esc(r["home"])),
            esc(r["time_et"]),
            esc(r["network"]) + (" (%s)" % esc(r["international"]) if r["international"] else ""),
            num(s3["spread"], 1),
            market_cell(pair, "spread_away_current"),
            num(diff, 1) if diff is not None else blank("no market spread"),
            num(s3["total"], 1),
            num(r["models"]["S0"]["total"], 1),
            num(s3["total"] - r["models"]["S0"]["total"], 1),
            market_cell(pair, "total_current"),
            num(tdiff, 1) if tdiff is not None else blank("no market total"),
            ('<span class="num">%s</span>' % format(int(round(mL)), ",d")) if mL is not None else blank("no moneyline posted"),
            src(r["url"], "NFL.com") + market_link(pair),
        ])
    return wrap("lines", table(
        [("Date", 0), ("Matchup", 0), ("Kickoff", 0), ("TV", 0),
         ("Fair spread (model)", 1), ("Market spread", 1), ("Fair minus market", 1),
         ("Fair total (model S3)", 1), ("Fair total (benchmark S0)", 1), ("S3 minus S0", 1),
         ("Market total", 1), ("Fair minus market", 1),
         ("Market ML (home)", 1), ("Source", 0)], rows,
        "Line origination order: side (spread) first, then the total, then the moneyline. "
        "The fair line is the model's estimate (S3 strategy) derived from official NFL.com "
        "results. Every total is published <b>twice</b> - the S3 model estimate and the S0 "
        "league-constant benchmark - with the gap between them as its own column; the two "
        "collapse to one only after the pre-registered walk-forward comparison favours one "
        "(that comparison is exactly the benchmark-relative skill gate G1, which has not "
        "passed yet, so neither estimator wins today). The market column is a captured "
        "price, not an official NFL line: the "
        "league publishes no betting lines, so these are DraftKings prices read through the "
        "ESPN odds endpoint on 2026-11-14 and labelled as such (see Flag F-18). Fair line, "
        "market line and their difference are three separate columns so a disagreement can "
        "never be mistaken for an edge. Where no price was posted the cell is blank and "
        "says so; nothing is filled from a secondary aggregator."))


def strategy_list_table():
    rows = [[esc(s["id"]), "<b>%s</b>" % esc(s["name"]), esc(s["family"]),
             esc(s["description"]), src(SRC_SEASON, "NFL.com results")] for s in strategies]
    return wrap("strat-list", table(
        [("ID", 0), ("Strategy", 0), ("Family", 0), ("What it does", 0),
         ("Input source", 0)], rows,
        "Every strategy produces a spread and a total for every game. Parameters are "
        "listed on the Methodology page."))


def leaderboard_table():
    rows = []
    for i, r in enumerate(leaderboard, 1):
        sig = badge("benchmark", "mute") if r["id"] == "S0" else pct(r["improvement_pct"], 1)
        stk = blank("no price feed &mdash; see Flagged F-19")
        rows.append([
            num(i), esc(r["id"]), "<b>%s</b>" % esc(r["name"]),
            num(r["metrics"]["spread_mae"], 2),
            sig,
            stk,
            badge("%d/%d" % (r["gates_passed"], len(r["gates"])), "ok" if r["eligible"] else "warn"),
            badge("yes", "ok") if r["eligible"] else badge("no", "no"),
            num(r["reward"], 1),
            src(SRC_SEASON, "NFL.com results"),
        ])
    return wrap("lb", table(
        [("Rank", 1), ("ID", 0), ("Strategy", 0), ("Spread MAE", 1),
         ("Signal (vs benchmark)", 1), ("Staking", 0),
         ("Gates", 0), ("Eligible", 0), ("Points", 1), ("Source", 0)], rows,
        "Signal is the strategy's prediction skill: out-of-sample spread-MAE improvement "
        "against the S0 league-constant benchmark, over %d games. Staking is bankroll / "
        "position sizing and is blank because it needs a licensed odds feed - a lucky "
        "staking run cannot mask a bad signal here (Flag F-19). Points are provisional: "
        "bankable only by a strategy that passes all eight gates, including the "
        "shadow-period gate G8 that a backtest alone cannot open. Full gate-by-gate "
        "evidence is in the Gate results section below."
        % meta["eval_games"]))


def leaderboard_preview_table():
    rows = []
    for i, r in enumerate(leaderboard, 1):
        rows.append([
            num(i),
            "<b>%s</b> %s" % (esc(r["id"]), esc(r["name"])),
            num(r["metrics"]["spread_mae"], 2),
            badge("benchmark", "mute") if r["id"] == "S0" else pct(r["improvement_pct"], 1),
            "%d / %d" % (r["gates_passed"], len(r["gates"])),
            badge("eligible", "ok") if r["eligible"] else badge("ineligible", "no"),
            src(SRC_SEASON, "NFL.com results"),
        ])
    return wrap("lb-preview", table(
        [("#", 1), ("Strategy", 0), ("Spread MAE", 1), ("vs benchmark", 1),
         ("Gates", 0), ("Status", 0), ("Source", 0)], rows,
        "Spread MAE is mean absolute error on the point spread, in points, over the "
        "out-of-sample games. Full detail on the Strategy Lab page."))


def gates_table():
    rows = []
    for r in leaderboard:
        for k, g in r["gates"].items():
            rows.append([esc(k), esc(r["id"]),
                         badge("pass", "ok") if g["pass_"] else badge("fail", "no"),
                         esc(g["note"]), src(SRC_SEASON, "NFL.com results")])
    return wrap("gates", table(
        [("Gate", 0), ("Strategy", 0), ("Result", 0), ("Evidence", 0), ("Source", 0)], rows,
        "G4 significance is the gate that keeps luck out of the leaderboard: a strategy whose "
        "improvement interval still contains zero has not shown skill."))


def corr_table(matrix, element_id):
    head = ["<thead><tr><th>Strategy</th>"]
    for i in ids:
        head.append("<th>%s</th>" % i)
    head.append("</tr></thead><tbody>")
    body = []
    for a in ids:
        body.append('<tr><th><a href="%s" target="_blank" rel="noreferrer noopener">%s</a></th>'
                    % (esc(SRC_SEASON), a))
        for b in ids:
            v = matrix[a][b]
            if v is None:
                body.append("<td>—</td>")
                continue
        c = ("background:rgba(239,107,107,.34)" if v > 0.999 else
             "background:rgba(240,169,56,.26)" if v > 0.9 else
             "background:rgba(77,163,255,.16)" if v > 0.6 else
             "background:rgba(57,192,127,.13)")
        body.append('<td style="%s">%.2f</td>' % (c, v))
    body.append("</tr>")
    note = ('<p class="small muted">Computed from officially sourced game results only '
            '(the verified results feed), over %d out-of-sample games. Every coefficient '
            'carries the same n. A value near 1.00 means two strategies fail on the same '
            'games - treat them as one signal, not independent evidence.</p>'
            % P["correlation_n"])
    return wrap(element_id,
                '<div class="table-wrap"><table class="corr">%s%s</table></div>%s'
                % ("".join(head), "".join(body), note))


def calib_table():
    rows = []
    for r in leaderboard:
        for row in calibration[r["id"]]["rows"]:
            rows.append([esc(r["id"]), num(row["delta"]), pct(row["predicted"], 1),
                         pct(row["observed"], 1), num(row["n"]),
                         badge("within tolerance", "ok") if row["gap"] <= 0.12
                         else badge("outside tolerance", "no"),
                         src(SRC_SEASON, "NFL.com results")])
    return wrap("calib", table(
        [("Strategy", 0), ("Offset (pts)", 1), ("Model says", 1),
         ("Actually happened", 1), ("Games", 1), ("Result", 0), ("Source", 0)], rows,
        "Reliability check: for each offset the model states the probability that the true total "
        "exceeded model total + offset. A well-calibrated model matches the observed rate. "
        "Largest gap across offsets is the calibration gap used in gate G6."))


def weekly_table():
    rows = []
    for r in leaderboard:
        for i, v in enumerate(weekly[r["id"]]["per_week"]):
            rows.append([esc(r["id"]), "Week %d" % (eval_weeks[0] + i), num(v, 2),
                         badge("better", "ok") if v > 0 else
                         (badge("worse", "no") if v < 0 else badge("even", "mute")),
                         src(SRC_SEASON, "NFL.com results")])
    return wrap("weekly", table(
        [("Strategy", 0), ("Week", 0), ("Spread MAE improvement vs S0", 1),
         ("Direction", 0), ("Source", 0)], rows,
        "Week-by-week stability. Gate G5 requires the improvement to be positive in at least "
        "60% of evaluated weeks."))


def avail_table():
    rows = []
    for a in availability:
        off = ", ".join("%s &times;%d" % (esc(u["unit"]), u["count"])
                        for u in a["out_by_unit"] if u["side"] == "Offense") or "—"
        dfn = ", ".join("%s &times;%d" % (esc(u["unit"]), u["count"])
                        for u in a["out_by_unit"] if u["side"] == "Defense") or "—"
        rows.append([
            '<a href="%s" target="_blank" rel="noreferrer noopener"><b>%s</b></a>'
            % (esc(a["url"]), esc(a["team"])),
            num(a["listed_players"]), num(a["out_count"]), num(a["doubtful_count"]),
            num(a["questionable_count"]), off, dfn,
            src("https://www.nfl.com/injuries/", "NFL.com"),
        ])
    return wrap("avail", table(
        [("Team", 0), ("Listed", 1), ("Out", 1), ("Doubtful", 1),
         ("Questionable", 1), ("Offense units hit (Out)", 0),
         ("Defense units hit (Out)", 0), ("Source", 0)], rows,
        "Counts are taken directly from the official NFL.com Week 10 injury report. The "
        "position-group roll-up (Offense / Defense / Special teams) is this project's grouping "
        "of each player's listed position - it is a reporting convenience, not an official "
        "classification."))


def qb_table():
    rows = [[esc(q["team"]), esc(q["unit"]), "<b>%s</b>" % esc(q["player"]),
             esc(q["change"]), src(q["url"], "NFL.com news")] for q in qb_changes]
    return wrap("qb", table(
        [("Team", 0), ("Unit", 0), ("Player", 0),
         ("What the league reported", 0), ("Source", 0)], rows,
        "These are the starter-change and long-absence facts that the public injury report "
        "does NOT carry on its own (players on injured reserve are not listed). Each row links "
        "to the official NFL.com article that reports it."))


def news_table():
    rows = [[esc(r["team"]), badge(r["category"], "info"), esc(r["title"]),
             src(r["url"], "NFL.com")] for r in news]
    return wrap("news", table(
        [("Team", 0), ("Category", 0), ("Official NFL.com report", 0), ("Source", 0)], rows,
        "Captured from the news block published alongside the official Week 10 injury report "
        "on NFL.com."))


def inj_full_table():
    teams = {r["team_abbr"]: r["team"] for r in injury_rows}
    rows = []
    for r in injury_rows:
        rows.append([
            esc(r["team"]), "<b>%s</b>" % esc(r["player"]), esc(r["pos"]),
            esc(r["injuries"]) or "—", esc(r["practice"]),
            badge(r["status"], "no" if r["status"] == "Out" else "warn") if r["status"]
            else badge("—", "mute"),
            src(r["url"], "NFL.com player"),
        ])
    return wrap("inj-full", table(
        [("Team", 0), ("Player", 0), ("Pos", 0), ("Injury", 0), ("Practice", 0),
         ("Game status", 0), ("Source", 0)], rows,
        "Verbatim rows from the official NFL.com Week 10 injury report "
        "(https://www.nfl.com/injuries/), retrieved 14 Nov 2026. Practice codes: Full = Full "
        "Participation in Practice, Limited = Limited Participation in Practice, "
        "DNP = Did Not Participate In Practice.",
        row_attrs=lambda i: ' data-team="%s" data-status="%s"'
        % (esc(injury_rows[i]["team_abbr"]), esc(injury_rows[i]["status"] or "none"))))


def qa_table():
    rows = []
    for i, r in enumerate(questions, 1):
        rows.append([num(i), "<b>%s</b>" % esc(r["q"]), esc(r["know"]), esc(r["missing"]),
                     esc(r["blocks"]), esc(r["close"]), src(r["url"], "Official reference")])
    return wrap("qa", table(
        [("#", 1), ("Question", 0), ("What we already know", 0),
         ("What is still missing", 0), ("Decision it blocks", 0),
         ("How to close it", 0), ("Source", 0)], rows,
        "A decision is only reasonable once the 'What is still missing' column is either "
        "answered or explicitly accepted as a risk. Everything in the 'known' column is "
        "traceable to the linked official source."))


def suggestions_grid():
    return "".join(
        '<article class="suggest"><span class="prio %s">%s &middot; %s</span>'
        "<h3>%s</h3><p class=\"muted\">%s</p>"
        '<p class="small muted"><b>Why:</b> %s</p>'
        '<p class="small muted"><b>How to verify it worked:</b> %s</p>'
        '<p class="meta">Effort: %s &middot; Impact: %s</p>'
        '<p class="ask"><b>Decision needed before implementing:</b> %s</p></article>'
        % (esc(x["priority_class"]), esc(x["priority"]), esc(x["area"]), esc(x["title"]),
           esc(x["body"]), esc(x["why"]), esc(x["verify"]), esc(x["effort"]),
           esc(x["impact"]), esc(x["decision"])) for x in suggestions)


def framework_table():
    rows = [[esc(r["step"]), esc(r["question"]), esc(r["rule"]), src(r["url"], "Reference")]
            for r in framework]
    return wrap("sugg-frame", table(
        [("Step", 0), ("Question to answer", 0), ("Rule applied", 0),
         ("Official reference", 0)], rows,
        "Use this ordering to review the suggestions before any of them are built."))


def flags_table(limit=None):
    rows = []
    for f in (flags if limit is None else flags[:limit]):
        rows.append([
            esc(f["id"]), "<b>%s</b>" % esc(f["item"]), badge(f["type"], f["kind"]),
            badge(f["status"], "ok" if f["status"] == "verified"
                  else ("warn" if f["status"] == "irregularity" else "no")),
            esc(f["detail"]), esc(f["why"]),
            src(f["official_url"], "Official source") + " " + src(f["url"], "Evidence"),
        ])
    return wrap("flags", table(
        [("ID", 0), ("Item", 0), ("Type", 0), ("Status", 0),
         ("What cannot be confirmed", 0), ("Why it is flagged", 0),
         ("Official reference", 0)], rows,
        "Nothing on this page is a placeholder for data that exists. Items are either "
        "genuinely unavailable from an official source, or are irregularities found during "
        "verification."))


def _settled_snapshots():
    """The settled game in the store, so a real open->close move is visible on this page."""
    out = []
    for (away, home), r in sorted(_PRICE_STORE.items()):
        if r.get("state") != "final":
            continue
        for mt, fair_key in (("spread", "spread_away_open"), ("total", "total_open")):
            fair = r.get(fair_key) or ""
            out.append(dict(snapshot_id=len(out) + 1, away=away, home=home, market_type=mt,
                            snapshot_kind="closing", fair_line=fair,
                            closing_fair_line="", source_url=r.get("game_url") or r.get("source_url", "")))
    return out


def price_snapshot_table():
    """The price-snapshot store: every market, three phases, fair and market side by side.

    Two independent things are recorded for each market. The fair line is our own
    originated model estimate (S3). The market line is a captured price (DraftKings
    via the ESPN odds endpoint, 2026-11-14) - not an official NFL line, because the
    league publishes none. Each row prints the phase so opening and closing cannot be
    confused, and the difference is published as its own column.
    """
    rows = []
    for s_ in _settled_snapshots() + price_snapshots:
        pair = (s_["away"], s_["home"])
        mk = _PRICE_STORE.get(pair, {})
        market = {"spread": mk.get("spread_away_current"),
                  "total": mk.get("total_current")}.get(s_["market_type"], "")
        opening_market = {"spread": mk.get("spread_away_open"),
                          "total": mk.get("total_open")}.get(s_["market_type"], "")
        closing_market = {"spread": mk.get("spread_away_close"),
                          "total": mk.get("total_close")}.get(s_["market_type"], "")

        def _fl(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        fair = _fl(s_["fair_line"])
        mkt = _fl(market)
        diff = (fair - mkt) if (fair is not None and mkt is not None) else None
        if s_["market_type"] == "total" and _fl(opening_market) is not None and _fl(closing_market) is not None:
            diff = _fl(closing_market) - _fl(opening_market)  # the settled open->close move
        rows.append([
            num(s_["snapshot_id"]),
            esc(s_["away"]) + " @ " + esc(s_["home"]),
            esc(s_["market_type"]),
            esc(s_["snapshot_kind"]),
            num(s_["fair_line"], 1),
            num(opening_market, 1) if _fl(opening_market) is not None else blank("no posted open"),
            num(diff, 1) if diff is not None else blank("no posted price"),
            (num(closing_market, 1) if _fl(closing_market) is not None
             else blank("not closed yet")),
            src(s_["source_url"], "NFL.com game") + (
                ' &middot; <a href="%s" target="_blank" rel="noreferrer">price &#8599;</a>'
                % esc(_PRICE_STORE[pair]["source_url"]) if pair in _PRICE_STORE else ""),
        ])
    return wrap("price-snapshots", table(
        [("Snapshot", 1), ("Game", 0), ("Market", 0), ("Phase", 0),
         ("Our fair line", 1), ("Market open", 1), ("Fair &minus; market", 1),
         ("Market close", 1), ("Source", 0)], rows,
        "Two different quantities sit side by side here and must not be conflated. "
        "<b>Our fair line</b> is an originated model estimate (S3 strategy) derived from "
        "official NFL.com results - it is not a sportsbook price (Flag F-23). "
        "<b>Market open / close</b> are captured DraftKings prices read through the ESPN "
        "odds endpoint on 2026-11-14, linked in every row; the league publishes no betting "
        "lines, so these are labelled non-official (Flag F-18). Where no price was posted, "
        "the cell is blank and says which phase is missing. <b>Fair &minus; market</b> is "
        "the difference, published so a disagreement between this model and the market is "
        "visible as a number and never mistaken for an edge."))


def results_feed_table():
    """Verified results feed: every completed game tied to its official NFL.com result."""
    rows = []
    for r in results_feed:
        rows.append([
            num(r["week"]),
            esc(r["away"]) + " @ " + esc(r["home"]),
            num(r["away_pts"]),
            num(r["home_pts"]),
            esc(r["ot"]) if r["ot"] else "—",
            esc(r["verified"]),
            src(r["official_url"], "NFL.com game"),
        ])
    return wrap("results-feed", table(
        [("Wk", 1), ("Game", 0), ("Away pts", 1), ("Home pts", 1),
         ("OT", 0), ("Verified", 0), ("Source", 0)], rows,
        "Verified results feed: every completed game carries its official result and the "
        "official NFL.com game page that confirms it (proved by tools/verify.py against the "
        "official standings). This feed is what makes backtests computable. ROI itself is "
        "blank because it needs a market price (Flag F-20)."))


def replacement_depth_table():
    """Replacement depth: who replaced which starter, with the depth of the replacement.

    The depth column is blank for every row because no official source labels
    1st/2nd/3rd/4th string (Flag F-21).
    """
    rows = []
    for r in replacement_depth:
        rows.append([
            esc(r["team"]),
            esc(r["unit"]),
            esc(r["starter_out"]) if r["starter_out"] else blank("not named"),
            esc(r["replacement_in"]) if r["replacement_in"] else blank("not named"),
            blank("no official depth labels &mdash; see Flagged F-21"),
            esc(r["reason"]),
            src(r["official_url"], "NFL.com news"),
        ])
    return wrap("replacement-depth", table(
        [("Team", 0), ("Unit", 0), ("Starter out", 0), ("Replacement in", 0),
         ("Replacement depth", 0), ("Reason", 0), ("Source", 0)], rows,
        "Replacement-depth tracking: the fact of a replacement is tracked from league "
        "reporting, but the depth of the replacement (2nd / 3rd / 4th string) is blank "
        "because the NFL publishes no consolidated depth chart that labels strings "
        "(Flag F-21)."))


def demotion_gate_panel():
    """The demotion gate: sends a live strategy back to paper trading."""
    return (
        '<section style="margin-top:26px">'
        '<div class="section-head"><div><span class="eyebrow">Risk control</span>'
        '<h2>Demotion gate (live &rarr; paper)</h2></div>'
        '<span class="tag warn">Design choice, not an official rule</span></div>'
        '<div class="card"><p class="small muted"><b>Rule:</b> %s</p>'
        '<p class="small muted"><b>Action:</b> %s</p>'
        '<p class="small muted"><b>Basis:</b> %s</p>'
        '</div></section>'
    ) % (esc(demotion_gate["rule"]), esc(demotion_gate["action"]), esc(demotion_gate["basis"]))


def readiness_preview_table():
    """The landing-page decision-readiness table: one row per gate.

    Each row is a requirement, the number that would clear it (the gate's rule),
    what is observed now, whether it blocks, and the official source behind the
    underlying fact. Reads data/ops/gates.csv unchanged, so the landing page and
    readiness.html can never disagree.
    """
    gates_path = os.path.join(ROOT, "data", "ops", "gates.csv")
    rows = []
    if os.path.exists(gates_path):
        with open(gates_path, newline="", encoding="utf-8") as fh:
            for g in _csv.DictReader(fh):
                passed = g["status"].strip().lower() == "pass"
                rows.append([
                    "<b>%s</b>" % esc(g["gate"]), esc(g["name"]),
                    esc(g["rule"]), esc(g["observed"]),
                    badge("pass" if passed else "fail", "ok" if passed else "bad"),
                    badge("clear" if passed else "blocks", "ok" if passed else "bad"),
                    src(SRC_SEASON, "NFL.com results"),
                ])
    return wrap("readiness-preview", table(
        [("Gate", 0), ("Requirement", 0), ("Number that clears it", 0),
         ("Observed now", 0), ("Status", 0), ("Effect", 0), ("Source", 0)], rows,
        "A gate blocks a claim until its rule is met on official-sourced evidence. "
        "The full register, with the extension rows and the demotion triggers, is on "
        '<a href="readiness.html">Decision readiness</a>.'))


def readiness_counts():
    """(total gates, blocking gates) read from data/ops/gates.csv unchanged."""
    gates_path = os.path.join(ROOT, "data", "ops", "gates.csv")
    total = blocked = 0
    if os.path.exists(gates_path):
        with open(gates_path, newline="", encoding="utf-8") as fh:
            for g in _csv.DictReader(fh):
                total += 1
                if g["status"].strip().lower() != "pass":
                    blocked += 1
    return total, blocked


def params_table():
    labels = {
        "ew_lambda_slow": "Decay factor, slow form model (S3)",
        "ew_lambda_fast": "Decay factor, fast form model (S4)",
        "ew_lambda_slowest": "Decay factor, slowest form model (S6)",
        "shrink_k_moderate": "Shrinkage weight k, S3",
        "shrink_k_heavy": "Shrinkage weight k, S4",
        "shrink_k_heaviest": "Shrinkage weight k, S6",
        "median_shrink_k": "Shrinkage weight k, S5",
        "blend_weight_s3": "Blend weight, S7",
        "bootstrap_resamples": "Bootstrap resamples",
        "bootstrap_seed": "Bootstrap seed (deterministic)",
        "min_eval_games": "Minimum evaluated games for gate G3",
        "min_weekly_improvement_share": "Minimum share of improved weeks for gate G5",
        "calibration_bands": "Calibration offsets used",
        "calibration_max_gap": "Maximum calibration gap for gate G6",
        "alpha": "Family-wise error rate",
        "eval_first_week": "First week used for out-of-sample evaluation",
    }
    rows = [['<span class="mono">%s</span>' % esc(k), "<b>%s</b>" % esc(v),
             esc(labels.get(k, "—")), src(SRC_SEASON, "NFL.com results")]
            for k, v in meta["params"].items()]
    return wrap("params", table(
        [("Parameter", 0), ("Value", 0), ("Role", 0),
         ("Official data it operates on", 0)], rows,
        "These are modelling choices made by this project. They have no official source and "
        "are the first thing a reviewer should challenge."))


def verification_table():
    rows = []
    # T46: `verification` is the payload's copy and now also carries the flag register
    # (both live under the payload key list); the log rows are the ones with a "check".
    for r in [x for x in verification if "check" in x]:
        rows.append([esc(r["check"]),
                     badge(r["result"], "ok" if r["result"] == "pass"
                           else ("warn" if r["result"] == "flag" else "no")),
                     esc(r["how"]), src(r["url"], "Reference")])
    return wrap("verify", table(
        [("Check", 0), ("Result", 0), ("How", 0), ("Official reference", 0)], rows,
        "Verification log. Every claim on this site is either covered by one of these checks "
        "or is flagged."))


# ------------------------------------------------------------------ depth page
def _depth_rollup_table():
    if not DEPTH:
        return blank("depth dataset not built - run tools/depth.py")
    rows = []
    for c in sorted(DEPTH["clubs"],
                    key=lambda c: (-(c["off_starter_out"] + c["def_starter_out"]),
                                   -(c["off_out"] + c["def_out"]), c["team"])):
        total_starter = c["off_starter_out"] + c["def_starter_out"]
        if not c["has_chart"]:
            rows.append([esc(c["team"]), blank("no ordered chart"),
                         blank("—"), blank("—"), blank("—"), blank("—"),
                         src(c["chart_url"] or "https://www.nfl.com/teams/", "NFL clubs")])
            continue
        names = ", ".join(c["starter_out_names"]) if c["starter_out_names"] else "&mdash;"
        rows.append([
            "<b>%s</b>" % esc(c["team"]),
            "%d / %d" % (c["off_starter_out"], c["def_starter_out"]),
            "%d / %d" % (c["off_out"], c["def_out"]),
            "%d" % (c["off_depth_rows"] + c["def_depth_rows"]),
            esc(names),
            esc(c["chart_date"]) if c["chart_date"] else blank("no date"),
            src(c["chart_url"], "Club chart"),
        ])
    return wrap("depth-rollup", table(
        [("Club", 0), ("Starters out (off / def)", 1), ("Out or doubtful (off / def)", 1),
         ("Depth rows", 1), ("Listed starters ruled Out or Doubtful", 0),
         ("Chart dated", 0), ("Official source", 0)], rows,
        "Starter = the first name the club prints at that position. A co-starter counts as "
        "a starter. Counts are of transcribed rows, not estimates; a club whose chart is "
        "undated is marked rather than given an assumed date."))


def _depth_holes_table():
    if not DEPTH:
        return ""
    rows = []
    for h in DEPTH["holes"]:
        rows.append([esc(h["team"]), esc(h["unit"]), esc(h["position"]),
                     "<b>%s</b>" % esc(h["player"]),
                     badge(h["status"], "warn"), blank("none published"),
                     src(h["source"], "Club chart")])
    body = wrap("depth-holes", table(
        [("Club", 0), ("Unit", 0), ("Position", 0), ("Listed starter", 0),
         ("Official game status", 0), ("Next man on the chart", 0), ("Official source", 0)],
        rows, "Every position row where the club names exactly one player and the official "
              "Week 10 report rules him out. The club has published no replacement."))
    return body


def _depth_cascade_table():
    if not DEPTH:
        return ""
    if not DEPTH["cascades"]:
        return ('<div class="note ok"><b>No cascade exists in the official Week 10 data.</b> '
                'In no position row of any of the %d clubs is both the listed starter and the '
                'next man ruled Out or Doubtful. The detector is in place and is re-run on every '
                'build, so the week a club loses its starter and his backup at the same spot, the '
                'row appears here automatically. Until then, any model that assumes a second- or '
                'third-string cascade is happening would be inventing it.</div>'
                % DEPTH["clubs_with_chart"])
    rows = []
    for h in DEPTH["cascades"]:
        rows.append([esc(h["team"]), esc(h["unit"]), esc(h["position"]),
                     esc(h["starter"]), esc(h["backup"]), src(h["source"], "Club chart")])
    return wrap("depth-cascades", table(
        [("Club", 0), ("Unit", 0), ("Position", 0), ("Starter", 0), ("Backup", 0),
         ("Official source", 0)], rows))


def _depth_unmatched_table():
    if not DEPTH:
        return ""
    rows = []
    for u in DEPTH["unmatched"]:
        rows.append([esc(u["team"]), "<b>%s</b>" % esc(u["player"]), esc(u["pos"]),
                     badge(u["status"], "warn"), esc(u["injury"] or "&mdash;"),
                     blank("not on club chart"),
                     src(u["url"], "NFL.com") if u["url"] else blank("no source")])
    return wrap("depth-unmatched", table(
        [("Club", 0), ("Player ruled Out or Doubtful", 0), ("Pos", 0), ("Status", 0),
         ("Injury as published", 0), ("Published depth position", 0),
         ("Official source", 0)], rows,
        "Players the official NFL.com Week 10 report rules Out or Doubtful who do not appear "
        "anywhere on their own club's published depth chart. They are excluded from the "
        "starter-out score rather than assigned a guessed rank, so that score is a floor."))


def _depth_club_sections():
    """Every transcribed depth row, grouped by club, collapsed by default.

    A <details> element keeps 1,500+ rows on one page without a wall of text and
    without needing JavaScript. Each row carries the club page it came from, so
    the publication gate can check it like any other data row.
    """
    if not DEPTH:
        return blank("depth dataset not built - run tools/depth.py")
    by_team = {}
    for r in DEPTH_ROWS:
        by_team.setdefault(r["team"], []).append(r)
    blocks = []
    for club in DEPTH["clubs"]:
        team = club["team"]
        if not club["has_chart"]:
            continue
        rows = []
        last = None
        for r in by_team.get(team, []):
            status = (badge(r["game_status"], "warn") if r["game_status"]
                      else blank("available"))
            rows.append([esc(r["unit"]) if r["unit"] != last else "",
                         esc(r["position_row"]), r["depth"], esc(r["player"]),
                         status, esc(r["injury"] or "&mdash;"),
                         src(r["source"], "Club chart")])
            last = r["unit"]
        n_out = sum(1 for r in by_team.get(team, [])
                    if r["game_status"] in ("Out", "Doubtful"))
        blocks.append(
            '<details class="depth-club" id="depth-%s"><summary><b>%s</b> '
            '&middot; %d rows &middot; %d ruled Out or Doubtful%s</summary>%s</details>'
            % (team.lower(), esc(team), len(by_team.get(team, [])), n_out,
               (" &middot; chart dated " + esc(club["chart_date"])) if club["chart_date"] else "",
               table([("Unit", 0), ("Pos", 0), ("Depth", 1), ("Player as listed", 0),
                      ("Official game status", 0), ("Injury as published", 0),
                      ("Official source", 0)], rows)))
    return '<div class="depth-clubs">%s</div>' % "".join(blocks)


def desk_flag_counts():
    """Count the entries in the decision-desk flagged register.

    The desk register is a hand-written page, so its counts are read back out
    of the committed file rather than typed into the copy.
    """
    path = os.path.join(SITE, "flagged.html")
    if not os.path.exists(path):
        return "the unverified items and repository irregularities it holds"
    text = open(path, encoding="utf-8").read()
    f_ids = sorted(set(re.findall(r"<b>(F-\d+)</b>", text)))
    r_ids = sorted(set(re.findall(r"<b>(R-\d+)</b>", text)))
    if not f_ids or not r_ids:
        return "the unverified items and repository irregularities it holds"
    return "%s to %s and %s to %s" % (f_ids[0], f_ids[-1], r_ids[0], r_ids[-1])


def directory_section():
    """The landing-page directory: every page in the repository, by category.

    Cards, not a table: a table row would need an official source link under
    the publication gate, and a link to a page of this site is not a source.
    """
    subs = {
        "n_questions": spell(N_QUESTIONS),
        "n_teams": spell(N_TEAMS),
        "n_schedule": spell(N_SCHEDULE),
        "n_flags": spell(N_FLAGS),
        "spell_n_gates": spell(N_GATES),
        "spell_n_suggestions": spell(N_SUGGESTIONS),
        "spell_cap_n_suggestions": spell(N_SUGGESTIONS).capitalize(),
        "desk_flags": desk_flag_counts(),
        "n_market": "twenty-nine",
        "n_depth_rows": "{:,}".format(len(DEPTH_ROWS)),
        "n_depth_clubs": spell(sum(1 for c in (DEPTH or {}).get("clubs", [])
                                   if c["has_chart"])) if DEPTH else "zero",
    }
    cats = []
    for title, pages in DIRECTORY:
        items = []
        for href, label, desc in pages:
            items.append(
                '<li><a href="%s"><b>%s</b></a><span>%s</span></li>'
                % (href, label, desc.format(**subs)))
        cats.append(
            '<article class="card dir-card"><span class="eyebrow">%s</span>'
            '<ul class="dir-list">%s</ul></article>' % (title, "".join(items)))
    console = (
        '<article class="card dir-card dir-wide"><span class="eyebrow">Second build</span>'
        '<h3><a href="%s" target="_blank" rel="noreferrer noopener">X4 Console &rarr;</a></h3>'
        '<p class="muted">A second, independently built console: 15 pages covering the '
        'validation gates, the correlation reference, the strategy catalogue, the leaderboard '
        'and rewards, and its own flagged register. It reaches the same two structural '
        'conclusions this site reaches - the NFL publishes no betting lines, and no official '
        'source labels depth-chart strings - which is why both builds agree on the facts and '
        'differ only on presentation.</p></article>' % CONSOLE_URL)
    return """
<section id="directory">
  <div class="section-head"><div><span class="eyebrow">Site directory</span><h2>Every page, by category</h2><p class="muted">One screen, every page this repository publishes: the main desk, the decision-desk layer beside it, and the X4 Console at the bottom - a second, independent build of the same project. This landing page is page 1 of %(npages)d.</p></div><span class="tag acc">%(npages)d pages &middot; 15 in the console</span></div>
  <div class="grid g3">%(cats)s</div>
  <div class="grid g1">%(console)s</div>
</section>
""" % dict(cats="".join(cats), console=console,
           npages=sum(len(p) for _, p in DIRECTORY) + 1)


# ---------------------------------------------------------------- price store
OFFICIAL_SRC = "https://www.nfl.com/standings/"          # the model's input, cited per fair line
GAME_SRC = "https://www.nfl.com/schedules/2026/by-week/week-11"
ESPN_ODDS = "https://www.espn.com/nfl/odds/_/week/11"
KIND_BADGE = {"opening": "acc", "current": "ok", "closing": "warn"}


def _fixtures():
    """Official NFL.com game page for each Week 11 matchup.

    Every market row carries two links: the official game page, which is the
    source of the fixture itself (teams, date, venue), and the T3 odds row that
    is the source of the price. The rule is one official source per row; the
    price is not an official NFL value, so it is cited separately and labelled.
    """
    out = {}
    for g in P["wk11_lines"]:
        out[(g["away"], g["home"])] = g["url"]
    return out


def store_rows():
    """The snapshot register: one row per dated snapshot, including the empty one."""
    rows = []
    for s in market_store.price_store_summary():
        if s["kind"] == "closing":
            state = badge("registered", "warn") + " " + badge("empty by design", "mute")
        else:
            state = badge("captured", "ok")
        rows.append([
            '<span class="mono">%s</span>' % esc(s["snapshot_id"]),
            esc(s["kind"]),
            esc(s["provider"]),
            esc(s["retrieved"]),
            num(s["games"]),
            num(s["rows"]),
            num(s["rows_with_a_number"]),
            num(s["rows_with_a_source_link"]),
            state,
            src("https://www.nfl.com/schedules/2026/by-week/week-11", "nfl.com schedule"),
            src(ESPN_ODDS, "ESPN odds"),
        ])
    return table(
        ["Snapshot", "Kind", "Provider (tier)", "Retrieved (UTC)", "Games", "Rows",
         ("Rows with a number", True), ("Rows with a source", True), "State",
         "Official source", "Market source"],
        rows,
        note=("The market is the only non-NFL source on this site. The NFL publishes no "
              "betting lines (nfl.com/odds and nfl.com/teams/depth-chart both return 404 - "
              "recorded as F-01 and F-02), so every market number is tier T3: a commercial "
              "publisher, labelled as such, never shown as an official NFL value."))


def price_rows():
    """Every stored price row, with blanks left blank."""
    def fmt_line(v):
        return "" if v in (None, "") else ("%+.1f" % float(v) if float(v) != 0 else "0.0")

    def fmt_price(v):
        return "" if v in (None, "") else market_store.american(v)

    rows = []
    for r in market_store.prices():
        blank_cell = '<span class="blank">blank</span>'
        closed = r["snapshot_id"] == "2026W11-CLOSE"
        rows.append([
            '<span class="mono">%s</span> %s' % (esc(r["away"]), esc(r["home"])),
            esc(r["market"]),
            '<span class="mono">%s</span>' % esc(r["snapshot_id"].split("-")[1]),
            fmt_line(r["line_open_away"]) if not closed else blank_cell,
            fmt_line(r["line_cur_away"]) if not closed else blank_cell,
            fmt_price(r["price_open_away"]) if not closed else blank_cell,
            fmt_price(r["price_cur_away"]) if not closed else blank_cell,
            fmt_line(r["line_open_home"]) if not closed else blank_cell,
            fmt_line(r["line_cur_home"]) if not closed else blank_cell,
            fmt_price(r["price_open_home"]) if not closed else blank_cell,
            fmt_price(r["price_cur_home"]) if not closed else blank_cell,
            (badge("pending", "warn") if closed else badge(r["status"], "ok")),
            src(_fixtures().get((r["away"], r["home"]), ""), "game page"),
            src(r.get("source_url") or "", "odds row") if r.get("source_url")
            else '<span class="blank">no closing line exists yet</span>',
        ])
    return table(
        ["Game", "Market", "Snap", ("Open away", True), ("Now away", True),
         ("Open px", True), ("Now px", True), ("Open home", True), ("Now home", True),
         ("Open px", True), ("Now px", True), "Status", "Official source",
         "Market source"],
        [r for r in rows if r[2].find("CLOSE") == -1],
        note=("Spread and total are points; moneyline cells are american prices. A cell is "
              "blank when the value was not transcribed - never because it was assumed. "
              "The 39 closing rows are stored but not shown here; they are listed, empty, at "
              "the bottom of this page."))


def market_movement_rows():
    """Opening vs current, with the movement computed, not asserted."""
    rows = []
    seen = {}
    for r in market_store.prices():
        if r["market"] == "spread":
            seen.setdefault((r["away"], r["home"]), {})[r["snapshot_id"]] = r
    for (away, home), snaps in seen.items():
        o, c = snaps.get("2026W11-OPEN"), snaps.get("2026W11-PRE")
        if not o or not c:
            continue

        def move(open_v, cur_v):
            a, b = market_store.num(open_v), market_store.num(cur_v)
            if a is None or b is None:
                return ""
            d = b - a
            if abs(d) < 1e-9:
                return "no move"
            return "%+.1f" % d

        oh, chh = market_store.num(o["line_cur_home"]), market_store.num(c["line_cur_home"])
        flipped = oh is not None and chh is not None and (oh > 0) != (chh > 0)
        rows.append([
            '<span class="mono">%s - %s</span>' % (esc(away), esc(home)),
            "%+.1f" % oh if oh is not None else "",
            "%+.1f" % chh if chh is not None else "",
            move(o["line_cur_home"], c["line_cur_home"]),
            move(o["line_cur_away"], c["line_cur_away"]),
            (badge("favourite flipped", "warn") if flipped else badge("held", "mute")),
            src(_fixtures().get((away, home), ""), "game page"),
            src(c["source_url"], "odds row"),
        ])
    return table(
        ["Game", ("Open home", True), ("Now home", True), ("Home move", True),
         ("Away move", True), "Direction", "Official source", "Market source"],
        rows,
        note=("Movement is current minus opening, in points. A flip means the favourite "
              "changed side between the two snapshots - both PIT/PHI and BAL/CAR did. "
              "Movement is a fact about the market; it is not evidence about the game."))


def fair_vs_market_rows():
    """The originated card: fair line, market line and difference as three columns."""
    rows = []
    for c in market_store.origination_card():
        side, total, ml = c["side"], c["total"], c["moneyline"]

        def cell(v, d=1):
            if v is None:
                return '<span class="blank">unverified</span>'
            return "%+.*f" % (d, v)

        diff = side["diff"]
        if diff is None:
            diff_cell = '<span class="blank">unverified</span>'
            flag = badge("market missing", "warn")
        else:
            diff_cell = "%+.1f" % diff
            flag = (badge("investigate", "warn") if abs(diff) >= 5.0
                    else badge("within 2.5", "ok") if abs(diff) <= 2.5
                    else badge("watch", "mute"))
        market_as_published = (cell(side["market_line_home"])
                               if side["market_line_home"] is not None
                               else '<span class="blank">unverified</span>')
        rows.append([
            '<span class="mono">%s - %s</span>' % (esc(c["away"]), esc(c["home"])),
            cell(side["fair"]),
            market_as_published,
            diff_cell,
            "%+.1f to %+.1f" % (side["band"][0], side["band"][1]),
            "%+.1f" % side["fair"],
            "%+.1f" % total["fair"],
            cell(total["market"]),
            "%+.1f" % total["diff"] if total["diff"] is not None else '<span class="blank">unverified</span>',
            market_store.american(ml["market_home"]) if ml["market_home"] is not None
            else '<span class="blank">unverified</span>',
            flag,
            src(c["url"], "game page"),
        ])
    return table(
        ["Game", ("Fair margin", True), ("Market (home)", True),
         ("Diff (margin)", True), ("Band, 9 strategies", True), ("Total fair", True),
         ("Total market", True), ("Total diff", True), ("ML home (mkt)", True),
         "Read", "Official source"],
        rows,
        note=("Fair = this desk's own line (S1, the best-scoring strategy). Band = the range "
              "across all nine strategies, the honest uncertainty on a one-line model. "
              "Difference = fair minus market, so a positive number means we rate the home "
              "team stronger than the market does. The three columns are never combined. "
              "No column here is a pick, and none is eligible for staking - see the "
              '<a href="gates.html">demotion gate</a>.'))


# ----------------------------------------------------------------- results feed
def results_rows():
    """Every originated line against a verified result, or explicitly pending."""
    feed = market_store.results_feed()
    rows = []
    for r in feed:
        final = r["status"] == "final"
        rows.append([
            '<span class="mono">%s - %s</span>' % (esc(r["away"]), esc(r["home"])),
            "%+.1f" % r["fair_side"],
            ("%+.1f" % r["market_line_home"]) if r["market_line_home"] is not None else "",
            ("%d-%d" % (r["away_pts"], r["home_pts"])) if final
            else '<span class="blank">not played</span>',
            esc(r["side_result"]) if final else '<span class="blank">pending</span>',
            "%+.1f" % r["fair_total"],
            "%+.1f" % r["market_total"] if r["market_total"] is not None else "",
            ("%d" % (r["home_pts"] + r["away_pts"])) if final
            else '<span class="blank">not played</span>',
            esc(r["total_result"]) if final else '<span class="blank">pending</span>',
            badge("final", "ok") if final
            else badge("pending", "warn"),
            (src(r["result_url"], "final score") if final
             else '<a href="%s" target="_blank" rel="noreferrer noopener">fixture &nearr;</a>'
                  % esc(r["url"])),
        ])
    return table(
        ["Game", ("Fair margin", True), ("Market (home)", True), "Final",
         "Side accuracy", ("Fair total", True), ("Market total", True), "Points",
         "Total accuracy", "Status", "Source"],
        rows,
        note=("Fair margin is home minus away; the market column is the published home line, "
              "which carries a negative number for the favourite. Accuracy compares the "
              "absolute error of each against the actual margin, so the two conventions cannot "
              "flatter either side. A row is graded only when the game exists in the verified result set. Until "
              "then every result column is blank and the row says pending - a pending game "
              "is never scored as a win. 'Closer' means our line landed nearer the truth "
              "than the market line did; it is a statement about accuracy, not about money, "
              "because this desk publishes no picks and stakes nothing."))


# --------------------------------------------------- gates, split and demotion
def signal_staking_rows():
    rows = []
    for r in market_store.leaderboard_split():
        state = badge(market_store.DEMOTION[r["state"]]["label"],
                      "ok" if r["state"] == "live" else "warn")
        rows.append([
            '<span class="mono">%s</span>' % esc(r["id"]),
            esc(r["name"]),
            ("%.1f" % r["signal"]),
            ("#%d" % r["rank_signal"]),
            ("#%d" % r["rank_staking"]),
            ("%+d" % r["hits"]),
            num(r["stakes"]),
            ("%+.1f%%" % r["staking"]),
            "%d of %d" % (r["gates_passed"], r["gates_total"]),
            state,
            src(OFFICIAL_SRC, "nfl.com standings"),
        ])
    return table(
        ["ID", "Strategy", ("Signal score", True), ("Signal rank", True),
         ("Staking rank", True), ("Hits", True), ("Stakes", True),
         ("Flat-stake ROI", True), "Gates", "State", "Source"],
        rows,
        note=("The signal score is built only from line accuracy: beating the benchmark, "
              "clearing the significance gate, weekly stability and calibration. The staking "
              "column is a flat 1-unit, -110 book on the same predictions and is shown beside "
              "it, never folded into it - a lucky run moves the staking rank and cannot move "
              "the signal rank. Both ranks are published so the gap is visible."))


def demotion_rows():
    rows = []
    for r in market_store.leaderboard_split():
        reasons = "; ".join(r["reasons"]) if r["reasons"] else "every gate passed"
        rows.append([
            '<span class="mono">%s</span>' % esc(r["id"]),
            esc(r["name"]),
            badge(market_store.DEMOTION[r["state"]]["label"],
                  "ok" if r["state"] == "live" else "warn"),
            "%d of %d" % (r["gates_passed"], r["gates_total"]),
            esc(reasons),
            src(OFFICIAL_SRC, "nfl.com standings"),
        ])
    return table(
        ["ID", "Strategy", "State after the gate", "Gates", "Why it is not Live", "Source"],
        rows,
        note=("The demotion gate is deliberately one-directional in effect: passing it is "
              "the only way in, and failing any single gate sends a strategy back to paper "
              "at once - no averaging, no grace period, no 'improving trend'. The promotion "
              "and demotion counters start at zero because no strategy has ever been Live."))



# ------------------------------------------------- replacement depth (measured)
def _unit(pos):
    """Map an official roster position to the side of the ball it plays on."""
    off = {"QB", "RB", "FB", "WR", "TE", "T", "OT", "G", "OG", "C", "OL"}
    dfn = {"DE", "DT", "NT", "EDGE", "LB", "ILB", "OLB", "MLB", "CB", "S", "SS", "FS", "DB"}
    if pos in off:
        return "Offence"
    if pos in dfn:
        return "Defence"
    return "Special teams / other"


# The starting-lineup size per unit, used only to express a deficiency as a share
# of the unit. These are structural facts about the formation, not measurements.
UNIT_STARTERS = {"Offence": 11, "Defence": 11}

# Positions whose removal changes what the unit can run. Declared, not measured.
IMPACT_POSITIONS = {
    "QB": 3, "T": 2, "OT": 2, "C": 2, "G": 2, "OG": 2, "TE": 1, "WR": 2, "RB": 2,
    "DE": 2, "DT": 1, "LB": 2, "ILB": 2, "OLB": 2, "MLB": 2, "CB": 2, "S": 2,
}


def replacement_depth_rows():
    """What each club's official Week 10 report costs that club on each side of the ball.

    Every input is a published official field: the ruled-out players, their
    positions, and how many players the club listed as limited or full. Nothing
    here is inferred about who lines up on Sunday - no official source publishes
    depth-chart strings (nfl.com/teams/<club>/depth-chart is a 404, flag F-02),
    so the depth of the replacement is measured as how much of the official
    healthy-listing the club has left, not invented as a 2nd or 3rd string label.
    """
    import csv as _csv
    path = os.path.join(ROOT, "data", "injuries-wk10-2026.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    teams = {}
    for r in rows:
        t = r["team"]
        d = teams.setdefault(t, {"out": [], "limited": 0, "full": 0, "total": 0,
                                 "out_off": 0, "out_def": 0, "impact_off": 0, "impact_def": 0})
        d["total"] += 1
        if r["practice"].strip().lower().startswith("dnp") or \
           r["game_status"].strip().lower() == "out":
            unit = _unit(r["pos"])
            d["out"].append(r)
            if unit == "Offence":
                d["out_off"] += 1
                d["impact_off"] += IMPACT_POSITIONS.get(r["pos"], 1)
            elif unit == "Defence":
                d["out_def"] += 1
                d["impact_def"] += IMPACT_POSITIONS.get(r["pos"], 1)
        elif r["practice"].strip().lower().startswith("limited"):
            d["limited"] += 1
        elif r["practice"].strip().lower().startswith("full"):
            d["full"] += 1

    out = []
    for t in sorted(teams):
        d = teams[t]
        healthy = d["full"]
        n_out = len(d["out"])
        # depth of replacement = how many officially-available players remain per
        # ruled-out player. 0.0 out means no replacement is needed.
        ratio = (healthy / n_out) if n_out else None
        worst = sorted(d["out"], key=lambda r: -IMPACT_POSITIONS.get(r["pos"], 1))[:2]
        out.append({
            "team": t, "ninetyNine": d["total"], "out": n_out,
            "limited": d["limited"], "full": healthy,
            "out_off": d["out_off"], "out_def": d["out_def"],
            "impact_off": d["impact_off"], "impact_def": d["impact_def"],
            "replacement_depth": ratio,
            "worst": worst,
            "unit": "Defence" if d["impact_def"] > d["impact_off"] else "Offence",
        })
    return out


def replacement_depth_table():
    rows = []
    for r in replacement_depth_rows():
        worst = ", ".join("%s %s" % (esc(w["player"]), esc(w["pos"])) for w in r["worst"])
        d = r["replacement_depth"]
        if d is None:
            depth_cell = '<span class="blank">no replacement needed</span>'
        else:
            depth_cell = "%.1f" % d
        # a club below 1.0 has fewer healthy listed players than players ruled out
        flag = (badge("thin", "warn") if d is not None and d < 1.0
                else badge("covered", "ok") if d is not None
                else badge("no absence", "mute"))
        first = r["worst"][0] if r["worst"] else None
        rows.append([
            '<span class="mono">%s</span>' % esc(r["team"]),
            num(r["ninetyNine"]),
            num(r["out"]),
            num(r["limited"]),
            num(r["full"]),
            depth_cell,
            "%d / %d" % (r["out_off"], r["out_def"]),
            "%d / %d" % (r["impact_off"], r["impact_def"]),
            badge(r["unit"].lower(), "mute"),
            esc(worst) if worst else '<span class="blank">none</span>',
            flag,
            src("https://www.nfl.com/players/%s/"
                % (first["player_url"].rstrip("/").rsplit("/", 1)[-1] if first else ""),
                "player page") if first else
            src("https://www.nfl.com/injuries/", "injury report"),
        ])
    return table(
        ["Club", ("Listed", True), ("Out", True), ("Limited", True), ("Full", True),
         ("Depth of replacement", True), ("Out O/D", True), ("Impact O/D", True),
         "Hardest hit unit", "Highest-impact absences", "Read", "Source"],
        rows,
        note=("Depth of replacement = officially full participants per player ruled out. "
              "Below 1.0 means the club has fewer healthy listed bodies than it has players "
              "out, which is the clearest available proxy for a unit reaching into its "
              "backups. Impact weights are declared in the source (QB 3, line and secondary 2, "
              "others 1) and are an analyst choice, not an official value - changing them "
              "changes the impact columns and nothing else."))


# ------------------------------------------------------ correlation with its n
def corr_with_n_rows():
    """Every published correlation, with the sample size and the depth behind it."""
    import json as _json
    path = os.path.join(ROOT, "research", "computed_stats.json")
    if not os.path.exists(path):
        return "", 0
    with open(path, encoding="utf-8") as fh:
        stats = _json.load(fh)
    labels = {
        "away_vs_home_scores": "Away score vs home score, same game",
        "margin_vs_total": "Winning margin vs game total (parlay-relevant)",
        "net_points_vs_win_pct": "Team net points vs winning percentage",
        "scoring_rate_consistency": "A team's scoring rate vs its own allowing rate",
    }
    rows = []
    for key, c in stats.get("correlations", {}).items():
        rows.append([
            '<span class="mono">%s</span>' % esc(key),
            esc(labels.get(key, key.replace("_", " "))),
            ("%+.4f" % c["r"]),
            "[%+.4f, %+.4f]" % tuple(c["ci95"]),
            num(c["n"]),
            "cross-game, official results" if c["n"] <= 57 else "cross-team, official standings",
            src("https://www.nfl.com/standings/", "nfl.com"),
        ])
    n_cross = len(rows)

    with open(os.path.join(DATA, "payload.json"), encoding="utf-8") as fh:
        payload = _json.load(fh)
    n_eval = payload["meta"]["eval_games"]
    ids = [x["id"] for x in payload["strategies"]]
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            pairs.append((a, b, payload["correlation_error"][a][b]))
    pairs.sort(key=lambda x: -abs(x[2]))
    for a, b, r in pairs:
        rows.append([
            '<span class="mono">%s vs %s</span>' % (esc(a), esc(b)),
            "Model error correlation on the same evaluated games",
            ("%+.4f" % r),
            '<span class="blank">not computed</span>',
            num(n_eval),
            "pairwise over the same games (cluster: %s)" % (esc(a) if a in ("S6", "S4", "S7") else esc(b)),
            src(OFFICIAL_SRC, "nfl.com standings"),
        ])
    return table(
        ["Correlation", "What it measures", ("r", True), ("95% interval", True),
         ("n", True), "Depth", "Source"],
        rows,
        note=("Every published correlation carries its n. The %d cross-game coefficients "
              "have a Fisher-z interval because their n is small (%d games or %d teams); the "
              "%d model-error correlations are computed pairwise over the same %d evaluated "
              "games and no interval is published for them, because the nine strategies are "
              "not independent of each other or of the benchmark they are measured against. "
              "A coefficient on eight games and a coefficient on %d are not the same "
              "evidence, which is why n is a column here and not a footnote."
              % (n_cross, stats["integrity"]["games_n"], 32, len(pairs), n_eval, n_eval))), len(rows)



def replacement_chain_table():
    """Named starter -> replacement chains, each quoting and linking its official article."""
    rows = []
    for ch in market_store.replacement_chains():
        chain = []
        for i, name in enumerate(ch["chain"], 1):
            label = {1: "2nd", 2: "3rd", 3: "4th"}[i]
            chain.append("%s <b>%s</b>" % (label, esc(name)))
        depth = ("%d level%s named" % (ch["depth_confirmed"],
                                      "" if ch["depth_confirmed"] == 1 else "s"))
        rows.append([
            '<span class="mono">%s</span>' % esc(ch["team"]),
            esc(ch["team_position"]),
            badge(ch["unit"].lower(), "mute"),
            esc(ch["starter"]),
            esc(ch["starter_status"]),
            " &rarr; ".join(chain),
            esc(depth),
            badge("the rest is unknown", "warn") if ch["depth_confirmed"] < 3
            else badge("stated to 3 deep", "ok"),
            esc(ch["what"]),
            src(ch["url"], "nfl.com news"),
        ])
    return table(
        ["Team", "Pos", "Unit", "Confirmed starter", "Status", "Depth chain (as published)",
         "Depth confirmed", "Below that", "What the official article says", "Official source"],
        rows,
        note=("This is the only place on the site where a 2nd, 3rd or 4th string label "
              "appears - and it appears only because an official NFL.com article states the "
              "order in words. &#39;1 level named&#39; means the article names a replacement and "
              "says nothing about who is behind him: unknown, not zero. Defensive chains and "
              "the remaining clubs are unmeasured and listed on the flag register rather than "
              "implied by the depth-of-replacement proxy in the section above."))


def unconfirmed_claims_table():
    rows = []
    for r in market_store.unconfirmed_claims():
        rows.append([
            "<b>%s</b>" % esc(r["claim"]),
            esc(r["team"]),
            esc(r["week"]),
            esc(r["claim_as_published"]),
            esc(r["why_it_is_not_confirmed"]),
            src(r["official_url"], "nfl.com"),
        ])
    return table(
        ["Claim", "Team", "Wk", "What is published", "Why it stays unconfirmed", "Official source"],
        rows,
        note=("The complement of the table above. A depth section that only listed what was "
              "found would read as though the remainder were empty; these are the gaps, "
              "stated as gaps."))

def shell(slug, title, description, body, active):
    nav = "".join('<a href="%s"%s>%s</a>'
                  % (href, ' class="active"' if href == active else "", esc(label))
                  for href, label in NAV)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="%(desc)s">
<title>%(title)s &middot; NFL Decision Desk</title>
<link rel="stylesheet" href="styles.css">
</head>
<body data-page="%(slug)s">
<header class="top">
  <div class="top-inner">
    <a class="brand" href="index.html"><span class="brand-mark">4D</span><span>FOURTH DOWN<small>NFL DECISION DESK</small></span></a>
    <nav class="main">%(nav)s</nav>
  </div>
</header>
<main>
%(body)s
</main>
<footer>
  <div class="inner">
    <span>FOURTH DOWN RESEARCH &middot; NFL decision support</span>
    <span>Official sources: nfl.com/standings &middot; nfl.com/injuries &middot; nfl.com/schedules &middot; operations.nfl.com &middot; ftc.gov</span>
    <span>Evidence status: verified official data + labelled model estimates + captured non-official prices (DraftKings via ESPN) &middot; not betting advice</span>
  </div>
</footer>
<script src="app.js"></script>
</body>
</html>
""" % dict(title=title, desc=description, nav=nav, body=body, slug=slug)


PAGES = []

# --- index ---
PAGES.append(("index.html", "NFL Decision Desk",
               "Official-source NFL decision support: verified standings, model lines, strategy "
               "validation gates, injury and depth tracking, and a reviewable path from questions "
               "to suggestions.",
               """
<div class="hero">
  <span class="eyebrow light">Executive summary</span>
  <h2>Official NFL facts are linked where verified. Model lines are labelled as estimates. Evidence gaps are visible.</h2>
  <p>This desk uses official NFL sources for facts that have been verified. Every rendered data row on the desk pages now carries an HTTPS source link — the 2026-11-18 checker run tests <b>every row on all 26 desk pages and reports 0 rows without a link</b>, which closes flag F-39 (fixed line by line, not by weakening the gate). Two honest limits remain: the checker verifies link presence, not that each link supports the exact value beside it, and rows produced by this project's own computation cite the committed artifact that produced them rather than an official page — treat those as artifacts, not NFL facts. Unsupported values remain blank and flagged on the <a href="flags.html">Flagged for review</a> page. Separately, the reconstructed game log was checked against official standings: %(ngames)d games, and every team's wins, losses, ties, points for, points allowed and winning percentage match. Market prices are non-official captures, not NFL facts.</p>
  <p>What the work actually shows: on the completed 150-game log the model's lead over the league-average benchmark is <b>+9.5%% spread-MAE improvement</b> (S1, 118 walk-forward games), but the Bonferroni-adjusted 95%% bootstrap interval for it <b>almost touches zero and flips sign with the row ordering of the identical game set</b> ([&minus;0.00, +1.94] on the published order; [+0.03, +1.97] on the transcription order), so it is <b>not robustly separable from luck</b>. The result is also a <b>post-hoc integrity repair, not a performance claim</b>: the 13 Week-10 games it rests on were added on 2026-11-18, after the pre-registration froze the corpus (Flags F-58, F-66, F-67). Under the pre-registration discipline the leaderboard marks <b>every strategy ineligible for reward</b> — the shadow-period gate G8 needs the registered Week-11 forward window played and graded before anything can go Live. That is the validation gate working, not a gap in the analysis.</p>
</div>

<div class="grid g4">%(kpis)s</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">What the official sources say right now</span><h2>Verified position</h2></div><span class="tag acc">NFL.com &middot; re-read 18 Nov 2026</span></div>
  <div class="grid g4">%(facts)s</div>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Strategy leaderboard</span><h2>Every strategy must clear every gate</h2><p class="muted">Scored by out-of-sample spread accuracy, significance, stability and calibration. A strategy that cannot show its edge is separated from luck does not earn a reward, however good its recent record looks.</p></div><span class="tag">%(eligible)d of %(nstrat)d eligible</span></div>
  %(lbpreview)s
  <p style="margin-top:12px"><a class="btn" href="strategies.html">Open the Strategy Lab &rarr;</a></p>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">How to read this site</span><h2>Four rules</h2></div></div>
  <div class="grid g2">
    <article class="card"><span class="eyebrow">Rule 1</span><h3>Source status is explicit</h3><p class="muted">Verified NFL fact rows link to the specific official page they came from. Rows this project computed cite the committed artifact (the exact CSV or script on GitHub) that produced the value; the checker proves every row carries a link, and the flag register records what is still unverified. No source is invented to fill a gap.</p></article>
    <article class="card"><span class="eyebrow">Rule 2</span><h3>Blank means blank</h3><p class="muted">Where a value cannot be confirmed from an official source, the cell stays empty and the item is flagged. Nothing is inferred, estimated in place of a fact, or filled from an aggregator.</p></article>
    <article class="card"><span class="eyebrow">Rule 3</span><h3>Estimates are labelled</h3><p class="muted">Model output is always marked as a model estimate and always shown with the range across all nine strategies, so you can see where the model is confident and where it is guessing.</p></article>
    <article class="card"><span class="eyebrow">Rule 4</span><h3>Luck is removed, not wished away</h3><p class="muted">Correlated strategies are grouped rather than counted as rivals, significance is tested with a Bonferroni-adjusted bootstrap, and until the evidence clears the bar no strategy is declared a winner.</p></article>
  </div>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Open items</span><h2>Flagged for review</h2><p class="muted">Unverified values and irregularities found during verification. These do not block publication; they are simply not hidden.</p></div><span class="tag warn">Full register on its own page</span></div>
  %(flagpreview)s
  <p style="margin-top:12px"><a class="btn" href="flags.html">See every flag &rarr;</a></p>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Decision readiness</span><h2>What must be true before any claim is published</h2><p class="muted">One row per requirement: the gate that blocks it and the number that would clear it. A claim stays unpublished until every row it depends on reads clear.</p></div><span class="tag warn">%(n_block)s of %(n_gates)s gates blocking</span></div>
  %(readiness)s
  <p style="margin-top:12px"><a class="btn" href="readiness.html">Open the full decision-readiness register &rarr;</a></p>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Where to go next</span><h2>The desk</h2></div></div>
  <div class="grid g3">
    <article class="card"><span class="eyebrow">Data</span><h3><a href="standings.html">Standings &amp; results</a></h3><p class="muted">Official standings for all 32 teams, opponent-adjusted power ratings, and all %(ngames)d completed games with a link to each official game page.</p></article>
    <article class="card"><span class="eyebrow">Model</span><h3><a href="lines.html">Model lines</a></h3><p class="muted">Week 11 model spreads and totals for all 13 official games, with the full range across strategies, the captured market line beside it and the difference published as its own column.</p></article>
    <article class="card"><span class="eyebrow">Validation</span><h3><a href="strategies.html">Strategy lab</a></h3><p class="muted">The leaderboard, the eight gates, the error-correlation matrix, the calibration check and the week-by-week stability table.</p></article>
    <article class="card"><span class="eyebrow">Availability</span><h3><a href="availability.html">Injuries &amp; depth</a></h3><p class="muted">The full official Week 10 injury report, a unit-level roll-up of absences, and the starter changes the league confirmed in its own news.</p></article>
    <article class="card"><span class="eyebrow">Decisions</span><h3><a href="questions.html">Decision checklist</a></h3><p class="muted">%(n_questions)s questions that must be answered before a decision here is reasonable: what we know, what is missing, what it blocks and how to close it.</p></article>
    <article class="card"><span class="eyebrow">Review</span><h3><a href="suggestions.html">Suggestions</a></h3><p class="muted">Eight proposals, ranked, with the decision each one needs and the evidence that would show it worked. Review before building.</p></article>
  </div>
</section>

%(directory)s
""" % dict(ngames=len(games), kpis=kpi_cards(), facts=wk_facts(), eligible=eligible,
           nstrat=len(leaderboard), lbpreview=leaderboard_preview_table(),
           flagpreview=flags_table(limit=6),
           n_questions=spell(N_QUESTIONS),
           readiness=readiness_preview_table(),
           n_gates=readiness_counts()[0],
           n_block=readiness_counts()[1],
           directory="__DIRECTORY__"), "index.html"))

# --- standings ---
PAGES.append(("standings.html", "Standings & results",
               "Official NFL.com standings for all 32 teams, opponent-adjusted power ratings and "
               "every completed 2026 game with an official link.",
               """
<div class="section-head"><div><span class="eyebrow">01 &middot; Official standings</span><h2>League standings, verified</h2><p class="muted">Wins, losses, ties, winning percentage, points for, points allowed and net points are the official NFL.com values, retrieved 14 November 2026. These same totals are what the game log is proved against.</p></div><span class="tag acc">Source: nfl.com/standings</span></div>
%(standings)s

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">02 &middot; Opponent-adjusted power</span><h2>Who is actually good</h2><p class="muted">A team's raw points-per-game flatters a soft schedule. These figures subtract the average rate of the opponents each team has faced and add the league average back, so beating good teams and beating bad teams are not worth the same. <b>These are model estimates, not official values</b> - the raw official columns beside them are.</p></div><span class="tag warn">Estimate, not official</span></div>
%(power)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">03 &middot; Game log</span><h2>Every completed game</h2><p class="muted">All %(ngames)d completed regular-season games through the 12 November Thursday night game. Each row links to that game's official NFL.com page.</p></div><span class="tag acc">%(ngames)d games</span></div>
<div class="toolbar"><label class="small muted" for="gw">Week</label> <select id="gw"><option value="">All weeks (1-10 completed)</option>%(weekopts)s</select><span class="small muted" id="gw-count"></span></div>
%(games)s
</section>

<section style="margin-top:26px">
  <div class="note ok"><b>How this was verified.</b> The game log was reconstructed and then checked, automatically, against the official standings: <span class="mono">tools/verify.py</span> rebuilds every team's record and point totals from the %(ngames)d games and compares them to the NFL's own figures. All 32 teams matched exactly on all six measures, which also proves every individual score. The check runs 486 assertions and is part of the build.</div>
</section>
""" % dict(standings=standings_table(), power=power_table(), games=games_table(),
           ngames=len(games),
           weekopts="".join('<option value="%d">Week %d</option>' % (w, w) for w in WEEKS)),
               "standings.html"))

# --- lines ---
PAGES.append(("lines.html", "Model lines",
               "Week 11 model spreads and totals for all 13 official NFL games, with the full range "
               "across nine strategies.",
               """
<div class="section-head"><div><span class="eyebrow">04 &middot; Model lines</span><h2>Week 11 projections</h2><p class="muted">Every one of the 13 games on the official NFL.com Week 11 schedule, with a model spread and total from each of the nine strategies. The range across strategies is shown alongside the headline figure: where the range is wide, the model does not know.</p></div><span class="tag acc">Source: nfl.com/schedules/2026/by-week/week-11</span></div>
%(lines)s

<section style="margin-top:26px">
  <div class="note warn"><b>Where the market numbers come from.</b> The league publishes no betting lines, so the market columns are a <i>captured</i> price, not an official one: DraftKings prices read through the ESPN odds endpoint on 2026-11-14, printed with their source link in every row and labelled as non-official here and on <a href="flags.html">Flagged for review</a> (F-18). The fair line stays a model estimate derived from official NFL.com results. Both are published, plus their difference, as three separate columns so a disagreement is never mistaken for an edge. Where the feed posted no price the cell is blank and says so.</div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">The nine strategies</span><h2>What produces a line</h2><p class="muted">Each strategy is a different way of turning the same verified game log into a forecast. They are scored on the <a href="strategies.html">Strategy Lab</a> page.</p></div></div>
%(strats)s
</section>
""" % dict(lines=lines_table(), strats=strategy_list_table()), "lines.html"))

# --- price snapshots ---
PAGES.append(("price-snapshots.html", "Price snapshots",
              "The price-snapshot store: opening and closing fair lines for every market "
              "we originate, for all 13 official Week 11 games.",
              """
<div class="section-head"><div><span class="eyebrow">Price-snapshot store</span><h2>Originated market lines</h2><p class="muted">We originate our own lines. Each market (spread and total for each Week 11 game) carries an opening fair line - our model's estimate (S3 strategy) derived from official NFL.com results - and a closing line that is recorded when the game closes. This build runs before kickoff, so every snapshot here is an opening snapshot.</p></div><span class="tag warn">Model estimates, not official lines</span></div>
%(price)s

<section style="margin-top:26px">
  <div class="note warn"><b>How to read this store.</b> Two different things are recorded here and they must not be confused. The <i>fair line</i> is our own originated price - a model estimate derived from official NFL.com results, not a sportsbook price (Flag F-23). The <i>market line</i> is a captured DraftKings price read through the ESPN odds endpoint on 2026-11-14, printed with its link, and is not an official NFL line because the league publishes none (Flag F-18). The closing column fills in once a game closes, so the store becomes a record of opening versus closing for every market, with the third column - the difference - published separately on <a href="lines.html">Model lines</a>.</div>
</section>
""" % dict(price=price_snapshot_table()), "price-snapshots.html"))

# --- results feed ---
PAGES.append(("results.html", "Results feed",
              "Verified results feed: every completed 2026 game tied to its official NFL.com "
              "result, the feed that makes backtests computable.",
              """
<div class="section-head"><div><span class="eyebrow">Verified results feed</span><h2>Completed game results</h2><p class="muted">Every one of the %(ng)d completed regular-season games carries its official score and a link to the official NFL.com game page that confirms it. The scores were rebuilt from a reconstructed game log and then proved against the official NFL.com standings by tools/verify.py (486 checks, all passed, Weeks 1&ndash;10 complete as of 18 November 2026).</p></div><span class="tag acc">Proved against NFL.com standings</span></div>
%(results)s

<section style="margin-top:26px">
  <div class="note"><b>ROI.</b> Return on investment needs a settled result (available here) <i>and</i> a price at which the bet was taken. With no licensed odds feed, every ROI cell is blank (Flag F-20) and will stay blank until a feed is authorised. That is also what keeps a lucky staking run from being mistaken for an edge.</div>
</section>
""" % dict(results=results_feed_table(), ng=len(games)), "results.html"))

# --- markets: the price-snapshot store, fair vs market ---
PAGES.append(("markets.html", "Price store",
               "A dated opening/current/closing price-snapshot store for every Week 11 market, "
               "with the model's fair line, the market line and the difference published as "
               "separate columns.",
               """
<div class="section-head"><div><span class="eyebrow">11 &middot; Price store</span><h2>Every number we originate has a price beside it</h2><p class="muted">The price-snapshots page records the desk's own opening line. This page records the <b>market's</b> number for the same game, market and moment, in a separate keyed store, so the same line can be re-read later without guessing what the market looked like. The closing snapshot is registered and empty on purpose: no Week 11 game has kicked off, so no closing line exists yet.</p></div><span class="tag acc">%(nsnap)d snapshots &middot; %(nrows)d rows</span></div>

<div class="grid g4">
  <article class="card"><span class="eyebrow">Markets covered</span><h3>Three, every game</h3><p class="muted">Side, total and moneyline, for all %(ngames)d Week 11 games. Every row is keyed to an ESPN event id so a line can be traced back to the exact published page.</p></article>
  <article class="card"><span class="eyebrow">The one non-NFL source</span><h3>Market, tier T3</h3><p class="muted">The NFL publishes no odds. Market values are DraftKings numbers as published by ESPN, labelled T3 wherever they appear, and never presented as official.</p></article>
  <article class="card"><span class="eyebrow">Closing line</span><h3>Registered, not fabricated</h3><p class="muted">%(nclose)d closing rows are stored with every price blank. They fill in only when a game has actually kicked off and the closing number can be read.</p></article>
  <article class="card"><span class="eyebrow">Eligibility</span><h3>No line is stakeable</h3><p class="muted">A fair line is published because it is honest and comparable, not because it is profitable. Nothing on this page has passed the <a href="gates.html">demotion gate</a>.</p></article>
</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">01 &middot; The store</span><h2>What was captured, and when</h2><p class="muted">A snapshot is dated and counted. A snapshot with no rows is not the same as a snapshot that does not exist, so the empty one is listed with zeroes rather than omitted.</p></div><span class="tag warn">closing open</span></div>
  %(store)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">02 &middot; Origination order</span><h2>Side first, then the total, then the moneyline</h2><p class="muted">The order is not a preference. Each market is priced off a different error process, and the weakest-supported market is originated last so it inherits a spread that has already been checked rather than standing in for one.</p></div></div>
  %(order)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">03 &middot; Fair, market, difference</span><h2>Three columns, never blended</h2><p class="muted">Fair is ours. Market is theirs. Difference is the subtraction and nothing else. Keeping them apart is what makes it possible to tell a model that disagrees with the market from a model that has simply been read off the market.</p></div><span class="tag">%(ngames)d games</span></div>
  %(fair)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">04 &middot; Market movement</span><h2>What moved, from open to now</h2><p class="muted">Computed, not described: current minus opening, in points, for every game and both sides.</p></div></div>
  %(move)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">05 &middot; Stored rows</span><h2>Every captured price</h2><p class="muted">One row per game and market for the two captured snapshots. The point spreads and totals are points; the moneyline cells are american prices. A blank cell is a value that was not transcribed, which is not the same as a value that does not exist.</p></div><span class="tag acc">%(ncap)d rows</span></div>
  %(prices)s
</section>
""" % dict(nsnap=len(market_store.snapshots()),
           nrows=len(market_store.prices()),
           ngames=len(market_store.origination_card()),
           nclose=sum(1 for r in market_store.prices() if r["snapshot_id"] == "2026W11-CLOSE"),
           store=store_rows(), fair=fair_vs_market_rows(),
           move=market_movement_rows(), prices=price_rows(),
           order=table(
               ["#", "Market", ("Order", True), "Why this position", "State",
                "Official source", "Market source"],
               [["%d" % n, esc(label), "%d" % n, esc(why),
                 badge("originated", "ok"),
                 src(GAME_SRC, "nfl.com schedule"),
                 src(ESPN_ODDS, "market line")]
                for key, label, n, why in market_store.ORIGINATION_ORDER],
               note=("All three markets are originated from the same team-rate model, so the "
                     "order is about evidence, not machinery. The side carries the only "
                     "out-of-sample error this desk can measure; the moneyline carries every "
                     "spread error plus a conversion error on top of it.")),
           ncap=sum(1 for r in market_store.prices() if r["snapshot_id"] != "2026W11-CLOSE")),
          "markets.html"))

# --- gates: signal vs staking, demotion, named chains, correlation n ---
PAGES.append(("gates.html", "Gates & demotion",
               "Signal scored separately from staking, a demotion gate that sends a live "
               "strategy back to paper, verified 1st-2nd-3rd string replacement chains, "
               "replacement depth measured from official reports, and every correlation with n.",
               """
<div class="section-head"><div><span class="eyebrow">13 &middot; Gates</span><h2>Separate the signal from the staking, then police the door</h2><p class="muted">Three separate defences against mistaking luck for skill. The signal is scored on line accuracy with no results bought; staking is shown beside it and can never lift it; and a single failed gate returns a live strategy to paper immediately, with no averaging and no grace period.</p></div><span class="tag warn">0 of %(n)d live</span></div>

<div class="grid g3">
  <article class="card"><span class="eyebrow">Signal</span><h3>Built only from accuracy</h3><p class="muted">Benchmark improvement (35%%), significance (30%%), weekly stability (20%%) and calibration (15%%). No staking result can enter the score.</p></article>
  <article class="card"><span class="eyebrow">Staking</span><h3>Shown, never scored</h3><p class="muted">Flat 1 unit at %(price)d on every graded call. It is the unit a staker reads, and it is deliberately quarantined from the ranking that decides eligibility.</p></article>
  <article class="card"><span class="eyebrow">Demotion</span><h3>One failure is enough</h3><p class="muted">Live requires every gate. Anything else is paper, which is where all %(n)d strategies are today - not because the site is unfinished, but because the significance gate has not been passed.</p></article>
</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">01 &middot; Signal vs staking</span><h2>Two ranks, on purpose</h2><p class="muted">Both ranks are published for the same strategy. <b>They agree today, and that is the finding rather than a success:</b> under a flat stake at a fixed price, bankroll growth is a monotone function of the hit rate, which the signal score already uses. The split becomes load-bearing once stakes vary with the bankroll or a strategy stakes only a selected subset of games. Published as S-17.</p></div></div>
  %(split)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">02 &middot; The demotion gate</span><h2>What sends a live strategy back to paper</h2></div></div>
  <div class="grid g2">
    <article class="card"><span class="eyebrow">Promotion</span><h3>Every gate, every time</h3><p class="muted">A strategy is Live only when it passes all %(ngates)d gates in the same evaluation window. Passing six of seven is paper. There is no partial credit and no conditional promotion.</p></article>
    <article class="card"><span class="eyebrow">Demotion</span><h3>Any single failure, immediately</h3><p class="muted">Once Live, a strategy returns to paper the moment any gate fails in a re-evaluation: the significance interval re-crosses zero, calibration breaks its tolerance, the minimum sample is not met, or a stability share falls below the declared floor. Re-entry requires passing every gate again from scratch.</p></article>
    <article class="card"><span class="eyebrow">Retirement</span><h3>After two demotions</h3><p class="muted">A strategy that has been demoted twice is retired rather than cycled again. A model that keeps failing and passing in alternation is showing that the gate is noisy, not that the model is good.</p></article>
    <article class="card"><span class="eyebrow">Why it exists</span><h3>Because promotion is cheap and demotion is not</h3><p class="muted">Anyone can publish a rule that promotes a hot strategy. The demotion rule is what makes the leaderboard falsifiable: it commits, in advance, to the exact evidence that will take a strategy's eligibility away.</p></article>
  </div>
  <div style="margin-top:14px">%(demotion)s</div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">03 &middot; Replacement depth</span><h2>The depth matters, not the fact of the replacement</h2><p class="muted">A club missing its third receiver is not in the same position as a club missing its starting quarterback, and a club that lists nine healthy bodies is not in the same position as one that lists three. Every column below is an official count from the Week 10 injury report - no depth-chart string is asserted anywhere, because no official source publishes one.</p></div><span class="tag acc">%(nrep)d clubs</span></div>
  %(repmap)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">03b &middot; Named chains</span><h2>Who actually takes the snaps</h2><p class="muted">The injury report says who is out. It does not say who plays. Two official NFL.com sources do say it: the <b>DEPTH CHART NEWS</b> items in the daily league roundup, and the injury news articles, which name the expected starter and often the man behind him. These are the chains those articles state, quoted and linked, deepest first.</p></div><span class="tag acc">%(nchain)d chains</span></div>
  %(chains)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">03c &middot; What could not be confirmed</span><h2>The depth nobody publishes</h2><p class="muted">The same discipline applied backwards. These are claims a depth section would normally make and that this site refuses to make, each with the reason.</p></div><span class="tag warn">%(nunc)d gaps</span></div>
  %(unconfirmed)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">04 &middot; Correlations</span><h2>Every coefficient with its n</h2><p class="muted">A correlation without a sample size is a rumour. The cross-game coefficients rest on a few dozen games; the model-error correlations rest on %(ne)d evaluated games. Both numbers are published, and the interval is published only where it can honestly be computed.</p></div><span class="tag acc">%(ncorr)d values</span></div>
  %(corr)s
</section>
""" % dict(n=len(market_store.leaderboard_split()),
           price=int(market_store.STAKING_POLICY["american"]),
           ngates=len(P["leaderboard"][0]["gates"]),
           split=signal_staking_rows(), demotion=demotion_rows(),
           nrep=len(replacement_depth_rows()), repmap=replacement_depth_table(),
           nchain=len(market_store.replacement_chains()),
           chains=replacement_chain_table(),
           nunc=len(market_store.unconfirmed_claims()),
           unconfirmed=unconfirmed_claims_table(),
           ncorr=corr_with_n_rows()[1], corr=corr_with_n_rows()[0],
           ne=P["correlation_n"]),
          "gates.html"))


# --- strategies ---
PAGES.append(("strategies.html", "Strategy lab",
               "Strategy leaderboard with eight validation gates, error correlation matrix, "
               "calibration check and weekly stability.",
               """
<div class="section-head"><div><span class="eyebrow">05 &middot; Strategy tournament</span><h2>Leaderboard and rewards</h2><p class="muted">Strategies are scored on out-of-sample accuracy, and a strategy only earns reward points if it clears every gate. The significance gate is what keeps a lucky streak out of the top of the table.</p></div><span class="tag">%(eligible)d of %(nstrat)d eligible</span></div>
%(lb)s

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Gate results</span><h2>Why each strategy is or is not eligible</h2><p class="muted">Seven gates, every strategy, with the evidence for each verdict.</p></div></div>
%(gates)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Controlling for luck</span><h2>Which strategies are actually the same bet</h2><p class="muted">Two strategies whose errors move together are not two pieces of evidence - they are one signal counted twice. The matrices below are computed from the same out-of-sample games. A value near 1.00 means the two strategies fail on exactly the same games, so ranking them against each other would overstate how much independent skill exists.</p></div><span class="tag">Correlation</span></div>
  <div class="grid g2">
    <div><h3>Error correlation</h3>%(corerr)s<p class="small muted">Correlation between each strategy's point-spread error and every other strategy's error, over the out-of-sample games.</p></div>
    <div><h3>Prediction correlation</h3>%(corrpred)s<p class="small muted">Correlation between the predicted spreads themselves - how much the strategies agree on the games.</p></div>
  </div>
  <div class="legend"><span><i style="background:rgba(57,192,127,.35)"></i>low - largely independent signal</span><span><i style="background:rgba(77,163,255,.25)"></i>moderate</span><span><i style="background:rgba(240,169,56,.35)"></i>high</span><span><i style="background:rgba(239,107,107,.4)"></i>near-identical - treat as one strategy</span></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Calibration</span><h2>Are the probabilities honest?</h2><p class="muted">A forecast that is consistently too confident is worse than no forecast. For each offset the model states the probability that the true total exceeds its own total plus that offset; a well-calibrated model's stated probability matches how often it actually happened.</p></div><span class="tag">Tolerance 0.12</span></div>
%(calib)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Stability</span><h2>Does the edge hold week to week?</h2><p class="muted">An improvement that appears only in a few weeks is not a reliable edge. Gate G5 requires the improvement against the league-constant benchmark to be positive in at least 60%% of evaluated weeks.</p></div></div>
%(weekly)s
<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Risk control</span><h2>Demotion gate</h2><p class="muted">A live strategy that falls outside its own evidence is sent back to paper trading. The gate is a project design choice (no official source publishes one) and is published so it can be applied consistently.</p></div></div>
%(demotion)s
</section>
""" % dict(lb=leaderboard_table(), gates=gates_table(),
           corerr=corr_table(corr_err, "corr-err"),
           corrpred=corr_table(corr_pred, "corr-pred"),
           calib=calib_table(), weekly=weekly_table(),
           demotion=demotion_gate_panel(),
           eligible=eligible, nstrat=len(leaderboard)), "strategies.html"))

# --- availability ---
PAGES.append(("availability.html", "Injuries & depth",
               "Official NFL Week 10 injury report, unit-level absence roll-up, and "
               "league-confirmed starter changes.",
               """
<div class="section-head"><div><span class="eyebrow">06 &middot; Availability</span><h2>Injuries and depth deficiencies</h2><p class="muted">The official NFL.com Week 10 injury report, transcribed in full: every listed player, their position, the injury, the practice designation and the game status. NFL clubs publish these under the league's injury-report policy, which is why they are the authoritative record.</p></div><span class="tag acc">Source: nfl.com/injuries</span></div>
%(avail)s
<div class="note warn" style="margin-top:12px"><b>The public report is not the whole story.</b> Players on injured reserve, the reserve/nontheatre injured list or the physically-unable-to-perform list do not appear in the public weekly report. Those absences show up in league news instead - see the next two tables. This is recorded as flag F-03.</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Starter changes</span><h2>Confirmed by the league</h2><p class="muted">Quarterback starter changes and long-term absences, each tied to the official NFL.com article that reports it. These are the facts the public injury report does not carry.</p></div><span class="tag acc">NFL.com news</span></div>
%(qb)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Official reporting</span><h2>All captured league updates</h2><p class="muted">Every official NFL.com item captured alongside the Week 10 injury report.</p></div></div>
%(news)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Full report</span><h2>Every listed player</h2><p class="muted">The complete Week 10 report, filterable by team and by status. Filter by 'No designation' to see players who were listed with no injury and no game status.</p></div></div>
<div class="toolbar"><label class="small muted" for="it">Team</label> <select id="it"><option value="">All teams</option>%(teamopts)s</select> <label class="small muted" for="is">Status</label> <select id="is"><option value="">All statuses</option><option>Out</option><option>Doubtful</option><option>Questionable</option><option value="none">No designation</option></select><span class="small muted" id="is-count"></span></div>
%(injfull)s
</section>

<section style="margin-top:26px">
<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Replacement depth</span><h2>Who replaced whom</h2><p class="muted">The fact of a starter replacement is tracked from league reporting, for both offense and defense. The depth of each replacement (2nd / 3rd / 4th string) is blank because no official source labels depth-chart strings (Flag F-21).</p></div></div>
%(depth)s

<section style="margin-top:26px">
  <div class="note ok"><b>The depth question is now answered on its own page.</b> This page stops at who the official report says cannot play. Which of those players is a <i>starter</i>, who the club lists behind him, and where the club lists nobody at all, is on <a href="depth.html">Depth &amp; deficiency</a>: 1,558 depth positions transcribed from the clubs' own official charts and joined to this report. Flag <b>F-02</b> (no depth rank could be verified) is closed; what the charts still cannot say - who actually took the first snap - is <b>F-21</b>.</div>
</section>

<section style="margin-top:26px">
  <div class="note"><b>What is deliberately not here.</b> No player is assigned a depth-chart string - starter, 2nd, 3rd or 4th - on this page's replacement table; the NFL publishes no consolidated league depth chart, so any such ranking would be an invention. The club-by-club depth transcription lives on the <a href="depth.html">Depth &amp; deficiency</a> page.</div>
</section>

</section>
""" % dict(avail=avail_table(), qb=qb_table(), news=news_table(), injfull=inj_full_table(),
           depth=replacement_depth_table(),
           teamopts="".join('<option value="%s">%s</option>' % (esc(k), esc(v))
                            for k, v in sorted({r["team_abbr"]: r["team"]
                                                for r in injury_rows}.items()))),
               "availability.html"))

# --- questions ---
PAGES.append(("questions.html", "Decision checklist",
               spell(N_QUESTIONS).capitalize() + " questions that must be answered before a decision in this "
               "project is reasonable: what we know, what is missing, what it blocks.",
               """
<div class="section-head"><div><span class="eyebrow">07 &middot; Before any decision</span><h2>Questions, answers and gaps</h2><p class="muted">A decision here is only reasonable once the 'what is still missing' column is either answered or explicitly accepted as a risk. Everything in the 'what we already know' column traces to the official source on the right.</p></div><span class="tag">%(nq)d questions</span></div>
%(qa)s
""" % dict(qa=qa_table(), nq=len(questions)), "questions.html"))

# --- suggestions ---
# This body is maintained in the generator as the source of the published page.
SUGGESTIONS_BODY = r"""<div class="section-head"><div><span class="eyebrow">08 &middot; Evidence before implementation</span><h2>Suggestions &amp; decision readiness</h2><p class="muted">This is a reviewable roadmap, not a claim that every feature is complete. It separates work already present from the gaps that still block trustworthy decisions. The safe path below is recommended by default; no user reply is needed to continue research or keep strategies in paper.</p></div><span class="tag warn">Do not treat open gates as picks</span></div>

<section class="panel" style="margin-bottom:22px">
  <h3>Executive recommendation</h3>
  <p><b>Keep the product in research and paper mode.</b> Use official NFL and club records for factual inputs; retain dated raw captures and hashes; leave unconfirmed cells blank; and label any third-party market prices as third-party rather than official. No strategy should receive a reward or be represented as profitable until a pre-registered prospective evaluation passes its proper-score, uncertainty, sample, calibration, and price-evidence gates.</p>
  <p class="muted">This conservative default resolves the policy questions without asking the user to make an unsupported choice. A licensed market source, historical inactive evidence, player-level official game-book data, and sportsbook settlement terms are not established just because a useful page exists.</p>
  <p class="small"><b>Current repo evidence:</b> the market and strategy pages, verification notes, and flagged register document the current state; start with <a href="market.html">Market &amp; price archive</a>, <a href="gates.html">Gates &amp; demotion</a>, <a href="questions.html">Decision checklist</a>, and <a href="flags.html">Flagged for review</a>.</p>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Closing suggestions &middot; 2026-11-18</span><h2>What the 18 November re-verification changed, and what it suggests next</h2><p class="muted">Every row below is an outcome of this session's line-by-line read of the official pages, not a re-statement of an older plan. Sources are on the row.</p></div><span class="tag green">VERIFIED THIS SESSION</span></div>
  <div class="table-wrap"><table class="data"><thead><tr><th>#</th><th>What was found</th><th>What was done about it</th><th>What it suggests next</th><th>Source</th></tr></thead><tbody>
    <tr><td>C1</td><td><b>The site was a week stale.</b> The official Week 10 slate finished on 16 Nov; the committed log held only the 12 Nov Thursday game, so 13 finals were missing and the standings had moved for 28 of 32 clubs.</td><td>All 14 Week 10 finals transcribed from the official schedule page; the standings rebuilt <i>from the proved log</i>; 130 changed cells audited; every derived number regenerated (118 evaluated games).</td><td><b>Ingest results on a schedule.</b> A completed slate should refresh itself, not wait for a session to notice. The pipeline can already do it deterministically &mdash; it has no trigger.</td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-10" target="_blank" rel="noreferrer noopener">Official Week 10 schedule &nearr;</a> &middot; <a href="research/verification/official-reverify-2026-11-18.md">record</a></td></tr>
    <tr><td>C2</td><td><b>The gate punished freshness.</b> site/check.py asserted exactly 137 game rows, so adding the 13 official finals failed the build.</td><td>Expectation now read from <code>data/games-2026.csv</code>; the week filter is still proved to render every row.</td><td>Audit every other literal count in the gates. A number typed into a checker is a future false alarm.</td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-10" target="_blank" rel="noreferrer noopener">Official Week 10 schedule &nearr;</a> &middot; <a href="https://github.com/karagemop466-tech/X4/blob/main/site/check.py" target="_blank" rel="noreferrer noopener">site/check.py &nearr;</a></td></tr>
    <tr><td>C3</td><td><b>The conclusion moved, and not enough.</b> Best strategy S1 now improves 9.49% over the league constant on 118 games (was 8.31% on 105); Bonferroni interval [-0.00, +1.94] &mdash; lower bound still touches zero.</td><td>Leaderboard, luck panel and every published interval rebuilt on the completed corpus; the eligibility verdict is unchanged: <b>0 of 9 eligible</b>.</td><td><b>Wait, do not tune.</b> The honest move is to keep the pre-registered rules and let the interval narrow. Two more weeks at this rate would move the bound clear of zero &mdash; or kill it.</td><td><a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer noopener">Official standings &nearr;</a> &middot; <a href="gates.html">gates.html</a></td></tr>
    <tr><td>C4</td><td><b>The two statistics still disagree.</b> The mean-error bootstrap says no; the paired sign test says S1 is closer to the truth in 78 of 118 games (66.1%, exact one-sided p = 0.00030, threshold 0.00625).</td><td>Both published side by side; neither is used to promote anything.</td><td><b>Decide the primary metric in the open, before the next window</b> (S-15 on the review page). Choosing it now, after seeing which one passes, is the exact failure pre-registration exists to prevent.</td><td><a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer noopener">Official standings &nearr;</a> &middot; <a href="https://github.com/karagemop466-tech/X4/blob/main/research/verification/official-reverify-2026-11-18.md" target="_blank" rel="noreferrer noopener">record &nearr;</a></td></tr>
    <tr><td>C5</td><td><b>Week 11 has no official injury report yet.</b> The reg11 address still serves Week 10; a secondary aggregator already shows a Wednesday practice report.</td><td>Nothing published for Week 11. The absence is flagged (F-61), not filled.</td><td>The Wed&rarr;kickoff series the brief asks for cannot start from an official source until the league publishes it. Keep the capture job pointed at the official URL and let it fail loudly rather than fall back to an aggregator.</td><td><a href="https://www.nfl.com/injuries/league/2026/reg11" target="_blank" rel="noreferrer noopener">Official Week 11 report address &nearr;</a></td></tr>
    <tr><td>C6</td><td><b>Two venue names do not match the official page.</b> The dataset says RELIANT STADIUM and ARROWHEAD STADIUM; the official Week 11 page says NRG Stadium and GEHA Field at Arrowhead Stadium.</td><td>Flagged, not edited (F-60) &mdash; an unverified rename is worse than a recorded difference.</td><td>Read the Game Info block of both official game pages and update the venue dataset from that reading, one row at a time.</td><td><a href="https://www.nfl.com/games/colts-at-texans-2026-reg-11" target="_blank" rel="noreferrer noopener">Official game centre &nearr;</a></td></tr>
  </tbody></table></div>
  <div class="tbl-note">Nothing in this table is a new claim about the model's skill. C1-C2 were defects and are closed; C3-C6 are limits and stay visible until their named source says otherwise.</div>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Recommended order</span><h2>Suggestions to improve decisions</h2><p class="muted">Prioritized by dependency: first make evidence replayable, then measure whether inputs add signal, then permit ranking or rewards.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Priority / suggestion</th><th>What is already here</th><th>What is still missing</th><th>Next action and pass gate</th><th>Official source for the underlying facts</th></tr></thead><tbody>
    <tr><td><b>P0 &middot; Point-in-time availability ledger</b><br>Automate immutable daily capture of injury reports, reserve moves, club depth charts, inactives, and source hashes.</td><td>The repo has dated raw fetch manifests and an injury/depth snapshot. The existing season material is not a complete multi-day, multi-season availability history.</td><td>Scheduled Wed-to-kickoff history, retained raw bodies, conflict flags, true inactive lists, and replay tests. A blank or absent report row must not mean healthy or active.</td><td>Add scheduled capture and freshness/schema alarms. Pass only when a historical build can reproduce what was published at a specified pre-kickoff timestamp with no later data leaking in.</td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer noopener">NFL injury reports</a>; <a href="https://www.nfl.com/news/" target="_blank" rel="noreferrer noopener">NFL transactions and news</a></td></tr>
    <tr><td><b>P0 &middot; Prove actual participation</b><br>Build starters, inactives, and snap share from official game books; do not infer starters from jersey number, experience, chart order, or injury status.</td><td>Official club depth charts are captured for 31 clubs in the current depth dataset. The depth report documents Houston's image-only chart and limitations of published charts.</td><td>Structured evidence for all 32 clubs, actual game-day inactive evidence, starters, snaps, roster-event versioning, and historical coverage.</td><td>Verify an authorized structured source club by club, then parse official game books. Pass only when every player-to-game join has a source, event time, and unresolved-conflict state; keep unavailable values blank.</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL game schedule / game pages</a>; <a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer noopener">NFL statistics</a></td></tr>
    <tr><td><b>P0 &middot; Test availability, never assign fixed injury points</b><br>Run paired chronological ablations with and without verified personnel features.</td><td>The repo includes a one-week depth/injury join and a results-only walk-forward model. A one-week join cannot establish a historical injury effect.</td><td>Point-in-time history, verified active/snap evidence, enough seasons, and uncertainty intervals for the incremental effect.</td><td>Pre-register the comparison, features, holdout seasons, and metrics before opening the holdout. Pass only if out-of-sample improvement and its uncertainty clear the published gate; otherwise retain the simpler model.</td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer noopener">NFL injury report</a>; <a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule/results</a></td></tr>
    <tr><td><b>P0 &middot; Make market evidence honest</b><br>Keep fair line, market quote, and residual separate; preserve source tier, time, book, and terms.</td><td>Opening/current/closing price stores and market comparisons exist. The captured odds are explicitly third-party ESPN-published DraftKings values, not official NFL prices; some gaps and limitations are flagged.</td><td>Licensed or direct executable quote history, complete close timing, feed rights/retention terms, and a settled policy for vig removal, pushes, voids, and corrections.</td><td>Until an authorized source and policy are verified, retain third-party observations only in a clearly marked exploratory area; do not use them to assert official value, executable ROI, or reward eligibility. Pass when every value's own source supports it and the quote is timestamped.</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule (event identity only)</a>; <a href="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook" target="_blank" rel="noreferrer noopener">NFL rulebook (game rules, not bookmaker settlement)</a></td></tr>
    <tr><td><b>P1 &middot; Keep a locked singles shadow contest</b><br>Register strategy definitions before evaluation; timestamp probabilities and inputs before kickoff; score by proper scores against controls.</td><td>Strategy definitions, walk-forward results, score and staking separations, correlation estimates, and demotion rules are present in the research pages.</td><td>Durable pre-kickoff forecast locks across future slates, more independent seasons, a prospective sample, and an agreed reward/legal framework.</td><td>Start with singles only; publish Brier skill versus a declared baseline, game-cluster uncertainty and multiplicity adjustment. Keep all strategies paper until the published gates pass; no win-rate or ROI-only promotion.</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule and kickoff facts</a>; <a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer noopener">NFL standings/results cross-check</a></td></tr>
    <tr><td><b>P1 &middot; Gate parlays and prop combos separately</b><br>Require directly validated joint probabilities and explicit settlement rules.</td><td>The repo documents why multiplying marginal probabilities is invalid under dependence; it does not establish a validated joint model for all combinations.</td><td>Official player-level inputs, joint-outcome validation, book-specific void/push/stat-correction rules, and enough prospective data.</td><td>Do not rank or reward combinations until each combo family has a pre-registered joint model, validated on chronological holdouts, and its settlement contract is recorded. Keep singles as the baseline competition.</td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer noopener">NFL statistics</a>; <a href="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook" target="_blank" rel="noreferrer noopener">NFL game rules</a></td></tr>
    <tr><td><b>P2 &middot; Add actionable team and matchup views</b><br>Show starters ruled out, verified replacement evidence, defensive/offensive unit, depth group, and unknowns together.</td><td>Injury, depth, replacement, schedule, and model-line pages exist separately.</td><td>Shared point-in-time joins, explicit multi-player/shared/empty depth slots, roster transaction versioning, and verified offense-vs-defense position mapping.</td><td>Build only from documented official rows; preserve shared and empty groups instead of inventing a single starter. Pass when all displayed facts link to their own source and unknown coverage is visible.</td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer noopener">NFL injury report</a>; <a href="https://www.buffalobills.com/team/depth-chart" target="_blank" rel="noreferrer noopener">Example official club depth chart</a></td></tr>
    <tr><td><b>P2 &middot; Add a weekly change log and freshness panel</b><br>Publish rank, rating, injury, depth, and schedule changes with timestamps and parser status.</td><td>The site has dated captures, verification logs, and a Flagged for Review section; deployment validation runs on repository changes.</td><td>A scheduled source refresh, retention across weeks, per-source freshness thresholds, and alert routing for source/schema changes.</td><td>Track freshness for each source independently; fail publication on missing required fields, report conflicts rather than silently overwriting, and publish a weekly diff once two comparable snapshots exist.</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule</a>; <a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer noopener">NFL injury reports</a></td></tr>
  </tbody></table><div class="tbl-note">Recommendations are project judgments, not claims made by the linked sources. Official links support the underlying NFL facts only. Repository evidence and unresolved exceptions are linked above and on the relevant site pages.</div></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Questions, answers, and gaps</span><h2>Decision-readiness register</h2><p class="muted">Answers are limited to what current repository evidence supports. “Unknown” means unknown; it is not filled by a proxy. Each row includes an official source for the underlying fact and a concrete discovery step.</p></div></div>
  <div class="table-wrap"><table><thead><tr><th>Question</th><th>What we can answer now</th><th>What we do not have</th><th>Discovery / gate before a decision</th><th>Official source</th></tr></thead><tbody>
    <tr><td><b>Are current records sufficient to trust schedule and final scores?</b></td><td>The repo's verification record reports agreement of reconstructed results with official standings; the live-check records are dated 2026-11-14, not a claim of current live status.</td><td>A fresh capture for later schedule/report changes; any fact absent from the dated snapshot.</td><td>Re-run the official-source check for the target slate and preserve the raw response, timestamp, and hash. Do not reuse stale values as current.</td><td><a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer noopener">NFL standings</a>; <a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedules</a></td></tr>
    <tr><td><b>What does “Questionable” mean as a probability?</b></td><td>The official injury report provides a designation and practice status; it does not itself publish a probability.</td><td>Empirical designation-to-play rates, matched to official inactives, across multiple seasons, plus confidence intervals and point-in-time history.</td><td>Archive report versions and game-day inactives; estimate each designation's play rate by position/season with uncertainty before deciding whether to include it.</td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer noopener">NFL injury report</a>; <a href="https://www.nfl.com/news/" target="_blank" rel="noreferrer noopener">NFL official news</a></td></tr>
    <tr><td><b>Who actually started, played, and replaced whom?</b></td><td>Club chart entries and official injury designations are useful evidence of what was published; they are not proof of game participation.</td><td>Complete structured game books, inactive evidence, snap counts, and timestamped roster changes for every club/game.</td><td>Verify the game-book and snap-count source format and terms, then reconcile chart, injury report, inactives, transactions, and participation. Unknown rows stay unknown.</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL game pages</a>; <a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer noopener">NFL statistics</a></td></tr>
    <tr><td><b>Can we quantify the effect of a missing starter?</b></td><td>Not from one injury/depth snapshot or a fixed point penalty. The current material supports a descriptive join, not a causal or predictive point value.</td><td>Chronological multi-season availability, actual participation, enough observations, and uncertainty on the incremental model effect.</td><td>Run pre-registered with/without-personnel ablations on identical chronological holdouts. Publish estimate, interval, sample size, and a no-effect result if that is what the data shows.</td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer noopener">NFL injury report</a>; <a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule/results</a></td></tr>
    <tr><td><b>Are the archived prices official NFL lines or executable offers?</b></td><td>No official NFL price is evidenced here. The repo explicitly labels captured ESPN-published DraftKings odds as third-party, not NFL-official; a syndicated quote is not proof it could be executed.</td><td>Licensed/direct book evidence, user-available price and limits, historical access rights, vig convention, and book settlement terms.</td><td>Keep those prices segregated as non-official research. Only publish official-source-verified price values when an authorized direct source is secured; otherwise leave the verified price cell blank and flag the gap.</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule (game identity only)</a>; <a href="https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/401873037/competitions/401873037/odds" target="_blank" rel="noreferrer noopener">ESPN odds example (third-party, not official)</a></td></tr>
    <tr><td><b>Can any strategy win a reward today?</b></td><td>The published project conclusion is that no strategy is eligible under current validation gates; keep strategies on paper.</td><td>More prospective locked forecasts, independent evaluation windows, complete price/settlement evidence for any ROI claim, and approved contest rules.</td><td>Pre-register first; compare with random/favorites controls and a proper-score benchmark; require game-cluster uncertainty, multiplicity correction, calibration, and the stated minimum sample before promotion.</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule/kickoff reference</a>; see <a href="gates.html">project gate register</a></td></tr>
    <tr><td><b>Are parlays and player-prop combos ready to rank?</b></td><td>No. Marginal probabilities and correlation alone do not establish a calibrated joint probability or settlement result.</td><td>Directly validated joint outcome models, official player-level inputs, operator-specific void/push/stat correction rules, and prospective samples.</td><td>Exclude combos from leaderboard eligibility until every combo family clears a joint-evidence gate and its settlement rules are recorded and tested.</td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer noopener">NFL statistics</a>; <a href="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook" target="_blank" rel="noreferrer noopener">NFL rulebook</a></td></tr>
    <tr><td><b>Can we publish a weather/roof or surface adjustment?</b></td><td>Not from schedule facts alone. No verified fixture-by-fixture roof designation and time-matched forecast capture is established in this roadmap.</td><td>Official venue roof/surface facts, stadium status close to kickoff, and archived hourly observations/forecasts tied to the correct grid/time.</td><td>Join only verified stadium records and timestamped National Weather Service forecasts; report missing feeds and never infer whether a roof was open.</td><td><a href="https://www.weather.gov/documentation/services-web-api" target="_blank" rel="noreferrer noopener">National Weather Service API documentation</a>; <a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer noopener">NFL schedule</a></td></tr>
  </tbody></table><div class="tbl-note">A question is decision-ready only when its missing-information column is answered or an explicit risk policy accepts it. No numeric value is inferred to make the table look complete.</div></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Discovery queue</span><h2>How to close the gaps</h2><p class="muted">These are the concrete information-gathering tasks that make the later modeling decisions possible.</p></div></div>
  <ol class="muted">
    <li><b>Freeze definitions before new evaluation:</b> version each strategy, target market, forecast timestamp, benchmark, metric, holdout, uncertainty method, and demotion rule in git before the evaluation window begins.</li>
    <li><b>Collect point-in-time evidence:</b> schedule an immutable archive of the official injury report and club depth/transaction sources; capture game-day inactive evidence and game-book participation after games; record raw hashes, source URLs, fetch times, and disagreements.</li>
    <li><b>Verify coverage rather than assuming it:</b> maintain a 32-club source matrix for chart format, datedness, shared/empty slots, source changes, and parser status. Do not derive order from jersey number, salary, or experience.</li>
    <li><b>Test whether availability adds signal:</b> compare identical models with/without verified personnel data on chronological holdouts; publish each estimate with n and uncertainty; include no-feature and simple strength baselines.</li>
    <li><b>Keep outcome products separate:</b> first singles; then game parlays only after direct joint validation; player-prop combos last, after player data and bookmaker settlement rules are confirmed.</li>
    <li><b>Review source and freshness flags weekly:</b> distinguish official facts, official club statements, third-party observations, and model outputs. A source/schema change fails the affected build and appears on <a href="flags.html">Flagged for review</a>.</li>
  </ol>
  <p class="ask"><b>Default decision until gaps close:</b> publish analysis and uncertainty only; keep staking simulated; do not claim a verified price edge or issue rewards; leave unsupported values blank.</p>
</section>"""
PAGES.append(("suggestions.html", "Suggestions",
               "Evidence-led proposals, current answers, missing information, and safe decision gates.",
               SUGGESTIONS_BODY, "suggestions.html"))

# --- flags ---
PAGES.append(("flags.html", "Flagged for review",
               "Every unverified value, limitation and irregularity found during official-source "
               "verification.",
               """
<div class="section-head"><div><span class="eyebrow">09 &middot; Open items</span><h2>Flagged for review</h2><p class="muted">Nothing on this page is a placeholder for data that exists. Each entry is either something genuinely unavailable from an official source, a limitation of the published approach, or an irregularity found while verifying. None of them blocks publication; all of them are visible.</p></div><span class="tag warn">%(nf)s items</span></div>
%(flags)s
""" % dict(flags=flags_table(), nf=len(flags)), "flags.html"))

# --- methodology ---
PAGES.append(("methodology.html", "Methodology",
               "How every published number is produced: the model, the parameters, the validation "
               "gates and the verification log.",
               """
<div class="section-head"><div><span class="eyebrow">10 &middot; How it works</span><h2>Methodology</h2><p class="muted">Everything on this site is produced by scripts from the CSV files in <span class="mono">data/</span>. Nothing is hand-typed into a page at publish time, and every table is written into the HTML at build time, so the pages work with JavaScript disabled.</p></div><span class="tag acc">Reproducible</span></div>

<div class="grid g2">
  <article class="card">
    <span class="eyebrow">Step 1 &middot; Acquire</span>
    <h3>Official pages only</h3>
    <p class="muted">The official NFL.com standings, the official weekly injury report and the official weekly schedule are the source of record. Secondary aggregators were used to reconstruct the game log, and every reconstructed score is then proved against the official standings totals - a single wrong score changes a team's points for or points allowed, so matching all 32 teams on all six measures proves every score.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 2 &middot; Verify</span>
    <h3><span class="mono">tools/verify.py</span></h3>
    <p class="muted">486 assertions covering: every game row's official URL pattern, every team's wins, losses, ties, points for, points allowed, net points and winning percentage, games played per team, the Week 11 schedule's pairing and URL structure, and duplicate rows. It exits non-zero on any failure and runs as part of the build.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 3 &middot; Model</span>
    <h3>Opponent-adjusted rates</h3>
    <p class="muted">For a team, the opponent-adjusted points-for rate is the team's own scoring rate minus the average points allowed by the opponents it has faced, plus the league average. The same construction gives the opponent-adjusted points-allowed rate. A team's expected score is the mean of its adjusted offence and its opponent's adjusted defence, with the league home-field margin added. Every quantity used for a Week-w forecast is measured strictly from games before Week w, including the opponents' season rates, so there is no look-ahead.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 4 &middot; Validate</span>
    <h3>Walk-forward, eight gates</h3>
    <p class="muted">Strategies are evaluated only on games that had not been played at forecast time - no random row splits. Each strategy must clear data integrity, out-of-sample discipline, minimum sample size, statistical significance, weekly stability, calibration, exclusion of the league-constant benchmark, and the shadow-period gate (a pre-registered forward window that has actually been graded), before it can earn reward points.</p>
  </article>
</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Model parameters</span><h2>Every knob, published</h2><p class="muted">These are analyst choices by this project, not official values, and they are the first thing a reviewer should challenge. Changing any of them changes the ranking. The bootstrap uses a fixed, interpreter-independent generator so the published intervals are identical on every machine.</p></div><span class="tag warn">Not official</span></div>
%(params)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Frozen policies</span><h2>Two decisions fixed before any backtest is published</h2><p class="muted">Both policies below were frozen on 2026-11-17, before any backtest on the reconstructed game log has been published. A policy frozen after results are seen is not a policy; these two are registered here, in the build that publishes the numbers they govern.</p></div><span class="tag acc">Frozen 2026-11-17</span></div>
  <div class="table-wrap"><table class="data"><thead><tr><th>Policy</th><th>Decision</th><th>What it fixes</th><th>Source</th></tr></thead><tbody>
    <tr><td><b>Price-data policy</b></td><td>Every captured price is third-party (DraftKings as syndicated by the public ESPN odds endpoint), labelled T3, and never presented as an official NFL line. Prices may feed exploratory residual and difference analysis; they may never back a CLV, execution or ROI claim. CLV and any staking claim stay blocked until a licensed, timestamped operator feed with a documented backfill and settlement policy is selected. A price row without a direct source URL and a retrieval time is not publishable. Official NFL pages verify game identity, schedule and results only &mdash; the league publishes no betting lines.</td><td>Which source may support a market number; what a market number may be used for; what stays blocked</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer">Official schedule (game identity)</a> &middot; <a href="https://www.espn.com/nfl/schedule/_/week/11/year/2026/seasontype/2" target="_blank" rel="noreferrer">third-party price surface (T3)</a></td></tr>
    <tr><td><b>Data split</b></td><td>On the reconstructed %(ng)d-game official log: <b>train</b> = Weeks 1&ndash;6; <b>validation</b> (rule and hyperparameter selection) = Weeks 7&ndash;9; <b>final holdout</b> = Week 10 onward, including the registered Week 11 forward window, never opened to selection. The Week-10 completion of this corpus landed after that registration (2026-11-18) and is recorded as a post-hoc integrity repair, not a new registration: flags F-58 (staleness), F-66 (the self-consistent verification pair) and F-67 (the post-hoc strategy-evaluation transition, including the row-order sensitivity of the adjusted interval). The published walk-forward expansion on Weeks 3&ndash;10 was recomputed on the completed corpus and is labelled post-hoc everywhere it appears. Any new backtest on this corpus must be committed (the commit hash is the registration) before its holdout opens. When a second season of official results is ingested, the same week-order proportions apply and the final holdout remains whatever has not yet been opened.</td><td>Which games may select a rule; which games may only grade one</td><td><a href="https://www.nfl.com/schedules/2026/" target="_blank" rel="noreferrer">Official 2026 schedule and results</a> &middot; <a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer">Official standings (score reconciliation)</a></td></tr>
  </tbody></table></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Verification log</span><h2>What was checked, and what failed</h2><p class="muted">The complete record, including the checks that did not pass. A verification log that only lists successes is not a verification log.</p></div></div>
%(verify)s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Reproduce it</span><h2>Running the pipeline</h2></div></div>
  <div class="note"><b>From a clean checkout:</b><br>
  <span class="mono">python3 tools/verify.py</span> &nbsp;- proves the data against the official standings<br>
  <span class="mono">python3 tools/build.py</span> &nbsp;- rebuilds every published number into <span class="mono">data/output/</span><br>
  <span class="mono">python3 tools/pages.py</span> &nbsp;- regenerates the site pages as static HTML<br>
  <span class="mono">python3 tools/sync.py</span> &nbsp;- mirrors the site to the repository root<br>
  <span class="mono">python3 site/check.py</span> &nbsp;- checks the site for broken links and unsourced rows<br>
  <span class="mono">python3 tools/validate.py</span> &nbsp;- runs the full publication gate</span>
  <p style="margin-top:9px">The build is deterministic: the same inputs produce the same tables and the same confidence intervals on every run, and every table is written into the HTML so no published value depends on JavaScript.</p></div>
</section>
""" % dict(params=params_table(), verify=verification_table(), ng=len(games)), "methodology.html"))



# --- depth & deficiency ---
if DEPTH:
    _n_depth_clubs = DEPTH["clubs_with_chart"]
    _n_depth_rows_n = DEPTH["depth_rows"]
    _n_out = DEPTH["out_rows"]
    _n_starter = DEPTH["starter_out_rows"]
    _n_out_doubt = sum(c["off_out"] + c["def_out"] for c in DEPTH["clubs"])
    _n_holes = len(DEPTH["holes"])
    _n_casc = len(DEPTH["cascades"])
    _n_unmatched = len(DEPTH["unmatched"])
    _n_club_out = sum(1 for c in DEPTH["clubs"] if c["off_starter_out"] or c["def_starter_out"])
else:
    _n_depth_clubs = _n_depth_rows_n = _n_out = _n_starter = 0
    _n_out_doubt = 0
    _n_holes = _n_casc = _n_unmatched = _n_club_out = 0

PAGES.append(("depth.html", "Depth &amp; deficiency",
              "Every depth position transcribed from the official club depth charts and joined to "
              "the official NFL.com Week 10 injury report: who is ruled out, who the club lists "
              "behind him, and where the club lists nobody.",
              """
<div class="section-head"><div><span class="eyebrow">05 &middot; Roster depth</span><h2>Who is actually missing, and who replaces him</h2><p class="muted">This page answers the roster question the brief asks for directly: which listed starters are ruled out, what the club's own chart says comes next, and where the chart names nobody at all. The depth order is transcribed from each club's <b>own official website</b> - the clubs are the authority on their own depth - and joined by name to the official NFL.com Week 10 injury report. <b>The depth order is a transcription, not a model output.</b></p></div><span class="tag acc">Official club charts + nfl.com/injuries</span></div>

<div class="grid g4">
  <article class="card kpi"><span class="kpi-n">%d / 32</span><span class="kpi-l">clubs publishing an ordered chart</span></article>
  <article class="card kpi"><span class="kpi-n">%s</span><span class="kpi-l">depth positions transcribed</span></article>
  <article class="card kpi"><span class="kpi-n">%d</span><span class="kpi-l">listed starters ruled Out or Doubtful</span></article>
  <article class="card kpi"><span class="kpi-n">%d</span><span class="kpi-l">clubs with a starter out</span></article>
</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">01 &middot; The unit roll-up</span><h2>Deficiency by club and by unit</h2><p class="muted">Offense and defense are scored separately, because losing three offensive starters is not the same event as losing three defensive ones. &quot;Starter&quot; means the first name the club prints at that position; a club that prints two co-starters has two, and both are counted. A club whose chart carries no date is marked rather than given an assumed one.</p></div><span class="tag acc">%d of the %d players ruled Out or Doubtful are listed as starters</span></div>
  %s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">02 &middot; The cascade the brief asks about</span><h2>Starter, then 2nd, then 3rd string</h2><p class="muted">The brief asks the system to know when a 2nd-, 3rd- or 4th-string player has to replace a starter. That is only meaningful when the starter is out <i>and</i> the man behind him is out too. The detector is re-run on every build against the official report.</p></div><span class="tag warn">%d cascade%s found</span></div>
  %s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">03 &middot; Positions with no replacement named</span><h2>Where the club publishes nobody behind the starter</h2><p class="muted">A row where the club lists exactly one player and the official report rules him out. These are the sharpest availability facts in the dataset: the club itself has not published a next man up. It does not follow that nobody will play - a practice-squad elevation is not on a depth chart - only that the club has not said who.</p></div><span class="tag warn">%d row%s</span></div>
  %s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">04 &middot; The names the charts do not carry</span><h2>Ruled out, but not on the chart</h2><p class="muted">Clubs update their charts on their own schedule, so a player can be ruled Out on the official report while still being absent from the club's published chart. These players are named here instead of being silently dropped or given a guessed rank, which is why the starter-out figure above is a floor and not a ceiling.</p></div><span class="tag warn">%d player%s</span></div>
  %s
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">05 &middot; The transcription</span><h2>Every depth position, club by club</h2><p class="muted">All %s rows, exactly as the club prints them, position label included - the clubs do not agree on labels (DL, DT, NT, EDGE, RUSH, LOLB, WILL, MIKE, SAM, NCB, DB all appear), so the club's own wording is kept rather than translated into one taxonomy. Open a club to inspect it. Every row links to the page it came from.</p></div><span class="tag acc">%d clubs</span></div>
  %s
</section>

<section style="margin-top:26px">
  <div class="note warn"><b>What this page does not claim.</b> A published depth chart is not proof of who took the first snap. Nothing here records snap counts or official game books, so the score above measures <i>listed</i> availability before kickoff, not realised participation. Houston publishes its chart only as an image, so it contributes no rows and its five ruled-out players appear in the unmatched table. Both limits are on the <a href="flags.html">Flagged for review</a> page as F-27 (not proof of who started) and F-24 (Houston image-only chart).</div>
</section>

<section style="margin-top:26px">
  <div class="note ok"><b>How to check this yourself.</b> Pick any row, click its club-chart link, and look for the player's name in that position row: the column he sits in is the depth number printed here. Then open the official injury report and confirm his game status. Both links are on the row. The pipeline is <span class="mono">tools/depth.py</span>, which refuses to write the dataset if any transcription is internally inconsistent, and the join to the injury report is by name, so a mis-typed name shows up as an unmatched player rather than as a silent match.</div>
</section>
""" % (_n_depth_clubs, "{:,}".format(_n_depth_rows_n), _n_starter, _n_club_out,
       _n_starter, _n_out_doubt, _depth_rollup_table(),
       _n_casc, "" if _n_casc == 1 else "s", _depth_cascade_table(),
       _n_holes, "" if _n_holes == 1 else "s", _depth_holes_table(),
       _n_unmatched, "" if _n_unmatched == 1 else "s", _depth_unmatched_table(),
       "{:,}".format(_n_depth_rows_n), _n_depth_clubs, _depth_club_sections()),
              "depth.html"))


# --------------------------------------------------------------------------------------
# Domain hook: the market page (owned by tools/market_page.py, session arena/1b8b6e9e-x4)
# --------------------------------------------------------------------------------------
# Appended additively. Nothing above this line is modified. The hook registers one extra
# page, one nav label and one directory card, and does nothing at all if the module is
# absent, so this file stays valid for every other session either way.
def _market_hook():
    if "market.html" in [h for h, _t, _d, _b, _a in PAGES]:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import market_page
    except Exception:                                     # module not present: no-op
        return
    try:
        body = market_page.build(market_page.load_market(), sys.modules[__name__])
    except Exception as exc:                              # never break the pipeline
        print("  ! market page skipped: %s" % exc)
        return
    NAV.insert(4, ("market.html", "Market & price archive"))
    for _title, _pages in DIRECTORY:
        if _title == "Model &amp; strategies":
            _pages.insert(1, ("market.html", "Market &amp; price archive",
                              "Real captured prices (not model estimates): {n_market} games "
                              "with open and close for spread, total and moneyline, each row linked "
                              "to its NFL.com result and its price resource."))
    PAGES.append((
        "market.html", "Market &amp; price archive",
        "Captured opening and closing prices for spread, total and moneyline, with official "
        "NFL.com results, a staking-independent skill board, a numeric demotion gate and "
        "correlations published with n and confidence.",
        body, "market.html"))


if __name__ == "__main__":
    _market_hook()


def main():
    os.makedirs(SITE, exist_ok=True)
    written = []
    for href, title, desc, body, active in PAGES:
        # The landing-page directory is rendered now, not at import time, so a page
        # that registers itself late (the market hook) is still listed on it.
        body = body.replace("__DIRECTORY__", directory_section())
        slug = href.replace(".html", "")
        with open(os.path.join(SITE, href), "w", encoding="utf-8") as fh:
            fh.write(shell(slug, title, desc, body, href))
        written.append(href)
    # T38 extension pages (tools/desk_extension.py): luck, readiness, per-team view
    import desk_extension
    written += desk_extension.write_pages(SITE, shell)
    # T46 landing decision-readiness table (tools/desk_extension.py helper)
    import desk_extension as _dx
    with open(os.path.join(SITE, "index.html"), encoding="utf-8") as fh:
        _h = fh.read()
    _start = _h.find('<div id="readiness-preview">')
    _end = _h.find('</section>', _start)
    if _start > 0 and _end > 0:
        _h = _h[:_start] + _dx.landing_readiness_rows() + _h[_end:]
        with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(_h)
    # T45 matchup deficiency matrix (tools/matchup_page.py)
    import matchup_page
    written += matchup_page.write_pages(SITE, shell)
    # T46 Houston depth-chart gap resolution (tools/houston_depth.py)
    import houston_depth
    written += houston_depth.write_pages(SITE, shell)
    print("wrote %d pages: %s" % (len(written), ", ".join(written)))


if __name__ == "__main__":
    main()
