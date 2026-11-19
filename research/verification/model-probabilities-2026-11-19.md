# Walk-forward origination and probability outputs — verification record

Session `arena/26eb97b1-x4`, 2026-11-19. Task T70 on the board. This record
states what was checked, against which source, and what was deliberately left
unchanged.

## The two defects this task addresses

1. **Look-ahead in the graded corpus.** `tools/origination.py` priced every
   event — including the already-played Week 9 and Week 10 fixtures it then
   graded — with the same ratings: `data/standings-wk10-2026.csv`, the
   standings *after* Week 10. The home edge was fitted on weeks 6–9, which
   contains the Week 9 games being graded. The published signal statistic was
   therefore measured on contaminated rows, and the pre-registration's gate G3
   ("out-of-sample") was evaluated by counting graded weeks rather than by
   looking for look-ahead, so it passed on contaminated rows.
2. **No probability for a side or a total.** The model emitted a margin and a
   total, so the two markets the brief asks about most — the side and the
   total — had no probability and therefore no proper score. This is the open
   board request E5 from `arena/cc97fdb0-x4` ("Side and total have no
   probability output").

## What the corrected model does

A line for a game in week **W** is now produced from:

* **ratings through week W−1**, computed from `data/games-2026.csv` — the
  official game log that `tools/verify.py` proves against the NFL.com
  standings;
* **a home edge fitted on weeks [W−5, W−2]**, the same official home margins.

Nothing dated at or after the event's own week can enter a line: the edge
window for week *W* ends at *W−2*, and the ratings stop at *W−1*.

The edge window [W−5, W−2] is the registered rule: for Week 11 it is weeks
6–9, exactly the weeks the pre-registration
(`research/preregistration/wk11-forward-v1.md`, commit
`8a3320092abe75aeafdbb0b1cdc586b37b93cbfb`) fitted the edge on. The two
pre-registered Week 11 lines are therefore **byte-identical** before and after
the change, and `tools/test_origination.py` now holds them as fixed values:

| Event | Fair side | Fair total | Fair moneyline (home) | Home edge | sigma |
|---|---|---|---|---|---|
| 401873066 IND at HOU (W11) | 5.2 | 48.2 | 64.87% | −0.39 | 13.6 |
| 401873070 MIA at BUF (W11) | 12.2 | 47.2 | 81.59% | −0.39 | 13.6 |

### Verification of the walk-forward inputs

* The ratings computed from the official game log through week 10 are asserted
  equal, team by team and field by field (games played, points for, points
  against, the shrunk strength and the shrunk total), to
  `data/standings-wk10-2026.csv`. The maximum absolute difference is 0.
  (`tools/origination.py`, `originate()`; test
  `test_ratings_from_the_log_match_the_official_standings`.)
* The edge window for every week is asserted to lie strictly before the
  event's week (`test_the_registered_edge_window_is_weeks_six_to_nine`,
  `test_no_prediction_uses_a_week_at_or_after_the_game`).
* The neutral-site set is unchanged: `data/international-2026.csv`, one row per
  2026 International Game, each with the official weekly schedule page that
  labels it. The home edge is set to zero on those fixtures, as before.

## The probability store

`data/ops/model_outputs.csv` — 30 rows, one per originated market (10 events ×
side, total, moneyline), in the mandated order. Each row records:

