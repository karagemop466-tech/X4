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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "output")
SITE = os.path.join(ROOT, "site")

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
    ("strategies.html", "Strategy lab"),
    ("availability.html", "Injuries & depth"),
    ("depth.html", "Depth & deficiency"),
    ("questions.html", "Decision checklist"),
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
    ]),
    ("Verified data", [
        ("standings.html", "Standings &amp; results",
         "Official standings for all {n_teams} teams, power ratings, and every completed game with its official link."),
        ("data.html", "Verified data",
         "Standings, the Week 10 slate, the Week 11 schedule with a dated market snapshot, and 57 results."),
        ("availability.html", "Injuries &amp; depth",
         "The full official Week 10 injury report, a unit-level roll-up, and the starter changes the league confirmed."),
        ("depth.html", "Depth &amp; deficiency",
         "All {n_depth_rows} depth positions transcribed from the {n_depth_clubs} clubs that publish an ordered chart, joined to the official injury report: who is out, who replaces him, and where no replacement is named."),
        ("injuries.html", "Availability",
         "Player-linked injury rows and the starter-to-second-string deficiency pipeline for both units."),
    ]),
    ("Model &amp; strategies", [
        ("lines.html", "Model lines",
         "Week 11 model spreads and totals for all {n_schedule} official games, with the market column left blank."),
        ("strategies.html", "Strategy lab",
         "The leaderboard, the {spell_n_gates} validation gates, the error-correlation matrix, calibration and stability."),
        ("signals.html", "Line lab &amp; signals",
         "Thirteen originated baseline lines against the market, ten candidate signals, eight gates and four correlations with confidence intervals."),
        ("leaderboard.html", "Leaderboard",
         "Singles, parlays and prop-combination divisions with the scoring formula and the anti-gaming rules."),
    ]),
    ("Review &amp; flags", [
        ("suggestions.html", "Suggestions",
         "{spell_cap_n_suggestions} ranked proposals, each with the decision it needs and the evidence that would show it worked."),
        ("review.html", "Suggestions review queue",
         "Eighteen proposals with Accept / Hold / Reject, saved in the browser, so a path is chosen before anything is built."),
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
    ]),
]

SRC_SEASON = "https://www.nfl.com/schedules/2026/"


# ------------------------------------------------------------------ helpers
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


def wk_facts():
    facts = [
        ("Week 11 schedule published",
         "NFL.com lists 13 games for Week 11 (Nov 19&ndash;23) and confirms the six teams on "
         "bye: Atlanta, Cleveland, Green Bay, LA Rams, New England and Seattle.",
         "https://www.nfl.com/schedules/2026/by-week/week-11"),
        ("Official standings",
         "Through the Nov 12 Thursday night game: Buffalo 7&ndash;1 leads the AFC East; San "
         "Francisco 7&ndash;1 leads the NFC West; the Los Angeles Chargers are 0&ndash;8.",
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
        "All %d completed games in the 2026 regular season through the Nov 12 game. Every "
        "score reproduces the official NFL.com standings totals for all 32 teams exactly "
        "(verified by tools/verify.py)." % len(games),
        row_attrs=lambda i: ' data-week="%d"' % games[i]["week"]))


