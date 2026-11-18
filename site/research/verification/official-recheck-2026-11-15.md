# Official re-check of the committed Week 10 injury data — 2026-11-15

Session: `arena/deec2dc3-x4` (single-branch session). Scope: an independent, line-by-line
comparison of part of `data/injuries-wk10-2026.csv` against the live NFL.com Week 10
injury report. This note does **not** verify the whole dataset; it verifies four clubs.

## Sources

| Source | URL | Retrieved |
|---|---|---|
| NFL.com 2026 injury report, Week 10 (page chunk 1 of 8: WAS, NYG, NE, DET) | https://www.nfl.com/injuries/league/2026/reg10 | 2026-11-15 (platform web fetch) |
| NFL.com injury report URL for Week 11 | https://www.nfl.com/injuries/league/2026/reg11 | 2026-11-15 — **served the Week 10 page** (page title "Week 10 of the 2026 Season"; the URL resolved to `reg10`). No Week 11 report was available at this address. |
| Committed dataset | `data/injuries-wk10-2026.csv` (captured 2026-11-14) | repository |

## Method

The 44 player rows printed on the official page for Washington, the NY Giants, New England and
Detroit were transcribed by hand (name, position, injury, practice status, game status) and
compared field-by-field with the committed CSV rows for the same clubs. Practice labels were
mapped ("Full Participation in Practice" -> Full, "Limited Participation in Practice" -> LP,
"Did Not Participate In Practice" -> DNP); the CSV uses "Full", "Limited" and "DNP", so a
label-only difference (LP vs Limited) is not a discrepancy.

## Result

- Rows: official 44 / committed 44 for these four clubs. No missing or extra players.
- Positions, injuries and game-status cells: all match.
- Practice status: **two real differences**, both already recorded as flag **F-34** in
  `tools/content.py` and the site's Flagged for Review page:

| Player | Club | Committed CSV | Official NFL.com (2026-11-15) | Source |
|---|---|---|---|---|
| Greg Van Roten (G) | NE | Limited | Full Participation in Practice | https://www.nfl.com/injuries/league/2026/reg10 |
| Charles Woods (CB) | NE | Limited | Full Participation in Practice | https://www.nfl.com/injuries/league/2026/reg10 |

The CSV is an earlier dated snapshot by design (the repository keeps dated captures and flags
drift rather than overwriting it), so the cells were **not** edited here. They stay flagged.

## Items from the review request, checked

| Request | Finding |
|---|---|
| Populate the three blank Lions game-status cells (Joseph, Mays, Reed) | **Already populated** in the committed CSV as `Out` (rows DET Kerby Joseph, Cade Mays, D.J. Reed). Matches the official page: all three "Out" (https://www.nfl.com/injuries/league/2026/reg10). |
| Week 10 row count "254 vs 279" | The committed CSV has **345** data rows across **28** club labels (`SEA` 15, `CIN` 9). Neither 254 nor 279 is reproduced by the committed file, and the official page was **not** counted in full here (it spans 8 page chunks). The count discrepancy is **unverified** and is flagged for review. |
| Cincinnati shown as injury-free (4 players) | The committed CSV has 9 `CIN` rows, not 0. The official count for Cincinnati was not verified in this session (it lies outside the chunk compared). Flagged. |
| Week 11 injury report capture | Not available at the Week 11 URL on 2026-11-15 (see Sources). The daily capture schedule therefore cannot start from this address; an official Week 11 URL must be confirmed before capture. |

## Not done in this session (honest scope)

- The other 28 clubs' rows were not compared.
- The full row counts (345 committed vs the official total) were not verified.
- The 191 desk-table rows without an https source link (flag F-39) were not changed.
- No new snapshot, hash or capture store was created; no daily schedule was added.

## Irregularities for review

1. Two Week 10 practice-status cells differ from the official page (F-34; this note re-confirms them on 2026-11-15).
2. The committed Week 10 row count (345) differs from the figures in the review request (254 / 279); the official total is unverified.
3. The Week 11 report is not served at the `reg11` address on 2026-11-15.
