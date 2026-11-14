# Strategy validation and the leaderboard

Produced by `tools/build.py` over 105 out-of-sample games (Weeks 3-10 of the 2026 season). Underlying results: <https://www.nfl.com/schedules/2026/> and <https://www.nfl.com/standings/>.

## The seven gates

A strategy only earns reward points if it clears every gate. The gates are designed so that a strategy with a lucky record fails at least one of them.

| Gate | What it tests | Pass rule |
|---|---|---|
| G1 Data integrity | Point-in-time correctness | Every input is an official NFL.com page; each forecast uses only games played before it, with no look-ahead |
| G2 Out-of-sample | Honest evaluation | Walk-forward evaluation across the season, weeks 3-10; no random row splits |
| G3 Minimum sample | Enough evidence | At least 40 evaluated games |
| G4 Significance | Skill, not luck | The Bonferroni-adjusted bootstrap interval for the improvement over the benchmark excludes zero |
| G5 Stability | Consistency | The improvement is positive in at least 60% of evaluated weeks |
| G6 Calibration | Honesty of the probability | The largest gap between the model's stated probability and the observed rate is at most 0.12 |
| G7 Not the benchmark | A real competitor | The league-constant benchmark is excluded from rewards by definition |

## The leaderboard

| Rank | ID | Strategy | Spread MAE | Total MAE | Direction | Improvement | 95% CI | Weeks improved | Calib. gap | Gates | Eligible | Points |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | S1 | Simple mean, opponent-adjusted | 9.26 | 11.45 | 65.7% | 8.31% | -0.23 to 1.88 | 62% | 0.076 | 6/7 | no | 51.50 |
| 2 | S8 | Last 5 games window | 9.29 | 11.57 | 64.8% | 7.97% | -0.25 to 1.85 | 62% | 0.065 | 6/7 | no | 50.70 |
| 3 | S2 | Exponentially weighted | 9.39 | 11.22 | 62.9% | 7.03% | -0.53 to 1.88 | 62% | 0.074 | 6/7 | no | 45.30 |
| 4 | S5 | Median + shrinkage | 9.49 | 11.17 | 61.0% | 5.99% | -0.20 to 1.43 | 62% | 0.059 | 6/7 | no | 41.30 |
| 5 | S3 | EW + shrinkage | 9.77 | 11.03 | 57.1% | 3.31% | -0.44 to 1.06 | 62% | 0.065 | 6/7 | no | 27.40 |
| 6 | S4 | Fast EW + heavy shrinkage | 9.83 | 11.06 | 57.1% | 2.63% | -0.49 to 0.95 | 62% | 0.073 | 6/7 | no | 23.40 |
| 7 | S7 | Blend S3 and S6 | 9.91 | 11.03 | 55.2% | 1.84% | -0.59 to 0.91 | 62% | 0.076 | 6/7 | no | 19.10 |
| 8 | S6 | Slow EW + heavy shrinkage | 10.08 | 11.04 | 49.5% | 0.24% | -0.76 to 0.73 | 62% | 0.069 | 6/7 | no | 11.70 |
| 9 | S0 | League constant | 10.10 | 11.12 | 42.9% | baseline | 0.00 to 0.00 | 0% | 0.053 | 4/7 | no | 5.60 |

## The headline result

**No strategy is eligible.** The best strategy improves point-spread MAE over the league-constant benchmark by about eight percent, but the Bonferroni-adjusted bootstrap interval for that improvement still contains zero. In plain terms: the improvement is not yet distinguishable from the luck that a sample of this size produces on its own.

That is the correct finding, not a failure of the analysis. A leaderboard that ranked by point estimate would have crowned a winner the evidence does not support. The points column is therefore provisional for every row, and the eligible column is empty.

## Why the interval contains zero

Four reasons, and the first is the one that matters most:

