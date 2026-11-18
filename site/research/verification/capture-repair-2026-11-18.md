# Official capture pipeline: repair and live verification (T48)

**Date:** 2026-11-18 (UTC) · **Branch:** `arena/dad920d9-x4` · **Task:** T48 (takeover of the stale claim `arena/7db594d1-x4`, PR #62) · **Flags addressed:** F-47, F-48, F-56

## 1. What was broken

Four scheduled runs of *Official capture (injury report and club depth pages)* failed on `main` (runs 44175196682, 44043083196, 43967865851, 43818369872). The runner log archive could not be downloaded from the sandbox, so the **live cause of those four runs is unknown** and is not asserted here.

Two defects were confirmed in the code path, both reproduced offline on a scratch copy of `main`:

1. **Uncaught exception at Houston.** `tools/depth.py` records Houston's chart URL as an empty string (its chart is an image). The capture loop passed `''` to `urllib`, which raised `ValueError: unknown url type: ''`, ending the job at the Houston target. Fixed: Houston is not a structured source and is excluded by design.
2. **Lost evidence and global freshness.** A failed source stopped the commit step; freshness took the newest manifest line across all sources. Fixed: each source is reported separately, failures are written to the manifest, the commit step still runs, and freshness requires a recent schema-valid read for **every** expected source.

A third defect surfaced on the first live run on GitHub's runners (run 44231894783): the injury page was fetched (HTTP 200, 402,295 bytes) but failed its schema check. The page uses **relative** player links (`href="/players/<slug>/"`, 348 matches); the check looked only for absolute `https://www.nfl.com/players/` links, which appear in the rendered markdown but not in the HTML. Fixed; the check now accepts both forms. The stored Week 10 page yields 347 player links, which equals its 347 body rows.

## 2. Storage policy change (raw bytes are not committed)

This repository is public. The brief requires raw row-level data to stay in a private store until the terms are read, and the audit (T40) left the retention question open. The capture tool therefore **no longer commits raw page bytes**. By default it commits only the manifest: URL, UTC fetch time, HTTP status, byte count, SHA-256, schema result and a changed flag. Raw bytes are written only to a directory named by the environment variable `X4_CAPTURE_RAW_DIR`, which must be outside the repository. The workflow does not set it, and `data/captures/**/*.gz` is git-ignored.

The first two live runs (44231894783, 44232017215) had committed raw bytes to the branch before this policy was applied. Those commits were removed from the branch history before merge (force-push with lease, after checking that no `.gz` object remains reachable). Their hashes stay in the manifest.

**Decision needed (D1):** choose a private store for raw bytes (for example, a private repository or bucket with the owner's credentials). Until one exists, captures are verifiable by hash only: a later private copy can be checked against the committed SHA-256, but it cannot be replayed from this repository.

## 3. Live result: scheduled-workflow test run on this branch

| Run | Commit | Result | What it showed |
|---|---|---|---|
| [44231894783](https://github.com/karagemop466-tech/X4/actions/runs/44231894783) | `f37fdc9` (before schema fix) | failure | Depth: 31/31 HTTP 200, schema valid. Injuries: HTTP 200, schema **failed** on relative player links. |
| [44232017215](https://github.com/karagemop466-tech/X4/actions/runs/44232017215) | `8d74bff` (schema fix) | success | 32/32 valid. Raw bytes were committed to the branch and later removed (see §2). |
| [44232449157](https://github.com/karagemop466-tech/X4/actions/runs/44232449157) | `e89e47a` (policy) | **success** | 32/32 valid, manifest-only commit (`8a7cf0d`, 32 lines). **This is the verified state.** |

Workflow dispatch is not available to this token (HTTP 403), so the test used a temporary `push` trigger on this branch, which is removed before merge.

### Per-source read, run 44232449157 (2026-11-18 03:44 UTC)

All 32 structured sources. Houston is excluded by design (image-only chart; see §5). Each row links to the page that was read.

| # | Source | Official URL read | Fetched (UTC) | HTTP | Bytes | SHA-256 (12) | Changed vs previous read | Schema |
|---|---|---|---|---|---|---|---|---|
| 1 | injuries | https://www.nfl.com/injuries/ | 2026-11-18T03:44:00Z | 200 | 402,299 | `1d896816da9a` | no | valid |
| 2 | depth/ARI | https://www.azcardinals.com/team/depth-chart | 2026-11-18T03:44:00Z | 200 | 281,490 | `a2f84fd1646c` | yes | valid |
| 3 | depth/ATL | https://www.atlantafalcons.com/team/depth-chart | 2026-11-18T03:44:00Z | 200 | 308,399 | `8979c4ce0def` | no | valid |
| 4 | depth/BAL | https://www.baltimoreravens.com/team/depth-chart | 2026-11-18T03:44:01Z | 200 | 286,885 | `f5ec2ed5c5db` | yes | valid |
| 5 | depth/BUF | https://www.buffalobills.com/team/depth-chart | 2026-11-18T03:44:01Z | 200 | 290,112 | `0a21cbd1bcf2` | yes | valid |
| 6 | depth/CAR | https://www.panthers.com/team/depth-chart | 2026-11-18T03:44:01Z | 200 | 319,331 | `b889a59e7e46` | yes | valid |
| 7 | depth/CHI | https://www.chicagobears.com/team/depth-chart | 2026-11-18T03:44:01Z | 200 | 280,155 | `f630a3db18e1` | yes | valid |
| 8 | depth/CIN | https://www.bengals.com/team/depth-chart | 2026-11-18T03:44:01Z | 200 | 284,376 | `91caba0b1c8d` | yes | valid |
| 9 | depth/CLE | https://www.clevelandbrowns.com/team/depth-chart | 2026-11-18T03:44:02Z | 200 | 286,416 | `69aaaf848f19` | no | valid |
| 10 | depth/DAL | https://www.dallascowboys.com/team/depth-chart | 2026-11-18T03:44:02Z | 200 | 269,686 | `d900fcb19e5b` | yes | valid |
| 11 | depth/DEN | https://www.denverbroncos.com/team/depth-chart | 2026-11-18T03:44:02Z | 200 | 283,898 | `62e5fc09354f` | yes | valid |
| 12 | depth/DET | https://www.detroitlions.com/team/depth-chart | 2026-11-18T03:44:02Z | 200 | 280,657 | `e77187c6057e` | yes | valid |
| 13 | depth/GB | https://www.packers.com/team/depth-chart | 2026-11-18T03:44:03Z | 200 | 282,495 | `b5add6d3e7cf` | yes | valid |
| 14 | depth/IND | https://www.colts.com/team/depth-chart | 2026-11-18T03:44:03Z | 200 | 335,855 | `e61a375577aa` | yes | valid |
| 15 | depth/JAX | https://www.jaguars.com/team/depth-chart | 2026-11-18T03:44:03Z | 200 | 298,717 | `27cd063a9ddc` | yes | valid |
| 16 | depth/KC | https://www.chiefs.com/team/depth-chart | 2026-11-18T03:44:03Z | 200 | 290,819 | `3e1326d7f895` | yes | valid |
| 17 | depth/LAC | https://www.chargers.com/team/depth-chart | 2026-11-18T03:44:03Z | 200 | 348,696 | `e903a98a53e5` | yes | valid |
| 18 | depth/LAR | https://www.therams.com/team/depth-chart | 2026-11-18T03:44:03Z | 200 | 281,985 | `8ceab9a5af91` | no | valid |
| 19 | depth/LV | https://www.raiders.com/team/depth-chart | 2026-11-18T03:44:04Z | 200 | 286,152 | `96229c37f002` | yes | valid |
| 20 | depth/MIA | https://www.miamidolphins.com/team/depth-chart | 2026-11-18T03:44:04Z | 200 | 274,193 | `c9c7fc58568a` | yes | valid |
| 21 | depth/MIN | https://www.vikings.com/team/depth-chart | 2026-11-18T03:44:04Z | 200 | 296,647 | `4a6e1ebfc353` | yes | valid |
| 22 | depth/NE | https://www.patriots.com/team/depth-chart | 2026-11-18T03:44:04Z | 200 | 345,655 | `a7ce7aa8e25d` | yes | valid |
| 23 | depth/NO | https://www.neworleanssaints.com/team/depth-chart | 2026-11-18T03:44:05Z | 200 | 498,077 | `17d269c19c5f` | yes | valid |
| 24 | depth/NYG | https://www.giants.com/team/depth-chart | 2026-11-18T03:44:05Z | 200 | 284,276 | `1e048338a801` | yes | valid |
| 25 | depth/NYJ | https://www.newyorkjets.com/team/depth-chart | 2026-11-18T03:44:05Z | 200 | 282,254 | `e736439ddf9f` | yes | valid |
| 26 | depth/PHI | https://www.philadelphiaeagles.com/team/depth-chart | 2026-11-18T03:44:05Z | 200 | 345,961 | `adee8be1d9e4` | yes | valid |
| 27 | depth/PIT | https://www.steelers.com/team/depth-chart/ | 2026-11-18T03:44:06Z | 200 | 297,626 | `a83f15d52b63` | no | valid |
| 28 | depth/SEA | https://www.seahawks.com/team/depth-chart/ | 2026-11-18T03:44:06Z | 200 | 300,501 | `c9519cf80901` | yes | valid |
| 29 | depth/SF | https://www.49ers.com/team/depth-chart | 2026-11-18T03:44:06Z | 200 | 277,826 | `077e94ff8623` | yes | valid |
| 30 | depth/TB | https://www.buccaneers.com/team/depth-chart | 2026-11-18T03:44:06Z | 200 | 284,428 | `2a8d30aac14c` | yes | valid |
| 31 | depth/TEN | https://www.tennesseetitans.com/team/depth-chart | 2026-11-18T03:44:06Z | 200 | 292,047 | `d57d395b2ab3` | no | valid |
| 32 | depth/WAS | https://www.commanders.com/team/depth-chart | 2026-11-18T03:44:07Z | 200 | 290,292 | `6b37622cacae` | yes | valid |

### Independent checks on the 03:44 read

* **Hash integrity:** `tools/capture_official.py verify` re-hashes every retained file; with raw bytes not retained, the 32 new entries are hash-only and are counted, not failed. The earlier entries that referenced raw files are reported as "not present here".
* **Freshness:** `tools/capture_official.py freshness --kind all --max-hours 13` passes for all 32 sources.
* **Unit tests:** `tests/test_capture_official.py`, 11 tests, offline, pass; one test runs only when the private store is configured and is skipped otherwise.

## 4. Cell-level delta against the committed Week 10 dataset

`tools/capture_delta.py` reads one stored capture (from the private store), extracts every row of the official report's tables, maps the official wording to the dataset's codes, and compares each cell with `data/injuries-wk10-2026.csv`.

**Result for the 2026-11-18 03:40:10 UTC read: 347 rows across 28 clubs, 347 of 347 keys matched, 1,388 cells compared, 0 cells differ, 0 unmapped club names, 0 unknown practice wordings.** The delta file `research/verification/capture-delta-2026-11-18.csv` therefore contains no data rows (header only), so it publishes no row-level data.

The zero-difference result also confirms that the Week 10 dataset matches the official page as read on 2026-11-18, which is a finding about the page and not only about the tool.

## 5. Raw hashes over-report change

Between the 03:39 and 03:40 reads of the same pages, the raw SHA-256 changed for **6 of 32** sources: the injuries page and five club pages (ATL, CLE, LAR, PIT, TEN). Comparing their extracted table cells showed **no content change** in any of the six. The raw bytes differ because of markup that is not part of the data (the byte counts for LAR differ by 139 bytes, while its 155 cells are identical).

**Consequence:** a raw-hash change is not evidence of a designation change. Any "what changed" analysis must compare extracted, normalised content. The tool stores hashes of raw bytes for immutability and must not be read as a change signal on its own.

## 6. What this does not establish

* The **live cause** of the four historical failures is unknown; the Houston `ValueError` is a confirmed defect on the code path, and the post-fix runs show the success path, not the historical cause.
* **Week 11 is still not published.** The capture still reads the Week 10 report (`WEEK 10` heading), and freshness checks recency, not which week is current. This is flag F-61, still open.
* **Houston depth:** the Texans page was read on 2026-11-18 and shows one image under the heading "Unofficial Depth Chart", with no structured chart. Houston remains excluded and F-46 stays open.
* **Scheduled history starts only after merge.** GitHub runs `schedule` triggers only from the default branch, so the multi-day series begins when this reaches `main`.
* **Schema checks are structural.** They confirm the markers the tool expects and the row counts. They do not validate what the values mean.
* **Terms:** whether NFL.com and club pages may be stored at all, even as hashes, is not determined here (D1 and the terms question remain open).

## 7. Official sources read for this record (2026-11-18)

* Injury report, Week 10 as served by the league (read through the page-fetch tool): https://www.nfl.com/injuries/league/2026/reg10 (the Week 11 address `…/reg11` returned this Week 10 page, so Week 11 was not published at read time)
* Houston depth chart, image only, labelled "Unofficial Depth Chart": https://www.houstontexans.com/team/depth-chart
* The 32 captured sources are listed in §3 and in `data/captures/manifest.jsonl`.

## 8. Flags for the integration owner (requested in COORDINATION.md; not edited here)

* **F-47 / F-48:** status can move from "no capture history" to "pipeline repaired; first valid run 2026-11-18 03:44 UTC; scheduled history starts on merge". The historical four failures remain "cause unknown".
* **F-56:** the code-path risks named in the audit (lost partial captures; global freshness) are fixed in this branch.
* **New, D1:** raw-byte retention for a public repository is a decision for the owner.
* **New:** raw SHA-256 is not a change signal (§5).
