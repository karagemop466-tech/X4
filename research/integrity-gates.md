# Integrity gates: what was built, what it proves, and what it still cannot answer

Generated context and hand-written findings for `site/programme.html`. Every figure in
this note is reproduced by `python3 tools/build_integrity.py`, whose formulas are
printed in the source. No number here was typed in from memory.

Captured at **2026-11-14T19:17Z**. Sources are named per claim; the store itself carries
the URL on every row.

---

## 1. The price-snapshot store

`research/data/price_snapshots_2026.csv` holds one row per game and keeps every phase in
separate columns: opening, current and closing, for the spread, the total and both
moneylines. It is **14 games** (the 13-game Week 11 slate and the settled Week 10
Thursday game) and **252 derived price rows** once expanded to long format.

**Provider.** DraftKings, as syndicated by ESPN's public odds endpoint
(`sports.core.api.espn.com/.../odds`). The provider name and id are recorded on every
row. This is **not** an NFL line: the league publishes no betting lines, which the
existing Flagged page records as F-02. The distinction matters and is made explicit on
the page.

**What the store proves.** The settled Week 10 game is the proof of concept. Its total
moved from **47.5 at the open to 40.5** by the close, a seven-point adjustment, while
the spread never left 1.5. Any model that only looked at the close would have missed the
single largest piece of information the market produced that week.

**What the store does not have yet.** Thirteen of the fourteen games have no close,
because a close does not exist until settlement. That is not missing data to be
back-filled; it is data that has not happened yet. The one rule the page follows is that
an absent close is published as blank and never replaced with the current number.

**Irregularity found while building it.** The captured `spread` field is quoted from the
**away** side, so `spread: +10` means the *away* team receives ten points and the *home*
team is favoured. The first draft of the origination table read the sign the other way
and produced a market-side column that said `IND` was favoured at `HOU`. It was caught
by cross-checking against the desk's independent line table (which has HOU −10) and
fixed. The data now agrees with that independent table on all 13 games, which is the one
cross-check available.

---

## 2. The verified results feed

`research/data/results_2026.csv`: **137 games**, Weeks 1–10, each with both scores, an
overtime flag, a status and the official NFL.com game URL.

The feed is not merely collected, it is **proved**. Wins, losses, ties, points for,
points allowed and net points are recomputed from the feed for all 32 clubs and compared
field by field with the official standings table: **192 fields, zero mismatches**. A
single transposed score anywhere in 137 games would break at least two of those fields.

This is the prerequisite for ROI. A backtest without a settled-results feed can report
error metrics and nothing else, because it has nothing to settle against. The existing
strategy lab is exactly in that position: it reports MAE and calibration, no money.

**Limitation.** The feed covers ten weeks. Every gate that requires a hundred settled
bets is therefore failing on sample size, not on skill, and no amount of analysis
substitutes for the other eight weeks.

---

## 3. Settling a paper bet end to end

`research/data/results_graded_week10.csv`: nine strategy models, one settled game,
market by market. Week 10 WAS 24 at NYG 21.

| Market | What is graded | Result on the night |
|---|---|---|
| Spread | The side the model's line favours, settling against the **closing** number | 5 of 9 models won, 4 lost. S0's line was within 0.02 points of a pick'em and finished 3 points the wrong side of the actual margin |
| Total | Over or under the closing total | All nine models took the over and all nine won |
| Moneyline | The side the model favours, at the closing price | the same 5 won and 4 lost, at +105 and −125 respectively |

**The total row is the trap and it is worth stating plainly.** Nine models, nine wins on
the total, looks like a perfect signal. It is one game. A hit rate of 9/9 on n = 9
different models is not nine independent pieces of evidence; the existing correlation
matrix already shows those models' predictions correlate between 0.92 and 0.999, so
this is essentially one bet made nine times.

**The correction this work forced.** The first version of this dataset published a
column named `clv_points`. It was wrong. It measured how far a model's line sat from the
closing number, which is a *disagreement*, not closing-line value. CLV is the difference
between the price **taken** and the price at the close. This project has never taken a
price — every strategy is paper-only — so the CLV ledger is published with **zero rows**
and every gate that depends on CLV reports **BLOCKED**. The column is renamed
`disagreement_points` and the mistake is recorded on the page rather than quietly
corrected.