1. **Ten weeks is a short sample.** One hundred and five evaluated games cannot separate an eight percent improvement from noise. The remedy is more games and more seasons - which means archiving point-in-time data going forward rather than reconstructing it.
2. **The benchmark is strong.** The league-constant benchmark scores a 42.9% direction accuracy, which is close to a coin flip with a small home-field tilt. Beating a weak baseline is easy; beating this one is not.
3. **The strategies are not independent.** Four of the nine are the same signal with different smoothing. Treating them as nine competitors inflates the apparent amount of evidence - see `correlation-and-luck.md`.
4. **The comparison is a paired test on a noisy quantity.** The bootstrap resamples games, not strategies, and the per-game spread error has a standard deviation of roughly ten points. An improvement of under one point per game cannot clear that noise with 105 samples.

## What each strategy does

**S1 - Simple mean, opponent-adjusted** (Team form). Unweighted mean points for/allowed per team, adjusted for the average quality of opponents already faced.
**S8 - Last 5 games window** (Team form). Unweighted mean over the five most recent games only, opponent-adjusted.
**S2 - Exponentially weighted** (Team form). Decay-weighted team scoring and allowing (lambda=0.65), opponent-adjusted, no shrinkage.
**S5 - Median + shrinkage** (Robust). Median scoring/allowing shrunk toward the league mean with k=4: robust to a single blowout loss.
**S3 - EW + shrinkage** (Regularised). Decay-weighted scoring/allowing (lambda=0.65) shrunk toward the league mean with k=4, opponent-adjusted.
**S4 - Fast EW + heavy shrinkage** (Regularised). Faster decay (lambda=0.80) with heavier shrinkage (k=6): trades responsiveness for stability.
**S7 - Blend S3 and S6** (Ensemble). Equal blend of the S3 (fast, moderate) and S6 (slow, heavy) regularised models.
**S6 - Slow EW + heavy shrinkage** (Regularised). Long memory (lambda=0.45) with heavy shrinkage (k=8): the most conservative team-form model.
**S0 - League constant** (Benchmark). League average home/away scoring measured before the game. Uses no team information; this is the benchmark every other strategy must beat.

## Gate-by-gate verdicts

| Strategy | Gates passed | Failing gates |
|---|---|---|
| S1 | 6/7 | G4 significance |
| S8 | 6/7 | G4 significance |
| S2 | 6/7 | G4 significance |
| S5 | 6/7 | G4 significance |
| S3 | 6/7 | G4 significance |
| S4 | 6/7 | G4 significance |
| S7 | 6/7 | G4 significance |
| S6 | 6/7 | G4 significance |
| S0 | 4/7 | G4 significance, G5 stability, G7 not the benchmark |

## Weekly stability

| Week | S1 | S8 | S2 | S5 | S3 | S4 | S7 | S6 | S0 |
|---|---|---|---|---|---|---|---|---|---|
| Week 3 | -0.69 | -0.69 | -1.79 | -0.74 | -1.06 | -0.95 | -1.11 | -1.16 | 0.00 |
| Week 4 | 1.50 | 1.50 | 1.47 | 0.68 | -0.01 | -0.24 | -0.31 | -0.64 | 0.00 |
| Week 5 | -0.10 | -0.10 | -1.02 | -0.29 | -0.32 | -0.22 | -0.32 | -0.37 | 0.00 |
| Week 6 | 0.81 | 0.81 | 0.73 | 1.80 | 1.05 | 0.99 | 1.00 | 0.94 | 0.00 |
| Week 7 | 0.17 | 0.21 | 0.07 | 0.10 | 0.33 | 0.37 | 0.32 | 0.31 | 0.00 |
| Week 8 | 1.53 | 1.39 | 2.44 | 0.75 | 1.32 | 1.11 | 1.14 | 0.96 | 0.00 |
| Week 9 | 2.84 | 2.70 | 3.38 | 2.24 | 1.25 | 1.02 | 0.80 | 0.36 | 0.00 |
| Week 10 | -1.18 | -1.04 | -1.04 | -1.68 | 0.36 | 0.38 | 0.56 | 0.76 | 0.00 |

Positive means the strategy beat the league-constant benchmark that week. A strategy that is positive in only a handful of weeks is describing one good run, not an edge.

