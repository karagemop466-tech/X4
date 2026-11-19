# Published correlations and home-edge constants — re-verification

Session `arena/26eb97b1-x4`, 2026-11-19. Task T75 on the board.

Two flags were still open on the board: **F-62** ("the margin-vs-total
correlation is published with n = 57 on two pages while it is computed on
n = 54") and **F-63** ("one home-edge measurement is published at +0.1 and at
+0.07, and is measured on weeks 6-9 while 150 games exist"). Both were found
before the pages were rebuilt by later sessions, so this task re-reads every
published correlation row and every published home-edge constant line by line,
records the result, and adds a checker that keeps them true.

## What the checker does

`tools/check_published_stats.py` re-derives every published correlation and
every published home-edge constant from the committed official data and
compares the value, the interval **and the n** with what the page carries. It
runs inside the publication gate (`tools/validate.py`), so a stale or
mislabelled n fails the build instead of sitting on the page.

Its output is `research/verification/published-statistics-2026-11-19.csv`.

## Result: every published number holds

| Quantity | Value | 95% interval | n | Window | Published on |
|---|---|---|---|---|---|
| away score ↔ home score | +0.0486 | [−0.1125, +0.2073] | 150 | all completed games | `site/correlations.html` |
| home margin ↔ game total | −0.1405 | [−0.2941, +0.0202] | 150 | all completed games | `site/correlations.html` |
| net points ↔ win percentage | +0.8755 | [+0.7583, +0.9379] | 32 | 32 clubs | `site/correlations.html` |
| points for/g ↔ points allowed/g | −0.2911 | [−0.5808, +0.0641] | 32 | 32 clubs | `site/correlations.html` |
| away_vs_home_scores | +0.0182 | [−0.2435, +0.2775] | 57 | weeks 6-9 sample | `site/gates.html` |
| margin_vs_total | −0.3224 | [−0.5432, −0.0598] | 54 | weeks 6-9 sample, neutral-site games removed | `site/gates.html` |
| net_pts_vs_win_pct | +0.8717 | [+0.7514, +0.9359] | 32 | 32 clubs | `site/gates.html` |
| pts_per_game_vs_pts_allowed_per_game | −0.2041 | [−0.5161, +0.1557] | 32 | 32 clubs | `site/gates.html` |
| home-field edge, official corpus | −0.53 | [−2.72, +1.65] | 146 of 150 | weeks 1-10, neutral-site games excluded | `site/executive-summary.html` |
| home-field edge, weeks 6-9 | +0.07 | [−3.59, +3.74] | 54 | weeks 6-9, neutral-site games excluded | `site/executive-summary.html` |

### F-62

The defect was real when it was found: `research/computed_stats.json` records
the margin-vs-total correlation on **n = 54** (the weeks 6-9 sample with the
three neutral-site games removed) while the executive-summary row and the
correlations page attached **57** — the size of the input file — to the same
*r*.

That substitution is gone from the site. The desk correlations page publishes
the margin-vs-total correlation as **r = −0.141 on n = 150**, computed from the
official game log; the legacy rows publish **−0.3224 on n = 54**, and the
programme page labels that row `Margin vs game total (neutral-site removed,
n=54)`. Every published correlation now carries the n it was computed on:
n = 150 for the two cross-game coefficients, n = 32 for the two cross-club
coefficients.

One thing a reader should still see: the same quantity is published on two
windows — n = 150 on the full log and n = 54 on the weeks 6-9 sample. Each row
carries its own window and n, and the difference between the two is the point
of printing both.

### F-63

The defect also had two parts.

1. *Two roundings of one number.* The executive summary published +0.1 and the
   line-lab model text published +0.07, with no window and no n beside either.
   There is no second rounding left on the site.
2. *The window.* The constant is fitted on weeks 6-9 (n = 54). Re-deriving it on
   the full verified corpus — 146 of 150 games, the four international fixtures
   excluded per the official schedule — gives **−0.5 points**, the opposite
   sign to the +0.07 the line lab adds to every Week 11 spread.

Both are now published together, on the desk executive summary: the corpus
measurement (−0.5 points, 95% CI [−2.7, +1.6], n = 146 of 150, with the four
excluded fixtures named), the statement that the interval contains zero so no
home edge is assumed, and the weeks 6-9 measurement (+0.07, n = 54, window
named). The strategy lab names the window its own home-edge strategy is fitted
on (`Game results Wks 6–9`).

What remains is a model caveat rather than a publication defect: a constant
that changes sign with its window is a window-dependent number, and the pages
now say which window produced the one they use. The origination layer carries
the same caveat in **F-95**, where the three neutral-site games inside the
registered edge window are named.

## Sources used

| Source | Used for |
|---|---|
| `data/games-2026.csv` | the two cross-game correlations and the corpus home edge |
| `data/standings-wk10-2026.csv` | the two cross-club correlations |
| `research/data/games_weeks6-9_2026.csv` | the weeks 6-9 correlations and home edge |
| `research/data/standings_2026_through_week10_tnf.csv` | the weeks 6-9 cross-club correlations |
| `data/international-2026.csv` | the neutral-site games excluded from the home edge |

Nothing was transcribed by hand and nothing was fetched: every input is a
committed file and every published page is the one this repository builds.

## How to reproduce

```bash
python3 tools/check_published_stats.py   # exit 0 = every published number holds
```
