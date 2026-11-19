#!/usr/bin/env python3
"""
Render `schedule.html` - the dated official schedule announcement, placed beside the
live schedule (T73, session arena/cd475bd1-x4).

What the page shows
-------------------
Left column: the league's dated schedule announcement (NFL media release, 14 May 2026),
one row per published fact, each row carrying the verbatim excerpt it came from and
the official media.nfl.com link.

Right column: the live schedule (NFL.com), linked, and the Week 11 fixtures already
verified row-for-row against the live page (see research/verification/
live-reverification-2026-11-18.md). Only 13 of the 272 regular-season games are in
this repository; the page says so.

What the page refuses to do
---------------------------
* It never fills a value the release does not state. A Week 18 matchup time is shown
  as "not yet assigned", because the release says it has not been assigned.
* Every date in the announcement is checked against the calendar: the published
  weekday must match the date. A mismatch fails the build.
* A row without an official https link on an allowed host fails the build.

Run:  python3 tools/schedule_page.py          (validates, then writes site/schedule.html)
Hook: tools/pages.py calls write_pages(SITE, shell) from its main(), like glossary.py.
"""
import csv
import datetime
import html
import os
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANNOUNCEMENT = os.path.join(ROOT, "data", "schedule-announcement-2026.csv")
WEEK11 = os.path.join(ROOT, "data", "schedule-wk11-2026.csv")
SITE = os.path.join(ROOT, "site")

ALLOWED_HOSTS = {"media.nfl.com", "www.nfl.com"}
ANNOUNCEMENT_URL = "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"
LIVE_URL = "https://www.nfl.com/schedules/2026/"
LIVE_WEEK11_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
EXPECTED_ANNOUNCEMENT_ROWS = 13
EXPECTED_WEEK11_ROWS = 13
REQUIRED = ("id", "item", "published_value", "verbatim_excerpt", "source_url", "checked_date")


class ValidationError(Exception):
    pass


def _esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def load_announcement(path=ANNOUNCEMENT):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return rows


def load_week11(path=WEEK11):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def validate_announcement(rows):
    """Raise ValidationError on the first problem. Returns the rows unchanged."""
    if len(rows) != EXPECTED_ANNOUNCEMENT_ROWS:
        raise ValidationError("announcement has %d rows, expected %d" %
                              (len(rows), EXPECTED_ANNOUNCEMENT_ROWS))
    seen = set()
    for r in rows:
        rid = r.get("id", "")
        for f in REQUIRED:
            if not (r.get(f) or "").strip():
                raise ValidationError("%s: required field %r is blank" % (rid, f))
        if rid in seen:
            raise ValidationError("duplicate id %s" % rid)
        seen.add(rid)
        u = urlparse(r["source_url"])
        if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
            raise ValidationError("%s: source is not an official NFL https link: %s" %
                                  (rid, r["source_url"]))
        if r["source_url"] != ANNOUNCEMENT_URL:
            raise ValidationError("%s: unexpected source %s" % (rid, r["source_url"]))
        try:
            datetime.date.fromisoformat(r["checked_date"])
        except ValueError:
            raise ValidationError("%s: checked_date %r is not an ISO date" % (rid, r["checked_date"]))
        if r.get("iso_date"):
            d = datetime.date.fromisoformat(r["iso_date"])
            if (r.get("weekday") or "") != d.strftime("%A"):
                raise ValidationError("%s: %s is a %s, not %s" %
                                      (rid, r["iso_date"], d.strftime("%A"), r.get("weekday")))
    return rows


def validate_week11(rows):
    if len(rows) != EXPECTED_WEEK11_ROWS:
        raise ValidationError("Week 11 has %d rows, expected %d" % (len(rows), EXPECTED_WEEK11_ROWS))
    for r in rows:
        u = urlparse(r.get("nfl_url") or "")
        if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
            raise ValidationError("Week 11 %s@%s: no official NFL.com game link" %
                                  (r.get("away"), r.get("home")))
    return rows


def _table(headers, rows):
    out = ['<div class="table-wrap"><table><thead><tr>']
    out += ["<th>%s</th>" % _esc(h) for h in headers]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def _src(url, label="Official source"):
    return ('<a href="%s" target="_blank" rel="noreferrer noopener">%s &nearr;</a>'
            % (_esc(url), _esc(label)))


