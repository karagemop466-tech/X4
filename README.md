# Fourth Down — NFL Decision Desk

Official-source NFL decision support: verified data, model lines, a strategy leaderboard
that refuses to reward luck, injury and depth tracking, and a reviewable path from
questions to suggestions.

**Live site:** https://karagemop466-tech.github.io/X4/

## What is in the repository

| Path | What it holds |
|---|---|
| `data/` | The verified source data: 137 official games, the official standings for all 32 teams, the official Week 10 injury report, the official Week 11 schedule, and league-confirmed starter changes |
| `data/output/` | Machine-readable copies of every number the site publishes (`payload.json`, `payload.js` and one file per table), regenerated on each build |
| `research/` | The written findings: model lines, correlations and luck control, strategy validation, injuries and depth, depth-chart acquisition, data verification, and the sources register |
| `tools/` | The pipeline: `verify.py` proves the data, `build.py` produces every published number, `pages.py` and `sync.py` build the site, `validate.py` runs the whole gate |
| `site/` | The published multi-page site: nine generated pages plus eleven decision-desk pages, all statically rendered |
| `docs/` | The X4 Console - a second, independent build of the same project, published at `/console/` |
| `console/` | A byte-identical mirror of `docs/`, so the repository root that GitHub Pages serves is the same site the workflow publishes |
| `COORDINATION.md` | The shared board for the parallel agent sessions working on this repository |

## The site, by category

The landing page carries a **directory** of every published page, grouped by the question
it answers, so nothing has to be guessed at.

| Category | Pages |
|---|---|
| Overview & decisions | `executive-summary.html` · `questions.html` (decision checklist) · `decisions.html` (30-question Q&A) · `requirements.html` (40-item inventory) |
| Verified data | `standings.html` (32 clubs, 137 games) · `data.html` (desk: 32 + 14 + 13 + 57 rows) · `availability.html` (345 injury rows) · `depth.html` (1,558 depth positions from 31 official club charts, joined to the injury report) · `injuries.html` (desk: 22 player rows + the deficiency pipeline) |
| Model & strategies | `lines.html` (13 Week-11 model lines) · `strategies.html` (leaderboard, 7 gates, correlation matrix) · `signals.html` (desk: 13 lines, 10 signals, 8 gates, 4 correlations) · `leaderboard.html` (singles / parlays / props) |
| Review & flags | `suggestions.html` (12 proposals) · `review.html` (desk: 18 proposals with Accept / Hold / Reject) · `flags.html` (main register) · `flagged.html` (desk register) |
| Method & sources | `methodology.html` · `sources.html` (the source register) · `repo-review.html` (line-by-line repository review) |
| Second build | The **X4 Console** at `/console/` - 15 pages, built independently, reaching the same two structural conclusions |

## The one rule everything follows

Every table row carries a direct link to the official NFL page it came from, and every
value that cannot be confirmed from an official source is left blank and flagged rather
than filled in. `site/check.py` enforces this: it executes the real renderer, inspects
the resulting markup, and fails the build if any rendered data row lacks an official
source link.

## Reproducing everything

```bash
python3 tools/verify.py     # prove the data against the official NFL.com standings
python3 tools/build.py      # regenerate every published number into data/output/
python3 tools/pages.py      # regenerate the site pages
python3 tools/sync.py       # keep the root copies in step with site/ and docs/
python3 site/check.py       # check the rendered site for broken links and unsourced rows
python3 tools/check_site.py # check the decision-desk pages the same way
node docs/check.js          # check the X4 Console
python3 tools/validate.py   # all of the above, plus determinism and repository hygiene
```

Python 3 standard library only for the pipeline. Node is used by `tools/render.js` to
execute the browser renderer during the site check; the published site itself needs no
build step and no server.

## The findings in one paragraph

The game log was reconstructed and then **proved** against the official NFL.com standings:
all 32 teams match on wins, losses, ties, points for, points allowed and net points,
which also proves every individual score. Nine strategies were then scored on 105
out-of-sample games under a walk-forward protocol with no look-ahead. The best strategy
beats a league-constant benchmark by about eight percent on point-spread error, and it is
well calibrated - but its Bonferroni-adjusted bootstrap interval still contains zero, so
**no strategy passes every validation gate and none is eligible for reward**. The
correlation matrix shows that four of the nine strategies (S3, S4, S6 and S7, minimum
pairwise prediction correlation 0.94) are effectively one signal, so they cannot be
counted as four independent pieces of evidence. Model lines for all 13 official
Week 11 games are published as a range across strategies.

**Real prices now exist, and they do not flatter the model.** The NFL publishes no betting
lines, so no price here is official, but one licensed book's prices (DraftKings, published
by ESPN) were captured and archived verbatim for 29 games - spread, total and moneyline,
opening and closing, 174 rows, each linked to its NFL.com result and its price resource.
On the 16 graded games **every strategy's spread error is worse than simply taking the
closing line's implied margin** (best 9.32 points against the line's 8.47), every
strategy's fair numbers are **compressed toward zero** relative to the board (10%-72% of
market width), and the numeric demotion gate therefore keeps all nine on paper. Nine
independent checks re-derive every published market number from the source CSVs in
`tools/market_check.py`; it caught four sign and axis errors during development.

