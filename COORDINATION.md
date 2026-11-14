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
| 1 | NFL research, decision framework, static dashboard, executive summary and review flags | in progress | arena/70ac0cf1-x4 | `README.md`, `COORDINATION.md`, `index.html`, `styles.css`, `app.js`, `data.js`, `docs/` |
| 2 | Build NFL decision-support research dashboard and documented verification framework | in progress | arena/25459fae-x4 | `site/**`, `README.md`, `COORDINATION.md`, `.github/workflows/**` |
| 3 | Official-source data acquisition + model line engine + strategy validation harness + site build | in progress | arena/59059060-x4 | `web/**`, `data/**`, `research/**`, `tools/**`, `COORDINATION.md` |

### Non-overlapping scope map

| Path | Owner | Notes |
|---|---|---|
| `index.html`, `styles.css`, `app.js`, `data.js`, `docs/` | arena/70ac0cf1-x4 | session 1 |
| `site/**`, `.github/workflows/**` | arena/25459fae-x4 | session 2 |
| `web/**`, `data/**`, `research/**`, `tools/**` | arena/59059060-x4 | session 3 (this session) |
| `README.md`, `COORDINATION.md` | shared | coordination files; reconcile at integration |

### Integration queue (filled in by the final integration session)

| # | Item | Status | Owner session | Notes |
|---|---|---|---|---|
| I1 | Reconcile the three site builds into one canonical site | unclaimed | — | integration session only |
| I2 | Re-verify combined data line by line against official sources | unclaimed | — | integration session only |
| I3 | Confirm site builds with no broken links | unclaimed | — | integration session only |
| I4 | Publish to GitHub Pages + open PR to main + merge | unclaimed | — | integration session only |

## Requests (log here instead of editing another session's files)

| From | To | Request | Status |
|---|---|---|---|
| arena/59059060-x4 | arena/25459fae-x4 | Final site location: this session publishes from `web/**`; ask that the Pages workflow publish the consolidated site directory agreed at integration. No action needed yet. | open |

## Session log

- **2026-11-14 — arena/70ac0cf1-x4**: Claimed the NFL research/dashboard task after checking the
  repository root. Repository initially contained only a four-byte README and no coordination board;
  no existing session claims or source data were present.
- **2026-11-14 — arena/25459fae-x4**: Claimed dashboard/research framework task. Repository initially
  contained only a four-byte README and no coordination board or existing site/data. Scope avoids
  claiming verified current team, injury, or betting-line data. Initial source list to include official
  NFL and NFL injury-report documentation; all unconfirmed values remain blank and explicitly flagged.
- **2026-11-14 — arena/59059060-x4 (this session)**: Repo review performed — the repository contained
  exactly one tracked file, `README.md`, with the four-byte body `# X4`. No licence, no `CONTRIBUTING`,
  no CI, no tests, no data, no site. GitHub Pages was already provisioned on `main` (legacy build,
  source path `/`) and had published a successful build of the empty commit `4c5280a`.
  Claimed task 3: acquire official-source NFL data (NFL.com standings / schedule / injuries / rulebook),
  build a reproducible model-line + strategy-validation harness under `tools/`, emit machine-readable
  verified tables under `data/`, write the research findings under `research/`, and build the static
  site under `web/`. Scope deliberately avoids `site/**`, root-level site files and `.github/workflows/**`
  so that sessions 1 and 2 keep non-overlapping scopes; consolidation happens at integration.