| Field group | Fields |
|---|---|
| the event | `event_id`, `week`, `away`, `home`, `market`, `selection`, `event` |
| the model's number | `model_line`, `mu` |
| the reference | `reference_line` (the market's captured opening line) |
| the probability | `probability`, `probability_pct` |
| the dispersion | `sigma`, `sigma_n`, `sigma_window`, `sigma_method` |
| the alternative | `probability_alt`, `probability_alt_pct`, `probability_gap_pts` |
| the market | `market_probability`, `market_probability_basis` |
| the inputs | `away_gp`, `home_gp`, `away_diff`, `home_diff`, `away_total`, `home_total`, `home_edge`, `edge_window`, `edge_n`, `ratings_through_week`, `prior_games`, `input_source` |
| the sources | `official_url` (the NFL.com game page for the fixture), `input_source`, `model`, `notes` |

The three probability definitions:

* **side** — P(the home team covers the captured opening spread) =
  Φ((fair margin + posted home handicap) / σ_margin). The posted home handicap
  is negative when the home team is favoured, so the term is the distance from
  the model's margin to the cover threshold.
* **total** — P(the game total goes over the captured opening total) =
  Φ((fair total − posted total) / σ_total).
* **moneyline** — P(the home team wins) = Φ(fair margin / σ_margin) with the
  **registered** σ, so the pre-registered Week 11 number does not move.

### Where the two dispersions come from

| Dispersion | Value | n | Window |
|---|---|---|---|
| σ_margin, model residual | 12.31 | 102 games | weeks 4–10 of the official game log |
| σ_margin, league | 13.52 | 150 games | weeks 1–10 of the official game log |
| σ_total, model residual | 13.40 | 102 games | weeks 4–10 of the official game log |
| σ_total, league | 14.18 | 150 games | weeks 1–10 of the official game log |

The model residual is the standard deviation of the walk-forward prediction
error: every game in weeks 4–10 is predicted from the information available
before its week, and the residual against the official final score is measured.
Nothing is assumed.

The brief asks for two estimators to stay visible with the gap until a
walk-forward comparison says which one wins, so both are published
(`data/ops/dispersion_comparison.csv`):

| Quantity | Candidate | sigma | 95% coverage of the outcomes | Brier of the win probability | Verdict |
|---|---|---|---|---|---|
| margin | model residual | 12.310 | 0.9608 | 0.2167 | closest to 95% coverage |
| margin | league | 13.516 | 0.9608 | 0.2175 | |
| total | model residual | 13.402 | 0.9510 | — | closest to 95% coverage |
| total | league | 14.182 | 0.9608 | — | |

The total is scored by interval coverage rather than by a Brier score, because a
probability taken at the model's own median is 0.5 for any dispersion and
cannot discriminate between them.

## Proper scores on the graded corpus

`data/ops/probability_scores.csv` — the model's probability and the market's
probability of **the same event**, scored on the 24 settled markets:

| Market | n | Model Brier | Market Brier | Skill | 95% game-cluster interval | Bonferroni p | State |
|---|---|---|---|---|---|---|---|
| side | 8 | 0.2095 | 0.2429 | +0.1378 | [−0.0956, +0.3602] | 0.3822 | fail (n < 30) |
| total | 8 | 0.1734 | — | — | — | — | no market benchmark (F-94) |
| moneyline | 8 | 0.2079 | 0.1973 | −0.0540 | [−0.5178, +0.2058] | 1.0000 | fail (n < 30) |

The benchmark for the moneyline is the de-vigged captured price. The benchmark
for the side is derived from that same price converted into a cover probability
at the posted spread, and is labelled as derived on every row. A posted total
carries no probability, so the total has a model Brier score and no market
forecast to be better than; none is invented (F-94).

**Which price the benchmark is.** Of the eight settled events in the graded
corpus, four carry `close_kind = close` (a true closing price) and four carry
`close_kind = current_as_close` — the last price captured before the event,
standing in for a close because the capture did not run after kickoff. The
label says so exactly rather than calling all eight a closing price:

> de-vigged captured price (a last-captured price used as the close in 4 of 8
> rows, not a true close)

and `data/ops/probability_scores.csv` carries the composition in its own
`benchmark_rows` column (`close: 4; current_as_close: 4`). This is flag F-96.
The skill numbers are unchanged, and they are not evidence of skill either way.

The interval is a game-cluster bootstrap: whole games are resampled, because a
game contributes a side, a total and a moneyline that are not independent
observations. The Bonferroni factor is 3, the number of market types scored.

## What the correction did to the published numbers

| Measure | Before (contaminated) | After (walk-forward) |
|---|---|---|
| settled markets graded | 24 | 24 |
| mean fair−market difference | −3.566 points | **−1.654 points** |
| p-value | 0.0918 | **0.2311** |
| gates passed | 2 of 8 | 2 of 8 |
| eligible | no | no |
| paper staking result | +2.082 units (+17.351% ROI) | **+6.751 units (+28.128% ROI)** |
| maximum drawdown | −2.198 units | **−4.359 units** |

The paper staking result improved while the signal statistic moved towards
zero. That is exactly the divergence the two-score split exists to expose, and
it is the reason neither number is allowed to rank a strategy on its own. The
strategy remains ineligible at 2 of 8 gates, and the forward window is
unaffected.

## The forward window

`tools/gen_escrow.py` now scores side, total and moneyline in Stage 1. The
forward ledger carries, for each of the six Week 11 markets, the model's
probability, the market probability where one exists, the event the probability
is about, the reference line and the scored outcome. With no Week 11 game
settled, every Stage 1 statistic is still reported as NOT EVALUABLE with the
number that would clear it — the registered G4 floor is n ≥ 30 settled forward
markets of that type and the count is 0.

## Sources used

| Source | Used for |
|---|---|
| `data/games-2026.csv` — official game log, each row linking its NFL.com game page | the walk-forward ratings, the home-edge windows, the residual dispersion, every settled outcome |
| `data/standings-wk10-2026.csv` — official NFL.com standings | the cross-check on the log-derived ratings |
| `data/international-2026.csv` — official International Game labels | the neutral-site set that zeroes the home edge |
| `data/schedule-wk11-2026.csv` — official Week 11 schedule | the official game URL for the forward fixtures |
| `data/ops/price_snapshots.csv` — captured prices (DraftKings, syndicated by ESPN; third-party, labelled T3) | the reference line and the market benchmark |

No NFL.com value was transcribed by hand in this task and no value was
inferred: every number above is computed by `tools/origination.py` from the
committed files.

## What is still open

* **F-94** — a total has no market benchmark, so it cannot enter a
  benchmark-relative ranking until over/under prices are captured separately.
* **F-95** — the registered home-edge estimator counts the three neutral-site
  games inside its window. The pre-registration fixes it for Week 11, so the
  change is a versioned model (v2) that has to be registered before a window
  opens.
* **F-96** — half of the graded market benchmarks are a last-captured price
  used as the close rather than a true closing price. The label is exact; what
  is missing is a capture that runs after kickoff.
* The forward window still has no pre-kickoff entry price and no real close
  (E2, E7), and the escrow holds nothing.
