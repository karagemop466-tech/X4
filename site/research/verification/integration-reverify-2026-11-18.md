# T48 final-integration re-verification — 2026-11-18

Session `arena/13a69046-x4`, 2026-11-18 (UTC). Every check below was run or read in this
session. Nothing is inferred: a value that could not be confirmed stayed out of this file.
The sandbox cannot open a socket to nfl.com, so live reads go through the page-fetch tool;
the committed-data checks are the repository's own deterministic harnesses.

## 1. Live official reads (page-fetch tool, 2026-11-18)

| # | Check | Source (official) | Result |
|---|---|---|---|
| 1 | All 32 clubs' W/L/T/PF/PA vs `data/standings-wk10-2026.csv` | https://www.nfl.com/standings/ (both chunks read) | **32/32 match, 0 mismatches** |
| 2 | All 13 Week 11 fixtures (away, home, date) vs `data/schedule-wk11-2026.csv` | https://www.nfl.com/schedules/2026/by-week/week-11 (3 chunks read) | **13/13 match**; byes ATL/CLE/GB/LAR/NE/SEA = 13 games |
| 3 | Week 9 final CLE 22 – NO 23 (OT) for the F-49 settlement | https://www.nfl.com/games/browns-at-saints-2026-reg-9 | **confirmed** (quarter-by-quarter and totals both read) |
| 4 | F-61 claim: the reg11 injury address still serves Week 10 | https://www.nfl.com/injuries/league/2026/reg11 → redirects to `reg10`; title "Week 10 of the 2026 Season", heading "Injuries - WEEK 10" | **re-confirmed**; no official Week 11 report exists on 2026-11-18 |
| 5 | Five injury cells read cell-for-cell: Van Roten, Woods (NE), Joseph, Mays, Reed (DET) | https://www.nfl.com/injuries/league/2026/reg10 (chunk 0) vs `data/injuries-wk10-2026.csv` | **5/5 match** (Full/Questionable, Full/Questionable, DNP/Out ×3) |

## 2. Deterministic harnesses (this branch, before merge)

| Check | Command | Result |
|---|---|---|
| Game log vs official standings (two-source agreement) | `python3 tools/reverify_2026_11_18.py` | PASS — 150 games, Weeks 1–10, all 32 clubs reproduce the official standings; every Week 10 final matches the official Week 10 schedule page |
| Full publication gate | `python3 tools/validate.py` | **VALIDATION PASSED** — verify + capture checks + market re-derivation + site gate (3,318 data rows, every one source-linked) + root mirror byte-identical + determinism + console gate + desk checker (incl. the new Snapshot-freshness gate) + data hygiene |
| Independent settlement re-check | `python3 tools/settlement_recheck.py` | 24 settled bets, recorded = re-settled, **changed: 0**, price mismatches 0 |
| Removal-of-luck artifact | `python3 tools/luck.py` | regenerated: n=24, mismatches **[]** (was 1 stale entry), recorded ROI +64.2% |

## 3. F-49 settlement reconciliation (verified, then registered)

- Defect: side bets graded on the straight-up winner, ignoring the closing spread (pre-fix code at `fb8a6cb`).
- Fix on main: PR #63, commit `915bf42` — grade = official margin + recorded home handicap, exact tie = push, three regression tests (`tools/test_origination.py`, run by the gate).
- Live proof: official final CLE 22 – NO 23 (check 3) ⇒ the Browns +4.5 side bet covers and is **won**; `data/ops/graded.csv` now records `won`.
- Re-verified today: settlement re-check changed: 0 over 24 bets; published `signal-vs-staking.html` shows +15.414 units / +64.224% (n=24) and `luck.html` shows the same 15.41 — the old F-49 text claiming an uncorrected figure was still published is no longer true.
- Register updated in this session: **F-49 → resolved** (Correction), **F-50 → updated** (luck.json now holds zero mismatches after regeneration).

## 4. What this session did NOT verify (left as flagged, not filled)

- Week 11 game statuses: no official Week 11 report exists yet (check 4; F-55/F-61 stand).
- Raw capture history: the scheduled capture workflow's state is owned by session
  `arena/dad920d9-x4` (F-47/F-48/F-65); this session did not touch capture files.
- Week 11 venues: owned by session `arena/5534e2ba-x4` (F-60); this session read only the
  fixture list (check 2), not the Game Info stadium blocks.

## Irregularities found by this session

1. **Conflict markers committed to `main` by the PR #90 merge** — `COORDINATION.md` (root and `site/` mirror) contained a stray `=======` and `>>>>>>> origin/main` near the file end. Removed during this session's claim rebase with no content loss (union kept); the pipeline sync re-publishes the mirror.
2. **Nine desk pages advertised `Snapshot 2026-11-14`** four days after the tree was re-verified — fixed by the freshness gate carried in PR #83's commit `c2836ec` (cherry-picked) plus re-dating the nine hand-written pages in both mirrors; the gate now fails the build if the label ever regresses.
3. **`data/output/luck.json` was stale relative to the fixed `graded.csv`** (still listed the pre-fix mismatch) because `tools/luck.py main()` is not a validate step — regenerated; F-50 records the cause.