---

## 4. Side, then total, then moneyline

`research/data/market_origination_wk11.csv`: 13 games, each with our fair line, the
market line and the difference as three separate columns, plus a gap bucket.

| Gap between our line and the market | Games |
|---|---|
| within 1 point | 1 |
| 1–2.5 points | 1 |
| 2.5–5 points | 3 |
| more than 5 points | 9 |

**The ordering is a dependency, not a preference.** The side is estimated from team
strength. The total is estimated from scoring and conceding rates. The moneyline is
**not an independent estimate**: it is the side converted to a win probability through
the same distribution (σ = 13.47 points, the sample standard deviation of the margin
over 57 official games). Presenting it as a third independent opinion would count one
signal twice, which is the exact failure mode the correlation gate exists to prevent.

**What a big gap means.** Nine of thirteen games sit more than five points from the
market. It would be easy to publish that as an edge. It is much more likely to be the
model's blind spot: the model uses season-to-date scoring rates and ignores who is
actually available, rest, travel and weather. A five-point disagreement with a market
that prices all of those is a reason to investigate, not a reason to bet.

---

## 5. Signal separated from staking

Two boards, never combined.

**Signal board** — per model: settled bets, wins, hit rate, average disagreement,
average no-vig cover probability, Brier score, share of bets that beat the close, and n.
**Staking board** — per model: net units, drawdown, survival.

The signal board is what survives a lucky or unlucky staking pattern. A model that beats
the close 58% of the time over 500 bets has a signal whether or not the staking rule
survived the drawdown; a model that won because it happened to be staked large during a
four-week streak has no signal regardless of its bankroll.

**The demonstration** (`research/data/staking_vs_signal_sim.csv`, labelled on the page as
a simulation and not evidence about any market):

| Edge | Staking | 100 bets | 1,000 bets | 5,000 bets |
|---|---|---|---|---|
| Fair coin, p = 0.500 | flat 1-unit | 103.09 | 73.64 | **busted** (bet 3,799) |
| Fair coin, p = 0.500 | 5% of bankroll | 104.18 | 8.52 | **busted** |
| Real edge 2.4 pts, p = 0.524 | flat 1-unit | 108.82 | 109.91 | 178.18 |
| Real edge 2.4 pts, p = 0.524 | 5% of bankroll | 138.84 | 52.51 | 16.79 |

Two identical edges, two staking rules, opposite outcomes. The 5,000-bet real edge that
grows steadily under flat staking shrinks to 16.79 under proportional staking, because a
drawdown cut the position size at the worst possible moment. The signal never changed.
A leaderboard that ranks on bankroll is ranking the staking column and calling it skill.

**Honest limitation.** The simulation is deterministic and seeded, but it is still one
path. It demonstrates a mechanism, not a distribution. The real leaderboard needs
thousands of settled paper bets before its signal column means anything, and that is a
data-availability problem, not a modelling one.

---

## 6. Replacement depth

`research/data/replacement_depth_measured.csv`: seven rows, each recording the depth
slot the replacement occupies. The point of the requirement is that "the starter is out"
carries almost no information: a team replacing its quarterback with a former starter and
a team replacing him with a third-string call-up trip the same flag.

| Measured | Rows |
|---|---|
| Depth slot recorded | 7 of 7 |
| Replacement identified by name | 5 of 7 (two rows leave it blank) |
| Replacement starts this season | 1 of 7 |
| Snap share | **0 of 7** |
| Deficiency points | **0 of 7** |

Three of the five columns are substantially blank, and this is the honest state. The
official injury report publishes a **designation** — Out, Doubtful, Questionable, or a
practice status — not snap counts. Depth slot is derivable from the club's published
chart; playing time is not obtainable from any official page this repository has
verified.

**Irregularity that blocks the table.** Baltimore's row records two different official
absence windows for the same player: 6–9 weeks from one NFL.com item and 6–10 from
another. That is already on the Flagged page as **F-04**. The depth table records both
and refuses to price either. A depth measurement is only worth what the availability
assumption beneath it is worth, and that assumption currently has two official answers.

---

## 7. Correlations, each with n

`research/data/correlation_n.csv`: five values, each with its n, a 95% Fisher-z
interval, the exact input file, and the official page the input came from.

