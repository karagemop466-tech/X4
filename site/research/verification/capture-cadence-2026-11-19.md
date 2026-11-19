# Scheduled official-capture cadence audit — 2026-11-19

Task: T66 (session `arena/f138e625-x4`). Scope: evidence only. No captured value, no
published number and no workflow setting was changed by this record.

## Question

The capture workflow (`.github/workflows/capture.yml`) is declared to run every six hours.
Is it actually running on that cadence, and how much freshness margin does the
13-hour freshness gate leave?

## What the workflow declares

`.github/workflows/capture.yml`, line 17:

```yaml
schedule:
  - cron: "17 */6 * * *"
```

That is minute 17 of hours 00, 06, 12 and 18 UTC. The freshness step runs with
`--max-hours 13` (`tools/capture_official.py freshness --kind all --max-hours 13`).

## What GitHub documents about the schedule event

GitHub Docs, "Events that trigger workflows", section `schedule`
(<https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule>),
states, in the note at the top of the section:

> The `schedule` event can be delayed during periods of high loads of GitHub Actions
> workflow runs. High load times include the start of every hour. If the load is
> sufficiently high enough, some queued jobs may be dropped. To decrease the chance of
> delay, schedule your workflow to run at a different time of the hour.

The same section states that scheduled workflows run only on the default branch, and that
in a public repository they are disabled after 60 days without repository activity.

## What actually ran (GitHub Actions run list, `gh run list --workflow=capture.yml`)

Every run whose event is `schedule`, most recent first. Run links use the pattern
`https://github.com/karagemop466-tech/X4/actions/runs/<id>`.

| Created (UTC) | Conclusion | Run ID | Head commit | Offset from nearest cron slot |
|---|---|---|---|---|
| 2026-11-19 07:33:18 | success | 44480508108 | c62f3aa | +1 h 16 min after the 06:17 slot |
| 2026-11-18 20:37:49 | failure | 44393037693 | 752acca | +2 h 20 min after the 18:17 slot |
| 2026-11-18 07:37:35 | failure | 44260352677 | d71c388 | +1 h 20 min after the 06:17 slot |
| 2026-11-17 21:00:15 | failure | 44175196682 | fb8a6cb | +2 h 43 min after the 18:17 slot |
| 2026-11-17 08:00:28 | failure | 44043083196 | fb8a6cb | +1 h 43 min after the 06:17 slot |
| 2026-11-16 22:13:03 | failure | 43967865851 | fb8a6cb | +3 h 56 min after the 18:17 slot |
| 2026-11-16 06:40:25 | failure | 43818369872 | fb8a6cb | +23 min after the 06:17 slot |

Observations, each checkable with the command above:

1. No scheduled run has been created at a `:17` minute. Creation times lag the nominal slot
   by 23 minutes to almost 4 hours.
2. Between the 07:33:18Z run and the time of this record (about 19:30Z on 2026-11-19), no
   scheduled run is recorded. The 12:17Z and 18:17Z slots of 2026-11-19 produced no run
   record. The observed gap is about 12 hours, against a declared six.
3. Six of the seven scheduled runs failed. Only two of those failures can be tied to a
   manifest row: the reads at 2026-11-18T07:37:40Z and 20:37:55Z are `injuries` reads of the
   Week 11 page that failed the schema gate (`week: 11`, 2 status headers, 26 player links;
   see `data/captures/manifest.jsonl`). That is the condition already recorded as F-83 and
   T60/T63. The 2026-11-16 and 2026-11-17 failures have **no manifest row**, and
   `gh run view <id> --log-failed` returned `EOF` for the three of them checked
   (43818369872, 43967865851, 44175196682), so their cause is **unverified**.
4. The only successful scheduled run in this list is the one at 07:33:18Z. Its manifest
   rows are the 14 depth-chart reads (`depth/*`) with `fetched_utc` 2026-11-19T07:33:33Z to
   07:33:34Z, all HTTP 200 and `schema_ok: true`. This record does not check the other
   schedule-independent reads.

## Freshness margin (reproduced)

Running `python3 tools/capture_official.py freshness --kind all --max-hours 13` at
2026-11-19 19:28Z reported:

```
freshness passed for all 32 expected sources
```

with each source at 11.9 hours. The gate therefore passes now but reaches its 13-hour limit
at about **20:33Z on 2026-11-19**. The schedule has no run record that would refresh it
before then, based on the observed cadence above.

## What this does and does not show

- It shows the scheduled cadence is not the declared six-hour cadence, and that the 13-hour
  gate has very little margin under the observed behaviour.
- It does not show that the platform is failing permanently. GitHub's documentation
  describes this as a normal delay mode, not an outage. A later run may appear at any time.
- It does not change any captured value. The manifest is unchanged by this record.

## Options for the owner (recorded, not implemented)

These are decisions for the capture owner. This record does not make them.

1. Move the cron minute away from the top of the hour, as the GitHub documentation
   suggests (for example, a minute such as `23` or `37`). This lowers the risk of dropped
   runs. It does not guarantee a cadence.
2. Shorten the cron interval (for example every three hours) so one missed slot does not
   exhaust the freshness margin. This increases the number of commits to `main`.
3. Keep the 13-hour gate but add a second trigger source that does not depend on the
   schedule event, for example a `workflow_dispatch` called by an external job. This needs
   an external scheduler, which the sandbox does not have.
4. Record missed slots in the manifest so the gap is visible on the public Flagged page
   rather than only in the Actions list.

## Sources

- GitHub Docs, "Events that trigger workflows", `schedule` section:
  <https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule>
- Workflow definition: `.github/workflows/capture.yml` in this repository
  (<https://github.com/karagemop466-tech/X4/blob/main/.github/workflows/capture.yml>)
- Run list: `gh run list --workflow=capture.yml` on 2026-11-19 (run IDs in the table above)
- Manifest: `data/captures/manifest.jsonl` (<https://github.com/karagemop466-tech/X4/blob/main/data/captures/manifest.jsonl>)

## Irregularities flagged

- **Irregular scheduled cadence** (this record): observed gaps of about 12 hours against a
  six-hour cron, and no scheduled run recorded for the 12:17Z and 18:17Z slots of 2026-11-19.
- The 13-hour freshness gate is reached at about 20:33Z on 2026-11-19 unless a run lands.
- **Unverified failure cause** for the scheduled runs of 2026-11-16 and 2026-11-17 (no manifest
  row; GitHub run logs not retrievable from this sandbox at the time of the audit).
