#!/usr/bin/env python3
"""
The private Game-Book operations layer, published as its own page.

``tools/gamebook_sweep.py`` turns 14 official NFL Game Book PDFs into the five
public datasets behind ``gamebook.html``. This module documents the layer that
sits underneath those datasets: the raw verbatim captures, their hashes and
stamps, the parse, the derived datasets, and the reuse gate that separates the
two.

The split exists because a PDF is a *licensed artefact*, not data. The verbatim
text and the per-player rows it contains are kept in the repository as evidence
and are never re-published as a table of their own; only numbers derived from
them - a play rate with its interval, a starter row, a venue string - are
published. This page is the record of that boundary.

Run:  python3 tools/gamebook_ops.py
"""
import csv
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "ops", "raw")
DATA = os.path.join(ROOT, "data")
SITE = os.path.join(ROOT, "site")

WEEK = 10
RETRIEVED = "2026-11-18"
INVENTORY = os.path.join(ROOT, "data", "ops", "gamebook-capture-inventory.json")


# --------------------------------------------------------------- the captures
def captures():
    """One row per stored raw capture: name, bytes, SHA-256, stamp."""
    inv = {}
    if os.path.exists(INVENTORY):
        inv = json.load(open(INVENTORY, encoding="utf-8"))
    rows = []
    for name in sorted(inv):
        rec = inv[name]
        rows.append({
            "file": name,
            "bytes": rec["bytes"],
            "sha256": rec["sha256"],
            "stamp": rec["stamp"],
        })
    return rows


def _slug_game(name):
    """gamebook-hou-at-cle-full-2026-reg10.txt -> (HOU, CLE)."""
    core = name.replace("gamebook-", "").replace("-full", "")
    core = core.replace("-2026-reg10.txt", "")
    parts = core.split("-at-")
    return (parts[0].upper(), parts[1].upper()) if len(parts) == 2 else ("", "")


# ------------------------------------------------------------------- datasets
PUBLIC_DATASETS = [
    ("data/venue-surface-wk10-2026.csv",
     "Stadium, city, surface/roof, game weather, attendance, kickoff, duration",
     "One row per game", "Totals and passing props need the roof/surface field; "
     "it was not on the site before this sweep."),
    ("data/actual-starters-wk10-2026.csv",
     "Team, unit, position, jersey, player, flag",
     "One row per starting slot",
     "The league's own record of who started, which is not the club depth chart."),
    ("data/inactive-lists-wk10-2026.csv",
     "Team, section (Not Active / Did Not Play), position, jersey, player, note",
     "One row per listed player",
     "The official game-day exclusions, kept apart from the Friday report."),
    ("data/designation-outcomes-wk10-2026.csv",
     "Player, designation, practice, what the Game Book shows, verdict, resolution",
     "One row per designated player",
     "The join behind the calibration, published row by row so the rate can be checked."),
    ("data/designation-reliability-wk10-2026.csv",
     "Designation, n resolved, played, play rate, 95% Wilson interval, n unresolved",
     "One row per designation",
     "The first empirical answer to what Out/Doubtful/Questionable meant."),
]

PRIVATE_ARTIFACTS = [
    ("data/ops/raw/gamebook-*.txt",
     "Verbatim text converted from the official Game Book PDF of each game",
     "Evidence only - never republished as a table"),
    ("data/ops/raw/gamebook-*.txt.stamp",
     "UTC retrieval stamp per capture",
     "Freshness; lets a reader tell how old a capture is"),
    ("data/ops/gamebook-capture-inventory.json",
     "Byte count and SHA-256 of every capture",
     "Alteration check - a changed capture changes its hash"),
    ("research/verification/gamebook-sweep-2026-11-18.md",
     "What the sweep proved, what it could not, per game",
     "The audit trail for the published numbers"),
    ("research/verification/gamebook-sweep-2026-11-18.csv",
     "The same record as machine-readable check/value/detail rows",
     "Gate-readable form of the above"),
]