| Quantity | r | n | 95% interval | Excludes zero |
|---|---|---|---|---|
| Away score vs home score | 0.0182 | 57 | [−0.243, 0.278] | no |
| Margin vs total | −0.3099 | 57 | [−0.528, −0.054] | **yes** |
| Margin vs total, neutral sites removed | −0.3224 | 54 | [−0.543, −0.060] | **yes** |
| Net points vs win % | 0.8717 | 32 | [0.751, 0.936] | **yes** |
| Points for per game vs points against per game | −0.2041 | 32 | [−0.516, 0.156] | no |

**The one that matters for parlays** is margin vs total, r = −0.31 on n = 57 (r = −0.32 with neutral sites removed, n = 54). In
high-scoring games the margin tends to shrink, so a "favourite covers and the over hits"
parlay has two legs pulling against each other. Pricing that joint at the product of two
independent probabilities overstates the payout, which is precisely what the parlay gate
exists to catch.

**The one that does not** is the away-score/home-score correlation, r = 0.018, which is
indistinguishable from zero. Two teams' scores are not usefully dependent in this
window, so "both teams over" cannot assume dependence in either direction.

**What is deliberately absent.** Every player-level prop correlation. Those need paired
per-player game logs, which this repository does not hold. They are not estimated.

---

## 8. The demotion gate

`research/data/demotion_gate_rules.csv`: five written rules, each with a state and a
reason.

| Gate | Rule | State | Why |
|---|---|---|---|
| D1 signal | Beat the close on ≥55% of ≥100 settled bets | **BLOCKED** | 9 settled bets; no stake-time capture |
| D2 staking | Net ROI 95% CI lower bound > 0 | **NOT MET** | n = 9 < 100 |
| D3 probability quality | Brier < 0.25 | **NOT MET** | n = 9 < 100 |
| D4 survival | Drawdown ≤ 20% of peak | **NOT MET** | measured over nine rows |
| D5 availability | ≥1 priced market at stake time | **BLOCKED** | no stake-time capture exists |

**The gate's most useful property is that it fails loudly on an empty dataset.** A gate
that passed here would be worse than no gate at all. Two of the five rules cannot be
evaluated until the first pre-kickoff capture writes a row, and that single pipeline
change unblocks both.

**What demotion means in practice.** A demoted strategy keeps publishing its line into
the store and its pre-registered bets into the feed; its staking board is frozen and its
signal board keeps accumulating. Promotion back requires re-clearing D1 and D2 on a
fresh sample. The loop is the point: the only exit is more out-of-sample evidence, which
is the one thing a lucky run cannot manufacture.

---

## 9. The questions that must be answered before an ROI or reward decision

These are ordered by what they block. Each carries the dataset that would answer it.

1. **What is a stake, and when is it placed?** Every ROI and CLV number is undefined
   until "the price we got" is a recorded fact. *Blocked on:* the first pre-kickoff
   capture. *Blocks:* D1, D5, and the entire reward schedule.
2. **How many settled bets exist, and are they independent?** Nine bets across nine
   highly correlated models is closer to one observation than nine. *Blocked on:* the
   full-season feed and the model-correlation matrix applied when counting n.
3. **Which staking rule is the benchmark?** Flat units and proportional staking produce
   opposite verdicts on the same signal (section 5). Until the rule is fixed in advance,
   any ROI comparison can be tuned after the fact. *Blocked on:* a policy choice, not
   data.
4. **What is the reward paid on?** A reward on bankroll pays for luck by construction.
   A reward on CLV pays for signal but needs question 1 answered first. *Blocked on:*
   question 1 plus a policy decision.
5. **Does the market we price against still exist at stake time?** The store captures
   one provider. If a strategy's edge exists only at a price no bookmaker offers, ROI is
   fictional. *Blocked on:* capturing the price actually available to the account that
   would take it.
6. **Is a 5-point disagreement with the market a signal or a blind spot?** Eight of
   thirteen Week-11 games disagree by more than five points. The answer determines
   whether the model is worth improving or abandoning. *Blocked on:* pricing
   availability into the side, which is blocked on the depth measurement in section 6.

**The one decision this work can support today** is to keep every strategy in paper mode
and to start the capture. Nothing else is supported by the data currently in the
repository.
