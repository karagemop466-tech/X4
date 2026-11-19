# Week 11 official injury report: live read, 2026-11-19 (T66)

**Session:** `arena/d47a356c-x4` · **Read time:** 2026-11-19 19:29 UTC (page fetched in seven chunks within the same session)
**Official source (every row below relates to this page):** https://www.nfl.com/injuries/league/2026/reg11
**Schedule cross-check:** https://www.nfl.com/schedules/2026/by-week/week-11 (13 games; repo file `data/schedule-wk11-2026.csv`)

## What this record is, and is not

- It records **coverage**: which of the 13 scheduled Week 11 games the official page shows, and how many player rows sit under each club, as read from the live page.
- It does **not** transcribe any designation, practice status or game status into a dataset. No Week 11 row is added to `data/`, `site/` or the public tables. The public Week 11 gate (T65, F-61, F-83) stays as it was.
- Counts were made by reading the seven fetched chunks of the page, not by a script run on the raw HTML. The raw HTML is not reachable from this sandbox (the network allowlist does not include nfl.com). A byte-level, script-verified capture therefore still requires the scheduled official-capture workflow.

## Coverage: 13 of 13 games, 26 of 26 clubs

| Day & time (ET) · network | Game | Away rows | Home rows | Rows in game | Page shows |
|---|---|---:|---:|---:|---|
| Thu 19 Nov 8:15 PM · Prime Video | IND @ HOU | 11 | 15 | 26 | club tables for both |
| Sun 22 Nov 1:00 PM · CBS | PIT @ PHI | 10 | 15 | 25 | club tables for both |
| Sun 22 Nov 1:00 PM · CBS | ARI @ KC | 12 | 15 | 27 | club tables for both |
| Sun 22 Nov 1:00 PM · FOX | BAL @ CAR | 6 | 13 | 19 | club tables for both |
| Sun 22 Nov 1:00 PM · FOX | TB @ DET | 6 | 8 | 14 | club tables for both |
| Sun 22 Nov 1:00 PM · CBS | MIA @ BUF | 11 | 15 | 26 | club tables for both |
| Sun 22 Nov 1:00 PM · FOX | TEN @ DAL | 9 | 14 | 23 | club tables for both |
| Sun 22 Nov 1:00 PM · FOX | NO @ CHI | 10 | 5 | 15 | club tables for both |
| Sun 22 Nov 4:05 PM · FOX | NYJ @ LAC | 8 | 11 | 19 | club tables for both |
| Sun 22 Nov 4:25 PM · CBS | JAX @ NYG | 13 | 6 | 19 | club tables for both |
| Sun 22 Nov 4:25 PM · CBS | LV @ DEN | 6 | 9 | 15 | club tables for both |
| Sun 22 Nov 8:20 PM · NBC, Universo | MIN @ SF | 10 | 15 | 25 | club tables for both |
| Mon 23 Nov 8:15 PM · ESPN | CIN @ WAS | 0 | 0 | 0 | "No Injuries Reported" for both clubs |
| **Total** | **13 games** | | | **253 player rows** | **26 club sections** |

The 26 clubs with a section are the 26 clubs playing in the 13 games. The six clubs without one (ATL, CLE, GB, LAR, NE, SEA, as listed on the repository's own site text) are on bye. The bye list itself was not re-read from the schedule page in this task.

The game list matches `data/schedule-wk11-2026.csv` exactly (13 of 13 matchups, same days and kickoff times). Cross-check: the schedule file marks MIN @ SF as an international game ("Mexico City"). The injury page carries no venue, so this record neither confirms nor contradicts it; the venue question is left to the existing venue flags.

## What this changes in the repository's claims

- The repository's Week 11 status (F-55, F-61, T65 and the landing-page readiness row) says the Week 11 report is unpublished or partial. **On this read, the official page is published for all 13 games.** The repository still holds only the partial 2026-11-18 capture (two club tables). That is a stale repository state, not a source fact, and it is recorded here for the integration session to correct. Nothing in `site/` was edited by this task.
- F-69 (Game Center widget reads "no active injuries" for a club whose report lists injuries) concerns the Week 10 report and was not re-tested here.

## Irregularities noticed on the live page (flagged, not corrected)

1. **Name and profile link differ for one Bills player.** The row reads "Dee Alford" (CB), and its profile link is `nfl.com/players/deaundre-ford/`. It may reflect a legal name, but this read cannot confirm that. Flagged for manual review.

No other irregularity was found in this read. Blank game-status cells appear for players with a practice status and no injury, which is how the page presents them, so they are not flagged.

## Sources used in this record

- Official NFL injury report, Week 11: https://www.nfl.com/injuries/league/2026/reg11 (read 2026-11-19, seven chunks)
- Official NFL schedule, Week 11: https://www.nfl.com/schedules/2026/by-week/week-11 (the repo file `data/schedule-wk11-2026.csv` was checked against it)
- Official per-game links (from the schedule file): https://www.nfl.com/games/colts-at-texans-2026-reg-11 and the other twelve `nfl.com/games/...-2026-reg-11` pages

## Verification performed

- Read all seven chunks of the live page; counted the club tables and player rows per game by reading them.
- Matched the 13 game headers against `data/schedule-wk11-2026.csv`: 13 of 13 matchups, days and times.
- Confirmed the club count: 13 games × 2 clubs = 26 club sections, the 26 clubs not on bye.
- Not verified here: the content of each designation (no transcription), the venue of any game, and the script-level byte hash of the page.

## Limits

This is one manual read of one page at one time. It is not a capture: it has no retained hash, no timestamp from the capture pipeline, and no raw bytes. The scheduled official-capture workflow (`.github/workflows/capture.yml`) remains the only route to a verified snapshot, and its Week 11 freshness gate (F-83) is still open.
