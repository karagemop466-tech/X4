#!/usr/bin/env python3
"""T38 decision-desk extension: three pages, rendered by the shared generator.

Pages written into site/ (called from tools/pages.py main() through write_pages):

  luck.html       removal-of-luck panel: controls (random picks, favourites),
                  cluster-bootstrap interval, and the settlement reconciliation
                  row by row against official NFL.com scores.
  readiness.html  decision readiness: one row per requirement with the blocking
                  gate and the number that clears it, plus the two-sided
                  "what would change our mind" field for the live v1 model.
  teams.html      per-team view: record, Week-10 official report counts,
                  depth-chart starters listed Out or Doubtful, the depth-2
                  replacement the chart names, and official Out players that
                  do not join the depth file. Week-11 venues from NFL.com.

Rules this module follows
- Every table row carries a link to an official source, or is shown blank and
  flagged. No value is inferred, filled, or taken from a jersey number,
  experience or salary.
- Nothing here changes the leaderboard. Controls and ROI on this page are not
  ranking criteria; each is shown with n and an interval.
- Injury signal is a change, not a level. The page shows the Week-10 report as a
  level only, and states that no second dated snapshot exists to compute a delta.
"""
import csv
import os

import luck

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OPS = os.path.join(DATA, "ops")

NFL_WEEK10_INJURY = "https://www.nfl.com/injuries/league/2026/reg10"
NFL_STANDINGS = "https://www.nfl.com/standings/"
NFL_SCHEDULE_WK11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
NFL_SEASON = "https://www.nfl.com/schedules/2026/"  # official season schedule and final scores
PREREG = "research/preregistration/wk11-forward-v1.md"


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _norm(name):
    return name.replace(".", "").replace("'", "").strip().lower()


def _page_helpers():
    # imported here so this module can be imported without the generator running
    import pages as P
    return P


# --------------------------------------------------------------------- data
def build_teams():
    P = _page_helpers()
    standings = _rows(os.path.join(DATA, "standings-wk10-2026.csv"))
    inj = _rows(os.path.join(DATA, "injuries-wk10-2026.csv"))
    dep = _rows(os.path.join(DATA, "depth-wk11-2026.csv"))
    out = []
    for s in sorted(standings, key=lambda r: r["abbr"]):
        t = s["abbr"]
        ti = [r for r in inj if r["team"] == t]
        td = [r for r in dep if r["team"] == t]
        counts = {k: sum(1 for r in ti if r["game_status"] == k) for k in ("Out", "Doubtful", "Questionable")}
        starters_out = []
        replacements = []
        for r in td:
            if r["depth"] == "1" and r["game_status"] in ("Out", "Doubtful"):
                starters_out.append("%s %s (%s)" % (r["position_row"], r["player"], r["game_status"]))
                rep = [x for x in td if x["unit"] == r["unit"] and x["position_row"] == r["position_row"]
                       and x["depth"] == "2"]
                replacements.append(rep[0]["player"] if rep else "")
        joined = {_norm(x["player"]) for x in td}
        unmatched = [r["player"] + " (" + r["game_status"] + ")" for r in ti
                     if r["game_status"] == "Out" and _norm(r["player"]) not in joined]
        chart_src = td[0]["source"] if td else ""
        chart_date = sorted({r["chart_date"] for r in td if r["chart_date"]})
        out.append(dict(team=t, name=s["team"], w=s["w"], l=s["l"], t=s["t"],
                        counts=counts, starters_out=starters_out, replacements=replacements,
                        unmatched=unmatched, depth_rows=len(td), chart_src=chart_src,
                        chart_date=chart_date, injury_rows=len(ti)))
    return out


def venues():
    return _rows(os.path.join(DATA, "venues-wk11-2026.csv"))


