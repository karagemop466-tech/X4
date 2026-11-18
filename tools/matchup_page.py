#!/usr/bin/env python3
"""T41: Offense vs defense matchup deficiency matrix for the Week 11 slate.

Writes site/matchup.html (called from tools/pages.py main() through
write_pages, the same hook pattern desk_extension uses).

What the page shows
- One row per (Week 11 game, direction, position group) for four paired
  axes - trench, coverage, backs vs linebackers, tight ends vs safeties -
  plus one quarterback row per game, 117 rows in total (13 games x 9).
- Each row carries both sides' club-chart chains, depth 1 to the last
  string the club prints, with the official Week 10 game status badge on
  every player the report rules on.
- A computed deficiency flag: a listed depth-1 player the official report
  rules Out or Doubtful, the chart's next listed player behind him, a
  hole where the club lists nobody, or a cascade where both are ruled out.

Rules this module follows
- Depth is the club's own column order, transcribed in data/depth-wk11-2026.csv
  by tools/depth.py. Nothing here re-derives a rank from jersey number,
  experience or salary (F-02).
- Game status is the official NFL Week 10 report - the most recent official
  report at build time; the Week 11 report was not yet published when this
  page was built (checked 2026-11-17: the reg11 address serves the Week 10
  report). A Week 10 designation is not a Week 11 designation and the page
  says so.
- A published chart is not proof of who started (F-27). The page measures
  listed availability only.
- Houston publishes its chart as an image, so its cells are blank and
  flagged (F-24); nothing is guessed to fill them.
- The position-to-position pairing is this desk's analyst choice and is
  published in full on the page; the NFL publishes no matchup grouping.
- Every table row carries the official NFL.com game link and both clubs'
  chart links, so every row passes the publication gate.
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

SCHEDULE = os.path.join(DATA, "schedule-wk11-2026.csv")
DEPTH = os.path.join(DATA, "depth-wk11-2026.csv")

# Houston's chart is a single bitmap with no table markup (F-24). The URL is
# the source that shows that, and it doubles as the row's official club link.
HOU_CHART = "https://www.houstontexans.com/team/depth-chart"
NFL_INJURY = "https://www.nfl.com/injuries/league/2026/reg10"

# (key, label, side-A unit, side-A positions, side-B unit, side-B positions).
# For the four paired axes side A is one club's offense and side B the
# opponent's defense; the Direction cell of each row spells out which clubs.
# The QB axis is special-cased below: both sides read the Offense unit.
AXES = [
    ("trench", "Trench: offensive line vs defensive front",
     "Offense", ["LT", "RT", "LOT", "ROT", "T", "LG", "RG", "C"],
     "Defense", ["EDGE", "EDGE2", "DE", "DE2", "OLB", "OLB2", "RUSH", "LOLB",
                 "ROLB", "LDE", "RDE", "DT", "DT2", "DT3", "NT", "DL", "DL2",
                 "DL3", "DL4", "LDT", "RDT"]),
    ("coverage", "Coverage: receivers vs defensive backs",
     "Offense", ["WR", "WR2", "WR3"],
     "Defense", ["CB", "CB2", "CB3", "LCB", "RCB", "NCB", "NB", "N", "DB"]),
    ("backers", "Backs vs linebackers",
     "Offense", ["RB", "HB", "FB"],
     "Defense", ["LB", "LB2", "LB3", "ILB", "ILB2", "MLB", "MIKE", "SAM",
                 "WILL", "WLB", "SLB", "LILB", "RILB"]),
    ("te", "Tight ends vs safeties",
     "Offense", ["TE", "TE2"],
     "Defense", ["S", "S2", "S3", "FS", "SS"]),
]
QB_KEY = "qb"
QB_LABEL = "Quarterbacks: both clubs' listed QBs"
QB_POSITIONS = ["QB"]

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _page_helpers():
    # imported here so this module can be imported without the generator running
    import pages as P
    return P


def load():
    """Schedule in CSV order; depth chains keyed (team, unit, position)."""
    schedule = _rows(SCHEDULE)
    depth = _rows(DEPTH)
    charts = {}
    sources = {}
    dates = {}
    for r in depth:
        key = (r["team"], r["unit"], r["position_row"])
        charts.setdefault(key, []).append(r)
        if r["source"] and r["team"] not in sources:
            sources[r["team"]] = r["source"]
        if r["chart_date"]:
            dates.setdefault(r["team"], r["chart_date"])
    for key in charts:
        charts[key].sort(key=lambda r: int(r["depth"]))
    for team in {r["team"] for r in depth}:
        sources.setdefault(team, "")
    return schedule, charts, sources, dates


def _badge(status):
    if status == "Out":
        return ' <span class="b no">Out</span>'
    if status == "Doubtful":
        return ' <span class="b warn">Doubtful</span>'
    if status == "Questionable":
        return ' <span class="b warn">Questionable</span>'
    return ""


def chain_html(team, unit, positions, charts, blank):
    """The club's listed chain for each position it charts in this group."""
    parts = []
    for pos in positions:
        chain = charts.get((team, unit, pos))
        if not chain:
            continue
        segs = []
        for r in chain:
            segs.append("%s %s%s" % (r["depth"], _page_helpers().esc(r["player"]),
                                     _badge(r["game_status"])))
        parts.append("<b>%s</b> %s" % (_page_helpers().esc(pos), " &middot; ".join(segs)))
    if not parts:
        if team == "HOU":
            return blank("Houston publishes no structured chart - image only (F-24)")
        return blank("club charts none of these positions")
    return "<br>".join(parts)


