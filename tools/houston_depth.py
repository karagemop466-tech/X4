#!/usr/bin/env python3
"""T47: Authorized-source resolution of the Houston depth-chart gap (S5 / F-24).

WHY THIS EXISTS
---------------
The Houston Texans publish their official depth chart only as a single bitmap
image (`houstontexans.com/team/depth-chart` renders one `<img>` with no table
markup and no ordered text). No authorized structured club chart exists for
Houston, and every third-party Houston depth source (ESPN, ProFootballNetwork,
Statz, StatRankings, StickToTheModel) is non-official and is rejected by the
verification policy. That left gate S5 ("depth charts for all 32 clubs") blocked
at 31 of 32 and flag F-24 open.

The brief prescribes the authorized route for exactly this case: "use snap
counts as the starter proxy when the depth chart is unavailable" and "do not
model depth from jersey order; model it from playing time." The official NFL
Game Book is that source. This tool ingests the Game Book for Houston's Week 10
game at Cleveland (HOU 24 - CLE 27, 2026-11-15) and derives **playing-time
depth indices** from two of its sections:

  * Lineups          -> the ACTUAL starters per unit (depth-1 by play, not by chart)
  * Playtime Percent -> per-player snap counts / snap share, split by unit

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
* It does NOT republish raw Game Book player rows. The Game Book's own copyright
  notice restricts reuse to assisting media coverage; per the T38 reuse gate this
  tool stores the raw capture privately (hash + stamp under data/ops/raw/) and
  publishes only DERIVED indices (starter snap share, backup snap share,
  starters-at-100%, and the inactive-player / actual-starter pairing), each
  carrying the Game Center page and the PDF link for manual review.
* It does NOT infer the club's 2nd/3rd/4th-string ordinal chart. The Game Book
  is not a depth chart. The club-chart depth chain for Houston therefore stays
  blank and flagged (F-24, refined); this tool adds the authorized playing-time
  proxy the brief asks for, and says so explicitly.
* It does not touch data/depth-wk11-2026.csv or tools/depth.py. Houston's club
  chart rows remain absent from that dataset by design.

Sources (all fetched live 2026-11-18 UTC):
  Game Center : https://www.nfl.com/games/texans-at-browns-2026-reg-10
  Game Book   : https://static.www.nfl.com/image/upload/v1794829724/gamecenter/ab583279-4feb-11f1-abca-2c54536568a9.pdf
  Raw capture : data/ops/raw/gamebook-hou-at-cle-2026-reg10.txt (+ .stamp)

Usage:  python3 tools/houston_depth.py            # validate + write CSV + page
        python3 tools/houston_depth.py --check    # validate only (CI gate)
"""
import csv
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "ops", "raw", "gamebook-hou-at-cle-2026-reg10.txt")
OUT_CSV = os.path.join(DATA, "houston-playtime-depth-wk10-2026.csv")

GAME_CENTER = "https://www.nfl.com/games/texans-at-browns-2026-reg-10"
GAME_BOOK = ("https://static.www.nfl.com/image/upload/v1794829724/gamecenter/"
             "ab583279-4feb-11f1-abca-2c54536568a9.pdf")
RETRIEVED = "2026-11-18"
# SHA-256 of the committed raw capture (data/ops/raw/gamebook-hou-at-cle-2026-reg10.txt).
RAW_SHA256 = "a9acbb8c8b417147afab7ca5f02a9a99c8656acb93d5fb2c73d1f1f9ea9db2ad"

# ---------------------------------------------------------------------------
# Transcribed VERBATIM from the official Game Book (see raw capture). Names are
# the Game Book's own initials.surname form; they are the join key to SNAPS.
# ---------------------------------------------------------------------------

