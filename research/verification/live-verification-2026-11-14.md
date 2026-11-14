# Live official-source verification — 2026-11-14

Session `arena/970ba0eb-x4`, task **T20** (live official-source verification
harness). This record documents an independent re-check of the committed data
against the live official NFL.com pages, captured on 2026-11-14, and the
irregularities it found.

## What was done

The committed datasets were re-checked against the **live** official NFL.com
pages (not against the values already recorded in the repo). The captures were
turned into committed snapshots under `research/verification/` and diffed
against `data/*.csv` by the new harness `tools/verify_live.py`.

```bash
python3 tools/verify_live.py all      # snapshot mode (reproducible, no network)
python3 tools/verify_live.py standings --live   # re-fetch + parse (needs network)
python3 tools/verify_live.py schedule --live
python3 tools/verify_live.py injuries
```

The harness has two modes. **Snapshot mode** (default) diffs a committed
official snapshot against the committed data and is fully reproducible offline.
**Live mode** (`--live`) re-fetches the official page over HTTPS and parses it,
for on-demand re-certification. It is deliberately **not** part of
`tools/validate.py`'s publish gate, because live fetching needs network access
and must not be able to block or race the deterministic build.

## Sources (all official, all retrieved 2026-11-14)

| Dataset | Official source | Snapshot file |
|---|---|---|
| Standings (all 32 clubs) | https://www.nfl.com/standings/ | `research/verification/standings-live-2026-11-14.csv` |
| Week 11 schedule (13 games + byes) | https://www.nfl.com/schedules/2026/by-week/week-11 | `research/verification/schedule-wk11-live-2026-11-14.csv` |
| Week 10 injury report (44-row sample) | https://www.nfl.com/injuries/ | `research/verification/injuries-wk10-live-2026-11-14.csv` |

Each snapshot row carries its own `source` URL and `retrieved` date, so any
value can be re-checked against the official page by hand.

## What was verified

### 1. Standings — all 32 clubs (PASS)

The 32 rows of `data/standings-wk10-2026.csv` were compared field by field
(W, L, T, PCT, PF, PA, NET) against the live official standings. **All 32
match on every field** (32 rows, 256 field checks).

- The NFL's winning-percentage formula `(W + 0.5·T) / G` reproduces the
  published `pct` for every club.
- NFL.com labels the Rams `LA` and the Cardinals `AZ`; the committed data keys
  them `LAR` and `ARI` (the abbreviations NFL.com itself uses in its game-page
  URLs). This is a label difference only — no value differs — and is documented
  as **F-14 / R-11**. The harness normalises the key for the value comparison
  (see `_standings_key` in `tools/verify_live.py`); the value columns are
  compared untouched.

### 2. Week 11 schedule — all 13 games (PASS)

All 13 games were compared on matchup, date, kickoff time, network, official
game-page URL and the Mexico City international designation against the live
official Week 11 schedule. **All 13 match** (13 rows, 117 field checks). The
six teams on bye (ATL, CLE, GB, LAR, NE, SEA) match the official bye list.

### 3. Week 10 injury report — 44-row sample (2 mismatches found)

A 44-row sample was captured live (WAS 9, NYG 11, NE 15, DET 9 — the four
teams the prior integration session also read individually) and compared on
player, position, injury, practice status and game status. **42 of 44 rows
match.** Two rows do **not**:

| Player | Club | Committed practice | Live official practice |
|---|---|---|---|
| Greg Van Roten (G) | NE | `Limited` | `Full Participation in Practice` |
| Charles Woods (CB) | NE | `Limited` | `Full Participation in Practice` |

Sources: committed value `data/injuries-wk10-2026.csv`; live official value
https://www.nfl.com/injuries/ retrieved 2026-11-14.

**Interpretation.** The NFL updates the public injury report during the week
(the prior integration session recorded 55 changed practice codes on one
re-fetch). The committed cells therefore reflect an earlier official snapshot;
the live page has since moved. This is a genuine data-drift finding, not a
transcription error.

**Action taken: flagged, not edited.** The committed data was deliberately left
unchanged — editing it would fork the published numbers away from the snapshot
the rest of the build was verified against. The drift is published on both
flagged registers as **F-29** (main site) and **R-14** (decision-desk layer),
with both values and both source links, so it can be reviewed and, if the
current snapshot is adopted, regenerated through the normal pipeline.

The snapshot is a **partial** capture (4 of the 28 playing teams, 44 of 345
committed rows). The harness reports the 301 un-captured committed rows as
"not covered", not as failures, so a partial sample cannot produce false
positives.

## Normalisations applied (labels only, never values)

- **Standings key:** `LA`→`LAR`, `AZ`→`ARI` (documented label difference F-14/R-11).
- **Practice status:** the official page prints full text
  ("Full Participation in Practice" / "Did Not Participate In Practice" /
  "Limited Participation in Practice"); the committed CSV stores the short code
  (`Full` / `DNP` / `Limited`). The snapshot holds the official text verbatim and
  the harness maps it to the short code for the value compare. No injury,
  position or game-status value is altered.

## Result

- Standings: **PASS** (32/32).
- Week 11 schedule: **PASS** (13/13 + byes).
- Week 10 injuries (44-row sample): **2 mismatches**, both a documented
  official-report drift; flagged as F-29 / R-14 and left for review.

The full publication gate (`python3 tools/validate.py`) **PASSES** with these
changes; the harness's injuries FAIL is a finding recorded on the flagged
pages, not a build blocker (the harness is intentionally outside the publish
gate).
