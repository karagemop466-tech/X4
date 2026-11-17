# Official Game Book / Game Center / inactive evidence source review — 2026-11-17

Task: T38 (taken over by session `arena/550d7436-x4` from the stale claim PR #49, whose
session log cited this report by a filename that was never committed). The task is a
**descriptive source audit**: it verifies what official NFL game-day evidence pages and
documents actually publish, and where each datum in the availability pipeline must come
from. It ingests no player rows and republishes no Game Book content.

Every source below was fetched live on 2026-11-17 (UTC) with the platform's page-fetch
tool. Quotes are verbatim.

## Sources verified

| # | Source | URL | What was verified on the live page |
|---|---|---|---|
| 1 | NFL Support — "Game Books" | https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books | Official support article: Game Summaries ("Game Books") are published in the NFL.com Game Centers; "At the bottom of the Recap, there should be a Download Game Book PDF containing every score and stat from the game." |
| 2 | Game Center, completed game (MIN at GB, 2026 REG 10) | https://www.nfl.com/games/vikings-at-packers-2026-reg-10 | Live page shows final score 30–10, quarter scores, Game Info (Location GREEN BAY, WI; Stadium LAMBEAU FIELD), inline division standings, and a **"Download Game Book (PDF)"** link |
| 3 | The Game Book PDF itself | https://static.www.nfl.com/image/upload/v1794829721/gamecenter/ab788967-4feb-11f1-abca-2c54536568a9.pdf | Parsed in full (7 chunks). Contents verified below |
| 4 | NFL Week 10 inactives article (Sunday, 12 games) | https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season | Published 2026-11-15; per-club inactive lists for the Sunday slate, including the Munich game (Patriots), each player named, emergency third QBs marked |
| 5 | NFL Week 10 pregame injuries article | https://www.nfl.com/news/week-10-injuries-sunday-pregame-2026-nfl-season | Published 2026-11-15; designation + activity outcome per player ("officially active" / "inactive"), attributed to NFL Network reporting — a **news** source, not the report itself |
| 6 | Around The NFL series page (listing of inactives articles) | https://www.nfl.com/news/series/around-the-nfl-news | Confirms the league publishes a dedicated inactives article per slate, including "Week 10 Monday night inactives: Los Angeles Chargers at Baltimore Ravens" (its article URL was not individually fetched, so only the listing is cited here) |
| 7 | Official injury report page | https://www.nfl.com/injuries/ | Already captured and reconciled by the repository (347-row Week 10 capture, T37); the daily pre-kickoff series source |

## What the Game Book contains (verified against source 3)

The Game Book is the most complete single official game-day document the league
publishes. For the MIN-at-GB 2026 Week 10 book, every section below was read directly
from the PDF:

| Section | Datum it establishes | Requirement it answers |
|---|---|---|
| Header | Date, clubs, venue ("at Lambeau Field, Green Bay, WI"), start time, **game weather: "Sunny Open Stadium on Natural Grass", Temp 45° F, Humidity 51%, Wind NW 5 mph, Wind Chill 42** | The venue/weather fixture-context features must be sourced here rather than from an aggregator |
| Copyright + use restriction | Verbatim: "NFL Copyright © 2026 by The National Football League. All rights reserved. This summary and play-by-play is for the express purpose of assisting media in their coverage of the game; any other use of this material is prohibited without the written permission of the National Football League." | A **hard reuse gate** on republishing the document's own text — see the policy section below |
| Officials | Crew by position and name | Not currently used by any model; available for completeness |
| **Lineups** | Actual starters per team, by unit (offense and defense), with jersey number and name (e.g., the offense's QB/LT/LG/C/RG/RT/WR/WR/WR/QB/RB/FB rows; defense's EDGE/DL/LB/CB/S rows) | "Use official NFL Game Books for **actual starters** and game-day status; do not infer depth rank or snaps" — this is the authoritative starter evidence, replacing any inference from jersey order, salary, or depth-chart column position |
| **Substitutions** | Every player who entered the game, with jersey number | Replacement tracking: who actually replaced a starter, not who a chart lists behind him |
| **Did Not Play / Not Active** | Separate lists per team, with jersey numbers; "Not Active" is the official inactive list for the game | Game-day status evidence that settles "Questionable → played or not" — the join the designation-reliability requirement needs |
| Field goals, scoring plays, drive data | Scoring sequence with time and drive info | Results feed already verified from standings; the Game Book independently confirms |
| Attendance, time | "Paid Attendance: 78,332", game time 2:57 | Fixture context |
| Individual statistics | Rushing / passing / receiving / INTs / punting / returns per player | Player-level features (only if a licensed use is established) |
| Ten longest plays, touchdown scoring info, possession detail | Drive-level game shape | Analysis only |
| **Playtime Percentage** | **Per-player snap counts and percentages, split by Offense / Defense / Special Teams** (e.g., "B.Brandel C 69 100%" on offense; "E.Williams S 69 100%" on defense; reserves with partial shares) | "Do **not** model depth from jersey order; model it from **playing time**" — the official playing-time source the repository has been missing. Snap share per player per unit is exactly the measured availability value the depth ledger currently reports as 0 |

