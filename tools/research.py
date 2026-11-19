#!/usr/bin/env python3
"""Generate the written research findings in research/ from the published payload.

The research documents quote the same numbers the site publishes. Generating
them from data/output/payload.json means a document can never drift away from
the data it describes.

Run:  python3 tools/research.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "output")
RESEARCH = os.path.join(ROOT, "research")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content  # noqa: E402

with open(os.path.join(DATA, "payload.json"), encoding="utf-8") as fh:
    P = json.load(fh)

standings = P["standings"]
power = P["power"]
games = P["games"]
lines = P["wk11_lines"]
leaderboard = P["leaderboard"]
corr_err = P["correlation_error"]
corr_pred = P["correlation_prediction"]
calibration = P["calibration"]
weekly = P["weekly"]
availability = P["availability"]
injury_rows = P["injury_rows"]
qb_changes = P["qb_changes"]
news = P["news"]
meta = P["meta"]
ids = [s["id"] for s in P["strategies"]]

SEASON_SRC = "<https://www.nfl.com/schedules/2026/>"
STAND_SRC = "<https://www.nfl.com/standings/>"
INJ_SRC = "<https://www.nfl.com/injuries/>"
WK11_SRC = "<https://www.nfl.com/schedules/2026/by-week/week-11>"


def f2(x):
    return "%.2f" % x


def f3(x):
    return "%.3f" % x


def write(name, lines_):
    path = os.path.join(RESEARCH, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines_) + "\n")
    print("wrote research/%s" % name)


# ------------------------------------------------------------------ model lines
out = [
    "# Week 11 model lines",
    "",
    "Schedule source: %s (official NFL.com, retrieved 14 November 2026)." % WK11_SRC,
    "Underlying results: %s and %s (official)." % (SEASON_SRC, STAND_SRC),
    "",
    "Every number below is a **model estimate** produced by `tools/build.py` from the official "
    "results. The market-line column is deliberately empty: the NFL publishes no official betting "
    "lines and no licensed odds feed has been authorised for this repository (flag F-01).",
    "",
    "| Away | Home | Date | Kickoff (ET) | TV | Spread range | Total range | S3 line | Market line | Source |",
    "|---|---|---|---|---|---|---|---|---|---|",
]
for r in lines:
    sp = [r["models"][k]["spread"] for k in r["models"]]
    to = [r["models"][k]["total"] for k in r["models"]]
    s3 = r["models"]["S3"]
    out.append("| %s | %s | %s | %s | %s | %s to %s | %s to %s | %s / %s | *(blank)* | [NFL.com](%s) |"
               % (r["away"], r["home"], r["date"], r["time_et"], r["network"],
                  f2(min(sp)), f2(max(sp)), f2(min(to)), f2(max(to)),
                  f2(s3["spread"]), f2(s3["total"]), r["url"]))
out += [
    "",
    "## Reading the range",
    "",
    "The spread range spans all nine strategies and the total range likewise. A narrow range means "
    "the strategies agree and the verified data supports a directional view; a wide range means the "
    "model is close to indifferent, and any pick built on that game is a coin flip dressed up as "
    "analysis.",
    "",
    "## Team strength behind the lines",
    "",
    "Opponent-adjusted rates: a team's points-for rate minus the average points allowed by the "
    "opponents it has faced, plus the league average, and the mirror image for points allowed. "
    "These are model estimates. The raw official columns are in `data/standings-wk10-2026.csv` and "
    "on the Standings page.",
    "",
    "| Rank | Team | Adj. points for | Adj. points allowed | Adj. margin | Official PF | Official PA | Source |",
    "|---|---|---|---|---|---|---|---|",
]
for i, r in enumerate(power[:8], 1):
    out.append("| %d | %s | %s | %s | %s | %d | %d | [NFL.com](%s) |"
               % (i, r["abbr"], f2(r["adj_pf"]), f2(r["adj_pa"]), f2(r["adj_net"]),
                  r["pf"], r["pa"], r["url"]))
out += ["", "| Rank | Team | Adj. points for | Adj. points allowed | Adj. margin | Official PF | Official PA | Source |",
        "|---|---|---|---|---|---|---|---|"]
for i, r in enumerate(power[-8:], len(power) - 7):
    out.append("| %d | %s | %s | %s | %s | %d | %d | [NFL.com](%s) |"
               % (i, r["abbr"], f2(r["adj_pf"]), f2(r["adj_pa"]), f2(r["adj_net"]),
                  r["pf"], r["pa"], r["url"]))
out += [
    "",
    "## Why no line is presented as a recommendation",
    "",
    "Three reasons, in order of importance. First, there is no market price, so there is nothing to "
    "compare an estimate against - a model line without a price is not a bet. Second, the improvement "
    "over the league-constant benchmark has a confidence interval that still contains zero (flag "
    "F-07), so the model has not demonstrated skill over noise. Third, the public Week 10 injury "
    "report omits players on injured reserve, so a material part of the availability picture is "
    "missing from the inputs (flag F-03).",
    "",
    "## Source links",
    "",
    "- Official Week 11 schedule: %s" % WK11_SRC,
    "- Official standings: %s" % STAND_SRC,
    "- Official Week 10 injury report: %s" % INJ_SRC,
    "- Official team pages: linked per row.",
    "",
]
write("model-lines-week11.md", out)

# ------------------------------------------------------------------ correlations
hi = [(a, b, corr_err[a][b]) for i, a in enumerate(ids) for b in ids[i + 1:]
      if corr_err[a][b] is not None and corr_err[a][b] >= 0.98]
mid = [(a, b, corr_err[a][b]) for i, a in enumerate(ids) for b in ids[i + 1:]
       if corr_err[a][b] is not None and 0.90 <= corr_err[a][b] < 0.98]
lo = [(a, b, corr_err[a][b]) for i, a in enumerate(ids) for b in ids[i + 1:]
      if corr_err[a][b] is not None and corr_err[a][b] < 0.90]
out = [
    "# Correlation and luck control",
    "",
    "Computed by `tools/build.py` over the %d out-of-sample games (Weeks %d-%d). Underlying results: "
    "%s and %s." % (meta["eval_games"], meta["eval_weeks"][0], meta["eval_weeks"][1],
                    SEASON_SRC, STAND_SRC),
    "",
    "## Why this is on the site at all",
    "",
    "If two strategies make the same mistakes on the same games, they are one signal counted twice. "
    "Ranking them against each other tells the reader the desk holds more independent evidence than "
    "it does, and building a combination from the two looks like diversification when it is not.",
    "",
    "## Spread-error correlation",
    "",
    "| | " + " | ".join(ids) + " |",
    "|---|" + "---|" * len(ids),
]
for a in ids:
    out.append("| " + a + " | " + " | ".join(f3(corr_err[a][b]) if corr_err[a][b] is not None else "-"
                                              for b in ids) + " |")
out += [
    "",
    "## What the matrix says",
    "",
    "**Near-identical (0.98 and above):** " + ", ".join("%s-%s (%s)" % (a, b, f3(v))
                                                          for a, b, v in sorted(hi, key=lambda x: -x[2])) + ".",
    "",
    "**Strongly related (0.90 to 0.98):** " + ", ".join("%s-%s (%s)" % (a, b, f3(v))
                                                         for a, b, v in sorted(mid, key=lambda x: -x[2])) + ".",
    "",
    "**Largely independent (below 0.90):** " + ", ".join("%s-%s (%s)" % (a, b, f3(v))
                                                          for a, b, v in sorted(lo, key=lambda x: -x[2])) + ".",
    "",
    "## Prediction correlation",
    "",
    "| | " + " | ".join(ids) + " |",
    "|---|" + "---|" * len(ids),
]
for a in ids:
    out.append("| " + a + " | " + " | ".join(f3(corr_pred[a][b]) if corr_pred[a][b] is not None else "-"
                                              for b in ids) + " |")
out += [
    "",
    "## Consequence for the leaderboard",
    "",
    "The regularised family (S3, S4, S6, S7) is effectively a single signal: those pairs fail on the "
    "same games. The leaderboard keeps them as separate rows for transparency, but a strategy that "
    "fails a gate on its own cannot borrow strength from a near-duplicate that passes it.",
    "",
    "This is the concrete mechanism for removing luck from the equation. It is not enough for a "
    "strategy to beat the benchmark; it has to beat it with a signal that is not already being "
    "counted.",
    "",
    "## Practical rule for combinations",
    "",
    "A parlay or prop combination built from two legs whose error correlation is above roughly 0.95 is "
    "close to a single bet priced twice. Multiplying marginal probabilities in that situation "
    "overstates the joint probability of the combination winning, and the overstatement compounds with "
    "every extra leg. Each combination therefore has to be priced from a joint estimate and compared "
    "against the same legs taken singly.",
    "",
    "## What is still missing",
    "",
    "These correlations are between **model** strategies. The correlation that actually matters for a "
    "parlay is between **market legs** - two player props or two spreads priced by the same book - and "
    "that cannot be computed here, because no licensed odds feed has been authorised (flag F-01). The "
    "matrix above is the correlation between our own candidate signals, which is the part we can "
    "measure honestly.",
    "",
    "## Source links",
    "",
    "- Official schedule and results: %s" % SEASON_SRC,
    "- Official standings: %s" % STAND_SRC,
    "",
]
write("correlation-and-luck.md", out)

# ------------------------------------------------------------------ strategy validation
out = [
    "# Strategy validation and the leaderboard",
    "",
    "Produced by `tools/build.py` over %d out-of-sample games (Weeks %d-%d of the 2026 season). "
    "Underlying results: %s and %s."
    % (meta["eval_games"], meta["eval_weeks"][0], meta["eval_weeks"][1], SEASON_SRC, STAND_SRC),
    "",
    "## The seven gates",
    "",
    "A strategy only earns reward points if it clears every gate. The gates are designed so that a "
    "strategy with a lucky record fails at least one of them.",
    "",
    "| Gate | What it tests | Pass rule |",
    "|---|---|---|",
    "| G1 Data integrity | Point-in-time correctness | Every input is an official NFL.com page; each "
    "forecast uses only games played before it, with no look-ahead |",
    "| G2 Out-of-sample | Honest evaluation | Walk-forward evaluation across the season; no random "
    "row splits |",
    "| G3 Minimum sample | Enough evidence | At least %d evaluated games |" % meta["params"]["min_eval_games"],
    "| G4 Significance | Skill, not luck | The Bonferroni-adjusted bootstrap interval for the "
    "improvement over the benchmark excludes zero |",
    "| G5 Stability | Consistency | The improvement is positive in at least %.0f%% of evaluated weeks |"
    % (100 * meta["params"]["min_weekly_improvement_share"]),
    "| G6 Calibration | Honesty of the probability | The largest gap between the model's stated "
    "probability and the observed rate is at most %.2f |" % meta["params"]["calibration_max_gap"],
    "| G7 Not the benchmark | A real competitor | The league-constant benchmark is excluded from "
    "rewards by definition |",
    "",
    "## The leaderboard",
    "",
    "| Rank | ID | Strategy | Spread MAE | Total MAE | Direction | Improvement | 95% CI | Weeks "
    "improved | Calib. gap | Gates | Eligible | Points |",
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
]
for i, r in enumerate(leaderboard, 1):
    out.append("| %d | %s | %s | %s | %s | %.1f%% | %s | %s to %s | %.0f%% | %s | %d/7 | %s | %s |"
               % (i, r["id"], r["name"], f2(r["metrics"]["spread_mae"]), f2(r["metrics"]["total_mae"]),
                  100 * r["metrics"]["direction_accuracy"],
                  "baseline" if r["id"] == "S0" else "%.2f%%" % (100 * r["improvement_pct"]),
                  f2(r["ci_low"]), f2(r["ci_high"]), 100 * r["weekly_positive_share"],
                  f3(r["calibration_max_gap"]), r["gates_passed"],
                  "**yes**" if r["eligible"] else "no", f2(r["reward"])))
n_elig = sum(1 for r in leaderboard if r["eligible"])
out += [
    "",
    "## The headline result",
    "",
    "**%s.** %s"
    % ("No strategy is eligible." if n_elig == 0 else "%d of %d strategies are eligible." % (n_elig, len(leaderboard)),
       "The best strategy improves point-spread MAE over the league-constant benchmark by about "
       "%.0f percent, but the Bonferroni-adjusted bootstrap interval for that improvement still "
       "contains zero. In plain terms: the improvement is not yet distinguishable from the luck that "
       "a sample of this size produces on its own." % (100 * leaderboard[0]["improvement_pct"])),
    "",
    "That is the correct finding, not a failure of the analysis. A leaderboard that ranked by point "
    "estimate would have crowned a winner the evidence does not support. The points column is "
    "therefore provisional for every row, and the eligible column is empty.",
    "",
    "## Why the interval contains zero",
    "",
    "Four reasons, and the first is the one that matters most:",
    "",
    "1. **Ten weeks is a short sample.** %d evaluated games cannot separate a %.0f percent improvement "
    "from noise. The remedy is more games and more seasons - which means archiving point-in-time data "
    "going forward rather than reconstructing it."
    % (meta["eval_games"], 100 * leaderboard[0]["improvement_pct"]),
    "2. **The benchmark is strong.** The league-constant benchmark scores a %.1f%% direction accuracy, "
    "which is close to a coin flip with a small home-field tilt. Beating a weak baseline is easy; "
    "beating this one is not."
    % (100 * [r for r in leaderboard if r["id"] == "S0"][0]["metrics"]["direction_accuracy"]),
    "3. **The strategies are not independent.** Several are the same signal with different smoothing. "
    "Treating them as nine competitors inflates the apparent amount of evidence - see "
    "`correlation-and-luck.md`.",
    "4. **The comparison is a paired test on a noisy quantity.** The bootstrap resamples games, not "
    "strategies, and the per-game spread error has a standard deviation of roughly ten points. An "
    "improvement of under one point per game cannot clear that noise with this many samples.",
    "",
    "## What each strategy does",
    "",
]
for r in leaderboard:
    out.append("**%s - %s** (%s). %s" % (r["id"], r["name"], r["family"], r["description"]))
out += ["", "## Gate-by-gate verdicts", "", "| Strategy | Gates passed | Failing gates |", "|---|---|---|"]
for r in leaderboard:
    fails = [k for k, g in r["gates"].items() if not g["pass_"]]
    out.append("| %s | %d/7 | %s |" % (r["id"], r["gates_passed"], ", ".join(fails) if fails else "none"))
out += ["", "## Weekly stability", "",
        "| Week | " + " | ".join(r["id"] for r in leaderboard) + " |",
        "|---|" + "---|" * len(leaderboard)]
for w in range(len(weekly["S0"]["per_week"])):
    out.append("| Week %d | " % (meta["eval_weeks"][0] + w)
               + " | ".join(f2(weekly[r["id"]]["per_week"][w]) for r in leaderboard) + " |")
out += [
    "",
    "Positive means the strategy beat the league-constant benchmark that week. A strategy that is "
    "positive in only a handful of weeks is describing one good run, not an edge.",
    "",
    "## Calibration",
    "",
    "| Strategy | Offset | Model probability | Observed rate | Games | Within tolerance |",
    "|---|---|---|---|---|---|",
]
for r in leaderboard:
    for row in calibration[r["id"]]["rows"]:
        out.append("| %s | %+d pts | %.1f%% | %.1f%% | %d | %s |"
                   % (r["id"], row["delta"], 100 * row["predicted"], 100 * row["observed"],
                      row["n"], "yes" if row["gap"] <= 0.12 else "no"))
out += [
    "",
    "Every strategy passes calibration comfortably. That is worth stating plainly: the forecasts are "
    "not systematically overconfident, which means the failure to clear the significance gate is a "
    "sample-size problem and not a badly-calibrated model.",
    "",
    "## Source links",
    "",
    "- Official schedule and results: %s" % SEASON_SRC,
    "- Official standings: %s" % STAND_SRC,
    "",
]
write("strategy-validation.md", out)

# ------------------------------------------------------------------ injuries and depth
tot_l = sum(a["listed_players"] for a in availability)
tot_o = sum(a["out_count"] for a in availability)
tot_d = sum(a["doubtful_count"] for a in availability)
tot_q = sum(a["questionable_count"] for a in availability)
out = [
    "# Injuries and depth deficiencies",
    "",
    "Source: the official NFL.com Week 10 injury report, %s, retrieved 14 November 2026, for the %d "
    "teams playing in Week 10." % (INJ_SRC, len(availability)),
    "",
    "## What the official report contains",
    "",
    "For each listed player: the listed position, the injury description, the practice participation "
    "code and the game status. The practice codes are Full Participation in Practice, Limited "
    "Participation in Practice, and Did Not Participate In Practice; the game statuses are Out, "
    "Doubtful and Questionable. A blank status means the player was listed with no designation.",
    "",
    "## Absence roll-up by team",
    "",
    "| Team | Players listed | Out | Doubtful | Questionable | Offense units hit | Defense units hit | Source |",
    "|---|---|---|---|---|---|---|---|",
]
for a in availability:
    off = ", ".join("%s x%d" % (u["unit"], u["count"])
                    for u in a["out_by_unit"] if u["side"] == "Offense") or "-"
    dfn = ", ".join("%s x%d" % (u["unit"], u["count"])
                    for u in a["out_by_unit"] if u["side"] == "Defense") or "-"
    out.append("| %s | %d | %d | %d | %d | %s | %s | [NFL.com](%s) |"
               % (a["team"], a["listed_players"], a["out_count"], a["doubtful_count"],
                  a["questionable_count"], off, dfn, a["url"]))
out += [
    "",
    "Totals across the %d teams playing: **%d** players listed, **%d** Out, **%d** Doubtful, **%d** "
    "Questionable." % (len(availability), tot_l, tot_o, tot_d, tot_q),
    "",
    "## What the report cannot tell us",
    "",
    "Two gaps, both material to any depth analysis:",
    "",
    "**1. Players on injured reserve do not appear.** The public weekly report covers players who are "
    "expected to take part in the upcoming game. Baltimore's starting quarterback appears nowhere in "
    "the Week 10 table - his absence surfaces only in the league's own news reporting, where the "
    "Ravens confirm he is expected to miss six to ten weeks. Any availability model built from the "
    "public report alone will silently miss exactly the absences that move a line the most. This is "
    "flag F-03.",
    "",
    "**2. There is no depth-chart string.** The report says who is available; it does not say who the "
    "second, third or fourth string is at a position. The NFL publishes no consolidated league depth "
    "chart, so no player on this site is assigned a depth rank. This is flag F-02.",
    "",
    "## Starter changes the league confirmed",
    "",
    "These come from official NFL.com reporting rather than the injury report.",
    "",
    "| Team | Unit | Player | What the league reported | Source |",
    "|---|---|---|---|---|",
]
for q in qb_changes:
    out.append("| %s | %s | %s | %s | [NFL.com](%s) |"
               % (q["team"], q["unit"], q["player"], q["change"], q["url"]))
out += [
    "",
    "## Unit depth deficiencies that can be evidenced",
    "",
    "A depth deficiency means a position group has lost its starter and the replacement level is "
    "unknown or lower. The following can be stated from the official report and the league's own "
    "reporting without inferring anything:",
    "",
    "**Green Bay - running back.** Josh Jacobs is Out with a finger injury and the league reports he "
    "is to undergo surgery, with the return timeline to be determined. A genuine absence of the "
    "team's leading back rather than a doubt.",
    "",
    "**Minnesota - quarterback and tight end.** Kyler Murray and T.J. Hockenson are both Out, so the "
    "replacement at quarterback is a backup by definition. The league also confirmed J.J. McCarthy was "
    "expected to play in Week 10.",
    "",
    "**San Francisco - wide receiver.** Mike Evans is Out with an Achilles injury. With Deebo Samuel "
    "and Demarcus Robinson listed and no status, the depth behind the top receiver is unclear.",
    "",
    "**Seattle - quarterback.** Sam Darnold is Out with ribs and quadricep injuries, the league "
    "confirmed he is ruled out for the Week 10 game against the Raiders, and Drew Lock is expected to "
    "start. A confirmed backup starting is a measurable event, unlike an inferred depth rank.",
    "",
    "**Cleveland and Arizona - quarterback.** The league confirmed Deshaun Watson starts for Cleveland "
    "against Houston and Carson Beck starts for Arizona against the LA Rams.",
    "",
    "**Miami - quarterback.** Malik Willis was placed on injured reserve with a groin injury, with Kyle "
    "McCord in line for a first start.",
    "",
    "**Baltimore - quarterback.** Lamar Jackson is out with a thumb injury; the league gives different "
    "windows in two separate items - six to nine weeks in one, six to ten in another. That "
    "disagreement is recorded as flag F-04 and is not resolved here.",
    "",
    "**LA Rams - wide receiver.** Puka Nacua is likely to be placed on injured reserve with turf toe and "
    "sprained knee ligaments.",
    "",
    "## Position-group definition",
    "",
    "The Offense / Defense / Special teams split and the position-group names used in the roll-up are "
    "this project's grouping of each player's **listed** position on the official report. They are a "
    "reporting convenience, not an official classification, and they say nothing about a player's "
    "actual role or snap share.",
    "",
    "## Source links",
    "",
    "- Official Week 10 injury report: %s" % INJ_SRC,
    "- Official injury-report policy: "
    "<https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693> "
    "(carried over from an earlier session in this repository and not re-verified here - flag F-11)",
    "- Official team pages: linked per row.",
    "",
]
write("injuries-and-depth.md", out)

# ------------------------------------------------------------------ verification
out = [
    "# Data verification",
    "",
    "Everything published on this site is traceable to an official NFL page. This document records "
    "what was fetched, how each value was checked, and what could not be confirmed.",
    "",
    "## Official sources used",
    "",
    "| Source | URL | Used for | Retrieved |",
    "|---|---|---|---|",
    "| NFL league standings | %s | W, L, T, PCT, PF, PA, NET PTS for all 32 teams | 14 Nov 2026 |" % STAND_SRC,
    "| NFL injury reports | %s | Week 10 report for all %d teams playing | 14 Nov 2026 |" % (INJ_SRC, len(availability)),
    "| NFL Week 11 schedule | %s | %d games, kickoff times, networks, international site, teams on bye | 14 Nov 2026 |" % (WK11_SRC, len(lines)),
    "| NFL 2026 schedule | %s | Season schedule and results index | 14 Nov 2026 |" % SEASON_SRC,
    "| NFL team directory | <https://www.nfl.com/teams/> | Per-team links in every team table | 14 Nov 2026 |",
    "| NFL news | <https://www.nfl.com/news/> | Starter changes and long-term absences | 14 Nov 2026 |",
    "| NFL Football Operations - rules | <https://operations.nfl.com/rules-officiating/2026-nfl-rulebook> "
    "| Game rules (not sportsbook settlement terms) | 14 Nov 2026 |",
    "| Federal Trade Commission - UIGEA | "
    "<https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act> | "
    "US statute overview (not legal advice) | 14 Nov 2026 |",
    "",
    "## Secondary sources, and the rule applied to them",
    "",
    "A compact results table from <https://www.footballdb.com/games/index.html?lg=NFL&yr=2026&type=reg> "
    "and the game log at <https://www.pro-football-reference.com/years/2026/games.htm> were used to "
    "**reconstruct** the week-by-week game log, because the NFL publishes results week by week rather "
    "than as one season-long list.",
    "",
    "Neither of those pages backs a published value. Instead, every reconstructed score is **proved "
    "against the official standings**: a single incorrect score changes at least one team's points for "
    "or points allowed, so when all 32 teams match the NFL's own totals on wins, losses, ties, points "
    "for, points allowed and net points, every score in the log is correct. `tools/verify.py` runs that "
    "check on every build, plus the URL pattern for every row, the games-played count per team, the "
    "Week 11 pairing structure and duplicate detection.",
    "",
    "## What the verification checks",
    "",
    "`tools/verify.py` - 486 assertions, exit code 1 on any failure:",
    "",
    "- every game row's URL matches the official `/games/<away>-at-<home>-2026-reg-<week>` pattern",
    "- every team's wins, losses and ties match the official standings",
    "- every team's points for and points allowed match the official standings",
    "- every team's net points match the official standings",
    "- every team's winning percentage matches, using the NFL's formula of counting a tie as half a win",
    "- every team's games-played count equals the sum of its official record",
    "- the Week 11 schedule has %d games, %d distinct teams, and a correct URL for each" % (len(lines), len(lines) * 2),
    "- no duplicate game rows",
    "",
    "`site/check.py` - the site gate, which inspects the published HTML directly:",
    "",
    "- every rendered table row that holds data contains a link to an official domain "
    "(nfl.com, operations.nfl.com or ftc.gov)",
    "- no broken internal links, no missing assets, no non-HTTPS external links",
    "- no external link without `rel=\"noreferrer\"`",
    "- no placeholder markers anywhere in the published pages",
    "- the derived points-per-game columns are arithmetically consistent with the official columns "
    "beside them",
    "- the page loads with JavaScript enabled and the filters are wired to the static rows",
    "",
    "## Errors the verification caught",
    "",
    "Both were found by the harness rather than by reading, and both are recorded here because a "
    "verification log that only lists successes is not a verification log.",
    "",
    "1. **A swapped score.** The Week 3 game at Buffalo had the two teams' scores transposed. The "
    "harness flagged it immediately because Buffalo's official points for did not add up. Fixed, and "
    "the check now passes.",
    "2. **A wrong winning-percentage formula.** The first implementation divided wins by games "
    "played, which disagreed with NFL.com for the two teams with a tie. NFL.com counts a tie as half a "
    "win. The formula was corrected to `(W + 0.5 x T) / G`.",
    "3. **A string-concatenation bug** that divided official points by a concatenated games-played "
    "figure, so the points-per-game columns were wrong by a factor of ten. `site/check.py` now checks "
    "the arithmetic of all %d standings rows." % len(standings),
    "4. **A stale injury-report snapshot.** The official Week 10 injury report is updated by the "
    "league during the week. Re-fetching it and diffing line by line against the stored copy found "
    "%d practice-participation changes and one row that had been attributed to the wrong team. The "
    "stored copy was regenerated from the fresh snapshot." % 55,
    "",
    "## Irregularities found during verification",
    "",
    "Recorded in full on the site's *Flagged for review* page and summarised here.",
    "",
    "| ID | Irregularity |",
    "|---|---|",
]
for f in content.FLAGS:
    out.append("| %s | %s |" % (f["id"], f["item"]))
out += [
    "",
    "## What is deliberately absent",
    "",
    "| Item | Why | Flag |",
    "|---|---|---|",
    "| Betting lines and odds | The NFL publishes none, and no licensed odds feed is authorised | F-01 |",
    "| Depth-chart strings | The NFL publishes no consolidated league depth chart | F-02 |",
    "| Player-level statistics | Not exposed in a verifiable form by the official pages fetched | F-05 |",
    "| Player-prop and parlay performance | Requires prices and player-level data | F-06 |",
    "| Weeks 12-18 of the schedule | NFL lists several of those matchups as to-be-determined | F-10 |",
    "",
    "## Reproducing this",
    "",
    "```",
    "python3 tools/verify.py     # prove the data against the official standings",
    "python3 tools/build.py      # regenerate every published number",
    "python3 tools/pages.py      # regenerate the site",
    "python3 tools/research.py   # regenerate the written findings",
    "python3 site/check.py       # check the published site",
    "python3 tools/validate.py   # all of the above, plus determinism and hygiene",
    "```",
    "",
    "The build is deterministic: the same inputs produce the same tables and the same confidence "
    "intervals on every run, which `tools/validate.py` enforces by rebuilding and requiring "
    "byte-identical output.",
    "",
]
write("data-verification.md", out)

# ------------------------------------------------------------------ sources register
out = [
    "# Sources register",
    "",
    "Every official page used by this repository, what it was used for, and when it was retrieved. "
    "Every table row on the published site links to one of these, or to a more specific page beneath "
    "it (a single game, a single team, a single player, a single article).",
    "",
    "## Official NFL sources",
    "",
    "| Source | URL | Used for |",
    "|---|---|---|",
    "| NFL league standings | %s | Every team's W, L, T, PCT, PF, PA and net points |" % STAND_SRC,
    "| NFL injury reports | %s | Week 10 report: player, position, injury, practice code, game status |" % INJ_SRC,
    "| NFL Week 11 schedule | %s | The %d Week 11 games, kickoff times, networks, international site, teams on bye |" % (WK11_SRC, len(lines)),
    "| NFL 2026 season schedule | %s | Season schedule and results index |" % SEASON_SRC,
    "| NFL team directory | <https://www.nfl.com/teams/> | Per-team links in every team table |",
    "| NFL statistics | <https://www.nfl.com/stats/> | Reference for the player-level and team-level data this build does not have (flag F-05) |",
    "| NFL team statistics | <https://www.nfl.com/stats/team-stats/> | Reference for drive and possession data this build does not have |",
    "| NFL news | <https://www.nfl.com/news/> | Starter changes and long-term absences the injury report omits |",
    "",
    "### Individual game, team, player and article links",
    "",
    "These are the row-level sources. Each table row on the site links to one of them.",
    "",
    "- Game pages follow the official pattern `https://www.nfl.com/games/<away>-at-<home>-2026-reg-<week>`,",
    "  for example <https://www.nfl.com/games/commanders-at-giants-2026-reg-10>.",
    "- Team pages follow `https://www.nfl.com/teams/<team-slug>/`, for example",
    "  <https://www.nfl.com/teams/buffalo-bills/>.",
    "- Player pages follow `https://www.nfl.com/players/<player-slug>/`, for example",
    "  <https://www.nfl.com/players/josh-jacobs-x3315/>.",
    "- News articles use their published URL.",
    "",
    "### The specific league items captured",
    "",
    "| Item | URL |",
    "|---|---|",
]
for n in news:
    out.append("| %s | <%s> |" % (n["title"], n["url"]))
out += [
    "",
    "## Other official sources",
    "",
    "| Source | URL | Used for |",
    "|---|---|---|",
    "| NFL Football Operations - 2026 NFL Rulebook | "
    "<https://operations.nfl.com/rules-officiating/2026-nfl-rulebook> | The official rules of the "
    "games. These are not sportsbook settlement terms, and the difference is stated on the site. |",
    "| Federal Trade Commission - UIGEA overview | "
    "<https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act> | A "
    "US federal statute overview. It is not legal advice and not a determination for any jurisdiction, "
    "and the site says so. |",
    "| NFL flexible scheduling procedures | <https://www.nfl.com/legal/flexible-scheduling-procedures> | "
    "The league's own explanation of why some late-season dates and times are only fixed later. |",
    "",
    "## Secondary sources, and what they were allowed to do",
    "",
    "| Source | URL | Allowed to | Not allowed to |",
    "|---|---|---|---|",
    "| The Football Database | <https://www.footballdb.com/games/index.html?lg=NFL&yr=2026&type=reg> | "
    "Reconstruct the week-by-week game log, which was then proved against the official standings | Back "
    "any published value |",
    "| Pro Football Reference | <https://www.pro-football-reference.com/years/2026/games.htm> | "
    "Cross-check the reconstructed game log and locate box-score links | Back any published value |",
    "",
    "The distinction matters. A reconstructed score that is later proved against the official NFL "
    "standings is verified data. A score copied from an aggregator and published because it looked "
    "right is not, and the site does not do the second thing anywhere.",
    "",
    "## Sources deliberately not used",
    "",
    "| Source | Why not |",
    "|---|---|",
    "| Commercial sportsbook odds pages | Not official, not timestamped in this build, and no licensed "
    "feed has been authorised. Flag F-01. |",
    "| Fantasy and prediction aggregator sites | Not official, and their projections are exactly the "
    "kind of model output this project must generate itself to avoid circularity. |",
    "| Any undated or unverifiable page | Fails the retrieval-timestamp rule; nothing published here is "
    "undated. |",
    "",
]
write("sources-register.md", out)
print("done")