## Calibration

| Strategy | Offset | Model probability | Observed rate | Games | Within tolerance |
|---|---|---|---|---|---|
| S1 | -6 pts | 62.6% | 61.8% | 89 | yes |
| S1 | -3 pts | 54.2% | 61.8% | 89 | yes |
| S1 | +0 pts | 45.6% | 49.4% | 89 | yes |
| S1 | +3 pts | 37.3% | 39.3% | 89 | yes |
| S1 | +6 pts | 29.4% | 34.8% | 89 | yes |
| S8 | -6 pts | 62.5% | 61.8% | 89 | yes |
| S8 | -3 pts | 54.1% | 60.7% | 89 | yes |
| S8 | +0 pts | 45.6% | 49.4% | 89 | yes |
| S8 | +3 pts | 37.3% | 42.7% | 89 | yes |
| S8 | +6 pts | 29.5% | 36.0% | 89 | yes |
| S2 | -6 pts | 61.9% | 65.2% | 89 | yes |
| S2 | -3 pts | 53.3% | 60.7% | 89 | yes |
| S2 | +0 pts | 44.6% | 48.3% | 89 | yes |
| S2 | +3 pts | 36.0% | 41.6% | 89 | yes |
| S2 | +6 pts | 28.2% | 33.7% | 89 | yes |
| S5 | -6 pts | 63.3% | 64.0% | 89 | yes |
| S5 | -3 pts | 54.8% | 60.7% | 89 | yes |
| S5 | +0 pts | 46.1% | 46.1% | 89 | yes |
| S5 | +3 pts | 37.5% | 39.3% | 89 | yes |
| S5 | +6 pts | 29.5% | 34.8% | 89 | yes |
| S3 | -6 pts | 62.8% | 64.0% | 89 | yes |
| S3 | -3 pts | 54.2% | 60.7% | 89 | yes |
| S3 | +0 pts | 45.4% | 51.7% | 89 | yes |
| S3 | +3 pts | 36.7% | 39.3% | 89 | yes |
| S3 | +6 pts | 28.8% | 34.8% | 89 | yes |
| S4 | -6 pts | 62.9% | 64.0% | 89 | yes |
| S4 | -3 pts | 54.3% | 60.7% | 89 | yes |
| S4 | +0 pts | 45.5% | 52.8% | 89 | yes |
| S4 | +3 pts | 37.0% | 39.3% | 89 | yes |
| S4 | +6 pts | 29.0% | 34.8% | 89 | yes |
| S7 | -6 pts | 62.8% | 64.0% | 89 | yes |
| S7 | -3 pts | 54.2% | 61.8% | 89 | yes |
| S7 | +0 pts | 45.4% | 50.6% | 89 | yes |
| S7 | +3 pts | 36.8% | 39.3% | 89 | yes |
| S7 | +6 pts | 28.9% | 34.8% | 89 | yes |
| S6 | -6 pts | 62.8% | 64.0% | 89 | yes |
| S6 | -3 pts | 54.2% | 60.7% | 89 | yes |
| S6 | +0 pts | 45.5% | 50.6% | 89 | yes |
| S6 | +3 pts | 37.0% | 40.4% | 89 | yes |
| S6 | +6 pts | 29.0% | 36.0% | 89 | yes |
| S0 | -6 pts | 63.5% | 62.9% | 89 | yes |
| S0 | -3 pts | 54.6% | 59.6% | 89 | yes |
| S0 | +0 pts | 45.5% | 48.3% | 89 | yes |
| S0 | +3 pts | 36.6% | 41.6% | 89 | yes |
| S0 | +6 pts | 28.4% | 33.7% | 89 | yes |

Every strategy passes calibration comfortably. That is worth stating plainly: the forecasts are not systematically overconfident, which means the failure to clear the significance gate is a sample-size problem and not a badly-calibrated model.

## Source links

- Official schedule and results: <https://www.nfl.com/schedules/2026/>
- Official standings: <https://www.nfl.com/standings/>