# ------------------------------------------------------------------ render
def luck_page():
    P = _page_helpers()
    esc, src, badge, table, blank = P.esc, P.src, P.badge, P.table, P.blank
    z = luck.compute()
    o = z["ours_recorded"]
    r = z["ours_resettled"]
    c1 = z["control_random"]
    c2 = z["control_favourites"]
    ctr = z["n_bets"]

    def pc(x, d=1):
        return "%.*f%%" % (d, 100 * x)

    summary_rows = [
        ["Our record, as graded in data/ops/graded.csv", "%d bets" % ctr,
         pc(o["roi"]), "%+.2f units" % o["pnl_units"],
         "[%s, %s]" % (pc(o["ci95_cluster"][0]), pc(o["ci95_cluster"][1])),
         src(NFL_SCHEDULE_WK11, "Schedule source")],
        ["Our record, re-settled against the recorded line and official score", "%d bets" % ctr,
         pc(r["roi"]), "%+.2f units" % r["pnl_units"],
         "[%s, %s]" % (pc(r["ci95_cluster"][0]), pc(r["ci95_cluster"][1])),
         src("https://www.nfl.com/schedules/2026/", "Official schedule")],
        ["Control C1: random side, seeded (10,000 draws), mean", "%d bets" % ctr,
         pc(c1["roi_mean"]), "-", "[%s, %s] draw 95%%" % (pc(c1["roi_ci95"][0]), pc(c1["roi_ci95"][1])),
         src("https://www.nfl.com/schedules/2026/", "Official schedule")],
        ["Control C2: favourites only (side laying points, shorter price)", "%d bets" % ctr,
         pc(c2["roi"]), "%+.2f units" % c2["pnl_units"], "not computed (single rule)",
         src("https://www.nfl.com/schedules/2026/", "Official schedule")],
    ]
    summary = table(
        [("Series", 0), ("n", 1), ("ROI", 1), ("P&L", 1), ("Game-cluster 95% interval", 0), ("Source", 0)],
        summary_rows,
        "ROI is shown with n and an interval because n is %d bets across %d games. "
        "It is not a ranking criterion. Random picks reproduce our recorded ROI in %s of "
        "draws and our re-settled ROI in %s. A cluster interval containing zero is not a "
        "finding of skill." % (ctr, z["n_events"], pc(c1["share_ge_ours_recorded"]),
                              pc(c1["share_ge_ours_resettled"])))

    unit_rows = []
    for u in z["units"]:
        ok = u["matches"]
        unit_rows.append([
            esc(u["event_id"]), esc("Week %d" % u["week"]),
            esc("%s at %s" % (u["away"], u["home"])),
            esc(u["market"]), esc(u["bet"]), esc(u["price"]),
            esc(u["line"] if u["line"] is not None else "-"),
            esc("%s %d - %d %s" % (u["away"], u["official_away"], u["official_home"], u["home"])),
            esc(u["recorded_outcome"]), esc(u["resettled_outcome"]),
            badge("matches" if ok else "DIFFERS", "ok" if ok else "bad"),
            src(u["official_url"], "NFL.com game"),
        ])
    units = table(
        [("Event", 0), ("Week", 0), ("Game", 0), ("Market", 0), ("Bet", 0), ("Price", 1),
         ("Line", 1), ("Official final", 0), ("Recorded", 0), ("Re-settled", 0), ("Check", 0),
         ("Official source", 0)],
        unit_rows,
        "Every row is one originated bet. The official final score and game link come "
        "from data/ops/results.csv. Re-settled outcomes apply the recorded line to the "
        "official score; the recorded column is what data/ops/graded.csv says.")

    per = z["per_type"]
    per_rows = []
    for mk in ("side", "total", "moneyline"):
        p = per[mk]
        per_rows.append([esc(mk), str(p["n"]), str(p["need"]),
                         str(p["wins_resettled"]), str(p["losses_resettled"]),
                         blank("gate G2 not met" if p["n"] < 100 else ""),
                         src(NFL_SEASON, "Official schedule and scores")])
    pertype = table(
        [("Market", 0), ("Bets (n)", 1), ("Bets still needed for G2 (100)", 1),
         ("Re-settled wins", 1), ("Re-settled losses", 1), ("Status", 0), ("Source", 0)],
        per_rows, "Gate G2 requires 100 settled bets per market type. None is met.")

    mism = z["mismatches"]
    mrows = []
    for m in mism:
        mrows.append([esc(m["event_id"]), esc(m["market"] + " " + m["bet"]),
                      esc("recorded %s, re-settled %s" % (m["recorded"], m["resettled"])),
                      esc("line %s; official away %d, home %d" % (m["line"], m["official_away"], m["official_home"])),
                      src(m["official_url"], "NFL.com game")])
    mismatch_block = table(
        [("Event", 0), ("Bet", 0), ("Outcome", 0), ("Line and official score", 0), ("Official source", 0)],
        mrows,
        "Settlement reconciliation. The grader in tools/origination.py applies side bets "
        "to the straight-up winner (lines 575-578) and not to the spread. Event 401873039 "
        "shows the effect. The recorded graded.csv value is not edited here; the corrected "
        "figure is shown beside it and the rule change is pre-registered in %s." % PREREG)

    body = (
        "<section><div class=\"section-head\"><div><span class=\"eyebrow\">Removal of luck</span>"
        "<h2>Could our staking record have appeared by chance?</h2>"
        "<p class=\"muted\">Controls, a game-cluster interval and the settlement check. "
        "Sample: %d bets, %d games, weeks 9 and 10 only.</p></div></div>"
        "<div class=\"card\">%s</div></section>"
        "<section><div class=\"card\"><span class=\"eyebrow\">Controls</span>%s</div></section>"
        "<section><div class=\"card\"><span class=\"eyebrow\">Gate G2 by market</span>%s</div></section>"
        "<section><div class=\"card\"><span class=\"eyebrow\">Settlement reconciliation</span>%s</div></section>"
        "<section><div class=\"card\"><span class=\"eyebrow\">Every originated bet</span>%s</div></section>"
    ) % (ctr, z["n_events"], summary, summary, pertype, mismatch_block, units)
    return body


