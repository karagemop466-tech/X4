# Decision register: what is known, what is missing, and what would settle it

> **Status after the T31 integration (2026-11-14, session `arena/f7614083-x4`).**
> The findings below are unchanged and still correct: they were true when they were
> written and nothing here has been rewritten to look newer than it is. What changed is
> the surrounding state, and a reader needs to know it:
>
> * A **second, wider price capture** now exists - 29 games, opening and closing, spread,
>   total and moneyline - published on `market.html`, and it is graded against the official
>   NFL.com results: **432 graded bets over 16 settled games, nine strategies**, with a
>   skill board that cannot see a stake and a staking board beside it. Every one of the
>   nine strategies breaches at least one demotion rule and sits on paper.
> * The two captures were taken independently and are **reconciled number by number**:
>   112 of 112 comparable values match (`tools/reconcile_prices.py`, part of the
>   publication gate; the row-by-row record is
>   `research/data/price_capture_reconciliation.csv`).
> * The word **"close" means different things in the two stores** - that is flag F-38.
> * The prices are **not official**. The league publishes no betting lines; the numbers
>   are one book's, published by ESPN, and are labelled non-official everywhere they
>   appear (F-01, F-18, F-36).
>
> Nothing above changes the conclusion of this note: the sample is still far short of the
> gate thresholds, and no strategy is eligible for reward.

Every row states one question that blocks a decision, the answer the repository can
currently support, the information that answer is missing, and the concrete step that
would obtain it. **The answer column never guesses.** Where the data cannot support an
answer, the row says so and the decision is marked blocked.

Status vocabulary:
- **ANSWERED** — the data in this repository settles it today.
- **PARTIAL** — part of the question is settled and the rest is named.
- **BLOCKED** — cannot be answered without information the repository does not hold.
- **POLICY** — not a data question at all; it needs a human decision.

Companion data: `research/data/integrity_summary.json`,
`research/data/demotion_gate_rules.csv`, `research/data/correlation_n.csv`.

---

## A. The market and the price

| # | Question | Answer today | Missing information | How to obtain it | Status |
|---|---|---|---|---|---|
| A1 | What price was available to us at the moment a stake would have been placed? | **Nothing.** No stake-time capture exists. The store starts 2026-11-14T19:17Z and every strategy is paper-only | A timestamped price row written before kick-off | One scheduled run per week that writes `price_snapshots_2026.csv` at T−60 minutes | BLOCKED |
| A2 | Did the market move after we would have bet? | **Yes, sometimes a lot.** The one settled game moved 7 points on the total (47.5 → 40.5) and 0 on the spread | Which of our 13 Week-11 games will move, and in which direction | The same scheduled capture, then a diff of open/current/close | PARTIAL |
| A3 | Is the DraftKings-via-ESPN price the price we could actually get? | **Unknown.** The feed is a public syndication, not an executable quote | Whether the account that would take the bet sees the same number, and any limit on stake size | Read the actual book's price at the moment of the stake and store it beside the syndicated one | BLOCKED |
| A4 | Does an official NFL line exist? | **No.** The league publishes no betting lines; recorded as F-01, F-18 and F-36 | — | — | ANSWERED |
| A5 | How many games can we price? | **13 of 13** on the Week-11 slate, plus 1 settled Week-10 game | Weeks 12–18, which NFL lists as to-be-determined (F-10) | Wait for the league to publish them; do not guess kickoff times | PARTIAL |

## B. The results feed and the sample

| # | Question | Answer today | Missing information | How to obtain it | Status |
|---|---|---|---|---|---|
| B1 | Can every published score be trusted? | **Yes.** All 150 completed games through Week 10 reproduce all 32 official standings rows on 192 fields | — | — | ANSWERED |
| B2 | How many settled bets exist? | **Nine** in the integrity store (one game × nine models) and **432** in the price archive (16 settled games × nine strategies × three markets) | The rest of the season | Settle weeks 1–9 from the feed; the scores already reconcile | PARTIAL |
| B3 | Are those nine bets independent? | **No.** The models' prediction errors correlate 0.92–0.999 | An effective sample size, not a raw count of rows | Report the *number of independent signals*, not the number of bets, and shrink n accordingly | BLOCKED |
| B4 | Is a 55% hit rate distinguishable from luck at the sample we have? | **No.** No gate accepts fewer than 100 settled bets | More settled bets | See B2 | BLOCKED |
| B5 | Is there a full official per-play or per-drive source for player stats? | **Not confirmed.** No official per-player game log has been verified in this repository | An official, machine-readable player-log source | Verify `nfl.com/stats/player-stats` and NFL's Next Gen Stats documentation before using either | BLOCKED |

## C. The model

| # | Question | Answer today | Missing information | How to obtain it | Status |
|---|---|---|---|---|---|
| C1 | What is our fair line for each Week-11 game? | **Published** for all 13 games as a median across nine strategies | Which single strategy is the fair line | A decision on whether to publish a range or nominate one model | POLICY |
| C2 | Why do 9 of 13 lines disagree with the market by more than 5 points? | **Unknown, but the likely cause is named**: the model ignores availability, rest, travel and weather | Whether pricing availability would close the gap | Add the depth-slot measure to the side estimate and re-measure the gap | BLOCKED |
| C3 | Is the model's win probability calibrated? | **Partially.** The existing lab reports calibration bands; the new moneyline derivation is one distribution applied to the side | Out-of-sample calibration of the *moneyline* specifically | Score the derived moneylines against settled results once B2 is done | PARTIAL |
| C4 | Should the moneyline be a separate model? | **No** (a modelling position, stated as such): it is the side converted through the same σ | — | — | ANSWERED |
| C5 | What is σ and where does it come from? | **13.47 points**, sample standard deviation of the margin over 57 official games | Whether σ is stable across weeks and game states | Recompute per week and compare; a drift means the win-probability column is mis-scaled | PARTIAL |

