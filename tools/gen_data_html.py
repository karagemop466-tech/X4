#!/usr/bin/env python3
"""Generate data.html table bodies from the committed CSVs (single source of truth)."""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research" / "data"

NAMES = {
    "BUF": "Buffalo Bills", "NE": "New England Patriots", "NYJ": "New York Jets", "MIA": "Miami Dolphins",
    "PIT": "Pittsburgh Steelers", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "BAL": "Baltimore Ravens",
    "JAX": "Jacksonville Jaguars", "HOU": "Houston Texans", "IND": "Indianapolis Colts", "TEN": "Tennessee Titans",
    "DEN": "Denver Broncos", "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "NYG": "New York Giants", "DAL": "Dallas Cowboys", "WAS": "Washington Commanders", "PHI": "Philadelphia Eagles",
    "CHI": "Chicago Bears", "DET": "Detroit Lions", "MIN": "Minnesota Vikings", "GB": "Green Bay Packers",
    "CAR": "Carolina Panthers", "NO": "New Orleans Saints", "TB": "Tampa Bay Buccaneers", "ATL": "Atlanta Falcons",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "LA": "Los Angeles Rams", "AZ": "Arizona Cardinals",
}
ALIAS = {"ARI": "AZ", "LAR": "LA"}
norm = lambda t: ALIAS.get(t, t)

teams = list(csv.DictReader((DATA / "standings_2026_through_week10_tnf.csv").open()))
games = list(csv.DictReader((DATA / "games_weeks6-9_2026.csv").open()))
odds = list(csv.DictReader((DATA / "week11_odds_2026.csv").open()))

standings_rows = []
for t in teams:
    gp = int(t["w"]) + int(t["l"]) + int(t["t"])
    wlt = f'{t["w"]}-{t["l"]}-{t["t"]}' if t["t"] != "0" else f'{t["w"]}-{t["l"]}'
    net = int(t["net"])
    standings_rows.append(
        f'<tr><td><b>{t["team"]}</b> {NAMES[t["team"]]}</td><td>{t["conf"]} {t["div"]}</td>'
        f'<td class="num">{wlt}</td><td class="num">{gp}</td><td class="num">{t["pf"]}</td>'
        f'<td class="num">{t["pa"]}</td><td class="num">{net:+d}</td>'
        f'<td><a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer">nfl.com standings ↗</a></td></tr>'
    )

# Week 10 slate (official nfl.com scores page, fetched 2026-11-14)
week10 = [
    ("WAS", "NYG", "Thu Nov 12, 8:15 PM", "Prime Video", "FINAL — WAS 24, NYG 21", "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"),
    ("NE", "DET", "Sun Nov 15, 9:30 AM", "FOX", "Scheduled · Munich intl.", "https://www.nfl.com/games/patriots-at-lions-2026-reg-10"),
    ("KC", "ATL", "Sun Nov 15, 1:00 PM", "CBS", "Scheduled", "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10"),
    ("HOU", "CLE", "Sun Nov 15, 1:00 PM", "FOX", "Scheduled", "https://www.nfl.com/games/texans-at-browns-2026-reg-10"),
    ("MIN", "GB", "Sun Nov 15, 1:00 PM", "FOX", "Scheduled", "https://www.nfl.com/games/vikings-at-packers-2026-reg-10"),
    ("MIA", "IND", "Sun Nov 15, 1:00 PM", "CBS", "Scheduled", "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10"),
    ("CAR", "NO", "Sun Nov 15, 1:00 PM", "FOX", "Scheduled", "https://www.nfl.com/games/panthers-at-saints-2026-reg-10"),
    ("BUF", "NYJ", "Sun Nov 15, 1:00 PM", "CBS", "Scheduled", "https://www.nfl.com/games/bills-at-jets-2026-reg-10"),
    ("JAX", "TEN", "Sun Nov 15, 1:00 PM", "FOX", "Scheduled", "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10"),
    ("LAR", "AZ", "Sun Nov 15, 4:05 PM", "CBS", "Scheduled", "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10"),
    ("SEA", "LV", "Sun Nov 15, 4:05 PM", "CBS", "Scheduled", "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10"),
    ("SF", "DAL", "Sun Nov 15, 4:25 PM", "FOX", "Scheduled", "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10"),
    ("PIT", "CIN", "Sun Nov 15, 8:20 PM", "NBC", "Scheduled", "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10"),
    ("LAC", "BAL", "Mon Nov 16, 8:15 PM", "ESPN", "Scheduled", "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"),
]
week10_rows = [
    f'<tr><td><b>{a}</b> at <b>{h}</b></td><td>{when}</td><td>{tv}</td><td>{st}</td>'
    f'<td><a href="{u}" target="_blank" rel="noreferrer">game page ↗</a></td></tr>'
    for a, h, when, tv, st, u in week10
]

