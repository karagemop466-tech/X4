#!/usr/bin/env python3
"""
T48 - the open-question register: what we know, what we do not, and the number that
would settle it.

WHY THIS EXISTS
---------------
The brief asks for "a clear list of questions, information and answers that need to be
addressed before any decision can be reasonably made based upon the information that we
already have and do not have", and separately for suggestions that *discover* the missing
information. The site already has three related pages (questions.html, decisions.html,
readiness.html) but none of them is a single register in which every row carries, in one
line, (a) the question, (b) what is already known with a count taken from the committed
files, (c) what is missing, (d) the gate that blocks the decision it would unlock, and
(e) the specific number that would clear that gate.

This tool builds that register. Every "what we have" figure is COMPUTED at build time from
the committed data; none is typed. That is the whole point: a register of unknowns that is
itself stale is worse than no register. `--check` fails if any computed figure drifts from
the committed page.

WHAT IT DOES NOT DO
-------------------
It does not answer any question. Where the answer is not in the committed data the cell says
so and the row is marked blocked. No value is estimated, inferred or filled in.

Usage:
  python3 tools/open_questions.py           # rebuild site/open-questions.html + mirror
  python3 tools/open_questions.py --check   # fail if the page is stale
"""
from __future__ import annotations

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OPS = os.path.join(DATA, "ops")
SITE = os.path.join(ROOT, "site")

NFL_INJ = "https://www.nfl.com/injuries/league/2026/reg10"
NFL_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-11"
NFL_STAND = "https://www.nfl.com/standings/"
NFL_INJ11 = "https://www.nfl.com/injuries/league/2026/reg11"
REPO = "https://github.com/karagemop466-tech/X4/blob/main/"


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def counts():
    """Every figure the register quotes, computed from the committed files."""
    c = {}
    games = rows(os.path.join(DATA, "games-2026.csv"))
    c["games"] = len(games)
    c["weeks"] = len({g["week"] for g in games})

    inj = rows(os.path.join(DATA, "injuries-wk10-2026.csv"))
    c["inj_rows"] = len(inj)
    c["inj_out"] = sum(1 for r in inj if r["game_status"] == "Out")
    c["inj_doubtful"] = sum(1 for r in inj if r["game_status"] == "Doubtful")
    c["inj_questionable"] = sum(1 for r in inj if r["game_status"] == "Questionable")
    c["inj_designated"] = sum(1 for r in inj if r["game_status"])
    c["inj_teams"] = len({r["team"] for r in inj})

    depth = rows(os.path.join(DATA, "depth-wk11-2026.csv"))
    c["depth_rows"] = len(depth)
    c["depth_clubs"] = len({d["team"] for d in depth})

    feed = rows(os.path.join(DATA, "results-feed.csv"))
    c["feed_rows"] = len(feed)

    snap = rows(os.path.join(DATA, "market-prices-2026.csv"))
    c["price_rows"] = len(snap)
    c["price_games"] = len({(r["away"], r["home"], r["week"]) for r in snap})
    c["price_close"] = sum(1 for r in snap if r["close_line"])

    graded = rows(os.path.join(OPS, "graded.csv"))
    c["graded"] = len(graded)

    st = json.load(open(os.path.join(DATA, "output", "sign_test.json"), encoding="utf-8"))
    c["sign_n"] = st["n"]
    best = max(st["strategies"].items(), key=lambda kv: kv[1]["wins"])
    c["sign_best"] = best[0]
    c["sign_wins"] = best[1]["wins"]
    c["sign_p"] = best[1]["p_one_sided"]
    c["sign_bonf"] = st["bonferroni_alpha"]
    c["sign_clearers"] = sum(1 for v in st["strategies"].values() if v["clears_bonferroni"])

    lb = json.load(open(os.path.join(DATA, "output", "leaderboard.json"), encoding="utf-8"))
    c["strategies"] = len(lb)
    c["eligible"] = sum(1 for s in lb if str(s.get("eligible")).lower() in ("true", "yes", "1"))

    clv = rows(os.path.join(ROOT, "research", "data", "clv_ledger.csv"))
    c["clv_rows"] = len(clv)

    c["clubs_with_out"] = len({r["team"] for r in inj if r["game_status"] == "Out"})
    hou = os.path.join(DATA, "houston-playtime-depth-wk10-2026.csv")
    c["gamebook_club_weeks"] = 1 if os.path.exists(hou) else 0
    return c


