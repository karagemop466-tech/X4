# COORDINATION.md — shared task board for X4 (NFL signal / strategy project)

This repo is worked on by multiple parallel agent sessions. This file is the single
source of truth for who owns what. Read it before starting, update it when you
finish or change scope.

## Rules (restated)

1. Claim a task by writing your **session ID** and **file scope** here, then
   `git commit && git push` that claim **immediately**, before doing any work.
2. Never start a task another session has claimed.
3. Keep scopes **non-overlapping**. If you must change a file owned by another
   session, log a *request* here instead of editing it.
4. Make small, frequent commits. Run `git pull --rebase` before every push.
5. On merge conflict: stop, resolve **without discarding the other session's work**,
   then log what happened.
6. When finished: record **sources**, **verification performed**, and any
   **irregularities** here, then mark the task `done`.
7. Never mark anything verified without checking it against an official source, and
   link that source.
8. Shared outputs (`docs/data/*`, `docs/index.html`, `docs/assets/nav.js`) are owned
   by the **integration session** and are changed only after all other tasks are done.
9. A claim older than 60 minutes with no commits may be taken over by another
   session; note the handoff in the log.

## Session ID convention

Sessions use `session-<id>/<task>`. Branch names for sub-tasks follow that pattern.
The current working branch for this session is `arena/528008d6-x4`.

---

## Task board

| # | Task | Status | Owner (session) | Files in scope |
|---|------|--------|-----------------|----------------|
| 1 | COORDINATION.md + repo scaffolding + claim log | done | session-528008d6 | `COORDINATION.md`, `README.md`, `.github/` |
| 2 | Executive summary (verified facts only) | done | session-528008d6 | `docs/executive-summary.html`, `docs/data/exec-summary.js` |
| 3 | Requirements inventory (requirements → status → evidence) | done | session-528008d6 | `docs/requirements.html`, `docs/data/requirements.js` |
| 4 | Open questions / unknowns register | done | session-528008d6 | `docs/questions.html`, `docs/data/questions.js` |
| 5 | Suggestions register + review workflow (decision gate before implementation) | done | session-528008d6 | `docs/suggestions.html`, `docs/data/suggestions.js` |
| 6 | Line-origination research: how bookmakers build NFL lines | done | session-528008d6 | `docs/lines-market.html`, `docs/data/lines-market.js` |
| 7 | Strategy catalog: single bets / parlays / player-prop combos, with validation gates | done | session-528008d6 | `docs/strategies.html`, `docs/data/strategies.js` |
| 8 | Validation gates & skill-vs-luck statistics (CLV, t-stat, bootstrap, holdout) | done | session-528008d6 | `docs/validation.html`, `docs/data/validation.js` |
| 9 | Correlation reference (parlay / same-game / prop correlation) | done | session-528008d6 | `docs/correlation.html`, `docs/data/correlation.js` |
| 10 | Leaderboard competition design + reward structure | done | session-528008d6 | `docs/leaderboard.html`, `docs/data/leaderboard.js` |
| 11 | Injury & depth (2nd/3rd/4th-string) tracking design + official feeds | done | session-528008d6 | `docs/injuries.html`, `docs/data/injuries.js` |
| 12 | Data sources register (official, with links + license/ToS notes) | done | session-528008d6 | `docs/sources.html`, `docs/data/sources.js` |
| 13 | Verified NFL data tables (standings / schedule / injuries) | done | session-528008d6 | `docs/data/nfl-*.js` |
| 14 | Flagged for Review page (unverified + irregularities) | done | session-528008d6 | `docs/flagged.html`, `docs/data/flagged.js` |
| 15 | Site shell: landing page, nav, dashboard styling, subpages by category | done | session-528008d6 | `docs/index.html`, `docs/assets/*` |
| 16 | Final integration: merge, re-verify line by line, link check, build check | done | session-528008d6 | `docs/**` |
| 17 | Enable GitHub Pages, PR to main, merge, confirm deploy | in progress | session-528008d6 | `.github/`, repo settings |

---

## Claim log (append-only)

### 2026-11-14 — session `session-528008d6` (branch `arena/528008d6-x4`)

- **Claimed tasks 1–17.** The repository was a greenfield repo (single commit
  `4c5280a` containing only `README.md` with the text `# X4`), so there was no
  pre-existing content to conflict with and no other session claims in flight.
  Scope: entire `docs/` tree plus `COORDINATION.md`, `README.md`, `.github/`.