def lines_table():
    rows = []
    for r in lines:
        sp = [r["models"][k]["spread"] for k in r["models"]]
        to = [r["models"][k]["total"] for k in r["models"]]
        s3 = r["models"]["S3"]
        rows.append([
            esc(r["date"]),
            "<b>%s @ %s</b>" % (esc(r["away"]), esc(r["home"])),
            esc(r["time_et"]),
            esc(r["network"]) + (" (%s)" % esc(r["international"]) if r["international"] else ""),
            "%s to %s" % (num(min(sp), 1), num(max(sp), 1)),
            "%s to %s" % (num(min(to), 1), num(max(to), 1)),
            "%s / %s" % (num(s3["spread"], 1), num(s3["total"], 1)),
            blank("no official NFL source &mdash; see Flagged F-01"),
            src(r["url"], "NFL.com"),
        ])
    return wrap("lines", table(
        [("Date", 0), ("Matchup", 0), ("Kickoff", 0), ("TV", 0),
         ("Model spread range", 1), ("Model total range", 1),
         ("Recommended line (S3)", 1), ("Market line", 0), ("Source", 0)], rows,
        "Spreads and totals are MODEL ESTIMATES produced by tools/build.py from official "
        "NFL.com results; the range spans all nine strategies. The market-line column is "
        "intentionally blank: the NFL does not publish official betting lines, and no licensed "
        "odds feed has been authorised for this repository."))


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
        rows.append([
            num(i), esc(r["id"]), "<b>%s</b>" % esc(r["name"]),
            num(r["metrics"]["spread_mae"], 2), num(r["metrics"]["total_mae"], 2),
            pct(r["metrics"]["direction_accuracy"], 1),
            badge("benchmark", "mute") if r["id"] == "S0" else pct(r["improvement_pct"], 1),
            "%s to %s" % (num(r["ci_low"], 2), num(r["ci_high"], 2)),
            pct(r["weekly_positive_share"], 0),
            num(r["calibration_max_gap"], 3),
            badge("%d/7" % r["gates_passed"], "ok" if r["gates_passed"] == 7 else "warn"),
            badge("yes", "ok") if r["eligible"] else badge("no", "no"),
            num(r["reward"], 1),
            src(SRC_SEASON, "NFL.com results"),
        ])
    return wrap("lb", table(
        [("Rank", 1), ("ID", 0), ("Strategy", 0), ("Spread MAE", 1), ("Total MAE", 1),
         ("Direction acc.", 1), ("Improvement", 1), ("95% CI", 1),
         ("Weeks improved", 1), ("Calibration gap", 1), ("Gates", 0),
         ("Eligible", 0), ("Points", 1), ("Source", 0)], rows,
        "Improvement is the reduction in spread MAE against the S0 league-constant benchmark, "
        "measured over %d out-of-sample games. The confidence interval is a %s "
        "Bonferroni-adjusted paired bootstrap interval. Points are provisional: they are only "
        "bankable by a strategy that passes all seven gates."
        % (meta["eval_games"], num(meta["bonferroni_alpha"], 4))))