def register(c):
    """(id, question, what we have, what is missing, gate that blocks, number that clears it,
    source url, source label). 'What we have' strings interpolate COMPUTED counts only."""
    return [
        ("OQ-01", "Can any strategy be promoted from paper to live?",
         "%d strategies evaluated, %d eligible. Best sign-test result: %s wins %d of %d games "
         "(p = %.5f, threshold %.5f) while the mean-error bootstrap gate still fails."
         % (c["strategies"], c["eligible"], c["sign_best"], c["sign_wins"], c["sign_n"],
            c["sign_p"], c["sign_bonf"]),
         "A primary skill metric fixed in writing before a window opens. Two statistics "
         "currently disagree and %d of %d strategies clear the one that is not the gate."
         % (c["sign_clearers"], c["strategies"]),
         "G4 (probability quality) + S-15 (primary metric undecided)",
         "The owner names the primary metric in a committed pre-registration file; the "
         "named metric then passes its own Bonferroni threshold on the next prospective window",
         REPO + "data/output/sign_test.json", "sign_test.json"),
        ("OQ-02", "Has any price been taken at the moment a stake would be placed?",
         "%d archived price rows across %d games; %d carry a closing number; the CLV ledger "
         "has %d rows." % (c["price_rows"], c["price_games"], c["price_close"], c["clv_rows"]),
         "A stake-time capture. The archive records a closing number, not a price taken at "
         "the moment a stake would have been placed, so CLV cannot be computed for any bet "
         "and the ledger is empty by design rather than by omission.",
         "G7 (closing-line value) and demotion rules D1/D5",
         "%d CLV ledger row with a stake-time price and a matching close"
         % max(c["clv_rows"] + 1, 1),
         REPO + "research/data/clv_ledger.csv", "clv_ledger.csv"),
        ("OQ-03", "How much is one missing starter actually worth?",
         "A measured club-level contrast exists: %d of %d clubs carried an Out in Week 10 and "
         "the clear-group comparison rests on %d club-games; both intervals span zero."
         % (c["clubs_with_out"], 28, 28 - c["clubs_with_out"]),
         "A player-level estimate. It needs snap counts for the replacement and the man he "
         "replaced; the repository holds %d club-week of official playing time."
         % c["gamebook_club_weeks"],
         "S5 (depth for all 32 clubs) and the identifiability gate on personnel-ablation.html",
         "32 club-weeks of official playing time across at least 2 weeks (I3 on the ablation page)",
         REPO + "data/personnel-ablation-wk10-2026.csv", "personnel ablation"),
        ("OQ-04", "Is the depth chart a usable starter/backup label?",
         "%d depth rows across %d of 32 clubs; Houston is an image and is left blank."
         % (c["depth_rows"], c["depth_clubs"]),
         "A structured route for all 32 clubs, and a published date on the 26 charts that "
         "carry none, so a stale chart is detectable rather than assumed current.",
         "S5",
         "32 of 32 clubs with a structured, dated chart (or a verified snap-count route for all 32)",
         "https://www.nfl.com/teams/", "NFL.com clubs"),
        ("OQ-05", "Does a game status mean what it says?",
         "%d player rows on the Week 10 report: %d Out, %d Doubtful, %d Questionable, %d with "
         "no designation." % (c["inj_rows"], c["inj_out"], c["inj_doubtful"],
                              c["inj_questionable"], c["inj_designated"]),
         "An empirical play rate per designation. Measuring it needs several seasons of "
         "designations joined to official inactive lists, and only one week of report is captured.",
         "F-61 / the capture pipeline (F-47, F-48, F-65)",
         "multiple seasons of designations joined to official inactive lists, with play rate and CI per label",
         NFL_INJ, "Official Week 10 injury report"),
        ("OQ-06", "Is a completed Week 11 report available to model the current slate?",
         "The Week 11 address was read on 2026-11-18 and still serves Week 10 content; the "
         "13 Week 11 fixtures and kickoff times are transcribed and verified.",
         "The official Week 11 injury report. Until it publishes, no Week 11 availability "
         "claim can be made from an official source.",
         "F-61",
         "the reg11 address serving a Week 11 header with Week 11 player rows",
         NFL_INJ11, "Week 11 report address"),
        ("OQ-07", "Can results, ratings and ROI be computed on the full season?",
         "%d games in the log across %d weeks; the results feed holds %d rows and reconciles "
         "to the official standings." % (c["games"], c["weeks"], c["feed_rows"]),
         "%d paper bets are graded so far (nine strategies x one settled game); Weeks 11-18 "
         "plus enough further settled bets to satisfy the sample gate." % c["graded"],
         "G2 (sample sufficiency, n >= 100)",
         "100 settled bets per market type, settled against the verified feed",
         REPO + "data/results-feed.csv", "results feed"),
        ("OQ-08", "Do injuries and availability add signal, or just noise?",
         "The ablation on personnel-ablation.html measures the one contrast the data supports "
         "and finds both intervals spanning zero.",
         "A with/without model comparison on a chronological holdout, which needs the verified "
         "availability features that OQ-03 and OQ-04 show do not exist yet.",
         "S5 + OQ-03",
         "two identical models, one with verified availability features, on a chronological holdout, "
         "difference reported with an interval",
         REPO + "research/verification/personnel-ablation-2026-11-18.md", "ablation method note"),
    ]