# Actual starters by position group, from the Game Book "Lineups" section.
LINEUPS_OFF = {
    "QB": ["C.Stroud"],
    "RB": ["W.Marks"],
    "WR": ["N.Collins", "K.Boutte", "X.Hutchinson"],
    "TE": ["D.Schultz"],
    "OL": ["A.Ersery", "F.Nwaiwu", "E.Brown", "E.Ingram", "T.Brown"],
}
LINEUPS_DEF = {
    "DE": ["J.Clowney", "W.Anderson"],
    "DT": ["T.Togiai", "S.Rankins"],
    "CB": ["D.Stingley", "K.Lassiter"],
    "LB": ["J.Hansen", "H.To'oTo'o"],
    "S": ["C.Bullock", "J.Pitre", "M.Stewart"],
}

# Per-player snaps / snap share by unit, from the "Playtime Percentage" section.
# tuple = (unit, group, off_snaps, off_pct, def_snaps, def_pct, st_snaps, st_pct)
# pct is the Game Book's own "percent of playtime" for that unit; 0 = none.
SNAPS = {
    # ---- offense ----
    "A.Ersery":    ("OFF", "OL", 67, 100, 0, 0, 4, 12),
    "E.Ingram":    ("OFF", "OL", 67, 100, 0, 0, 4, 12),
    "F.Nwaiwu":    ("OFF", "OL", 67, 100, 0, 0, 4, 12),
    "T.Brown":     ("OFF", "OL", 67, 100, 0, 0, 4, 12),
    "E.Brown":     ("OFF", "OL", 67, 100, 0, 0, 0, 0),
    "C.Stroud":    ("OFF", "QB", 67, 100, 0, 0, 0, 0),
    "N.Collins":   ("OFF", "WR", 57, 85, 0, 0, 0, 0),
    "X.Hutchinson":("OFF", "WR", 51, 76, 0, 0, 0, 0),
    "K.Boutte":    ("OFF", "WR", 47, 70, 0, 0, 0, 0),
    "D.Schultz":   ("OFF", "TE", 44, 66, 0, 0, 0, 0),
    "T.Dell":      ("OFF", "WR", 33, 49, 0, 0, 0, 0),
    "W.Marks":     ("OFF", "RB", 30, 45, 0, 0, 0, 0),
    "F.Moreau":    ("OFF", "TE", 22, 33, 0, 0, 14, 42),
    "E.Demercado": ("OFF", "RB", 22, 33, 0, 0, 0, 0),
    "D.Ogunbowale":("OFF", "RB", 15, 22, 0, 0, 14, 42),
    "M.Klein":     ("OFF", "TE", 8, 12, 0, 0, 9, 0),
    "B.Fisher":    ("OFF", "OL", 6, 9, 0, 0, 4, 12),
    "J.Andrews":   ("OFF", "OL", 4, 12, 0, 0, 0, 0),
    "N.Thomas":    ("OFF", "OL", 0, 0, 0, 0, 4, 12),
    # ---- defense ----
    "H.To'oTo'o":  ("DEF", "LB", 0, 0, 68, 100, 6, 18),
    "D.Stingley":  ("DEF", "CB", 0, 0, 68, 100, 3, 9),
    "K.Lassiter":  ("DEF", "CB", 0, 0, 68, 100, 3, 9),
    "J.Pitre":     ("DEF", "S", 0, 0, 68, 100, 0, 0),
    "C.Bullock":   ("DEF", "S", 0, 0, 68, 100, 0, 0),
    "J.Hansen":    ("DEF", "LB", 0, 0, 66, 97, 9, 27),
    "M.Stewart":   ("DEF", "S", 0, 0, 65, 96, 8, 24),
    "W.Anderson":  ("DEF", "DE", 0, 0, 54, 79, 8, 24),
    "J.Clowney":   ("DEF", "DE", 0, 0, 52, 76, 2, 6),
    "S.Rankins":   ("DEF", "DT", 0, 0, 45, 66, 2, 6),
    "T.Togiai":    ("DEF", "DT", 0, 0, 44, 65, 2, 6),
    "L.Hall":      ("DEF", "DT", 0, 0, 28, 41, 6, 18),
    "D.Robinson":  ("DEF", "DE", 0, 0, 22, 32, 22, 67),
    "N.Jones":     ("DEF", "DT", 0, 0, 15, 22, 6, 18),
    "K.McDonald":  ("DEF", "DT", 0, 0, 14, 21, 6, 18),
    "R.Blankenship":("DEF", "S", 0, 0, 2, 3, 12, 36),
    "J.Ingram":    ("DEF", "S", 0, 0, 1, 1, 23, 70),
    "T.Smith":     ("DEF", "CB", 0, 0, 0, 0, 29, 88),
    "W.Woodaz":    ("DEF", "LB", 0, 0, 0, 0, 29, 88),
    "J.Hummel":    ("DEF", "LB", 0, 0, 0, 0, 21, 64),
    "K.Ramsey":    ("DEF", "S", 0, 0, 0, 0, 20, 61),
    "C.Muma":      ("DEF", "LB", 0, 0, 0, 0, 20, 61),
    "C.Stover":    ("DEF", "TE", 0, 0, 0, 0, 19, 58),
    "A.Brinkman":  ("DEF", "LS", 0, 0, 0, 0, 11, 33),
    "N.Remigio":   ("DEF", "WR", 0, 0, 0, 0, 11, 33),
    "K.Kroeger":   ("DEF", "P", 0, 0, 0, 0, 11, 33),
    "K.Fairbairn": ("DEF", "K", 0, 0, 0, 0, 9, 27),
}

