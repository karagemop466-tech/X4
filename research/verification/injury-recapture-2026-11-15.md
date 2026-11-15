# Week 10 injury report: full re-capture and correction, 2026-11-15

**Source (official):** NFL.com, *Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season*, https://www.nfl.com/injuries/ (retrieved 2026-11-15, UTC, through the platform's page-fetch tool, 8 text chunks, `totalChunks: 8`, read to the end).

**Capture file (every row, as read):** `research/verification/official-injury-report-wk10-capture-2026-11-15.csv`, SHA-256 `8f4f661ff1d6dbe4a431acec95ca2927a13691762b74e050ea5cc27011fff01f`.

**Drift alarm:** `tools/capture_check.py` compares the capture with `data/injuries-wk10-2026.csv` cell by cell and fails the publication gate on any difference. It is pinned to 347 rows and 28 teams.

## What the official page holds

| Item | Official read (2026-11-15) | Committed before this session | Committed after this session |
|---|---|---|---|
| Player rows across 28 club sections | **347** | 345 | 347 |
| Rows with an injury description or a game status | 171 | 160 | 171 |
| Clubs with no designation at all | 0 | 0 | 0 |
| Out / Doubtful rows | 81 (70 Out, 11 Doubtful) | 76 | 81 |

Rows per club (rows with an injury or game status in brackets):
WAS 9 (2) · NYG 11 (1) · NE 15 (12) · DET 9 (5) · KC 13 (6) · ATL 11 (5) · MIN 13 (8) · GB 17 (12) · JAX 11 (4) · TEN 12 (6) · BUF 14 (5) · NYJ 9 (9) · MIA 11 (4) · IND 14 (7) · CAR 12 (7) · NO 12 (6) · HOU 16 (11) · CLE 12 (3) · LAR 14 (7) · ARI 15 (9) · SEA 15 (4) · LV 5 (2) · SF 12 (8) · DAL 19 (11) · PIT 8 (1) · CIN 9 (4) · LAC 19 (10) · BAL 10 (2).

## Corrections made to the committed dataset

Twenty-six cells differed, and two rows were absent. Each correction is the value printed on the official page.

| Club | Player | Field | Committed | Official 2026-11-15 |
|---|---|---|---|---|
| BAL | Calais Campbell | row added | (absent) | DT, no injury, DNP |
| BAL | Ronnie Stanley | row added | (absent) | T, no injury, DNP |
| NE | Greg Van Roten | practice | Limited | Full (Hamstring, Questionable) |
| NE | Charles Woods | practice | Limited | Full (Hamstring, Questionable) |
| GB | Savion Williams | practice | Full | Limited |
| JAX | Antonio Johnson | practice | Full | Limited |
| MIA | Kaytron Allen | practice | Limited | Full |
| IND | Arden Key | injury / game status | Hamstring / Questionable | none / none |
| HOU | David Montgomery | practice | Limited | Full (Groin, Questionable) |
| HOU | Jaylin Smith | practice | Limited | Full (Hamstring, Questionable) |
| CLE | Denzel Ward | practice | Full | Limited |
| ARI | Andrew Wingard | practice | Limited | DNP (Groin, Questionable) |
| SF | C.J. West | practice | Limited | Full (Knee, Questionable) |
| DAL | Von Miller | practice | Full | DNP |
| LAC | Kayode Awosika | injury / practice / game | none / Limited / none | Fibula / Full / Questionable |
| LAC | Bud Dupree | practice | DNP | Full |
| LAC | Justin Eboigbe | injury / game | none / none | Ankle / Questionable |
| LAC | Ladd McConkey | injury / game | none / none | Back / Questionable |
| LAC | Keaton Mitchell | practice | Limited | Full |
| LAC | David Njoku | injury / practice / game | none / Limited / none | Fibula / Full / Questionable |
| LAC | Denzel Perryman | injury / game | none / none | Pectoral / Questionable |
| LAC | Trey Pipkins | injury / practice / game | none / DNP / none | Not injury related - personal matter, Knee / Limited / Questionable |
| LAC | Branson Taylor | injury / game | none / none | Ankle / Out |
| LAC | Brenen Thompson | injury / game | none / none | Hamstring / Doubtful |
| LAC | Isas Waxter | injury / game | none / none | Ankle / Out |
| LAC | Kendall Williamson | injury / game | none / none | Calf / Out |
| BAL | Jaylinn Hawkins | injury / game | none / none | Knee / Out |
| BAL | Adam Randall | injury / game | none / none | Neck, Hamstring / Questionable |

