# Brief claims re-verified against the live official pages, 2026-11-17 (T40)

**Session:** `arena/d15ce403-x4` · **Date of reads:** 2026-11-17 (UTC date; the page-fetch tool does not record a time of day)
**Method:** each claim the brief names was checked against an official NFL.com or club page read in this session, through the platform's page-fetch tool. This sandbox cannot reach nfl.com over its own network, so every read is a text rendering of the page, not raw HTTP bytes.
**Machine-readable copy:** `research/verification/brief-claims-2026-11-17.csv`
**Reserve-list transcription:** `research/verification/official-reserve-list-2026-11-17.csv` (25 rows)

Verdict key: **Confirmed** = the official page says so. **Confirmed as announced** = the official page reports an expected event, not a game-day fact. **Reported** = an official article says so, but an official record in the repository's reads does not agree. **Not reproduced** = the official page does not show what the brief says. **Not checked** = out of this pass.

## Summary

| Verdict | Count |
|---|---|
| Confirmed | 4 |
| Confirmed as announced | 3 |
| Reported, conflict open | 2 |
| Not reproduced | 2 |
| Not checked this session | 3 |

The brief's injury-table counts (254 and 279 rows) were not re-read in full this session. The prior capture (T37, 2026-11-15) read all 347 rows and found neither figure. That record stands; see C2.

## Claim-by-claim register

| # | Brief claim (ref) | Verdict | Official evidence (link, read 2026-11-17) | What it means for the site |
|---|---|---|---|---|
| C1 | The Lions' game-status cells for Kerby Joseph, Cade Mays and D.J. Reed are blank (VR-08, VR-12) | **Not reproduced** | Week 10 injury report, Lions section: Joseph (S, Knee, DNP, **Out**), Mays (C, Ankle, DNP, **Out**), Reed (CB, Hip, DNP, **Out**). https://www.nfl.com/injuries/ | No blank remains. The committed file already reads Out for all three. |
| C2 | Week 10 tables are stale: 254 rows committed vs 279 live; four no-injury sections vs two (VR-04 to VR-07) | **Not reproduced** (prior record stands) | The first of the eight text chunks of the Week 10 report was re-read this session and the page is still the Week 10 report. The full 347-row read of 2026-11-15 is recorded in `research/verification/injury-recapture-2026-11-15.md`, which reports that neither 254 nor 279 is reproduced by any count of the page. | No change. The 2026-11-15 record (347 rows, 28 clubs) is the current committed state. |
| C3 | Malik Willis is absent from the weekly report because he is on injured reserve, not because he is healthy (VR-25, VQ-06) | **Confirmed** | NFL.com: "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start" (placed on IR on a Tuesday; will miss Weeks 10-13). https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start . NFL.com reserve-list entry dated 11/10: Malik Willis, Reserve/Injured. https://www.nfl.com/transactions/league/reserve-list/2026/11 | Supports the rule that "not listed" must not mean "available". Row is in `official-reserve-list-2026-11-17.csv`, line 23. |
| C4 | Kyle McCord replaces Willis at QB for Miami (VR-25, VQ-05) | **Confirmed as announced** | Same NFL.com article: McCord "will fill in, beginning Sunday on the road against the Indianapolis Colts"; the article says McCord "is poised to make his first NFL start" on that Sunday. | The game-day starter is not confirmed by this session. No game book was read. |
| C5 | Drew Lock starts for Seattle with Sam Darnold out (VR-24) | **Confirmed as announced** | NFL.com: "Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again." https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again . Second NFL.com article: Lock "has no injury designation and will start Sunday"; he was limited in practice with right elbow and oblique injuries. https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders | The Seattle row in `data/qb-starter-changes.csv` is consistent with both articles. Game-day starter not confirmed. |
| C6 | Lamar Jackson went on injured reserve (VR-17, VR-26) | **Reported, conflict open (F-44)** | NFL.com, 1 Nov 2026: Jesse Minter said Jackson "will be placed on injured reserve", at least four games. https://www.nfl.com/news/ravens-qb-lamar-jackson-suffers-right-thumb-injury-bills . NFL.com (later): "With Jackson and Tyler Huntley placed on injured reserve, the Ravens were forced to start … Joe Fagnano." https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season . **But** neither the 2026-11-14 capture nor the 2026-11-17 read of the NFL.com November reserve list shows Jackson or Huntley (F-44). | Carried as reported, not as a reserve-list fact. |
| C7 | Tyler Huntley went on injured reserve (VR-26) | **Reported, conflict open (F-44)** | NFL.com, 1 Nov: Huntley "hurt his toe in the first half"; ESPN reported turf toe, per the NFL.com article. https://www.nfl.com/news/ravens-qb-lamar-jackson-suffers-right-thumb-injury-bills . The IR statement is in the later NFL.com article in C6. Not on the reserve-list reads (F-44). | As C6. |
| C8 | Baltimore still publishes Jackson and Huntley at QB, a stale depth row (VR-17, VQ-07) | **Not reproduced** | Ravens club depth chart, read 2026-11-17, Offense, QB row: Jacoby Brissett, Joe Fagnano, Kedon Slovis. Neither Jackson nor Huntley. https://www.baltimoreravens.com/team/depth-chart . | The **club chart** is not stale. The committed replacement row for Baltimore is (F-45). |
| C9 | Brissett is the Ravens' replacement starter, acquired by trade (VR-24, VR-25) | **Confirmed** | NFL.com trades table, November: Jacoby Brissett, ARI to BAL, 11/06. https://www.nfl.com/transactions/league/trades/2026/11 . Ravens depth chart (C8) lists him first at QB. NFL.com: "The Ravens then acquired Brissett on Friday in a trade." | The committed Baltimore row says "no replacement starter named in league reporting". That is out of date (F-45). |
| C10 | The Colts' Week 10 release documents two starting-receiver trades (Downs and Allen) | **Confirmed** | NFL.com trades table, November: Josh Downs, IND to KC, 11/10; Keenan Allen, IND to SF, 11/10. https://www.nfl.com/transactions/league/trades/2026/11 | Trades confirmed. Not checked: whether both appear in the same article as the Colts' depth chart, as the brief states. |
| C11 | Texans publish depth as an image and need an authorised structured source (brief, Fix-the-two-depth-parsing-failures) | **Confirmed** | Houston Texans depth-chart page, read 2026-11-17: the chart body is an image; the page is labelled "Unofficial Depth Chart" and holds no text rows. https://www.houstontexans.com/team/depth-chart | No transcription was made, as the brief requires. No authorised structured source was identified in this session (F-46). |
| C12 | Reserve list: "not listed" must never mean "available" (VR-25, VQ-06) | **Confirmed in part** | Willis (C3) is listed as IR and absent from the injury report. The 2026-11-17 reserve-list read is 25 rows and the 2026-11-14 capture is 17 rows; they disagree (F-43). | The reserve list is not yet a complete source. Use it as evidence of a listing, never as proof of absence. |
| C13 | The Seahawks' row says "no injury designation" for Lock (SEA row in `qb-starter-changes.csv`) | **Confirmed** | The NFL.com article in C5 quotes the coach saying so. The same article records elbow and oblique limits in practice. | Accurate as written. The article's practice limits are not in the CSV. Not raised as an irregularity. |
| C14 | Immutable multi-day availability snapshots exist (capture every day, with hashes) | **Not reproduced** | `data/captures/` does not exist on this branch (the repository holds no capture files). `.github/workflows/capture.yml` runs on a schedule from the default branch, so it has not yet run on this branch. | Not met until the capture workflow runs on `main` and commits captures. Logged as F-47. |
| C15 | Seattle puts two players in one slot; Washington leaves a slot empty (VR-21, VR-23, VQ-08) | **Not checked** | Not part of this pass. | Unchanged. |
| C16 | Week 11 status for the Lions, Seattle and Cincinnati injuries | **Not checked** | Not part of this pass. The Week 11 report had not been posted as of this read (the NFL.com page is still the Week 10 report). | Unchanged. |
| C17 | Official Texans and Ravens depth charts for later weeks (VR-17 generally) | **Not checked** | Only the two charts named above were read. | Unchanged. |

