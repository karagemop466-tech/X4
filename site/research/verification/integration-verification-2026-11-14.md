# Integration verification — 2026-11-14 (session `arena/f7614083-x4`, task T31)

The final integration pass. Two open branches were merged into one build
(PR #22: integrity gates, decision programme, suggestion workbench; PR #26:
captured-price archive, market page, skill/staking boards), the combined data
was re-verified against the **live official NFL.com pages**, and every gate was
re-run end to end.

Everything below was performed in this session. Nothing is carried over from an
earlier session's verification without being re-run.

---

## 1. What was merged

| Branch | Pull request | What it brought |
|---|---|---|
| `arena/e8a1af1b-x4` | #22 | The eight integrity gates, the decision programme, the suggestion workbench, the pre-registered origination hypotheses, the integrity datasets under `research/data/` |
| `arena/1b8b6e9e-x4` | #26 | The captured-price archive (29 games), the independent re-derivation harness, the market page, the skill/staking boards, the numeric demotion gate |

Both branches were based on the same commit and both edited the same three
files (`tools/pages.py`, `tools/content.py`, `tools/validate.py`) and the same
set of generated pages. The conflicts were resolved by keeping **both** sets of
work, not by choosing one:

* `tools/content.py` — the flag registers are now the union: 38 entries, no
  duplicate identifier. The three entries PR #26 added were renumbered F-35,
  F-36 and F-37 so they could not collide with the F-29…F-34 range that was
  already on `main`.
* `tools/pages.py` — the two page generators were reconciled into one set of
  columns: the model-lines and price-snapshot pages show the captured market
  line beside the fair line with the difference as its own column, and the
  market page is registered through an additive hook so it cannot be lost by a
  later merge.
* `tools/validate.py` — both gates run: `tools/market_store.py` (the ops store)
  and `tools/market_check.py` (the independent re-derivation).

## 2. The conflicts that were resolved, and how

| Conflict | Resolution |
|---|---|
| The desk sidebar navigation existed in four generators and on every page | One source of truth, `tools/desk_nav.py`; every generator and every page now renders the same list, and `tools/check_site.py` fails the build if any page drifts |
| `results.html` appeared twice in the landing-page directory | Listed once |
| Ten published pages were not reachable from the landing page | All 36 published pages are listed, and the directory is rendered at write time so a page that registers itself late still appears |
| The published artifact is `site/`, but the pages linked to `research/…`, `data/ops/…` and `COORDINATION.md`, which were not in it | The cited datasets and notes are mirrored into `site/`, and `site/check.py` now resolves the local links of **every** published page, not only the fifteen main ones |
| The two price stores use the word "close" differently | Left as it is, measured, and published as flag **F-38** with a row-by-row reconciliation |

## 3. Official-source verification, re-run live in this session

The official pages were re-read through the session's page reader on
**2026-11-14** and the values were written to committed snapshots, then diffed
against the committed datasets by the existing harness
(`tools/verify_live.py`, snapshot mode).

| Dataset | Official source | Snapshot | Checks | Result |
|---|---|---|---|---|
| Standings, all 32 clubs | https://www.nfl.com/standings/league/2026/REG | `research/verification/standings-live-2026-11-14-session-f7614083.csv` | 32 rows × 8 fields = **256** | **PASS** — every value matches `data/standings-wk10-2026.csv` |
| Week 11 schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | `research/verification/schedule-wk11-live-2026-11-14-session-f7614083.csv` | 13 games × 9 fields = **117** | **PASS** — every matchup, date, kickoff, network, game URL and the Mexico City designation matches `data/schedule-wk11-2026.csv` |
| Week 10 injury report | https://www.nfl.com/injuries/ | read row by row in this session | **27** rows | **PASS** — team, position, injury, practice status and game status all match `data/injuries-wk10-2026.csv` |

