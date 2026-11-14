# X4 — NFL Signal & Strategy Console

A research and governance console for originating independent NFL prices, turning them into
candidate strategies, and admitting a strategy to a leaderboard only after it passes
validation gates designed to strip out luck.

**Live site:** published from `docs/` on `main` via GitHub Pages.

## What is actually in here

| Area | Contents |
|------|----------|
| `docs/` | The entire site. Static HTML/CSS/JS — **no build step**, so there is nothing to break. |
| `docs/data/` | One JS data file per subject. Every table on the site is rendered from these. |
| `docs/assets/` | `styles.css`, `nav.js` (single nav definition + stat filler), `table.js` (one table renderer). |
| `COORDINATION.md` | Shared task board for parallel agent sessions: claims, scopes, verification policy, completion log. |

## The verification rule

Every row in every table carries a **Status** and a **Source**.

- `verified` — read off an official primary source during the session; the URL is on the row.
- `design` — this project's own engineering proposal (thresholds, schemas, workflows).
- `secondary` — media or aggregator source; never sufficient on its own to verify a value.
- `unverified` — unknown. Rendered as *— unverified —* and listed on **Flagged for Review**.

**Nothing is inferred, interpolated, modelled or filled in. Unknown means blank.**

## Honest status of the strategy work

There are 12 candidate strategies, 16 correlation pairs and a 9-gate validation pipeline
specified. There are **zero** backtested strategies and **zero** estimated correlations,
because the repository contains no historical odds, play-by-play or participation data.
Two structural blockers are documented on the site:

1. **No official source for betting prices.** The league does not publish odds; prices are
   commercial products of licensed operators. Without a closing line there is no
   closing-line value, which is the project's primary anti-luck measurement.
2. **No official source for depth / "string".** `nfl.com/teams/<club>/depth-chart` returns
   HTTP 404. Club sites publish ordered depth charts but do not label 1st/2nd/3rd/4th string.

Both are on the **Flagged for Review** page with source links.

## Data captured

Verified from official sources on 2026-11-14 (2026 regular season, Week 10):

- Standings for all 32 clubs — `https://www.nfl.com/standings/`
- Week 10 schedule, 14 games plus the official bye list — `https://www.nfl.com/schedules/2026/REG10`
- 345 official injury-report rows — `https://www.nfl.com/injuries/`
- Roster and elevation rules — `https://operations.nfl.com/calendar-events/nfl-free-agency/contract-language`
- Injury-report designation definitions, gambling policy, and league news used for
  personnel notes — see the Source Register page on the site.

## Working in parallel

Read `COORDINATION.md` first. Claim a task with your session ID and file scope, commit and
push that claim immediately, and never start a task another session has claimed. Shared
outputs (`docs/data/*`, `docs/index.html`, `docs/assets/nav.js`) are owned by the final
integration session.

## Not wagering advice

This repository contains no wagering advice and places no wagers. Several of the documents
describe *proposed* methods that have not been tested.