def side_flags(team, unit, position, charts):
    """Deficiency items for one side of one axis.

    An item exists when the club's listed depth-1 player at a position in
    the group is ruled Out or Doubtful by the official report: what the club
    prints behind him, a hole where it prints nobody, or a cascade where the
    next man is ruled out too.
    """
    items = []
    for pos in position:
        chain = charts.get((team, unit, pos)) or []
        if not chain:
            continue
        d1 = chain[0]
        status = d1["game_status"]
        if status not in ("Out", "Doubtful"):
            continue
        head = "%s %s1 %s (%s)" % (team, pos, d1["player"], status)
        if len(chain) == 1:
            items.append(head + " - the club lists no replacement")
        else:
            d2 = chain[1]
            if d2["game_status"] in ("Out", "Doubtful"):
                items.append(head + " and %s2 %s (%s) - both ruled out"
                             % (pos, d2["player"], d2["game_status"]))
            else:
                items.append(head + " - chart lists %s2 %s" % (pos, d2["player"]))
    return items


def _game_label(game):
    y, m, d = game["date"].split("-")
    return "%s %s &middot; %s ET &middot; %s" % (
        _MONTHS[int(m) - 1], int(d), game["time_et"], game["network"])


def build():
    """Every row of both tables, plus the counts the hero prints."""
    P = _page_helpers()
    schedule, charts, sources, dates = load()
    rows = []
    attrs = []
    n_def = 0

    def add(game, direction, axis_key, a_label, a_html, b_label, b_html,
            flags, sources_cell, game_flag):
        nonlocal n_def
        flag_html = ("<br>".join(P.esc(f) for f in flags) if flags
                     else P.badge("no listed starter Out or Doubtful", "ok"))
        if game_flag:
            flag_html = P.blank(game_flag) + ("<br>" + flag_html if flags else "")
        rows.append([
            '<b>%s</b><br><span class="small muted">%s</span>'
            % (P.esc("%s @ %s" % (game["away"], game["home"])), _game_label(game)),
            P.esc(direction),
            P.esc(a_label),
            a_html,
            b_html,
            flag_html,
            sources_cell,
        ])
        flagged = bool(flags) or bool(game_flag)
        attrs.append(' data-game="%s@%s" data-axis="%s" data-def="%d"'
                     % (game["away"], game["home"], axis_key, 1 if flagged else 0))
        if flagged:
            n_def += 1

    for game in schedule:
        away, home = game["away"], game["home"]
        hou_note = None
        if "HOU" in (away, home):
            hou_note = "HOU side not assessable - no structured chart (F-24)"
        away_src = sources.get(away) or (HOU_CHART if away == "HOU" else "")
        home_src = sources.get(home) or (HOU_CHART if home == "HOU" else "")
        game_src = P.src(game["nfl_url"], "NFL.com game")
        both_src = "%s %s %s" % (game_src, P.src(away_src, away + " chart"),
                                 P.src(home_src, home + " chart"))

        for key, label, a_unit, a_pos, b_unit, b_pos in AXES:
            for a_team, b_team in ((away, home), (home, away)):
                direction = "%s %s vs %s %s" % (a_team, a_unit.lower(),
                                                b_team, b_unit.lower())
                flags = side_flags(a_team, a_unit, a_pos, charts)
                flags += side_flags(b_team, b_unit, b_pos, charts)
                note = hou_note if "HOU" in (a_team, b_team) else None
                add(game, direction, key, a_team + " " + a_unit.lower(),
                    chain_html(a_team, a_unit, a_pos, charts, P.blank),
                    b_team + " " + b_unit.lower(),
                    chain_html(b_team, b_unit, b_pos, charts, P.blank),
                    flags, both_src, note)

        flags = side_flags(away, "Offense", QB_POSITIONS, charts)
        flags += side_flags(home, "Offense", QB_POSITIONS, charts)
        note = hou_note if "HOU" in (away, home) else None
        add(game, "%s QBs vs %s QBs" % (away, home), QB_KEY,
            away + " QBs",
            chain_html(away, "Offense", QB_POSITIONS, charts, P.blank),
            home + " QBs",
            chain_html(home, "Offense", QB_POSITIONS, charts, P.blank),
            flags, both_src, note)

    # Example chart per axis: the Week 11 club that charts the most of the
    # group's position labels (ties break alphabetically), used only to give
    # the mapping table a live source link per row.
    examples = {}
    for key, _label, a_unit, a_pos, b_unit, b_pos in AXES:
        best, best_n = None, -1
        for team in sorted({g["away"] for g in schedule} | {g["home"] for g in schedule}):
            if team == "HOU":
                continue
            n = sum(1 for p in a_pos if (team, a_unit, p) in charts) \
                + sum(1 for p in b_pos if (team, b_unit, p) in charts)
            if n > best_n:
                best, best_n = team, n
        examples[key] = best

    return schedule, rows, attrs, n_def, sources, dates, charts, examples


