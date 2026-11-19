# E5: model probability outputs for side and total (T71)

Session: `arena/9c4553d7-x4`, 2026-11-19 UTC. Board: `COORDINATION.md` row T71.
Closes the open request "flags E5" (addressed to the origination owner) on the escrow
register at `escrow.html#flags`. Escrow register rows changed: **E5** flipped to
RESOLVED, **E8** added (settlement defect found and corrected in the same scope).

## Question

The brief says: *"Store every model output as a probability plus its inputs, not just a
pick"* and *"Rank with proper scores and uncertainty"*. The origination model emitted a
margin (side) and a total (total), so a proper score existed only for the moneyline and
gate G4 ("Brier score better than the market's Brier score") printed
`not computed: needs a per-market probability with n>=30`. This task stores every output
as a probability plus its inputs and evaluates G4 from real Brier scores.

## Specification (fixed before the numbers were computed)

Each market type has one fixed binary event, named per row, priced at each captured
number. The events never depend on the model's pick, so a proper score is well defined:

| Market | Event | Distribution | Formula | Inputs (stored per row) |
|---|---|---|---|---|
| side | `home_covers` | `normal_margin` | `P(margin > -line) = Phi((mu + line) / sigma)` | `prob_mu` = fair home margin, `prob_sigma` = measured margin sd (weeks 6–9 2026 official log) |
| total | `over_line` | `poisson_total` | `P(total > line)` under `Poisson(mu)` | `prob_mu` = fair total |
| moneyline | `home_wins` | `normal_margin` | `P(margin > 0) = Phi(mu / sigma)` | same as side |

Stored in `data/ops/fair_market_difference.csv` (columns `prob_dist`, `prob_mu`,
`prob_sigma`, `prob_event`, `prob_event_open_pct`, `prob_event_close_pct`) and, in
probability form, in `data/ops/fair_lines.csv` (`fair_ml_home_pct` is the side/moneyline
probability output; `p_over_fair_pct` is the total output at its own fair number;
`prob_inputs` prints the parameters). The model card records the spec under
`probability_outputs`. No number is transcribed or inferred: every input comes from the
committed official game log (`data/games-2026.csv`, rows carry their nfl.com game page)
and the already-captured price store (`data/ops/price_snapshots.csv`, DraftKings via the
ESPN odds endpoint, labelled third-party/T3 under the price-data policy).

Brier scores (`data/ops/scores_brier.csv`) compare the model probability of the event at
the **close** number against the de-vigged captured price of the same event, on settled
non-push rows only. A row missing either probability is excluded, never filled.

## Verification performed

1. **13 regression tests pass** (`python3 tools/test_origination.py`): 3 pre-existing
   settlement tests unchanged, 10 new — the side probability is exactly 0.5 at the fair
   line, monotone in the line; the total probability sits near 0.5 at its fair number and
   falls as the line rises; the moneyline probability is 0.5 at zero margin; missing
   inputs return `None` (never a guess); `devig_pair("-110","-110") = 0.5`; a full fmd row
   round-trips its probability columns and raw result; a synthetic model edge scores
   positive Brier skill; rows without a probability are excluded.
2. **Every settled row re-derived against the official game log**: a script joined all 24
   settled rows of `data/ops/fair_market_difference.csv` to `data/games-2026.csv` by
   (week, away, home) and checked `result_margin` = home pts − away pts, `result_total` =
   home pts + away pts, and each `result` cell against the row's own market rule.
   **24 rows checked, 0 mismatches.**
3. **Spot check of the probability math** (row 401873037, JAX at BAL, week 9): fair home
   margin −13.6, sigma 13.6. Home −4.5 open → `Phi((-13.6 + -4.5) / 13.6)` = 9.16%
   (published cell 9.16). Home +9.5 close → `Phi((-13.6 + 9.5) / 13.6)` = 38.15%
   (published cell 38.15). Total fair 46.3: `P(X > 49.5)` under Poisson(46.3) = 31.23%
   and `P(X > 40.5)` = 80.12% (published cells 31.23 / 80.12).
4. **Moneyline probability equals its own fair column verbatim** (the rounded mu/sigma
   re-derivation drifts by ~0.03pp; the stored probability is the fair value so the two
   columns can never disagree — checked on all 10 moneyline rows).
5. **Escrow self-tests** (`python3 tools/test_escrow.py`): all pre-existing checks pass,
   including the two stage-1 NOT EVALUABLE checks and the synthetic Brier-skill check.
6. **Pipeline**: `python3 tools/validate.py` (full gate) — result recorded on the PR.
   `tools/origination.py` is deterministic: a second run leaves every byte unchanged.

## G4 after the change (`data/ops/gates.csv`)

`side n=8 model 0.1656 vs market 0.2480 (skill +0.3322); total n=8 model 0.1148 vs market
0.2514 (skill +0.5435); moneyline n=8 model 0.1728 vs market 0.1973 (skill +0.1241) |
pooled n=24` — **fail**, correctly: the registered rule needs n >= 30 per market type.
The gate now reports the numbers it used instead of "not computed". These are backtest
grades on the weeks 9–10 corpus and are not reward evidence; the forward board remains
n = 0 until Week 11 settles.

## Irregularity found and corrected in scope (escrow register E8)

- The forward ledger (`tools/gen_escrow.py` `settle_forward`) settled **side** picks
  against the straight-up `result` column instead of the entry line, and the total-row
  `result` column compared the game total against **0**, so every played game read
  "over". Corrected: side and total settle against the entry line from the raw official
  result (`result_margin` / `result_total`, new columns on every settled fmd row), and
  the total `result` column resolves against the captured line. Verified cell by cell
  against the official game log (see check 2 — the same script covers the corrected
  cells). Legacy/synthetic rows without raw results keep the old path.

## What this does not do

- It does not make G4 pass. n = 8 per market type on the backtest corpus; the registered
  threshold is 30.
- It does not add a probability to `markets.csv` (the market registry) — the registry
  keeps the mandated side → total → moneyline order and one row per market; the
  probabilities live on the fair/market/difference rows and the fair-lines rows.
- It does not touch the captured prices, the settlement of graded bets, or any official
  dataset; `data/ops/graded.csv`, `scores_signal.csv` and `scores_staking.csv` are
  byte-identical after the change (checked with `git diff`).
