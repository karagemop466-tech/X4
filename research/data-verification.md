# Data verification

Everything published on this site is traceable to an official NFL page. This document records what was fetched, how each value was checked, and what could not be confirmed.

## Official sources used

| Source | URL | Used for | Retrieved |
|---|---|---|---|
| NFL league standings | <https://www.nfl.com/standings/> | W, L, T, PCT, PF, PA, NET PTS for all 32 teams | 14 Nov 2026 |
| NFL injury reports | <https://www.nfl.com/injuries/> | Week 10 report for all 28 teams playing | 14 Nov 2026 |
| NFL Week 11 schedule | <https://www.nfl.com/schedules/2026/by-week/week-11> | 13 games, kickoff times, networks, international site, teams on bye | 14 Nov 2026 |
| NFL 2026 schedule | <https://www.nfl.com/schedules/2026/> | Season schedule and results index | 14 Nov 2026 |
| NFL team directory | <https://www.nfl.com/teams/> | Per-team links in every team table | 14 Nov 2026 |
| NFL news | <https://www.nfl.com/news/> | Starter changes and long-term absences | 14 Nov 2026 |
| NFL Football Operations - rules | <https://operations.nfl.com/rules-officiating/2026-nfl-rulebook> | Game rules (not sportsbook settlement terms) | 14 Nov 2026 |
| Federal Trade Commission - UIGEA | <https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act> | US statute overview (not legal advice) | 14 Nov 2026 |

## Secondary sources, and the rule applied to them

A compact results table from <https://www.footballdb.com/games/index.html?lg=NFL&yr=2026&type=reg> and the game log at <https://www.pro-football-reference.com/years/2026/games.htm> were used to **reconstruct** the week-by-week game log, because the NFL publishes results week by week rather than as one season-long list.

Neither of those pages backs a published value. Instead, every reconstructed score is **proved against the official standings**: a single incorrect score changes at least one team's points for or points allowed, so when all 32 teams match the NFL's own totals on wins, losses, ties, points for, points allowed and net points, every score in the log is correct. `tools/verify.py` runs that check on every build, plus the URL pattern for every row, the games-played count per team, the Week 11 pairing structure and duplicate detection.

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

`site/check.py` - the site gate, which inspects the published HTML directly:

- every rendered table row that holds data contains a link to an official domain (nfl.com, operations.nfl.com or ftc.gov)
- no broken internal links, no missing assets, no non-HTTPS external links
- no external link without `rel="noreferrer"`
- no placeholder markers anywhere in the published pages
- the derived points-per-game columns are arithmetically consistent with the official columns beside them
- the page loads with JavaScript enabled and the filters are wired to the static rows

## Errors the verification caught

Both were found by the harness rather than by reading, and both are recorded here because a verification log that only lists successes is not a verification log.

1. **A swapped score.** The Week 3 game at Buffalo had the two teams' scores transposed. The harness flagged it immediately because Buffalo's official points for did not add up. Fixed, and the check now passes.
2. **A wrong winning-percentage formula.** The first implementation divided wins by games played, which disagreed with NFL.com for the two teams with a tie. NFL.com counts a tie as half a win. The formula was corrected to `(W + 0.5 x T) / G`.
3. **A string-concatenation bug** that divided official points by a concatenated games-played figure, so the points-per-game columns were wrong by a factor of ten. `site/check.py` now checks the arithmetic of all 32 standings rows.
4. **A stale injury-report snapshot.** The official Week 10 injury report is updated by the league during the week. Re-fetching it and diffing line by line against the stored copy found 55 practice-participation changes and one row that had been attributed to the wrong team. The stored copy was regenerated from the fresh snapshot.

## Irregularities found during verification

Recorded in full on the site's *Flagged for review* page and summarised here.

| ID | Irregularity |
|---|---|
| F-01 | Official market betting lines |
| F-02 | Depth-chart string: starter, 2nd, 3rd, 4th |
| F-03 | Players on injured reserve, PUP and NFI |
| F-04 | Two official sources give different absence windows for the same player |
| F-05 | Player-level game logs, snaps, drives and EPA |
| F-06 | Player-prop and parlay strategy performance |
| F-07 | No strategy has passed all seven validation gates |
| F-08 | Model parameters have no official source |
| F-09 | NFL.com deep links of the form /schedules/2026/REG<n>/ silently redirect to the current week |
| F-10 | Weeks 12 to 18 of the 2026 schedule are not published here |
| F-11 | Injury-report policy link carried over from an earlier session was not re-verified |
| F-12 | Repository hygiene at the start of this build |
| F-13 | The published site exists in two copies that could drift apart |
| F-14 | The same two clubs are labelled differently in the two layers |
| F-15 | The X4 Console's no-JavaScript fallback counts were stale |
| F-16 | Two different flagged registers reuse the same identifiers |
| F-17 | The three published layers define three different validation gates |
| F-18 | Market betting lines (spread, total, moneyline) |
| F-19 | Staking / bankroll figures |
| F-20 | ROI and expected-value figures |
| F-21 | Replacement depth: starter, 2nd, 3rd, 4th string |
| F-22 | Demotion gate basis |
| F-23 | Price-snapshot store values are model estimates, not official lines |
| F-24 | The Houston Texans publish their depth chart only as an image |
| F-25 | 19 officially ruled-out players do not appear on their own club's published depth chart |
| F-26 | Clubs disagree on what a depth chart is, and some say so in writing |
| F-27 | A published depth chart is not proof of who started |
| F-28 | Only two position rows have no published replacement, and no row has both starter and backup out |
| F-29 | Player-prop and prop-combination prices |
| F-30 | Prices are from one book and are not official |
| F-31 | Doubled HTML entity in the depth summary text |

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
python3 tools/research.py   # regenerate the written findings
python3 site/check.py       # check the published site
python3 tools/validate.py   # all of the above, plus determinism and hygiene
```

The build is deterministic: the same inputs produce the same tables and the same confidence intervals on every run, which `tools/validate.py` enforces by rebuilding and requiring byte-identical output.

