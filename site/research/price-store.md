# Price store, results feed and the origination order

**Session:** `arena/4e108e9a-x4` (task T21)
**Date:** 2026-11-14
**Scope:** the six items below. No published value from the model, the standings,
the injury report or the schedule was changed.

---

## 1. Which of the six requirements were already met, and which were not

An earlier session (`arena/da12b830-x4`) recorded a post-merge verification, and
its coordination board carries a row **T21** as unclaimed work. This session read
the published site page by page before writing anything, and the honest starting
position was different for each requirement.

| Requirement | State found | What this session did |
|---|---|---|
| Price-snapshot store with opening and closing numbers | **Not built.** `research/data/week11_odds_2026.csv` held a single undated snapshot of the current line. No opening number, no closing number, no snapshot identity. | Built a keyed store: 3 registered snapshots x 13 games x 3 markets = 117 rows. Opening and current are populated; closing is registered and empty. |
| Verified results feed | **Not built.** The game log (`data/games-2026.csv`) existed and was proved against the standings, but nothing joined an originated line to a result. | Built `results_feed()`: every originated line joined to a graded result or explicitly pending, with the grading rule stated. |
| Originate side, then total, then moneyline | **Partially.** All three markets were priced (`wk11_lines`), but with no stated order and no reason for one. | Published an explicit origination order with the evidence-based reason for each position. |
| Fair line, market line and difference as separate columns | **Not built.** The main site's market column was deliberately blank (no authorised odds feed); the decision-desk layer compared fair against market but with market as a linked label, not a column. | Three separate columns, plus the nine-strategy band, on both the price-store page and the results feed. |
| Separate signal from staking on the leaderboard | **Not built.** The leaderboard scored one composite per strategy. | Signal score and staking result computed from **different inputs**, ranked separately, both ranks published. |
| Track the depth of the replacement, not the fact | **Specified, not measured.** The decision-desk layer specified a deficiency pipeline; no count existed. | A measurable definition from official fields only, applied to all 28 clubs in the Week 10 report. |
| Correlations only from official numbers, with n published | **Met, but n was not a column** on the desk layer. | Every coefficient published with its n, and with the interval only where one can honestly be computed. |
| Demotion gate | **Specified, not implemented.** | Implemented as data: promotion, demotion, retirement, with the reason each strategy is not live. |

---

## 2. What was verified, and against what

Every check below was run in this session against a live official page.

| Check | Method | Result |
|---|---|---|
| Standings, 32 clubs | `nfl.com/standings`, both chunks, transcribed into `research/verification/standings-2026-11-14-session-4e108e9a.csv` and diffed field by field against `data/standings-wk10-2026.csv` | **192 of 192 fields match** (W, L, T, PF, PA, NET x 32). Sum PF = sum PA = 6,291; wins = losses = 136; ties = 2; 137 games. |
| Week 11 schedule, 13 games | `nfl.com/schedules/2026/by-week/week-11`, all three chunks | **13 of 13 match** on matchup, date, kickoff time, network, game-page URL and the Mexico City designation. |
| Week 10 injury report, 8 clubs | `nfl.com/injuries`, chunks 0, 3 and 4 - 101 players transcribed with player links into `research/verification/injuries-week10-2026-11-14-session-4e108e9a.csv` | **401 of 404 fields match.** Three practice statuses differ; published as **F-18**, not corrected. |
| Market lines, 13 games, 3 markets | ESPN's published odds for the same event ids, read through ESPN's odds feed | **39 opening values and 39 current values captured**, each with its source row. Registered as tier T3, never as an official NFL value. |
| The NFL publishes no odds | `nfl.com/odds/` fetched directly | **HTTP 404** - independently reproduced, confirming F-01. |
| The NFL publishes no depth chart | `nfl.com/teams/depth-chart` and `nfl.com/teams/kansas-city-chiefs/depth-chart` fetched directly | **Both HTTP 404** - independently reproduced, confirming F-02. |
| The model numbers did not move | `tools/market_store.py` imports `tools/build.py` and calls the same nine strategy functions; no parameter was edited | The origination card reproduces the site's S1 line exactly. |

---

## 3. The origination order, and why it is that order

| Order | Market | Reason |
|---|---|---|
| 1 | Side (spread) | The only market whose error this desk can measure, because every final score is in hand. 105 out-of-sample games. |
| 2 | Total | Priced off the same team rates but a different error process: the margin-vs-total correlation measured on the official game log is **-0.32**. A side edge carries no information about the total. |
| 3 | Moneyline | A conversion of the spread plus the push mass plus the vig. It inherits every spread error and adds its own, so it is originated last. |

The order is published on `markets.html` with this reasoning, not asserted as a
preference.

---

## 4. The signal / staking split

**Signal** is built only from evidence about the line: benchmark improvement
(0.35), significance (0.30), weekly stability (0.20) and calibration (0.15). None
of those inputs can be moved by a staking run.

**Staking** is a flat 1-unit book at -110 on the strategy's directional call, over
the same 105 out-of-sample predictions. It is displayed beside the signal and can
never enter it.

| Strategy | Signal | Signal rank | Staking rank | Flat-stake ROI | State |
|---|---|---|---|---|---|
| S1 Simple mean, opponent-adjusted | 56.6 | 1 | 1 | +25.5% | paper |
| S8 Last 5 games window | 55.4 | 2 | 2 | +23.6% | paper |
| S2 Exponentially weighted | 52.1 | 3 | 3 | +20.0% | paper |
| S5 Median + shrinkage | 48.5 | 4 | 4 | +16.4% | paper |
| S3 EW + shrinkage | 39.1 | 5 | 5 | +9.1% | paper |
| S4 Fast EW + heavy shrinkage | 36.7 | 6 | 6 | +9.1% | paper |
| S7 Blend S3 and S6 | 33.9 | 7 | 7 | +5.5% | paper |
| S6 Slow EW + heavy shrinkage | 28.3 | 8 | 8 | -5.5% | paper |
| S0 League constant | 15.0 | 9 | 9 | -18.2% | paper |

