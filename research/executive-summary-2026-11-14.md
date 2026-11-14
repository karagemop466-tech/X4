# Executive summary — 2026-11-14

**Project:** Fourth Down / NFL Decision Desk (repository `karagemop466-tech/X4`)
**Session:** `arena/4e108e9a-x4`, task **T21** on the coordination board
**Published site:** https://karagemop466-tech.github.io/X4/
**New pages this session:** `markets.html`, `results.html`, `gates.html`

---

## The one-paragraph version

The paid-data problem this project had is now a *store* problem, not a *guess*
problem. Every Week 11 market we originate now has an opening number, a current
number, a registered-but-empty closing slot, a fair line from our own model and a
difference column beside it — stored in a keyed CSV, not in prose. Three new
pages publish it, plus a results feed that refuses to grade an unplayed game, a
leaderboard that scores signal and staking on separate inputs, replacement depth
measured from official counts instead of asserted from a depth chart that does
not exist, and a demotion gate that is implemented rather than described. The
central conclusion is uncomfortable and unchanged: **no strategy passes the
significance gate, so nothing is live, nothing is stakeable, and every reward
figure stays blank.** Along the way this session found one new data irregularity
(three practice statuses have moved since the committed snapshot) and one new
and more important statistical finding: on the same 105 games, the model is
closer to the truth than the benchmark **64.8% of the time (p = 0.0016)** even
though the mean-error interval still contains zero.

---

## 1. What was delivered

| # | Requirement | Delivered as | Verified by |
|---|---|---|---|
| 1 | Price-snapshot store, opening and closing | `data/market-snapshots.csv` (3 dated snapshots), `data/market-prices.csv` (117 rows), `markets.html` | 78 populated values, each with a source row; 39 closing rows empty by design |
| 2 | Verified results feed | `results_feed()` in `tools/market_store.py`, `results.html` | 13 rows joined, 0 graded, 13 explicitly pending; an assertion fails the build if a pending row ever carries an outcome |
| 3 | Side, then total, then moneyline | `ORIGINATION_ORDER`, published with reasons | Order is a data structure read by the page, not a sentence in a paragraph |
| 4 | Fair, market and difference as three columns | `origination_card()` (S1 fair line), on `markets.html` and `results.html`; PR #21 publishes the S3 line in the same three columns on `lines.html` | `diff == fair - market` asserted for all 13 rows; the sign conversion is one named function and round-trip tested |
| 5 | Signal separated from staking | `signal_and_staking()`, on `gates.html` | Two independent inputs, two ranks, plus an assertion that no staking result can exceed the maximum a flat -110 book can return |
| 6 | Depth of the replacement | `replacement_depth_rows()`, all 28 clubs on `gates.html` | Counted from official fields only; no depth-chart string is asserted anywhere |
| 7 | Correlations with n | `corr_with_n_rows()`, 40 coefficients on `gates.html` | n is a column; the interval is published only where it can honestly be computed |
| 8 | Demotion gate | `DEMOTION` + per-strategy reasons on `gates.html` | 9 of 9 strategies paper; the gate is data, and the build asserts nothing is live |
| 9 | Suggestions a reviewer can choose between | existing `suggestions.html` + new **S-15** on `review.html` | 18 proposals with Accept/Hold/Reject |
| 10 | Questions, information and answers before deciding | existing `questions.html` (16) + `review.html` (30 Q&A) + `research/price-store.md` §8 | every open gap paired with the decision that closes it |

---

## 2. What is verified, and how

| Claim | Source | Method | Result |
|---|---|---|---|
| Standings, all 32 clubs | nfl.com/standings | fresh transcription, then a field-by-field diff against the committed CSV | **192 / 192 fields match** |
| Week 11 schedule, 13 games | nfl.com/schedules/2026/by-week/week-11 | all three chunks read | **13 / 13 match** on matchup, date, time, network, URL, Mexico City flag |
| Week 10 injuries, 8 clubs | nfl.com/injuries | 101 players transcribed with player links, 404 fields diffed | **401 / 404 match**; 3 practice statuses differ → **F-18** |
| The NFL publishes no odds | nfl.com/odds/ | fetched directly | **404** — independently confirmed |
| The NFL publishes no depth chart | nfl.com/teams/depth-chart, /teams/kansas-city-chiefs/depth-chart | fetched directly | **both 404** — independently confirmed |
| Market lines, 13 games x 3 markets | ESPN's published DraftKings numbers, same event ids | read from the published feed, stamped 2026-11-14 | 39 opening + 39 current values captured; **tier T3, never official** |
| Published model numbers | `data/output/payload.json` | new module imports the existing model rather than re-deriving it | unchanged; the card reproduces the site's S1 line |

