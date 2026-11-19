#!/usr/bin/env python3
"""Generate depth-audit.html (and the site/ mirror): every club's depth coverage, side by side.

WHY THIS PAGE EXISTS
--------------------
`depth.html` publishes the transcribed strings. This page answers a different question that
the brief asks directly: **for each of the 32 clubs, is the published chart actually
represented, and where is it not?** It is the "32-team roster sweep" made visible, one row
per club, so a reader can see at a glance which clubs have no chart, which have a chart that
cannot describe a shared slot, and how much of each chart made it into the dataset.

Every number is computed from `data/depth-wk11-2026.csv` at build time. Every row links the
club's own official depth-chart page. Clubs with no machine-readable chart are marked and
linked, never filled in.

VERIFICATION STATUS AT PUBLICATION (2026-11-18)
----------------------------------------------
Cell-level against the live club pages this session could read: SEA, CLE, BAL, WAS (offence
sections read and compared name by name; the measurement is on `brief-register.html` and in
`research/verification/depth-slot-fidelity-2026-11-18.md`). The other clubs' rows report the
committed dataset's own counts and the chart URL, which is a statement about the dataset, not
about the live page. That distinction is printed on the page so no row overstates itself.

Run:  python3 tools/gen_depth_audit.py
"""
import csv
import html
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_nav  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SITE = os.path.join(ROOT, "site")
RETRIEVED = "2026-11-18"
SITE_URL = "https://karagemop466-tech.github.io/X4/"

# Clubs whose live chart was read and compared cell by cell in this session.
CELL_VERIFIED = {"SEA", "CLE", "BAL", "WAS"}
SPECIAL_TEAMS = {"P", "K", "LS", "H", "PR", "KR"}


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(s):
    return html.escape(str(s), quote=True)


def a(url, label):
    return '<a href="%s" target="_blank" rel="noreferrer noopener">%s &nearr;</a>' % (esc(url), esc(label))


rows = read(os.path.join(DATA, "depth-wk11-2026.csv"))
teams = sorted({r["team"] for r in rows})

by_club = defaultdict(list)
for r in rows:
    by_club[r["team"]].append(r)

clubs_out, totals = [], defaultdict(int)
for club in teams:
    rs = by_club[club]
    units = sorted({r["unit"] for r in rs})
    cols = defaultdict(list)
    for r in rs:
        cols[(r["unit"], r["position_row"])].append(int(r["depth"]))
    cells = defaultdict(int)
    for r in rs:
        cells[(r["unit"], r["position_row"], r["depth"])] += 1
    shared = sum(1 for v in cells.values() if v > 1)
    solo = sum(1 for v in cols.values() if len(v) == 1)
    st = sum(1 for r in rs if r["position_row"] in SPECIAL_TEAMS)
    url = rs[0]["source"]
    dated = sorted({r["chart_date"] for r in rs if r["chart_date"]})
    max_depth = max(int(r["depth"]) for r in rs)
    verified = club in CELL_VERIFIED
    status = ('<span class="tag green">cell-checked</span>' if verified
              else '<span class="tag">dataset only</span>')
    totals["rows"] += len(rs)
    totals["shared"] += shared
    totals["empty"] += sum(1 for r in rs if r.get("slot_kind") == "empty")
    totals["st"] += st
    totals["solo"] += solo
    totals["clubs"] += 1
    totals["verified"] += 1 if verified else 0
    clubs_out.append([
        "<b>%s</b>" % esc(club),
        "%d" % len(rs),
        "%d" % len(cols),
        "%d" % solo,
        '<span class="tag %s">%d</span>' % ("red" if shared == 0 else "green", shared),
        "%d" % max_depth,
        "%d" % st,
        esc(", ".join(units)),
        esc(", ".join(dated)) if dated else '<span class="muted">club prints no date</span>',
        status,
        a(url, "Club chart"),
    ])

# clubs with no machine-readable chart at all
import depth as depth_module  # noqa: E402
missing_chart = sorted(c for c, u in depth_module.CHART_URL.items() if not u)

body = []
body.append('<main><header class="topbar"><div><span class="eyebrow">DECISION DESK</span>'
            '<h1>Depth audit</h1></div><span class="status-pill"><i></i> Retrieved %s</span></header>'
            % RETRIEVED)