**The two ranks agree today, and that is the finding, not a success.** The reason
is mechanical: with a flat stake at a fixed price, the staking result is a
monotone function of the hit rate, and the hit rate is one of the inputs the
signal score already uses. A split that only separates two columns which move
together is not yet doing the work.

It becomes load-bearing in exactly two situations, and the page says so:

1. **Stake sizing that reacts to the bankroll.** Once stakes vary with the running
   total, the staking result stops being a function of the hit rate. A hot run on
   increasing stakes can then outrun a flat-stake number by a wide margin, and the
   two ranks separate.
2. **A different bet selection.** If a strategy stakes only the games it rates most
   highly, the staked subset is not the same 118 games the signal is scored on, and
   the two are no longer measuring the same thing.

Until one of those is in place, the flat-stake column is presented as a sanity
check on the hit-rate column rather than as independent evidence. That is the
honest description, and it is printed on the page next to the table.

### A second, sharper finding from the same numbers

The significance gate still fails for every strategy. The bootstrap interval on
the **average** margin error contains zero - but the **paired sign test** on the
same 118 games does not: S1 lands closer to the truth than the league-constant
benchmark in **78 of 118 games (66.1%), exact binomial p = 0.00030** (regenerated by
`tools/sign_test.py`; the 68-of-105 figures this paragraph previously quoted described a
superseded corpus and are corrected here, not silently dropped). Both of those
sentences are true at the same time, and the difference matters:

- The bootstrap interval is on a *mean absolute error difference*, a quantity
  dominated by a handful of blowouts where no model does well.
- The sign test is on the *direction of the smaller error*, which is what a
  head-to-head comparison actually asks.

This session did **not** change the gate, because changing a gate after seeing
that a strategy would pass it is the exact behaviour the gate exists to prevent.
It is published as an open question on the suggestions register instead (**S-15**),
with the decision it needs.

---

## 5. Replacement depth, measured

No official source labels depth-chart strings. `nfl.com/teams/<club>/depth-chart`
returns 404, and the club sites publish ordered charts without 1st/2nd/3rd/4th
labels. So "depth of the replacement" is defined as something an official page
actually supports:

```
depth of replacement = officially full participants / players ruled out
```

| Club | Listed | Out | Limited | Full | Depth of replacement | Hardest-hit unit |
|---|---|---|---|---|---|---|
| LAR | 14 | 7 | 5 | 2 | **0.3** | defence |
| MIN | 13 | 6 | 4 | 3 | **0.5** | offence |
| GB | 17 | 6 | 7 | 4 | **0.7** | offence |
| HOU | 16 | 7 | 3 | 6 | **0.9** | offence |
| JAX | 11 | 3 | 5 | 3 | 1.0 | defence |
| DAL | 19 | 8 | 2 | 9 | 1.1 | defence |

(The four rows above are the four thinnest clubs in the report; the full 28-club
table is on `gates.html`.)

Clubs below 1.0 have fewer healthy listed bodies than players ruled out. That is
a **proxy**, and the page says so: it measures how much of the officially healthy
listing is left, not who lines up on Sunday. An impact weight per position (QB 3,
line and secondary 2, others 1) is declared in the source as an analyst choice so
a reviewer can change it and see the impact columns move.

---

## 6. Correlations, with n

Every coefficient on `gates.html` carries its n as a column:

- Four cross-game coefficients from the official game log, with Fisher-z 95%
  intervals: **n = 54 to 57**, intervals published.
- Nine-strategy pairwise model-error correlations over the **same 105 evaluated
  games**, with **no interval published** - the nine strategies are not
  independent of each other or of the benchmark, so a Fisher-z interval would
  overstate its own precision. The page states the reason.

The distinction is deliberate: **n = 8 and n = 105 are not the same evidence**, and
a table that leaves n out lets a reader treat them as if they were.

---

## 7. The demotion gate

| State | Rule |
|---|---|
| **Live** | Every gate passed in the same evaluation window. |
| **Paper** | Anything else. Published and tracked; not eligible for reward. |
| **Retired** | Two demotions. A model that alternates between passing and failing is showing that the gate is noisy, not that the model is good. |

The gate is implemented in `tools/market_store.py` as `signal_and_staking()`, and
the published table carries the specific reason each strategy is not live. Today
that reason is the same for all nine: the significance gate.

---

## 8. What is still missing, and what would close it

| Gap | Why it matters | What closes it | Decision needed |
|---|---|---|---|
| No closing line | CLV - the only luck-resistant economic measure - cannot be computed | Take a closing snapshot at/after each kickoff | Who captures it, and at what clock time (Q-S1) |
| No spread/total price in the opening snapshot | CLV needs the price, not just the points | Read the price game by game at capture | Whether a single -110 is an acceptable proxy (Q-S2) |
| Signal and staking ranks are collinear | The split is not yet load-bearing | A staking rule that is not a monotone function of the hit rate | Whether variable staking is in scope at all (Q-S3) |
| 118 evaluated games from one season | Every gate is underpowered | Prospective, locked predictions across seasons | Who locks the line and how the lock is enforced (Q-S4) |
| No injury-impact measurement | Depth is counted, not priced | Snap counts from official game books | Whether game books may be parsed and redistributed (Q-S5) |
| Market is a single provider | A single book is not a market | A licensed multi-provider feed | Budget and licensing (Q-S6) |

Full question register with these items: `site-questions.html` on the published site.