**What was *not* verified, and is flagged rather than filled in:** closing lines
(no game has kicked off), spread and total prices (not transcribed game by game),
player-prop prices, depth-chart strings, and injury-impact point values. See
`flags.html` F-18 to F-20 and the existing F-01 to F-17.

---

## 3. The findings that change what a decision-maker should do

### 3.1 No strategy is live, and the gate is working

Nine strategies, 105 out-of-sample games, walk-forward with no look-ahead. The
best (S1) improves point-spread MAE by **8.31%** over a league-constant
benchmark and is well calibrated (max gap 5.3% across five bands). Its
Bonferroni-adjusted bootstrap interval on that improvement is **[-0.21, +1.82]
points — it contains zero.** Under the published rule, that is a fail, so all
nine are on paper and no reward figure is published.

### 3.2 But the model does beat the benchmark, more often than not — and the gate cannot see it

The same 105 games, compared head to head:

| Measure | Value | Interpretation |
|---|---|---|
| Games where S1's spread was closer than the benchmark's | **68 of 105 (64.8%)** | a paired sign test, not a mean |
| Exact binomial p, two-sided | **0.0016** | would clear even the Bonferroni threshold of 0.00625 |
| Mean absolute-error improvement | **0.84 points**, CI [-0.21, +1.82] | contains zero |

Both are correct. They disagree because the bootstrap is on a **mean** that a
handful of blowouts dominate, while the sign test asks how often the model wins
the head-to-head. This is the single most decision-relevant fact this session
produced, and it is **published as an open question (S-15), not acted on** —
changing a gate after discovering a strategy would pass it is precisely the
behaviour a pre-registered gate exists to prevent.

**The decision for the owner:** whether the significance gate should be defined on
the **mean error difference** (current) or on the **paired win rate** (proposed),
with both published. This is a methodological choice, not a data question.

### 3.3 Signal and staking currently rank identically — because flat staking is a function of the hit rate

All nine strategies rank in the same order on signal and on flat-stake ROI. That
is not a validation of the split; it is a limitation of the current staking rule.
With a flat stake at a fixed price, bankroll growth is a monotone function of the
hit rate, which the signal score already uses. The split becomes load-bearing
only under variable stake sizing or selective bet selection. Both are published
as consequences, and the page says so rather than claiming the split has already
proved something.

### 3.4 The market moved a long way, and two favourites flipped

From the opening snapshot to the current one, same day:

| Game | Open (home) | Now (home) | Move | Note |
|---|---|---|---|---|
| NYJ at LAC | LAC -9.5 | LAC -1.5 | **+8.0** | the largest move on the card |
| BAL at CAR | BAL -4.5 | CAR -1.5 | **+3.0** | **favourite flipped** |
| ARI at KC | KC -11.5 | KC -14.0 | -2.5 | |
| MIA at BUF | BUF -11.5 | BUF -16.5 | -5.0 | |
| PIT at PHI | PHI -5.5 | PIT -4.5 | **+1.0 with a flip** | **favourite flipped** |
| NO at CHI | CHI -6.5 | CHI -9.5 | -3.0 | |

Two of thirteen games changed favourite. That is a direct argument for the store
this session built: a single undated snapshot would have recorded the current
line and given no way to know the market had moved eight points.

### 3.5 Our fair lines disagree most where the model is blindest

| Game | Fair margin | Market (home) | Difference |
|---|---|---|---|
| ARI at KC | +5.1 (KC by 5.1) | -14.0 (KC by 14) | **-8.9** |
| MIA at BUF | +6.9 | -16.5 | **-9.6** |
| IND at HOU | +4.1 | -10.0 | **-5.9** |
| TB at DET | -1.1 (DET by 1.1) | -3.5 | -2.4 |

