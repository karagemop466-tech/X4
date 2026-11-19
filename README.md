# Fourth Down — NFL Decision Desk

Official-source NFL decision support: verified data, model lines, a strategy leaderboard
that refuses to reward luck, injury and depth tracking, and a reviewable path from
questions to suggestions.

**Live site:** https://karagemop466-tech.github.io/X4/

## What is in the repository

| Path | What it holds |
|---|---|
| `data/` | The verified source data: 150 official games through Week 10, standings for all 32 teams, the schema-valid Week 10 injury dataset, the Week 11 schedule, official depth charts and transaction evidence. A later Week 11 injury capture is only partial (12 of 13 scheduled games) and is not treated as a complete player dataset; see [Flagged for Review](https://karagemop466-tech.github.io/X4/flags.html) (F-89) and the [official injury report](https://www.nfl.com/injuries/). |
| `research/data/injury-report-delta-wk10.csv` | The first published **what-changed delta**: every cell that moved between the 2026-11-14 and 2026-11-15 official captures of the same Week 10 report (2 players added, 32 cells changed on 16 players) |
| `data/output/` | Machine-readable copies of every number the site publishes (`payload.json`, `payload.js` and one file per table), regenerated on each build |
| `research/` | The written findings: model lines, correlations and luck control, strategy validation, injuries and depth, depth-chart acquisition, data verification, and the sources register |
| `tools/` | The pipeline: `verify.py` proves the data, `build.py` produces every published number, `pages.py` and `sync.py` build the site, `validate.py` runs the whole gate |
| `site/` | The published, statically rendered decision dashboard and its category pages, datasets and verification notes |
| `docs/` | The X4 Console - a second, independent build of the same project, published at `/console/` |
| `console/` | A byte-identical mirror of `docs/`, so the repository root that GitHub Pages serves is the same site the workflow publishes |
| `COORDINATION.md` | The shared board for the parallel agent sessions working on this repository |

## The site, by category

The landing page carries a **directory** of every published page, grouped by the question
it answers, so nothing has to be guessed at.

| Category | Pages |
|---|---|
| Overview & decisions | `executive-summary.html` · `questions.html` (decision checklist) · `decisions.html` (30-question Q&A) · `requirements.html` (40-item inventory) |
| Verified data | `standings.html` (32 clubs, 150 games) · `data.html` (desk: 32 + 14 + 13 + 57 rows) · `availability.html` (347 injury rows) · `depth.html` (1,558 depth positions from 31 official club charts, joined to the injury report) · `houston-depth.html` (Houston: no structured chart, so starter/playing-time depth derived from the official Game Book; F-24) · `injuries.html` (desk: 22 player rows + the deficiency pipeline) · `replacements.html` (desk: the replacement chains, side by side) · `markets.html` (the price-snapshot store) · `results.html` (the verified results feed) |

| Model & strategies | `lines.html` (13 Week-11 model lines, fair / market / difference as three columns) · `market.html` (the captured-price archive: 29 games, 87 price rows, skill and staking boards) · `price-snapshots.html` · `strategies.html` (leaderboard, 7 gates, correlation matrix) · `gates.html` (signal vs staking, the demotion gate) · `signals.html` (desk: 13 lines, 10 signals, 8 gates, 4 correlations) · `leaderboard.html` (singles / parlays / props) · `origination.html` + `price-store.html` + `signal-vs-staking.html` + `correlations.html` + `method-lab.html` (the origination layer) |
| Personnel ablation | `personnel-ablation.html` (T48: injury and personnel ablations instead of fixed penalties — the measured points-per-designation contrast on the official Week 10 report with n and 95% intervals, the empty control group that blocks the feature, and the identifiability gate) · `open-questions.html` (T48: the eight open questions, each with what is known, the gate that blocks it, and the number that would clear it, all computed at build time) |
| Review & flags | `suggestions.html` · `review.html` (Accept / Hold / Reject) · `workbench.html` (ranked proposals) · `programme.html` (integrity gates) · `flags.html` (current register generated from `data/output/flags.json`) · `flagged.html` (desk blanks and irregularities) · `ops-review.html` · `verification.html` · `requirements-closure.html` · `delta.html` (dated injury-report differences) |
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
The current committed run has **24 settled markets**. The signal score is a mean fair-minus-market difference of **-2.415 points** (p = **0.1028**); only **2 of 8** origination gates pass, so it is **not eligible**. Staking on the same record shows **+15.414 units** and **+64.224% ROI** in this small sample. That divergence is the point of the separate signal and staking panels: realized return is not evidence of a profitable signal, and it cannot qualify a strategy. These are repository-derived paper results, not a recommendation or a live betting record; see `signal-vs-staking.html` and `requirements-closure.html`.

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

## Provenance and the known source-link gap

A verified NFL fact should link directly to the official NFL page that supports it; a
value that cannot be confirmed stays blank and is flagged. The latest audit (`research/audits/official-row-source-coverage-current-2026-11-19.md`) classified **1,138 rows across 29 desk pages**: 725 had allowlisted official-domain links only, 90 had both official and non-official links, 323 had non-official HTTPS links only, and none had no HTTPS link. This is a hostname inventory, not evidence that a link supports the value beside it. **F-39 remains an irregularity** for source-to-field verification; the zero-link-presence result must not be described as full verification. In particular, market prices come from ESPN's odds endpoint, not an official NFL betting line. See the [official-source audit](research/audits/official-row-source-coverage-current-2026-11-19.md) and the public [Flagged for Review register](https://karagemop466-tech.github.io/X4/flags.html).

The main-site `site/check.py` checks rendered data tables, and `tools/check_site.py` checks the desk pages for HTTPS source-link presence. Passing those checks means links are present and local links resolve; it does **not** mean every linked page is official or validates every adjacent value.

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

The game log was reconstructed and then **proved** against official NFL.com standings:
all 32 clubs match on wins, losses, ties, points for, points allowed and net points. The
committed corpus contains **150 completed games through Week 10**. Nine strategies were
scored on **118 out-of-sample games** under a chronological walk-forward protocol; the
best (S1) improves point-spread MAE over the league-constant baseline by **9.49%**, but
its 95% interval (**-0.01 to 1.97 points**) still includes zero. **No strategy is eligible
for a reward.** The spread-error correlations are based on n = 118; the regularized
strategies S3, S4, S6 and S7 are near-duplicates (correlations of 0.998–0.999), so they
are not independent evidence. See `research/strategy-validation.md` and
`research/correlation-and-luck.md`.

Prices are third-party market observations, not official NFL lines. `data/ops/price_snapshots.csv`
holds **60** opening/closing readings for the **30** originated markets (10 events), and
`data/ops/fair_market_difference.csv` keeps fair, market and residual in separate
columns. The current origination ledger grades **24** settled markets; the market dashboard
is a separate archive, so its records must not be conflated with the origination sample.
In the 16-game market comparison, every candidate's spread error is worse than the captured
closing market's (best model MAE 9.32 vs. market 8.47). This evidence keeps strategies on
paper and does not establish a betting edge. See `market.html`, `origination.html`, and
`signal-vs-staking.html`.

## The market column: what it is and what it is not

The league publishes no betting lines, so none of the market prices here is official NFL
data. Prices are third-party observations from the ESPN odds endpoint; each price row
retains its source URL and retrieval time. The current origination layer contains **30
markets**, with opening/closing prices in `data/ops/price_snapshots.csv`, and publishes fair
line, market line and fair-minus-market as separate values in
`data/ops/fair_market_difference.csv`. The site's other captured-market archive is a
separate dataset (`data/market-snapshots-2026.csv`); do not treat its records as the same
sample as the originated-line ledger.

A residual is a model-vs-market comparison, not proof of value. The opener/closer policy
and third-party source limitations are documented alongside the data; values with absent
source support remain flagged rather than upgraded to verified.


## Roster depth: which starters are actually missing

`depth.html` answers the depth question from an official source. The league publishes no
consolidated depth chart and `nfl.com/teams/<club>/depth-chart` 404s, but **each club publishes
its own chart on its own official website as a table whose column position is the depth
position**. 31 of the 32 clubs publish a machine-readable ordered chart; all 1,558 positions are
transcribed with a link to the page each came from, and joined by name to the official NFL.com
Week 10 injury report. The exception is Houston, which publishes its chart only as an image
(no authorized structured chart exists). For Houston the starter axis is resolved from an
authorized source instead — the official NFL Game Book (actual starters + per-player snap
counts), published as derived playing-time depth indices on `houston-depth.html` (flag F-24).

| Measure | Week 10 |
|---|---|
| Out/Doubtful players who sit on their club's chart | 62 of 81 (see F-42 on the one name-only match) |
| ... at **depth 1** (the listed starter) | **41** (23 offense, 18 defense) |
| Clubs with at least one listed starter out or doubtful | 20 |
| Positions where the club names nobody behind a ruled-out starter | 2 (both Tennessee) |
| Cascades - starter *and* his listed backup both out | **0** |

The zero is published deliberately. Any model that assumes a second- or third-string cascade is
happening in Week 10 would be inventing it. Houston publishes its chart only as an image, so it
contributes no rows (F-18); 20 ruled-out or doubtful players who are absent from their own club's chart are
listed by name rather than given a guessed rank (F-25), which makes the starter-out figure a
floor. These figures are from the 2026-11-15 re-capture of the official report (F-41); the earlier
prose (57 of 76, 40, 19) was not produced by the depth tool and is superseded (F-42). A published chart is not proof of who started - that is F-21, and ingesting the official
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

## Archived integration history

The dated session notes below preserve historical decisions, figures and merge records; their
old counts are not the current dashboard state. For current evidence, use the executive summary,
source audit and generated datasets linked above. The current provenance limitation (F-39) is
explicitly open in the audit above even though older integration notes record its earlier closure.

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

## The T31 integration pass (session `arena/da0b8a31-x4`)

The final integration after the origination layers landed:

- **The two remaining open pull requests were integrated in full** - PR #26 (real captured
  market prices: 174 DraftKings-via-ESPN rows over 29 games, open and close, the
  staking-independent skill board, the numeric demotion gate and `market.html`) and PR #22
  (the integrity programme: `programme.html`, the suggestion `workbench.html`,
  `research/decision-register.md`, `research/origination-programme.md`,
  `research/integrity-gates.md` and the `research/data/` datasets behind them). Both
  reported CONFLICTING; every conflict was resolved keeping **both** sessions' work, and
  the flag ids they both numbered F-29..F-31 were renumbered F-35..F-37 because the main
  register already held F-29..F-34 (the map is in `COORDINATION.md`).