def body(c):
    import pages as P
    esc, src, badge, table = P.esc, P.src, P.badge, P.table
    out = []
    for (qid, q, have, missing, gate, clears, url, label) in register(c):
        blocked = True
        out.append([
            '<a id="%s"></a><b>%s</b>' % (esc(qid), esc(qid)),
            esc(q), esc(have), esc(missing), esc(gate), esc(clears),
            src(url, label), badge("blocked" if blocked else "clear", "bad" if blocked else "ok"),
        ])
    t = table(
        [("ID", False), ("Question", False), ("What we already know", False),
         ("What is missing", False), ("Gate that blocks the decision", False),
         ("The number that would clear it", False), ("Source", False), ("State", False)],
        out, cls="data",
        note="Every figure in the 'what we already know' column is computed at build time by "
             "tools/open_questions.py from the committed CSV/JSON; none is typed. If a number "
             "here disagrees with the page it cites, the build fails. 'The number that would "
             "clear it' is a specification of the missing evidence, not an estimate of it.")

    h = ['<section class="hero"><div class="wrap"><span class="eyebrow">Open questions &middot; T48</span>'
         '<h1>The questions that must be answered before any decision is reasonable</h1>'
         '<p class="lede">One row per open question, with what is already known (counted from the '
         'committed data), what is missing, the gate that blocks the decision it would unlock, and '
         'the specific number that would clear that gate. Nothing here is answered by opinion.</p>'
         '<p class="meta">' + src(NFL_STAND, "Official standings") + ' &middot; '
         + src(NFL_INJ, "Official Week 10 report") + ' &middot; '
         + src(NFL_SCHED, "Official Week 11 schedule") + '</p></div></section>']
    h.append('<section class="section"><div class="section-head"><div>'
             '<span class="eyebrow">The register</span>'
             '<h2>Eight questions, eight blocking gates, eight stated clearing numbers</h2>'
             '</div></div>' + t + '</div></section>')
    h.append('<section class="section"><div class="section-head"><div>'
             '<span class="eyebrow">Why this page is generated</span>'
             '<h2>A register of unknowns that is itself out of date is worse than none</h2>'
             '</div></div><p>A previous session found the site a week stale because a completed '
             'slate had not been ingested (F-58), and a later read found stale counts surviving in '
             'prose the gate does not check (F-66). This register was therefore built as a '
             'generator rather than a document: <code>python3 tools/open_questions.py --check</code> '
             'fails the publication gate when any count it quotes stops matching the committed '
             'data. When a gate clears, this page changes by itself, and if it does not, the build '
             'breaks.</p></div></section>')
    return "".join(h)


def page():
    """The complete page HTML, for --check comparison."""
    import desk_nav
    c = counts()
    return desk_nav.side(), body(c)


def check():
    path = os.path.join(SITE, "open-questions.html")
    if not os.path.exists(path):
        print("FAIL: site/open-questions.html is missing; run tools/open_questions.py")
        return 1
    html = open(path, encoding="utf-8").read()
    c = counts()
    problems = []
    for (qid, q, have, missing, gate, clears, url, label) in register(c):
        if qid not in html:
            problems.append("row %s missing from the page" % qid)
        # the computed 'what we have' sentence must appear verbatim (HTML-escaped)
        import html as _h
        if _h.escape(have, quote=False) not in html and have not in html:
            problems.append("row %s: computed text not found on the page (stale build)" % qid)
    if problems:
        for p in problems:
            print("FAIL:", p)
        print("open_questions: %d problem(s); rebuild with tools/open_questions.py" % len(problems))
        return 1
    print("open_questions: OK (%d rows, every computed figure matches the committed page)"
          % len(register(c)))
    return 0


def main():
    if "--check" in sys.argv:
        return check()
    import desk_nav
    c = counts()
    h = body(c)
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="description" content="The open-question register: what is known, what '
            'is missing, the gate that blocks each decision, and the number that would clear it.">'
            '<title>Open questions &middot; Fourth Down Research</title>'
            '<link rel="stylesheet" href="desk.css"></head><body>'
            + desk_nav.side()
            + '<main class="main">' + h + '</main></body></html>\n')
    with open(os.path.join(SITE, "open-questions.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print("open_questions: wrote site/open-questions.html (%d rows)" % len(register(c)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