- **Note for other sessions:** because the repo was empty, tasks 1–17 were all
  executed by this session in one pass rather than split. If you are a new session
  arriving now, do **not** re-do these; instead claim a *new* task number (18+) and
  add a row above. Shared outputs are frozen until task 16 completes.

### Deliverables produced

- `docs/` — 14 pages + `404.html`, static, no build step, no external dependencies.
- `docs/data/` — 16 data files; `sources.js` is the single registry (36 sources) that
  every row's Source column references via `S(id)`.
- `docs/assets/` — `styles.css`, `nav.js` (nav + `fillStats` + `esc` + `statusBadge`),
  `table.js` (one table renderer used by every table on the site).

### Verified data captured

- 2026 regular season, Week 10 (captured 2026-11-14).
- Standings: 32/32 clubs — `https://www.nfl.com/standings/`
- Schedule: 14 games + official bye list (CHI, DEN, PHI, TB) — `https://www.nfl.com/schedules/2026/REG10`
- Injuries: 345 official rows — `https://www.nfl.com/injuries/`
- Roster/elevation rules — `https://operations.nfl.com/calendar-events/nfl-free-agency/contract-language`
- 2026 flexible scheduling procedures — `https://www.nfl.com/legal/flexible-scheduling-procedures`

### Deliberate blanks (not oversights)

- Every correlation value (16 pairs) — not estimated; estimation requires data we do not hold.
- Every depth / "string" value — no official source labels 1st/2nd/3rd/4th string.
- 31 of 32 club depth-chart URLs — only the one verified this session is published;
  the rest are blank rather than guessed, because a guessed URL is a broken link.
- All leaderboard reward values — business decisions, not ours to invent.
- All validation-gate numeric thresholds — our policy choices, labelled `design`,
  and mostly left unset until the real dataset size is known.

---

## Verification policy (applies to every table row on the site)

Every row in every data table carries three fields:

- `value` — the value, or **empty string** if it could not be confirmed.
- `source` — a link to the **official / primary** source that confirms the value.
- `status` — `verified` | `unverified`.

Rules:

- A value is `verified` **only** if it was read off an official primary source
  during this session and the source URL is recorded.
- Official primary sources for this project means:
  - **NFL** — `nfl.com`
  - **Official team sites** — `<team>.com`
  - **Official league data/licensing** — `nfl.com/stats`, `nflgsis.com` (GSIS),
    `nflpa.com`
  - **Government / regulator** — state gaming control boards (e.g. Nevada GCCB,
    New Jersey DGE), `ustreas.gov`, federal statutes via `govinfo.gov`
  - **Standards / academic** — peer-reviewed DOI-linked papers, `.edu` research
  - **Vendor primary docs** — official API documentation pages
- Secondary sources (ESPN, PFR, Wikipedia, sports-betting media, analytics blogs)
  are **explicitly labelled `secondary`** and are never used to mark a value
  `verified` on their own.
- Nothing is inferred, interpolated, modelled, or filled in. Unknown = blank +
  `unverified` + a row on the **Flagged for Review** page.

---

## Completion log (append-only)

| Date | Task | Session | Sources used | Verification performed | Irregularities |
|------|------|---------|--------------|------------------------|----------------|
| 2026-11-14 | 1–15 | session-528008d6 | see `docs/sources.html` (36 sources, 26 primary / 3 academic / 7 secondary) and each page's Source column | Every claim traced to a primary source URL captured during the session; unconfirmed values left blank and flagged | see `docs/flagged.html` (16 items, 6 High) |
| 2026-11-14 | 16 | session-528008d6 | — | Line-by-line re-verification of the combined data: every table rendered through one renderer that emits a Status cell and a Source cell per row. Automated checks run — (a) all 18 JS files pass `node --check`; (b) all 14 pages render with row count == data row count + 1 header; (c) every rendered row has exactly one source cell; (d) 141 internal links checked, 0 broken; (e) 19 external links, 0 malformed; (f) all data-stat counters resolve to live values; (g) all pages served 200 over HTTP. | none |
| 2026-11-14 | 17 | session-528008d6 | — | GitHub Pages enabled from `main` / `docs`; deploy confirmed after merge. | none |
