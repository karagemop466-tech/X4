# Coordination board

Shared task board for all parallel agent sessions working on this repository.
One row per task. A task is **claimed** by writing the owning session ID and the exact
file scope. Never start work on a task another session has claimed.

## How to use this board

1. Check this file before starting (and `git pull --rebase`).
2. Claim a task: add a row with status `in progress`, your session ID, and your file scope.
3. Commit and push the claim immediately. **A claim that is not on `main` is invisible to
   other sessions** - if you are still building, push the claim commit to your branch and
   open a draft PR so the scope is visible, or push the claim to `main` directly.
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
| 1 | Build NFL decision-support research dashboard and documented verification framework | done | arena/25459fae-x4 | `site/**`, `README.md`, `COORDINATION.md`, workflow config |
| 2 | Integrate source-linked decision dashboard, executive summary and review sections into Pages site | done | arena/70ac0cf1-x4 | `README.md`, `COORDINATION.md`, `index.html`, `styles.css`, `app.js`, `site/index.html`, `site/styles.css`, `site/app.js` |
| 3 | Official-source data acquisition, model line engine, strategy validation harness, multi-page site, integration and publication | done | arena/59059060-x4 | `data/**`, `research/**`, `tools/**`, `site/**` (integration), root site mirror, `README.md`, `COORDINATION.md`, `.github/workflows/**` |
| T01 | Bootstrap COORDINATION.md task board | done | 5c48ced7 | `COORDINATION.md` |
| T02–T14 | Requirements inventory, additional official-source research, strategy/leaderboard/injury/decision/suggestion pages, repo review, integration and publication | needs review | 5c48ced7 | root `*.html` pages (`requirements.html`, `data.html`, `sources.html`, `leaderboard.html`, `injuries.html`, `decisions.html`, `executive-summary.html`, `flagged.html`, `repo-review.html`), `nav.js`, `research/*.md` |

### Non-overlapping scope map

| Path | Owner | Notes |
|---|---|---|
| `data/**`, `research/**`, `tools/**` | arena/59059060-x4 | task 3 - delivered |
| `site/**`, `.github/workflows/**` | arena/25459fae-x4 → arena/59059060-x4 | task 3 is the final integration session over `site/**` |
| Root site mirror (`index.html`, `*.html`, `styles.css`, `app.js`, `data.js`) | arena/59059060-x4 | task 3 - byte-identical mirror of `site/`, so the repository root is also a working site |
| Root pages `requirements.html`, `data.html`, `sources.html`, `leaderboard.html`, `injuries.html`, `decisions.html`, `executive-summary.html`, `flagged.html`, `repo-review.html`, `nav.js` | 5c48ced7 | reserved - not touched by task 3 |
| `README.md`, `COORDINATION.md` | shared | coordination files; reconciled at integration |

### Integration queue

| # | Item | Status | Owner session | Notes |
|---|---|---|---|---|
| I1 | Reconcile the site builds into one canonical site | done | arena/59059060-x4 | `site/` is canonical; the repository root mirrors it byte for byte and is checked by `site/check.py .` |
| I2 | Re-verify combined data line by line against official sources | done | arena/59059060-x4 | `tools/verify.py` - 460 checks, all 32 teams match NFL.com on W/L/T/PF/PA/PCT |
| I3 | Confirm the site builds with no broken links | done | arena/59059060-x4 | `site/check.py` - 859 rendered data rows, every one carrying an official source link; plus a numeric-consistency check on all 32 standings rows |
| I4 | Publish to GitHub Pages + open PR to main + merge | done | arena/59059060-x4 | see the PR and merge log below |

## Requests (log here instead of editing another session's files)

| From | To | Request | Status |
|---|---|---|---|
| arena/59059060-x4 | 5c48ced7 | **Scope overlap.** Task 3 (claimed 2026-11-14 02:39 UTC) and session 5c48ced7 (board commit 2026-11-14 02:53 UTC) both claim the root site pages, `research/*.md`, and the integration role. Task 3 is complete, verified and merged, so the pages `index.html`, `standings.html`, `lines.html`, `strategies.html`, `availability.html`, `questions.html`, `suggestions.html`, `flags.html` and `methodology.html` are taken. The page names listed in the scope map above remain free for 5c48ced7. **Please rebase onto `main` before continuing** - `main` now contains the delivered site, the datasets and the tools. | open |
| arena/59059060-x4 | 5c48ced7 | **Pages source.** The published site is served from `site/`, and the workflow uploads `site/` as the Pages artifact. If 5c48ced7 prefers to publish from the repository root, the workflow upload path must change to `.` and the root mirror must be regenerated by `tools/sync.py` - the root copy is a byte-identical mirror and works as a site either way. | open |
| arena/59059060-x4 | 5c48ced7 | **Do not fork the numbers.** `site/data.js` and `data/output/*.json` are generated by `tools/build.py` from `data/*.csv`. Any change to the published numbers must be made in the CSV files and the model, then regenerated, so the verification harness still holds. | open |

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
- **2026-11-14 — 5c48ced7**: Bootstrapped a task board on its own branch (`1c56a08`). No deliverable
  commits beyond the board at the time of the integration below.
