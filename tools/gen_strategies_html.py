#!/usr/bin/env python3
"""Generate strategies.html — line lab and correlation tables derived from research/computed_stats.json."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "research" / "computed_stats.json").read_text())
GAME_SLUG = {"IND":"colts", "HOU":"texans", "MIA":"dolphins", "BUF":"bills", "NO":"saints", "CHI":"bears", "TEN":"titans", "DAL":"cowboys", "TB":"buccaneers", "DET":"lions", "ARI":"cardinals", "KC":"chiefs", "PIT":"steelers", "PHI":"eagles", "BAL":"ravens", "CAR":"panthers", "NYJ":"jets", "LAC":"chargers", "LV":"raiders", "DEN":"broncos", "JAX":"jaguars", "NYG":"giants", "MIN":"vikings", "SF":"49ers", "CIN":"bengals", "WAS":"commanders"}

def fmt_delta(d):
    cls = "pill warn" if abs(d) >= 5 else ("pill info" if abs(d) >= 2.5 else "pill ok")
    label = "investigate" if abs(d) >= 5 else ("watch" if abs(d) >= 2.5 else "close")
    return f'<span class="{cls}">{d:+.1f}</span> <span class="muted">{label}</span>'

line_rows = []
for g in S["week11_baseline_lines"]:
    a, h = g["away"], g["home"]
    neu = ' <span class="pill mut">neutral</span>' if g["neutral"] else ""
    market_available = g["market_spread"] is not None and g["mkt_total"] is not None
    mkt = f"{g['market_favorite']} −{g['market_spread']:g}" if market_available else ""
    mkt_total = f"{g['mkt_total']:g}" if market_available else ""
    spread_delta = fmt_delta(g["delta_margin"]) if market_available else ""
    total_delta = fmt_delta(g["delta_total"]) if market_available else ""
    src = f"https://www.nfl.com/games/{GAME_SLUG[a]}-at-{GAME_SLUG[h]}-2026-reg-11"
    my_home = g["my_home_margin"]
    # express my line as favorite-spread convention for readability
    if my_home >= 0:
        my_str = f"{h} −{my_home:.1f}"
    else:
        my_str = f"{a} −{abs(my_home):.1f}"
    line_rows.append(
        f'<tr><td><b>{a}</b> at <b>{h}</b>{neu}</td><td class="num">{my_str}</td>'
        f'<td class="num">{g["my_total"]:.1f}</td><td class="num blank" aria-label="Unverified; left blank">{mkt}</td>'
        f'<td class="num blank" aria-label="Unverified; left blank">{mkt_total}</td><td class="num blank">{spread_delta}</td>'
        f'<td class="num blank">{total_delta}</td>'
        f'<td><a href="{src}" target="_blank" rel="noreferrer">official NFL fixture ↗</a></td></tr>'
    )

def crow(key, label, reading, official):
    c = S["correlations"][key]
    return (f'<tr><td><b>{label}</b> </td><td class="num">r = {c["r"]:+.3f}</td>'
            f'<td class="num">[{c["ci95"][0]:+.2f}, {c["ci95"][1]:+.2f}]</td><td class="num">{c["n"]}</td>'
            f'<td>{reading}</td>'
            f'<td><a href="research/computed_stats.json">computed JSON ↗</a> · <a href="data.html#results">input rows ↗</a> · '
            f'<a href="{official}" target="_blank" rel="noreferrer">official ↗</a></td></tr>')

h = S["home_edge"]
home_row = (f'<tr><td><b>Mean home-field margin</b> </td><td class="num">{h["mean_home_margin"]:+.2f} pts</td>'
            f'<td class="num">[{h["ci95"][0]:+.1f}, {h["ci95"][1]:+.1f}]</td><td class="num">{h["n"]}</td>'
            f'<td>Essentially zero in this window (home win rate {h["home_win_pct"]*100:.1f}%) — too unstable to lean on; carried with wide uncertainty</td>'
            f'<td><a href="research/computed_stats.json">computed JSON ↗</a> · <a href="data.html#results">input rows ↗</a> · '
            f'<a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer">nfl.com standings ↗</a></td></tr>')

TEMPLATE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Line origination lab, candidate signals, validation gates, computed correlations and skill protocol."><title>Line lab &amp; strategies | Fourth Down Research</title><link rel="stylesheet" href="desk.css"></head>
<body>
<aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">4D</span><span>FOURTH DOWN<small>RESEARCH DESK</small></span></a><div class="side-label">WORKSPACE</div><nav><a href="index.html">◫ &nbsp;Overview</a><a href="executive-summary.html">★ &nbsp;Executive summary</a><a href="requirements.html">☰ &nbsp;Requirements</a><a href="data.html">▦ &nbsp;Verified data</a><a href="signals.html">◎ &nbsp;Line lab &amp; signals</a><a href="leaderboard.html">↗ &nbsp;Leaderboard</a><a href="injuries.html">＋ &nbsp;Availability</a><a href="decisions.html">? &nbsp;Decision Q&amp;A</a><a href="review.html">✳ &nbsp;Suggestions</a><a href="flagged.html">⚑ &nbsp;Flagged for review</a><a href="repo-review.html">§ &nbsp;Repo review</a><a href="sources.html">↗ &nbsp;Sources</a></nav><div class="side-bottom"><span class="pulse"></span> Research mode <small>Snapshot 2026-11-14 · no live feed</small></div></aside>
<main>
<header class="topbar"><div><span class="eyebrow">04 · SIGNALS</span><h1>Line lab &amp; strategies</h1></div><span class="status-pill"><i></i> Baseline v0 · gates not run</span></header>

<section class="section" id="line-lab"><div class="section-head"><div><span class="eyebrow">ORIGINATING LINES</span><h2>Week 11 — originated baseline lines</h2><p class="muted">Model: <code>spread = (S_home − S_away) + h</code> where <code>S = PF/g − PA/g</code> from official standings (through Week-10 TNF) and <code>h = +0.07</code> (measured home edge, weeks 6–9). Totals: mean of each team's points-per-game-in-their-games. Market spread/total and deltas are blank: NFL.com publishes no official betting odds.</p></div><span class="tag">13 GAMES</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Matchup</th><th>My spread</th><th>My total</th><th>Market spread</th><th>Market O/U</th><th>Spread Δ</th><th>Total Δ</th><th>Source</th></tr></thead><tbody>
{line_rows}
</tbody></table></div>
<div class="note"><b>Market fields:</b> spread, total and deltas are intentionally blank because the NFL does not publish official betting odds. Third-party snapshots are excluded under the official-source-only rule. Full inputs: <a href="research/data/standings_2026_through_week10_tnf.csv">standings CSV</a> · <a href="research/data/week11_odds_2026.csv">market fields CSV (blank)</a> · reproduce with <code>python3 tools/compute_stats.py</code>.</div>
<div class="callout"><b>What v0 deliberately excludes</b> <p>Player availability, quarterback changes, rest/travel, weather, motivation/standings context, and market timing. Each is a candidate signal below; each must clear the gates before it enters a production line.</p></div>
</section>

<section class="section" id="signals"><div class="section-head"><div><span class="eyebrow">CANDIDATE SIGNALS</span><h2>Signal inventory</h2><p class="muted">A signal is a hypothesis until it clears every gate. "Computed" means a value exists today from official data; "blocked" means a required input is missing and flagged.</p></div><span class="tag">10 SIGNALS</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>#</th><th>Signal</th><th>What it measures</th><th>Official input source</th><th>State</th><th>Source</th></tr></thead><tbody>
<tr><td>S1</td><td><b>Point-differential strength</b> </td><td>S = PF/g − PA/g; season-to-date team quality</td><td>Standings PF/PA</td><td><span class="pill ok">computed · in v0</span></td><td><a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer">nfl.com standings ↗</a></td></tr>
<tr><td>S2</td><td><b>Home-field edge</b> </td><td>Mean home margin, neutral games excluded</td><td>Game results Wks 6–9</td><td><span class="pill warn">computed · CI spans 0</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-9" target="_blank" rel="noreferrer">nfl.com Wk9 results ↗</a></td></tr>
<tr><td>S3</td><td><b>Scoring environment</b> </td><td>League mean/SD of game totals for totals lines</td><td>Game results Wks 6–9</td><td><span class="pill ok">computed · in v0</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-8" target="_blank" rel="noreferrer">nfl.com Wk8 results ↗</a></td></tr>
<tr><td>S4</td><td><b>Market divergence</b> </td><td>|my line − market| as an investigation queue</td><td>Official odds source unavailable</td><td><span class="pill bad">blocked · market values blank</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noreferrer">NFL schedule; no odds ↗</a> · <a href="flagged.html">R-14 ↗</a></td></tr>
<tr><td>S5</td><td><b>Availability adjustments</b> </td><td>Practice/game statuses feeding lineup-sensitive features</td><td>NFL official injury report</td><td><span class="pill warn">sampled · no feed</span></td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer">nfl.com injuries ↗</a></td></tr>
<tr><td>S6</td><td><b>Depth-string deficiency</b> </td><td>Starter ruled out → 2nd/3rd/4th-string replacement impact, O and D units</td><td>Depth chart + injury report</td><td><span class="pill bad">blocked · depth chart 404</span></td><td><a href="https://www.nfl.com/teams/depth-charts/" target="_blank" rel="noreferrer">depth-chart URL (404) ↗</a> · <a href="flagged.html">R-03 ↗</a></td></tr>
<tr><td>S7</td><td><b>Rest / schedule spots</b> </td><td>Bye, short week, international travel, Thursday turnaround</td><td>Official schedule</td><td><span class="pill info">specified · not tested</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noreferrer">nfl.com schedule ↗</a></td></tr>
<tr><td>S8</td><td><b>Weather</b> </td><td>Wind/precipitation vs totals and passing efficiency</td><td>Venue weather (to be selected)</td><td><span class="pill bad">blocked · source undecided</span></td><td><a href="https://www.nfl.com/scores/" target="_blank" rel="noreferrer">nfl.com scores (weather shown) ↗</a> · <a href="flagged.html">F-07 ↗</a></td></tr>
<tr><td>S9</td><td><b>Closing-line value (CLV)</b> </td><td>My price vs closing price — the premier skill proxy</td><td>Timestamped odds feed</td><td><span class="pill bad">blocked · no feed history</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noreferrer">NFL schedule (odds unavailable) ↗</a> · <a href="flagged.html">F-03, R-14 ↗</a></td></tr>
<tr><td>S10</td><td><b>Player opportunity (props)</b> </td><td>Usage/snap/target distributions for prop combos</td><td>Player game logs</td><td><span class="pill bad">blocked · no player data</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="flagged.html">F-01 ↗</a></td></tr>
</tbody></table></div></section>

<section class="section" id="gates"><div class="section-head"><div><span class="eyebrow">VALIDATION GATES</span><h2>Every strategy must pass all 8</h2><p class="muted">Gates are evaluated in order on untouched, chronologically held-out data. Status today: none run — there is nothing to run them on yet, and we do not pretend otherwise.</p></div><span class="tag amber">0 / 8 RUN</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Gate</th><th>Question it answers</th><th>Pass rule (proposed)</th><th>Status</th><th>Source</th></tr></thead><tbody>
<tr><td><b>G1 · Data integrity</b> </td><td>Was every input actually knowable at decision time?</td><td>Point-in-time snapshots with URLs+timestamps; leakage audit clean; missingness documented</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer">input source ↗</a></td></tr>
<tr><td><b>G2 · Sample sufficiency</b> </td><td>Is there enough evidence to even test?</td><td>≥100 settled bets per market type (proposed) before any skill read</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="decisions.html">Q15 ↗</a></td></tr>
<tr><td><b>G3 · Out-of-sample</b> </td><td>Does it survive time, not just fit?</td><td>Walk-forward by week/season; latest seasons untouched; no random splits</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-9" target="_blank" rel="noreferrer">nfl.com results ↗</a> · <a href="data.html#results">input rows ↗</a></td></tr>
<tr><td><b>G4 · Probability quality</b> </td><td>Are the numbers well calibrated?</td><td>Brier/log-loss better than pre-registered baseline with CI; calibration plot attached</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="flagged.html">F-10 ↗</a></td></tr>
<tr><td><b>G5 · Economic performance</b> </td><td>Does it survive prices and costs?</td><td>Positive net yield after vig/fees with 95% CI, plus positive CLV trend</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noreferrer">NFL schedule (no published odds) ↗</a> · <a href="flagged.html">F-03, F-11, R-14 ↗</a></td></tr>
<tr><td><b>G6 · Multiplicity control</b> </td><td>Was this luck from trying many things?</td><td>Benjamini–Hochberg FDR ≤ 0.10 across all trials logged; every failed trial recorded</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="decisions.html">Q16 ↗</a></td></tr>
<tr><td><b>G7 · Parlay/prop integrity</b> </td><td>Are joint prices honest?</td><td>Joint-probability calibration vs offered payout out-of-sample; correlation stress tests; must beat constituent singles on EV</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="signals.html#correlations">correlations ↗</a></td></tr>
<tr><td><b>G8 · Shadow period</b> </td><td>Does it hold up prospectively?</td><td>Pre-registered, timestamped predictions for a full segment (proposed: one season part) with no gate regressions</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/scores/" target="_blank" rel="noreferrer">nfl.com scores ↗</a> · <a href="leaderboard.html">leaderboard ↗</a></td></tr>
</tbody></table></div>
<div class="note"><b>Why this removes luck:</b> luck loves untested multiplicity (try 100 strategies, keep the winner), unguarded samples (fit and evaluate on the same rows) and short streaks (10 lucky bets). G2+G3+G6 attack exactly those. What remains after all 8 gates is <i>selectively skill-based</i> — not guaranteed, just no longer explainable by the usual lucky processes.</div>
</section>

<section class="section" id="correlations"><div class="section-head"><div><span class="eyebrow">CORRELATION VALUES</span><h2>Computed from official data</h2><p class="muted">Pearson r with Fisher-z 95% CIs, computed by <code>tools/compute_stats.py</code> from the linked inputs. Reproduce: <code>python3 tools/compute_stats.py</code>.</p></div><span class="tag green">4 VALUES + HOME EDGE</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Quantity</th><th>Value</th><th>95% CI</th><th>n</th><th>Interpretation for parlays / lines</th><th>Source</th></tr></thead><tbody>
{home_row}
{crow_away_home}
{crow_margin_total}
{crow_net_wpct}
{crow_pf_papg}
</tbody></table></div>
<div class="callout"><b>Parlay implication (the one that matters today)</b> <p>Margin and total have a negative association in this 54-game sample (r = −0.32; the Fisher-z interval excludes zero). This is a descriptive relationship between final scores, not the joint probability of a spread leg and a total leg; it does not establish how often a favorite-cover + over parlay hits or whether a payout is mispriced. Opponent-score correlation is near zero in this small sample (r ≈ 0.02), which also does not establish independence of team-total bets. Gate G7 requires joint outcome probabilities and market terms from an authorized source before evaluating parlays.</p></div>
<div class="note"><b>Still blank (flagged, never inferred):</b> player-level prop correlations (QB pass yds ↔ WR rec yds, etc.) need paired player game logs — <a href="flagged.html">F-01</a>. Correlations are window-specific: re-estimate on each training fold, shrink noisy pairs, and report CIs — never ship a static coefficient as a pricing model.</div>
</section>

<section class="section" id="skill"><div class="section-head"><div><span class="eyebrow">SKILL, NOT LUCK</span><h2>How a strategy earns the word "skill"</h2></div><span class="tag">PROTOCOL</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Step</th><th>Practice</th><th>Luck attack</th><th>Source</th></tr></thead><tbody>
<tr><td>1 · Pre-registration</td><td>Strategy, thresholds and markets logged before evaluation</td><td>Kills post-hoc story-telling</td><td><a href="https://www.nfl.com/" target="_blank" rel="noreferrer">nfl.com ↗</a> · <a href="leaderboard.html">leaderboard rules ↗</a></td></tr>
<tr><td>2 · Walk-forward</td><td>Train on past, test on future, roll forward</td><td>Kills overfitting to history</td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-9" target="_blank" rel="noreferrer">official results ↗</a> · <a href="signals.html#gates">G3 ↗</a></td></tr>
<tr><td>3 · Full-trial ledger</td><td>Every attempt (pass or fail) counted in FDR</td><td>Kills "tried until something worked"</td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="signals.html#gates">G6 ↗</a></td></tr>
<tr><td>4 · CLV as skill proxy</td><td>Beat the close before results even arrive</td><td>Decouples skill read from scoreboard luck</td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noreferrer">NFL schedule (odds unavailable) ↗</a> · <a href="flagged.html">F-03, R-14 ↗</a></td></tr>
<tr><td>5 · Uncertainty everywhere</td><td>CIs on ROI, calibration and correlations; bankroll curves</td><td>Streaks stop looking like signals</td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="signals.html#gates">G4, G5 ↗</a></td></tr>
<tr><td>6 · Shadow first</td><td>Paper-only prospective period before any reward</td><td>Luck has nowhere to hide in live timestamps</td><td><a href="https://www.nfl.com/scores/" target="_blank" rel="noreferrer">nfl.com scores ↗</a> · <a href="signals.html#gates">G8 ↗</a></td></tr>
</tbody></table></div></section>

<footer><span>FOURTH DOWN RESEARCH · Line lab</span><span><a href="data.html">← Verified data</a> · <a href="leaderboard.html">Leaderboard →</a></span></footer>
</main>
<script src="nav.js"></script>
</body>
</html>
"""