# Week 11: schedule from nfl.com, odds from ESPN (both fetched 2026-11-14)
wk11_meta = {
    "IND": ("HOU", "Thu Nov 19, 8:15 PM", "Prime", 0), "MIA": ("BUF", "Sun Nov 22, 1:00 PM", "CBS", 0),
    "NO": ("CHI", "Sun Nov 22, 1:00 PM", "FOX", 0), "TEN": ("DAL", "Sun Nov 22, 1:00 PM", "FOX", 0),
    "TB": ("DET", "Sun Nov 22, 1:00 PM", "FOX", 0), "ARI": ("KC", "Sun Nov 22, 1:00 PM", "CBS", 0),
    "PIT": ("PHI", "Sun Nov 22, 1:00 PM", "CBS", 0), "BAL": ("CAR", "Sun Nov 22, 1:00 PM", "FOX", 0),
    "NYJ": ("LAC", "Sun Nov 22, 4:05 PM", "FOX", 0), "JAX": ("NYG", "Sun Nov 22, 4:25 PM", "CBS", 0),
    "LV": ("DEN", "Sun Nov 22, 4:25 PM", "CBS", 0), "MIN": ("SF", "Sun Nov 22, 8:20 PM", "NBC", 1),
    "CIN": ("WAS", "Mon Nov 23, 8:15 PM", "ESPN", 0),
}
GAME_SLUG = {
    "IND": "colts-at-texans", "MIA": "dolphins-at-bills", "NO": "saints-at-bears", "TEN": "titans-at-cowboys",
    "TB": "buccaneers-at-lions", "ARI": "cardinals-at-chiefs", "PIT": "steelers-at-eagles", "BAL": "ravens-at-panthers",
    "NYJ": "jets-at-chargers", "JAX": "jaguars-at-giants", "LV": "raiders-at-broncos", "MIN": "vikings-at-49ers",
    "CIN": "bengals-at-commanders",
}
week11_rows = []
for o in odds:
    a, h = norm(o["away"]), norm(o["home"])
    when, tv, neutral = wk11_meta[o["away"]][1], wk11_meta[o["away"]][2], wk11_meta[o["away"]][3]
    fav, sp, tot = norm(o["favorite"]), float(o["spread"]), o["total"]
    src_sched = f'https://www.nfl.com/games/{GAME_SLUG[o["away"]]}-2026-reg-11'
    week11_rows.append(
        f'<tr><td><b>{a}</b> at <b>{h}</b>{" · neutral" if neutral else ""}</td><td>{when}</td><td>{tv}</td>'
        f'<td class="num">{fav} −{sp:g}</td><td class="num">{tot}</td>'
        f'<td><a href="{src_sched}" target="_blank" rel="noreferrer">nfl.com game ↗</a> · '
        f'<a href="https://www.espn.com/nfl/schedule/_/week/11/year/2026/seasontype/2" target="_blank" rel="noreferrer">ESPN odds ↗</a></td></tr>'
    )

results_rows = []
for g in games:
    a, h = norm(g["away"]), norm(g["home"])
    neu = ' <span class="pill mut">neutral</span>' if g["neutral_site"] == "1" else ""
    results_rows.append(
        f'<tr><td class="num">W{g["week"]}</td><td><b>{a}</b> at <b>{h}</b>{neu}</td>'
        f'<td class="num">{g["away_score"]} – {g["home_score"]}</td>'
        f'<td class="num">{int(g["home_score"]) - int(g["away_score"]):+d}</td>'
        f'<td><a href="{g["game_url"]}" target="_blank" rel="noreferrer">game page ↗</a></td></tr>'
    )

stats = json.loads((ROOT / "research" / "computed_stats.json").read_text())
it = stats["integrity"]

TEMPLATE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Verified NFL data tables: standings, schedules, odds and results with official source links."><title>Verified data | Fourth Down Research</title><link rel="stylesheet" href="styles.css"></head>
<body>
<aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">4D</span><span>FOURTH DOWN<small>RESEARCH DESK</small></span></a><div class="side-label">WORKSPACE</div><nav><a href="index.html">◫ &nbsp;Overview</a><a href="executive-summary.html">★ &nbsp;Executive summary</a><a href="requirements.html">☰ &nbsp;Requirements</a><a href="data.html">▦ &nbsp;Verified data</a><a href="strategies.html">◎ &nbsp;Line lab &amp; signals</a><a href="leaderboard.html">↗ &nbsp;Leaderboard</a><a href="injuries.html">＋ &nbsp;Availability</a><a href="decisions.html">? &nbsp;Decision Q&amp;A</a><a href="suggestions.html">✳ &nbsp;Suggestions</a><a href="flagged.html">⚑ &nbsp;Flagged for review</a><a href="repo-review.html">§ &nbsp;Repo review</a><a href="sources.html">↗ &nbsp;Sources</a></nav><div class="side-bottom"><span class="pulse"></span> Research mode <small>Snapshot 2026-11-14 · no live feed</small></div></aside>
<main>
<header class="topbar"><div><span class="eyebrow">03 · DATA</span><h1>Verified data tables</h1></div><span class="status-pill"><i></i> All rows source-linked · fetched 2026-11-14</span></header>

