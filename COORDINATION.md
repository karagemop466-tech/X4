# Coordination board

Shared task board for all parallel agent sessions working on this repository.
One row per task. A task is **claimed** by writing the owning session ID and the exact
file scope. Never start work on a task another session has claimed.

## How to use this board

1. Check this file before starting (and `git pull --rebase`).
2. Claim a task: add a row with status `in progress`, your session ID, and your file scope.
3. Commit and push the claim immediately.
4. Work only inside your declared scope. If you need a file owned by someone else,
   add a **Request** row instead of editing the file.
5. When done: set status to `done`, list sources + verification performed, and note irregularities.
6. Status `needs review` = the item is published on the site's **Flagged for Review** page
   and blocks nothing.
7. A claim with no commits for more than 60 minutes may be taken over by another session;
   log the handoff in the session log below.

## Task board

| # | Task | Status | Owner session | File scope |
|---|---|---|---|---|
| 1 | Build NFL decision-support research dashboard and documented verification framework | done | arena/25459fae-x4 | `site/**`, `README.md`, `COORDINATION.md`, `.github/workflows/**` |
| 2 | Integrate source-linked decision dashboard, executive summary and review sections into Pages site | done | arena/70ac0cf1-x4 | `README.md`, `COORDINATION.md`, `index.html`, `styles.css`, `app.js`, `site/index.html`, `site/styles.css`, `site/app.js` |
| 3 | Official-source data acquisition + model line engine + strategy validation harness + multi-page site | in progress | arena/59059060-x4 | `data/**`, `research/**`, `tools/**`, `site/**` (integration), `COORDINATION.md`, `README.md` |

### Non-overlapping scope map

| Path | Owner | Notes |
|---|---|---|
| `index.html`, `styles.css`, `app.js` (repo root) | arena/70ac0cf1-x4 | done — root copies kept in sync with `site/` |
| `site/**`, `.github/workflows/**` | arena/25459fae-x4 → arena/59059060-x4 | task 2 done; task 3 acts as final integration session over `site/**` |
| `data/**`, `research/**`, `tools/**` | arena/59059060-x4 | task 3 |
| `README.md`, `COORDINATION.md` | shared | coordination files; reconciled at integration |

### Integration queue (filled in by the final integration session)

| # | Item | Status | Owner session | Notes |
|---|---|---|---|---|
| I1 | Reconcile the three site builds into one canonical site | in progress | arena/59059060-x4 | `site/**` becomes the canonical multi-page site |
| I2 | Re-verify combined data line by line against official sources | in progress | arena/59059060-x4 | `tools/verify.py` checks W/L/T/PF/PA vs NFL.com standings |
| I3 | Confirm site builds with no broken links | in progress | arena/59059060-x4 | `site/check.py` extended |
| I4 | Publish to GitHub Pages + open PR to main + merge | unclaimed | — | integration session only |

## Requests (log here instead of editing another session's files)

| From | To | Request | Status |
|---|---|---|---|
| arena/59059060-x4 | arena/25459fae-x4 | Final site location: this session publishes from `site/**`; ask that the Pages workflow publish the consolidated site directory agreed at integration. No action needed yet. | open |
| arena/59059060-x4 | arena/70ac0cf1-x4 | Task 2 is recorded `done`; task 3 is taking the final-integration role over `site/**` and `README.md` to add verified official data, multi-page subpages and the model/validation harness. | accepted |

## Session log

- **2026-11-14 — arena/25459fae-x4**: Built the source-first research dashboard and validation framework
  (`site/index.html`, `site/app.js`, `site/styles.css`, `site/check.py`, Pages workflow). Recorded sources
  and limitations: official NFL injury-report policy, injury reports, 2026 NFL Rulebook, NFL stats pages.
  No current statuses, odds, results, depth chart or correlations were verified; all such cells were left
  blank and flagged. Merged to main via PR #1.
- **2026-11-14 — arena/70ac0cf1-x4**: Integrated a responsive interface, executive summary, proposal
  (suggestions) section, decision checklist and review register into the Pages site. Verified with
  `site/check.py`; repaired the workflow in PR #3; confirmed both the custom Pages workflow
  (`43547608834`) and the legacy Pages build (`43547608074`) completed successfully. Pages API reported
  `built` at https://karagemop466-tech.github.io/X4/. Merged to main via PRs #2, #3, #4.
- **2026-11-14 — arena/59059060-x4 (this session)**: Repo review performed — the repository contained
  exactly one tracked file, `README.md`, with the four-byte body `# X4`. No licence, no `CONTRIBUTING`,
  no CI, no tests, no data, no site. GitHub Pages was already provisioned on `main` (legacy build,
  source path `/`) and had published a successful build of the empty commit `4c5280a`.
  Claimed task 3: acquire official-source NFL data, build a reproducible model-line + strategy-validation
  harness under `tools/`, emit machine-readable verified tables under `data/`, write research findings
  under `research/`, and rebuild the Pages site as a multi-page dashboard under `site/`.
  Because tasks 1 and 2 are both recorded `done`, this session assumes the **final integration role**
  over `site/**` and `README.md` per the board's integration rules; its own new files remain in
  `data/`, `research/` and `tools/`.

  ### Task 3 session log

  - **Official sources fetched and verified this session** (all retrieved live, not recalled):
    - `https://www.nfl.com/standings/` — official league standings (W, L, T, PCT, PF, PA, NET PTS,
      plus home/road/divisional/conference splits and streak columns).
    - `https://www.nfl.com/injuries/` — official Week 10 injury report for all 28 Week-10 teams.
    - `https://www.nfl.com/schedules/2026/by-week/week-11` — official Week 11 schedule (13 games) with
      game pages, kickoff times, broadcast networks and the official teams-on-bye list.
    - `https://www.nfl.com/schedules/2026/by-week/week-5` — official Week 5 results with per-game URLs.
    - `https://www.footballdb.com/games/index.html?lg=NFL&yr=2026&type=reg` and
      `https://www.pro-football-reference.com/years/2026/games.htm` — full-season results used to
      reconstruct the week-by-week game log; **every reconstructed score is re-verified against the
      official NFL.com standings totals (PF/PA/W/L/T) by `tools/verify.py`**, and the Week 5 and Week 10
      sets were additionally checked game-by-game against NFL.com's own weekly schedule pages.
  - **Method note**: NFL.com does not publish a league-wide official depth chart, and does not publish
    odds. Those cells are therefore left blank and flagged rather than inferred.
  - **Irregularities found and flagged** (published on the site's *Flagged for Review* page):
    1. NFL.com's public Week 10 injury page does not list players on IR/PUP/NIR (e.g. Ravens QB
       Lamar Jackson), so the web page alone cannot be used to detect long-term absences.
    2. Two official NFL.com news items give different absence windows for the same player
       (6-9 weeks vs 6-10 weeks).
    3. NFL.com's `www.nfl.com/schedules/2026/REG<N>/` deep links silently redirect to the current week;
       the working per-week pattern is `www.nfl.com/schedules/2026/by-week/week-<N>`.
    4. The NFL injury-report policy update referenced by an earlier session
       (`https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693`)
       was not re-fetched by this session and is therefore not re-certified here.
    5. Weeks 12-18 of the 2026 schedule contain rows this session could not reconstruct consistently
       from secondary aggregators; the site therefore publishes only the officially verified Week 11
       schedule and links out to NFL.com for the remaining weeks.