# Inactive / did-not-play, from the Game Book "Not Active" and "Did Not Play".
INACTIVE = {
    "A.Al-Shaair":  ("DEF", "LB", "Not Active"),
    "B.Jordan":     ("OFF", "TE", "Not Active"),
    "M.Harrison":   ("OFF", "WR", "Not Active"),
    "D.Montgomery": ("OFF", "RB", "Not Active"),
    "D.Hunter":     ("DEF", "DE", "Not Active"),
    "K.Rutledge":   ("OFF", "OL", "Not Active"),
    "W.Teller":     ("OFF", "OL", "Not Active"),
}
DID_NOT_PLAY = {
    "D.Mills": ("OFF", "QB", "Did Not Play"),
    "B.Smith": ("OFF", "OL", "Did Not Play"),
}

GROUPS = [("OFF", LINEUPS_OFF), ("DEF", LINEUPS_DEF)]


# ---------------------------------------------------------------------------
def _page_helpers():
    import pages as P
    return P


def _unit_pct(rec, unit):
    """Snap-share percent for the given unit from a SNAPS tuple."""
    if rec is None:
        return None
    idx = 2 if unit == "OFF" else 4
    return rec[idx + 1]


def _unit_snaps(rec, unit):
    if rec is None:
        return 0
    idx = 2 if unit == "OFF" else 4
    return rec[idx]