def _announcement_table(rows):
    body = []
    for r in rows:
        value = _esc(r["published_value"])
        if r.get("weekday") and r.get("iso_date"):
            value = "%s &middot; %s" % (_esc(r["weekday"]), value)
        body.append([
            _esc(r["id"]),
            _esc(r["item"]),
            value,
            "<q>%s</q>" % _esc(r["verbatim_excerpt"]),
            _src(r["source_url"], "NFL media release"),
        ])
    return _table(["ID", "Published fact", "Value as published", "Verbatim excerpt", "Source"],
                  body)


def _week11_table(rows):
    body = []
    for r in rows:
        time_cell = _esc(r.get("time_et") or "")
        body.append([
            _esc(r["date"]),
            _esc(time_cell) if time_cell else '<span class="blank">not published</span>',
            "%s at %s" % (_esc(r["away"]), _esc(r["home"])),
            _esc(r.get("network") or "") or '<span class="blank">not published</span>',
            _src(r["nfl_url"], "NFL.com game page"),
        ])
    return _table(["Date", "Kickoff (ET)", "Game", "Network", "Source"], body)


def build_body(announcement, week11):
    validate_announcement(announcement)
    validate_week11(week11)
    n_ann = len(announcement)
    n_wk11 = len(week11)
    return """
<section class="page-head">
  <span class="eyebrow">Schedule &middot; 2026 season</span>
  <h1>Official schedule announcement, beside the live schedule</h1>
  <p class="lede">The league&rsquo;s dated announcement of the 2026 regular season (14 May 2026) on the
  left, and the live NFL.com schedule on the right. Every value in the left column is quoted
  from the official release; nothing is inferred. The repository holds {n_wk11} of the 272
  regular-season games (Week 11); the rest are on the live page.</p>
</section>

<section class="schedule-split" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px;align-items:start">
  <div>
    <h2>Dated announcement &middot; 14 May 2026</h2>
    <p class="muted small">{n_ann} published facts. Each row links to the official NFL media release
    <a href="{ann_url}" target="_blank" rel="noreferrer noopener">{ann_url}</a>. Weekday and date
    pairs were checked against the calendar.</p>
    {ann_table}
    <p class="tbl-note">Not yet published by the league: the dates, start times and networks of the
    Week 18 matchups (row S13).</p>
  </div>
  <div>
    <h2>Live schedule &middot; NFL.com</h2>
    <p class="muted small"><a href="{live_url}" target="_blank" rel="noreferrer noopener">2026 schedule on NFL.com &nearr;</a>
    &middot; <a href="{wk11_url}" target="_blank" rel="noreferrer noopener">Week 11 by week &nearr;</a></p>
    <p class="muted small">Week 11 fixtures in this repository, {n_wk11} rows. Each row links to its
    NFL.com game page. Earlier sessions checked these 13 rows against the live page (see
    <code>research/verification/live-reverification-2026-11-18.md</code>).</p>
    {wk11_table}
  </div>
</section>
""".format(n_ann=n_ann, n_wk11=n_wk11, ann_url=ANNOUNCEMENT_URL, live_url=LIVE_URL,
           wk11_url=LIVE_WEEK11_URL, ann_table=_announcement_table(announcement),
           wk11_table=_week11_table(week11))


DESCRIPTION = ("The NFL's dated 2026 schedule announcement (14 May 2026) beside the live "
               "NFL.com schedule, with each published fact quoted and linked to its official source.")


def write_pages(site_dir, shell):
    body = build_body(validate_announcement(load_announcement()), validate_week11(load_week11()))
    with open(os.path.join(site_dir, "schedule.html"), "w", encoding="utf-8") as fh:
        fh.write(shell("schedule", "Schedule announcement", DESCRIPTION, body, "schedule.html"))
    return ["schedule.html"]


def main():
    try:
        ann = validate_announcement(load_announcement())
        wk = validate_week11(load_week11())
    except ValidationError as exc:
        print("schedule: VALIDATION FAILED: %s" % exc, file=sys.stderr)
        return 1
    print("schedule: %d announcement rows verified against the calendar; %d Week 11 rows with official links"
          % (len(ann), len(wk)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
