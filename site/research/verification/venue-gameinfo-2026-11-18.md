# Week 11 venue verification against the official Game Info block — 2026-11-18

Task T48, session `arena/5534e2ba-x4`. Every row below was read from the official
NFL.com **game centre** page for that fixture, in the "Game Info" block, which publishes
`LOCATION` and `STADIUM` as two separate labelled fields. The committed dataset
`data/venues-wk11-2026.csv` is compared against those two fields, cell for cell.

Machine-readable copy: `research/verification/venue-gameinfo-2026-11-18.csv`
(13 rows, the exact published string and the exact committed string side by side).
All pages were read 2026-11-18 UTC with the page-fetch tool. The sandbox cannot open a
socket to `nfl.com`, so this is a **rendered-page read**, not a hash-verified capture —
the same limitation recorded for F-47/F-48/F-61 and for the T46 re-verification.

## Result

| Fixture | Official `LOCATION` | Official `STADIUM` | Committed | Agrees |
|---|---|---|---|---|
| Colts at Texans | HOUSTON, TX | RELIANT STADIUM | same | yes |
| Dolphins at Bills | ORCHARD PARK, NY | HIGHMARK STADIUM | same | yes |
| Ravens at Panthers | CHARLOTTE, NC | BANK OF AMERICA STADIUM | same | yes |
| Saints at Bears | CHICAGO, IL | SOLDIER FIELD | same | yes |
| Titans at Cowboys | ARLINGTON, TX | AT&T STADIUM | same | yes |
| Buccaneers at Lions | DETROIT, MI | FORD FIELD | same | yes |
| Cardinals at Chiefs | KANSAS CITY, MO | ARROWHEAD STADIUM | same | yes |
| Steelers at Eagles | PHILADELPHIA, PA | LINCOLN FINANCIAL FIELD | same | yes |
| Jets at Chargers | INGLEWOOD, CA | SOFI STADIUM | same | yes |
| Jaguars at Giants | EAST RUTHERFORD, NJ | METLIFE STADIUM | same | yes |
| Raiders at Broncos | DENVER, CO | EMPOWER FIELD AT MILE HIGH | same | yes |
| Vikings at 49ers | MEXICO CITY | ESTADIO BANORTE | same | yes |
| Bengals at Commanders | LANDOVER, MD | NORTHWEST STADIUM | same | yes |

**13 of 13 fixtures agree on both the city and the stadium string. 0 disagreements.**
The dataset was not edited: there was nothing to change.

## The F-60 question, answered

F-60 recorded that the *Week 11 schedule page* names **NRG Stadium** and **GEHA Field at
Arrowhead Stadium** in its ticket and hotel links for the Houston and Kansas City
fixtures, while the committed dataset says RELIANT STADIUM and ARROWHEAD STADIUM.

Read on 2026-11-18, the official schedule page still links
`destinationAddress.location=NRG+Stadium`
(<https://www.nfl.com/schedules/2026/by-week/week-11>) and the game centre still prints
`StadiumSTADIUMRELIANT STADIUM` and `StadiumSTADIUMARROWHEAD STADIUM`.

That is not a contradiction to be resolved by picking a winner, and it is not a
transcription error in either direction:

- The **game centre Game Info block** is the field this dataset transcribes, and it
  carries the older names. The committed values reproduce it exactly.
- The **ticket/hotel deep links** on the schedule page are venue-booking metadata
  (Ticketmaster and Marriott destination strings) that carry the venues' current
  commercial names. They are a different field on a different page.

A club's or venue's in-use name (NRG Stadium; GEHA Field at Arrowhead Stadium) is a
naming preference, not a relocation or a different building. Because the project's rule
is *transcribe the official field, never rename by inference*, the dataset keeps the
Game Info string, and the two names are published side by side here rather than
silently swapped.

**F-60 resolved as a naming difference, with the verification recorded.** What remains
open is a modelling question, not a data question: if a venue name is ever used as a
feature (roof, surface, altitude — the stadium overlay in the suggestions queue), the
model must key on a stable venue id, not on a name string that two official pages spell
differently. That is recorded as the residual below.

## Irregularities found during this verification

1. **Two official NFL.com pages spell two venues differently** (game centre vs schedule
   page deep links). Neither value is wrong; a name-based join between them would fail.
   Published as flag **F-60**, now marked resolved-as-naming-difference with this
   verification linked.
2. **The `state` field is blank for the Mexico City fixture** in
   `data/venues-wk11-2026.csv`. The official Game Info block publishes `MEXICO CITY`
   as the location and does not publish a US state, so a blank cell is the faithful
   transcription. It is left blank rather than filled with a guess, and is now named
   on this page so it is not mistaken for an omission.
3. **A separate internal-consistency defect was found on the same day** on
   `readiness.html`: its "what would change our mind" keep table published hard-coded
   values (`n = 12`, `p = 0.0918`, `largest week 90 percent`) that contradicted the gate
   table directly above it reading the same three measurements from
   `data/ops/gates.csv` (`n = 24`, `p = 0.1028`, `largest week = 58%`). The keep table now
   reads the committed gate file. That is flag **F-71** and it is a page-generator fix,
   not a data change; no published measurement moved, the page's account of itself
   was made consistent with its own source.