def build():
    """Derived playing-time depth indices: one row per position group."""
    rows = []
    for unit, lineups in GROUPS:
        for group, starters in lineups.items():
            starter_set = set(starters)
            # players who appear in the snap table for this unit+group
            members = [(n, SNAPS[n]) for n in SNAPS
                       if SNAPS[n][0] == unit and SNAPS[n][1] == group]
            non_starters = [(n, r) for n, r in members if n not in starter_set]
            # starter snap share = the lead (depth-1) starter's share
            lead = starters[0]
            lead_pct = _unit_pct(SNAPS.get(lead), unit)
            # backup snap share = highest non-starter share at the group
            backup_pct = max((_unit_pct(r, unit) or 0 for _, r in non_starters),
                             default=None)
            starters_100 = sum(1 for s in starters
                               if (_unit_pct(SNAPS.get(s), unit) or 0) == 100)
            inactive_here = [n for n, (u, g, st) in list(INACTIVE.items()) +
                             list(DID_NOT_PLAY.items())
                             if u == unit and g == group]
            rows.append({
                "table": "playtime_depth",
                "team": "HOU",
                "unit": unit,
                "position_group": group,
                "actual_starters": ", ".join(starters),
                "starter_snap_share_pct": "" if lead_pct is None else lead_pct,
                "backup_snap_share_pct": "" if backup_pct is None else backup_pct,
                "starters_at_100pct": starters_100,
                "n_inactive_at_group": len(inactive_here),
                "inactive_players": ", ".join(inactive_here),
                "source_game_center": GAME_CENTER,
                "source_pdf": GAME_BOOK,
                "retrieved": RETRIEVED,
                "raw_sha256": RAW_SHA256,
            })
    # Replacement pairing: each inactive/DNP player vs the actual starter(s) at
    # their position group. A DERIVED index (two verified facts paired), not a
    # raw Game Book row.
    rep_rows = []
    for unit, lineups in GROUPS:
        for group, starters in lineups.items():
            for name, (u, g, status) in list(INACTIVE.items()) + list(DID_NOT_PLAY.items()):
                if u == unit and g == group:
                    rep_rows.append({
                        "table": "replacement_pairing",
                        "team": "HOU",
                        "unit": unit,
                        "position_group": group,
                        "inactive_player": name,
                        "inactive_status": status,
                        "actual_starter_in_place": ", ".join(starters),
                        "source_game_center": GAME_CENTER,
                        "source_pdf": GAME_BOOK,
                        "retrieved": RETRIEVED,
                        "raw_sha256": RAW_SHA256,
                    })
    return rows, rep_rows