## D. Staking, rewards and demotion

| # | Question | Answer today | Missing information | How to obtain it | Status |
|---|---|---|---|---|---|
| D1 | Should the leaderboard rank on bankroll? | **No.** Simulation shows identical edges producing opposite bankroll outcomes under two staking rules | — | — | ANSWERED |
| D2 | Which staking rule is the benchmark? | **Undecided** | A policy choice, plus the bankroll and risk tolerance it implies | Fix one rule in advance, in writing, before any live run | POLICY |
| D3 | What should a reward be paid on? | **Undecided, but constrained**: not bankroll (D1). CLV is the right target and is currently unmeasurable (A1) | A1, plus a policy choice on what counts as "beating the close" | Start the capture; hold rewards until D1/D2 clear | BLOCKED |
| D4 | When is a live strategy demoted? | **Specified**: five rules, states published, two blocked | A live strategy to demote, and A1 for two of the rules | Run the gate weekly; it is a script, not a meeting | PARTIAL |
| D5 | Can a demoted strategy return? | **Yes, by re-clearing D1 and D2 on a fresh sample** | — | — | ANSWERED |
| D6 | How large is the reward pool? | **Blank.** No figure is published anywhere in this repository | A business decision | Not ours to invent; record it as blank until given | POLICY |

## E. Availability and depth

| # | Question | Answer today | Missing information | How to obtain it | Status |
|---|---|---|---|---|---|
| E1 | Who is out this week? | **Known** for every player on the official Week-10 report and the league-news items that carry long-term absences | Players on IR/PUP/non-football injury are omitted by the public report (F-03) | Use league news per transaction; already partially captured in `data/qb-starter-changes.csv` | PARTIAL |
| E2 | How deep is the replacement? | **Depth slot recorded for 7 of 7 rows** in the new dataset | Any measure of how much of the job the replacement actually does | Official snap counts, which this repository has not verified a source for | BLOCKED |
| E3 | How many weeks is a player actually out? | **Conflicting.** Two official NFL.com items give 6–9 and 6–10 weeks for the same player (F-04) | A ruling on which official item governs | A human decision, recorded, with both links kept | BLOCKED |
| E4 | Does an official page label 1st/2nd/3rd/4th string? | **No.** `nfl.com/teams/<club>/depth-chart` returns 404 (F-03 on the console); club sites publish ordered charts without string labels | — | — | ANSWERED |
| E5 | Does availability explain the market gap? | **Unknown** — the natural next experiment | E2 and E3 | Price the depth measure into the side and re-measure C2 | BLOCKED |

## F. Correlations and combinations

| # | Question | Answer today | Missing information | How to obtain it | Status |
|---|---|---|---|---|---|
| F1 | Do two teams' scores depend on each other? | **No**: r = 0.018, n = 57, interval spans zero | — | — | ANSWERED |
| F2 | Do margin and total depend on each other? | **Yes, negatively**: r = −0.31, n = 57, interval excludes zero | How stable it is across seasons | Recompute per season and publish the interval each time | PARTIAL |
| F3 | Can a two-leg parlay be priced from the two singles? | **No** — F2 shows the independence assumption is false for the favourite/over pair | The joint distribution | Prices and settled joints; the store will supply them once it has closes | BLOCKED |
| F4 | What is the correlation between two props on the same team? | **Blank.** No paired player logs exist | Same as B5 | Same as B5 | BLOCKED |
| F5 | How many correlations have been computed in total? | **Five**, each with n and an interval | Player-level anything | B5 | PARTIAL |
| F6 | Is a "same-game parlay" offered at a fair price? | **Unknown.** No joint price has been captured | The offered joint price at stake time | Extend the capture to parlay prices | BLOCKED |

## G. Governance of this project

| # | Question | Answer today | Missing information | How to obtain it | Status |
|---|---|---|---|---|---|
| G1 | What happens to a suggestion before it is built? | **It is reviewed, accepted, held or rejected on `review.html`, and the choice is stored** | Nothing | — | ANSWERED |
| G2 | Who decides? | **The repository owner.** Recorded as such on the page; no automation chooses for them | — | — | ANSWERED |
| G3 | How is a published number kept honest? | **It is generated by a script from a committed dataset, and the build fails if the page and the dataset disagree** | — | — | ANSWERED |
| G4 | What happens when a figure cannot be sourced? | **It is left blank, flagged, and listed on the Flagged page** | — | — | ANSWERED |
| G5 | Who resolves F-04 and the other flagged irregularities? | **A human, after review.** Flagged items do not block publication; they block the decisions that depend on them | A ruling | Review the Flagged page | POLICY |

---

## The four suggestions that would most improve decisions, in order

1. **Schedule the capture before the kick-off.** It is one job, and it unblocks A1, A2,
   D3 and the two blocked demotion gates. Nothing else on this list has that leverage.
2. **Settle weeks 1–9 from the feed that already reconciles.** It costs one script and it
   moves B2 from 9 settled bets to 1,350 (150 games × 9 models), which is the first sample any gate accepts.
3. **Stop publishing a bankroll leaderboard, even in paper mode.** D1 is settled by
   simulation; continuing to rank on bankroll teaches the reader the wrong lesson.
4. **Publish the number of independent signals, not the number of bets.** B3 is the
   single most flattering mistake available: nine correlated models look like nine
   chances to be right and are closer to one.

## What this register deliberately does not do

It does not answer C2, E5 or F3 by inference. Each has a plausible story — the model
ignores injuries, availability explains the gap, correlated legs explain the parlay
pricing — and **a plausible story is not evidence**. Each is marked blocked with the
dataset that would settle it named on the row.
