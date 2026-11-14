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
| `site/` | The published multi-page site: fifteen generated pages plus twenty-two decision-desk pages, all statically rendered, plus the datasets and notes the pages cite |
| `docs/` | The X4 Console - a second, independent build of the same project, published at `/console/` |
| `console/` | A byte-identical mirror of `docs/`, so the repository root that GitHub Pages serves is the same site the workflow publishes |
| `COORDINATION.md` | The shared board for the parallel agent sessions working on this repository |

## The site, by category

The landing page carries a **directory** of every published page, grouped by the question
it answers, so nothing has to be guessed at.

| Category | Pages |
|---|---|
| Overview & decisions | `executive-summary.html` · `questions.html` (decision checklist) · `decisions.html` (30-question Q&A) · `requirements.html` (40-item inventory) |
| Verified data | `standings.html` (32 clubs, 137 games) · `data.html` (desk: 32 + 14 + 13 + 57 rows) · `availability.html` (345 injury rows) · `depth.html` (1,558 depth positions from 31 official club charts, joined to the injury report) · `injuries.html` (desk: 22 player rows + the deficiency pipeline) · `replacements.html` (desk: the replacement chains, side by side) · `markets.html` (the price-snapshot store) · `results.html` (the verified results feed) |
| Model & strategies | `lines.html` (13 Week-11 model lines, fair / market / difference as three columns) · `market.html` (the captured-price archive: 29 games, 87 price rows, skill and staking boards) · `price-snapshots.html` · `strategies.html` (leaderboard, 7 gates, correlation matrix) · `gates.html` (signal vs staking, the demotion gate) · `signals.html` (desk: 13 lines, 10 signals, 8 gates, 4 correlations) · `leaderboard.html` (singles / parlays / props) · `origination.html` + `price-store.html` + `signal-vs-staking.html` + `correlations.html` + `method-lab.html` (the origination layer) |
| Review & flags | `suggestions.html` (12 proposals) · `review.html` (desk: 18 proposals with Accept / Hold / Reject) · `workbench.html` (12 proposals on one documented rubric, ranked) · `programme.html` (the eight integrity gates) · `flags.html` (main register, 38 entries) · `flagged.html` (desk register, 12 blanks + 14 irregularities) · `ops-review.html` · `verification.html` · `requirements-closure.html` (ten of twelve requirements closed) |
| Method & sources | `methodology.html` · `sources.html` (the source register) · `repo-review.html` (line-by-line repository review) |
| Second build | The **X4 Console** at `/console/` - 15 pages, built independently, reaching the same two structural conclusions |

## The origination layer (T21)

A third layer asks the question the data layers cannot: *can this system originate a
number, beat the market to it, and prove it lost for the right reason?* It lives at
`/origination.html` and the seven pages beside it — `price-store.html`,
`signal-vs-staking.html`, `correlations.html`, `replacements.html`, `method-lab.html`,
`verification.html`, `requirements-closure.html` — and it is generated end to end from
cached bodies by `tools/origination.py`, `tools/depth.py` and `tools/ops.py`.

The honest result: **the machinery works and the evidence does not exist yet.** Ten ESPN
events are bound to official fixtures across weeks 9-11, producing 30 originated markets
(side -> total -> moneyline, in that fixed order), 12 of which are settled and graded.
Signal score: mean difference **-3.566 points**, p = **0.0918**, **2 of 8** gates passed,
**not eligible**. Staking score on the same markets: **+2.082 units**, **+17.351% ROI**,
max drawdown -2.198 units. A positive paper P&L sitting on a negative edge is exactly the
divergence the two-score split exists to expose, and in `signal-vs-staking.html` it is the
headline rather than a footnote.

| Artifact | What it holds |
|---|---|
| `data/ops/price_snapshots.csv` | 60 readings, open and close in separate fields, each with a UTC stamp and an https URL |
| `data/ops/fair_market_difference.csv` | 30 rows: fair, market, difference as three columns, never merged |
| `data/ops/event_identity.csv` | 10 event -> fixture bindings, each with the proof that the binding is unique |
| `data/ops/transactions.csv` | 67 official transaction rows, every one linked to its nfl.com page |
| `data/ops/depth.csv` | 17 replacement losses joined to their official additions; 6 read THIN, 2 UNRESOLVED - the *urgency* proxy, deliberately weaker than the transcribed charts above and labelled as such |
| `data/ops/gates.csv` / `demotion_rules.csv` | 8 gates and 6 demotion triggers, each evaluated rather than asserted |

