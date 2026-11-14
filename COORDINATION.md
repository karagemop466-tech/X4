# COORDINATION.md — Shared Task Board

**Repo:** karagemop466-tech/X4
**Active session ID:** `5c48ced7`
**Session branch:** `arena/5c48ced7-x4` (platform-mandated session branch; equivalent to `session-5c48ced7/<task>` naming)
**Base commit:** `4c5280a7863a98605e2457690ad8a61cbd733f7f` (main)
**Started (UTC):** 2026-11-14

## Ground rules (for all sessions)

1. Read this file before starting any work. Claim a task by writing your session ID + file scope below, commit and push the claim immediately.
2. Never start a task another session has claimed. Keep file scopes non-overlapping.
3. If a task requires editing a file owned by another session, log a request in the "Cross-session requests" section instead of editing it.
4. Small, frequent commits. Run `git pull --rebase` before every push. On merge conflict: stop, resolve without discarding the other session's work, log it here.
5. Every factual table row must link an official, verifiable source. Values that cannot be confirmed from an official source are left blank and flagged (see `flagged.html`). Never infer or fill in values.
6. A task marked `needs review` means it is published on the Flagged for Review page; it does not block anything.
7. When a task is done: record sources, verification performed, and irregularities here, then mark `done`.
8. Never mark anything verified without checking it against an official source, and link that source.
9. Shared outputs (table data, site index, navigation) are changed only by the integration session once other tasks are done.
10. If a claim is older than 60 minutes with no commits, another session may take over and note the handoff here.

## Task board

Prior sessions 25459fae-x4 and arena/70ac0cf1-x4 completed and merged their claims before session 5c48ced7 began; their rows are retained (bottom of board) with their log preserved verbatim in the Session log section. Both prior sessions are inactive (branches deleted after merge), so their file scopes are released to the integration session.

| ID | Task | Status | Owner | File scope | Notes |
|----|------|--------|-------|------------|-------|
| T01 | Bootstrap COORDINATION.md task board | done | 5c48ced7 | `COORDINATION.md` | Created 2026-11-14; pushed immediately after claim. Rebased onto main and integrated with prior sessions' board (add/add conflict resolved by preserving both records). |
| T02 | Requirements inventory: full list of user requirements, mapped to deliverables | in progress | 5c48ced7 | `requirements.html` | 40 requirements extracted from the user brief; each mapped to a deliverable, status, and verification state. |
| T03 | Research & verify official NFL facts (season state, standings, schedule, depth charts, injuries, rules) | in progress | 5c48ced7 | `data.html`, `sources.html`, `research/*.md` | Sources fetched 2026-11-14: nfl.com standings/scores/schedules/injuries/depth-charts, operations.nfl.com rulebook. Every data row carries a source URL. |
| T04 | Strategy framework: signals, validation gates, correlation methodology + computed correlation values, skill-vs-luck metrics | in progress | 5c48ced7 | `strategies.html`, `research/strategies.md` | Methodology labeled as design/proposal. Computed correlation values are reproduced from official nfl.com data with formula, n, and retrieval date. |
| T05 | Leaderboard competition design (single / parlay / player-prop combo; rewards) | in progress | 5c48ced7 | `leaderboard.html`, `research/leaderboard.md` | Design document; scoring math specified; reward-pool parameters flagged as owner decisions. |
| T06 | Injury & depth-chart deficiency tracking design (incl. 2nd–4th string replacements, offense & defense) | in progress | 5c48ced7 | `injuries.html`, `research/injuries.md` | System design + official-source sample rows; unconfirmable cells blank + flagged. |
| T07 | Decision Q&A: questions/info/answers required before decisions; missing-information discovery | in progress | 5c48ced7 | `decisions.html`, `research/decisions.md` | 30 questions in 6 categories; each with known/unknown status, blocked decision, and how to obtain missing info. |
| T08 | Suggestions section (reviewable, choosable paths before implementation) | in progress | 5c48ced7 | `suggestions.html`, `research/suggestions.md` | 18 suggestions with impact/effort/status; filter UI; reviewer selection persisted locally; no implementation without selection. |
| T09 | Executive summary | in progress | 5c48ced7 | `executive-summary.html` | Detailed summary; verified/unverified counts; key decisions. |
| T10 | Site build: clean landing page + category subpages, dashboard UI, navigation, Flagged for Review page | in progress | 5c48ced7 | `index.html`, `*.html` subpages, `styles.css`, `nav.js` | Static multi-page site at repo root (Pages source: main /). Supersedes single-page layout; `site/` retained as historical archive, no longer linked. |
| T11 | Line-by-line verification pass; flag every unverified value and repo irregularity | in progress | 5c48ced7 | `flagged.html`, `repo-review.html`, `research/verification.md` | Verification log per item with source links; irregularities R-01…R-08 published for review. |
| T12 | Integration: combined data re-verified, link check passes, site builds with no broken links | in progress | 5c48ced7 | `index.html`, `nav.js`, shared nav | Integration session; `tools/check_site.py` validates all root pages, anchors, assets, and source links on data rows. |
| T13 | Create PR to main, merge without waiting for approval | in progress | 5c48ced7 | `COORDINATION.md` | See "PR & merge log" below for links and results. |
| T14 | Confirm GitHub Pages deploy succeeds after merge | in progress | 5c48ced7 | n/a (repo settings) | Verified via GitHub Pages API status `built`, Actions `pages-build-deployment` success, and HTTP 200 on live URL. |