PIPELINE = [
    ("1. Locate", "The game-centre page of each official Week 10 game is read and "
     "the &ldquo;Download Game Book (PDF)&rdquo; link under END GAME is taken from "
     "that page.", "nfl.com/games/&lt;away&gt;-at-&lt;home&gt;-2026-reg-10"),
    ("2. Capture", "The PDF is converted to text and stored verbatim under "
     "<code>data/ops/raw/</code> with a UTC stamp. No value is edited at this stage.",
     "data/ops/raw/gamebook-*.txt"),
    ("3. Hash", "A SHA-256 is taken of every capture and recorded in the inventory, "
     "so a later edit is detectable rather than invisible.",
     "data/ops/gamebook-capture-inventory.json"),
    ("4. Parse", "Sections are split on the printed rule lines and each of the four "
     "player lists - Lineups, Substitutions, Did Not Play, Not Active - is parsed "
     "into rows. A row the conversion lost is kept as a blank row with a flag.",
     "tools/gamebook_sweep.py"),
    ("5. Join", "Each player on the official Week 10 injury report is matched to his "
     "own game&rsquo;s Game Book by surname <i>and</i> first initial. A surname alone "
     "is not accepted.", "tools/gamebook_sweep.py"),
    ("6. Derive", "Play rates are computed per designation with a 95% Wilson interval "
     "and the unresolved count published beside n.",
     "data/designation-reliability-wk10-2026.csv"),
    ("7. Publish", "Only the derived datasets reach the site. The raw captures stay in "
     "the repository as evidence behind the private page.",
     "gamebook.html"),
]

NOT_USED_FOR = [
    ("Re-publishing the PDF text",
     "The Game Book is a licensed league artefact. Its verbatim text is evidence, "
     "not content, so it is stored and hashed rather than rendered as a page of its "
     "own."),
    ("Filling a blank by inference",
     "Where the conversion lost a cell - eleven Cleveland starters, a Dallas "
     "defensive name column - the cell is published blank with the reason. It is "
     "never filled from another week, a club site or a memory of the roster."),
    ("Deciding a designation outcome from absence",
     "A player absent from all four Game Book sections is unresolved, not "
     "&lsquo;did not play&rsquo;. Treating absence as an inactive would inflate n and "
     "bias the play rate downward."),
    ("Feeding the calibration into the model",
     "One week of one season is a first estimate, not a constant. The Doubtful "
     "interval spans 3%&ndash;56%, so it is published as uninformative rather than "
     "used as a feature."),
    ("Ranking depth by jersey number",
     "Explicitly rejected in the brief. Depth order comes from a club chart or from "
     "playing time, never from a number on a shirt."),
]


