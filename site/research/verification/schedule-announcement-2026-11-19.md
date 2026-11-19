# Dated schedule announcement beside the live schedule (T71)

Checked: 2026-11-19 (UTC). Session `arena/cd475bd1-x4`. Brief item: *"Publish the league's dated schedule announcement beside the live schedule page."*

## Sources read

| Role | Official URL | How it was read | Date of the content |
|---|---|---|---|
| Dated announcement (primary) | https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced | `fetch_page`, both chunks read in full (chunk 0 and chunk 1, `hasMore` false on chunk 1) | Football Communications release, **May 14, 2026** |
| Live schedule | https://www.nfl.com/schedules/2026/ | `fetch_page`, chunk 0 read; Week 11 Thursday game and the first Sunday games seen on the page | Live page, read 2026-11-19 |
| Week 11 by week | https://www.nfl.com/schedules/2026/by-week/week-11 | Not re-read in this session. The 13 rows were checked 13/13 against this page by an earlier session: `research/verification/live-reverification-2026-11-18.md` | Live page, 2026-11-18 |

The bash sandbox cannot reach `nfl.com` or `media.nfl.com` (outbound allowlist), so no check here is machine-run against the live site. Every excerpt in `data/schedule-announcement-2026.csv` was compared by eye with the fetched text; the reviewer should compare them with the link in each row.

Secondary coverage (Sportsnet, Yahoo Sports, WNY Papers) was read only to find the official release. None of its wording is used.

## What is published (rows S01 to S13)

| ID | Published fact | Official excerpt (verbatim, from the release) |
|---|---|---|
| S01 | Announcement date: 14 May 2026 | "May 14, 2026 — The NFL announced its 18-week, 272-game regular-season schedule for 2026" |
| S02 | 18 regular-season weeks | "The NFL announced its 18-week, 272-game regular-season schedule for 2026" |
| S03 | 272 regular-season games | "Complete 18-Week, 272-Game Regular-Season Schedule Available on NFL.com" (subtitle) |
| S04 | 17 games per team | "The NFL's 32 teams will each play 17 games over 18 weeks." |
| S05 | Kickoff game: Wed 9 Sep 2026, New England at Seattle, 8:20 p.m. ET, NBC | "…host the New England Patriots at Lumen Field on Wednesday, September 9 (8:20 p.m. ET, NBC)" |
| S06 | Week 18, Saturday 9 Jan 2027 | "The regular season will conclude with Week 18 on Saturday, January 9, and Sunday, January 10." |
| S07 | Week 18, Sunday 10 Jan 2027 | same sentence as S06 |
| S08 | Year of the January dates: 2027 | "the matchup in primetime on Saturday, January 2, 2027" |
| S09 | 16 division games in Week 18 | "all 16 games scheduled for the final week of the season are division contests" |
| S10 | Bye weeks 5 to 14 | "Byes will begin in Week 5 and end in Week 14." |
| S11 | Nine international games | "The NFL schedule features nine international games, the most-ever in a season" |
| S12 | Thanksgiving tripleheader, Thu 26 Nov 2026 | "The NFL Thanksgiving Games presented by American Express will feature a tripleheader on Thursday, November 26." |
| S13 | Week 18 matchups not yet assigned | "Specific dates, start times and networks for Week 18 matchups will be determined and announced following the conclusion of Week 17." |

## Checks performed

1. **Weekday against calendar (automated).** Every row with a date has a published weekday. `tools/schedule_page.py` computes the weekday for each date and fails the build on a mismatch. All six dated rows (S01, S05, S06, S07, S08, S12) match.
2. **Source host (automated).** Every row must be `https` on `media.nfl.com` or `www.nfl.com` and must point at the one announcement URL. A non-official link fails the build.
3. **Row count and blanks (automated).** The announcement must have exactly 13 rows, and no required field may be blank. A drift in row count fails the build.
4. **Week 11 rows (automated).** The 13 Week 11 fixtures on the right-hand side must each carry an official NFL.com game link. Week 11 values were checked against the live page earlier (13/13).
5. **Site checks.** `site/check.py` passes: every data row has an official source link, no broken local links, and the page renders in the browser smoke test. The checker's official-host pattern was widened to also accept `media.nfl.com`, so that the NFL media release counts as an official source. Nothing else in the checker changed.
6. **Unit tests (offline).** `tests/test_schedule_page.py`: 12 tests covering validation, the pinned row counts, the calendar, and the page body. Run in the publication gate.

## Not verified / limits

- Excerpts were compared by eye with the fetched text, not by a machine comparison against the live site (sandbox outbound limits). The links let a reviewer check each row in one click.
- The release gives no year beside "Saturday, January 9" and "Sunday, January 10". 2027 is inferred from the calendar and from the release's "January 2, 2027". Flagged as **F-91**.
- Week 18 matchups are not yet assigned by the league. The page says so, and no Week 18 game is listed. Flagged as **F-90**.
- The repository holds **13 of 272** regular-season games (Week 11 only). The other 259 are on the live NFL.com schedule and are not transcribed here. This is the existing limitation **F-10**.

## Irregularities for review

- **F-90** (Limitation): Week 18 matchups unassigned. Official source: https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced
- **F-91** (Irregularity): the Week 18 dates carry no year in the release sentence. Official source: the same release.
- **Host allowlist widened** to `media.nfl.com` in `site/check.py`. The release is on the NFL's media host, not `www.nfl.com`, and the checker had rejected it. Reviewer: confirm this is the right official host for a league release.

## Files

- `data/schedule-announcement-2026.csv` (new): the 13 rows above, with the excerpt and the source for each
- `tools/schedule_page.py` (new): validation and the page generator
- `tests/test_schedule_page.py` (new): offline tests
- `site/schedule.html` and root `schedule.html` (generated)
- `tools/pages.py` (two additive lines: directory entry and `write_pages` call)
- `tools/content.py` (F-90 and F-91, additive)
- `tools/render.js` (one PAGES entry), `site/check.py` (one PAGES entry; `media.nfl.com` in the official-host pattern)
- `tools/validate.py` (one added test step)