The Chargers section was the largest difference: twelve of its nineteen rows changed. The committed Chargers rows carried no designation at all (0 of 19). Why that section was stale is not determined from this sandbox; it is recorded as an observation, not a cause.

## Claims in the brief that did not reproduce

- **"254 rows" committed and "279 rows" live.** The committed file held 345 rows, and the live page holds 347. Neither 254 nor 279 is reproduced by any count of the page (all rows, rows with a designation, or rows with a practice status below Full).
- **Rodney Shelley (LAC) Full to Limited** (recorded on 2026-11-14 in F-40). The live read shows **Full**, matching the committed value. This single change is not reproduced.
- **"Seattle and Cincinnati are shown as injury-free."** The committed dataset and the rendered availability page both show four designated players for each. Seattle lists 15 players (4 designated) and Cincinnati lists 9 (4 designated). The brief's "15 and 4" describe the 15 Seattle rows and the 4 Cincinnati designations, not an injury-free display.
- **Baltimore quarterbacks on the chart (VR-17, VR-26, VQ-07).** The brief says Lamar Jackson and Tyler Huntley are still published at QB. The club's own depth chart, read on 2026-11-15 from https://www.baltimoreravens.com/team/depth-chart, lists **Jacoby Brissett, Joe Fagnano and Kedon Slovis** at QB and neither Jackson nor Huntley. The committed `data/depth-wk11-2026.csv` agrees with the club page. The stale-row flag therefore does not apply to the current chart. The transactions-log comparison was not re-run in this pass.
- **Lions blanks (Kerby Joseph, Cade Mays, D.J. Reed).** These read **Out** on the live page and were already Out in the committed file. No blank remains.

## Consequences in the published site

The regenerated depth join (`tools/depth.py`) moved. The published prose had said 57 Out or Doubtful players on a chart, 40 at depth 1, 19 clubs and 19 absent; the depth tool's own output at the committed snapshot was 58 and 40, so the prose and the tool disagreed (F-42). The rebuilt values are **62 of 81** on a chart, **41** at depth 1 (23 offense, 18 defense), **20** clubs with a listed starter out or doubtful, and **20** absent from their chart. Two holes (Tennessee, LG and LB) and zero cascades are unchanged. The README and `research/depth-and-deficiency.md` now quote these values. See F-25 and F-42.

One join is by name only and is flagged (F-42): Michael Burton (CLE) is FB, Calf, Out on the report and RB, depth 3 on the club's own chart. He is counted in the 62 and is not a starter.

The console (`docs/`) carried the same 2026-11-14 read. Its rows were patched to the same 347 values, its static counts were changed from 345 to 347, and `node docs/check.js` passes.

## Limits of this record

- This sandbox cannot reach nfl.com directly (an outbound TLS connection to nfl.com is closed). The read therefore came through the platform's page-fetch tool, which returns the page as text. The capture file is a transcription of that text. It is not the raw HTTP bytes, and the SHA-256 above is of the transcription.
- Every corrected value was transcribed into the capture file and checked by script against the committed file, so a transcription slip would appear as a difference, not pass silently. The first scheduled run of `tools/capture_official.py` on GitHub's runners is the test that stores the raw bytes and hashes.
- The player links in the committed file were carried over unchanged. Only the two new Ravens links (`calais-campbell`, `ronnie-stanley`) were read from this session's page text.
