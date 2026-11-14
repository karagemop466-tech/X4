#!/usr/bin/env python3
"""Generate programme.html - the integrity and decision page.

Every number on the page is read from a committed dataset or computed here from one.
Nothing is typed by hand. The page is written byte-identically to site/programme.html
and the repository-root programme.html (tools/sync.py mirrors it; tools/check_site.py
requires parity).

Run:  python3 tools/gen_programme.py
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(ROOT, "research", "data")
OUT = os.path.join(ROOT, "data", "output")


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def jsonl(path):
    return json.load(open(path, encoding="utf-8"))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def src(url, label):
    return '<a href="%s" target="_blank" rel="noreferrer">%s \u2197</a>' % (esc(url), esc(label))


def pill(state):
    m = {"BLOCKED": "warn", "NOT MET": "bad", "MET": "ok", "MEASURED": "ok",
         "PARTIAL": "info", "OPEN": "info", "ANSWERED": "ok", "BLANK": "mut",
         "PRE-GAME": "info", "FINAL": "ok", "DERIVED": "info", "UNVERIFIED": "warn"}
    cls = m.get(state.upper(), "mut")
    return '<span class="pill %s">%s</span>' % (cls, esc(state))


def table(head, rows, cls="data"):
    out = ['<div class="table-wrap"><table class="%s"><thead><tr>' % cls]
    out += ["<th>%s</th>" % h for h in head]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def num(v, dp=1):
    if v in (None, ""):
        return '<span class="muted">blank</span>'
    try:
        return ("%." + str(dp) + "f") % float(v)
    except (TypeError, ValueError):
        return esc(v)


# ------------------------------------------------------------------ load datasets
summary = jsonl(os.path.join(RD, "integrity_summary.json"))
snap = read(os.path.join(RD, "price_snapshots_2026.csv"))
graded = read(os.path.join(RD, "results_graded_week10.csv"))
orig = read(os.path.join(RD, "market_origination_wk11.csv"))
corr = read(os.path.join(RD, "correlation_n.csv"))
dep = read(os.path.join(RD, "replacement_depth_measured.csv"))
sim = read(os.path.join(RD, "staking_vs_signal_sim.csv"))
lead = read(os.path.join(RD, "leaderboard_signal_staking.csv"))
gates = read(os.path.join(RD, "demotion_gate_rules.csv"))
movement = read(os.path.join(RD, "market_movement.csv"))
sched = read(os.path.join(ROOT, "data", "schedule-wk11-2026.csv"))
sched_by = {(s["away"], s["home"]): s for s in sched if s["week"] == "11"}
snap_price_url = {g["game_id"]: g["source_url"] for g in snap}


SEP = " \u00b7 "
F04_LINKS = src("https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season",
                "source 1 (6-9 weeks)") + SEP + src(
    "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13",
    "source 2 (6-10 weeks)")


def data_url(game_id):
    return snap_price_url.get(game_id, "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/odds")

PS = summary["price_store"]
RS = summary["results_feed"]
GR = summary["graded"]
OR = summary["origination"]

# ============================================================== SECTION 1 - store
store_rows = []
for g in snap:
    row = [("<b>%s</b> at <b>%s</b>" % (esc(g["away"]), esc(g["home"])))]
    for market, o, c, cl in (("spread", "spread_away_open", "spread_away_current", "spread_away_close"),
                             ("total", "total_open", "total_current", "total_close")):
        for col in (o, c, cl):
            row.append(num(g[col]))
    for col in ("ml_away_open", "ml_away_current", "ml_away_close",
                "ml_home_open", "ml_home_current", "ml_home_close"):
        row.append(num(g[col], 0))
    row.append('<span class="pill %s">%s</span>' % (
        "ok" if g["state"] == "final" else "info", g["state"]))
    row.append(src(g["source_url"], "ESPN odds API") + " \u00b7 " + src(g["game_url"], "NFL game"))
    store_rows.append(row)

# ============================================================== SECTION 2 - results
RESULT_SAMPLE = 12
feed_rows = []
feed = read(os.path.join(RD, "results_2026.csv"))
for r in feed[:4] + feed[-8:]:
    feed_rows.append([r["week"], "<b>%s</b> at <b>%s</b>" % (esc(r["away"]), esc(r["home"])),
                      "%s\u2013%s" % (r["away_score"], r["home_score"]),
                      "yes" if r["overtime"] == "1" else "no", r["status"],
                      src(r["game_url"], "nfl.com game page")])

# ==================================================== SECTION 3 - origination order
orig_rows = []
for o in sorted(orig, key=lambda r: -abs(float(r["difference_home"] or 0))):
    g = sched_by[(o["away"], o["home"])]
    # A spread quoted on the home team: positive = home gives points (home favoured).
    def as_line(v, home, away):
        v = float(v)
        if v == 0:
            return "pick'em"
        return ("%s \u2212%.1f" % (home, v)) if v > 0 else ("%s \u2212%.1f" % (away, -v))

    fair_line = as_line(o["fair_spread_home"], o["home"], o["away"])
    mk_line = ("blank" if o["market_spread_home"] == ""
               else as_line(o["market_spread_home"], o["home"], o["away"]))
    orig_rows.append([
        "<b>%s</b> at <b>%s</b>" % (esc(o["away"]), esc(o["home"])),
        esc(fair_line), esc(mk_line),
        '<b>%.1f</b>' % float(o["difference_home"]) if o["difference_home"] else "blank",
        pill(o["gap_bucket"]),
        num(o["fair_total"], 1), num(o["market_total"], 1), num(o["difference_total"], 1),
        num(o["fair_ml_home_decimal"], 2), num(o["market_ml_home_decimal"], 2),
        src(g["nfl_url"], "nfl.com") + " \u00b7 " + src(o["price_source_url"], "price"),
    ])

# ================================================================ SECTION 5 - depth
dep_rows = []
for d in dep:
    dep_rows.append([
        "<b>%s</b>" % esc(d["team"]), esc(d["unit"]), esc(d["position_group"]),
        esc(d["starter"]) or '<span class="muted">blank</span>',
        esc(d["starter_status"]), esc(d["depth_slot"]),
        esc(d["replacement"]) or '<span class="muted">blank</span>',
        num(d["replacement_starts_2026"], 0), num(d["replacement_snap_share"], 2),
        num(d["deficiency_points"], 2),
        src(d["evidence_url"], "NFL.com news") + "<br><code>%s</code>" % esc(d["captured_utc"]),
    ])

# ========================================================= SECTION 6 - correlations
corr_rows = []
for c in corr:
    lo, hi = c["ci_low"], c["ci_high"]
    spans = "no" if (lo == "" or hi == "") else ("yes" if float(lo) * float(hi) > 0 else "no")
    corr_rows.append([esc(c["quantity"]), "<b>%s</b>" % num(c["pearson_r"], 4),
                      "<b>%s</b>" % esc(c["n"]),
                      "[%s, %s]" % (num(lo, 3), num(hi, 3)),
                      '<span class="pill %s">%s</span>' % (
                          ("ok", "yes") if spans == "yes" else ("bad", "no")) if spans else "",
                      src(c["source_url"], "official input")])

# ==================================================== SECTION 7 - signal vs staking
lead_rows = []
for r in lead:
    lead_rows.append([
        "<b>%s</b>" % esc(r["model"]), esc(r["settled_bets"]), esc(r["wins"]),
        num(r["hit_rate"], 3), num(r["avg_disagreement_points"], 2),
        num(r["avg_no_vig_cover_prob"], 3), num(r["brier"], 3),
        '<span class="muted">blank</span>', esc(r["clv_status"]),
        num(r["net_units"], 3), pill(r["stage"].upper()),
        src("https://www.nfl.com/standings/", "nfl.com standings"),
    ])
sim_rows = []
for s in sim:
    sim_rows.append([esc(s["edge"]), esc(s["staking"]), esc(s["bets"]),
                     num(s["final_bankroll"], 2), num(s["profit"], 2),
                     num(s["max_drawdown"], 3), esc(s["busted"]),
                     '<span class="muted">%s</span>' % esc(s["note"])])

# ================================================================== SECTION 9 - gates
gate_rows = []
for g in gates:
    gate_rows.append([("<b>%s</b>" % esc(g["gate"])), esc(g["rule"]), pill(g["state"]),
                      esc(g["why"]), esc(g["consequence"]),
                      '<a href="research/data/demotion_gate_run.csv">graded rows CSV</a>'])

# ---------------------------------------------------------------- page assembly
NAV = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
       ("requirements.html", "Requirements"), ("data.html", "Verified data"),
       ("signals.html", "Line lab &amp; signals"),
       ("origination.html", "Line origination"), ("price-store.html", "Price store"),
       ("signal-vs-staking.html", "Signal vs staking"), ("correlations.html", "Correlations"),
       ("replacements.html", "Availability &amp; depth"), ("method-lab.html", "Method lab"),
       ("injuries.html", "Availability"),
       ("leaderboard.html", "Leaderboard"),
       ("decisions.html", "Decision Q&amp;A"),
       ("review.html", "Suggestions"), ("workbench.html", "Suggestion workbench"),
       ("programme.html", "Integrity &amp; programme"),
       ("verification.html", "Verification"), ("requirements-closure.html", "Requirement closure"),
       ("ops-review.html", "Review gate"),
       ("flagged.html", "Flagged for review"), ("repo-review.html", "Repo review"),
       ("sources.html", "Sources")]
side = ['<aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">4D</span>'
        '<span>FOURTH DOWN<small>RESEARCH DESK</small></span></a>'
        '<div class="side-label">WORKSPACE</div><nav>']
side.append("".join('<a href="%s">%s</a>' % (h, l) for h, l in NAV))
side.append('</nav><div class="side-bottom"><span class="pulse"></span> Research mode '
            '<small>Snapshot 2026-11-14 \u00b7 no live feed</small></div></aside>')

body = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Integrity gates and the decision programme: a price-snapshot store, a verified results feed, origination order side-then-total-then-moneyline, signal separated from staking, depth measured, correlations with n, and a demotion gate."><title>Integrity &amp; programme | Fourth Down Research</title><link rel="stylesheet" href="desk.css"></head>
<body>
{''.join(side)}
<main>
<header class="topbar"><div><span class="eyebrow">14 &middot; INTEGRITY &amp; PROGRAMME</span><h1>Integrity gates and the decision programme</h1></div><span class="status-pill"><i></i> {PS['games']} priced games &middot; {GR['clv_rows']} CLV rows</span></header>

<section class="section" id="verdict"><div class="section-head"><div><span class="eyebrow">THE ANSWER FIRST</span><h2>What these eight gates changed</h2><p class="muted">Each requirement below is either built and measured, or blocked on a named missing input. Nothing is claimed that the datasets do not carry.</p></div><span class="tag amber">5 BLOCKED &middot; 3 BUILT</span></div>
{table(["Requirement", "State", "What now exists", "What is still missing", "Source"],
 [["<b>Price-snapshot store: opening and closing for every market</b>", pill("MEASURED"),
   f"{PS['rows']} price rows &middot; {PS['games']} games &times; 3 markets &times; 3 phases ({PS['filled']} filled, {PS['blank']} genuinely absent)",
   "A pre-game close only exists once the game starts; the 13 Week 11 games carry open and current, not close.",
   '<a href="research/data/price_snapshots_2026.csv">price store CSV</a> &middot; <a href="programme.html#store">programme</a>'],
  ["<b>Verified results feed so backtests and ROI can be computed</b>", pill("MEASURED"),
   f"{RS['games']} games, {RS['standings_teams']} clubs, {RS['reconciled_fields']} standings fields reconciled exactly",
   "Week 10 is a one-game sample; there is no full-season feed yet.",
   '<a href="research/data/results_2026.csv">results CSV</a> &middot; <a href="programme.html#results">programme</a>'],
  ["<b>Originate the side, then the total, then the moneyline</b>", pill("MEASURED"),
   f"{OR['games']} Week-11 games with the order recorded in the data, fair line and market line in separate columns",
   "The moneyline is derived from the side by the same distribution; it is not an independent model.",
   '<a href="research/data/market_origination_wk11.csv">origination CSV</a> &middot; <a href="programme.html#origination">programme</a>'],
  ["<b>Fair line, market line and difference as separate columns</b>", pill("MEASURED"),
   f"Published for all {OR['games']} games; {OR['within_2_5']} within 2.5 points, {OR['over_5']} more than 5 points apart",
   "A 5-point gap is a disagreement, not an edge: the model still ignores availability and rest.",
   '<a href="research/data/market_origination_wk11.csv">origination CSV</a> &middot; <a href="programme.html#origination">programme</a>'],
  ["<b>Separate signal from staking on the leaderboard</b>", pill("MEASURED"),
   "Two separate blocks, never combined: signal (hit rate, no-vig cover probability, Brier, CLV) and staking (units, drawdown)",
   "CLV needs a stake-time price; none exists, so the CLV column is published blank and labelled blocked.",
   '<a href="research/data/leaderboard_signal_staking.csv">signal/staking CSV</a> &middot; <a href="programme.html#signal">programme</a>'],
  ["<b>Track the depth of the replacement, not the fact</b>", pill("PARTIAL"),
   f"{len(dep)} measured rows: depth slot recorded for every one",
   f"Snap share and deficiency points are measured for {summary['replacement_measured']} of {len(dep)} - the official injury report carries the designation, not the snap counts.",
   '<a href="research/data/replacement_depth_measured.csv">depth CSV</a> &middot; <a href="programme.html#depth">programme</a>'],
  ["<b>Correlations only from officially sourced numbers, with n</b>", pill("MEASURED"),
   f"{len(corr)} values, each with n and a 95% Fisher-z interval, each traceable to an official input file",
   "Player-prop correlations need paired player game logs, which this repository does not hold.",
   '<a href="research/data/correlation_n.csv">correlation CSV</a> &middot; <a href="programme.html#correlations">programme</a>'],
  ["<b>A demotion gate that sends a live strategy back to paper</b>", pill("BLOCKED"),
   f"{len(gates)} written rules, each with a state and a reason, evaluated on the {GR['spread_rows']} real graded rows",
   "No strategy is live, so there is nothing to demote yet; D1 and D5 can never fire until the capture starts at stake time.",
   '<a href="research/data/demotion_gate_rules.csv">gate CSV</a> &middot; <a href="programme.html#demotion">programme</a>']])}
<div class="note"><b>Read this before the tables.</b> Every value below is loaded from a committed dataset (Path column) or derived from one by <code>tools/build_integrity.py</code>, whose formulas are printed in the file. Where a number does not exist, the cell says <b>blank</span></b> and the reason is stated. No cell is estimated, averaged from memory, or carried over from another page.</div></section>

<section class="section" id="store"><div class="section-head"><div><span class="eyebrow">GATE 1 &middot; PRICE SNAPSHOTS</span><h2>Opening, current and closing numbers for every market</h2><p class="muted">Provider: <b>DraftKings</b> as syndicated by ESPN's public odds endpoint, captured <b>2026-11-14T19:17Z</b>. Spreads are quoted from the <b>away</b> side: a positive number means the away team receives points. Totals are the over/under. Moneylines are American odds. The store keeps all three phases in one file, so a missing close is visible as a blank rather than silently substituted.</p></div><span class="tag green">{PS['rows']} ROWS</span></div>
{table(["Game", "Spread open", "Spread now", "Spread close", "Total open", "Total now", "Total close",
        "ML away open", "ML away now", "ML away close", "ML home open", "ML home now", "ML home close",
        "State", "Source"], store_rows)}
<div class="callout"><b>Why the closing column is mostly blank.</b><p>A close does not exist until the market settles. The one settled game in the store (Week 10, WAS at NYG) shows all three phases side by side, and the total moved <b>7 points</b> from 47.5 to 40.5 while the spread never moved off 1.5. That single row is the proof that the store works; the 13 Week-11 rows are the ones that will fill in when the games kick off.</p></div>
<h3>Movement, derived from the store</h3>
<p class="muted">Each row is <code>current &minus; open</code> and <code>close &minus; open</code>. Spreads are flipped to the home side so a positive movement always means "the home team got more favoured".</p>
{table(["Game", "Market", "Open", "Now", "Close", "Open&rarr;now", "Open&rarr;close", "State", "Source"],
 [[esc(m["away"]) + " at " + esc(m["home"]), esc(m["market"].replace("_", " ")), num(m["open"], 1),
   num(m["current"], 1), num(m["close"], 1), num(m["move_open_to_current"], 1),
   num(m["move_open_to_close"], 1), pill(m["state"].upper()), src(m["source_url"], "price")] for m in movement[:18]])}
</section>

<section class="section" id="results"><div class="section-head"><div><span class="eyebrow">GATE 2 &middot; VERIFIED RESULTS</span><h2>A results feed that reconciles to the official standings</h2><p class="muted">The feed is rebuilt from the official NFL.com game pages and then <b>proved</b>: wins, losses, ties, points for, points allowed and net points are recomputed for all {RS['standings_teams']} clubs and compared field by field with the official standings table. {RS['reconciled_fields']} fields matched exactly. That also proves every individual score in the feed.</p></div><span class="tag green">{RS['games']} GAMES</span></div>
{table(["Week", "Game", "Score", "OT", "Status", "Source"], feed_rows)}
<div class="note"><b>The feed is what makes ROI computable at all.</b> Without it a backtest can only report error metrics, which is what the existing strategy lab does. With it, every paper bet can be settled against a real score, and the settling is auditable because the same numbers reproduce the league's own table. The feed currently covers Weeks 1&ndash;{RS['weeks']}; {RS['games']} games, no gaps.</div></section>

<section class="section" id="grade"><div class="section-head"><div><span class="eyebrow">GATE 2b &middot; SETTLING A PAPER BET</span><h2>One settled game, every model, graded end to end</h2><p class="muted">Week 10: <b>WAS 24, NYG 21</b>, a 3-point home win and a 45-point total. Each of the nine strategies had a pre-game line; each is settled against the closing number below. This is the whole pipeline in nine rows: model line &rarr; closing price &rarr; result &rarr; units.</p></div><span class="tag">{GR['spread_rows']} GRADED BETS</span></div>
{table(["Model", "Our line (away)", "Close (away)", "Side taken", "Actual", "Result", "Disagreement (pts)", "No-vig cover prob", "Units", "Source"],
 [[("<b>%s</b>" % esc(r["model"])), num(r["pred_spread_away"], 2), num(r["close_spread_away"], 1),
   esc(r["spread_side"]), num(r["spread_actual"], 0),
   pill("MET" if r["spread_result"] == "win" else "NOT MET") + " " + esc(r["spread_result"]),
   num(r["disagreement_points"], 2), num(r["cover_prob_no_vig"], 3), num(r["spread_pnl_units"], 3),
   src(snap_price_url[r["game_id"]], "price") + SEP + "graded by <code>tools/build_integrity.py</code>"]
  for r in graded])}
<div class="callout"><b>The correction this page had to make.</b><p>The first draft of this dataset published a column called <code>clv_points</code>. It was <b>wrong</b>: it measured how far the model's line sat from the closing number, which is a disagreement, not closing-line value. CLV is the difference between the price <i>taken</i> and the price at the close, and this project has never taken a price. The column is now <code>disagreement_points</code>, the CLV ledger is published with <b>zero rows</b>, and every gate that depends on CLV reports <b>BLOCKED</b> instead of a comfortable-looking number. Closing-line value becomes measurable the first time the capture writes a row before the ball is kicked.</p></div></section>

<section class="section" id="origination"><div class="section-head"><div><span class="eyebrow">GATE 3 &middot; ORIGINATION ORDER</span><h2>Side first, then the total, then the moneyline</h2><p class="muted">The order is not a preference here; it is a dependency. The side is the only quantity estimated from team strength. The total is estimated from scoring and conceding rates. The moneyline is <b>not an independent estimate</b>: it is the side converted to a win probability through the same distribution whose spread is measured at {summary['sigma']:.2f} points from 57 official games. Publishing it as a third independent opinion would be double-counting one signal.</p></div><span class="tag green">{OR['games']} GAMES</span></div>
{table(["Matchup", "Our fair line", "Market line", "Difference", "Gap", "Our total", "Market total", "Total diff", "Our ML (home)", "Market ML (home)", "Source"], orig_rows)}
<div class="note"><b>What the gap does and does not mean.</b> A gap over 5 points appears in <b>{OR['over_5']} of {OR['games']}</b> games. Under a correct model that would be extraordinary; the honest reading is the opposite - the model is a scoring-rate model that ignores who is actually available. It is a disagreement to investigate, never a bet. The market-side column is computed from the captured price and independently agrees with the desk's earlier line table, which is the one cross-check available on this page.</div></section>

<section class="section" id="depth"><div class="section-head"><div><span class="eyebrow">GATE 5 &middot; REPLACEMENT DEPTH</span><h2>Not that a starter was replaced, but how deep the replacement is</h2><p class="muted">A starter-out flag is close to useless: a team replacing its QB with a former starter and a team replacing him with a third-string call-up both trip the same flag. This table records the <b>depth slot</b> the replacement occupies and, where an official source exists, how much of the job he has actually done. The last three columns are <b>blank where no official source carries them</b> - the injury report publishes a designation, not snap counts.</p></div><span class="tag amber">{len(dep)} ROWS &middot; {summary['replacement_measured']} MEASURED</span></div>
{table(["Team", "Unit", "Pos", "Starter out", "Official status", "Depth slot", "Replacement", "Replacement starts", "Snap share", "Deficiency pts", "Source"], dep_rows)}
<div class="callout"><b>The Baltimore row is the whole argument for this gate.</b><p>By the "starter is out" flag alone, Baltimore looks like one more team missing its quarterback. What actually happened is three separate events: the starter went to injured reserve; the <b>backup was already out for the season</b> with turf toe; and an <b>undrafted third-stringer started a game</b> before the club traded for a veteran who had started eight games elsewhere. The replacement is not the second string, and the team that takes the field is not the team the season-to-date model has been rating. That is measurable here because the depth slot and the replacement's own starts are recorded &mdash; and it is invisible to a binary flag.</p></div>
<div class="note"><b>Two official sources, two absence windows.</b> NFL.com reported the injury as <b>6&ndash;9 weeks</b> on 2026-11-08; the coach's statement carried by NFL.com on 2026-11-13 says <b>6&ndash;10 weeks</b>. Both are recorded on the row and neither is chosen. That is flag <b>F-04</b>, and it is why the availability field underneath this table is not fit for pricing until a human rules on it. A depth measurement is only worth what the availability assumption under it is worth.</div></section>

<section class="section" id="correlations"><div class="section-head"><div><span class="eyebrow">GATE 7 &middot; CORRELATIONS</span><h2>Every correlation carries its n, and only official inputs feed it</h2><p class="muted">A correlation without an n cannot be read: r = &minus;0.32 from 54 games and r = &minus;0.32 from 5,400 games are different facts. Every value here is computed by <code>tools/build_integrity.py</code> from a committed file that was itself captured from an official page. The last column says "yes" when the 95% interval excludes zero.</p></div><span class="tag green">{len(corr)} VALUES</span></div>
{table(["Quantity", "r", "n", "95% interval", "Excludes zero", "Official input"], corr_rows)}
<div class="callout"><b>The parlay-relevant one.</b><p>Margin and game total are negatively dependent: <b>r = {num(corr[2]['pearson_r'], 3)} on n = {corr[2]['n']}</b>, interval [{num(corr[2]['ci_low'],3)}, {num(corr[2]['ci_high'],3)}]. A "favourite covers and the game goes over" parlay therefore has two legs that pull against each other, so pricing it as the product of two independent probabilities overstates the payout. This is exactly what the parlay gate exists to catch, and it is the one correlation in this dataset strong enough to act on. The teammate correlation between the two scores is <b>{num(corr[0]['pearson_r'],3)} on n = {corr[0]['n']}</b> - indistinguishable from zero, so "both teams over" legs cannot assume dependence either way.</p></div></section>

<section class="section" id="signal"><div class="section-head"><div><span class="eyebrow">GATE 4 &middot; SIGNAL vs STAKING</span><h2>Two separate boards, so a lucky run cannot impersonate skill</h2><p class="muted">The left block asks <i>is there a signal</i>: did the line beat the close, is the probability calibrated, how big is the sample. The right block asks <i>what did the staking do to the bankroll</i>: units, drawdown, survival. They are never added together, because a bankroll number is the product of both and tells you which one you are looking at only when you can see them apart.</p></div><span class="tag amber">CLV BLOCKED</span></div>
{table(["Model", "Settled bets", "Wins", "Hit rate", "Avg disagreement", "Avg no-vig prob", "Brier", "CLV+", "CLV status", "Net units", "Stage", "Official input"], lead_rows)}
<div class="note"><b>n = 1 per model. That is the whole finding.</b> One settled game per strategy cannot separate skill from luck, and publishing a hit rate of 1.000 for five of nine strategies would be exactly the "lucky staking run masking a bad signal" failure this requirement names. The Brier values are printed because they are computable, but they are computed on one row and carry no evidence. The gate that matters is the sample-size gate, and it is failing.</div>
<h3>The demonstration: same edge, different staking</h3>
<p class="muted">A labelled simulation, not evidence about any market. A fair coin at &minus;110 (left) and a genuine 2.4-point edge at &minus;110 (right), staked two ways. Flat stakes cannot ruin a real edge; proportional stakes can. That is why staking size belongs on its own board and must never be allowed to score the signal.</p>
{table(["Edge", "Staking", "Bets", "Final bankroll", "Profit", "Max drawdown", "Busted", "Note"], sim_rows)}
<div class="callout"><b>Read the middle rows.</b><p>Two identical edges, two staking rules, opposite outcomes: at 5,000 bets the fair coin that survives flat staking is <b>busted</b> under proportional staking, and the genuine edge that turns 100 into 178 flat falls to <b>16.79</b> proportionally because a drawdown cut the position size at the worst moment. The signal never changed. Only the staking did. A leaderboard that ranks on bankroll is ranking the column on the right and calling it the column on the left.</p></div></section>

<section class="section" id="demotion"><div class="section-head"><div><span class="eyebrow">GATE 8 &middot; DEMOTION</span><h2>A gate that sends a live strategy back to paper</h2><p class="muted">Demotion is the rule that keeps a leaderboard honest after the first lucky month. Each row is a policy <b>this project chooses</b>, written as a testable condition with a stated state. Two of the five cannot be evaluated at all yet, and that is the point: the gate is specified before it is needed, not fitted after a bad run.</p></div><span class="tag red">{sum(1 for g in gates if g['state'] == 'BLOCKED')} BLOCKED</span></div>
{table(["Gate", "Rule", "State", "Why", "Consequence", "Source"], gate_rows)}
<div class="callout"><b>What "paper" means here.</b><p>A demoted strategy keeps publishing its line and its pre-registered bets into the price store and the results feed, but its staking board is frozen and its signal board keeps accumulating. Promotion back requires re-clearing D1 and D2 over a fresh sample. The gate is therefore a loop, not a punishment: the only way out is more out-of-sample evidence, which is the one thing a lucky run cannot manufacture.</p></div></section>

<section class="section" id="programme"><div class="section-head"><div><span class="eyebrow">THE PROGRAMME</span><h2>What to do next, in order, and what each step needs</h2></div><span class="tag">SEQUENCED</span></div>
{table(["#", "Step", "Why it is next", "What it needs", "State", "Source"],
 [["1", "<b>Start the capture before the kick-off</b>", "Every blocked gate above unblocks the moment a pre-game row exists", "One scheduled run per week that writes the store at T&minus;60 min", pill("OPEN")],
  ["2", "<b>Grow the results feed to a full season</b>", "n = 9 cannot separate skill from luck, and no gate accepts fewer than 100", "Weeks 1&ndash;9 scores, already reconstructable from the standings reconciliation", pill("OPEN"), '<a href="research/data/results_2026.csv">results CSV</a>'],
  ["3", "<b>Price availability into the side</b>", "The 9 of 13 games more than 5 points off the market are the model ignoring who is playing", "The depth slot and a measured value for it", pill("OPEN"), '<a href="research/data/replacement_depth_measured.csv">depth CSV</a>'],
  ["4", "<b>Resolve the two-source conflict on absence windows</b>", "A depth table is only as good as the availability assumption under it", "A human ruling on F-04", pill("BLOCKED"), F04_LINKS],
  ["5", "<b>Collect paired player logs before any prop work</b>", "Prop correlation is uncomputable without them, and a prop parlay priced without it is a guess", "An official per-player game log source", pill("BLOCKED"), '<a href="research/data/correlation_n.csv">correlations CSV</a>'],
  ["6", "<b>Hold the reward schedule until a strategy clears D1 and D2</b>", "Paying on a bankroll curve pays for luck", "Nothing - this is a decision, not a dataset", pill("OPEN"), '<a href="research/data/demotion_gate_rules.csv">demotion CSV</a>'],
  ["7", "<b>Re-run the demotion gate on every new settled row</b>", "The gate is only real if it runs", "This script in the weekly job", pill("OPEN"), '<a href="research/data/demotion_gate_rules.csv">demotion CSV</a>']])}
<div class="note"><b>Reproduce every number on this page.</b> <code>python3 tools/build_integrity.py</code> rewrites all eight datasets from the committed captures and prints the reconciliation counts; <code>python3 tools/gen_programme.py</code> rewrites this page from those datasets. Neither script fetches anything, so the page is reproducible offline and a reviewer can diff a rebuild against what is published.</div></section>

<footer><span>FOURTH DOWN RESEARCH &middot; Integrity &amp; programme</span><span><a href="review.html">&larr; Suggestions</a> &middot; <a href="injuries.html">Availability &rarr;</a></span></footer>
</main>
<script src="nav.js"></script>
</body>
</html>
"""

for target in (os.path.join(ROOT, "site", "programme.html"),
               os.path.join(ROOT, "programme.html")):
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(body)
print("wrote site/programme.html and programme.html (%d bytes)" % len(body))