def body():
    P = _page_helpers()
    esc, src, badge, table, blank = P.esc, P.src, P.badge, P.table, P.blank
    schedule, rows, attrs, n_def, sources, dates, _charts, examples = build()

    axis_rows = []
    for key, label, a_unit, a_pos, b_unit, b_pos in AXES:
        best = examples[key]
        axis_rows.append([
            esc(label),
            esc("%s: %s" % (a_unit, ", ".join(a_pos))),
            esc("%s: %s" % (b_unit, ", ".join(b_pos))),
            src(sources.get(best, ""), "example chart: %s" % best),
        ])
    axis_rows.append([
        esc(QB_LABEL),
        esc("Offense: QB (both clubs)"),
        esc("Offense: QB (both clubs)"),
        src(sources.get(examples.get("trench", ""), ""),
            "example chart: %s" % examples.get("trench", "")),
    ])
    mapping = table(
        [("Matchup group", 0), ("Side A positions as charted", 0),
         ("Side B positions as charted", 0), ("Source", 0)], axis_rows,
        "The pairing is this desk's analyst choice, published in full here; "
        "the NFL publishes no matchup grouping. Position labels are exactly "
        "as each club prints them - a club that charts OLB where another "
        "charts EDGE is shown under its own label. Example-chart links open "
        "a club page that carries those labels.")

    hero_rows = len(rows)
    hero_def = n_def
    teams = sorted({g["away"] for g in schedule} | {g["home"] for g in schedule})
    charted = sum(1 for t in teams if sources.get(t) and t != "HOU")

    toolbar = (
        '<div class="toolbar">'
        '<label class="small muted" for="mx-game">Game</label> '
        '<select id="mx-game">%s</select> '
        '<label class="small muted" for="mx-axis">Group</label> '
        '<select id="mx-axis"><option value="">All groups</option>%s</select> '
        '<label class="small muted" for="mx-show">Show</label> '
        '<select id="mx-show"><option value="">All rows</option>'
        '<option value="1">Deficiency or missing chart only</option></select> '
        '<span class="small muted" id="mx-count"></span></div>'
        % ("".join(
            '<option value="%s@%s"%s>%s @ %s &mdash; %s</option>'
            % (g["away"], g["home"], " selected" if i == 0 else "",
               g["away"], g["home"], _game_label(g).replace("&middot;", "-"))
            for i, g in enumerate(schedule)),
           "".join('<option value="%s">%s</option>' % (k, esc(lab))
                   for k, lab, _, _, _, _ in AXES)
           + '<option value="%s">%s</option>' % (QB_KEY, esc(QB_LABEL))))

    matrix = P.wrap("mx-rows", table(
        [("Game", 0), ("Direction", 0), ("Matchup group", 0),
         ("Side A chain (depth 1 to last listed)", 0),
         ("Side B chain (depth 1 to last listed)", 0),
         ("Listed-starter deficiency", 0), ("Sources", 0)],
        rows,
        "One row per game, direction and group: 13 games x (4 paired groups x "
        "2 directions + 1 quarterback row) = %d rows. Chain cells list every "
        "string the club prints at each position in the group, in the club's "
        "own order, with the official Week 10 game status badge on each "
        "player the report rules on. Status is the official NFL Week 10 "
        "report - the most recent official report at build time; the Week 11 "
        "report was not yet published (checked 2026-11-17), so a Week 10 "
        "designation is not a Week 11 designation. All club charts were "
        "retrieved 2026-11-14. A published chart lists who the club lists; "
        "it is not proof of who started (F-27). Houston publishes an image, "
        "so its cells are blank and flagged (F-24), never guessed."
        % hero_rows, row_attrs=lambda i: attrs[i]))

    return (
        '<section class="hero"><div>'
        '<span class="eyebrow light">Week 11 &middot; matchup matrix</span>'
        '<h2>Every listed string on both sides of every Week 11 matchup</h2>'
        '<p>For each fixture: the trench, the coverage, the backers, the '
        'tight-end and safety groups and both quarterback rooms, depth 1 to '
        'the last string each club prints, with the official game status on '
        'every player the report rules on and a flag wherever a listed '
        'depth-1 player is ruled out - the immediate mismatch a matchup '
        'creates. Filter to one fixture to read it on one screen.</p>'
        '<a class="button" href="#matrix">Read the matrix &darr;</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div>'
        '<strong>rows</strong><small>%d games &middot; %d groups &middot; '
        '%d flagged</small></div></section>'

        '<section><div class="note warn"><b>What this page does not claim.</b> '
        'A depth chart is a club\'s own listing, not proof of who starts '
        '(<a href="flags.html">F-27</a>), and a Week 10 designation is not a '
        'Week 11 designation: the statuses here are the official Week 10 '
        'report, the most recent official report published while this page '
        'was built. The position pairing between the two sides is this '
        'desk\'s analyst choice, published in full below; the NFL publishes '
        'no matchup grouping. Houston\'s chart is an image, so every HOU '
        'cell is blank and flagged (<a href="flags.html">F-24</a>). Depth '
        'ranks are the clubs\' own column order, never derived from jersey '
        'number or experience (F-02). Club charts are edited during the game '
        'week: this snapshot was retrieved 2026-11-14, and a club may have '
        'published a newer chart since (verified 2026-11-17: the Colts '
        'released their Week 11 chart on 16 November, and the live Packers '
        'chart no longer lists two players this snapshot holds - both were '
        'transactioned on 14 November). The '
        'row links open the club page as it stands now, so any difference '
        'against this dated snapshot is visible on the row itself.</div></section>'

        '<section id="matrix"><div class="section-head"><div>'
        '<span class="eyebrow">Offense vs defense</span>'
        '<h2>Matchup deficiency matrix</h2><p class="muted">%d of %d rows '
        'carry a listed-starter deficiency or an unassessable chart. Every '
        'row links its official game page and both clubs\' charts.</p>'
        '</div><span class="tag warn">%d flagged</span></div>%s%s</section>'

        '<section><div class="section-head"><div>'
        '<span class="eyebrow">Method</span>'
        '<h2>The position pairing, in full</h2><p class="muted">Published so '
        'the matrix can be argued with: every position label on both sides '
        'of every group.</p></div></div>%s</section>'

        % (hero_rows, len(schedule), len(AXES) + 1, charted,
           hero_def, hero_rows, hero_def, toolbar, matrix, mapping))


def write_pages(site_dir, shell):
    import pages as P
    body_html = body()
    slug = "matchup"
    with open(os.path.join(site_dir, "matchup.html"), "w", encoding="utf-8") as fh:
        fh.write(shell(slug, "Matchup deficiency matrix",
                       "Week 11 offense vs defense: every club's listed depth "
                       "1 to last string at each matchup group, the official "
                       "Week 10 game status on each player, and a flag wherever "
                       "a listed starter is ruled out.",
                       body_html, "matchup.html"))
    return ["matchup.html"]