def _rows_csv(path):
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------------ rendering
def body_real():
    import pages as P
    esc, src, badge, table, blank = P.esc, P.src, P.badge, P.table, P.blank
    caps = captures()
    h = []

    h.append(
        '<section class="card"><span class="eyebrow">What this layer is</span>'
        '<p>Every number on the <a href="gamebook.html">Game books</a> page is derived '
        'from an official NFL Game Book: the PDF the league publishes after each game '
        'holding the lineups, the substitutions, the did-not-play and not-active '
        'lists, and the header with the stadium, surface and weather. This page is the '
        'record of the layer <i>underneath</i> those numbers - the verbatim captures, '
        'their hashes and stamps, the parse that turns them into rows, and the reuse '
        'gate that separates what is stored from what is published.</p>'
        '<p>The split is not ceremony. A PDF is a licensed artefact rather than data, '
        'so its text is kept as evidence that can be re-read and re-checked, and only '
        'values derived from it - a play rate with its interval, a starter row, a '
        'venue string - are published. The distinction matters most where the source '
        'is incomplete: a cell the conversion lost is published as a blank with the '
        'reason it is blank, and the raw capture is what lets a reader confirm that '
        'the blank is the source&rsquo;s, not ours.</p></section>')

    # --- pipeline ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Pipeline</span>'
             '<h2>From a PDF link to a published number</h2>'
             '<p class="muted">Seven stages, each with the artefact it produces. '
             'Nothing enters a published dataset without passing through all '
             'seven.</p></div></div>')
    rows = [[esc(s), t, "<code class='mono'>%s</code>" % esc(a)]
            for s, t, a in PIPELINE]
    h.append(table([("Stage", 0), ("What happens", 0), ("Artefact", 0)], rows, cls="doc"))
    h.append('</section>')

    # --- capture inventory ---
    total_bytes = sum(c["bytes"] for c in caps)
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Capture register</span>'
             '<h2>Every capture, its size, hash and stamp</h2>'
             '<p class="muted">%d captures, %s bytes total, all retrieved %s. The hash '
             'is taken over the stored bytes, so any later edit - accidental or not - '
             'changes it. The stamp is the UTC retrieval time written when the capture '
             'was saved.</p></div>'
             '<span class="tag">%d captures</span></div>'
             % (len(caps), "{:,}".format(total_bytes), RETRIEVED, len(caps)))
    _pdf = {}
    for _r in _rows_csv(os.path.join(ROOT, "data", "venue-surface-wk10-2026.csv")) or []:
        _pdf[(_r["away"], _r["home"])] = (_r["source_game_center"], _r["source_pdf"])
    rows = []
    for c in caps:
        away, home = _slug_game(c["file"])
        rows.append([
            esc("%s @ %s" % (away, home)) if away else esc(c["file"]),
            "<code class='mono'>%s</code>" % esc(c["file"]),
            P.num(c["bytes"]),
            "<code class='mono'>%s&hellip;</code>" % esc(c["sha256"][:24]),
            "<code class='mono'>%s</code>" % esc(c["stamp"]),
            badge("stamped", "ok") if c["stamp"] else blank("no stamp"),
            ("%s %s" % (src(_pdf[(away, home)][0], "Game centre"),
                        src(_pdf[(away, home)][1], "PDF")))
            if (away, home) in _pdf else blank(),
        ])
    h.append(table([("Game", 0), ("Capture file", 0), ("Bytes", 1),
                    ("SHA-256 (first 24)", 0), ("Retrieved (UTC)", 0), ("", 0),
                    ("Source", 0)],
                   rows,
                   note="Two captures exist for Houston at Cleveland: the one taken by "
                        "T47 (Houston side only) and the full re-capture of both clubs. "
                        "Both are kept; their Houston rows agree independently."))
    h.append('</section>')

    # --- private artefacts ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Private artefacts</span>'
             '<h2>What is stored and not published</h2>'
             '<p class="muted">These files live in the repository so a published '
             'number can be traced back to the text it came from. They are not '
             'rendered as site pages.</p></div></div>')
    rows = [[("<code class='mono'>%s</code>" % esc(p)), esc(what), esc(why)]
            for p, what, why in PRIVATE_ARTIFACTS]
    h.append(table([("Path", 0), ("Contents", 0), ("Why it is kept", 0)], rows, cls="doc"))
    h.append('</section>')

    # --- public datasets ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Public exports</span>'
             '<h2>What is derived and published</h2>'
             '<p class="muted">Five datasets, each carrying the official source of '
             'every row. These are the only Game Book outputs that reach the '
             'site.</p></div><span class="tag">%d datasets</span></div>'
             % len(PUBLIC_DATASETS))
    rows = []
    for path, cols, grain, why in PUBLIC_DATASETS:
        n = _rows_csv(os.path.join(ROOT, path))
        rows.append([
            "<code class='mono'>%s</code>" % esc(path),
            esc(cols), esc(grain),
            P.num(len(n)) if n is not None else blank("not built"),
            esc(why),
            src("https://www.nfl.com/schedules/2026/by-week/week-10", "Schedule"),
        ])
    h.append(table([("Dataset", 0), ("Columns", 0), ("Grain", 0), ("Rows", 1),
                    ("Why it exists", 0), ("Source", 0)], rows))
    h.append('</section>')

    # --- not used for ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Reuse gate</span>'
             '<h2>What this layer is deliberately not used for</h2>'
             '<p class="muted">The gate is the point of the layer. Each row is a way '
             'the data could be used that would produce a number the sources do not '
             'support.</p></div></div>')
    rows = [[esc(what), esc(why)] for what, why in NOT_USED_FOR]
    h.append(table([("Not used for", 0), ("Why", 0)], rows, cls="doc"))
    h.append('</section>')

    # --- verify ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Reproducing it</span>'
             '<h2>How to check this yourself</h2>'
             '<p class="muted">The sweep is one command and it validates before it '
             'writes. The gate enforces 14 games, an https source on every row, '
             'eleven-or-blank starters per unit, and the arithmetic of the reliability '
             'table.</p></div></div>')
    h.append(
        '<pre class="mono" style="white-space:pre-wrap;background:var(--panel);'
        'border:1px solid var(--line);border-radius:10px;padding:14px 16px;'
        'font-size:13px;line-height:1.6">'
        'python3 tools/gamebook_sweep.py --check    # validate only, exit 1 on any problem\n'
        'python3 tools/gamebook_sweep.py            # rebuild the five datasets\n'
        'sha256sum data/ops/raw/gamebook-*.txt      # compare with the register above'
        '</pre>')
    h.append('</section>')
    return "".join(h)


def write_pages(site_dir, shell):
    body = body_real()
    with open(os.path.join(site_dir, "gamebook-ops.html"), "w", encoding="utf-8") as fh:
        fh.write(shell(
            "gamebook-ops", "Game Book operations (private layer)",
            "The layer underneath the published Game Book datasets: the verbatim "
            "captures and their hashes, the parse, the five derived datasets, and the "
            "reuse gate that separates what is stored from what is published.",
            body, "gamebook-ops.html"))
    return ["gamebook-ops.html"]


def main():
    print("gamebook_ops: %d captures registered" % len(captures()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