def readiness_page():
    P = _page_helpers()
    esc, src, badge, table, blank = P.esc, P.src, P.badge, P.table, P.blank
    gates = _rows(os.path.join(OPS, "gates.csv"))
    dem = _rows(os.path.join(OPS, "demotion_rules.csv"))
    z = luck.compute()

    rows = []
    for g in gates:
        passed = g["status"] == "pass"
        rows.append([esc(g["gate"]), esc(g["name"]), esc(g["rule"]), esc(g["observed"]),
                     badge("pass" if passed else "fail", "ok" if passed else "bad"),
                     badge("blocks" if not passed else "clear", "bad" if not passed else "ok"),
                     src(NFL_SEASON, "Official schedule and scores")])
    rows.append([esc("S1"), esc("Settlement reconciliation"),
                 esc("Recorded outcome equals the re-settled outcome for every graded bet"),
                 esc("%d of %d agree" % (z["n_bets"] - len(z["mismatches"]), z["n_bets"])),
                 badge("fail" if z["mismatches"] else "pass", "bad" if z["mismatches"] else "ok"),
                 badge("blocks", "bad"),
                 src(z["units"][0]["official_url"], "NFL.com game")])
    rows.append([esc("S2"), esc("Control baselines"),
                 esc("Our ROI reported beside random-pick and favourite controls"),
                 esc("present on the luck page"), badge("pass", "ok"), badge("clear", "ok"),
                 src(NFL_SCHEDULE_WK11, "Schedule source")])
    rows.append([esc("S3"), esc("Pre-registered forward window"),
                 esc("Rule, sample and gates committed before any Week 11 result"),
                 esc("committed at 50f588c, before kickoff on 19 November"),
                 badge("pass", "ok"), badge("clear", "ok"),
                 src(NFL_SCHEDULE_WK11, "Official Week 11 schedule")])
    rows.append([esc("S4"), esc("Injury change series"),
                 esc("Two or more dated official snapshots, so a change can be published"),
                 esc("one Week-10 snapshot; no delta exists"), badge("fail", "bad"), badge("blocks", "bad"),
                 src(NFL_WEEK10_INJURY, "NFL.com injury report")])
    rows.append([esc("S5"), esc("Depth charts for all 32 clubs"),
                 esc("A structured official chart for every club"),
                 esc("31 of 32 clubs have a chart in data; Houston is an image, not transcribed"),
                 badge("fail", "bad"), badge("blocks team trust", "bad"),
                 src("https://www.nfl.com/injuries/league/2026/reg10", "NFL.com injury report")])
    readiness = table(
        [("Gate", 0), ("Requirement", 0), ("Rule", 0), ("Observed", 0), ("Status", 0),
         ("Effect", 0), ("Source", 0)], rows,
        "Blocking items must clear before any settlement, ROI or strategy claim is published. "
        "Gates are read from data/ops/gates.csv unchanged. Rows S1 to S5 are added by this extension.")

    keep = [
        ["G2 sample", "at least 100 settled bets per market type", "n = 12 in total"],
        ["G5 significance", "one-sided p below 0.05 on the skill score", "p = 0.0918"],
        ["G7 stability", "no single week above 50 percent of the skill statistic", "largest week 90 percent"],
    ]
    dem_rows = []
    for d in dem:
        th = d["threshold"].strip()
        dem_rows.append([esc(d["rule"]), esc(d["name"]), esc(d["trigger"]),
                         esc(th) if th else blank("threshold blank in demotion_rules.csv: not evaluable"),
                         src(NFL_SCHEDULE_WK11, "Schedule source")])
    keep_rows = [[esc(a), esc(b), esc(c), src(NFL_SCHEDULE_WK11, "Schedule source")] for a, b, c in keep]
    change = table([("Gate", 0), ("Keep the model only if", 0), ("Observed now", 0), ("Source", 0)],
                   keep_rows, "A keep condition is met only when every gate passes.")
    demote = table([("Rule", 0), ("Name", 0), ("Demote to paper when", 0), ("Threshold", 0), ("Source", 0)],
                   dem_rows,
                   "Demotion triggers are the rules in data/ops/demotion_rules.csv. Two thresholds "
                   "are blank there (D1 and D6). Those rules cannot fire, so they are reported as "
                   "not evaluable. Their thresholds are not filled in here.")
    body = (
        "<section><div class=\"section-head\"><div><span class=\"eyebrow\">Decision readiness</span>"
        "<h2>What must be true before any claim is published</h2>"
        "<p class=\"muted\">Eight gates, five extension rows, the two-sided "
        "'what would change our mind' field for the live v1 ratio model.</p></div></div>"
        "<div class=\"card\">%s</div></section>"
        "<section><div class=\"card\"><span class=\"eyebrow\">What would change our mind: keep</span>%s</div></section>"
        "<section><div class=\"card\"><span class=\"eyebrow\">What would change our mind: demote</span>%s</div></section>"
    ) % (readiness, change, demote)
    return body


