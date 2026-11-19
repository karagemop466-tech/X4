# Request-versus-repository gap audit — session arena/2a5f637e-x4 (2026-11-19 UTC)

Scope: a read-only audit of the long requirements list against `main` at `06dcc0d`, plus the
live GitHub Pages site. No data, schema or published value was changed. Nothing here is a new
verified number. Where this file says "present", it means a page or file exists in the repository;
it does not mean the item was re-verified line by line in this session.

## 1. Checks run in this session

| Check | Result | Evidence |
|---|---|---|
| `python3 tools/validate.py` on branch `arena/2a5f637e-x4` | `VALIDATION PASSED - the repository is publishable.` (exit 0) | local run, 2026-11-19 |
| Live readiness page | Served; shows the eight gates, S1–S5 and the two-sided "what would change our mind" table | https://karagemop466-tech.github.io/X4/readiness.html |
| Latest `main` runs | `pages build and deployment` success (44480549695); `Official capture` success (44480508108) | `gh run list` on `main`, 2026-11-19 |
| Capture manifest | 192 rows; `raw_retained` is `false` on the rows inspected | `data/captures/manifest.jsonl` |
| Retention audit | 0 rows with `raw_retained: true`; 0 with `raw_store: private`; F-75 open | `research/verification/capture-retention-2026-11-19.md` |
| Weather / roof data | Official Game Book fields (surface/roof, game weather, wind) exist for **Week 10 only** | `data/venue-surface-wk10-2026.csv`; source links per row (NFL.com game centre PDFs) |
| NWS hourly forecast overlay | **Not built.** No NWS data in `data/`, no NWS source in `research/` or `tools/` | `grep -ril "NWS\|weather.gov"` on the repository |

## 2. Requirement status

Status key: **present** = built and gate-checked in an earlier session; **partial** = built for a
subset or with a documented gap; **missing** = not built; **blocked** = needs an authorised or
official source this sandbox cannot reach or has not been granted.