`verification.html` recomputes ten structural claims from the artifacts and prints the
measurement, so the page can contradict itself; `requirements-closure.html` gives all
twelve requirements of this layer a verdict, and marks two **partial** and one **blocked**
rather than claiming them closed.

The depth requirement is answered twice, from two directions, and the stronger answer is
the other session's. [`tools/depth.py`](#roster-depth-which-starters-are-actually-missing)
transcribes each club's **own** published chart, which is a real depth rank - 1,558
positions across 31 clubs. `tools/depth_ledger.py` cannot quote a rank, so it measures a
different observable that every club emits: how fast a club had to replace a player it
lost to Reserve/Injured. A same-or-next-day signing means nobody was behind him; a week
with no signing means somebody was. That reads THIN / NORMAL / COVERED / UNRESOLVED and is
labelled a proxy wherever it appears. Both are on `replacements.html`, side by side, and
where a transcribed rank exists it is the fact to quote.

### Provenance note on three odds bodies

The odds payloads for events **401873052**, **401873066** and **401873070** were
transcribed into `data/ops/raw/` by hand from the retrieved pages rather than written
directly by `.retrieval/record.py`, because the retrieval helper was not in the loop for
those three fetches. Their `.stamp` files were written by hand with the same retrieval
timestamp, so the timestamp records when the page was read, **not** when the file was
created. The values themselves are verbatim from the payloads — the JSON parses, the
fields are the ones the other seven bodies use, and `verification.html` checks that each
reading carries an https URL and a stamp — but the file-writing path for these three is a
human transcription step, and this note is here so the difference is visible rather than
implied. The other seven bodies were written by `record.py`.

A related correctness fix belongs here too: the set of neutral-site games was previously
typed by hand as three pairs and **omitted week 10's Munich game (Patriots at Lions)**, so
a home-field edge was being applied to a game played in Germany. It is now read from
`data/international-2026.csv`, where all five 2026 International Games carry the official
weekly schedule page that labels them as such; `tools/compute_stats.py` asserts that the
neutral flags in the game log equal exactly that official set.

## The one rule everything follows

Every table row carries a direct link to the official NFL page it came from, and every
value that cannot be confirmed from an official source is left blank and flagged rather
than filled in. `site/check.py` enforces this: it executes the real renderer, inspects
the resulting markup, and fails the build if any rendered data row lacks an official
source link.

## Reproducing everything

```bash
python3 tools/verify.py     # prove the data against the official NFL.com standings
python3 tools/verify_live.py # re-check the committed data against a captured (or live) official NFL.com page
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

## The final integration pass (T31, session `arena/f7614083-x4`)

The two open branches - PR #22 (the eight integrity gates, the decision programme, the
suggestion workbench) and PR #26 (the captured-price archive, the market page, the
skill/staking boards) - were merged into one build, reconciled with each other and with
`main`, re-verified against the live official pages and published.

| What | Detail |
|---|---|
| Both branches merged | Neither branch's work was discarded: the flag registers are the union (38 entries, no duplicate id), both page generators are kept, and both gates run in `tools/validate.py` |
| One navigation | `tools/desk_nav.py` is the single source for the desk sidebar; four copies had already drifted apart twice, and the build now fails if any page disagrees |
| Every page reachable | The landing-page directory is rendered at write time and lists all 36 published pages; ten of them had been unreachable from it |
| No dead links in the published site | The artifact is `site/`, but the pages linked to `research/…`, `data/ops/…` and `COORDINATION.md`, which were not in it - 41 dead links. The cited datasets and notes are now published with the site, and every published page's links are checked |
| Two price stores reconciled | The site carried two independently captured price stores. `tools/reconcile_prices.py` compares them number by number: **112 of 112 comparable values match**. The one genuine difference - the two stores use the word *close* differently - is published as flag **F-38** |
| Re-verified live | The official standings (32 clubs, 256 field checks), the Week 11 schedule (13 games, 117 checks) and 27 rows of the official injury report were re-read on 2026-11-14 and match the committed data |
| One publish gate | The Pages workflow now runs `tools/validate.py` - the whole gate - instead of three hand-picked steps |

The full record, with every number and every irregularity found, is
`research/verification/integration-verification-2026-11-14.md`.

## The earlier integration pass

The session before this one (`arena/da12b830-x4`) closed the site out:

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
