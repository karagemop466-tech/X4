# Week 11 official injury capture: freshness failure, F-55 correction, board audit

Task: T60 (session `arena/cd239f59-x4`). Retrieved 2026-11-19 (UTC).
Scope: diagnosis and logging only. No schema was changed, no Week 11 designation was transcribed or inferred, and no published value was edited.

## 1. What the official source shows today

| Check | Result | Source |
|---|---|---|
| The NFL.com injury page now carries the Week 11 report | Title: "Official Latest NFL Injury Report for Players - Week 11 of the 2026 Season". Heading "Injuries - WEEK 11". The first of seven rendered chunks lists Thursday, November 19 (8:15 PM EST, Prime Video) Colts at Texans, then Sunday, November 22 (1:00 PM EST, CBS) Steelers at Eagles and Cardinals at Chiefs. The remaining chunks were not read, so the total number of game sections is not verified here. | https://www.nfl.com/injuries/ |
| The Week 11 league address serves the Week 11 report | Title: "Official NFL Injury Report for Players - Week 11 of the 2026 Season". | https://www.nfl.com/injuries/league/2026/reg11 |
| The repository still holds only the Week 10 injury report | `data/injuries-wk10-2026.csv`; `data/output/availability.json` | repository |

This contradicts F-55, which said on 2026-11-17 that the Week 11 report was unpublished. F-55 is updated in `tools/content.py` with a dated note. Its original text is kept.

## 2. The scheduled capture is failing on `main`

| Evidence | Value | Source |
|---|---|---|
| Latest scheduled run of "Official capture (injury report and club depth pages)" on `main` | Run 44393037693, failure. The failing step is "Fail after preserving capture diagnostics", which runs after the freshness step failed. The other steps succeeded. | `gh run view 44393037693 --json jobs` (repository run record) |
| Previous scheduled run | Run 44260352677, failure, same failing step | same |
| Run-log download | Failed (`results-receiver ... EOF`). The step-level cause was therefore read from step outcomes and the committed manifest, not from the log text. | `gh run view --log-failed` |

Injury entries in the committed manifest (`data/captures/manifest.jsonl`, `kind: injuries`):

| Fetched (UTC) | HTTP | Schema OK | Week heading | Practice-status markers (need >= 28) | Game-status markers (need >= 28) | Player links (need >= 250) |
|---|---|---|---|---|---|---|
| 2026-11-18T03:39:04Z | 200 | False | 10 | 28 | 28 | 0 |
| 2026-11-18T03:40:10Z | 200 | True | 10 | 28 | 28 | 347 |
| 2026-11-18T03:44:00Z | 200 | True | 10 | 28 | 28 | 347 |
| 2026-11-18T07:37:40Z | 200 | False | 11 | 2 | 2 | 26 |
| 2026-11-18T20:37:55Z | 200 | False | 11 | 2 | 2 | 26 |

The schema is in `tools/capture_official.py`, function `schema_injuries`. It requires the heading and at least 28 practice-status markers, 28 game-status markers and 250 player links. The Week 10 pin was verified against a Week 10 raw page. Week 11 raw pages match the heading but not the counts.

Reproduced locally from the committed manifest:

```
python3 tools/capture_official.py freshness --kind injuries --max-hours 13
injuries     2026-11-18T03:44:00Z (27.2 hours ago); limit 13.0
freshness failed for 1 of 1 expected sources      (exit 1)
```

`python3 tools/capture_official.py verify` reports 0 failures.

## 3. Cause: not confirmed

The raw bytes are kept in a private store (`X4_CAPTURE_RAW_DIR`), which CI does not set, and this sandbox cannot reach nfl.com (`curl` to https://www.nfl.com/injuries/ returns no HTTP code). The raw HTML therefore cannot be inspected here.

A plausible explanation is that the Week 11 page renders some game days only after the first, so the raw HTML carries 2 practice-status tables and 26 player links, roughly one game. This is a hypothesis, not a finding. It is consistent with the manifest counts, but it has not been checked against the raw bytes.

## 4. What was not done, and why

- The schema was not loosened. The stored reads show the alarm doing its job: the freshness gate refused a read it could not validate.
- No Week 11 injury row was transcribed. Doing that by reading the page would be manual transcription of about 250 rows, which the verification policy does not allow for published values.
- The last valid Week 10 read was not replaced.

## 5. Options for review (none applied)

1. Record the count of game-status sections in each raw read in the manifest. This shows the drift without retaining raw bytes.
2. Rewrite the schema for the current NFL.com layout, verified against a live raw read taken inside CI. This needs a run with the raw store configured.
3. Keep the schema and accept that the injury data is stale until option 1 or 2 is done.

## 6. Irregularities logged

- F-55 corrected (the Week 11 report is now published on NFL.com; the repository is behind).
- F-83 added: the capture failure described in section 2.
- Board integrity logged on COORDINATION.md only (not on the public register, which requires an official source link on every row): eight identifiers used on more than one row, and T37 recorded as both done and in progress. Not edited, because the rows belong to earlier sessions.

## 7. Links for manual review

- https://www.nfl.com/injuries/
- https://www.nfl.com/injuries/league/2026/reg11
- https://github.com/karagemop466-tech/X4/actions/runs/44393037693
- https://github.com/karagemop466-tech/X4/actions/runs/44260352677
- https://github.com/karagemop466-tech/X4/blob/main/tools/capture_official.py
- https://github.com/karagemop466-tech/X4/blob/main/data/captures/manifest.jsonl
- https://github.com/karagemop466-tech/X4/blob/main/COORDINATION.md
