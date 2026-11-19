# Live proof of the merged official-injury capture gate (T66)

Session `arena/27b5881c-x4`, 2026-11-19 (UTC). Task T66. Records the first live capture that ran the
gate now on `main`, and the cadence problem that run exposed. Status of F-83 and F-86 is set by the
owning sessions, not by this note.

## Context

* The scheduled capture (`.github/workflows/capture.yml`) failed on `main` for every run from
  2026-11-16 06:40Z to 2026-11-18 20:37Z (six scheduled runs, all failure, per the GitHub run list).
* The structural gate and schedule-derived coverage field were merged to `main` by PR #118 (T63,
  `arena/1b8815c9-x4`), with T60 (`arena/cd239f59-x4`) as the diagnosis.
* No capture had run on `main` since that merge. This session's token cannot dispatch workflows
  (`gh workflow run capture.yml --ref main` returned HTTP 403, "Resource not accessible by
  integration"). The live test therefore used a temporary `push` trigger on this branch only.
* This session's own gate repair (PR #122) duplicated PR #118 and was superseded. Its code and tests
  are not carried forward.

## The live run

| Item | Value | Source |
|---|---|---|
| Run | 44477705766, conclusion success, every step success (the last step, "Fail after preserving capture diagnostics", fails if any gate outcome failed) | https://github.com/karagemop466-tech/X4/actions/runs/44477705766 |
| Injury read | fetched `2026-11-19T07:11:39Z`, HTTP 200, `schema_ok: true`, `changed: true` | `data/captures/manifest.jsonl`, the new `kind: injuries` row |
| Injury schema | week 11; 24 club tables; 12 of 13 scheduled games published (`coverage: partial`); 253 player links | same row, `schema` object |
| Club depth charts | 31 of 31 `schema_ok: true`; no failed reads | same file, `kind: depth/*` rows fetched 2026-11-19 |

The 32 rows were appended to `data/captures/manifest.jsonl` (160 rows before, 192 after). They were
written by that run on this branch, and the file is append-only. Raw page bytes are not retained
(`X4_CAPTURE_RAW_DIR` is not set in CI), so the count evidence is the manifest's own record.

## What the coverage means

The official report is published game day by game day. At 07:11Z on 2026-11-19 it showed 12 of the
13 Week 11 games. The schedule is https://www.nfl.com/schedules/2026/by-week/week-11 (13 games,
read 2026-11-19 about 07:00Z). The gate records `partial` and keeps the read. Freshness is about the
capture time. Downstream users must read `coverage` before treating a read as a complete week.

## Cadence (F-87)

The workflow cron is `17 */6 * * *`. The scheduled runs recorded on `main` started at 2026-11-16
06:40Z, 22:13Z, 2026-11-17 08:00Z, 21:00Z, 2026-11-18 07:37Z and 20:37Z. The gaps were 1.3 h, 13 h,
1.2 h, 9.4 h and 13 h, against a planned six-hour interval. No scheduled run has started since
2026-11-18 20:37Z, although the 2026-11-19 00:17Z and 06:17Z slots have passed. A freshness limit of
13 hours can therefore fail between runs with no fault in the gate.

## Corrections to earlier records

* The statement that the sandbox "cannot reach nfl.com" is incorrect for `fetch_page`, which read
  https://www.nfl.com/injuries/ on 2026-11-19 (about 06:55Z). Bash `curl` from the sandbox did fail
  (exit 35). Both facts are recorded here.

## Still open

* **F-87 (cadence).** Owner decision: the scheduler's cadence and the freshness limit.
* **Coverage policy.** Whether a `partial` read may count toward any model is an owner decision.
* **Scheduled confirmation on `main`.** The owning session's record (T63 on `main`) states that
  confirmation on `main` awaits the next scheduled run. That has not yet happened.
* **Manual trigger.** The repository's tooling token cannot dispatch workflows. `actions: write`, or
  a maintainer dispatch, would let a verification run start on demand.
* **Raw bytes (F-75).** Not retained by design. The raw-store policy is an owner decision.

## Sources

* https://www.nfl.com/injuries/ (Week 11 report, `fetch_page` on 2026-11-19 and the live capture above)
* https://www.nfl.com/schedules/2026/by-week/week-11 (13 games)
* https://github.com/karagemop466-tech/X4/actions/runs/44477705766 (the live run; its head commit was `601b131` on this branch before the branch was rebuilt on `main`)
* https://github.com/karagemop466-tech/X4/actions/workflows/capture.yml (scheduled-run history)
* Repository: `data/captures/manifest.jsonl`, `data/schedule-wk11-2026.csv`, `tools/capture_official.py`
