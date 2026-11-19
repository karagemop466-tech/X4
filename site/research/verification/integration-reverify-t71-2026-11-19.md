# T71 live spot re-verification against official NFL.com pages — 2026-11-19 (session `arena/c0a6d543-x4`)

Dated record of the live checks run during the T71 final-integration pass. Every
check below was read from the official page in this session through the
page-fetch tool (the bash sandbox cannot reach nfl.com); nothing was inferred or
filled in. Values that could not be confirmed are left blank and flagged.

## 1. Week 10 schedule and finals — 14/14 games match the committed log

Source: https://www.nfl.com/schedules/2026/by-week/week-10 (read 2026-11-19, 2 chunks).

Every final on the official page was compared with `data/games-2026.csv`
(week 10, columns `away`, `home`, `away_pts`, `home_pts`):

| Game | Official page | data/games-2026.csv | Match |
|---|---|---|---|
| WAS @ NYG | Commanders 24, Giants 21 | 24–21 | yes |
| NE @ DET (Munich) | Patriots 10, Lions 35 | 10–35 | yes |
| KC @ ATL | Chiefs 35, Falcons 13 | 35–13 | yes |
| HOU @ CLE | Texans 24, Browns 27 | 24–27 | yes |
| MIN @ GB | Vikings 30, Packers 10 | 30–10 | yes |
| MIA @ IND | Dolphins 22, Colts 24 | 22–24 | yes |
| CAR @ NO | Panthers 20, Saints 17 | 20–17 | yes |
| BUF @ NYJ | Bills 31, Jets 12 | 31–12 | yes |
| JAX @ TEN | Jaguars 40, Titans 23 | 40–23 | yes |
| LAR @ ARI | Rams 34, Cardinals 6 | 34–6 | yes |
| SEA @ LV | Seahawks 21, Raiders 13 | 21–13 | yes |
| SF @ DAL | 49ers 46, Cowboys 40 | 46–40 | yes |
| PIT @ CIN (SNF) | Steelers 18, Bengals 38 | 18–38 | yes |
| LAC @ BAL (MNF) | Chargers 23, Ravens 20 | 23–20 | yes |

Week 10 byes on the official page: CHI, DEN, PHI, TB.

## 2. Week 11 schedule — 13/13 rows match the committed schedule

Source: https://www.nfl.com/schedules/2026/by-week/week-11 (read 2026-11-19, chunk 0–1 of 3).

All 13 rows of `data/schedule-wk11-2026.csv` match the live page on matchup,
date, kickoff time and network: IND @ HOU (Thu 11-19, 8:15 PM, PRIME);
MIA @ BUF, BAL @ CAR, NO @ CHI, TEN @ DAL, TB @ DET, ARI @ KC, PIT @ PHI
(Sun 11-22, 1:00 PM; CBS/FOX as published); NYJ @ LAC (4:05 PM, FOX);
JAX @ NYG, LV @ DEN (4:25 PM, CBS); MIN @ SF (8:20 PM, NBC, Mexico City
international designation present on the official page); CIN @ WAS
(Mon 11-23, 8:15 PM, ESPN). No row was edited.

## 3. Official Week 11 injury report page — state confirmed

Source: https://www.nfl.com/injuries/ (read 2026-11-19 in this session; page
title "Official Latest NFL Injury Report for Players - Week 11 of the 2026
Season | NFL.com").

- The page is published for Week 11 with per-game club tables.
- Spot counts against the two hand censuses (PR #134 / PR #136 records):
  Colts 11 rows + Texans 15 rows = 26 for IND @ HOU (census: 26) and
  Steelers 10 + Eagles 15 = 25 for PIT @ PHI (census: 25). Consistent.
- The F-90 name irregularity was seen live in the Texans table: displayed
  "Jacob Hummel" links to `jake-hummel`. Not resolved here; identity
  confirmation is required before any name-based join.
- Game Status cells on Wednesday/Thursday practice rows are blank on the
  official page. Blank stays blank; it is never read as available.

## 4. Capture-manifest state re-read at integration time

`data/captures/manifest.jsonl` (256 rows after integrating PR #122's 32
workflow rows byte-for-byte): latest injuries read 2026-11-19T20:43:30Z,
HTTP 200, week 11, 24 club tables, 253 player links, `schema_ok=true`,
`coverage=partial` with `games_published=12` of 13 scheduled, and
`raw_retained=false`. The parser's 12-game coverage count disagrees with the
two hand censuses (13 game sections; the 13th carries the two "No Injuries
Reported" sections). Recorded as flag F-90; not resolved by inference.

## 5. Repository gates run in this session (all green)

- `tools/verify.py` — 486 assertions, 150 games, 32 teams: PASS (every club's
  W/L/T/PF/PA reproduces the official totals).
- `tools/audit_score_staleness.py` — PASS on the current corpus against the
  independent dated capture `research/verification/standings-live-2026-11-18.csv`
  (32/32 clubs reproduce).
- `tools/validate.py` — VALIDATION PASSED end to end (deterministic
  regeneration to a fixed point, mirrors in step, console publishable).
- `tools/check_site.py` — 30 desk pages (escrow.html included since T71),
  1,173 table rows, nav consistent, all local links resolve.

## Limits of this record

- The 253-row Week 11 census is two other sessions' hand tally (PR #134,
  PR #136), spot-checked here on two games only; it is not re-tallied.
- No player-level Week 11 row was transcribed into any dataset in this session.
- Freshness results are dated; re-run at use time.