## Irregularities for review

These are recorded as flags F-43 to F-47 on the Flagged for Review page, each with a source link.

- **F-43** NFL.com reserve-list reads are not complete or stable. The 2026-11-14 capture held 17 rows ending 11/07, and included Michael Wilson (ARI, 11/10). The 2026-11-17 read holds 25 rows ending 11/10, and does not include Wilson or any 11/07 to 11/09 entry. Cause not determined. The page may be showing a page of rows, or the reader may not have followed a pagination control. This sandbox cannot check the page's controls directly.
- **F-44** Lamar Jackson and Tyler Huntley: NFL.com articles say both were placed on injured reserve, but neither name appears in the November reserve-list reads. Reported, not reconciled.
- **F-45** The committed Baltimore replacement row (`data/replacement-depth.csv`, BAL, "no replacement starter named") is out of date. NFL.com reports Brissett's trade on 11/06 and Fagnano's start in Week 9. The club chart is current. Left unedited, because flag F-33 describes that CSV's contents.
- **F-46** The Texans' depth chart is published as an image only. No structured or text source was found. Per the brief, it is not transcribed by eye.
- **F-47** No immutable multi-day capture history exists on this branch (`data/captures/` absent). The capture workflow runs from the default branch. The first scheduled run on `main` is the test; see the T40 session log.

## Limits

- Every read is a text rendering from the platform's page-fetch tool. Raw HTTP bytes and page hashes were not captured in this session.
- The Week 10 injury report was checked only at its first text chunk (of eight). The full read is the 2026-11-15 record.
- No game book, box score or game-day starter was read. "Confirmed as announced" means the official page reported the expectation.
- The reserve-list transcription is a copy of two text chunks. It is not a complete list.
- Flag F-39 (191 desk rows without an https source link) is unchanged by this pass.
