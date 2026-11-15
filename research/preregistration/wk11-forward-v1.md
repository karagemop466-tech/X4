# Pre-registration: Week 11 forward window, v1 ratio model

Registered before any Week 11 game has kicked off. Week 11 official fixtures are
in `data/schedule-wk11-2026.csv` (13 games, 19 to 23 November 2026, sourced to
https://www.nfl.com/schedules/2026/by-week/week-11). No Week 11 result, closing
line or settlement exists at registration time.

## Strategy (unchanged model)

- Model: the v1 ratio model that `tools/origination.py` already runs. It is not
  re-fitted, re-weighted or tuned for this window.
- Origination order: side, then total, then moneyline. Fair line, market line and
  difference are kept as three separate columns and never blended.
- Bet rule (unchanged from the code): side picks the team whose fair line is
  better than the market line; total picks over or under on the same test;
  moneyline picks the side whose fair probability exceeds the market probability.

## Settlement rule (changed; fixed before any Week 11 settlement)

- Side bets settle **against the recorded line** (the team we picked must cover
  the spread), not on the straight-up winner. The straight-up settlement in
  `tools/origination.py` lines 575-578 is superseded for this window. The change
  is recorded in the Flagged for Review entries of the T34 extension.
- A cover of exactly zero is a push. A total equal to the line is a push.
- Moneyline settles on the straight-up winner; a tie is a push.
- Entry requires a recorded opening price and a recorded close. A missing close
  is recorded as missing, not filled.

## Sample window

- All 13 official Week 11 fixtures. The window is not extended after kickoff.

## Gates (taken from data/ops/gates.csv, unchanged)

G1 data integrity; G2 at least 100 settled bets per market type; G3 out-of-sample;
G4 Brier better than the market with n at least 30; G5 one-sided p below 0.05;
G6 Bonferroni-adjusted p below 0.05; G7 no week above 50 percent of skill; G8 a
further pre-registered segment with no regression.

## Demotion rules (taken from data/ops/demotion_rules.csv)

D1 skill evidence collapses: threshold is BLANK in the register. D2 Brier worse
than the market by more than 0.02 over 50 bets. D3 drawdown above 15 units at
stake 1. D4 any market graded without a source URL or UTC stamp (threshold 0).
D5 one week above 50 percent of skill. D6 fair-minus-market sign change over 50
bets: threshold is BLANK in the register.

Blank thresholds are not set in this document. A rule with a blank threshold
cannot trigger, so it is reported as NOT EVALUABLE, never as passed.

## Outcome statement

With 13 games the window cannot reach G2 (100 bets per type). It can only
produce a forward record that is reported with n and a cluster interval. No
ROI or win rate from this window ranks a strategy.