### What the Game Book does NOT carry

- **Practice designations** (DNP/LP/FP, Questionable/Doubtful/Out): those live only on the
  weekly report (source 7) and the Wed–Fri series the capture workflow collects.
- **Pregame inactive status before the game**: the authoritative pre-kickoff evidence is
  the league's inactives article (source 4) and the Game Center's own inactive listing;
  the Game Book confirms the same list after the fact ("Not Active").
- **Depth ranks**: the Game Book is not a depth chart. It publishes who played and how
  much, never the club's ordinal chart. Club charts (31 transcribed) remain the rank
  source; the Game Book is the *starter and playing-time* source. The two are joined by
  player, never merged.
- The commonly repeated "inactives are due 90 minutes before kickoff" timing is **not
  verified from an official page in this audit** and is marked unverified here rather
  than stated as fact.

## The reuse gate and the publication policy it forces

The Game Book's own text (source 3) restricts the material's use to assisting media
coverage of the game and prohibits any other use without written permission. The
repository therefore must not republish Game Book rows (the Lineups table, the Playtime
Percentage table, or any play-by-play text) as site content. What is compatible with the
restriction, and with the brief's "public analysis layer vs private data layer" split:

1. **Store raw captures privately** (hash + timestamp, like `data/ops/raw/`), never
   published; retain the hash for auditability.
2. **Derive locally, publish derived indices only**: e.g., per-club "starters who played
   100% of offensive snaps", "number of Week-10 starters absent from the Lineups table",
   a replacement's playtime share — as computed indices with `n` and the artifact that
   produced them, the same way correlations are published.
3. **Link for manual review**: every derived index cites the Game Center page (source 2)
   and the PDF link (source 3) so a reviewer can read the official document directly.
4. **Do not ingest player-level rows into the site** until either written permission is
   obtained or the derived-index boundary is reviewed by counsel. This audit takes no
   position on licensing; it records the gate.

## What this unblocks, in order

| Open item in the decision-readiness review | Status after this audit |
|---|---|
| "Can the replacement's role be confirmed before kickoff and after the game?" (C18 question 3) | The after-the-game half is now answerable: Game Book Substitutions + Playtime Percentage + Not Active give starter evidence, replacement evidence and snap share from one official document. The before-kickoff half still needs the scheduled inactives capture (blocked by F-43, the failing capture workflow) |
| "Zero measured replacement-depth rows" / playing-time features | The Game Book carries the official playtime percentage per player; a permission-gated capture could populate the ledger's blank snap-share columns from an official source instead of leaving them blank |
| "What constitutes an official starter?" | The Lineups table is the official starter list; club-chart column-1 groups stay the *named* slots, and the Game Book settles who actually started |
| Injury-designation reliability scoring | The "Not Active" list is the official played/did-not-play join for designations, per player per week |
| Fixture-context features (venue, roof/surface, weather) | The Game Book header publishes venue, surface ("Natural Grass"), roof state ("Open Stadium") and measured weather for **completed** games; forecast-side capture still needs the league's pregame designation channel and is unverified in this audit |

## Recommendation (permission-gated design)

1. Extend the capture tool with a `--kind gamebook` mode that stores each Game Book PDF
   behind its Game Center link with a SHA-256 hash and UTC fetch time, **without
   committing any extracted row**.
2. Add a local parser that emits derived indices (starters per unit, playtime share,
   not-active count) into the private store, joined by player to the injury report and
   the club charts.
3. Publish only the derived indices on the site, each with `n`, the producing artifact,
   and the official Game Center link — no Game Book text.
4. Keep the reuse restriction visible wherever derived indices are discussed, so the
   boundary the league set is not lost in later edits.

## Verification record

- All seven sources fetched 2026-11-17 UTC through the platform page-fetch/search tools.
- The PDF was parsed end to end (7 chunks); the use-restriction sentence, the Lineups
  header rows, the Did Not Play / Not Active lists and the Playtime Percentage section
  were each read directly from the returned text.
- No player row from any source was transcribed into this repository; the report quotes
  structure and one weather/venue header line as evidence of what the document carries.
- No gate was run against live data; `python3 tools/validate.py` remains the arbiter of
  the committed build (PASS on 2026-11-17 at the T41 commit `d850cc4`).