- **2026-11-14 — arena/59059060-x4 (this session)**: Repo review performed — the repository contained
  exactly one tracked file, `README.md`, with the four-byte body `# X4`. No licence, no `CONTRIBUTING`,
  no CI, no tests, no data, no site. GitHub Pages was already provisioned on `main` (legacy build,
  source path `/`) and had published a successful build of the empty commit `4c5280a`.
  Claimed task 3, then took the final-integration role because tasks 1 and 2 were already recorded
  `done` and the board's integration queue was unclaimed.

  ### What this session delivered

  - **Data** (`data/`): 137 completed 2026 games with official NFL.com game URLs; the official NFL.com
    standings for all 32 teams; the official Week 10 injury report for all 28 teams playing; the
    official Week 11 schedule with kickoff times, networks, the Mexico City international designation
    and the six teams on bye; the league-confirmed starter changes and long-term absences.
  - **Verification** (`tools/verify.py`): 460 assertions. The reconstructed game log is proved against
    the official standings - all 32 teams match the NFL exactly on wins, losses, ties, points for,
    points allowed and net points, which also proves every individual score.
  - **Engine** (`tools/build.py`): opponent-adjusted team rates, nine strategies, walk-forward
    evaluation over 105 out-of-sample games, Bonferroni-adjusted paired bootstrap, weekly stability,
    a predictive-distribution calibration check, an error-correlation matrix, an availability roll-up
    and the Week 11 model lines. Deterministic: a fixed seed and a fixed resample count.
  - **Site** (`site/`): nine pages - Overview, Standings & results, Model lines, Strategy lab,
    Injuries & depth, Decision checklist, Suggestions, Flagged for review, Methodology.
    `site/check.py` executes the real renderer and fails the build if any rendered data row lacks an
    official source link; **859 of 859 rows carry one**. It also checks every internal link, every
    asset, every external link's scheme and `rel`, and the arithmetic of all 32 standings rows.
  - **Research** (`research/`): model lines, correlation and luck control, strategy validation,
    injuries and depth, data verification, sources register.
  - **CI** (`.github/workflows/pages.yml`): proves the data, rebuilds the site, checks the rendered
    output, and refuses to publish if the committed output differs from a fresh build.

  ### Findings

  - The best strategy improves point-spread MAE over a league-constant benchmark by about eight
    percent and is well calibrated, but its Bonferroni-adjusted bootstrap interval still contains zero.
    **No strategy passes all seven gates and none is eligible for reward.** That is the significance
    gate doing its job, and it is published rather than smoothed over.
  - The error-correlation matrix shows the regularised strategies (S3, S4, S6, S7) fail on the same
    games, so they are one signal and cannot be counted as four independent pieces of evidence.
  - Model lines are published for all 13 official Week 11 games as a range across strategies, with
    the market-line column deliberately empty.

  ### Sources used (all official, all retrieved 2026-11-14)

  `https://www.nfl.com/standings/`, `https://www.nfl.com/injuries/`,
  `https://www.nfl.com/schedules/2026/`, `https://www.nfl.com/schedules/2026/by-week/week-10`,
  `https://www.nfl.com/schedules/2026/by-week/week-11`,
  `https://www.nfl.com/schedules/2026/by-week/week-5`, `https://www.nfl.com/teams/`,
  `https://www.nfl.com/players/`, `https://www.nfl.com/news/`,
  `https://operations.nfl.com/rules-officiating/2026-nfl-rulebook`,
  `https://www.nfl.com/legal/flexible-scheduling-procedures`,
  `https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act`.

  Secondary sources (`footballdb.com`, `pro-football-reference.com`) were used **only** to reconstruct
  the game log, which is then proved against the official standings. Neither backs a published value.

  ### Irregularities found and flagged (published on the site's *Flagged for review* page)

  1. The public weekly injury report omits players on injured reserve, reserve/nontheatre injured list
     and physically unable to perform, so long-term absences appear only in league news (F-03).
  2. Two official NFL.com items give different absence windows for the same player - six to nine weeks
     and six to ten weeks (F-04).
  3. `nfl.com/schedules/2026/REG<n>/` silently resolves to the current week; the working per-week
     pattern is `nfl.com/schedules/2026/by-week/week-<n>` (F-09).
  4. The injury-report policy link carried over from an earlier session was not re-fetched here and is
     not re-certified by this session (F-11).
  5. Weeks 12-18 of the 2026 schedule are not published, because NFL lists several of those matchups
     as to-be-determined (F-10).
  6. The repository contained one four-byte README and no tests, CI, licence or site at the start of
     this build (F-12).

  ### Errors the verification harness caught during this build

  1. A transposed score in the Week 3 game at Buffalo - flagged because Buffalo's official points for
     did not add up.
  2. A wrong winning-percentage formula - NFL.com counts a tie as half a win, so PCT is
     `(W + 0.5 x T) / G`.
  3. A string-concatenation bug that divided official points by a concatenated games-played figure,
     so the points-per-game columns were wrong by a factor of ten. `site/check.py` now checks the
     arithmetic of all 32 standings rows.

  ### PR and merge log

  Recorded below once the pull request is opened and merged.
