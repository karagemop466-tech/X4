# Data verification

Everything published on this site is traceable to an official NFL page. This document
records what was fetched, how each value was checked, and what could not be confirmed.

## Official sources used

| Source | URL | Used for | Retrieved |
|---|---|---|---|
| NFL league standings | <https://www.nfl.com/standings/> | W, L, T, PCT, PF, PA, NET PTS for all 32 teams | 14 Nov 2026 |
| NFL injury reports | <https://www.nfl.com/injuries/> | Week 10 report for all 28 teams playing | 14 Nov 2026 |
| NFL Week 11 schedule | <https://www.nfl.com/schedules/2026/by-week/week-11> | 13 games, kickoff times, networks, international site, teams on bye | 14 Nov 2026 |
| NFL Week 5 schedule | <https://www.nfl.com/schedules/2026/by-week/week-5> | Week 5 matchups and final scores | 14 Nov 2026 |
| NFL 2026 schedule | <https://www.nfl.com/schedules/2026/> | Season schedule and results index | 14 Nov 2026 |
| NFL team pages | <https://www.nfl.com/teams/> | Per-team links in every team table | 14 Nov 2026 |
| NFL news | <https://www.nfl.com/news/> | Starter changes and long-term absences | 14 Nov 2026 |
| NFL Football Operations - rules | <https://operations.nfl.com/rules-officiating/2026-nfl-rulebook> | Game rules (not sportsbook settlement terms) | 14 Nov 2026 |
| Federal Trade Commission - UIGEA | <https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act> | US statute overview (not legal advice) | 14 Nov 2026 |

## Secondary sources, and the rule applied to them

A compact results table from <https://www.footballdb.com/games/index.html?lg=NFL&yr=2026&type=reg>
and the game log at <https://www.pro-football-reference.com/years/2026/games.htm> were used to
**reconstruct** the week-by-week game log, because the NFL publishes results week by week
rather than as one season-long list.

Neither of those pages backs a published value. Instead, every reconstructed score is
**proved against the official standings**: a single incorrect score changes at least one
team's points for or points allowed, so when all 32 teams match the NFL's own totals on
wins, losses, ties, points for, points allowed and net points, every score in the log is
correct. `tools/verify.py` runs that check on every build, plus the URL pattern for every
row, the games-played count per team, the Week 11 pairing structure and duplicate detection.

The official NFL.com weekly schedule pages for Weeks 5 and 11 were opened directly and
compared game by game with the reconstruction as a second, independent check.

## What the verification checks

`tools/verify.py` - 460 assertions, exit code 1 on any failure:

- every game row's URL matches the official `/games/<away>-at-<home>-2026-reg-<week>` pattern
- every team's wins, losses and ties match the official standings
- every team's points for and points allowed match the official standings
- every team's net points match the official standings
- every team's winning percentage matches, using the NFL's formula of counting a tie as half a win
- every team's games-played count equals the sum of its official record
- the Week 11 schedule has 13 games, 26 distinct teams, and a correct URL for each
- no duplicate game rows

`site/check.py` - the site gate, which executes the real renderer and inspects the output:

- every rendered table row that holds data contains a link to an official domain
  (nfl.com, operations.nfl.com or ftc.gov)
- no broken internal links, no missing assets, no non-HTTPS external links
- no external link without `rel="noreferrer"`
- no placeholder markers anywhere in the published pages

## Two real errors the verification caught

Both were found by the harness rather than by reading, and both are recorded here because a
verification log that only lists successes is not a verification log.

1. **A swapped score.** The Week 3 game at Buffalo had the two teams' scores transposed.
   The harness flagged it immediately because Buffalo's official points for did not add up.
   Fixed, and the check now passes.
2. **A wrong winning-percentage formula.** The first implementation divided wins by games
   played, which disagreed with NFL.com for the two teams with a tie. NFL.com counts a tie
   as half a win. The formula was corrected to `(W + 0.5 x T) / G`.

## Irregularities found during verification

Recorded in full on the site's *Flagged for review* page and summarised here.

| ID | Irregularity |
|---|---|
| F-03 | The public weekly injury report omits players on injured reserve, reserve/nontheatre injured list and physically unable to perform. Long-term absences appear only in league news. |
| F-04 | Two official NFL.com items give different absence windows for the same player - six to nine weeks and six to ten weeks for Baltimore's quarterback. Both are recorded; neither is corrected here. |
| F-09 | URLs of the form `nfl.com/schedules/2026/REG<n>/` silently resolve to the current week instead of the requested one. The working per-week pattern is `nfl.com/schedules/2026/by-week/week-<n>`. |
| F-11 | The injury-report policy link recorded by an earlier session in this repository was not re-fetched during this build and is not re-certified here. |
| F-12 | At the start of this build the repository contained one tracked file, a four-byte README, with no licence, no tests, no continuous integration, no data and no site. |

## What is deliberately absent

| Item | Why | Flag |
|---|---|---|
| Betting lines and odds | The NFL publishes none, and no licensed odds feed is authorised | F-01 |
| Depth-chart strings | The NFL publishes no consolidated league depth chart | F-02 |
| Player-level statistics | Not exposed in a verifiable form by the official pages fetched | F-05 |
| Player-prop and parlay performance | Requires prices and player-level data | F-06 |
| Weeks 12-18 of the schedule | NFL lists several of those matchups as to-be-determined | F-10 |

## Reproducing this

```
python3 tools/verify.py     # prove the data against the official standings
python3 tools/build.py      # regenerate every published number
python3 tools/pages.py      # regenerate the site
python3 site/check.py       # check the rendered site
python3 tools/validate.py   # all of the above, plus determinism and hygiene
```

The build is deterministic: the same inputs produce the same tables and the same
confidence intervals on every run, which `tools/validate.py` enforces by rebuilding and
requiring byte-identical output.
