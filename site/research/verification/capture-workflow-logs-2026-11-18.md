# Capture workflow: root cause of the failing scheduled runs (2026-11-18)

Read-only diagnosis by session `arena/ad5e4c3d-x4` (task T46). No capture code and no
capture data was changed; the finding is published for the owner of
`tools/capture_official.py` and `.github/workflows/capture.yml`.

## What was observed

`gh run list --workflow capture.yml` shows four completed runs, every one a **failure**,
and nothing else:

| Run | Trigger | Started (UTC) | Finished (UTC) | Duration | Failing step |
|---|---|---|---|---|---|
| [44175196682](https://github.com/karagemop466-tech/X4/actions/runs/44175196682) | schedule | 2026-11-17T21:00:19Z | 2026-11-17T21:00:27Z | **8 s** | 4 - "Fetch, schema-check and store the official pages" |
| [44043083196](https://github.com/karagemop466-tech/X4/actions/runs/44043083196) | schedule | 2026-11-17T08:00:30Z | 2026-11-17T08:00:38Z | **8 s** | 4 - same |
| [43967865851](https://github.com/karagemop466-tech/X4/actions/runs/43967865851) | schedule | 2026-11-16T22:13:07Z | — | — | 4 - same |
| [43818369872](https://github.com/karagemop466-tech/X4/actions/runs/43818369872) | schedule | 2026-11-16T06:40:27Z | — | — | 4 - same |

Facts taken from the Actions API (`/actions/runs/<id>/jobs`), not from the log text:
every run fails at step 4 and steps 5-7 (verify, freshness, commit) are `skipped`, so
**no capture was ever stored and no manifest line was ever written**. `data/captures/`
does not exist in the repository, which is consistent with that.

## What the 8-second duration rules out

`fetch --kind all` builds **33 targets**: one injury-report URL plus one URL for each of
the 32 clubs in `tools/depth.py` `CHART_URL`. They are fetched **sequentially**, each with
`urllib.request.urlopen(..., timeout=60)`. A network failure on even one of them could not
finish the whole command in 8 seconds. The command therefore aborted rather than exhausted
its fetches.

## The root cause

`tools/depth.py` line 71 sets the Houston chart URL to the **empty string**:

```python
# Houston publishes the chart as a single image: no machine-readable order.
"HOU": "",
```

`tools/capture_official.py` `fetch()` iterates `sorted(depth_module.CHART_URL)` and passes
each value straight into its `http_get()`, whose first statement builds
`urllib.request.Request(url, ...)` with that value. Python raises
`ValueError: unknown url type: ''` for an empty URL, and **`ValueError` is not in the
`except (urllib.error.URLError, OSError, TimeoutError)` tuple** around the call, so the
exception propagates out of `fetch()`, out of `main()`, and terminates the step.

Both halves were reproduced in this session against the committed tree:

```
$ python3 -c "urllib.request.Request('')"
ValueError: unknown url type: ''
$ python3 -c "import tools.depth as d; print([t for t in ... if not t[1]])"
[('depth/HOU', '')]
```

`HOU` sorts between `GB` and `IND`, i.e. **11th of the 32 club targets**. Eleven
request/parse cycles on a warm GitHub runner fit an 8-second budget; 33 do not. That is
the whole observed behaviour, and it explains why the failure is identical and immediate
on every scheduled run.

## Why the earlier audits could not see it

F-47, F-48 and F-56 record the failure and call the cause **unknown**. The log text for
these runs is not retrievable from this environment: `gh run view --log-failed` and
`gh api .../jobs/<id>/logs` both return `EOF` from the Azure blob storage that serves
action logs (the signed URL downloads zero bytes). The conclusion above is therefore drawn
from **code + step outcome + duration**, not from the log line. It is stated as the
mechanism consistent with all three observations, and the one line of log that would
confirm it (`FETCH FAILED` is never printed, and the traceback ends at
`capture_official.py` -> `urllib/request.py`) is the check a reviewer should make when the
log service allows it.

## The minimal repair (not applied here)

Skip empty URLs instead of fetching them, and treat the Houston gap as the already-flagged
data limitation it is:

```python
for club in sorted(depth_module.CHART_URL):
    url = depth_module.CHART_URL[club]
    if not url:
        append_manifest({"kind": "depth/" + club, "url": None, "fetched_utc": iso(utc_now()),
                         "http_status": None, "skipped": "no machine-readable chart published",
                         "schema_ok": False})
        continue
    targets.append(("depth/" + club, url, schema_depth))
```

and add `ValueError` to the caught exceptions so a malformed URL fails that one source
rather than the whole job. The second change is defence in depth: without the first, the
`ValueError` path is exactly how this job has been failing.

The repair sits inside another session's file scope (`tools/capture_official.py`), so it is
logged here and on the brief register as irregularity **I-C** rather than edited.

## Sources

- [Run 44175196682](https://github.com/karagemop466-tech/X4/actions/runs/44175196682) and its
  job `134364580939` (per-step conclusions, `/actions/runs/44175196682/jobs`).
- [Run 44043083196](https://github.com/karagemop466-tech/X4/actions/runs/44043083196) and its
  job `133902129401`.
- `tools/depth.py` lines 71 (empty `HOU`) and 58-91 (`CHART_URL`, 32 clubs).
- `tools/capture_official.py` `fetch()`, `http_get()`, and the `except` tuple in `fetch()`.
- Github check-run annotations for the failing jobs, which carry only
  "Process completed with exit code 1" against the workflow file, no traceback.
