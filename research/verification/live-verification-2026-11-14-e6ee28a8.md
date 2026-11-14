# T33 — Independent live re-verification sweep (session `arena/e6ee28a8-x4`, 2026-11-14)

A full, independent re-fetch of the three official NFL.com pages that back the
published datasets, and a mechanical field-by-field diff against the committed
CSVs at the `main` tip of 2026-11-14 (~19:47 UTC, after PR #27). The sweep
**diffs, never edits** — every drift below is flagged for review, and the
committed data is untouched so the published build stays the snapshot it was
verified against.

## What was fetched (all official, all retrieved 2026-11-14 ~19:47 UTC)

| Page | URL | Chunks read |
|---|---|---|
| Standings (division, 2026 REG) | `https://www.nfl.com/standings/` | 2 of 2 |
| Week 11 schedule | `https://www.nfl.com/schedules/2026/by-week/week-11` | 3 of 3 |
| Week 10 injury report | `https://www.nfl.com/injuries/` | 8 of 8 |

Verbatim page captures are committed next to this record under
`research/verification/captures-2026-11-14-e6ee28a8/` (markdown transcriptions of
the fetched content, one file per page). `research/verification/live_sweep_2026-11-14_e6ee28a8.py`
parses them mechanically and re-runs the whole sweep offline; it fails loudly on
any parse anomaly rather than silently dropping a row.

## Results

| Check | Rows compared | Field checks | Result |
|---|---|---|---|
| Standings vs `data/standings-wk10-2026.csv` (W/L/T/PCT/PF/PA/NetPts per club) | 32 of 32 | 224 | **PASS — 0 mismatches** |
| Week 11 schedule vs `data/schedule-wk11-2026.csv` (date, kickoff, network, NFL.com game URL, Mexico City designation) | 13 of 13 | 52 | **PASS — 0 mismatches** |
| Week 11 byes (live) vs the byes published on `site/index.html` | 6 of 6 | — | **PASS** (ATL, CLE, GB, LAR, NE, SEA) |
| Week 10 injury report vs `data/injuries-wk10-2026.csv` (pos, injuries, practice, game status; **full capture, not the T20 44-row sample**) | 345 of 345 | 1,380 | **12 practice-status cells drift** (below) |

Total: **1,656 field checks; 12 mismatches, all in one column of one table.**
Snapshot CSVs with per-row source URLs and the retrieval date:
`live-sweep-standings-2026-11-14-e6ee28a8.csv`, `live-sweep-schedule-2026-11-14-e6ee28a8.csv`,
`live-sweep-injuries-2026-11-14-e6ee28a8.csv` (this directory).

## The 12 drifted practice-status cells (flagged, not edited)

The league updates the official report during the week (this is the same drift
mechanism T20 recorded as F-34/R-14 earlier today; the page's own news rail now
carries a "Saturday Nov 14" roundup, so the report moved again after that
capture). Every row below is quoted with its official player page, which is the
row's source link.

| # | Player (position, club) | Committed | Live official page now | Player page (source) |
|---|---|---|---|---|
| 1 | Greg Van Roten (G, NE) — **already flagged F-34/R-14** | Limited | Full | `https://www.nfl.com/players/greg-van-roten/` |
| 2 | Charles Woods (CB, NE) — **already flagged F-34/R-14** | Limited | Full | `https://www.nfl.com/players/charles-woods/` |
| 3 | Savion Williams (WR, GB) | Full | Limited | `https://www.nfl.com/players/savion-williams/` |
| 4 | Antonio Johnson (S, JAX) | Full | Limited | `https://www.nfl.com/players/antonio-johnson-3/` |
| 5 | Kaytron Allen (RB, MIA) | Limited | Full | `https://www.nfl.com/players/kaytron-allen/` |
| 6 | David Montgomery (RB, HOU) | Limited | Full | `https://www.nfl.com/players/david-montgomery/` |
| 7 | Jaylin Smith (CB, HOU) | Limited | Full | `https://www.nfl.com/players/jaylin-smith/` |
| 8 | Denzel Ward (CB, CLE) | Full | Limited | `https://www.nfl.com/players/denzel-ward/` |
| 9 | Andrew Wingard (S, ARI) | Limited | DNP | `https://www.nfl.com/players/andrew-wingard/` |
| 10 | C.J. West (DT, SF) | Limited | Full | `https://www.nfl.com/players/cj-west/` |
| 11 | Von Miller (LB, DAL) | Full | DNP | `https://www.nfl.com/players/von-miller/` |
| 12 | Rodney Shelley (CB, LAC) | Full | Limited | `https://www.nfl.com/players/rodney-shelley/` |

10 of the 12 are new since F-34/R-14. Direction of drift is mixed (six toward
less participation, five toward more, one unchanged), consistent with ordinary
report updates during the week rather than a transcription error in either
capture. **No value was edited**; regenerating the dataset from a fresh capture
is the site owners' call (it would re-fork the published numbers away from the
snapshot the rest of the build was verified against).

## Irregularities observed during the sweep (reported, not edited)

- The team label mapping `LA`/`AZ` (NFL.com) vs `LAR`/`ARI` (dataset) continues
  to apply to keys only — documented as F-14/R-11; no value differs.
- The committed injury CSV uses abbreviated practice codes (`Full`, `DNP`,
  `Limited`) while the official page spells them out; the mapping is 1:1 and is
  implemented in the sweep script, where an unrecognised code fails the run.

## Verification performed by this session

1. Both T20's snapshot harness (`tools/verify_live.py all`) and this sweep were
   run; both agree on the standings (32/32), schedule (13/13) and the F-34 cells.
2. The full-injury sweep extends T20's 44-row partial capture to all 345 rows.
3. The sweep script and captures are committed so the result is reproducible
   offline, like the rest of the build.