body.append(
    '<section><div class="hero"><span class="eyebrow light">One row per club</span>'
    '<h2>The roster sweep, made visible: which charts are represented, and where a shared '
    'slot is still not expressed.</h2>'
    '<p>%d clubs publish an ordered chart and every one of them is transcribed below. The '
    'transcription can now put two men in one cell: a club that prints a co-starter is '
    'stored as a shared cell, not as a starter and a backup. The <b>shared</b> column shows '
    'how many cells in each club\'s sheet hold more than one player &mdash; it is <b>%d across '
    'all %d clubs</b>. The <b>special teams</b> column is %s, for a different reason: those '
    'rows have never been transcribed for any club.</p>'
    '<p>Two kinds of row appear here and they mean different things. <i>cell-checked</i> means '
    'the live club page was read and compared name by name. <i>dataset only</i> '
    'means the row reports what the committed file holds &mdash; it is not a claim that the '
    'live page still matches it, and clubs edit their charts during the week.</p></div></section>'
    % (len(teams), totals["shared"], len(teams),
       ("zero everywhere" if totals["st"] == 0 else "%d rows in total" % totals["st"])))

body.append('<div class="cards">')
body.append('<article class="card hero-stat"><span class="k">Clubs with an ordered chart</span>'
            '<div class="v">%d of 32</div><div class="n">%s publishes an image only and has no rows</div></article>'
            % (len(teams), ", ".join(missing_chart) if missing_chart else "no club"))
body.append('<article class="card hero-stat"><span class="k">Transcribed positions</span>'
            '<div class="v">%d</div><div class="n">One row per printed player, per club</div></article>'
            % totals["rows"])
body.append('<article class="card hero-stat"><span class="k">Cells holding 2+ players</span>'
            '<div class="v">%d</div><div class="n">%s</div></article>'
            % (totals["shared"],
               "Shared cells keep every name in the same depth number"
               if totals["shared"] else
               "The measure of the shared-slot defect; a faithful transcription would not be zero"))
body.append('<article class="card hero-stat"><span class="k">Clubs cell-checked live</span>'
            '<div class="v">%d</div><div class="n">Read and compared name by name in this session</div></article>'
            % totals["verified"])
body.append('</div>')

body.append('<section><div class="section-head"><div><span class="eyebrow">The sweep</span>'
            '<h2>All %d clubs, by what the dataset holds</h2>'
            '<p class="muted">Columns: rows stored, distinct position columns, columns that name '
            'exactly one player, cells naming two or more players, deepest string, special-teams '
            'rows, the units present, any date the club prints on its own chart, whether the live '
            'page was checked this session, and the club page itself.</p></div>'
            '<span class="tag amber">defect quantified per club</span></div>' % len(teams))
body.append('<div class="card"><div class="table-wrap"><table class="data">'
            '<thead><tr><th>Club</th><th>Rows</th><th>Columns</th><th>Single-player columns</th>'
            '<th>Shared cells</th><th>Deepest</th><th>Special teams</th><th>Units</th>'
            '<th>Club-dated</th><th>Checked</th><th>Source</th></tr></thead><tbody>')
for r in clubs_out:
    body.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
body.append('</tbody></table></div>'
            '<p class="note">%s</p></div></section>'
            % ("A <b>shared cell of 0</b> is not a clean sheet: it would mean no club in this "
               "dataset has a cell with two players, while live pages do."
               if totals["shared"] == 0 else
               "<b>%d shared cell%s</b> and <b>%d printed empty cell%s</b> are now stored as "
               "published, instead of being read as a ranked list. The clubs whose charts were "
               "re-read live for this change are the ones whose cells can be checked against the "
               "club's own page; the remaining clubs still carry the 2026-11-14 transcription, "
               "and their shared and empty cells are not represented until each is re-read."
               % (totals["shared"], "" if totals["shared"] == 1 else "s",
                  totals["empty"], "" if totals["empty"] == 1 else "s")))

# The four checks, each evaluated against the committed file rather than asserted.
def _depth_of(team, pos, player):
    for r in rows:
        if (r["team"] == team and r["position_row"] == pos
                and r["player"] == player):
            return r
    return None


def _kind(team, pos, player):
    r = _depth_of(team, pos, player)
    return r.get("slot_kind", "single") if r else ""


sea_test = ("Kupp" in str(_depth_of("SEA", "WR", "Cooper Kupp"))
            and "Shaheed" in str(_depth_of("SEA", "WR", "Rashid Shaheed")))
sea_ok = (sea_test
          and _depth_of("SEA", "WR", "Cooper Kupp")["depth"] == "1"
          and _depth_of("SEA", "WR", "Rashid Shaheed")["depth"] == "1"
          and _depth_of("SEA", "WR", "Irvin Charles")["depth"] == "2")