- **Combined data re-verified against the live official pages**: nfl.com/standings read
  live and matched **32/32 clubs field by field**, the Week 11 schedule matched **13/13
  games**, and `tools/verify.py` (460 checks), `tools/market_store.py` and
  `tools/market_check.py` (432/432 re-derivations) all pass.
- **Every page is reachable from the landing directory**, including the nine
  origination-desk pages that previously only the desk sidebar linked.
- **Second pass (same day, after `main` moved to PR #33 and PR #29 opened):** `main` and PR #29's
  integration were merged in full; PR #34's live-sweep records were imported (its branch was too old
  to merge whole). The desk row-source check, which had never tested any row, now does, and it
  then reported 191 rows without an official link (flag F-39; closed line by line on 2026-11-17,
  see the provenance section above). Ten new injury drift cells are on
  the flags page (F-40). Details: `COORDINATION.md`, "T31 second integration pass".
- **One flag register, one nav, one gate**: F-01..F-37 with no duplicate ids, a union
  sidebar nav enforced by `tools/check_site.py`, and `tools/validate.py` now builds and
  checks every layer (main site, market layer, integrity programme, desk tables, console)
  with a determinism gate over 20 outputs. The publish workflow runs the same steps.

## Sources

NFL results, schedules, standings, injury reports, game books, roster moves and club depth
charts are linked to their official NFL or club source pages. Model outputs are derived
from committed inputs and code. Market prices are explicitly third-party observations
from ESPN's odds endpoint, not official NFL lines. Where the source-to-field link is not
proven, the value stays unverified or flagged; see `research/sources-register.md` and the
[dated provenance audit](research/audits/official-row-source-coverage-current-2026-11-19.md).

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
| Pages | 21 generated/main-site pages + linked review pages | 15 (incl. 404) |
| Pipeline | Python generator (`tools/`) → static output | No generator; hand-written static files |
| Publication gate | `python3 site/check.py` + `python3 tools/check_site.py` | `node docs/check.js` |