def teams_page():
    P = _page_helpers()
    esc, src, table, blank = P.esc, P.src, P.table, P.blank
    teams = build_teams()
    rows = []
    for t in teams:
        c = t["counts"]
        if t["depth_rows"]:
            chart = src(t["chart_src"], "Club depth chart") + (
                " &middot; chart date %s" % ", ".join(t["chart_date"]) if t["chart_date"]
                else " &middot; " + blank("chart date not stated"))
        else:
            chart = blank("no structured chart: club chart is an image")
        starters = "; ".join(t["starters_out"]) if t["starters_out"] else "none listed"
        reps = "; ".join(x for x in t["replacements"] if x) or ("none listed" if t["starters_out"] else "-")
        unmatched = "; ".join(t["unmatched"]) if t["unmatched"] else "none"
        rows.append([
            "<b>%s</b> %s" % (esc(t["team"]), esc(t["name"])),
            esc("%s-%s-%s" % (t["w"], t["l"], t["t"])),
            str(c["Out"]), str(c["Doubtful"]), str(c["Questionable"]),
            esc(starters), esc(reps), esc(unmatched), chart,
            src(NFL_WEEK10_INJURY, "Week 10 report"),
        ])
    teams_table = table(
        [("Team", 0), ("Record", 0), ("Out", 1), ("Doubtful", 1), ("Questionable", 1),
         ("Depth starters listed Out or Doubtful", 0), ("Depth-2 replacement named", 0),
         ("Official Out, not in depth file", 0), ("Depth chart", 0), ("Injury report", 0)],
        rows,
        "Injury counts are the Week-10 official report as a LEVEL, not a change. No second "
        "dated snapshot exists, so no delta is published (gate S4). Starters are depth-1 rows "
        "of the Week-11 depth file whose status came from the Week-10 report. A blank in "
        "'depth chart' means the club chart is not in structured form and is not transcribed. "
        "Houston has no chart rows; its five Out players cannot be joined and are listed as "
        "unmatched rather than inferred.")

    vrows = []
    for v in venues():
        place = v["city"] + ((", " + v["state"]) if v["state"] else "")
        vrows.append([esc("%s at %s" % (v["away"], v["home"])), esc(v["date"] + " " + v["time_et"] + " ET"),
                      esc(v["network"]), esc(place), esc(v["stadium"]),
                      src(v["official_url"], "NFL.com game centre")])
    venue_table = table(
        [("Game", 0), ("Kickoff", 0), ("Network", 0), ("Location", 0), ("Stadium", 0), ("Source", 0)],
        vrows,
        "Week 11 venues transcribed from the NFL.com game centre 'Game Info' block (fetched "
        "2026-11-15). The Week-11 injury report is not yet published: each game centre reads "
        "'not available at this time', so no Week-11 status is shown.")

    body = (
        "<section><div class=\"section-head\"><div><span class=\"eyebrow\">Per-team view</span>"
        "<h2>Availability, starters and replacements, team by team</h2>"
        "<p class=\"muted\">32 clubs. Levels from the Week-10 official report; "
        "starters from each club's own depth chart; replacements as the chart names them.</p>"
        "</div></div><div class=\"card\">%s</div></section>"
        "<section><div class=\"card\"><span class=\"eyebrow\">Week 11 venues</span>%s</div></section>"
    ) % (teams_table, venue_table)
    return body


# --------------------------------------------------------------- writer
PAGES_T38 = [
    ("luck.html", "Removal of luck",
     "Controls for the staking record, a game-cluster interval, and the settlement check against official scores.",
     luck_page, "luck.html"),
    ("readiness.html", "Decision readiness",
     "The gates that must clear before any claim is published, and what would change our mind about the live model.",
     readiness_page, "readiness.html"),
    ("teams.html", "Per-team view",
     "Availability, depth starters and named replacements for all 32 clubs, and the Week 11 venues from NFL.com.",
     teams_page, "teams.html"),
]


def write_pages(site_dir, shell):
    written = []
    for href, title, desc, fn, active in PAGES_T38:
        body = fn()
        slug = href.replace(".html", "")
        with open(os.path.join(site_dir, href), "w", encoding="utf-8") as fh:
            fh.write(shell(slug, title, desc, body, active))
        written.append(href)
    return written