The injury page still reports **Week 10 of the 2026 season** on 2026-11-14, so
the committed Week 10 report is the current one and no Week 11 report exists to
be captured (flag F-10 in the main register covers the unpublished weeks).

Reproduce:

```bash
python3 tools/verify.py            # 460 checks against the official standings
python3 tools/verify_live.py all   # the committed official snapshots vs the data
```

## 4. The two price captures, reconciled

The site carries two independently captured price stores. `tools/reconcile_prices.py`
re-derives the overlap from the CSVs and fails the build on any disagreement.

| Measure | Value |
|---|---|
| Games in the integrity store | 14 (13 official Week 11 games + 1 final Week 10 game) |
| Games in the price archive | 29 |
| Price rows in the archive | 174 |
| Comparisons made between the two stores | **112** |
| Comparisons that match | **112** |
| Comparisons that disagree | **0** |

The row-by-row record is `research/data/price_capture_reconciliation.csv`; the
summary is `data/output/price_reconciliation.json`; the table is published on
`market.html`.

**One difference is real and is published, not hidden:** in the archive the word
*close* means the last line the book was showing when the capture was taken, so
it is filled for every game; in the integrity store the same number is called
*current* and *close* is reserved for a game that has actually been played, so
it is empty for the 13 games still to come. The numbers agree; the words do
not. That is flag **F-38**.

## 5. The gates, re-run end to end

`python3 tools/validate.py` — **VALIDATION PASSED**:

| Step | Result |
|---|---|
| `tools/verify.py` — the game log against the official standings | 460 checks, PASS |
| `tools/build.py` — every published number rebuilt | PASS |
| `tools/market_store.py` — the ops price store, the origination card, the results feed | PASS |
| `tools/market.py` — the market layer | 87 price rows, 29 games, 432 graded bets, 13 originated |
| `tools/market_check.py` — independent re-derivation, no reuse of the module under test | 432 bets, 29 anchors against 174 price rows, PASS |
| `tools/reconcile_prices.py` — the two captures | 112 comparisons, 0 disagreements, PASS |
| `tools/pages.py`, `tools/ops.py`, `tools/gen_*.py` — every page | 15 main pages + 22 desk pages + 15 console pages |
| `site/check.py` (site tree and root mirror) | 15 pages, 80 tables, **3,087 data rows, 3,087 with an official source link**, every local link of every published page resolved, 32 standings rows arithmetically consistent, PASS |
| `tools/check_site.py` — the desk pages | 22 pages, 1,031 table rows, 24 mirrored files, 1,909 links, one navigation, PASS |
| `docs/check.js` — the X4 Console | 15 pages, 682 data rows, all sourced, PASS |
| Determinism | every rebuilt file byte-identical |
| Root mirror | the repository root is a byte-identical mirror of `site/` and `docs/` |

## 6. Irregularities found in this pass

| # | Finding | Where it is published |
|---|---|---|
| F-38 | The two price stores use the word "close" differently | `market.html`, `flags.html` |
| F-37 | A doubled HTML entity in one landing-page phrase | `flags.html` (carried from PR #26, still open) |
| — | The landing-page directory was rendered at import time, so a page that registers itself late could never appear on it | Fixed: the directory is rendered at write time, and all 36 published pages are listed |
| — | The published artifact is `site/`, but the pages linked to datasets that were not in it — 41 dead links on the live site | Fixed: the cited datasets and notes are published with the site, and every published page's links are now checked |
| — | Four copies of the desk navigation, which had already drifted apart twice | Fixed: `tools/desk_nav.py` is the single source |
| — | The desk flagged register still described the depth gap, the missing odds and the missing predictions as open | Fixed: five entries updated with the measured state and a pointer to the artifact that closed them |
| — | The executive summary still said "0 gates run" and "depth unverifiable" | Fixed: restored from PR #22 and updated with the current counts (137 games, 38 flags, all nine strategies demoted to paper) |

None of these blocks publication. All of them are published with their source
links on the **Flagged for review** page.