## Roster depth: which starters are actually missing

`depth.html` answers the depth question from an official source. The league publishes no
consolidated depth chart and `nfl.com/teams/<club>/depth-chart` 404s, but **each club publishes
its own chart on its own official website as a table whose column position is the depth
position**. 31 of the 32 clubs publish a machine-readable ordered chart; all 1,558 positions are
transcribed with a link to the page each came from, and joined by name to the official NFL.com
Week 10 injury report.

| Measure | Week 10 |
|---|---|
| Out/Doubtful players who sit on their club's chart | 57 of 76 |
| ... at **depth 1** (the listed starter) | **40** (23 offense, 17 defense) |
| Clubs with at least one listed starter out | 19 |
| Positions where the club names nobody behind a ruled-out starter | 2 (both Tennessee) |
| Cascades - starter *and* his listed backup both out | **0** |

The zero is published deliberately. Any model that assumes a second- or third-string cascade is
happening in Week 10 would be inventing it. Houston publishes its chart only as an image, so it
contributes no rows (F-18); 19 ruled-out players who are absent from their own club's chart are
listed by name rather than given a guessed rank (F-19), which makes the starter-out figure a
floor. A published chart is not proof of who started - that is F-21, and ingesting the official
game books is the fix ranked first in the suggestions queue.

## What is deliberately missing, and why

Market lines, depth-chart strings, player-level statistics and player-prop performance are
not published, because no official source for them was confirmed. Each is recorded on the
site's *Flagged for review* page and in `research/data-verification.md`. The suggestions
page ranks the work that would close those gaps, with the decision each one needs.

## Coordination

This repository is worked on by several agent sessions in parallel. `COORDINATION.md`
records who owns which files, what has been claimed, what has been merged, and the
verification and deployment history.

## The final integration pass

The last session (`arena/da12b830-x4`) closed the site out:

- **One map of the site.** The landing page now carries a directory of every published
  page grouped by category, and the top navigation links to it from every page. This
  closes the nav-reciprocity request left open by an earlier session.
- **The two open pull requests were integrated** (#10, the publish race; #11, the console's
  stale fallback counts). Neither branch could be merged — both had diverged from `main`
  and Git refused to merge them as unrelated histories — so their content was taken
  forward and re-verified instead, and the defects found in them were corrected and
  published on the *Flagged for review* page (F-13 to F-16, R-09 to R-12).
- **The publish path was made deterministic.** `tools/sync.py` now mirrors `docs/` into
  `console/` as well as `site/` into the root, so the legacy Pages build (which serves
  the repository root) and the custom workflow (which uploads `site/`) publish the same
  bytes. The publish workflow checks the mirror before it uploads.
- **The combined data was re-verified line by line** against NFL.com: the standings for
  all 32 clubs, the Week 10 injury report, the Week 11 schedule, the game log, and every
  correlation and confidence interval on the decision-desk layer, recomputed
  independently from the committed CSVs.
- **Two stale counts were corrected** in the desk executive summary (the injury sample is
  22 published rows, not 19; the irregularity register holds 12 entries, not 8).

## Sources

Official NFL.com pages only for published values: the league standings, the weekly injury
report, the weekly schedules, the team and player pages, and NFL.com news for starter
changes. Full register with URLs and retrieval dates in `research/sources-register.md`.

## Not advice

This is a research and decision-support project. It publishes no picks, accepts no bets,
pays no prizes and is not betting advice. Model figures are estimates derived from
official results and are labelled as such throughout.

## X4 Console (`docs/`) — a second, independent build

A parallel session (`arena/528008d6-x4`) produced a second, self-contained console under
`docs/` at the same time as the build described above. It is published alongside this one
at **`/console/`** on the same Pages site.

| | Main site (`site/`) | X4 Console (`docs/`) |
|---|---|---|
| Built by | `arena/25459fae-x4`, `arena/70ac0cf1-x4`, `arena/59059060-x4`, `5c48ced7`, `arena/da12b830-x4` | `arena/528008d6-x4` |
| Pages | 20 (9 generated + 11 decision-desk pages) | 15 (incl. 404) |
| Pipeline | Python generator (`tools/`) → static output | No generator; hand-written static files |
| Publication gate | `python3 site/check.py` + `python3 tools/check_site.py` | `node docs/check.js` |

Both builds follow the same one rule — every table row links to the official source it
came from, and anything unconfirmable is left blank and flagged — and both reached the
same two structural conclusions independently:

1. **The NFL publishes no betting lines.** (`site/`: no price is described as official -
   the model-line column stays a model estimate and captured prices are labelled
   "DraftKings via ESPN, non-official". `docs/`: flagged as **F-02**.)