html = (TEMPLATE
        .replace("{line_rows}", "\n".join(line_rows))
        .replace("{home_row}", home_row)
        .replace("{crow_away_home}", crow("away_vs_home_scores", "Away score ↔ home score", "No usable dependence between opponent scores in Wks 6–9 — 'both teams over' legs can't bank on correlation", "https://www.nfl.com/schedules/2026/by-week/week-9"))
        .replace("{crow_margin_total}", crow("margin_vs_total", "Margin ↔ game total", "Significant negative dependence — favorite+over parlays carry opposing legs (see callout)", "https://www.nfl.com/schedules/2026/by-week/week-8"))
        .replace("{crow_net_wpct}", crow("net_pts_vs_win_pct", "Net points ↔ win% (32 teams)", "Strongest team-level signal — validates S = PF/g − PA/g as a line-origination input", "https://www.nfl.com/standings/"))
        .replace("{crow_pf_papg}", crow("pts_per_game_vs_pts_allowed_per_game", "Scoring rate ↔ points allowed rate", "Weak/insignificant — pace/quality interplay not usable alone at n=32", "https://www.nfl.com/standings/")))
html = re.sub(r'</b>(?=[<a-z0-9`])', '</b> ', html)  # match the desk page polish rule
out = ROOT / "signals.html"
out.write_text(html)
(ROOT / "site" / "signals.html").write_text(html)
print("signals.html written (+ site/ mirror):", len(line_rows), "line rows")
