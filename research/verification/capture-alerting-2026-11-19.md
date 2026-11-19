# Capture alerting and cadence evidence (T67)

Session: `arena/6870a878-x4`, 2026-11-19 UTC. Board: `COORDINATION.md` row T67. Flags: F-88 (no alert channel), F-89 (cadence gap).

## Question

The brief asks the capture system to "monitor freshness and alert on source/schema changes", and to snapshot the official injury report on a schedule from Wednesday to kickoff. Two things had to be checked before any change:

1. Does any workflow alert when a capture is stale, missing or fails its schema gate?
2. Do the scheduled captures run on their stated cadence?

## Evidence, and how each item was checked

| Claim | Evidence | Checked how |
|---|---|---|
| No workflow raises an alert on a stale or failed capture | `.github/workflows/*.yml` on `main` at `06dcc0d`: no `issues`, `gh issue`, or notification step | `grep -rn "issue\|alert\|notify" .github/workflows/` returned nothing before this session |
| The capture job runs every six hours | `.github/workflows/capture.yml`: `cron: "17 */6 * * *"` | read from the file |
| Six injury reads span 27.9 hours, with gaps of 3.9 h, 13.0 h and 10.9 h | `data/captures/manifest.jsonl`, `kind == "injuries"` (six lines, distinct `fetched_utc`) | computed from the manifest; table below |
| Scheduled runs on `main` | `gh run list --workflow capture.yml` | run IDs listed below |
| Workflow dispatch is not available from the build sandbox | `gh workflow run capture.yml --ref main` returned HTTP 403 "Resource not accessible by integration" | command run 2026-11-19 19:30Z |
| The Week 11 injury page is live, titled Week 11 | https://www.nfl.com/injuries/ (live read through the page-fetch tool, 2026-11-19 ~19:29Z) | read directly; the sandbox cannot reach nfl.com from bash |
| GitHub notifications for scheduled workflows go to the workflow's creator, only if they have notifications enabled | https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs (read 2026-11-19) | read directly |
| GitHub says the schedule event can be delayed under high load and that queued jobs may be dropped | https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule. The quotation was confirmed through the community discussion https://github.com/orgs/community/discussions/210361, which quotes the page. The schedule section itself was **not** in the chunk fetched here. | partly verified: quotation confirmed via a quoting source |

### Manifest cadence (injuries source)

| # | Read (UTC) | Gap from previous read | Schema result | Coverage recorded |
|---|---|---|---|---|
| 1 | 2026-11-18 03:39:04 | - | failed (0 player links) | - |
| 2 | 2026-11-18 03:40:10 | 0.0 h | passed (Week 10, 347 links) | - |
| 3 | 2026-11-18 03:44:00 | 0.1 h | passed, unchanged re-read | - |
| 4 | 2026-11-18 07:37:40 | 3.9 h | failed (Week 11, 26 links) | - |
| 5 | 2026-11-18 20:37:55 | 13.0 h | failed (Week 11, 26 links) | - |
| 6 | 2026-11-19 07:33:33 | 10.9 h | passed (Week 11, 253 links) | partial, 12 of 13 games |

Mean interval across the five gaps after the first read: 5.6 hours. The cron implies about 6 hours. Scheduled runs on `main`, from `gh run list`: 44260352677 (2026-11-18T07:37:35Z, failure), 44393037693 (2026-11-18T20:37:49Z, failure), 44480508108 (2026-11-19T07:33:18Z, success). No scheduled capture is recorded after 07:33Z on 2026-11-19 at the time of writing (19:30Z).

## What was built

- `tools/capture_alert.py`: reads the committed manifest, reuses `capture_official.read_manifest`, `expected_kinds` and the same validity test as `freshness`, and classifies each of the 32 expected sources (injuries plus 31 club charts) as OK, PARTIAL, STALE, FAILED_LAST or MISSING. Exit 1 on STALE, FAILED_LAST or MISSING. Writes no data.
- `tests/test_capture_alert.py`: 16 offline tests (every status, the inclusive limit, error records, bad timestamps, report rendering, exit codes, unreadable manifest).
- `.github/workflows/capture-watchdog.yml`: runs every three hours at minute 43, runs the offline tests, runs the check, and keeps one open issue titled "Official capture alert" (created, or commented on if open), closing it on recovery. Permissions: `contents: read`, `issues: write`. It writes nothing to the repository.
- `tools/validate.py`: one added step runs the watchdog's offline tests in the publication gate.

## Verification run in this session

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests -p 'test_capture_alert.py'` | 16 tests, OK |
| `python3 -m unittest discover -s tests -p 'test_capture_official.py'` | unchanged, OK (one test skipped by design: the private raw capture is not retained) |
| `python3 tools/capture_alert.py check --now 2026-11-19T19:45:00Z` | exit 0; injuries PARTIAL (12 of 13 games, 12.2 h old); 31 club charts OK (12.2 h old) |
| `python3 tools/capture_alert.py check --now 2026-11-20T08:00:00Z` | exit 1; 32 of 32 sources STALE (24.4 h old) |
| `gh issue list --state open ... --jq ...` (the query the workflow uses) | runs cleanly; no open alert issue |
| YAML parse of `capture-watchdog.yml` (PyYAML in a scratch venv) | parses; triggers `schedule` and `workflow_dispatch`; permissions `contents: read`, `issues: write` |

## Not verified, and why

- **The watchdog has not run on GitHub.** Scheduled workflows run only from the default branch, and this session cannot dispatch workflows (HTTP 403). Its first live run on `main` after the merge is the confirmation. Until then, no alert claim is made as verified.
- **The cause of the 13.0-hour gap is not determined.** The run logs do not record why a scheduled run was not created. The delay is consistent with GitHub's documented behaviour, but it is not proven to be that.
- **Week 11 injury rows are not in the repository.** The latest capture is partial (12 of 13 games). No Week 11 designation is transcribed or inferred here.

## Irregularities for review (published on Flagged for Review as F-88 and F-89)

- F-88: no alert channel existed before this change.
- F-89: the scheduled capture did not hold its six-hour cadence in the measured window.
- F-85 (existing): the publication gate still passes while a source is stale. This change does not alter the gate, by design: a stale source is flagged, not used to block publication.

## Requests logged on the board (not edited here)

- Owner of the capture task: consider a second, more frequent cron, or a retry when a scheduled run is missing from the manifest. This would change `capture.yml`, which is outside this session's scope.
- Owner of the capture task: the manifest carries no coverage field for the Week 10 reads, so the coverage check cannot compare them against the schedule. Recording one would make PARTIAL checkable for every week.