| # | Requirement (as requested) | Status | Evidence / blocker |
|---|---|---|---|
| 1 | Price-snapshot store, open and close per market | present | `price-snapshots.html`, `data/price-snapshots.csv`, `data/market-snapshots-2026.csv` |
| 2 | Verified results feed | present | `results.html`, `data/results-feed.csv` |
| 3 | Origination order: side, then total, then moneyline | present | `origination.html`; README origination section |
| 4 | Fair line, market line, difference as separate columns | present | `lines.html` |
| 5 | Signal separated from staking on the leaderboard | present | `signal-vs-staking.html`, `gates.html` |
| 6 | Replacement depth, not just the fact of a replacement | partial | `replacements.html`, `data/replacement-depth.csv`; depth-slot fidelity note in `research/verification/depth-slot-fidelity-2026-11-18.md` |
| 7 | Correlations from official numbers, n published | present | `correlations.html`, `strategies.html` |
| 8 | Demotion gate sends a live strategy back to paper | partial | `readiness.html` D1–D6; **D1 and D6 thresholds are blank, so not evaluable** |
| 9 | Pre-registration; backtests excluded from leaderboard | present | `research/preregistration/`, 21 pages reference pre-registration |
| 10 | Availability graph (expected vs actual starters) | partial | `availability.html`, `actual-starters`; Week 10 only |
| 11 | Depth from playing time, not jersey order | partial | `houston-depth.html`; Houston ordinal chain blank (F-24) |
| 12 | Injury signal as a surprise, not a level | missing as a model feature | delta view exists (`delta.html`); no surprise model |
| 13 | 32-team roster / IR sweep before team-level trust | partial | `research/verification/independent-sweep-2026-11-18-92faad64.md`; Houston not resolved to an ordinal chain |
| 14 | Fixture-context features from published schedule facts | partial | schedule files exist (`data/schedule-wk10-2026.csv`, `schedule-wk11-2026.csv`) |
| 15 | Probability plus inputs for every model output | partial | model outputs in `data/output/`; not all rows carry probability + inputs |
| 16 | "Removal of luck" panel on the dashboard | present | `luck.html` |
| 17 | Two-sided "what would change our mind" per strategy | present for the v1 ratio model | `readiness.html`; not confirmed for every strategy |
| 18 | Publish residual against the market on a schedule | partial | `market.html`; schedule not evidenced |
| 19 | 136-game log turned into the pre-registered backtest corpus | partial | `data/games-2026.csv` (150 official games per README); corpus definition not re-verified |
| 20 | Price-data policy decided before any backtest is published | partial | `research/price-store.md`; policy status not re-checked |
| 21 | Injury-hub reads stored with clock time; publish deltas | partial | `delta.html`; `capture_official.py`; manifest entries carry `fetched_utc` |
| 22 | Decision-readiness table on the landing page | present | `readiness.html`; `index.html` |
| 23 | Venue of every fixture from the official game centre | partial | Week 10 complete (`venue-surface-wk10-2026.csv`); Week 11 in `venues-wk11-2026.csv` |
| 24 | League's dated schedule announcement beside the schedule page | missing (not found) | a grep of `site/*.html` for "schedule announcement" or "schedule release" returned nothing |
| 25 | Official NFL Game Books for starters and game-day status | partial | `gamebook.html`, `gamebook-ops.html`; coverage not complete for all 32 clubs |
| 26 | Game-level results to make ratings opponent-aware | not verified | the terms appear on `gates.html`, `lines.html`, `market.html`, `index.html`; no opponent-adjusted rating file was found in `data/` or `research/` |
| 27 | Injury and personnel ablations instead of fixed penalties | partial | `personnel-ablation.html`; control group empty (per page) |
| 28 | Immutable multi-day availability snapshots, raw retained | **blocked / partial** | hashes only; `raw_retained` 0; no private store configured (`capture-retention-2026-11-19.md`) |
| 29 | Immutable official snapshots with raw hashes, timestamps, conflict flags | partial | hashes and timestamps yes; raw bodies not retained; conflict flags not confirmed |
| 30 | Official inactive lists and snap counts | partial | `inactive-lists-wk10-2026.csv` (196 rows, 6 blank evidence); **snap counts not captured** |
| 31 | Fix the two depth-parsing failures (Texans image, Packers numbers) | partial | Packers number stripping not re-verified; Texans image still needs an authorised structured source (`houston-depth.html`, F-24) |
| 32 | Depth slots as groups, not a single starter | partial | `research/verification/depth-slot-fidelity-2026-11-18.md` |
| 33 | Roster turnover as a first-class event (Colts Week 10) | partial | `data/transactions/` exists; versioning against roster events not confirmed |
| 34 | Singles-only shadow baseline, frozen before kickoff | partial | pre-registration commit exists for Week 11 (readiness S3) |
| 35 | Parlays and props behind a joint-evidence gate | present as a gate | `leaderboard.html` (singles / parlays / props); no joint-probability source |
| 36 | Proper-score leaderboard divisions with uncertainty | partial | Brier and skill shown in `readiness.html`; per-division ranking not confirmed |
| 37 | Rank by Brier skill with cluster lower bound and multiplicity | partial | G4 and G6 in `readiness.html` are "not computed" |
| 38 | Durable snapshot storage outside the static site; freshness and alerts | **missing** | no external store configured; F-87 (scheduler cadence) open |
| 39 | Public analysis layer vs private data layer | **missing** | repository is public; row-level player files are tracked (`capture-retention-2026-11-19.md`); F-75 open |
| 40 | Per-team view: starters out, replacements named, net injury count | present | `teams.html` |
| 41 | Announced-starter evidence field | partial | `data/qb-starter-changes.csv` has rows for Drew Lock, Kyle McCord and Sam Darnold, each with an NFL.com news link. These are not re-verified in this session, and the file's source column is NFL.com news, not the league transaction log
| 42 | Official depth-chart register with date and source per row | present | `depth.html`; `data/depth-wk11-2026.csv` |
| 43 | Calibrate what "Questionable" means | blocked | official text gives no percentages; needs a designation-outcome series (`designation-reliability-wk10-2026.csv`, 171 rows, one week) |
| 44 | Interactive offense vs defense matchup matrix | partial | `matchup.html` (static tables; not confirmed interactive) |
| 45 | Stale depth rows flagged against the transactions log | partial | `data/transactions/`; flag coverage not re-verified |
| 46 | Point-in-time ledger for injuries, depth and inactives | partial | manifest and `delta.html`; no per-record ledger confirmed |
| 47 | Lions game-status designations populated | present in data (Out) | `data/injuries-wk10-2026.csv`: Kerby Joseph, Cade Mays, D.J. Reed each show Out (DNP). Not re-checked against the official article in this session |
| 48 | Re-capture Week 10 injury tables | partial | `injuries-wk10-2026.csv` (347 rows on the Week 10 page) |
| 49 | Reject deriving depth from jersey, experience or salary | present | policy recorded in `research/` |
| 50 | Shared and empty depth slots represented faithfully | partial | `depth-slot-fidelity-2026-11-18.md` |
| 51 | Resolve depth-order source before the backup-deficiency feature | blocked | route (a) per-club charts verified for 31 of 32 clubs; Houston blocked (F-24) |
| 52 | Score designation reliability before using it as a feature | partial | `designation-reliability-wk10-2026.csv`, `designation-outcomes-wk10-2026.csv`; one week only |
| 53 | Snapshot the injury report on Wed, Thu and Fri; daily to kickoff | partial | scheduled capture runs on `main` (success 2026-11-19); cadence gap F-87 |
| 54 | Snap counts as the starter proxy | missing | snap counts not captured |
| 55 | Control baseline (random; favourites) on every leaderboard run | partial | `luck.html`; only on the luck page |
| 56 | Stadium roof / surface and NWS hourly wind and precipitation overlay | **missing (NWS)**; partial (roof/surface, Week 10) | NWS grid not fetched; the sandbox allows only github, npm and pypi hosts in bash |
| 57 | Two-stage escrow (proper-score qualification, then CLV/ROI) | partial | `escrow.html`; `research/verification/escrow-2026-11-18.md` |
| 58 | Vig-free consensus vs originated fair-line decomposition | partial | `market.html`, `origination.html` |
| 59 | Weekly "what changed" diff | partial | `delta.html` (Week 10 only) |
| 60 | Publish every model total twice until one wins | partial | the term appears in `lines.html`; the dual-estimator gap column was not checked in this session |
| 61 | Drift alarm on every scraper | partial | `drift` in 3 pages; `tools/capture_official.py` schema checks |
| 62 | Reserve list so "not listed" never means "available" | partial | `official-reserve-list-2026-11-17.csv` |
| 63 | Reject season-long ROI ranking | present as policy | `strategies.html` |
| 64 | Archive weekly injury reports for past seasons | missing | only Week 10 and Week 11 official reads recorded |
| 65 | Pre-register each strategy before results | present | `research/preregistration/` |
| 66 | Train, validation and final holdout seasons | partial | "holdout" appears in `methodology.html`, `open-questions.html`, `executive-summary.html`; the data holds one season (2026), so a three-season split cannot be evidenced |
| 67 | Executive summary | present | `executive-summary.html` |
| 68 | Suggestions section for review before any change | present | `suggestions.html`, `review.html`, `workbench.html` |
| 69 | Questions, information and answers that gate decisions | present | `questions.html`, `open-questions.html`, `decisions.html` |
| 70 | Verified repository review with links | present | `repo-review.html` |
| 71 | Flagged for Review page | present | `flagged.html`, `flags.html` |

## 3. Blockers this session cannot clear

1. **Authorised sources.** The Texans depth image, the NWS hourly grid, snap counts, and the
   private store for raw captures need an authorised source or an owner decision. None is
   inferred here.
2. **Sandbox network.** Bash reaches only github.com, codeload.github.com, api.github.com,
   registry.npmjs.org, pypi.org and files.pythonhosted.org. Official NFL and club pages were read
   through the page-fetch tool only, for the spot checks listed in section 1.
3. **Coordination protocol.** `COORDINATION.md` asks each session to use its own
   `session-<id>/<task>` branch. This session is fixed to `arena/2a5f637e-x4`, so the work is
   logged on that branch only.
4. **Scale.** About 70 requirements, many needing multi-week data collection. A single session
   cannot finish them honestly.

## 4. Recommended order of work (for review, not started)

1. Decide the private-store location and the data-terms position (blocks rows 28, 29, 38, 39).
2. Configure durable retention for the capture bodies (rows 28, 29, 46, 64).
3. Add snap-count and NWS sources only after an authorised route is confirmed (rows 54, 56).
4. Clear the blank D1/D6 demotion thresholds, with the owner setting them (row 8).
5. Capture the Week 11 official injury report in full, once the schema check accepts it (rows 47, 53).