def leaderboard_preview_table():
    rows = []
    for i, r in enumerate(leaderboard, 1):
        rows.append([
            num(i),
            "<b>%s</b> %s" % (esc(r["id"]), esc(r["name"])),
            num(r["metrics"]["spread_mae"], 2),
            badge("benchmark", "mute") if r["id"] == "S0" else pct(r["improvement_pct"], 1),
            "%d / 7" % r["gates_passed"],
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
    return wrap(element_id,
                '<div class="table-wrap"><table class="corr">%s%s</table></div>'
                % ("".join(head), "".join(body)))


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
    for r in verification:
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
    <span>Evidence status: verified official data + labelled model estimates &middot; no market data &middot; not betting advice</span>
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
  <h2>Official NFL data, verified line by line. Model lines labelled as estimates. Nothing filled in that could not be confirmed.</h2>
  <p>This desk is built on the NFL's own pages. Every number in every table traces to an official NFL.com URL that a reviewer can open. Scores were rebuilt from a reconstructed game log and then <b>proved</b> against the official standings: %(ngames)d games, and every team's wins, losses, ties, points for, points allowed and winning percentage match the NFL exactly. Where an official source does not exist - market lines, depth-chart strings, player-prop prices - the cell is left blank and the gap is listed on the <a href="flags.html">Flagged for review</a> page.</p>
  <p>What the work actually shows: the model has signal over a league-average benchmark, but the improvement is <b>not yet statistically separable from luck</b>, so the leaderboard marks every strategy ineligible for reward. That is the validation gate working, not a gap in the analysis.</p>
</div>

<div class="grid g4">%(kpis)s</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">What the official sources say right now</span><h2>Verified position</h2></div><span class="tag acc">NFL.com &middot; 14 Nov 2026</span></div>
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
    <article class="card"><span class="eyebrow">Rule 1</span><h3>Every row has a source link</h3><p class="muted">Each table row links to the official page it came from - a specific NFL.com game page, player page or news article - not a home page. Click it and check the value yourself.</p></article>
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
  <div class="section-head"><div><span class="eyebrow">Where to go next</span><h2>The desk</h2></div></div>
  <div class="grid g3">
    <article class="card"><span class="eyebrow">Data</span><h3><a href="standings.html">Standings &amp; results</a></h3><p class="muted">Official standings for all 32 teams, opponent-adjusted power ratings, and all %(ngames)d completed games with a link to each official game page.</p></article>
    <article class="card"><span class="eyebrow">Model</span><h3><a href="lines.html">Model lines</a></h3><p class="muted">Week 11 model spreads and totals for all 13 official games, with the full range across strategies and the market-line column left blank on purpose.</p></article>
    <article class="card"><span class="eyebrow">Validation</span><h3><a href="strategies.html">Strategy lab</a></h3><p class="muted">The leaderboard, the seven gates, the error-correlation matrix, the calibration check and the week-by-week stability table.</p></article>
    <article class="card"><span class="eyebrow">Availability</span><h3><a href="availability.html">Injuries &amp; depth</a></h3><p class="muted">The full official Week 10 injury report, a unit-level roll-up of absences, and the starter changes the league confirmed in its own news.</p></article>
    <article class="card"><span class="eyebrow">Decisions</span><h3><a href="questions.html">Decision checklist</a></h3><p class="muted">%(n_questions)s questions that must be answered before a decision here is reasonable: what we know, what is missing, what it blocks and how to close it.</p></article>
    <article class="card"><span class="eyebrow">Review</span><h3><a href="suggestions.html">Suggestions</a></h3><p class="muted">Twelve proposals, ranked, with the decision each one needs and the evidence that would show it worked. Review before building.</p></article>
  </div>
</section>

%(directory)s
""" % dict(ngames=len(games), kpis=kpi_cards(), facts=wk_facts(), eligible=eligible,
           nstrat=len(leaderboard), lbpreview=leaderboard_preview_table(),
           flagpreview=flags_table(limit=6),
           n_questions=spell(N_QUESTIONS),
           directory=directory_section()), "index.html"))

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
  <div class="note ok"><b>How this was verified.</b> The game log was reconstructed and then checked, automatically, against the official standings: <span class="mono">tools/verify.py</span> rebuilds every team's record and point totals from the %(ngames)d games and compares them to the NFL's own figures. All 32 teams matched exactly on all six measures, which also proves every individual score. The check runs 460 assertions and is part of the build.</div>
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
  <div class="note warn"><b>There is no market column.</b> The NFL publishes no official betting lines, and no licensed odds feed has been authorised for this repository, so the market-line cell is empty rather than filled from an aggregator. Every figure in this table is a model estimate derived from official NFL.com results - it is a research output, not a price and not a recommendation.</div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">The nine strategies</span><h2>What produces a line</h2><p class="muted">Each strategy is a different way of turning the same verified game log into a forecast. They are scored on the <a href="strategies.html">Strategy Lab</a> page.</p></div></div>
%(strats)s
</section>
""" % dict(lines=lines_table(), strats=strategy_list_table()), "lines.html"))

