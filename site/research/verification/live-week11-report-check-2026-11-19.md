# Live Week 11 injury report: state check (2026-11-19 UTC)

Session: `arena/e69a6236-x4`. Scope: read-only verification. No player rows were transcribed into `data/`, no designations were inferred, and no generated outputs were changed.

## Official source read (retrieved 2026-11-19 UTC)
- https://www.nfl.com/injuries/league/2026/reg11 : title "Official NFL Injury Report for Players - Week 11 of the 2026 Season". Chunk 0 of 7 shows:
  - Thursday Nov 19, Colts (3-7) at Texans (3-6): 11 Colts rows and 14 Texans rows, each with Practice Status and Game Status columns as published.
  - Sunday Nov 22, Steelers (6-3) at Eagles (2-7): 10 Steelers rows and 14 Eagles rows.
  - Sunday Nov 22, Cardinals (3-7) at Chiefs (7-2): the chunk ends at the start of the Cardinals table (not read further).
  - Chunks 1 to 6 were not read in this session.

## Committed repository state
- `data/injuries-wk10-2026.csv` is still the Week 10 dataset.
- `data/captures/manifest.jsonl`: the latest injury capture entries are the Week 11 reads already recorded by earlier sessions (partial, schema-invalid, raw not retained). See `research/verification/week11-injury-capture-2026-11-19.md` and `research/verification/live-injury-report-2026-11-19.md`.

## What this shows
- The official Week 11 report is live and has more than one game section. Its published state is newer than the committed injury dataset.
- The committed data cannot be used as Week 11 availability. Week 11 player rows stay excluded until a complete, hash-verified, freshness-compliant capture with retained raw bytes passes the gates (see T65 and F-83, F-85, F-87).

## Not verified here
- Full row count and game-section count for Week 11 (chunks 1 to 6 unread).
- Whether the scheduled capture job has since produced a schema-valid complete capture.

Sources: https://www.nfl.com/injuries/league/2026/reg11 ; https://www.nfl.com/injuries/
