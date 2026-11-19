# Week 11 official injury report — census of the full 13-game page (2026-11-19)

**Check time:** 2026-11-19 UTC, live read of the official page during this session.
**Official source (one page, all 13 games):** [NFL.com — 2026 NFL Injury Report, Week 11](https://www.nfl.com/injuries/) (page title: "Official Latest NFL Injury Report for Players - Week 11 of the 2026 Season").
**Scope:** structure, per-game table counts and per-game player-row tallies only. **No player-level rows are copied into this file.** Player names, designations and statuses stay on the official page and in the private store described in F-75.
**Method:** the page was read in full (7 text chunks). Each game's club tables were counted from the page text. The row tallies below are **hand tallies**, not parser output. They are recorded so that the next scheduled capture can be checked against them, and they are not a substitute for a hash-verified capture.

## Why this record exists

- Flag F-55 said the Week 11 report was not published. That is no longer true: the page now lists every Week 11 game.
- The repository's Week 11 capture is still the 2026-11-18 partial read (Colts at Texans only, `schema_ok=false`). See [`week11-injury-capture-2026-11-19.md`](week11-injury-capture-2026-11-19.md) and [`live-injury-report-2026-11-19.md`](live-injury-report-2026-11-19.md).
- This census establishes what a complete Week 11 capture must contain. A capture that does not match these counts is partial and must not be used for modelling.

## Per-game census

Game links point to the official NFL.com game page recorded in [`data/schedule-wk11-2026.csv`](../../data/schedule-wk11-2026.csv). **Link check:** the IND @ HOU link was opened in this session and resolves to the official NFL.com Game Center (Prime Video, Nov 19, 8:15PM). The other 12 game links were copied from the schedule file and were **not individually opened** in this session; they remain to be confirmed. Times and networks are as printed on the official injury page.

| # | Game (away @ home) | Kickoff (ET, official page) | Network (official page) | Club sections | Player rows (hand tally) | Official source |
|---|---|---|---|---|---|---|
| 1 | IND @ HOU | Thu 19 Nov, 8:15 PM | Prime Video | 2 player tables | 11 + 15 = 26 | [Official game page](https://www.nfl.com/games/colts-at-texans-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 2 | PIT @ PHI | Sun 22 Nov, 1:00 PM | CBS | 2 player tables | 10 + 15 = 25 | [Official game page](https://www.nfl.com/games/steelers-at-eagles-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 3 | ARI @ KC | Sun 22 Nov, 1:00 PM | CBS | 2 player tables | 12 + 15 = 27 | [Official game page](https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 4 | BAL @ CAR | Sun 22 Nov, 1:00 PM | FOX | 2 player tables | 6 + 13 = 19 | [Official game page](https://www.nfl.com/games/ravens-at-panthers-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 5 | TB @ DET | Sun 22 Nov, 1:00 PM | FOX | 2 player tables | 6 + 8 = 14 | [Official game page](https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 6 | MIA @ BUF | Sun 22 Nov, 1:00 PM | CBS | 2 player tables | 11 + 15 = 26 | [Official game page](https://www.nfl.com/games/dolphins-at-bills-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 7 | TEN @ DAL | Sun 22 Nov, 1:00 PM | FOX | 2 player tables | 9 + 14 = 23 | [Official game page](https://www.nfl.com/games/titans-at-cowboys-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 8 | NO @ CHI | Sun 22 Nov, 1:00 PM | FOX | 2 player tables | 10 + 5 = 15 | [Official game page](https://www.nfl.com/games/saints-at-bears-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 9 | NYJ @ LAC | Sun 22 Nov, 4:05 PM | FOX | 2 player tables | 8 + 11 = 19 | [Official game page](https://www.nfl.com/games/jets-at-chargers-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 10 | JAX @ NYG | Sun 22 Nov, 4:25 PM | CBS | 2 player tables | 13 + 6 = 19 | [Official game page](https://www.nfl.com/games/jaguars-at-giants-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 11 | LV @ DEN | Sun 22 Nov, 4:25 PM | CBS | 2 player tables | 6 + 9 = 15 | [Official game page](https://www.nfl.com/games/raiders-at-broncos-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 12 | MIN @ SF | Sun 22 Nov, 8:20 PM | NBC, UNIVERSO | 2 player tables | 10 + 15 = 25 | [Official game page](https://www.nfl.com/games/vikings-at-49ers-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |
| 13 | CIN @ WAS | Mon 23 Nov, 8:15 PM | ESPN, ABC, ESPN2, ESPN DEPORTES | 2 "No Injuries Reported" sections | 0 | [Official game page](https://www.nfl.com/games/bengals-at-commanders-2026-reg-11) · [Injury page](https://www.nfl.com/injuries/) |

## Totals

| Measure | Value | Source |
|---|---|---|
| Games on the official page | 13 | [Injury page](https://www.nfl.com/injuries/) |
| Games in the repository's Week 11 schedule file | 13 | [`data/schedule-wk11-2026.csv`](../../data/schedule-wk11-2026.csv) |
| Player tables (games with an injury list) | 24 | [Injury page](https://www.nfl.com/injuries/) |
| "No Injuries Reported" sections | 2 (CIN, WAS) | [Injury page](https://www.nfl.com/injuries/) |
| Player rows (hand tally, all 24 tables) | **253** | Hand tally of the page text above |
| Repository Week 11 capture on 2026-11-18 (for comparison) | 26 player links, 2 tables, `schema_ok=false` | [`data/captures/manifest.jsonl`](../../data/captures/manifest.jsonl) |

**Consequence for the pipeline:** the fixed Week 10 pin (28 tables, 250+ links) cannot be met by a 13-game Week 11 page, and a 26-table count is the full Week 11 shape. The T63 coverage check should compare a capture against the 13 games and 24 player tables above, not against the Week 10 total.

## Page-level irregularities (for manual review)

1. **Display name and profile link disagree (Bills).** The Bills table shows "Dee Alford" (CB, Did Not Participate). Its profile link is `https://www.nfl.com/players/deaundre-ford/`. Reviewer should confirm the player identity on the official profile before any name-based join. [Injury page](https://www.nfl.com/injuries/)
2. **Display name and profile link disagree (Texans).** The Texans table shows "Jacob Hummel" (LB, Full Participation / Questionable). Its profile link is `https://www.nfl.com/players/jake-hummel/`. Same action. [Injury page](https://www.nfl.com/injuries/)
3. **Blank game-status cells on Wednesday–Thursday practice rows are expected, not "available".** Game status is only populated for players the club has already designated. Most rows show a practice status and an empty game status, so an empty cell must never be read as "healthy" or "available". This matches the official page's own layout. [Injury page](https://www.nfl.com/injuries/)
4. **Mixed designations are shown on the same page.** The Thursday game shows game statuses (e.g., Questionable, Out) while other games show none. The page is a point-in-time view, not a complete designation history. [Injury page](https://www.nfl.com/injuries/)
5. **Hand-tally caveat.** The 253 figure was tallied by hand from the fetched page text. A parser-confirmed count is required before any tally is used as a validation threshold. Flagged for the next capture run.

## What this record does not do

- It does not copy, transcribe or publish any player row, designation or status.
- It does not change the normalized Week 10 injury dataset, the depth charts, the starter file, the inactive lists, the snap counts, any model, any strategy, or any published line.
- It does not mark the Week 11 injury data as usable. Week 11 player rows stay gated until a complete, hash-verified, fresh capture exists (T65).
- It does not decide the source-terms or private-retention question (F-75).