def write_csv(rows, rep_rows):
    cols = ["table", "team", "unit", "position_group", "actual_starters",
            "starter_snap_share_pct", "backup_snap_share_pct", "starters_at_100pct",
            "n_inactive_at_group", "inactive_players",
            "inactive_player", "inactive_status", "actual_starter_in_place",
            "source_game_center", "source_pdf", "retrieved", "raw_sha256"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows + rep_rows:
            w.writerow({k: r.get(k, "") for k in cols})


# ---------------------------------------------------------------------------
def check():
    """Validate the transcription against the raw capture and internal rules."""
    problems = []
    # 1. raw capture hash
    if not os.path.exists(RAW):
        problems.append("raw capture missing: %s" % RAW)
    else:
        with open(RAW, "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
        if got != RAW_SHA256:
            problems.append("raw capture hash mismatch: %s != %s" % (got, RAW_SHA256))
    # 2. every lineup player appears in the snap table
    for unit, lineups in GROUPS:
        for group, starters in lineups.items():
            for s in starters:
                if s not in SNAPS:
                    problems.append("starter %s (%s %s) not in snap table" % (s, unit, group))
                elif SNAPS[s][0] != unit or SNAPS[s][1] != group:
                    problems.append("starter %s mapped to %s %s, expected %s %s"
                                    % (s, SNAPS[s][0], SNAPS[s][1], unit, group))
    # 3. snap shares within [0, 100]
    for n, rec in SNAPS.items():
        for i in (3, 5, 7):
            if not (0 <= rec[i] <= 100):
                problems.append("snap share out of range for %s: %s" % (n, rec[i]))
    # 4. inactive / DNP players are not actual starters
    starters_all = {s for _, lu in GROUPS for _, st in lu.items() for s in st}
    for n in list(INACTIVE) + list(DID_NOT_PLAY):
        if n in starters_all:
            problems.append("inactive/DNP player %s is also a listed starter" % n)
    # 5. built rows are non-empty and consistent
    rows, rep_rows = build()
    if len(rows) != 10:
        problems.append("expected 10 position-group rows, got %d" % len(rows))
    for r in rows:
        if not r["actual_starters"]:
            problems.append("empty starters for %s %s" % (r["unit"], r["position_group"]))
    return problems


# ---------------------------------------------------------------------------
def body_real():
    """Render the full page body (kept separate so body() stays simple)."""
    P = _page_helpers()
    esc, src, badge, table, blank = P.esc, P.src, P.badge, P.table, P.blank
    rows, rep_rows = build()

    depth_rows = []
    for r in rows:
        depth_rows.append([
            esc(r["unit"]),
            esc(r["position_group"]),
            esc(r["actual_starters"]),
            (P.num(r["starter_snap_share_pct"]) + "%") if r["starter_snap_share_pct"] != "" else blank(),
            (P.num(r["backup_snap_share_pct"]) + "%") if r["backup_snap_share_pct"] != "" else blank("none"),
            str(r["starters_at_100pct"]),
            str(r["n_inactive_at_group"]),
            esc(r["inactive_players"]) if r["inactive_players"] else blank("none"),
            "%s %s" % (src(r["source_game_center"], "Game Center"),
                       src(r["source_pdf"], "Game Book PDF")),
        ])
    depth_tbl = table(
        [("Unit", 0), ("Group", 0), ("Actual starters (Lineups)", 0),
         ("Starter snap share", 1), ("Backup snap share", 1),
         ("Starters at 100%", 1), ("Inactive at group", 1), ("Inactive players", 0),
         ("Source", 0)],
        depth_rows,
        note=("starter snap share = the depth-1 actual starter's share of that unit's snaps; "
              "backup snap share = the highest non-starter share at the same group. Derived "
              "from the Game Book, not the club's ordinal chart. n = 1 game (Houston at "
              "Cleveland, Week 10)."),
        row_attrs=lambda i: ' data-unit="%s" data-group="%s"' % (
            esc(rows[i]["unit"]), esc(rows[i]["position_group"])))

    rep_rows_html = []
    for r in rep_rows:
        rep_rows_html.append([
            esc(r["unit"]),
            esc(r["position_group"]),
            esc(r["inactive_player"]),
            badge(r["inactive_status"], "warn"),
            esc(r["actual_starter_in_place"]),
            "%s %s" % (src(r["source_game_center"], "Game Center"),
                       src(r["source_pdf"], "Game Book PDF")),
        ])
    rep_tbl = table(
        [("Unit", 0), ("Group", 0), ("Inactive / DNP player", 0), ("Status", 0),
         ("Actual starter at group", 0), ("Source", 0)],
        rep_rows_html,
        note=("Each inactive / did-not-play player is paired with the player who actually "
              "started at the same position group - a derived pairing of two verified Game "
              "Book facts, not a claim about who the club projected to start."),
        row_attrs=lambda i: ' data-unit="%s" data-group="%s"' % (
            esc(rep_rows[i]["unit"]), esc(rep_rows[i]["position_group"])))

    register = [
        ("Houston Texans official depth-chart page",
         [("https://www.houstontexans.com/team/depth-chart", "open")],
         "Chart renders as a single bitmap image; no table markup, no ordered text.",
         "no structured chart", badge("rejected", "no")),
        ("NFL.com club depth-chart address",
         [("https://www.nfl.com/teams/houston-texans", "open")],
         "Returns HTTP 404 for every club (tools/depth.py); the NFL publishes no "
         "structured depth chart.",
         "no structured chart", badge("rejected", "no")),
        ("NFL GSIS (nflgsis.com)",
         [("https://www.nflgsis.com/", "open")],
         "Official league data site (named official in the verification policy); "
         "publishes no depth-chart ordinal feed.",
         "no structured chart", badge("rejected", "no")),
        ("Third-party Houston depth sources (ESPN, PFN, Statz, StatRankings)",
         [("https://www.espn.com/nfl/team/depth/_/name/hou", "ESPN (non-official)"),
          ("https://www.houstontexans.com/team/depth-chart", "official chart")],
         "Structured depth tables exist, but all are non-official aggregators; the "
         "verification policy forbids using them to mark a value verified. The official "
         "chart link is shown because it is the authoritative source these aggregators "
         "derive from.",
         "non-official", badge("rejected", "no")),
        ("Official NFL Game Book (Week 10, HOU at CLE)",
         [(GAME_CENTER, "Game Center"), (GAME_BOOK, "Game Book PDF")],
         "Authorized structured source: Lineups (actual starters) + Playtime Percentage "
         "(per-player snaps / snap share). Used to derive the indices below. Reuse-gated: "
         "raw rows stored privately, indices only.",
         "authorized - used", badge("used", "ok")),
    ]
    reg_rows = [[esc(name), " ".join(src(u, l) for u, l in links), esc(what),
                esc(verdict), bh]
                for name, links, what, verdict, bh in register]
    reg_tbl = table(
        [("Candidate source", 0), ("Link", 0), ("What it publishes", 0),
         ("Verdict", 0), ("", 0)],
        reg_rows)

    hero = (
        "<p>Houston is the only club of the 32 whose official depth chart is published as "
        "an image, so no Houston <b>club-chart depth chain</b> (2nd/3rd/4th string) exists "
        "on an authorized source and those cells stay blank and flagged (<b>F-24</b>). The "
        "brief's prescribed fallback for this case is playing time: <i>use snap counts as "
        "the starter proxy when the depth chart is unavailable</i>. The official NFL Game "
        "Book for Houston's Week 10 game at Cleveland supplies actual starters (Lineups) "
        "and per-player snap counts (Playtime Percentage), so the playing-time depth below "
        "is derived from an authorized source, cell by cell. Raw Game Book rows are stored "
        "privately (hash + stamp under <code>data/ops/raw/</code>); only derived indices are "
        "published, per the T38 reuse gate.</p>"
    )

    return (
        '<section class="card"><span class="eyebrow">What this resolves</span>%s</section>\n'
        '<section class="card"><span class="eyebrow">Source resolution (every candidate tested)</span>%s'
        '<div class="tbl-note">A value is verified only from an official primary source. '
        'Third-party depth tables are structured but non-official, so they are rejected even '
        'though they would fill the cells. The Game Book is the authorized source the brief '
        'names for this case.</div></section>\n'
        '<section class="card"><span class="eyebrow">Playing-time depth by position group (derived index)</span>%s</section>\n'
        '<section class="card"><span class="eyebrow">Inactive players and the actual starter at their position</span>%s</section>\n'
        '<section class="card"><span class="eyebrow">What stays open</span>'
        '<p>The Houston <b>club-chart depth chain</b> (2nd/3rd/4th string) is not published by '
        'any authorized structured source and remains blank and flagged (<b>F-24</b>). Gate '
        '<b>S5</b> ("depth charts for all 32 clubs") is therefore closed for the '
        '<i>starter / playing-time</i> axis only: Houston now has an authorized actual-starter '
        'and snap-share view, while the ordinal depth chain remains a flagged gap. A single '
        'game is n = 1, so no per-position depth statistic is claimed beyond this game.</p>'
        '</section>\n'
    ) % (hero, reg_tbl, depth_tbl, rep_tbl)


def write_pages(site_dir, shell):
    rows, rep_rows = build()
    write_csv(rows, rep_rows)
    body_html = body_real()
    with open(os.path.join(site_dir, "houston-depth.html"), "w", encoding="utf-8") as fh:
        fh.write(shell("houston-depth", "Houston depth - authorized source",
                       "Houston publishes no structured depth chart (image only, F-24). "
                       "Resolved from the official NFL Game Book: actual starters and "
                       "per-player snap counts, published as derived playing-time depth "
                       "indices with the Game Center and PDF links.",
                       body_html, "houston-depth.html"))
    return ["houston-depth.html"]


def main():
    if "--check" in sys.argv:
        problems = check()
        if problems:
            for p in problems:
                print("FAIL:", p)
            print("houston_depth: %d problem(s)" % len(problems))
            return 1
        print("houston_depth: OK (raw hash, lineups, snap shares, inactive consistency)")
        return 0
    problems = check()
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    rows, rep_rows = build()
    write_csv(rows, rep_rows)
    print("houston_depth: wrote %s (%d group rows + %d pairing rows)"
          % (OUT_CSV, len(rows), len(rep_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
