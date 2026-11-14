# T32 — Reproduction and repair of the failing `Publish NFL Decision Lab` gate

Session `arena/e6ee28a8-x4`, 2026-11-14. Task claimed in `COORDINATION.md` as **T32**.

## Symptom

Every push to `main` since the PR #25 merge fails the `Publish NFL Decision Lab`
workflow at the step **"Confirm the published output is reproducible"**
(`git diff --exit-code -- site data research *.html *.css *.js` after a full
rebuild). Affected runs at the time of diagnosis:

| Run | Commit | Result |
|---|---|---|
| 43632180903 | PR #21 merge | success (last green publish) |
| 43632545850 | PR #25 merge | **failure** — reproducibility step |
| 43632743606 | PR #24 merge | cancelled (concurrency group) |
| 43632761165 | PR #23 merge (then `main` tip) | **failure** — reproducibility step |
| 43633294336 | PR #27 merge | **failure** — reproducibility step |

The legacy `pages build and deployment` and the `Desk validation` workflow stayed
green, so the site itself kept publishing; the strict byte-for-byte gate is what
went red.

## Reproduction (exact, not inferred)

CPython **3.12.9** was built from source in the session sandbox
(`codeload.github.com/python/cpython` tag `v3.12.9`, `./configure --prefix`,
`make -j2`) to match the workflow's `actions/setup-python` pin of `3.12`, and the
workflow's rebuild sequence was executed with each interpreter in turn on the
`main` tip `6014d73`:

```
python3 tools/verify.py
python3 tools/market_store.py
python3 tools/build.py
python3 tools/pages.py
python3 tools/sync.py
git diff --exit-code -- site data research '*.html' '*.css' '*.js'
```

Result before the fix:

| Interpreter | Sequence result |
|---|---|
| Python 3.11.2 (sandbox system python, same as the authors') | clean |
| Python 3.12.9 (CI's version) | **`data/output/market_store.json` differs, 62/62 lines** |

The differing bytes are last-ULP floating-point drift, e.g.
`data/output/market_store.json` for the Week 11 Colts–Texans card:

| Field | Python 3.11.2 | Python 3.12.9 |
|---|---|---|
| `side.fair` | `4.054587529287197` | `4.054587529287204` |
| `side.band[1]` | `9.277258391493355` | `9.277258391493348` |
| `side.spread_sd` | `2.861723998209677` | `2.861723998209676` |
| `total.fair` | `48.891640899567456` | `48.89164089956745` |

No HTML page differed — the rendered site rounds before printing — only the
machine-readable JSON store carries full-precision floats, which is why the gate
failed while the site kept publishing.

## Root cause

`tools/market_store.py` (`write_output()`) serialises the origination card with
full-precision floats. The model's arithmetic (`math.erf`-based normal CDF,
`statistics.pstdev`, band construction) is not bit-identical across interpreter
versions, so the serialised JSON is interpreter-dependent. `tools/build.py` had
already solved this exact class of failure for its own outputs at PR #6 by
normalising every published float through `round_floats(obj, places=9)`;
`market_store.py` (added later, PR #21) never adopted it.

## Repair

1. **`tools/market_store.py` — `write_output()`** now applies
   `build.round_floats(payload, 9)` before serialising (the same helper and the
   same precision `tools/build.py` uses).
2. **`tools/fetch.py` — `plan` writer** now leaves `data/ops/fetch_plan.json`
   untouched when the plan *items* are unchanged. Previously the `generated_utc`
   stamp was rewritten on every run, so every full `tools/validate.py` gate run
   (which executes `fetch.py plan`) dirtied the working tree with a
   timestamp-only change — the drift this session hit on arrival, and a standing
   invitation to timestamp-only commits.

## Verification performed

1. **Cross-interpreter byte-identity**: `market_store.py` run under 3.11.2,
   3.12.9, and 3.11.2 again — sha256 of `data/output/market_store.json` identical
   across all three (`4ded3b0a…9649d`).
2. **Full CI sequence** (verify → market_store → build → pages → sync →
   `git diff --exit-code` on `site data research *.html *.css *.js`): **clean on
   both 3.11.2 and 3.12.9** after the fix.
3. **Full local gate**: `python3 tools/validate.py` → **VALIDATION PASSED**, and
   the working tree is clean afterwards except for the intentionally regenerated
   `data/output/market_store.json` (committed); `data/ops/fetch_plan.json` is no
   longer churned by the gate run.
4. All pre-existing gates unchanged and green: official-standings proof
   (`verify.py`), desk checker (`check_site.py`), console checker
   (`docs/check.js`), root mirror, determinism section.

## Irregularities logged (not edited)

- `tools/validate.py` runs `tools/fetch.py ingest`, which prints
  "price rows: 117 (N new this run)" — i.e. the ingest step can append rows to
  `data/ops/price_snapshots.csv` from cached bodies during a *gate* run. Gate
  runs should not mutate datasets. Not fixed here (outside the failing gate);
  recorded as a request row in `COORDINATION.md` for the T21 owners' review.
- The workflow's determinism step uses unquoted `*.html *.css *.js` globs (bash
  expands them to root-level files only, while `site data research` are covered
  as directories). The quoted equivalent was used in this session's reproduction
  and covers a superset of paths, so the reproduction is at least as strict.

## Sources

- Workflow definition: `.github/workflows/pages.yml` on `main` (`6014d73`).
- Run records: GitHub Actions, repository `karagemop466-tech/X4`, runs
  43632180903 / 43632545850 / 43632743606 / 43632761165 / 43633294336
  (queried via `gh run list --workflow pages.yml`).
- CPython 3.12.9 source tarball: `https://codeload.github.com/python/cpython/tar.gz/refs/tags/v3.12.9`.
- Precedent for the repair: the PR #6 failure-and-repair record in
  `COORDINATION.md` ("The cause was that tools/build.py drew its bootstrap
  resamples from Python's random module … replaced with a fixed linear
  congruential generator and normalised every published float to a fixed
  precision").
