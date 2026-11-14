# Independent audit: row-level source provenance gate

**Audit date:** 2026-11-14 (UTC)

**Owner:** `arena/5092bd99-x4`
**Scope:** review of existing source-link validation and source classification. This is a code-path audit, not a new NFL data acquisition. No sports values or model outputs were changed.

## Executive finding

The desk-site checker does **not currently test whether a data-table row contains a source link**. `tools/check_site.py` collects hrefs into a page-wide list, but never puts them into the active row; each stored row is therefore empty, and the row-source loop skips it. I reproduced the behavior against both the current main file and PR #22 head `58d1da0ed508496055bfa1f65d756a8bdea8ab82`.

This means the reported `878 table rows` / `PASS` result from `python3 tools/check_site.py` is not evidence that row-level provenance was checked. The checker still performs other checks (local links, anchors, HTTPS links outside rows, navigation parity, mirror parity, and rectangular research CSVs); the finding is specifically about its row-source gate.

A second gap remains even after row-link capture is repaired: the current rule accepts **any** `https://` host. It cannot establish that a value is sourced from an official league, club, or data-provider site, nor that the citation is the source of the value in that cell. A general NFL schedule link in a row does not prove an ESPN odds value in that same row.

## Reproduction

Relevant code in the current checker is [`tools/check_site.py` lines 45–75](https://github.com/karagemop466-tech/X4/blob/6014d73dc7c9c76c4b3eded63284a33081bad9c6/tools/check_site.py#L45-L75) and the row-source loop is [lines 97–103](https://github.com/karagemop466-tech/X4/blob/6014d73dc7c9c76c4b3eded63284a33081bad9c6/tools/check_site.py#L97-L103). In `handle_starttag`, `<a href>` is added to `self.hrefs`, but not `self._cur_row`. The row is initialized as `[]` at a `<tr>` and appended unchanged at `</tr>`. The subsequent `if not row: continue` makes the source check a no-op for every collected row.

The same implementation is present at the open [PR #22 head](https://github.com/karagemop466-tech/X4/blob/58d1da0ed508496055bfa1f65d756a8bdea8ab82/tools/check_site.py#L45-L103). Main currently declares 20 desk pages, including the T21 operations pages; the PR #22 head declares 13 pages and currently lacks those newer operations pages because its branch predates their merge. Final integration must retain both the suggestion-program pages and the T21 operations pages in the gate.

I fed the parser three controlled `table.data` fixtures: (1) no link, (2) only an `http://` link, and (3) only `https://example.invalid`. For all three, the parser returned `p._rows == [[]]` and the published row-check loop recorded zero errors. I also parsed every current-main desk page with the checker's own `Page` class: **878 of 878 rows were stored as empty per-row href lists**. The fixtures are synthetic test cases, not NFL data. This falsifies the claimed behavior of the gate; it does not establish that every existing table row is actually unsourced.

## Coverage and source classification

- `site/check.py` does use an explicit host allowlist, but its `PAGES` list covers the 14 main generated pages, not the 20 desk pages covered by `tools/check_site.py`. See [`site/check.py`](https://github.com/karagemop466-tech/X4/blob/6014d73dc7c9c76c4b3eded63284a33081bad9c6/site/check.py).
- `tools/check_site.py` is the gate that includes the newer origination/operations pages, but its per-row href collection is empty and its intended rule checks only for an HTTPS prefix, not official domains.
- The repository's market page labels ESPN/DraftKings odds as third-party (`T3`) rather than NFL-official. For example, `data/market-prices.csv` cites an ESPN odds endpoint for the IND–HOU market row: [ESPN odds payload](https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/401873066/competitions/401873066/odds). That is provenance for what ESPN published, but it is not an official NFL source or a direct DraftKings source. The open [PR #26](https://github.com/karagemop466-tech/X4/pull/26) is also explicit that its one-book prices are non-official. That disclosure is good; under the user's strict verification rule, however, such values must not populate the verified official-source table. Use a direct official sportsbook source or leave those values blank and flag them. A separate NFL schedule URL cannot substantiate a sportsbook price.
- Official-source examples already used by the project include the [NFL standings](https://www.nfl.com/standings/), [official Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11), [NFL injury report](https://www.nfl.com/injuries/), and a club's own [Bills depth chart](https://www.buffalobills.com/team/depth-chart). These sources support only the facts they publish; they do not substantiate sportsbook prices.

## Verification performed

- `python3 tools/verify.py`: **PASS**, 460 checks; reconstructed game scores reproduce all 32 official NFL.com standings totals.
- `python3 tools/validate.py`: **PASS** on the current worktree based on main commit `6014d73`. This includes `tools/check_site.py`; because of the parser defect above, that PASS must not be cited as proof of per-row source coverage.
- `python3 tools/check_site.py`: reported 20 desk pages, 878 table rows, and PASS. The controlled parser reproduction shows the row-source part did not run effectively.
- `python3 tools/verify_live.py all`: standings **PASS** (32 rows / 256 field checks), schedule **PASS** (13 rows / 117 fields), injury snapshot **2 mismatches** in a partial 44-row sample (Greg Van Roten and Charles Woods, practice status). The harness identifies these as official-report drift; the committed snapshot was not changed. The current site already records this drift as F-34. The remaining 301 injury rows are outside that captured sample and were not checked by this snapshot run.

Snapshot verification uses the committed official captures and is reproducible offline; it is not a fresh fetch of NFL.com.

## Requested correction (not edited here)

`tools/check_site.py` is in the active PR #22 scope, so I did not modify it. The request is recorded in `COORDINATION.md` for that owner:

1. Add each anchor href to the row currently being parsed; fail on a data row with no source.
2. Add regression tests for no link, HTTP-only link, non-official HTTPS link, and allowed official links. A mutation test should remove a published row's source and prove the gate fails.
3. Apply an explicit host/source-tier policy. Distinguish official NFL, official club, official provider, third-party publisher, and model-derived values. Require the evidence link to support the value it is attached to; a generic official schedule link must not validate a third-party price.
4. If an item cannot meet the requested official-source standard, leave its numeric cell blank in the verified table and add a visible Flagged-for-Review entry. Optional third-party research values must be segregated and labelled non-official; they cannot satisfy the official-source gate.

The T30 source-policy request was also logged for the owner of PR #26 in `COORDINATION.md` and on the PR: use a direct official operator source or leave the verified price cells blank; third-party ESPN readings must not be passed off as official.

## Irregularities / limits

- **High severity:** the desk row-source gate is ineffective until corrected.
- **High severity:** HTTPS-only validation is weaker than the requested official-source rule.
- **Known, already flagged:** two practice-status differences in a partial official injury snapshot; do not silently overwrite the committed point-in-time record.
- This audit did not re-fetch all official pages or manually re-transcribe every row. It verifies the checker behavior, the committed snapshot harness outcome, and the source classifications described above; no broader verification claim is made.
