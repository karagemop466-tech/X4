#!/usr/bin/env python3
"""Generate strategies.html — line lab and correlation tables derived from research/computed_stats.json."""
import json, re
from pathlib import Path
import csv as _csv, os as _os
def _signal_staking_rows():
    path = _os.path.join(str(Path(__file__).resolve().parents[1]), "research", "data", "leaderboard_signal_staking.csv")
    if not _os.path.exists(path):
        return "<tr><td colspan=\"10\">signal/staking table not built</td></tr>"
    out = []
    for r in _csv.DictReader(open(path, newline="", encoding="utf-8")):
        stage = (r.get("stage") or "").strip()
        pill = "ok" if stage == "live" else "mut"
        out.append(
            "<tr><td><b>%s</b></td><td class=\"num\">%s</td><td class=\"num\">%s</td>"
            "<td class=\"num\">%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td>"
            "<td>%s</td><td class=\"num\">%s</td>"
            "<td><span class=\"pill %s\">%s</span></td>"
            "<td><a href=\"research/data/leaderboard_signal_staking.csv\">signal/staking CSV</a>"
            " &middot; <a href=\"https://www.nfl.com/scores/2026/REG10\">nfl.com score &#8599;</a></td></tr>"
            % (r.get("model",""), r.get("settled_bets",""), r.get("wins",""), r.get("hit_rate",""),
               r.get("brier",""), r.get("avg_disagreement_points",""),
               r.get("clv_status",""), r.get("net_units",""),
               pill, (stage or "paper").upper()))
    return "\n".join(out)



ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "research" / "computed_stats.json").read_text())
ESPN = "https://www.espn.com/nfl/schedule/_/week/11/year/2026/seasontype/2"

def fmt_delta(d):
    cls = "pill warn" if abs(d) >= 5 else ("pill info" if abs(d) >= 2.5 else "pill ok")
    label = "investigate" if abs(d) >= 5 else ("watch" if abs(d) >= 2.5 else "close")
    return f'<span class="{cls}">{d:+.1f}</span> <span class="muted">{label}</span>'

