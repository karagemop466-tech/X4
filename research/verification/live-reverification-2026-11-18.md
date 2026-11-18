# Live re-verification sweep — 2026-11-18 (T46 final integration)

Session: `arena/016cf314-x4`. All reads below were made through the platform page-fetch
tool on **2026-11-18 between 03:05 and 04:00 UTC** (the sandbox's direct network is
restricted to github.com / npm / pypi, so live reads go through the fetch tool; the
committed artifacts of every read are in this directory). Nothing in the frozen corpus
or the registered forecast record was edited; every value that could not be confirmed
from an official source stays blank and flagged.

## 1. Official standings — live vs committed snapshot

Source read: <https://www.nfl.com/standings/> (2026-11-18, 03:10–03:40 UTC).
Committed: `data/standings-wk10-2026.csv`.

**Verdict: the committed snapshot is internally correct but seasonally stale.** It was
captured mid-Week 10 (before the games of 15–16 November) while its filename says
"wk10". Row by row (32 teams) in `standings-delta-2026-11-18.csv`:

- **26 teams** have one completed Week 10 game that the snapshot does not include
  (`games_added = 1` each; every W/L/T/PF/PA cell compared against the live page).
- **6 teams unchanged**: the four Week 10 bye clubs (CHI, DEN, PHI, TB) and WAS/NYG,
  whose 12 November result is already in the snapshot and in the corpus.

Exact per-team cells: `standings-delta-2026-11-18.csv` (each row sourced to
<https://www.nfl.com/standings/>).

## 2. Week 10 results — verified and staged, corpus NOT edited

Source read: official Week 10 schedule page
<https://www.nfl.com/schedules/2026/by-week/week-10> (2026-11-18, 03:47 UTC), which
prints every final score and links each game's official game page.

- Week 10 = **14 games** (byes: CHI, DEN, PHI, TB). The reconstructed corpus
  (`data/games-2026.csv`) contains **1** of them (WAS 24–NYG 21, 12 November, itself
  re-confirmed against the schedule page).
- The remaining **13 games** (15–16 November) are transcribed in
  `week10-results-staged-2026-11-18.csv`, each row carrying its official
  `nfl.com/games/...` URL, the schedule-page source, and the read clock time.
- **Arithmetic proof:** adding the 13 staged results to the committed snapshot
  reproduces the live official standings **exactly for all 32 teams** on
  W/L/T/PF/PA (0 mismatches; the four bye clubs unchanged). This is the same
  proof technique `tools/verify.py` applies to the corpus, so every staged score is
  cross-checked against the NFL's own aggregates.

**Why the corpus was not edited (decision, not an omission):**

1. The site's registered data-split statement freezes the evaluation record:
   "The published walk-forward expansion on Weeks 3–10 stands as recorded at
   registration" (`tools/pages.py`, Data split row), and
   `research/preregistration/wk11-forward-v1.md` registers the Week 11 window
   against the corpus as it stood at registration. Ingesting 13 games would move
   every registered evaluation number (the "105 out-of-sample games" of F-07 and
   `research/strategy-validation.md` become 118) inside a live registration window.
2. Defect found during this review (**F-59**): `tools/build.py` rewrites
   `data/price-snapshots.csv` on every build from the current game log, so the
   "opening fair line = the first published model line" record is **not pinned**.
   A corpus ingest would silently rewrite the recorded Week 11 opening forecasts
   — exactly what "record forecasts before kickoff" forbids.
3. Therefore expansion is staged as a **registered follow-up** (F-58): pin the
   opening snapshots (F-59), commit a dated corpus-expansion registration, then
   ingest `week10-results-staged-2026-11-18.csv` in one reviewed change.

## 3. Week 11 schedule — 13/13 fixtures re-verified live

Source read: <https://www.nfl.com/schedules/2026/by-week/week-11>
(2026-11-18, 03:50–03:58 UTC). Every fixture, date, kickoff time and network in
`data/schedule-wk11-2026.csv` matches the live page row for row (13/13), including
the Mexico City designation (MIN–SF, Sunday night) and the Monday night game
(CIN–WAS, 23 November, 8:15 PM, ESPN). Live team records on the page (e.g. BUF 8–1,
SF 8–1) also agree with the standings read above. First kickoff: IND at HOU,
Thursday 19 November, 8:15 PM ET (PRIME) — about 22 hours after this sweep.

## 4. Week 11 injury report — still not published (F-55 re-check)

Source read: <https://www.nfl.com/injuries/league/2026/reg11>
(2026-11-18, 03:55 UTC). The address **still serves the Week 10 report** — page title
"Official NFL Injury Report for Players - Week 10 of the 2026 Season", resolved URL
`/reg10` — exactly the silent fall-back F-55 records. The page's week tabs now list
WEEK 11, but no Week 11 designation is served at that address. Verdict for F-55:
**re-checked, state unchanged**; no Week 11 designation exists in any official source
read, so none is published (and the pre-registration forbids using one before it is
officially published and captured).

## 5. Capture infrastructure disposition (PR #62 / board T47)

The capture-hardening branch (arena/7db594d1-x4) was reviewed line by line and
integrated: empty chart URLs (Houston image-only) are skipped instead of raising
`ValueError`, per-source fetch exceptions are recorded in the manifest before the
run fails, freshness is evaluated per source against schema-valid HTTP 200 captures,
`previous_sha256` refers to the same source, and the workflow persists its evidence
before failing. Five offline unit tests (verified passing in this session). This
fixes both code-path risks of F-56. Its privacy request is surfaced as **F-60**.

## 6. Gate hygiene

`tools/validate.py` now fails loudly if a gate run mutates any committed dataset
(the request logged by `arena/e6ee28a8-x4`): the ingest step may rebuild data/ops
from the committed raw bodies, but a gate run that would change a tracked dataset
fails with the changed file list and restores nothing (reviewed change or revert,
never a silent append). Both paths tested.

## Sources (all fetched 2026-11-18 UTC)

| Source | URL | Used for |
|---|---|---|
| Official NFL standings | https://www.nfl.com/standings/ | §1 delta table (32 teams) |
| Official Week 10 schedule/results | https://www.nfl.com/schedules/2026/by-week/week-10 | §2 staged results (14 finals) |
| Official Week 11 schedule | https://www.nfl.com/schedules/2026/by-week/week-11 | §3 fixture check (13/13) |
| Official injury report (reg11 address) | https://www.nfl.com/injuries/league/2026/reg11 | §4 F-55 re-check |
| Official game pages (per row) | e.g. https://www.nfl.com/games/bills-at-jets-2026-reg-10 | §2 evidence links |
| Committed corpus | https://github.com/karagemop466-tech/X4/blob/main/data/games-2026.csv | §2 comparison |

## Irregularities registered by this sweep

- **F-58** — Week 10 results (13 games) verified and staged; corpus expansion blocked
  on F-59 and a dated registration.
- **F-59** — the price-snapshot "opening" record is recomputed every build
  (`tools/build.py` rewrites `data/price-snapshots.csv`), so the first-published
  model line is not pinned; blocks corpus ingest and CLV measurement.
- **F-60** — raw availability captures are committed to a public repository while
  the brief requires a private data layer for raw row-level data until the terms
  are read; surfaced for the owner's decision (the Pages artifact publishes only
  `site/`, never `data/`).
- **F-55** — re-checked 2026-11-18: unchanged (Week 11 report not served).