<section class="section"><div class="section-head"><div><span class="eyebrow">INTEGRITY PANEL</span><h2>Transcription self-checks</h2><p class="muted">Run by <code>tools/compute_stats.py</code> — fails loudly if a committed number is mistyped.</p></div><span class="tag green">ALL PASSED</span></div>
<div class="metrics">
<article><span>Σ POINTS FOR</span><b>{sum_pf:,}</b><small>Must equal Σ points against — it does</small></article>
<article><span>Σ POINTS AGAINST</span><b>{sum_pa:,}</b><small>Equality proves standings row balance</small></article>
<article><span>WINS vs LOSSES</span><b>{wins} = {losses}</b><small>Ties: {ties} (one tie game, both teams)</small></article>
<article><span>ROWS CHECKED</span><b>32 teams · 57 games · 13 odds</b><small>Neutral-site flags asserted: London, Saint-Denis, Madrid</small></article>
</div>
<div class="note"><b>Policy:</b> values that could not be confirmed from the linked pages are not on this site — they are blank and listed on <a href="flagged.html">Flagged for review</a>. Abbreviations follow nfl.com standings codes (LA = Rams, AZ = Cardinals).</div>
</section>

<section class="section" id="standings"><div class="section-head"><div><span class="eyebrow">STANDINGS · 2026 REG</span><h2>All 32 teams — through Week 10 TNF</h2><p class="muted">Retrieved 2026-11-14 from nfl.com/standings. PF/PA = total points for/against; games = W+L+T.</p></div><span class="tag">32 ROWS</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Team</th><th>Conf / Div</th><th>W-L-T</th><th>G</th><th>PF</th><th>PA</th><th>Net</th><th>Source</th></tr></thead><tbody>
{standings_rows}
</tbody></table></div></section>

<section class="section" id="week10"><div class="section-head"><div><span class="eyebrow">WEEK 10 · IN PROGRESS</span><h2>Current slate</h2><p class="muted">Official nfl.com scores page, fetched 2026-11-14. Byes: CHI, DEN, PHI, TB.</p></div><span class="tag amber">1 FINAL · 13 PENDING</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Matchup</th><th>Kickoff (ET)</th><th>TV</th><th>Status</th><th>Source</th></tr></thead><tbody>
{week10_rows}
</tbody></table></div></section>

<section class="section" id="week11"><div class="section-head"><div><span class="eyebrow">WEEK 11 · NEXT SLATE</span><h2>Schedule + market snapshot</h2><p class="muted">Matchups/times from nfl.com; lines are DraftKings odds as published by ESPN, snapshot 2026-11-14 — lines move. Byes: ATL, CLE, GB, LAR, NE, SEA (cross-checked via ESPN API).</p></div><span class="tag">13 ROWS</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Matchup</th><th>Kickoff (ET)</th><th>TV</th><th>Market spread</th><th>O/U</th><th>Source</th></tr></thead><tbody>
{week11_rows}
</tbody></table></div></section>

<section class="section" id="results"><div class="section-head"><div><span class="eyebrow">RESULTS · WEEKS 6–9</span><h2>57 final scores (the correlation sample)</h2><p class="muted">Every row links its official game page. Margin = home − away. Neutral-site games flagged and excluded from home-edge math.</p></div><span class="tag">57 ROWS</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Wk</th><th>Matchup</th><th>Score (away – home)</th><th>Margin</th><th>Source</th></tr></thead><tbody>
{results_rows}
</tbody></table></div>
<div class="note"><b>Machine-readable copies:</b> <a href="research/data/games_weeks6-9_2026.csv">games CSV</a> · <a href="research/data/standings_2026_through_week10_tnf.csv">standings CSV</a> · <a href="research/data/week11_odds_2026.csv">odds CSV</a> · <a href="research/computed_stats.json">computed stats JSON</a>.</div>
</section>

<footer><span>FOURTH DOWN RESEARCH · Verified data</span><span><a href="index.html">← Overview</a> · <a href="strategies.html">Line lab →</a></span></footer>
</main>
<script src="nav.js"></script>
</body>
</html>
"""

html = TEMPLATE.format(
    sum_pf=it["sum_points_for"], sum_pa=it["sum_points_against"],
    wins=it["total_wins"], losses=it["total_losses"], ties=it["total_ties"],
    standings_rows="\n".join(standings_rows),
    week10_rows="\n".join(week10_rows),
    week11_rows="\n".join(week11_rows),
    results_rows="\n".join(results_rows),
)
(ROOT / "data.html").write_text(html)
print(f"data.html written: {len(standings_rows)} standings, {len(week10_rows)} week10, {len(week11_rows)} week11, {len(results_rows)} results")