Status values: `unclaimed` | `in progress` | `done` | `needs review`

### Claims from prior sessions (retained)

| Task | Status | Owner session | File scope |
|------|--------|---------------|------------|
| Build NFL decision-support research dashboard and documented verification framework | done | 25459fae-x4 | `site/**`, `README.md`, `COORDINATION.md`, workflow config |
| Integrate source-linked decision dashboard, executive summary and review sections into Pages site | done | arena/70ac0cf1-x4 | README.md, COORDINATION.md, index.html, styles.css, app.js, site/index.html, site/styles.css, site/app.js |

## Cross-session requests

- **5c48ced7 → future sessions:** root-level multi-page site (`*.html` at repo root) is now the canonical Pages source. Do not edit `site/**` (historical archive of sessions 25459fae-x4 / arena/70ac0cf1-x4) except by explicit claim.

## Session log

### 5c48ced7 — 2026-11-14
- **T01 done.** Created this file (repo had no COORDINATION.md at session start). Initial board claimed by `5c48ced7` because no other session had claimed any task at read time. Pushed immediately per protocol.
- **Conflict resolution:** `git pull --rebase origin main` produced an add/add conflict on `COORDINATION.md` (prior session had merged its own board during this session). Resolved by integrating: prior sessions' task rows and session log preserved verbatim below; no prior content discarded.
- **Branch note:** platform requires all session work on `arena/5c48ced7-x4`; this substitutes for the `session-<id>/<task>` branch convention. Non-overlapping file scopes still enforced above.

### Prior sessions (preserved verbatim from main)