Both builds have source-check gates, but their measured scopes differ. The latest desk
row audit checks **1,138 rows on 29 pages** and classifies URLs by official-domain host;
725 rows have official-domain-only links, 90 mix official and non-official links, 323
have non-official HTTPS links only, and none lack an HTTPS URL. This does **not** prove
that any link supports the value beside it; F-39 remains open for source-to-field review.
The X4 Console gate separately checks 657 rendered data rows and 149 internal links.
Unsupported values remain blank or flagged. Do not read these checks as a claim that
every row across the full repository has been individually verified. Both builds reached
the same two structural conclusions independently:

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
node docs/check.js     # current counts are printed by the checker (15 pages, 21 tables, 657 rows)
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
| `data.html` | Standings (32), Week 10 schedule, Week 11 schedule **with the market snapshot**, 150 results - every row linked |
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

## Publish-gate repair and live re-verification (T32 / T33, session `arena/e6ee28a8-x4`)

- **T32** repairs the `Publish NFL Decision Lab` gate, which had failed on every
  `main` push since PR #25. Root cause, reproduced exactly by building CPython
  3.12.9 from source: `tools/market_store.py` serialised `data/output/market_store.json`
  with interpreter-dependent last-ULP float drift (CI runs Python 3.12, the authors'
  sandbox 3.11). The writer now normalises every float with the same
  `build.round_floats(obj, 9)` call `tools/build.py` adopted at PR #6, and
  `tools/fetch.py plan` no longer rewrites `data/ops/fetch_plan.json` when its
  plan items are unchanged (the timestamp-only rewrite used to dirty the tree
  after every full gate run). Verified byte-identical under 3.11.2 and 3.12.9 and
  through the full CI sequence; full write-up in
  `research/verification/publish-gate-repro-2026-11-14.md`.
