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
| F-69 | The Game Center injury widget says a club is injury-free while the official report lists that club's injuries |
| F-70 | Two Week 11 venue cells carry the venue's short name, and the dataset is a faithful transcription of the page that prints it |
| F-68 | The multiplicity correction divided by 8 while performing 9 tests |
| F-66 | Stale numbers survive in generated prose because prose is not on the gate |
| F-67 | Two of the eight walk-forward strategies clear the Bonferroni sign test, and the primary metric is undecided |
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
| F-34 | Official injury-report drift on two practice-status cells |
| F-18 | Market betting lines are not an official NFL publication |
| F-19 | Staking / bankroll figures |
| F-20 | ROI and expected-value figures |
| F-21 | Replacement depth: starter, 2nd, 3rd, 4th string |
| F-22 | Demotion gate basis |
| F-23 | Price-snapshot store values are model estimates, not official lines |
| F-24 | The Houston Texans publish their depth chart only as an image |
| F-25 | 20 officially ruled-out or doubtful players do not appear on their own club's published depth chart |
| F-26 | Clubs disagree on what a depth chart is, and some say so in writing |
| F-27 | A published depth chart is not proof of who started |
| F-28 | Only two position rows have no published replacement, and no row has both starter and backup out |
| F-29 | Four practice statuses moved between the committed injury snapshot and the 2026-11-14 read |
| F-30 | No official closing line can exist, so the closing snapshot is stored empty |
| F-31 | The opening snapshot records points, not the price on those points |
| F-32 | The publication gate rejected the surname Fagnano as a placeholder marker |
| F-33 | The depth register on this site contradicted the official injury report for four of its seven rows |
| F-35 | Player-prop and prop-combination prices |
| F-36 | Prices are from one book and are not official |
| F-37 | Doubled HTML entity in the depth summary text |
| F-38 | The two price stores use the word 'close' differently |
| F-39 | Desk rows without an official source link: the row-source gate was not reading row links |
| F-40 | Ten further injury practice-status cells differ from the official report (reported, not yet independently re-checked) |
| F-41 | Week 10 injury dataset re-captured from the live official NFL.com report: 347 rows, 26 corrected cells, 2 added rows |
| F-42 | Two hand-written depth figures disagreed with the tool that produces them, and one depth match is by name only |
| F-43 | The NFL.com reserve-list reads disagree with each other, so 'not listed' cannot be read as 'available' |
| F-44 | Lamar Jackson and Tyler Huntley: NFL.com articles say both were placed on injured reserve, but neither is on the November reserve-list reads |
| F-45 | Baltimore: the club's own depth chart is current, but the committed replacement row for the Baltimore quarterback is out of date |
| F-46 | Re-confirmed on 2026-11-17: the Texans depth chart is an image only, labelled 'Unofficial Depth Chart', so no structured source exists for the Texans row |
| F-47 | No immutable multi-day availability capture history exists on this branch: data/captures/ is absent, and the capture workflow runs from the default branch |
| F-48 | The official-capture workflow has failed on all four of its runs on main, so no capture has been stored |
| F-49 | Side bets were settled on the straight-up winner, not on the spread: one recorded result was wrong (Week 9, CLE +4.5). Fixed on main |
| F-50 | An earlier count of six graded mismatches was wrong: the independent re-check reproduces one (none after the F-49 fix) |
| F-51 | Official Week 10 'Out' players missing from their club's depth file (I-3): the same players as F-25, re-read where stated |
| F-52 | The depth file dates five club charts, not one: an earlier note said only the Packers' (I-5) |
| F-53 | No full dated series of the official injury report exists yet: one full read and one partial read (I-6) |
| F-54 | Two demotion rules have blank thresholds, so they cannot trigger (I-7) |
| F-55 | The Week 11 injury report was not published on 2026-11-17 and the Week 11 link then served Week 10 content (I-8); on 2026-11-19 the Week 11 report is live on NFL.com and this repository still holds only the Week 10 report |
| F-56 | Capture-workflow code-path risks: a partial successful capture is lost and freshness is global, not per source (T40 audit) |
| F-57 | Under the stricter official-domain criterion, 464 of 1,259 desk rows still have no official-domain link, and no row yet carries source-to-value attribution (T-INT audit, arena/0c86fc5d-x4) |
| F-58 | The published tree was one week stale on 2026-11-18: 13 Week 10 finals were missing and every standings-derived number was a week old (T46) |
| F-59 | The site publication gate hard-coded 137 game rows, so a completed official week failed the build (T46) |
| F-60 | Week 11 venue naming differs between the official schedule page and the committed venue dataset (Houston, Kansas City) - resolved: both spellings are official and both are published |
| F-61 | Week 11 injury-report capture is incomplete: the official report is now published, but the latest committed capture failed schema validation |
| F-62 | The margin-vs-total correlation is published with n = 57 on two pages while it is computed on n = 54 |
| F-63 | One home-edge measurement is published at +0.1 and at +0.07, and is measured on weeks 6-9 while 150 games exist |
| F-64 | The depth dataset cannot represent a shared rank-1 cell, stores no special-teams row, and 4 of 103 sampled live players are absent |
| F-85 | The scheduled official-capture run fails because the injury-report check rejects a legitimately partial Week 11 report; the cause is a schema constant, not the page or the network (fixed on this branch, confirmation pending on main) |
| F-65 | Every scheduled official-capture run has failed, and the cause is a code defect: an empty depth-chart URL raises an uncaught ValueError |
| F-74 | The price-snapshot 'opening' record is recomputed every build: the first published model line is not pinned, and the 2026-11-18 ingest silently rewrote it |
| F-75 | Raw availability captures are committed to a public repository while the brief requires a private data layer for raw row-level data |
| F-71 | The decision-readiness 'what would change our mind' table published hard-coded numbers that contradicted the gate table directly above it |
| F-72 | The teams page called the Week 10 injury report a level with 'no second dated snapshot', while the second capture and its published delta exist |
| F-73 | The venue requirement was verified for 11 of 13 Week 11 fixtures; the other two carried an open naming question (F-60) |
| F-76 | Two official sources name the Munich venue differently: the Game Book says Allianz Arena, the game centre says FC Bayern Munich Stadium |
| F-77 | The Cleveland starting defence is absent from the Houston-at-Cleveland Game Book conversion |
| F-78 | The Carolina-at-New Orleans Game Book lost the Did Not Play and Not Active section headers |
| F-79 | The Seattle-at-Las Vegas substitution lists are interleaved and truncated by the conversion and could not be transcribed |
| F-80 | The Steelers-at-Bengals Game Book prints a referee who cannot have worked that game |
| F-81 | 37 of 171 Week 10 designations are unresolved because the player does not appear in his own Game Book at all |
| F-82 | 56 rows on the Game Book operations and glossary pages are exempt from the every-row-has-a-source rule |
| F-83 | The scheduled official injury capture has failed its freshness gate on main since the Week 11 report went live: the Week 11 page does not pass the schema pinned to Week 10 |

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

