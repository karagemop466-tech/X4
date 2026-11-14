# Sources register

Every official page used by this repository, what it was used for, and when it was
retrieved. Every table row on the published site links to one of these, or to a more
specific page beneath it (a single game, a single team, a single player, a single article).

## Official NFL sources

| Source | URL | Used for |
|---|---|---|
| NFL league standings | <https://www.nfl.com/standings/> | Every team's W, L, T, PCT, PF, PA and net points |
| NFL injury reports | <https://www.nfl.com/injuries/> | Week 10 report: player, position, injury, practice code, game status |
| NFL Week 11 schedule | <https://www.nfl.com/schedules/2026/by-week/week-11> | The 13 Week 11 games, kickoff times, networks, international site, teams on bye |
| NFL Week 10 schedule | <https://www.nfl.com/schedules/2026/by-week/week-10> | The completed Week 10 games |
| NFL Week 5 schedule | <https://www.nfl.com/schedules/2026/by-week/week-5> | Week 5 matchups and final scores, used as an independent check |
| NFL 2026 season schedule | <https://www.nfl.com/schedules/2026/> | Season schedule and results index |
| NFL team directory | <https://www.nfl.com/teams/> | Per-team links in every team table |
| NFL statistics | <https://www.nfl.com/stats/> | Reference for the player-level and team-level data this build does not have (flag F-05) |
| NFL team statistics | <https://www.nfl.com/stats/team-stats/> | Reference for drive and possession data this build does not have |
| NFL news | <https://www.nfl.com/news/> | Starter changes and long-term absences the injury report omits |

### Individual game, team, player and article links

These are the row-level sources. Each table row on the site links to one of them.

- Game pages follow the official pattern `https://www.nfl.com/games/<away>-at-<home>-2026-reg-<week>`,
  for example <https://www.nfl.com/games/commanders-at-giants-2026-reg-10>.
- Team pages follow `https://www.nfl.com/teams/<team-slug>/`, for example
  <https://www.nfl.com/teams/buffalo-bills/>.
- Player pages follow `https://www.nfl.com/players/<player-slug>/`, for example
  <https://www.nfl.com/players/josh-jacobs-x3315/>.
- News articles use their published URL, for example
  <https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders>.

### The specific league items captured

| Item | URL |
|---|---|
| Drew Lock has no injury designation and will start for Seattle | <https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders> |
| Sam Darnold ruled out for Week 10; Drew Lock expected to start again | <https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again> |
| Ravens confirm Lamar Jackson expected to miss 6-10 weeks | <https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13> |
| Ravens' Lamar Jackson out 6-9 weeks (conflicting window, flag F-04) | <https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season> |
| Browns to start QB Deshaun Watson; Cardinals' Carson Beck to start | <https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11> |
| Dolphins place Malik Willis on injured reserve; Kyle McCord in line for first start | <https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start> |
| Rams WR Puka Nacua likely to be placed on injured reserve | <https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl> |
| Packers RB Josh Jacobs to undergo finger surgery | <https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week> |
| Injury-report policy revisions (carried over from an earlier session, not re-verified - flag F-11) | <https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693> |

## Other official sources

| Source | URL | Used for |
|---|---|---|
| NFL Football Operations - 2026 NFL Rulebook | <https://operations.nfl.com/rules-officiating/2026-nfl-rulebook> | The official rules of the games. These are not sportsbook settlement terms, and the difference is stated on the site. |
| Federal Trade Commission - UIGEA overview | <https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act> | A US federal statute overview. It is not legal advice and not a determination for any jurisdiction, and the site says so. |
| NFL flexible scheduling procedures | <https://www.nfl.com/legal/flexible-scheduling-procedures> | The league's own explanation of why some late-season dates and times are only fixed later. |

## Secondary sources, and what they were allowed to do

| Source | URL | Allowed to | Not allowed to |
|---|---|---|---|
| The Football Database | <https://www.footballdb.com/games/index.html?lg=NFL&yr=2026&type=reg> | Reconstruct the week-by-week game log, which was then proved against the official standings | Back any published value |
| Pro Football Reference | <https://www.pro-football-reference.com/years/2026/games.htm> | Cross-check the reconstructed game log and locate box-score links | Back any published value |

The distinction matters. A reconstructed score that is later proved against the official
NFL standings is verified data. A score copied from an aggregator and published because it
looked right is not, and the site does not do the second thing anywhere.

## Sources deliberately not used

| Source | Why not |
|---|---|
| Commercial sportsbook odds pages | Not official, not timestamped in this build, and no licensed feed has been authorised. Flag F-01. |
| Fantasy and prediction aggregator sites | Not official, and their projections are exactly the kind of model output this project must generate itself to avoid circularity. |
| Any undated or unverifiable page | Fails the retrieval-timestamp rule; nothing published here is undated. |
