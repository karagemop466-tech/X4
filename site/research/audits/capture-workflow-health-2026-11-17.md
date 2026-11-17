# Scheduled official-capture workflow health review — 2026-11-17

## Executive finding

The repository has a scheduled official-source capture workflow, but its scheduled runs are currently failing before the verification, freshness, and commit steps. The checked-out `main` tree has no `data/captures/` directory or manifest. Therefore, this checkout contains no durable capture history from this workflow, and the site must not claim that the multi-day point-in-time availability series is operational.

The exact underlying fetch/schema failure is **unknown**. The GitHub run/job metadata confirms which step failed, but the Actions log payload could not be retrieved in this environment (the `gh run view --log` download terminated with `EOF`). No cause is guessed here.

## Verified operational facts

| Finding | Evidence | State |
|---|---|---|
| The workflow is scheduled every six hours and can also be manually dispatched. | [Workflow source](https://github.com/karagemop466-tech/X4/blob/main/.github/workflows/capture.yml) | Verified in the committed workflow |
| The workflow is intended to capture the NFL injury page and club depth pages, then verify hashes, check freshness, and commit captures. | [Workflow source](https://github.com/karagemop466-tech/X4/blob/main/.github/workflows/capture.yml); [capture implementation](https://github.com/karagemop466-tech/X4/blob/main/tools/capture_official.py) | Verified in repository code |
| Four most recent scheduled capture runs visible on 2026-11-17 failed: run 44175196682 (Nov 17 21:00 UTC), 44043083196 (Nov 17 08:00 UTC), 43967865851 (Nov 16 22:13 UTC), and 43818369872 (Nov 16 06:40 UTC). | [Run 44175196682](https://github.com/karagemop466-tech/X4/actions/runs/44175196682), [run 44043083196](https://github.com/karagemop466-tech/X4/actions/runs/44043083196), [run 43967865851](https://github.com/karagemop466-tech/X4/actions/runs/43967865851), [run 43818369872](https://github.com/karagemop466-tech/X4/actions/runs/43818369872) | Verified from GitHub Actions run metadata |
| In all four runs, the failing step was “Fetch, schema-check and store the official pages”; hash verification, freshness, and commit steps were skipped. | Each linked run's GitHub Actions job metadata, job “capture” | Verified from GitHub Actions job/step metadata |
| The latest successful Pages build/deploy checks visible in the run list are from Nov 15; the four capture failures are separate from that successful site deployment. | [Successful publish run](https://github.com/karagemop466-tech/X4/actions/runs/43749149785), [successful Pages deployment](https://github.com/karagemop466-tech/X4/actions/runs/43749149790), [successful desk validation](https://github.com/karagemop466-tech/X4/actions/runs/43749149800) | Verified from GitHub Actions metadata |
| In the audited checkout, `data/captures/` and `data/captures/manifest.jsonl` do not exist. | Local file check at `fb8a6cb91b69cf8ff152bda096591f55557844e8`; this is the same commit as the current `origin/main` at audit start. | Verified for this checkout only; not a claim about external backups |

## Confirmed design risks in the current workflow

These are code-path findings, independent of the unknown live failure cause:

1. **A failed fetch step prevents the later commit step from running.** `tools/capture_official.py fetch --kind all` can write a successful source's capture and manifest line before it exits non-zero because another source failed. In GitHub Actions, the later verification/freshness/commit steps have no `if: always()` condition. A partial successful capture can therefore remain only in the ephemeral runner and be lost when the job ends.
2. **The current freshness check is not per source and does not require success.** `freshness()` takes the maximum `fetched_utc` over every manifest entry. It does not require `schema_ok`, a stored file, or a recent successful capture for each source. An error entry with a recent timestamp could count as fresh if the workflow later runs the check after a partial failure.
3. **The current failure report does not establish the failure category in the published data.** The workflow fails loudly, which is preferable to silently publishing malformed data, but the capture manifest is absent from this checkout and no durable per-run source-status artifact is committed. A failure alert must include source, failure class, timestamp, and the relevant response/schema diagnostics without representing failed reads as successful snapshots.

These findings do **not** establish whether the current failures are network errors, source changes, or schema mismatches. The run logs are needed to distinguish those causes.

## Questions that remain unanswered (do not infer)

- Which target URL first fails in each run?
- Are failures HTTP/network errors, a challenge/interstitial response, or a schema-marker mismatch?
- Did any source succeed in a failed `--kind all` run, and if so, was that partial capture discarded as the code path suggests?
- Can the official source be captured with the existing parser under the runner's actual response body, and what stable versioned schema should be checked?
- Is the raw capture retention policy appropriate for the source terms? The workflow currently checks in the raw compressed bytes; this review does not determine permission to retain or redistribute them.

## Recommended recovery sequence (no owner input required to implement diagnostics)

1. Retrieve and archive the failing step logs for the four runs; classify each source outcome from its actual log. Keep the failure cause marked unknown until then.
2. Change capture execution to report every target's status, schema result, UTC time, URL and hash (where bytes were received) in a durable run summary. Never label a failed or schema-invalid fetch as a valid capture.
3. Make persistence semantics explicit: retain and verify valid successful source captures even if a different source fails, while returning a failing workflow status for any failed target. Avoid committing unvalidated bytes as usable snapshots.
4. Replace global freshness with per-source freshness over the latest **successful, schema-valid, hash-verified** snapshot; missing sources must fail the check.
5. Add parser/schema regression fixtures from authorized official captures and tests for an outage, one successful plus one failed target, a changed schema, an unchanged body, and missing/corrupt stored hashes.
6. After the workflow is repaired, confirm successive scheduled runs create a multi-day manifest and verified raw objects before marking immutable availability capture as operational. The capture failure is a blocker for availability-history backtests, not for unrelated site publication.
7. Ask the integration owner to surface this report and the current capture-health state on “Flagged for Review” or the decision-readiness table. This session does not change shared page generators or flag registers owned by integration.

## Scope and reproducibility

This review used only the committed workflow/script, local tree state, and GitHub Actions metadata accessed through `gh`. It did not access NFL.com from this environment, inspect the failed job's response body, edit injury/depth values, or claim official-source verification of any live injury designation.