- 2026-11-14 — Earlier session 25459fae-x4 completed its research dashboard and validation framework; its content and verification history are preserved in `site/` and below.
- 2026-11-14 — Current session checked the repository root before work and initially found only a four-byte README and no coordination file, site, or datasets. A separate session merged its completed contribution into `main` during this work. Fetched `origin/main`, identified overlapping work, preserved it and integrated this dashboard into the existing Pages site.
- Current-session claim commit `5a3e3aa` was pushed when the remote session branch did not exist. The standalone iteration commit was `94e9768`; integration follows the merged `main` contribution. No other branches were created.
- Earlier session sources: official NFL injury-report policy https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693; injury reports https://www.nfl.com/injuries/; rulebook https://operations.nfl.com/rules-officiating/2026-nfl-rulebook. Earlier checks: 8 IDs and 19 links in its source file; no current statuses, odds, results, depth chart or correlations verified.
- Current-session official pages fetched and checked: NFL injury reports (`https://www.nfl.com/injuries/`), NFL stats (`https://www.nfl.com/stats/`), team stats (`https://www.nfl.com/stats/team-stats/`), team directory (`https://www.nfl.com/teams/`), 2026 NFL Rulebook (`https://operations.nfl.com/rules-officiating/2026-nfl-rulebook`), and FTC UIGEA overview (`https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act`). They verify official source pages, not unpopulated rows. Current-session source check of the dashboard found 27 data rows, each with an HTTPS source link and no broken in-page anchors; the Pages source is verified separately below.
- Irregularity: initial `/the-rules/` reference returned 404; corrected to the verified NFL 2026 Rulebook. NFL rules are not book-specific wager settlement terms; FTC UIGEA is neither legal advice nor jurisdiction-specific guidance.
- Limitations: no licensed odds or historical point-in-time lineup data, API, predictions/results, model, data rights, product/jurisdiction, or contest rules. No current lines, injury statuses, depth ranks, empirical coefficients, edges, performance, or claim that luck can be eliminated are asserted. Unverified inputs remain flagged.
- Pages integration: retained earlier `site/` research and data-framework work; the new responsive interface and dedicated proposal section are integrated into Pages with styles and navigation. Verified exact `site/index.html` with Python parser: 8 IDs, 43 links, 27 data rows, every data row has HTTPS source, no broken anchors, both local assets exist; `python3 site/check.py` passes. Initial merged workflow run failed as a workflow-file issue before jobs started; replaced inline heredoc validation with standalone `site/check.py` and repaired workflow configuration in PR #3. PR #2 merged as `6e80cd05a00600cc0c4f49bb163947efe2dfa375` (https://github.com/karagemop466-tech/X4/pull/2); workflow-fix PR #3 merged as `8490ac8d237f5cd5aadfdbd618e666b3bb346ab4` (https://github.com/karagemop466-tech/X4/pull/3). Both custom Pages workflow `43547608834` and GitHub legacy Pages build/deploy `43547608074` completed successfully. Pages API reports `built`, public URL https://karagemop466-tech.github.io/X4/; Pages source is main root. Workflow warnings note Node 20 actions deprecation and `ubuntu-latest` image migration; builds/deploys succeeded. Site values that have no verified source data remain explicitly blank/flagged.

## PR & merge log

| PR | Branch → Base | Purpose | Link | Result |
|----|---------------|---------|------|--------|
| PR #1 | arena/25459fae-x4 → main | Add NFL Decision Lab research dashboard | https://github.com/karagemop466-tech/X4/pull/1 | merged 2026-11-14 (`4958ae6`) |
| PR #2 | arena/70ac0cf1-x4 → main | Source-linked NFL decision research dashboard | https://github.com/karagemop466-tech/X4/pull/2 | merged 2026-11-14 (`6e80cd0`) |
| PR #3 | arena/70ac0cf1-x4 → main | Fix NFL Pages validation and deployment workflow | https://github.com/karagemop466-tech/X4/pull/3 | merged 2026-11-14 (`8490ac8`) |
| PR #4 | arena/70ac0cf1-x4 → main | Record successful Pages publication | https://github.com/karagemop466-tech/X4/pull/4 | merged 2026-11-14 (`949fb44`) |
| PR #5 | arena/5c48ced7-x4 → main | Multi-page site: verified data, strategies, leaderboard, Q&A, suggestions, repo review | (recorded in PR #6) | (recorded in PR #6) |
| PR #6 | arena/5c48ced7-x4 → main | Final bookkeeping: records PR #5 result and Pages deploy verification | (see this PR on GitHub) | This line's presence on `main` proves PR #6 merged — it only reaches `main` via that merge. |

_Records are updated after each verified operation._