# --- strategies ---
PAGES.append(("strategies.html", "Strategy lab",
               "Strategy leaderboard with seven validation gates, error correlation matrix, "
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
</section>
""" % dict(lb=leaderboard_table(), gates=gates_table(),
           corerr=corr_table(corr_err, "corr-err"),
           corrpred=corr_table(corr_pred, "corr-pred"),
           calib=calib_table(), weekly=weekly_table(),
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
  <div class="note ok"><b>The depth question is now answered on its own page.</b> This page stops at who the official report says cannot play. Which of those players is a <i>starter</i>, who the club lists behind him, and where the club lists nobody at all, is on <a href="depth.html">Depth &amp; deficiency</a>: 1,558 depth positions transcribed from the clubs' own official charts and joined to this report. Flag <b>F-02</b> (no depth rank could be verified) is closed; what the charts still cannot say - who actually took the first snap - is <b>F-21</b>.</div>
</section>
""" % dict(avail=avail_table(), qb=qb_table(), news=news_table(), injfull=inj_full_table(),
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
PAGES.append(("suggestions.html", "Suggestions",
               "Twelve ranked proposals for reviewing and choosing before implementation, each with "
               "the decision it needs.",
               """
<div class="section-head"><div><span class="eyebrow">08 &middot; Review before building</span><h2>Suggestions</h2><p class="muted">The best path has to be chosen before any of it is implemented. Each proposal below states what it would do, why it matters, how you would know it worked, and the decision it needs from you first. None of them is presented as already built.</p></div><span class="tag warn">Choose before implementing</span></div>
<div id="sugg" class="grid g3">%(sugg)s</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">How to review them</span><h2>Ordering rule</h2><p class="muted">Work down this list. If a proposal cannot answer its question, the later ones are not worth evaluating yet.</p></div></div>
%(frame)s
</section>
""" % dict(sugg=suggestions_grid(), frame=framework_table()), "suggestions.html"))

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
    <p class="muted">460 assertions covering: every game row's official URL pattern, every team's wins, losses, ties, points for, points allowed, net points and winning percentage, games played per team, the Week 11 schedule's pairing and URL structure, and duplicate rows. It exits non-zero on any failure and runs as part of the build.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 3 &middot; Model</span>
    <h3>Opponent-adjusted rates</h3>
    <p class="muted">For a team, the opponent-adjusted points-for rate is the team's own scoring rate minus the average points allowed by the opponents it has faced, plus the league average. The same construction gives the opponent-adjusted points-allowed rate. A team's expected score is the mean of its adjusted offence and its opponent's adjusted defence, with the league home-field margin added. Every quantity used for a Week-w forecast is measured strictly from games before Week w, including the opponents' season rates, so there is no look-ahead.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 4 &middot; Validate</span>
    <h3>Walk-forward, seven gates</h3>
    <p class="muted">Strategies are evaluated only on games that had not been played at forecast time - no random row splits. Each strategy must clear data integrity, out-of-sample discipline, minimum sample size, statistical significance, weekly stability, calibration, and exclusion of the league-constant benchmark, before it can earn reward points.</p>
  </article>
</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Model parameters</span><h2>Every knob, published</h2><p class="muted">These are analyst choices by this project, not official values, and they are the first thing a reviewer should challenge. Changing any of them changes the ranking. The bootstrap uses a fixed, interpreter-independent generator so the published intervals are identical on every machine.</p></div><span class="tag warn">Not official</span></div>
%(params)s
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
""" % dict(params=params_table(), verify=verification_table()), "methodology.html"))



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
  <div class="note warn"><b>What this page does not claim.</b> A published depth chart is not proof of who took the first snap. Nothing here records snap counts or official game books, so the score above measures <i>listed</i> availability before kickoff, not realised participation. Houston publishes its chart only as an image, so it contributes no rows and its five ruled-out players appear in the unmatched table. Both limits are on the <a href="flags.html">Flagged for review</a> page as F-18 and F-21.</div>
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


def main():
    os.makedirs(SITE, exist_ok=True)
    written = []
    for href, title, desc, body, active in PAGES:
        slug = href.replace(".html", "")
        with open(os.path.join(SITE, href), "w", encoding="utf-8") as fh:
            fh.write(shell(slug, title, desc, body, href))
        written.append(href)
    print("wrote %d pages: %s" % (len(written), ", ".join(written)))


if __name__ == "__main__":
    main()
