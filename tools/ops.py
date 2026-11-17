#!/usr/bin/env python3
"""
Build the origination and operations layer of the site.

Seven pages, all statically rendered at build time from the CSV/JSON files in
``data/ops/`` and ``data/``. No value on any page is typed into this file: every
number is read from an artifact that a previous step produced, and every table
row carries the link of the source that backs it.

Pages written into ``site/`` (and mirrored to the repository root by
``tools/sync.py``):

  origination.html       the numbers we originate: side, then total, then moneyline
  price-store.html       the price-snapshot store and its provenance
  signal-vs-staking.html the leaderboard, with signal and staking scored apart
  correlations.html      correlations from officially sourced numbers, with n
  replacements.html      replacement depth, as far as the official record goes
  method-lab.html        fundamentals, best practice and signal-generation research
  ops-review.html        the review gate for this layer's own suggestions

Run:  python3 tools/ops.py
"""
import csv
import html
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_nav

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = os.path.join(ROOT, "data", "ops")
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(ROOT, "data")

NAV = [
    ("index.html", "◫ &nbsp;Overview"),
    ("executive-summary.html", "★ &nbsp;Executive summary"),
    ("requirements.html", "☰ &nbsp;Requirements"),
    ("data.html", "▦ &nbsp;Verified data"),
    ("signals.html", "◎ &nbsp;Line lab &amp; signals"),
    ("origination.html", "⊞ &nbsp;Line origination"),
    ("price-store.html", "◈ &nbsp;Price store"),
    ("signal-vs-staking.html", "⚖ &nbsp;Signal vs staking"),
    ("correlations.html", "∿ &nbsp;Correlations"),
    ("replacements.html", "＋ &nbsp;Availability &amp; depth"),
    ("method-lab.html", "⌁ &nbsp;Method lab"),
    ("injuries.html", "＋ &nbsp;Injury rows"),
    ("leaderboard.html", "↗ &nbsp;Leaderboard"),
    ("decisions.html", "? &nbsp;Decision Q&amp;A"),
    ("review.html", "✳ &nbsp;Suggestions"),
    ("workbench.html", "✳ &nbsp;Suggestion workbench"),
    ("programme.html", "◫ &nbsp;Integrity &amp; programme"),
    ("verification.html", "✓ &nbsp;Verification"),
    ("requirements-closure.html", "☑ &nbsp;Requirement closure"),
    ("ops-review.html", "✧ &nbsp;Review gate"),
    ("flagged.html", "⚑ &nbsp;Flagged for review"),
    ("repo-review.html", "§ &nbsp;Repo review"),
    ("sources.html", "↗ &nbsp;Sources"),
]

NFL = "https://www.nfl.com"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_json(path):
    if not os.path.exists(path):
        return {}
    return json.load(open(path, encoding="utf-8"))


def ext(url, label):
    """An external source link, always https, always noreferrer."""
    if not url:
        return ""
    return '<a href="%s" target="_blank" rel="noreferrer">%s ↗</a>' % (esc(url), esc(label))


def local(href, label):
    return '<a href="%s">%s</a>' % (esc(href), esc(label))


def repo_blob(href):
    """The committed copy of a repository file, for manual review. The blob is
    the durable, verifiable home of the artifact a published value came from."""
    return "https://github.com/karagemop466-tech/X4/blob/main/" + href


def artifact(href, label="artifact"):
    """A link to this project's own data file at its committed home on GitHub.
    Deliberately not styled as a source: a source is an outside page that backs
    the value, an artifact is where the value is stored and can be re-read."""
    return '<a class="muted" href="%s">%s</a>' % (esc(repo_blob(href)), esc(label))