line_rows = []
for g in S["week11_baseline_lines"]:
    a, h = g["away"], g["home"]
    neu = ' <span class="pill mut">neutral</span>' if g["neutral"] else ""
    fav = g["market_favorite"]
    mkt = f"{fav} −{g['market_spread']:g}"
    my_home = g["my_home_margin"]
    # express my line as favorite-spread convention for readability
    if my_home >= 0:
        my_str = f"{h} −{my_home:.1f}"
    else:
        my_str = f"{a} −{abs(my_home):.1f}"
    line_rows.append(
        f'<tr><td><b>{a}</b> at <b>{h}</b>{neu}</td><td class="num">{my_str}</td>'
        f'<td class="num">{g["my_total"]:.1f}</td><td class="num">{mkt}</td>'
        f'<td class="num">{g["mkt_total"]:g}</td><td class="num">{fmt_delta(g["delta_margin"])}</td>'
        f'<td class="num">{fmt_delta(g["delta_total"])}</td>'
        f'<td><a href="{ESPN}" target="_blank" rel="noreferrer">ESPN odds ↗</a></td></tr>'
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
<aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">4D</span><span>FOURTH DOWN<small>RESEARCH DESK</small></span></a><div class="side-label">WORKSPACE</div><nav><a href="index.html">◫ &nbsp;Overview</a><a href="executive-summary.html">★ &nbsp;Executive summary</a><a href="requirements.html">☰ &nbsp;Requirements</a><a href="data.html">▦ &nbsp;Verified data</a><a href="signals.html">◎ &nbsp;Line lab &amp; signals</a><a href="origination.html">⊞ &nbsp;Line origination</a><a href="price-store.html">◈ &nbsp;Price store</a><a href="signal-vs-staking.html">⚖ &nbsp;Signal vs staking</a><a href="correlations.html">∿ &nbsp;Correlations</a><a href="replacements.html">＋ &nbsp;Availability &amp; depth</a><a href="method-lab.html">⌁ &nbsp;Method lab</a><a href="injuries.html">＋ &nbsp;Injury rows</a><a href="leaderboard.html">↗ &nbsp;Leaderboard</a><a href="decisions.html">? &nbsp;Decision Q&amp;A</a><a href="review.html">✳ &nbsp;Suggestions</a><a href="workbench.html">✳ &nbsp;Suggestion workbench</a><a href="programme.html">◫ &nbsp;Integrity &amp; programme</a><a href="verification.html">✓ &nbsp;Verification</a><a href="requirements-closure.html">☑ &nbsp;Requirement closure</a><a href="ops-review.html">✧ &nbsp;Review gate</a><a href="flagged.html">⚑ &nbsp;Flagged for review</a><a href="repo-review.html">§ &nbsp;Repo review</a><a href="sources.html">↗ &nbsp;Sources</a></nav><div class="side-bottom"><span class="pulse"></span> Research mode <small>Snapshot 2026-11-14 · no live feed</small></div></aside>

<main>
<header class="topbar"><div><span class="eyebrow">04 · SIGNALS</span><h1>Line lab &amp; strategies</h1></div><span class="status-pill"><i></i> Baseline v0 · gates not run</span></header>

<section class="section" id="line-lab"><div class="section-head"><div><span class="eyebrow">ORIGINATING LINES</span><h2>Week 11 — my baseline vs market</h2><p class="muted">Model: <code>spread = (S_home − S_away) + h</code> where <code>S = PF/g − PA/g</code> from official standings (through Week-10 TNF) and <code>h = +0.07</code> (measured home edge, weeks 6–9). Totals: mean of each team's points-per-game-in-their-games. Market = DraftKings odds as published by ESPN, snapshot 2026-11-14.</p></div><span class="tag">13 GAMES</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Matchup</th><th>My spread</th><th>My total</th><th>Market spread</th><th>Market O/U</th><th>Spread Δ</th><th>Total Δ</th><th>Source</th></tr></thead><tbody>
{line_rows}
</tbody></table></div>
<div class="note"><b>Reading the deltas:</b> 6 of 13 spreads land within ±2.5 of market — a sanity pass for a one-line model. The three ≥5-point disagreements (NYJ/LAC, PIT/PHI, CIN/WAS) are <b>investigation candidates, not edges</b>: the market prices injuries, QB context and rest that v0 ignores. No bet, no edge, no accuracy claim is made here. Full inputs: <a href="research/data/standings_2026_through_week10_tnf.csv">standings CSV</a> · <a href="research/data/week11_odds_2026.csv">odds CSV</a> · reproduce with <code>python3 tools/compute_stats.py</code>.</div>
<div class="callout"><b>What v0 deliberately excludes</b> <p>Player availability, quarterback changes, rest/travel, weather, motivation/standings context, and market timing. Each is a candidate signal below; each must clear the gates before it enters a production line.</p></div>
</section>

<section class="section" id="signals"><div class="section-head"><div><span class="eyebrow">CANDIDATE SIGNALS</span><h2>Signal inventory</h2><p class="muted">A signal is a hypothesis until it clears every gate. "Computed" means a value exists today from official data; "blocked" means a required input is missing and flagged.</p></div><span class="tag">10 SIGNALS</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>#</th><th>Signal</th><th>What it measures</th><th>Official input source</th><th>State</th><th>Source</th></tr></thead><tbody>
<tr><td>S1</td><td><b>Point-differential strength</b> </td><td>S = PF/g − PA/g; season-to-date team quality</td><td>Standings PF/PA</td><td><span class="pill ok">computed · in v0</span></td><td><a href="https://www.nfl.com/standings/" target="_blank" rel="noreferrer">nfl.com standings ↗</a></td></tr>
<tr><td>S2</td><td><b>Home-field edge</b> </td><td>Mean home margin, neutral games excluded</td><td>Game results Wks 6–9</td><td><span class="pill warn">computed · CI spans 0</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-9" target="_blank" rel="noreferrer">nfl.com Wk9 results ↗</a></td></tr>
<tr><td>S3</td><td><b>Scoring environment</b> </td><td>League mean/SD of game totals for totals lines</td><td>Game results Wks 6–9</td><td><span class="pill ok">computed · in v0</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-8" target="_blank" rel="noreferrer">nfl.com Wk8 results ↗</a></td></tr>
<tr><td>S4</td><td><b>Market divergence</b> </td><td>|my line − market| as an investigation queue</td><td>ESPN/DraftKings snapshot</td><td><span class="pill ok">computed · informational</span></td><td><a href="https://www.espn.com/nfl/schedule/_/week/11/year/2026/seasontype/2" target="_blank" rel="noreferrer">ESPN odds ↗</a></td></tr>
<tr><td>S5</td><td><b>Availability adjustments</b> </td><td>Practice/game statuses feeding lineup-sensitive features</td><td>NFL official injury report</td><td><span class="pill warn">sampled · no feed</span></td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer">nfl.com injuries ↗</a></td></tr>
<tr><td>S6</td><td><b>Depth-string deficiency</b> </td><td>Starter ruled out → 2nd/3rd/4th-string replacement impact, O and D units</td><td>Depth chart + injury report</td><td><span class="pill bad">blocked · depth chart 404</span></td><td><a href="https://www.nfl.com/teams/depth-charts/" target="_blank" rel="noreferrer">depth-chart URL (404) ↗</a> · <a href="flagged.html">R-03 ↗</a></td></tr>
<tr><td>S7</td><td><b>Rest / schedule spots</b> </td><td>Bye, short week, international travel, Thursday turnaround</td><td>Official schedule</td><td><span class="pill info">specified · not tested</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noreferrer">nfl.com schedule ↗</a></td></tr>
<tr><td>S8</td><td><b>Weather</b> </td><td>Wind/precipitation vs totals and passing efficiency</td><td>Venue weather (to be selected)</td><td><span class="pill bad">blocked · source undecided</span></td><td><a href="https://www.nfl.com/scores/" target="_blank" rel="noreferrer">nfl.com scores (weather shown) ↗</a> · <a href="flagged.html">F-07 ↗</a></td></tr>
<tr><td>S9</td><td><b>Closing-line value (CLV)</b> </td><td>My price vs closing price — the premier skill proxy</td><td>Timestamped odds feed</td><td><span class="pill bad">blocked · no feed history</span></td><td><a href="https://www.espn.com/nfl/schedule/_/week/11/year/2026/seasontype/2" target="_blank" rel="noreferrer">odds snapshot ↗</a> · <a href="flagged.html">F-03 ↗</a></td></tr>
<tr><td>S10</td><td><b>Player opportunity (props)</b> </td><td>Usage/snap/target distributions for prop combos</td><td>Player game logs</td><td><span class="pill bad">blocked · no player data</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="flagged.html">F-01 ↗</a></td></tr>
</tbody></table></div></section>

<section class="section" id="gates"><div class="section-head"><div><span class="eyebrow">VALIDATION GATES</span><h2>Every strategy must pass all 8</h2><p class="muted">Gates are evaluated in order on untouched, chronologically held-out data. Status today: none run — there is nothing to run them on yet, and we do not pretend otherwise.</p></div><span class="tag amber">0 / 8 RUN</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Gate</th><th>Question it answers</th><th>Pass rule (proposed)</th><th>Status</th><th>Source</th></tr></thead><tbody>
<tr><td><b>G1 · Data integrity</b> </td><td>Was every input actually knowable at decision time?</td><td>Point-in-time snapshots with URLs+timestamps; leakage audit clean; missingness documented</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/injuries/" target="_blank" rel="noreferrer">input source ↗</a></td></tr>
<tr><td><b>G2 · Sample sufficiency</b> </td><td>Is there enough evidence to even test?</td><td>≥100 settled bets per market type (proposed) before any skill read</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="decisions.html">Q15 ↗</a></td></tr>
<tr><td><b>G3 · Out-of-sample</b> </td><td>Does it survive time, not just fit?</td><td>Walk-forward by week/season; latest seasons untouched; no random splits</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-9" target="_blank" rel="noreferrer">nfl.com results ↗</a> · <a href="data.html#results">input rows ↗</a></td></tr>
<tr><td><b>G4 · Probability quality</b> </td><td>Are the numbers well calibrated?</td><td>Brier/log-loss better than pre-registered baseline with CI; calibration plot attached</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="flagged.html">F-10 ↗</a></td></tr>
<tr><td><b>G5 · Economic performance</b> </td><td>Does it survive prices and costs?</td><td>Positive net yield after vig/fees with 95% CI, plus positive CLV trend</td><td><span class="pill info">defined</span></td><td><a href="https://www.espn.com/nfl/schedule/_/week/11/year/2026/seasontype/2" target="_blank" rel="noreferrer">market snapshot ↗</a> · <a href="flagged.html">F-03, F-11 ↗</a></td></tr>
<tr><td><b>G6 · Multiplicity control</b> </td><td>Was this luck from trying many things?</td><td>Benjamini–Hochberg FDR ≤ 0.10 across all trials logged; every failed trial recorded</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="decisions.html">Q16 ↗</a></td></tr>
<tr><td><b>G7 · Parlay/prop integrity</b> </td><td>Are joint prices honest?</td><td>Joint-probability calibration vs offered payout out-of-sample; correlation stress tests; must beat constituent singles on EV</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="signals.html#correlations">correlations ↗</a></td></tr>
<tr><td><b>G8 · Shadow period</b> </td><td>Does it hold up prospectively?</td><td>Pre-registered, timestamped predictions for a full segment (proposed: one season part) with no gate regressions</td><td><span class="pill info">defined</span></td><td><a href="https://www.nfl.com/scores/" target="_blank" rel="noreferrer">nfl.com scores ↗</a> · <a href="leaderboard.html">leaderboard ↗</a></td></tr>
</tbody></table></div>
<div class="note"><b>Why this removes luck:</b> luck loves untested multiplicity (try 100 strategies, keep the winner), unguarded samples (fit and evaluate on the same rows) and short streaks (10 lucky bets). G2+G3+G6 attack exactly those. What remains after all 8 gates is <i>selectively skill-based</i> — not guaranteed, just no longer explainable by the usual lucky processes.</div>

<section class="section" id="signal-staking"><div class="section-head"><div><span class="eyebrow">SIGNAL vs STAKING</span><h2>Two questions, never one number</h2><p class="muted">A strategy can be right about the game and still be a bad bet, and it can be a good bet while being right for the wrong reason. So the leaderboard publishes two separate things: <b>signal</b> (is the prediction better than the baseline?) and <b>staking</b> (what a bankroll would have done). They are never collapsed into one score.</p></div></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Strategy</th><th class="num">Settled</th><th class="num">Wins</th><th class="num">Hit rate</th><th class="num">Brier</th><th class="num">Avg disagreement (pts)</th><th>CLV status</th><th class="num">Net units</th><th>Stage</th><th>Source</th></tr></thead><tbody>
{signal_rows}
</tbody></table></div>
<section style="margin-top:18px">
  <div class="note warn"><b>Why the staking column cannot be filled yet.</b> Staking needs a price at the moment the bet is taken. This project has never taken a price at stake time &mdash; the store holds open, current and close, not stake &mdash; so every CLV cell is published <i>blank and labelled blocked</i> rather than filled with the model-to-close disagreement, which is a different quantity (Flag F-20). The net-units column is therefore a paper-trading record, not a return.</div>
  <div class="note"><b>What the numbers here are.</b> Nine graded rows from the settled Week&nbsp;10 game, one bet per model. The hit rates are 0.00 or 1.00 because n&nbsp;=&nbsp;1 per model: they are a wiring check, not a skill estimate. Nothing on this page scores a strategy as profitable. The simulation that shows why the two columns must stay separate &mdash; a 2.4-point true edge turning into <b>+78.18 flat</b> and <b>&minus;83.21 at 5% of bankroll</b> from the same 100-unit start &mdash; is on <a href="programme.html#signal">Integrity &amp; programme</a>.</div>
</section>
</section>

</section>

<section class="section" id="correlations"><div class="section-head"><div><span class="eyebrow">CORRELATION VALUES</span><h2>Computed from official data</h2><p class="muted">Pearson r with Fisher-z 95% CIs, computed by <code>tools/compute_stats.py</code> from the linked inputs. Reproduce: <code>python3 tools/compute_stats.py</code>.</p></div><span class="tag green">4 VALUES + HOME EDGE</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Quantity</th><th>Value</th><th>95% CI</th><th>n</th><th>Interpretation for parlays / lines</th><th>Source</th></tr></thead><tbody>
{home_row}
{crow_away_home}
{crow_margin_total}
{crow_net_wpct}
{crow_pf_papg}
</tbody></table></div>
<div class="callout"><b>Parlay implication (the one that matters today)</b> <p>Margin ↔ total is <b>negative</b> (r = −0.32, CI excludes 0): in high-scoring games the margin tends to shrink. A "favorite covers + over" parlay therefore has legs that move <i>against</i> each other — the true joint hit rate is below the naive product of the singles, so an independence-priced payout is worse than it looks. This is why gate G7 exists. Opponent scores show no usable correlation in this window (r ≈ 0.02), so "both teams over" legs cannot assume dependence either way yet.</p></div>
<div class="note"><b>Still blank (flagged, never inferred):</b> player-level prop correlations (QB pass yds ↔ WR rec yds, etc.) need paired player game logs — <a href="flagged.html">F-01</a>. Correlations are window-specific: re-estimate on each training fold, shrink noisy pairs, and report CIs — never ship a static coefficient as a pricing model.</div>
</section>

<section class="section" id="skill"><div class="section-head"><div><span class="eyebrow">SKILL, NOT LUCK</span><h2>How a strategy earns the word "skill"</h2></div><span class="tag">PROTOCOL</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Step</th><th>Practice</th><th>Luck attack</th><th>Source</th></tr></thead><tbody>
<tr><td>1 · Pre-registration</td><td>Strategy, thresholds and markets logged before evaluation</td><td>Kills post-hoc story-telling</td><td><a href="https://www.nfl.com/" target="_blank" rel="noreferrer">nfl.com ↗</a> · <a href="leaderboard.html">leaderboard rules ↗</a></td></tr>
<tr><td>2 · Walk-forward</td><td>Train on past, test on future, roll forward</td><td>Kills overfitting to history</td><td><a href="https://www.nfl.com/schedules/2026/by-week/week-9" target="_blank" rel="noreferrer">official results ↗</a> · <a href="signals.html#gates">G3 ↗</a></td></tr>
<tr><td>3 · Full-trial ledger</td><td>Every attempt (pass or fail) counted in FDR</td><td>Kills "tried until something worked"</td><td><a href="https://www.nfl.com/stats/" target="_blank" rel="noreferrer">nfl.com stats ↗</a> · <a href="signals.html#gates">G6 ↗</a></td></tr>
<tr><td>4 · CLV as skill proxy</td><td>Beat the close before results even arrive</td><td>Decouples skill read from scoreboard luck</td><td><a href="https://www.espn.com/nfl/schedule/_/week/11/year/2026/seasontype/2" target="_blank" rel="noreferrer">odds snapshot ↗</a> · <a href="flagged.html">F-03 ↗</a></td></tr>
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
        .replace("{signal_rows}", _signal_staking_rows())
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
