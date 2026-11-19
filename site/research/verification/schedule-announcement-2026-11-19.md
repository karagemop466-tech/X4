# Dated 2026 NFL schedule announcement beside the current schedule — 2026-11-19

## What was checked

The official NFL Media release was read on 2026-11-19:

- [2026 NFL Schedule Powered by AWS to be Released Thursday, May 14](https://media.nfl.com/news-and-releases/2026-nfl-schedule-powered-by-aws-to-be-released-thursday--may-14)

The page displays **May 08, 2026** and its dateline says **NEW YORK — May 8, 2026**. It states that the full 2026 NFL schedule would be released on **Thursday, May 14 at 8 p.m. ET**. The site repeats those as two distinct dates: publication of the announcement and the schedule-release date/time announced by the league.

The current official schedule was also read on 2026-11-19:

- [NFL.com 2026 schedule](https://www.nfl.com/schedules/2026/)
- [NFL.com Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11)

Both pages are headed `SCHEDULE 2026`; the Week 11 view includes the Colts-at-Texans game on Thursday, November 19, followed by the Sunday games. This confirms that the announcement is historical release metadata and the schedule pages are the current fixture references. It does not verify every fixture in the local CSV; the local table continues to link each row to its own official game-centre page and retains its separately dated verification record.

## Publication change

`tools/gen_brief_register.py` now renders a dated release-note card immediately above the fixture-context table in `brief-register.html` and `site/brief-register.html`. The card links to the NFL Media announcement, the live season schedule, and the Week 11 schedule. It labels the schedule-source read date (2026-11-19), distinguishes announcement publication from the announced release time, and says that current fixture facts come from the live schedule/game-centre sources rather than the older notice.

No schedule, venue, market, injury, or model value was changed or inferred. No third-party source was used.

## Reproduction and checks

- `python3 tools/gen_brief_register.py` — regenerated the page and its mirror; output reports 150 corpus games, 160/160 standings fields reconciled, and 13 fixture-context rows.
- `python3 -m unittest discover -s tests -p 'test_schedule_announcement.py'` — three offline tests verify the dated announcement, both current schedule links, and placement beside the fixture table.
- The test is wired into `tools/validate.py` immediately after the brief-register generator. The full publication gate and link checks remain the final integration verification.

## Scope limits / irregularities

- The NFL release is a dated announcement of when the schedule was to be released, not a replacement for the current schedule and not a source for the individual fixture details.
- The current schedule pages may change after this read; the page labels the read date rather than presenting this fetch as a permanent live snapshot.