The fair line here is **S1**, the highest-signal strategy. PR #21 publishes the
**S3** line on `lines.html`, and the two differ by up to 4.8 points on
MIA/BUF - which is the nine-strategy band doing its job, not a contradiction.
Both are published so the disagreement between strategies is visible.
The difference is signed as fair minus market, so a negative number means we rate
the home team **less** strongly than the market does. The pattern is consistent:
the market prices things this model does not see — availability, quarterback
context, rest and travel. That is why the disagreement is published as an
investigation queue and not as an edge.

### 3.6 Data drift is real and was caught by re-reading, not by assuming

Three practice statuses moved between the committed snapshot and this session's
read of the same page: Houston RB David Montgomery and CB Jaylin Smith are now
**full** participants (committed: limited), and Cleveland CB Denzel Ward is now
**limited** (committed: full). 401 of 404 fields were unchanged. Published as
**F-18** with both transcriptions linked; the committed file was **not**
overwritten, because doing so would silently change every availability count on
the site without a rebuild.

---

## 4. How to read the site now

| If you want to know… | Go to | What to trust |
|---|---|---|
| What the market said and says | `markets.html` | the stored numbers; the fair line is an estimate |
| Whether anything has hit | `results.html` | nothing is graded until the game is final |
| Whether a strategy has earned anything | `gates.html` | no. 0 of 9 live. |
| Why a strategy is on paper | `gates.html` | the reason column, one line per strategy |
| What depth a club has left | `gates.html` | the count, not a depth-chart label |
| How strong a correlation really is | `gates.html` | the n column, before the r |
| What is still unknown | `flags.html`, `questions.html` | all of it, listed |

---

## 5. The decisions that are now blocking progress

These are ordered by what they unblock, and each is a **choice**, not a research
task. Full detail on `questions.html` and `review.html`.

| # | Decision | Why it blocks | Cost of deciding late |
|---|---|---|---|
| Q-S1 | Who captures the closing snapshot, and at what clock time | CLV — the only economic measure that resists luck — cannot exist without it | every week without it is a week of CLV permanently lost |
| Q-S2 | Is a single -110 an acceptable proxy for the spread price? | CLV needs a price, not just points | a wrong proxy makes every CLV figure wrong in the flattering direction |
| Q-S3 | Is variable staking in scope? | the signal/staking split is collinear without it | the split stays decorative |
| Q-S4 | Define the significance gate on mean error or on paired win rate | **the best strategy passes one and fails the other** | the leaderboard cannot promote anything, ever |
| Q-S5 | May official game books be parsed for snap counts? | depth is counted, not priced, without them | injuries stay a count instead of a projection input |
| Q-S6 | Budget and licensing for a multi-provider odds feed | one book is not a market | single-provider market lines understate disagreement |
| Q-S7 | Reward pool, eligibility and legality | no figure can ship until this is set | the competition stays a shadow |

---

## 6. What this session deliberately did not do

- **Did not change any model parameter or published model number.** The new module
  imports the existing one.
- **Did not change any gate** after discovering that the paired win rate would
  pass. It is published as a question instead.
- **Did not overwrite the injury CSV** when three fields disagreed. The
  disagreement is the finding.
- **Did not invent a closing line, a spread price, a depth-chart string or an
  injury-impact value.** Each is blank and flagged.
- **Did not mark anything "won" or "live".** The strongest statement the evidence
  supports is "closer than the benchmark, 64.8% of the time".

---

## 7. Read this next

1. `markets.html` — the store, and the two sign conventions it keeps apart.
2. `gates.html` — signal vs staking, the demotion gate, replacement depth, and n.
3. `results.html` — why the feed is empty today and what it will contain on Monday.
4. `flags.html` — 20 entries, three of them new.
5. `review.html` — 18 proposals, and S-15, which is the one that matters most.

**Sources:** every value above links to the official NFL.com page it came from,
except the market numbers, which link to the published ESPN odds row and are
labelled tier T3 throughout. The full register is on `sources.html`; the
re-verification transcripts are in `research/verification/`.