- **T33** is an independent live re-verification sweep: all three official
  NFL.com pages (standings, Week 11 schedule, Week 10 injury report) re-fetched
  in full and diffed mechanically against the committed CSVs — **1,656 field
  checks**. Standings 32/32 and schedule 13/13 (including the Mexico City
  designation and the six byes) match exactly; the full 345-row injury capture
  (T20's sample was 44 rows) finds **12 practice-status cells the league has
  updated since the committed snapshot** — flagged with each cell's official
  player-page source link and left unedited. Record, captures, parser and
  per-row snapshot CSVs live in `research/verification/`
  (`live-verification-2026-11-14-e6ee28a8.md`, `captures-2026-11-14-e6ee28a8/`).

## Final integration and F-39 closure (T41, session `arena/550d7436-x4`, 2026-11-17)

- **F-39 closed line by line.** The 191 desk-table rows that had no HTTPS source link
  (13 pages) each now carry their authoritative evidence: official NFL pages for NFL
  facts, the committed artifact (the exact CSV or script, linked at its GitHub home) for
  computed and programme rows, and the official page checked plus a flag for blanks.
  The checker now reports **1,045 desk rows on 22 pages, 0 without a link**. The gate
  was not weakened; the honest limits are recorded on the flag (link presence is
  verified, not per-value semantic support; the 26 "points only" price rows stay
  unverified).
- **Stale-claim reconciliations.** The depth-rank rows that still said "404, unverified"
  (executive summary, requirements Q16/Q17, desk flags F-02/R-03) were superseded by the
  verified 31-club transcription (takeover of the stale T35 claim PR #44).
- **T38 Game Book evidence audit delivered** (takeover of stale claim PR #49, whose log
  cited a report that was never committed):
  [`research/verification/gamebook-source-review-2026-11-17.md`](research/verification/gamebook-source-review-2026-11-17.md).
  Verified live: the official [support article](https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books),
  a completed [Game Center](https://www.nfl.com/games/vikings-at-packers-2026-reg-10) with
  its Game Book PDF, the PDF's own use restriction (quoted verbatim in the report), the
  [Week 10 inactives article](https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season),
  and the Game Book's **Playtime Percentage** section - the official playing-time source.
  No player row is republished.
- **The injury report is published as a delta, not a level.** New `delta.html` and
  `tools/injury_delta.py` compute and publish every cell that moved between the two dated
  official captures of the Week 10 report; readiness row S4 now passes (the automated
  weekly series stays blocked on the failing capture workflow, flag F-43).
- **Every model total is published twice** (S3 model estimate and S0 benchmark, gap as its
  own column on `lines.html`) until the pre-registered walk-forward comparison picks a
  winner; the **price-data policy** and the **train/validation/final-holdout split** are
  frozen on `methodology.html`, dated before any backtest is published.
- **The T40 capture-health finding is surfaced** on both flag registers (main F-43, desk
  F-13), as its session requested. This session reproduced the same run-log EOF, so the
  failure cause remains unknown and is not guessed at.

## Two-stage escrow and the F-60 venue check (T48 / T49, session `arena/cc97fdb0-x4`, 2026-11-18)

- **`escrow.html`** (generated by `tools/gen_escrow.py`, self-tested by `tools/test_escrow.py`, run by `tools/validate.py`) implements the brief's two-stage board for the **pre-registered Week 11 window only** (`research/preregistration/wk11-forward-v1.md`, registration commit `8a33200`).
  - **Stage 1** is proper-score qualification: Brier skill against the de-vigged market, game-cluster bootstrap (B = 10,000, fixed seed), Bonferroni factor for the registered trials. Brier is defined for the **moneyline only**, because side and total publish a line, not a probability (flag E5).
  - **Stage 2** is a prospective CLV and ROI escrow: flat one-unit stakes, held until Stage 1 passes and a further pre-registered segment exists (G8, not yet registered).
- **Current result, stated as found:** 6 forward rows from 2 of 13 official Week 11 fixtures, 0 settled, 0 units held, 0 released. Every statistic is **NOT EVALUABLE**, not zero.
- **Flags for review (E1 to E7)** are on the page with source links. The two that matter most: the walk-forward numbers on `strategies.html` break the brief's rule against backtests on the leaderboard (E1); and all Week 11 entry prices were captured on 2026-11-14, four days before the registration (E7).
- **F-60 resolved** (`research/verification/venue-f60-2026-11-18.md`): the official per-game Game Info block reads `RELIANT STADIUM` and `ARROWHEAD STADIUM`, matching the committed venue file. NFL.com's schedule page uses different names only inside hotel-search links. No venue name was changed; two `retrieved` stamps were advanced to 2026-11-18.
- **Weather overlay: not built.** The NWS API is reachable, but the official game pages carry no stadium coordinates and no roof field, so the overlay cannot be keyed to a venue from an official source. It is recorded as blocked, with the two inputs that would clear it.
- The escrow page is **not yet linked from the shared navigation** (`tools/desk_nav.py`, `tools/check_site.py`, and the nine hand-written legacy pages are owned by the integration session). It carries its own sidebar link and is listed as a request on the board.