was_empty = [r for r in rows if r["team"] == "WAS" and r["slot_kind"] == "empty"]
was_ok = bool(was_empty) and was_empty[0]["position_row"] == "WR3" and was_empty[0]["depth"] == "2"
st_rows = sum(1 for r in rows if r["position_row"] in SPECIAL_TEAMS)
st_ok = st_rows > 0
dated = sum(1 for r in rows if r["chart_date"])
dated_ok = dated > 0

body.append(
    '<section><div class="section-head"><div><span class="eyebrow">What a correct transcript needs</span>'
    '<h2>Four changes, each checkable &mdash; and where each one stands</h2></div></div>'
    '<div class="card"><div class="kv">'
    '<div>Same depth, shared cell</div><div><span class="tag %s">%s</span> Both players in a printed '
    'first cell must carry the same depth number. Test: the Seattle WR row must read Kupp 1, '
    'Shaheed 1, Charles 2. It now reads %s.</div>'
    '<div>Empty cells kept</div><div><span class="tag %s">%s</span> A club that names no third player '
    'must be distinguishable from one we did not record. Test: Washington\'s third WR row has an '
    'explicitly empty second cell. It now has %d printed empty cell%s in the dataset.</div>'
    '<div>Special teams included</div><div><span class="tag %s">%s</span> P, K, H, LS, KR and PR are '
    'chart rows. Test: every club row above shows a non-zero special-teams count that matches its '
    'live page. The dataset holds %d special-teams rows, because those rows have never been '
    'transcribed.</div>'
    '<div>Versioned against roster moves</div><div><span class="tag %s">%s</span> A chart is only true '
    'until the next transaction. Test: each row carries the club\'s own printed date where it has one, '
    'and the capture is superseded when the transaction log shows a move. %d rows carry a club-printed '
    'date; the Washington chart was re-read on 2026-11-19 and had changed since 2026-11-14, which is '
    'the case the date column has to answer.</div>'
    '</div><p class="note">The measurement behind this page, including the four-club live sample '
    '(103 players, 4 absent, 0 shared cells represented at the time of the audit), is published at %s, '
    'and the change that closed the two cell tests is recorded at %s.</p></div></section>'
    % ("green" if sea_ok else "red", "PASS" if sea_ok else "OPEN",
       "%s %s %s" % (_depth_of("SEA", "WR", "Cooper Kupp")["depth"],
                     _depth_of("SEA", "WR", "Rashid Shaheed")["depth"],
                     _depth_of("SEA", "WR", "Irvin Charles")["depth"]) if sea_ok else "not as required",
       "green" if was_ok else "red", "PASS" if was_ok else "OPEN",
       len(was_empty), "" if len(was_empty) == 1 else "s",
       "green" if st_ok else "red", "PASS" if st_ok else "OPEN", st_rows,
       "green" if dated_ok else "red", "PASS" if dated_ok else "OPEN", dated,
       a(SITE_URL + "research/verification/depth-slot-fidelity-2026-11-18.md", "the depth fidelity report"),
       a(SITE_URL + "research/verification/depth-slot-cells-2026-11-19.md", "the cell-change record")))

body.append('<footer><span>FOURTH DOWN RESEARCH &middot; Depth audit</span><span>'
            '<a href="index.html">&larr; Back to overview</a> &middot; '
            '<a href="depth.html">Depth &amp; deficiency</a> &middot; '
            '<a href="brief-register.html">Brief register</a></span></footer></main>')

page = ('<!doctype html>\n<html lang="en">\n<head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="description" content="The 32-club depth sweep: every club with an ordered chart, '
        'the rows and columns the dataset holds, and the shared-slot defect quantified per club.">'
        '<title>Depth audit | Fourth Down Research</title>'
        '<link rel="stylesheet" href="desk.css"></head>\n'
        '<body data-page="depth-audit"><aside class="sidebar">' + desk_nav.side() + '</aside>\n'
        + "\n".join(body) + '\n<script src="nav.js"></script></body>\n</html>\n')

for target in (os.path.join(SITE, "depth-audit.html"), os.path.join(ROOT, "depth-audit.html")):
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(page)
print("wrote depth-audit.html (%d bytes): %d clubs, %d rows, shared %d, cell-checked %d"
      % (len(page), len(teams), totals["rows"], totals["shared"], totals["verified"]))