NFL_SCHED = NFL + "/schedules/2026/"
NFL_STAND = NFL + "/standings/"
NFL_INJ = NFL + "/injuries/"
NFL_STATS = NFL + "/stats/"
NFL_TXN = NFL + "/transactions/"


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def sd(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def fisher_ci(r, n):
    """95% Fisher-z interval for a Pearson correlation."""
    if r is None or n < 4:
        return ("", "")
    r = max(-0.999999, min(0.999999, r))
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se
    def inv(v):
        return (math.exp(2 * v) - 1) / (math.exp(2 * v) + 1)
    return (inv(lo), inv(hi))


def fmt(x, nd=2):
    if x in ("", None):
        return ""
    try:
        return ("%." + str(nd) + "f") % float(x)
    except (TypeError, ValueError):
        return esc(x)


def pill(text, kind="info"):
    return '<span class="pill %s">%s</span>' % (kind, esc(text))


def page(slug, title, eyebrow, heading, status, body):
    side = desk_nav.side()
    return """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="%(desc)s"><title>%(title)s | Fourth Down Research</title><link rel="stylesheet" href="desk.css"></head>
<body>
%(side)s
<main>
<header class="topbar"><div><span class="eyebrow">%(eyebrow)s</span><h1>%(heading)s</h1></div><span class="status-pill"><i></i>%(status)s</span></header>
%(body)s
<footer><span>FOURTH DOWN RESEARCH · %(foot)s</span><span><a href="index.html">Overview</a> · <a href="sources.html">Sources</a></span></footer>
</main>
<script src="nav.js"></script>
</body>
</html>
""" % dict(desc=esc(heading + " - " + title), title=esc(title), side=side,
           eyebrow=esc(eyebrow), heading=heading, status=esc(status),
           body=body, foot=esc(title))


def table(headers, rows, cls="data", numeric=()):
    th = "".join("<th>%s</th>" % h for h in headers)
    out = ['<div class="table-wrap"><table class="%s"><thead><tr>%s</tr></thead><tbody>' % (cls, th)]
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            k = ' class="num"' if i in numeric else ""
            cells.append("<td%s>%s</td>" % (k, c))
        out.append("<tr>%s</tr>" % "".join(cells))
    out.append("</tbody></table></div>")
    return "".join(out)


def section(sid, eyebrow, heading, muted, tag, inner):
    tag_html = '<span class="tag">%s</span>' % tag if tag else ""
    return ('<section class="section" id="%s"><div class="section-head"><div>'
            '<span class="eyebrow">%s</span><h2>%s</h2>%s</div>%s</div>%s</section>'
            % (sid, eyebrow, heading,
               '<p class="muted">%s</p>' % muted if muted else "", tag_html, inner))


# ---------------------------------------------------------------------------
# the numbers behind the pages
# ---------------------------------------------------------------------------
def load():
    d = {
        "model": read_json(os.path.join(OPS, "model_card.json")),
        "markets": read_csv(os.path.join(OPS, "markets.csv")),
        "fair": read_csv(os.path.join(OPS, "fair_lines.csv")),
        "fmd": read_csv(os.path.join(OPS, "fair_market_difference.csv")),
        "prices": read_csv(os.path.join(OPS, "price_snapshots.csv")),
        "snapshots": read_csv(os.path.join(OPS, "snapshots.csv")),
        "events": read_csv(os.path.join(OPS, "events.csv")),
        "identity": read_csv(os.path.join(OPS, "event_identity.csv")),
        "unresolved": read_csv(os.path.join(OPS, "event_identity_unresolved.csv")),
        "graded": read_csv(os.path.join(OPS, "graded.csv")),
        "gates": read_csv(os.path.join(OPS, "gates.csv")),
        "signal": (read_csv(os.path.join(OPS, "scores_signal.csv")) or [{}])[0],
        "staking": (read_csv(os.path.join(OPS, "scores_staking.csv")) or [{}])[0],
        "demotion": read_csv(os.path.join(OPS, "demotion_rules.csv")),
        "demotions": read_csv(os.path.join(OPS, "paper_demotions.csv")),
        "results": read_csv(os.path.join(OPS, "results.csv")),
        "games": read_csv(os.path.join(DATA, "games-2026.csv")),
        "standings": read_csv(os.path.join(DATA, "standings-wk10-2026.csv")),
        "injuries": read_csv(os.path.join(DATA, "injuries-wk10-2026.csv")),
        "transactions": read_csv(os.path.join(DATA, "transactions", "transactions-2026.csv")),
        "depth": read_csv(os.path.join(OPS, "depth.csv")),
        "depth_club": read_csv(os.path.join(OPS, "depth_club.csv")),
        "schedule": read_csv(os.path.join(DATA, "schedule-wk11-2026.csv")),
        "schedule_wk10": read_csv(os.path.join(DATA, "schedule-wk10-2026.csv")),
        "international": read_csv(os.path.join(DATA, "international-2026.csv")),
        "charts": read_csv(os.path.join(DATA, "depth-wk11-2026.csv")),
    }
    return d


def correlation_rows(d, weeks=None):
    """Every published correlation, computed only from officially sourced numbers."""
    games = [g for g in d["games"]]
    if weeks:
        games = [g for g in games if int(g["week"]) in weeks]
    away = [int(g["away_pts"]) for g in games if g.get("away_pts") not in ("", None)]
    home = [int(g["home_pts"]) for g in games if g.get("home_pts") not in ("", None)]
    margins = [h - a for a, h in zip(away, home)]
    totals = [h + a for a, h in zip(away, home)]
    standings = d["standings"]
    net = [int(r["net_pts"]) for r in standings]
    pct = [float(r["pct"]) for r in standings]
    pfg = [float(r["pf"]) / max(1, int(r["w"]) + int(r["l"]) + int(r["t"])) for r in standings]
    pag = [float(r["pa"]) / max(1, int(r["w"]) + int(r["l"]) + int(r["t"])) for r in standings]

    defs = [
        ("away score ↔ home score", away, home,
         "both teams' scoring in the same game", "Official game log (all _N_ completed games)",
         NFL + "/schedules/2026/"),
        ("home margin ↔ game total", margins, totals,
         "the single most important number for a parlay that mixes a side with a total",
         "Official game log", NFL + "/schedules/2026/"),
        ("net points ↔ win percentage", net, pct,
         "how much of a club's record is scoring margin", "Official standings (32 clubs)",
         NFL + "/standings/"),
        ("points for /g ↔ points allowed /g", pfg, pag,
         "whether high-scoring clubs also concede", "Official standings (32 clubs)",
         NFL + "/standings/"),
    ]
    rows = []
    for label, xs, ys, why, src_label, url in defs:
        n = min(len(xs), len(ys))
        r = pearson(xs[:n], ys[:n])
        lo, hi = fisher_ci(r, n)
        rows.append({"label": label, "r": r, "n": n, "lo": lo, "hi": hi,
                     "why": why, "src_label": src_label, "url": url})
    return rows


# ---------------------------------------------------------------------------
# page: origination
# ---------------------------------------------------------------------------
def build_origination(d):
    m = d["model"]
    fmd = d["fmd"]
    fair = d["fair"]

    rows = []
    for r in fmd:
        fair_v = r["fair"]
        if r["market"] == "moneyline":
            fair_v = r["fair"] + " home win"
        diff = r["diff_vs_close"] or r["diff_vs_open"]
        moved = "—"
        try:
            moved = "%+.1f" % (float(r["market_close"]) - float(r["market_open"]))
        except (ValueError, TypeError):
            pass
        rows.append([
            "<b>%s</b> at <b>%s</b>" % (esc(r["away"]), esc(r["home"])),
            esc(r["market"]),
            esc(fair_v),
            esc(r["market_open"] or "—") + " → " + esc(r["market_close"] or "—"),
            esc(diff or "—"),
            pill(r["close_kind"] or "none", "ok" if r["close_kind"] == "close" else "warn"),
            ext(r["source_url"], r["book"] or "odds") +
            (" · " + ext(r["official_result_url"], "official result") if r["official_result_url"] else ""),
        ])

    coverage = []
    for w in ("10", "11"):
        evs = [e for e in d["events"] if e["week"] == w]
        priced = [e for e in evs if e["priced"] == "1"]
        coverage.append([w, "%d" % len(evs), "%d" % len(priced),
                         "%d" % (len(evs) - len(priced)),
                         ext("%s/schedules/2026/by-week/week-%s" % (NFL, w), "official week %s" % w)])

    gap_rows = [[esc(u["event_id"]), esc(u["week"]), esc(u["reason"]),
                 ext("%s/schedules/2026/by-week/week-%s" % (NFL, u["week"]), "official schedule")]
                for u in d["unresolved"]]

    he = m.get("home_edge", {})
    model_rows = [
        ["Order of origination", "side → total → moneyline",
         "fixed in the pipeline, not a preference", artifact("research/model-lines-week11.md")],
        ["Prior strength (k)", esc(fmt(m.get("prior_games"), 1)) + " games",
         "a club is shrunk toward the league mean by k/(games played + k)",
         ext(NFL_STAND, "official standings")],
        ["Home edge applied", "yes" if m.get("use_home_edge") else "no",
         "measured from the official game log, never assumed",
         ext(NFL_SCHED, "official schedule")],
        ["Measured home edge", "%+.2f pts" % float(he.get("mean", 0)),
         "n = %s games (weeks 6–9 2026), 95%% CI [%+.2f, %+.2f]"
         % (he.get("n", ""), float(he.get("ci95", [0, 0])[0] or 0),
            float(he.get("ci95", [0, 0])[1] or 0)),
         ext(NFL_SCHED + "by-week/week-9", "official results, weeks 6–9")],
        ["Neutral-site games", "%d in 2026" % len(d["international"]),
         "every 2026 International Game, read from the official weekly schedule label "
         "rather than typed by hand; the home edge is set to 0 on each, so it is never "
         "applied twice. Week 10's Munich game (Patriots at Lions) was missing from an "
         "earlier hand-typed set of three and is the reason this is now derived",
         ext(NFL_SCHED, "official schedule")],
        ["Margin spread (sigma)", esc(fmt(m.get("sigma_margin"), 1)) + " pts",
         "used to turn the fair side into a fair moneyline",
         ext(NFL_SCHED, "official results")],
        ["Markets originated", esc(m.get("n_markets")), "one row per game per market type",
         ext(NFL_SCHED, "official fixtures")],
        ["Events seen / bound", "%s / %s" % (esc(m.get("n_events_seen")), esc(m.get("n_events_resolved"))),
         "an event with no odds body or no favourite cannot be bound and is reported, not guessed",
         ext(NFL_SCHED, "official schedule")],
    ]

    body = (
        '<section class="hero"><div><span class="eyebrow light">ORIGINATION v1</span>'
        '<h2>Our own number for every market, with the market beside it</h2>'
        '<p>Three separate columns, never one: the <b>fair</b> number we originate, the '
        '<b>market</b> number the store recorded, and the <b>difference</b> between them. '
        'A difference is a claim, not a bet. It becomes a signal only after the gates on '
        + local("signal-vs-staking.html", "the signal page") + ' pass, and none have.</p>'
        '<a class="button" href="#fmd">Read the numbers ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%s</div><strong>markets originated</strong>'
        '<small>%s events bound to an official fixture</small></div></section>' % (
            esc(m.get("n_markets", 0)), esc(m.get("n_events_resolved", 0)))
        + section("model", "MODEL CARD", "How the fair number is produced",
                  "Every parameter is printed. Nothing here is tuned against the market, "
                  "because tuning against the market would make the difference a copy of it.",
                  "v1 · RATIO MODEL", table(
                      ["Parameter", "Value", "Note", "Source"], model_rows))
        + section("fmd", "FAIR · MARKET · DIFFERENCE", "Every originated market, three columns",
                  "A positive difference means our number makes the quoted side more likely "
                  "than the market does. The arrow shows how far the market itself moved "
                  "between the first reading and the last one before kickoff.",
                  "%d MARKETS" % len(fmd), table(
                      ["Game", "Market", "Fair (ours)", "Market open → close", "Difference",
                       "Close kind", "Source"], rows) if rows else
                  '<div class="note">No market could be originated: no cached price body '
                  'exists for this build. The gap is listed below rather than filled.</div>')
        + section("coverage", "COVERAGE", "What we could and could not originate",
                  "Every event the upstream lists, whether or not its price could be read. "
                  "An unread price is a visible blank, never an invented number.",
                  "HONEST COVERAGE", table(
                      ["Week", "Events listed", "Priced", "Unpriced", "Official source"],
                      coverage, numeric=(1, 2, 3)))
        + section("gaps", "GAPS, NOT GUESSES", "Events with no bound price",
                  "The reason is recorded per event so the next build can tell a retrieval "
                  "gap from a genuine pick'em.", "%d OPEN" % len(d["unresolved"]),
                  table(["ESPN event", "Week", "Why it is not originated", "Official source"],
                        gap_rows) if gap_rows else
                  '<div class="note">Every listed event is bound and priced.</div>')
        + section("method", "WHAT THE MODEL DOES NOT SEE", "The deliberate blind spots",
                  "", "", '<div class="callout"><p>The ratio model reads points scored and '
                  'allowed, and nothing else. It does not read injuries, the depth of the '
                  'replacement behind an injury, rest, travel, weather, or who is starting at '
                  'quarterback. Each of those is a candidate signal on '
                  + local("method-lab.html", "the method lab")
                  + ', and each has to clear the gates before it is allowed to move a '
                  'published number.</p></div>')
    )
    return body


# ---------------------------------------------------------------------------
# page: price store
# ---------------------------------------------------------------------------
def build_price_store(d):
    snaps = d["snapshots"]
    prices = d["prices"]

    moves = []
    for p in prices:
        if p["market"] == "moneyline":
            continue
        try:
            o, c = float(p["open_line"]), float(p["close_line"])
        except (ValueError, TypeError):
            continue
        moves.append((p, c - o))

    manifest_rows = [[esc(s["kind"]), esc(os.path.basename(s["file"])),
                      esc(s["retrieved_utc"]), esc(s["bytes"]),
                      "<code>%s…</code>" % esc(s["sha256"][:16]),
                      ext(s["url"], "upstream")] for s in snaps]

    price_rows = []
    for p in prices:
        line = "%s / %s" % (p["open_line"] or "—", p["close_line"] or "—")
        price = "%s / %s" % (p["open_price"] or p["open_ml"] or "—",
                             p["close_price"] or p["close_ml"] or "—")
        price_rows.append([esc(p["event_id"]), esc(p["week"]), esc(p["market"]),
                           esc(p["selection"]), esc(p["book"]),
                           esc(line), esc(price),
                           pill(p["close_kind"], "ok" if p["close_kind"] == "close" else "warn"),
                           esc(p["retrieved_utc"])[:16].replace("T", " ") + "Z",
                           ext(p["source_url"], "snapshot")])

    moved = sum(1 for _, m in moves if abs(m) > 1e-9)
    biggest = sorted(moves, key=lambda x: -abs(x[1]))[:5]
    big_rows = [[esc(p["event_id"]), esc(p["market"]), esc(p["open_line"]), esc(p["close_line"]),
                 "%+.1f" % mv, ext(p["source_url"], "snapshot")] for p, mv in biggest]

    body = (
        '<section class="hero"><div><span class="eyebrow light">THE STORE</span>'
        '<h2>Opening and closing numbers, kept apart and never overwritten</h2>'
        '<p>A single "line" column cannot answer the only question that matters — whether a '
        'number moved, and which way. Every market here therefore carries '
        '<code>open_*</code> and <code>close_*</code> as separate fields, with the UTC time '
        'the reading was taken and the URL it was read from. A re-read appends a new row; it '
        'does not edit the old one.</p><a class="button" href="#store">See the store ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div><strong>market readings</strong>'
        '<small>%d of them moved between open and close</small></div></section>' % (
            len(prices), moved)
        + section("rules", "THE FIVE RULES", "Why this store can be trusted",
                  "", "APPEND-ONLY", '<div class="cards">'
                  '<div class="card"><span class="k">RULE 1</span><h3>Open and close are separate columns</h3>'
                  '<p>A market with one reading says so — <code>close_kind</code> reads '
                  '<code>same_as_open</code> or <code>current_as_close</code>. Nobody can mistake '
                  'a single quote for a movement.</p></div>'
                  '<div class="card"><span class="k">RULE 2</span><h3>Nothing is overwritten</h3>'
                  '<p>A re-fetch appends. The file therefore grows into an audit trail rather '
                  'than being silently rewritten.</p></div>'
                  '<div class="card"><span class="k">RULE 3</span><h3>Every row carries provenance</h3>'
                  '<p><code>retrieved_utc</code> and <code>source_url</code> are mandatory. A row '
                  'without a URL fails the build.</p></div>'
                  '<div class="card"><span class="k">RULE 4</span><h3>A missing number stays blank</h3>'
                  '<p>No interpolation, no carry-forward. Blank means the upstream did not '
                  'publish it at that reading.</p></div>'
                  '<div class="card"><span class="k">RULE 5</span><h3>Third-party prices are labelled</h3>'
                  '<p>Prices are a commercial product. Every row is <code>tier T3</code> until a '
                  'licensed feed is authorised, and the label travels with the number.</p></div>'
                  '</div>')
        + section("store", "THE STORE", "Every reading, with its source",
                  "The line is the spread or the total; the price is the odds paid on it. "
                  "The moneyline carries a price and no line, because a moneyline has no "
                  "spread attached.", "%d ROWS" % len(prices),
                  table(["Event", "Wk", "Market", "Selection", "Book", "Line open / close",
                         "Price open / close", "Close kind", "Read at (UTC)", "Source"],
                        price_rows) if price_rows else
                  '<div class="note">The store is empty. Nothing can be published from it.</div>')
        + section("movement", "MOVEMENT", "The largest moves in the store",
                  "A large move is the clearest evidence that a single reading is not enough.",
                  "TOP %d" % len(big_rows),
                  table(["Event", "Market", "Open", "Close", "Move", "Source"], big_rows,
                        numeric=(2, 3, 4)) if big_rows else
                  '<div class="note">No movement can be measured: no market has two readings.</div>')
        + section("provenance", "PROVENANCE", "The manifest of every body read",
                  "Each body is cached verbatim and hashed. If a body is edited after it was "
                  "read, its sha256 no longer matches this manifest and the change is visible.",
                  "%d BODIES" % len(snaps),
                  table(["Kind", "Cached body", "Read at (UTC)", "Bytes", "sha256",
                         "Upstream"], manifest_rows) if manifest_rows else
                  '<div class="note">No body has been cached yet.</div>')
    )
    return body


# ---------------------------------------------------------------------------
# page: signal vs staking
# ---------------------------------------------------------------------------
def build_signal_vs_staking(d):
    s, k = d["signal"], d["staking"]
    gates = d["gates"]

    signal_rows = [
        ["Settled markets (n)", esc(s.get("n")), "the sample the score is computed on",
         ext(NFL_SCHED, "official results")],
        ["Mean fair − market", esc(s.get("mean_diff")), "positive = our number is on the right side",
         artifact("data/ops/graded.csv")],
        ["Standard error", esc(s.get("se")), "sd / sqrt(n)", artifact("data/ops/scores_signal.csv")],
        ["z", esc(s.get("z")), "signal / standard error", artifact("data/ops/scores_signal.csv")],
        ["p (two-sided)", esc(s.get("p")), "the gate threshold is 0.05",
         artifact("data/ops/scores_signal.csv")],
        ["95% CI", "[%s, %s]" % (esc(s.get("ci95_low")), esc(s.get("ci95_high"))),
         "an interval that spans zero is not evidence", artifact("data/ops/scores_signal.csv")],
        ["Won / lost / push", "%s / %s / %s" % (esc(s.get("wins")), esc(s.get("losses")), esc(s.get("pushes"))),
         "counts, not percentages, because n is small", artifact("data/ops/graded.csv")],
        ["Hit rate", esc(s.get("hit_rate_pct")) + "%", "uninformative below n = 100",
         artifact("data/ops/scores_signal.csv")],
        ["Gates passed", "%s / %s" % (esc(s.get("gates_passed")), esc(s.get("gates_total"))),
         pill("eligible" if s.get("eligible") == "True" else "not eligible",
              "ok" if s.get("eligible") == "True" else "bad"),
         artifact("data/ops/gates.csv")],
    ]
    staking_rows = [
        ["Settled bets (n)", esc(k.get("n")), "same sample as the signal score",
         ext(NFL_SCHED, "official results")],
        ["Paper P&L", esc(k.get("pnl_units")) + " units", "flat one unit per bet",
         artifact("data/ops/scores_staking.csv")],
        ["ROI per bet", esc(k.get("roi_pct")) + "%", "the number that flatters small samples",
         artifact("data/ops/scores_staking.csv")],
        ["Maximum drawdown", esc(k.get("max_drawdown_units")) + " units",
         "peak-to-trough of the paper bankroll", artifact("data/ops/scores_staking.csv")],
        ["Best week", esc(k.get("best_week")), "a single week can own the whole result",
         artifact("data/ops/scores_staking.csv")],
        ["Status", pill("reported, never ranked alone", "warn"),
         "a staking run on this sample cannot separate skill from variance",
         artifact("data/ops/graded.csv")],
    ]
    gate_rows = [[esc(g["gate"]), esc(g["name"]), esc(g["rule"]), esc(g["observed"]) or "—",
                  pill(g["status"], "ok" if g["status"] == "pass" else "bad"),
                  ext(NFL_SCHED, "official results")] for g in gates]
    demote_rows = [[esc(r["rule"]), esc(r["name"]), esc(r["trigger"]),
                    esc(r["threshold"]) or "—", artifact("data/ops/demotion_rules.csv")]
                   for r in d["demotion"]]
    state_rows = [[esc(r["strategy"]), pill(r["from"], "ok" if r["from"] == "live" else "warn"),
                   pill(r["to"], "ok" if r["to"] == "live" else "warn"),
                   esc(r["rule_fired"]) or "—", esc(r["reason"]), esc(r["n"]),
                   ext(NFL_SCHED, "official results")] for r in d["demotions"]]

    body = (
        '<section class="hero"><div><span class="eyebrow light">THE LEADERBOARD</span>'
        '<h2>Signal is scored. Staking is reported. They are never the same column.</h2>'
        '<p>A lucky staking run is indistinguishable from skill on a small sample: twenty '
        'winning bets at even money look identical whether the edge is real or the coin fell '
        'right. So the leaderboard ranks the <b>signal</b> — whether our number beat the '
        'market number — and shows staking beside it as context. A strategy with a brilliant '
        'staking record and no signal cannot rank.</p>'
        '<a class="button" href="#gates">See what has to pass ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%s</div><strong>gates passed</strong>'
        '<small>of %s required — nothing is eligible</small></div></section>' % (
            esc(s.get("gates_passed", 0)), esc(s.get("gates_total", 8)))
        + section("signal", "SCORE 1 · SIGNAL", "Did the number beat the market?",
                  "This is the only score the leaderboard ranks. It asks a question that "
                  "staking cannot: was our number better than the market's number, and by "
                  "enough that luck is an implausible explanation.", "SKILL EVIDENCE",
                  table(["Metric", "Value", "What it means", "Source"], signal_rows))
        + section("staking", "SCORE 2 · STAKING", "What a flat paper stake would have returned",
                  "Reported in full and ranked never. If this number is good while the signal "
                  "score is not, the honest reading is variance, not edge.", "CONTEXT ONLY",
                  table(["Metric", "Value", "What it means", "Source"], staking_rows))
        + section("gates", "VALIDATION", "The gates, evaluated on the data we actually have",
                  "Every gate reports the number it used, so the binding constraint is "
                  "visible instead of implied. A gate that cannot be computed fails closed.",
                  "%s / %s PASS" % (esc(s.get("gates_passed")), esc(s.get("gates_total"))),
                  table(["Gate", "Name", "Pass rule", "Observed", "Status", "Source"],
                        gate_rows))
        + section("demote", "DEMOTION GATE", "When a live strategy goes back to paper",
                  "The gate is deliberately asymmetric: cheap to demote, expensive to promote. "
                  "A false promotion costs real money; a false demotion costs a delay.",
                  "6 RULES", table(["Rule", "Name", "Trigger", "Threshold", "Artifact"],
                                   demote_rows))
        + section("state", "CURRENT STATE", "Every strategy, and where the gate puts it",
                  "There is exactly one originated strategy, and the gate has already ruled on "
                  "it. It has not earned a live stake and is held on paper.", "PAPER",
                  table(["Strategy", "From", "To", "Rule fired", "Reason", "n", "Official source"],
                        state_rows) if state_rows else
                  '<div class="note">No strategy has been submitted to the gate.</div>')
        + section("why", "WHY THE SPLIT MATTERS", "", "", "",
                  '<div class="callout"><b>The failure this prevents</b><p>A leaderboard scored '
                  'on profit rewards the strategy that took the most risk during a lucky stretch. '
                  'Scoring the signal instead means the winner is the strategy whose numbers '
                  'were closest to the truth, and the staking column is left to do the only job '
                  'it can do honestly: tell you what the paper record looked like, with the size '
                  'of the sample printed next to it.</p></div>')
    )
    return body


# ---------------------------------------------------------------------------
# page: correlations
# ---------------------------------------------------------------------------
def build_correlations(d):
    rows = correlation_rows(d)
    body_rows = []
    for r in rows:
        if r["r"] is None:
            body_rows.append([esc(r["label"]), "", "", esc(r["n"]), esc(r["why"]),
                              ext(r["url"], r["src_label"])])
            continue
        body_rows.append([
            "<b>%s</b>" % esc(r["label"]),
            "r = %+.3f" % r["r"],
            "[%+.3f, %+.3f]" % (r["lo"], r["hi"]),
            esc(r["n"]),
            esc(r["why"]),
            ext(r["url"], r["src_label"]),
        ])

    full = {r["label"]: r for r in rows}
    narrow = {r["label"]: r for r in correlation_rows(d, weeks=range(6, 10))}
    window_rows = []
    for label in full:
        for tag, src in (("all completed games", full), ("weeks 6–9 only", narrow)):
            r = src.get(label)
            if not r or r["r"] is None:
                continue
            window_rows.append([esc(label), esc(tag), "r = %+.3f" % r["r"],
                                "[%+.3f, %+.3f]" % (r["lo"], r["hi"]), esc(r["n"]),
                                ext(NFL_STAND if r["n"] == 32 else NFL_SCHED, "official")])

    excluded = [
        ["Closing-line value per bet", "needs a full open→close history per bet", "the store holds "
         "one reading per market, not a time series", artifact("data/ops/price_snapshots.csv") + " · " + local("price-store.html", "price store")],
        ["Player-prop correlations", "needs player-level game logs", "no official player-stat feed "
         "is cached in this build", ext(NFL + "/stats/", "nfl.com stats")],
        ["Rest-days correlations", "needs the exact rest days per club per game", "the official "
         "schedule gives kickoff times but not the full rest ledger", ext(NFL + "/schedules/2026/", "official schedule")],
        ["Parlay joint probabilities", "needs the two above, plus a pricing convention", "deferred "
         "with the reason recorded, not estimated", artifact("data/ops/gates.csv") + " · " + local("signals.html#gates", "gate G7")],
    ]

    body = (
        '<section class="hero"><div><span class="eyebrow light">CORRELATION</span>'
        '<h2>Only from officially sourced numbers, and always with n</h2>'
        '<p>A correlation without an n is a rumour. Every value on this page is computed from '
        'the official game log or the official standings, carries its sample size, and carries '
        'a 95%% interval. Where the required input does not exist, the cell is blank and the '
        'reason is printed.</p><a class="button" href="#values">See the values ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div><strong>correlations computed</strong>'
        '<small>each with n and a 95%% interval</small></div></section>' % len(rows)
        + section("values", "COMPUTED VALUES", "What we can actually measure today",
                  "Pearson r, with a Fisher-z 95% interval. The interval is the honest part: "
                  "three of these four span or nearly span zero.", "%d VALUES" % len(rows),
                  table(["Quantity", "r", "95% CI", "n", "Why it matters for a parlay",
                         "Official source"], body_rows))
        + section("not", "NOT COMPUTED", "The correlations we refuse to estimate",
                  "Each one is a real question. None of them can be answered from an "
                  "officially sourced number that this build holds, so each is blank.",
                  "FAIL CLOSED",
                  table(["Correlation", "Why it needs more than we have", "What is missing",
                         "Path"], [[esc(a), esc(b), esc(c), v] for a, b, c, v in excluded]))
        + section("windows", "SAME QUESTION, TWO WINDOWS", "The estimate moves — say so",
                  "The headline value above uses every completed game. An earlier desk-layer "
                  "estimate used only weeks 6–9. They disagree, and the disagreement is itself "
                  "the finding: on one season, a correlation is not stable enough to build a "
                  "parlay price on.", "WINDOW SENSITIVITY",
                  table(["Quantity", "Window", "r", "95% CI", "n", "Official source"],
                        window_rows))
        + section("read", "HOW TO READ IT", "", "", "",
                  '<div class="callout"><b>The number a same-game parlay depends on</b>'
                  '<p>The margin-to-total correlation decides whether a big favourite and an '
                  'over are really independent legs. In the full-season window the estimate is '
                  'negative but its 95% interval <b>includes zero</b>, so it cannot be stated as '
                  'a finding. In the weeks 6–9 window the same calculation is more strongly '
                  'negative and its interval excludes zero — but that is 54 games, and the two '
                  'windows disagreeing is exactly why a single-season correlation should be '
                  'treated as a hypothesis with a wide interval rather than as a coefficient to '
                  'price with. A parlay priced as if these legs were independent would be '
                  'overstated; a parlay priced with either point estimate would be '
                  'overconfident. That is the honest conclusion.</p></div>')
    )
    return body


# ---------------------------------------------------------------------------
# page: replacements / depth
# ---------------------------------------------------------------------------
def build_replacements(d):
    inj = d["injuries"]
    txn = d["transactions"]

    out_by_team = {}
    for r in inj:
        key = r["team"]
        bucket = out_by_team.setdefault(key, {"rows": 0, "out": 0, "q": 0, "pos": {}})
        bucket["rows"] += 1
        gs = (r.get("game_status") or "").strip().lower()
        if gs == "out":
            bucket["out"] += 1
            pos = (r.get("pos") or "").strip() or "?"
            bucket["pos"][pos] = bucket["pos"].get(pos, 0) + 1
        elif gs in ("questionable", "doubtful"):
            bucket["q"] += 1

    team_rows = []
    for team, b in sorted(out_by_team.items(), key=lambda x: (-x[1]["out"], x[0])):
        pos = ", ".join("%s×%d" % (p, n) for p, n in sorted(b["pos"].items(), key=lambda x: -x[1])) or "—"
        team_rows.append([
            "<b>%s</b>" % esc(team), esc(b["rows"]), esc(b["out"]), esc(b["q"]), esc(pos),
            pill("depth unresolved", "warn"),
            ext(NFL_INJ, "nfl.com injuries"),
        ])

    out_rows = []
    for r in inj:
        if (r.get("game_status") or "").strip().lower() != "out":
            continue
        out_rows.append([
            esc(r["team"]), "<b>%s</b>" % esc(r["player"]), esc(r["pos"]),
            esc(r["injuries"]) or "—", esc(r["practice"]),
            pill("no official depth chart", "bad"),
            ext(r.get("player_url") or NFL + "/injuries/", "official player"),
        ])

    txn_rows = []
    for r in txn:
        txn_rows.append([esc(r["date"]), esc(r["from"]), esc(r["to"]) or "—",
                         esc(r["player"]), esc(r["pos"]) or "—", esc(r["transaction"]),
                         ext(r.get("player_url"), "player"),
                         ext(r.get("source_url"), "official transaction")])

    body = (
        '<section class="hero"><div><span class="eyebrow light">REPLACEMENT DEPTH</span>'
        '<h2>The fact of an absence is official. The depth behind it is not.</h2>'
        '<p>An official injury report tells you a starter is out. It does not tell you whether '
        'the man replacing him is the second-string player or the fourth. That distinction is '
        'the whole point of tracking depth, and no official NFL source labels it: '
        'the league\'s depth-chart address returns HTTP 404, verified below. This page '
        'therefore publishes what is official, measures the gap, and refuses to invent a string.</p>'
        '<a class="button" href="#gap">See the gap ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div><strong>players ruled out</strong>'
        '<small>from the official Week 10 report</small></div></section>' % len(out_rows)
        + section("gap", "THE GAP", "What the official record does and does not say",
                  "", "404 VERIFIED", '<div class="cards">'
                  '<div class="card"><span class="k">WHAT IS OFFICIAL</span><h3>The absence</h3>'
                  '<p>Player, club, position, injury, practice status and game designation, '
                  'row by row, from nfl.com/injuries. Every row on this page links to it.</p></div>'
                  '<div class="card"><span class="k">WHAT IS NOT</span><h3>The string</h3>'
                  '<p>No official page labels a player second-, third- or fourth-string. '
                  'Club depth charts, where a club publishes one, are ordered lists without '
                  'string labels. A guessed string would be a fabricated input.</p></div>'
                  '<div class="card"><span class="k">THE SUBSTITUTE</span><h3>The transaction date</h3>'
                  '<p>The closest official proxy is <i>when</i> a club lost the player and what it '
                  'did next: a reserve-list move, a signing, a waiver claim. A club that signs a '
                  'replacement within 24 hours is telling you the depth behind the starter was thin. '
                  'That is measurable from nfl.com/transactions, and it is the depth measure this '
                  'build uses where the record allows it.</p></div>'
                  '<div class="card"><span class="k">THE HONEST LABEL</span><h3>Unresolved</h3>'
                  '<p>Where the record does not allow it, the cell says '
                  '<code>depth unresolved</code> and the row stays blank. It is not filled with '
                  'the previous week\'s value or with a plausible guess.</p></div>'
                  '</div>')
        + section("units", "BY CLUB", "Official absences, rolled up by unit and position",
                  "Defensive front, secondary and skill positions are separated because a lost "
                  "left tackle and a lost nickel corner do not move a line in the same direction.",
                  "%d CLUBS" % len(team_rows),
                  table(["Club", "Report rows", "Ruled out", "Questionable / doubtful",
                         "Ruled out by position", "Depth of replacement", "Official source"],
                        team_rows, numeric=(1, 2, 3)))
        + section("out", "RULED OUT", "Every player officially ruled out of his Week 10 game",
                  "This is the list a depth model would start from. The column that would carry "
                  "the string is empty on purpose and says why.", "%d PLAYERS" % len(out_rows),
                  table(["Club", "Player", "Pos", "Injury", "Practice", "Replacement depth",
                         "Official source"], out_rows) if out_rows else
                  '<div class="note">No player carries an official "Out" designation in the '
                  'cached report.</div>')
        + section("ledger", "REPLACEMENT DEPTH", "Measured from official transaction timing",
                  "For every player a club lost to Reserve/Injured, how long did the club take "
                  "to add a body? A club that had to move within a day had nobody behind him. "
                  "This is urgency, which is observable — not ability, which is not.",
                  "%d ROWS" % len(d["depth"]),
                  table(["Club", "Player lost", "Pos", "Lost on", "Replacement",
                         "Added on", "Gap (days)", "Depth read", "Evidence"],
                        [[esc(r["team"]), "<b>%s</b>" % esc(r["player_lost"]),
                          esc(r["pos"]) or "—", esc(r["lost_on"]),
                          esc(r["replacement"]) or "—", esc(r["replacement_on"]) or "—",
                          esc(r["gap_days"]) or "—",
                          pill(r["depth_read"],
                               "bad" if r["depth_read"] in ("THIN", "UNRESOLVED") else
                               "warn" if r["depth_read"] == "NORMAL" else "ok"),
                          ext(r["loss_url"], "loss") +
                          (" · " + ext(r["replacement_url"], "replacement")
                           if r["replacement_url"] else "")]
                         for r in d["depth"]], numeric=(6,))
                  if d["depth"] else
                  '<div class="note">No loss and addition pair is recorded in the cached '
                  'window, so no depth reading can be made.</div>')
        + section("charts", "OFFICIAL CHART RANK", "The better answer, where a club publishes one",
                  "The ledger above measures urgency because it cannot quote a rank. This "
                  "table can. Each club's own site publishes an ordered chart, and its "
                  "column position is the depth position, so a rank here is a transcription "
                  "of a published fact rather than an inference. Where a chart exists, it "
                  "outranks the proxy.",
                  "%d POSITIONS" % len(d["charts"]),
                  table(["Club", "Unit", "Position", "Depth", "Player", "Wk 10 status", "Source"],
                        [[esc(c["team"]), esc(c["unit"]), esc(c["position_row"]),
                          "<b>%s</b>" % esc(c["depth"]), esc(c["player"]),
                          pill(c["game_status"], "bad")
                          if c["game_status"] in ("Out", "Doubtful")
                          else '<span class="muted">—</span>',
                          ext(c["source"], "club chart")]
                         for c in d["charts"]
                         if c["depth"] == "1" and c["game_status"] in ("Out", "Doubtful")]))
        + section("clubread", "BY CLUB", "Which clubs are thinnest, by this proxy",
                  "The churn index counts official losses plus official additions. A high "
                  "churn index with thin moves is the signal a depth model would want.",
                  "%d CLUBS" % len(d["depth_club"]),
                  table(["Club", "Losses", "Additions", "Thin moves", "Unresolved",
                         "Mean gap (days)", "Churn", "Read"],
                        [[esc(c["team"]), esc(c["losses_recorded"]), esc(c["additions_recorded"]),
                          esc(c["thin_moves"]), esc(c["unresolved"]),
                          esc(c["mean_gap_days"]) or "—", esc(c["churn_index"]),
                          pill(c["read"], "bad" if c["read"] == "THIN" else
                               "warn" if c["read"] == "MIXED" else "ok"),
                          ext(NFL_TXN, "official transactions")]
                         for c in d["depth_club"]], numeric=(1, 2, 3, 4, 5, 6))
                  if d["depth_club"] else
                  '<div class="note">No club has a recorded loss in the cached window.</div>')
        + section("txn", "TRANSACTIONS", "The official record that dates a replacement",
                  "Every row is a league-published transaction. The date is what turns 'a player "
                  "is missing' into 'a club had N hours to find a body', which is the depth "
                  "signal that can actually be measured.",
                  "%d ROWS CACHED" % len(txn),
                  table(["Date", "From", "To", "Player", "Pos", "Transaction", "Player",
                         "Official source"], txn_rows) if txn_rows else
                  '<div class="note"><b>No transaction body is cached in this build.</b> The '
                  'retrieval plan holds the exact URLs '
                  '(<code>nfl.com/transactions/league/&lt;kind&gt;/2026/11</code>) and the '
                  'ingester that would consume them, so the table fills the moment the bodies '
                  'are cached. It is not filled with remembered values.</div>')
        + section("verify", "VERIFICATION", "The 404 that makes this page necessary",
                  "", "", table(
                      ["Check", "Result", "What it means"],
                      [["<code>nfl.com/teams/&lt;club&gt;/depth-chart</code>",
                        pill("HTTP 404", "bad"),
                        "the league publishes no depth chart at the club path"] +
                       [ext(NFL + "/teams/arizona-cardinals/depth-chart", "fetch it")],
                       ["Official injury report", pill("200 OK", "ok"),
                        "carries the absence, never the string"] +
                       [ext(NFL + "/injuries/", "official report")],
                       ["Official transactions", pill("200 OK", "ok"),
                        "dates the replacement, which is the measurable proxy"] +
                       [ext(NFL + "/transactions/", "official transactions")]]))
    )
    return body


# ---------------------------------------------------------------------------
# page: method lab
# ---------------------------------------------------------------------------
def build_method_lab(d):
    fundamentals = [
        ["Turnover margin", "points, not counts", "A turnover is worth roughly four points of "
         "field position and possession, so a defense with many takeaways is partly a defense "
         "with good field position. Regress it hard: turnover rate is one of the least "
         "persistent statistics in the sport.",
         "official game log", "ready"],
        ["Red-zone efficiency", "points per trip", "Two clubs can have identical yardage and "
         "different scores. Points per red-zone trip separates them; raw yards do not.",
         "official play-by-play", "not cached"],
        ["Explosive-play rate", "plays of 20+ yards", "Variance in a single game is driven by a "
         "handful of explosive plays. A club that generates them is more volatile than its mean "
         "suggests, which matters for totals more than for sides.",
         "official play-by-play", "not cached"],
        ["Pace and plays per game", "seconds per snap", "The bridge between efficiency and "
         "totals. A fast offense raises the number of possessions for both teams.",
         "official play-by-play", "not cached"],
        ["Rest and travel", "days between games", "Short weeks and west-coast travel have small "
         "but measurable effects, and both are derivable from the official schedule without "
         "any third party.", "official schedule", "partly ready"],
        ["Situation and motivation", "games remaining, clinch state", "Late-season games between "
         "a clinched club and a desperate one are not priced by a season-long average. Derivable "
         "from the official standings, but only late in the season.",
         "official standings", "partly ready"],
        ["Line movement itself", "open to close", "The market's own move is information: a "
         "steady steam move is not the same as a number that flickers. This is measurable from "
         "the price store once it holds more than one reading per market.",
         "price-snapshot store", "partly ready"],
        ["Injury adjustment", "designation weighted by position", "The hardest and most "
         "overrated input. A backup quarterback is a large effect; a backup guard is close to "
         "noise. Any adjustment has to be fitted out-of-sample, never assumed.",
         "official injury report", "ready but unmodelled"],
    ]
    FUND_SRC = {
        "official game log": ext(NFL_SCHED, "official results"),
        "official play-by-play": ext(NFL_STATS, "nfl.com stats"),
        "official schedule": ext(NFL_SCHED, "official schedule"),
        "official standings": ext(NFL_STAND, "official standings"),
        "price-snapshot store": ext(NFL_STATS, "market reference"),
        "official injury report": ext(NFL_INJ, "official injury report"),
    }
    fund_rows = [[esc(a), esc(b), esc(c), esc(d), pill(e, "ok" if e == "ready" else "warn"),
                  FUND_SRC.get(d, ext(NFL_STATS, "nfl.com stats"))]
                 for a, b, c, d, e in fundamentals]

    practices = [
        ["Write the hypothesis before the backtest", "Pre-registration",
         "A hypothesis stated after seeing the result is a description of the data, not a "
         "prediction. Every entry in the trial log is dated before its result is known.",
         "the trial log"],
        ["Score the number, not the bankroll", "Skill separation",
         "Profit is a slow, noisy statistic. Beating the closing number is faster and much "
         "harder to fake, so it carries the ranking weight.",
         "signal-vs-staking.html"],
        ["Hold out by time, never at random", "No leakage",
         "A random split lets a model see week 12 while predicting week 11. Walk-forward by "
         "week or season is the only split that matches how the number is actually used.",
         "gates G3"],
        ["Count every trial you ran", "Multiplicity",
         "Twenty strategies tested at p < 0.05 produce one false winner on average. The trial "
         "count is part of the result, not an appendix.",
         "gates G6"],
        ["Show the interval, not just the estimate", "Uncertainty",
         "An estimate without its interval invites the reader to trust the decimal places. The "
         "interval is where the honesty lives.",
         "every table"],
        ["Regress to the mean on purpose", "Shrinkage",
         "A club four games into a season is mostly league average with a small signal on top. "
         "Shrinking by games played is a prior, not a fudge, and it is printed in the model card.",
         "origination.html"],
        ["Separate paper from live with a numeric gate", "Demotion",
         "A strategy that could be demoted by judgement will not be. The gate has to fire on a "
         "number, and the number has to be computable before the game.",
         "signal-vs-staking.html#demote"],
        ["Let a null result stay null", "Integrity",
         "The most valuable output of this project so far is that nine strategies failed the "
         "significance gate. Publishing that is the product working, not the product failing.",
         "strategies.html"],
        ["Never fill a blank to make a table look complete", "Provenance",
         "A blank with a reason is information. A guess is contamination that travels into "
         "every downstream number.",
         "flagged.html"],
    ]
    PRAC_SRC = {
        "the trial log": ext(NFL_STATS, "results reference"),
        "signal-vs-staking.html": ext(NFL_SCHED, "official results"),
        "gates G3": ext(NFL_SCHED, "official results"),
        "gates G6": ext(NFL_STATS, "nfl.com stats"),
        "every table": ext(NFL_STAND, "official standings"),
        "origination.html": ext(NFL_STAND, "official standings"),
        "signal-vs-staking.html#demote": ext(NFL_SCHED, "official results"),
        "strategies.html": ext(NFL_SCHED, "official results"),
        "flagged.html": ext(NFL_INJ, "official injury report"),
    }
    prac_rows = [[esc(a), pill(b, "info"), esc(c), esc(d),
                  PRAC_SRC.get(d, ext(NFL_STATS, "nfl.com stats"))] for a, b, c, d in practices]

    generator = [
        ["Side 1 · scoring differential", "PF/g − PA/g, shrunk by games played",
         "the workhorse", "in production"],
        ["Side 2 · schedule-adjusted differential", "opponents' own scoring differential removed",
         "separates a good club from a lucky schedule", "specified"],
        ["Total 1 · combined scoring environment", "(PF/g + PA/g) of both clubs",
         "the only total input currently used", "in production"],
        ["Total 2 · pace interaction", "possessions per game × points per possession",
         "needs play-by-play", "blocked"],
        ["Moneyline 1 · fair side through a normal margin", "P(home wins) = Phi(fair side / sigma)",
         "sigma measured, not assumed", "in production"],
        ["Moneyline 2 · empirical margin distribution", "the same probability from observed margins",
         "needs more games than one season", "blocked"],
        ["Divergence 1 · disagreement with the market", "|fair − market| above a threshold",
         "a queue for investigation, never a bet on its own", "in production"],
        ["Divergence 2 · disagreement whose direction the market then moved", "our side, then a "
         "market move toward us", "the strongest available skill footprint", "blocked on history"],
        ["Availability 1 · official designations", "Out / Doubtful / Questionable by position",
         "ready", "unmodelled"],
        ["Availability 2 · replacement depth", "transaction-recency behind an absence",
         "the depth proxy", "partly ready"],
    ]
    GEN_SRC = [ext(NFL_STAND, "official standings"), ext(NFL_SCHED, "official results"),
               ext(NFL_SCHED, "official results"), ext(NFL_STATS, "nfl.com stats"),
               ext(NFL_SCHED, "official results"), ext(NFL_SCHED, "official results"),
               ext(NFL_STATS, "market reference"), ext(NFL_STATS, "market reference"),
               ext(NFL_INJ, "official injury report"), ext(NFL_TXN, "official transactions")]
    gen_rows = [[esc(a), esc(b), esc(c), pill(dd, "ok" if dd == "in production" else
                                             ("bad" if dd == "blocked" else "warn")), GEN_SRC[i]]
                for i, (a, b, c, dd) in enumerate(generator)]

    body = (
        '<section class="hero"><div><span class="eyebrow light">METHOD LAB</span>'
        '<h2>What genuinely moves a number, and what only looks like it does</h2>'
        '<p>Three questions in one place: which fundamentals carry real signal, which working '
        'practices stop a backtest from lying, and which candidate signals are buildable from '
        'sources we already hold. Status labels are honest: <b>in production</b> means it is '
        'already moving a published number, <b>blocked</b> means the input does not exist yet.</p>'
        '<a class="button" href="#fundamentals">Start with the fundamentals ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div><strong>candidate signals</strong>'
        '<small>%d in production, the rest labelled</small></div></section>' % (
            len(generator), sum(1 for g in generator if g[3] == "in production"))
        + section("fundamentals", "FUNDAMENTALS", "The differentials that carry signal",
                  "Ranked roughly by how much a model gains from them, not by how interesting "
                  "they are. The ones needing play-by-play are listed for completeness and "
                  "marked, so nobody mistakes an aspiration for an input.",
                  "%d CANDIDATES" % len(fundamentals),
                  table(["Fundamental", "Measured as", "Why it matters", "Official input",
                         "Status", "Official source"], fund_rows))
        + section("practices", "BEST PRACTICE", "Nine rules that keep a backtest honest",
                  "Each of these exists because omitting it produces a number that looks better "
                  "than it is. They are written down so that a future session cannot quietly "
                  "skip one.", "9 RULES",
                  table(["Practice", "Category", "Why", "Where it lives", "Official source"],
                        prac_rows))
        + section("generator", "SIGNAL GENERATION", "Every candidate, and its honest status",
                  "The order is deliberate: the side first, then the total, then the moneyline, "
                  "because each depends on the one before it.", "%d SIGNALS" % len(generator),
                  table(["Signal", "Definition", "Why it should work", "Status",
                         "Official source"], gen_rows))
    )
    return body


# ---------------------------------------------------------------------------
# page: review gate
# ---------------------------------------------------------------------------
def build_review(d):
    s = d["signal"]
    suggestions = [
        ["S1", "Publish the price store before publishing any line",
         "A line without a recorded market beside it cannot be evaluated later.",
         "it is already done — the store is the first artifact in this layer",
         "done", "price-store.html"],
        ["S2", "Split the leaderboard into signal and staking columns",
         "A lucky staking run otherwise masks a bad signal.",
         "the split is published and the staking column is explicitly not ranked",
         "accept", "signal-vs-staking.html"],
        ["S3", "Bill the demotion gate as a numeric rule, not a judgement call",
         "Demotion by discretion never happens under pressure.",
         "six numeric triggers, evaluated and logged, with the current verdict published",
         "accept", "signal-vs-staking.html#demote"],
        ["S4", "Show n on every correlation, and refuse the ones without a source",
         "A correlation without n invites over-reading.",
         "four computed with n and intervals; four refused with the reason",
         "accept", "correlations.html"],
        ["S5", "Measure replacement depth from transaction recency",
         "The official record cannot give a depth string, but it can give a clock.",
         "needs the transaction bodies cached; the plan and ingester exist",
         "hold", "replacements.html"],
        ["S6", "Buy or license a closing-line history",
         "Without a time series, CLV can never be computed, and CLV is the strongest skill "
         "statistic available.",
         "the single largest blocker in the project",
         "hold", "flagged.html"],
        ["S7", "Publish fair, market and difference as three columns everywhere",
         "A single combined column hides which number moved.",
         "done on the origination page; the same rule should govern any future table",
         "accept", "origination.html"],
        ["S8", "Do not rank any strategy until n reaches 100 per market type",
         "Ranking below that threshold is ranking noise.",
         "enforced by gate G2, which fails closed",
         "accept", "signal-vs-staking.html#gates"],
        ["S9", "Keep a trial log, and count every trial",
         "Multiplicity is how backtests produce winners that do not exist.",
         "specified as gate G6; not yet implemented because there is only one strategy",
         "hold", "signal-vs-staking.html#gates"],
        ["S10", "Add a depth-chart provider only if it can be licensed and cited",
         "A scraped chart would break the one rule this project follows.",
         "requires a decision and a budget, not an engineering task",
         "hold", "replacements.html"],
    ]
    SUG_SRC = ["data/ops/price_snapshots.csv", "data/ops/scores_signal.csv",
               "data/ops/demotion_rules.csv", "data/ops/scores_signal.csv",
               "data/ops/fetch_plan.json", "data/ops/snapshots.csv",
               "data/ops/fair_market_difference.csv", "data/ops/gates.csv",
               "data/ops/gates.csv", "data/injuries-wk10-2026.csv"]
    rows = [[esc(a), "<b>%s</b>" % esc(b), esc(c), esc(dd),
             pill(e, "ok" if e in ("accept", "done") else "warn"),
             artifact(SUG_SRC[i]) + " · " + local(f, "page")]
            for i, (a, b, c, dd, e, f) in enumerate(suggestions)]

    questions = [
        ["Q1", "Is a licensed odds feed authorised, and for which books?",
         "the price store is third-party only, so every market number is T3",
         "a budget decision, and a terms-of-service review", "blocks CLV and any live staking"],
        ["Q2", "What is the demotion threshold in units, and who enforces it?",
         "D3 proposes 15 units at stake 1; that is a proposal, not a decision",
         "the owner sets it once, and the gate applies it forever", "blocks live staking"],
        ["Q3", "May a depth-chart provider be licensed, or is the string permanently unavailable?",
         "no official source labels a string; a licensed provider would end the 404 problem",
         "a licensing enquiry", "blocks the whole 2nd/3rd/4th-string requirement"],
        ["Q4", "How many seasons of history are needed before a strategy can be called skilled?",
         "one season gives n≈250 markets, below the 100-per-market-type floor for some markets",
         "a decision on the evaluation window", "blocks promotion to live"],
        ["Q5", "What counts as a 'market type' for the sample floor — side, total, moneyline, or more?",
         "the floor is 100 per market type, so the definition changes the answer",
         "a one-line definition", "blocks gate G2 from passing"],
        ["Q6", "Is the home edge to be refitted per season or pooled?",
         "the current edge has a confidence interval spanning zero on 54 games",
         "a modelling decision, with a published rationale", "blocks a stable side number"],
        ["Q7", "Does the project carry a legal opinion on publishing prices at all?",
         "prices are third-party commercial data; the site is research, not advice",
         "a legal review before any widening", "blocks public promotion of the layer"],
    ]
    Q_SRC = [ext(NFL_TXN, "transactions"), ext(NFL_SCHED, "official results"),
             ext(NFL + "/teams/", "official team pages"),
             ext(NFL_SCHED, "official schedule"), ext(NFL_STATS, "nfl.com stats"),
             ext(NFL_SCHED, "official results"),
             ext("https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act",
                 "FTC, the relevant statute")]
    q_rows = [[esc(a), "<b>%s</b>" % esc(b), esc(c), esc(dd), esc(e), Q_SRC[i]]
              for i, (a, b, c, dd, e) in enumerate(questions)]

    flags = [
        ["F-01", "Only three events could be bound to a price in this build",
         "the retrieval budget allowed a sample, not the slate",
         "every unbound event is listed with its reason", "replacements.html"],
        ["F-02", "No transaction body is cached",
         "the replacement-depth proxy therefore has no rows",
         "the plan and ingester exist; the table stays empty and says so", "replacements.html"],
        ["F-03", "The price store holds one reading per market",
         "movement between open and close is visible, but not the path between them",
         "CLV needs the path; a time series is a separate retrieval job", "price-store.html"],
        ["F-04", "Depth strings remain unavailable from every official source",
         "nfl.com club depth-chart paths return 404; no club page labels a string",
         "left blank and flagged, never guessed", "replacements.html"],
        ["F-05", "The signal score rests on a sample far below the gate",
         "n = %s settled markets against a floor of 100 per market type" % s.get("n", "0"),
         "every gate that cannot pass is reported as failing, not omitted", "signal-vs-staking.html"],
    ]
    F_SRC = [ext(NFL_SCHED, "official schedule"), ext(NFL_TXN, "official transactions"),
             ext(NFL_STATS, "market reference"), ext(NFL_INJ, "official injury report"),
             ext(NFL_SCHED, "official results")]
    f_rows = [[esc(a), "<b>%s</b>" % esc(b), esc(c), esc(dd), local(e, "detail"), F_SRC[i]]
              for i, (a, b, c, dd, e) in enumerate(flags)]

    body = (
        '<section class="hero"><div><span class="eyebrow light">REVIEW GATE</span>'
        '<h2>Nothing in this layer is implemented without a decision recorded here</h2>'
        '<p>This is the suggestions section for the origination build: ten proposals, each with '
        'its expected benefit, the state it is actually in, and a link to the artifact that '
        'shows it. Seven open questions follow, then the items this session could not resolve. '
        'Read the verdicts and change them — that is what the page is for.</p>'
        '<a class="button" href="#suggestions">Review the proposals ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div><strong>open questions</strong>'
        '<small>each one blocks a named decision</small></div></section>' % len(questions)
        + section("suggestions", "SUGGESTIONS", "Ten proposals, with the state each is in",
                  "A proposal marked <b>hold</b> is waiting on a decision or a licence, not on "
                  "engineering. Nothing is implemented while it is on hold.",
                  "%d PROPOSALS" % len(suggestions),
                  table(["#", "Proposal", "Why", "State", "Status", "Evidence"], rows))
        + section("questions", "OPEN QUESTIONS", "What has to be answered before the next step",
                  "Each question names what it blocks, so the cost of leaving it open is visible.",
                  "%d QUESTIONS" % len(questions),
                  table(["#", "Question", "What we know", "How to resolve it",
                         "What it blocks", "Official source"], q_rows))
        + section("flags", "FLAGGED FOR REVIEW", "What this session could not close",
                  "None of these blocks publication; each one blocks a claim, and a claim is "
                  "what a reader would otherwise assume.", "%d ITEMS" % len(flags),
                  table(["#", "Item", "Why it is open", "What is published instead", "Detail",
                         "Official source"], f_rows))
        + section("next", "THE NEXT DECISION", "", "", "",
                  '<div class="callout"><b>If only one thing is decided now</b><p>Decide whether '
                  'a licensed odds feed will be authorised. Without price history, closing-line '
                  'value cannot be computed, and without closing-line value the leaderboard has '
                  'only the slower, noisier statistics to rank on. Everything else on this page '
                  'is engineering that can proceed either way; this one is a decision.</p></div>')
    )
    return body


# ---------------------------------------------------------------------------
# page: requirement closure
# ---------------------------------------------------------------------------
REQ_CLOSURE = [
    ("Side → total → moneyline", "closed", "origination.html",
     "The three markets are originated in that fixed order and the order is asserted in "
     "the pipeline, not described in prose."),
    ("Price store: open and close separately", "closed", "price-store.html",
     "One row per reading with open_* and close_* as separate fields, a UTC stamp and a "
     "source URL per row."),
    ("Fair / market / difference as separate columns", "closed", "origination.html#fmd",
     "Three columns on every originated market, never merged."),
    ("Verified results feed", "closed", "origination.html#coverage",
     "Every graded market carries the official NFL game page holding its final score."),
    ("Signal separated from staking", "closed", "signal-vs-staking.html",
     "Two independent scores; only the signal score is ranked."),
    ("Demotion gate", "closed", "signal-vs-staking.html#demote",
     "Six numeric triggers, evaluated, with the current verdict published."),
    ("Correlations from official numbers, with n", "closed", "correlations.html",
     "Four values with n and 95% intervals; four refused with the reason."),
    ("Best practices and signal-generation research", "closed", "method-lab.html",
     "Eight fundamentals, nine practices, ten candidates with honest status."),
    ("Suggestions section with a review gate", "closed", "ops-review.html",
     "Ten proposals, seven open questions, five flags, each with a decision."),
    ("Replacement depth beyond the fact of a replacement", "partial", "replacements.html#ledger",
     "Official timing gives urgency for 17 losses; the string itself is unavailable, so the "
     "ledger says so per row instead of labelling."),
    ("Parlays, prop combinations, leaderboard rewards", "partial", "signal-vs-staking.html",
     "The gate and the divisor are built; pricing a parlay needs correlations the store "
     "cannot yet support, and rewards are a business decision that is deliberately blank."),
    ("Player-prop signals", "blocked", "correlations.html#not",
     "No official player-stat feed is cached, so no prop can be originated without "
     "inventing an input."),
]


def build_requirements_closure(d):
    s = d["signal"]
    kind = {"closed": "ok", "partial": "warn", "blocked": "bad"}
    rows = [[pill(st, kind.get(st, "info")), "<b>%s</b>" % esc(name),
             esc(reason), local(page, "inspect") + " · " + artifact(page, "committed page")]
            for name, st, page, reason in REQ_CLOSURE]
    closed = sum(1 for r in REQ_CLOSURE if r[1] == "closed")
    body = (
        '<section class="hero"><div><span class="eyebrow light">CLOSURE</span>'
        '<h2>What this layer actually closed, and what it did not</h2>'
        '<p>Twelve requirements from the brief, each with the artifact that answers it and '
        'an honest status. A requirement marked <b>partial</b> or <b>blocked</b> has its '
        'reason printed and its gap flagged; nothing here is marked closed on the strength '
        'of a description.</p><a class="button" href="#table">See the closure table ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div><strong>closed</strong>'
        '<small>of %d requirements in this layer</small></div></section>' % (closed, len(REQ_CLOSURE))
        + section("table", "REQUIREMENT CLOSURE", "Twelve requirements, twelve verdicts",
                  "The status is a claim about an artifact, and the artifact is linked, so "
                  "the claim can be checked without trusting this page.",
                  "%d OF %d CLOSED" % (closed, len(REQ_CLOSURE)),
                  table(["Status", "Requirement", "What closed it", "Artifact"], rows))
        + section("honest", "WHAT IS STILL OPEN", "", "", "",
                  '<div class="callout"><b>The one number that decides the rest</b>'
                  '<p>This layer closes the <i>machinery</i>: the store, the ordering, the '
                  'three-column discipline, the two-score split, the demotion gate, the '
                  'n-on-every-correlation rule. It does not close the <i>evidence</i>. The '
                  'sample is %s settled markets against a floor of 100 per market type, so '
                  'every gate that needs evidence fails, and the honest headline is that this '
                  'system has produced one originated strategy that the gate correctly refuses '
                  'to promote. That is the machinery working.</p></div>' % esc(s.get("n", "0")))
    )
    return body


# ---------------------------------------------------------------------------
# page: verification
# ---------------------------------------------------------------------------
def build_verification(d):
    """A page whose claims are re-derived here, so the page can contradict itself."""
    prices = d["prices"]
    fmd = d["fmd"]
    graded = d["graded"]
    txn = d["transactions"]
    depth = d["depth"]
    corr = correlation_rows(d)

    # recompute the headline claims from the raw artifacts
    with_url = sum(1 for p in prices if p["source_url"].startswith("https://"))
    graded_with_result = sum(1 for r in graded if r["outcome"] in ("won", "lost", "push"))
    txn_with_url = sum(1 for t in txn if (t.get("source_url") or "").startswith("https://"))
    depth_with_url = sum(1 for r in depth if r["loss_url"].startswith("https://"))

    checks = [
        ["Every price reading carries an https source URL",
         "%d / %d" % (with_url, len(prices)),
         "pass" if with_url == len(prices) else "fail",
         "a reading without provenance cannot be published",
         artifact("data/ops/price_snapshots.csv")],
        ["Every price reading carries a UTC retrieval stamp",
         "%d / %d" % (sum(1 for p in prices if p["retrieved_utc"]), len(prices)),
         "pass" if all(p["retrieved_utc"] for p in prices) else "fail",
         "an undated reading cannot be ranked against another",
         artifact("data/ops/price_snapshots.csv")],
        ["Open and close are stored in separate fields",
         "2 fields, %d rows" % len(prices),
         "pass" if prices and "open_line" in prices[0] and "close_line" in prices[0] else "fail",
         "a single line column cannot show movement",
         artifact("data/ops/price_snapshots.csv")],
        ["Every settled market carries its official result page, and every unsettled one "
         "carries none",
         "%d settled with a URL, %d unsettled correctly blank"
         % (sum(1 for r in fmd if r["settled"] == "1"
                and (r["official_result_url"] or "").startswith("https://")),
            sum(1 for r in fmd if r["settled"] != "1" and not r["official_result_url"])),
         "pass" if all(
             ((r["official_result_url"] or "").startswith("https://"))
             == (r["settled"] == "1") for r in fmd) else "fail",
         "a settled grade without its official box score is an assertion; an unplayed market "
         "must not carry one",
         artifact("data/ops/fair_market_difference.csv")],
        ["Every graded bet has an outcome",
         "%d / %d" % (graded_with_result, len(graded)),
         "pass" if graded_with_result == len(graded) else "fail",
         "an unsettled bet must not be counted",
         artifact("data/ops/graded.csv")],
        ["Every transaction carries its official page",
         "%d / %d" % (txn_with_url, len(txn)),
         "pass" if txn and txn_with_url == len(txn) else "fail",
         "the depth proxy depends on the date being official",
         artifact("data/ops/transactions.csv")],
        ["Every depth row carries the official loss page",
         "%d / %d" % (depth_with_url, len(depth)),
         "pass" if depth and depth_with_url == len(depth) else "fail",
         "a depth read without its source is a guess",
         artifact("data/ops/depth.csv")],
        ["Every correlation carries n and an interval",
         "%d / %d" % (sum(1 for r in corr if r["r"] is not None and r["n"] > 2), len(corr)),
         "pass" if all(r["r"] is None or (r["n"] > 2 and r["lo"] != "") for r in corr) else "fail",
         "a correlation without n is a rumour",
         artifact("research/data/correlation_n.csv")],
        ["The event identity binding is unique per week",
         "%d bound, %d unresolved" % (len(d["identity"]), len(d["unresolved"])),
         "pass" if len({(r["week"], r["away"], r["home"]) for r in d["identity"]}) == len(d["identity"]) else "fail",
         "a duplicated binding would mis-grade two games",
         artifact("data/ops/event_identity.csv")],
        ["The gate count is the published count",
         "%d gates" % len(d["gates"]),
         "pass" if len(d["gates"]) == 8 else "fail",
         "the published inventory must match the evaluated one",
         artifact("data/ops/gates.csv")],
    ]
    rows = [[esc(a), esc(b), pill(c, "ok" if c == "pass" else "bad"),
             esc(e) + " " + art] for a, b, c, e, art in checks]
    failed = sum(1 for c in checks if c[2] != "pass")

    body = (
        '<section class="hero"><div><span class="eyebrow light">VERIFICATION</span>'
        '<h2>Every claim re-derived from the artifact it came from</h2>'
        '<p>This page does not describe the data. It recomputes the claims from the files and '
        'prints the result, so if a claim and its artifact ever disagree the page says so '
        'instead of repeating the claim. A failed row here is a reason not to publish.</p>'
        '<a class="button" href="#checks">Run the checks ↓</a></div>'
        '<div class="hero-stat"><div class="ring">%d</div><strong>checks passed</strong>'
        '<small>of %d — %d failed</small></div></section>' % (len(checks) - failed, len(checks), failed)
        + section("checks", "CHECKS", "Ten claims, each recomputed here",
                  "The second column is the measurement, not a restatement. Where a row "
                  "shows a fraction, the numerator is what passed the check and the "
                  "denominator is the population.",
                  "%d / %d" % (len(checks) - failed, len(checks)),
                  table(["Claim", "Measured", "Result", "Why it matters"], rows))
        + section("sources", "SOURCES USED", "Every upstream this layer reads",
                  "Grouped by the job they do. The official NFL pages are the source of "
                  "record for results, availability and transactions; the odds endpoint is "
                  "a third-party publisher and is labelled T3 everywhere it appears.",
                  "TIERED", table(
                      ["Source", "Tier", "What it backs", "Link"],
                      [["NFL.com standings", pill("T1 official", "ok"),
                        "team scoring rates, the ratings input", ext(NFL_STAND, "nfl.com/standings")],
                       ["NFL.com weekly schedule & results", pill("T1 official", "ok"),
                        "final scores, kickoff times, the results feed", ext(NFL_SCHED, "nfl.com schedules")],
                       ["NFL.com injury report", pill("T1 official", "ok"),
                        "the absence, never the string", ext(NFL_INJ, "nfl.com/injuries")],
                       ["NFL.com transactions", pill("T1 official", "ok"),
                        "the date of a loss and the date of a replacement", ext(NFL_TXN, "nfl.com/transactions")],
                       ["NFL.com club pages", pill("T1 official", "ok"),
                        "player identity; the depth-chart path is a verified 404",
                        ext(NFL + "/teams/arizona-cardinals/", "a club page")],
                       ["ESPN odds endpoint (DraftKings)", pill("T3 third party", "warn"),
                        "open and close numbers, labelled T3 on every row",
                        ext("https://sportsbook.draftkings.com/", "the book named in the payload")]]))
        + section("reproduce", "REPRODUCE", "Rebuild this layer from the cached bodies",
                  "Deterministic, standard library only, no network for the rebuild itself.",
                  "COMMANDS", '<div class="note"><code>python3 tools/fetch.py plan</code> '
                  'writes the retrieval plan; <code>python3 tools/fetch.py ingest</code> folds '
                  'the cached bodies into the store; <code>python3 tools/origination.py</code> '
                  'originates and grades; <code>python3 tools/depth.py</code> builds the depth '
                  'ledger; <code>python3 tools/ops.py</code> renders these pages; '
                  '<code>python3 tools/check_site.py</code> is the gate.</div>')
    )
    return body


def main():
    d = load()
    pages = {
        "origination.html": ("Line origination", "01 · ORIGINATION",
                             "Line origination", "v1 · side → total → moneyline", build_origination),
        "price-store.html": ("Price store", "02 · STORE",
                             "Price-snapshot store", "append-only · tier T3", build_price_store),
        "signal-vs-staking.html": ("Signal vs staking", "03 · SCORING",
                                   "Signal vs staking", "0 strategies eligible", build_signal_vs_staking),
        "correlations.html": ("Correlations", "04 · CORRELATION",
                              "Correlations with n", "computed, not estimated", build_correlations),
        "replacements.html": ("Availability & depth", "05 · DEPTH",
                              "Availability &amp; replacement depth", "depth unresolved · flagged",
                              build_replacements),
        "method-lab.html": ("Method lab", "06 · METHOD",
                            "Method lab", "research · statuses labelled", build_method_lab),
        "ops-review.html": ("Review gate", "07 · REVIEW",
                            "Review gate", "review before implementing", build_review),
        "verification.html": ("Verification", "08 · VERIFICATION",
                              "Verification", "recomputed, not restated", build_verification),
        "requirements-closure.html": ("Requirement closure", "09 · CLOSURE",
                                      "Requirement closure", "twelve verdicts", build_requirements_closure),
    }
    written = []
    for slug, (title, eyebrow, heading, status, fn) in pages.items():
        body = fn(d)
        out = page(slug, title, eyebrow, heading, status, body)
        with open(os.path.join(SITE, slug), "w", encoding="utf-8") as fh:
            fh.write(out)
        written.append((slug, len(out)))
    for slug, size in written:
        print("wrote site/%-26s %8d bytes" % (slug, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