2. **No official source labels depth-chart strings.** `nfl.com/teams/<club>/depth-chart`
   returns HTTP 404; club sites publish ordered charts without 1st/2nd/3rd/4th labels.
   (`docs/`: flagged as **F-03**.)

They also independently caught the same source conflict: two official NFL.com items give
different absence windows for the same player (6-9 weeks vs 6-10 weeks) — **F-04** on the
`site/` board, **F-06** on the `docs/` board.

Reproducing the console's checks:

```bash
node docs/check.js     # 15 pages, 22 tables, 682 rows, 142 internal links, 27 external
```

The reconciliation of the two builds — including the merge conflict on `COORDINATION.md`
and `README.md`, and the file-scope statement — is logged in the
*Appendix — session `arena/528008d6-x4`* at the bottom of `COORDINATION.md`.

## The market page (session `arena/1b8b6e9e-x4`, T30)

`market.html` is the only page on the site where a number is a **real bettable price**.
It exists because an earlier snapshot store described model output as an opening line: its
`source_url` was an NFL.com game page, which cannot contain a price, and its own note read
"Model estimate ... not an official betting line". A store built from a model's own output
cannot measure line movement, closing-line value or ROI, because there is no market in it.
This page keeps the two apart:

| On the page | What it is | How each row is sourced |
|---|---|---|
| Origination table | Desk fair number, market number, difference - three separate columns, side then total then moneyline | NFL.com game page + the ESPN odds resource |
| Snapshot table | 87 captured rows: open and close for spread, total and moneyline | NFL.com game page + the ESPN odds resource |
| Results feed | 29 games, 16 final, official scores | that game's NFL.com page |
| Skill board | out-of-sample error only; no stake is an input, so no staking run can lift a rank | NFL.com results |
| Staking board | flat 1-unit and 25% Kelly ledger, ranked separately | NFL.com results |
| Depth | how often the opening number was still the closing number | NFL.com results |
| Correlations | r with **n** and a 95% CI on every value | NFL.com results |
| Demotion gate | four numeric rules, default paper | NFL.com results |
| Anchoring diagnostic | how far the desk's number sits from the board | NFL.com results |

Two honest results are published on it rather than buried: **no strategy beats the closing
line on spread error** over the graded sample, and every strategy's fair spread is
**compressed** to 10%-72% of market width, which is why a pick's win rate is never used here
as evidence of skill. `tools/market_check.py` re-derives all 432 graded bets, the 13
originated games and all 29 anchors from the source CSVs without importing the module under
test.

## Decision-desk pages (session `5c48ced7`, PR #12)

An additional layer of ten category pages sits alongside the main site. Each exists
**byte-identically at the repository root and in `site/`**, so every publishing path
(legacy root build and the `site/` artifact) carries them, and `tools/sync.py` keeps
them mirrored. No existing `site/` file was modified.

| Page | What it adds |
|---|---|
| `executive-summary.html` | Decision-maker summary: verified state, top decisions, findings, blanks |
| `requirements.html` | All 40 brief requirements mapped to deliverables, status and verification |
| `data.html` | Standings (32), Week 10 slate, Week 11 schedule **with the market snapshot**, 57 results - every row linked |
| `signals.html` | 13 originated baseline lines vs market, 10 candidate signals, 8 validation gates, **4 correlation values with 95% CIs**, skill-vs-luck protocol |
| `leaderboard.html` | Singles/parlays/props divisions, scoring formula, anti-gaming rules, reward phases (amounts blank + flagged) |
| `injuries.html` | 21 official player-linked injury rows + the starter-to-2nd/3rd/4th-string deficiency specification (offense and defense) |
| `decisions.html` | 30-question decision Q&A: known / missing / how to obtain / decision blocked |
| `review.html` | 18 proposals with Accept/Hold/Reject selection (saved locally) - review before any build |
| `flagged.html` | Desk flags F-01..F-12 and irregularities R-01..R-08 with evidence links |
| `repo-review.html` | Line-by-line file review of the repository |
| `sources.html` | Full source register with tiers and retrieval dates |

Desk-specific tooling (separate from the pipeline above):

```bash
python3 tools/check_site.py     # desk pages: links, anchors, nav, https source per data row
python3 tools/compute_stats.py  # recompute correlations / home edge / baseline lines from research/data/*.csv
python3 tools/gen_data_html.py  # regenerate data.html from the CSVs (CI enforces byte-identical output)
```

**What the desk layer contributes to the open gaps:** a dated **market snapshot**
(all 13 Week-11 spreads and totals, DraftKings as published by ESPN, 2026-11-14,
labelled T3 - not official NFL lines), four **computed correlation values** with
confidence intervals (including margin-vs-total r = -0.32, the parlay-relevant one),
and a **measured home edge** whose confidence interval spans zero. These are separate
inputs (`research/data/*.csv`) and never fork the numbers produced by `tools/build.py`;
`data/**` was not touched.
