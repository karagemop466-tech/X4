#!/usr/bin/env python3
"""Re-derive every published correlation and every published home-edge constant.

The brief requires two things that are easy to break and hard to see:
  * every correlation is computed only from officially sourced numbers, and
  * every published correlation carries the n it was actually computed on.

The number printed beside a correlation is the number a reader trusts, so this
checker recomputes each one from the committed official data and compares it
with what the published page carries: the value, the interval and the n. A
mismatch fails the build instead of sitting on the page.

Nothing here is transcribed by hand and nothing is fetched: every input is a
committed file, and every published page is the one this repository builds.

Run:  python3 tools/check_published_stats.py   (exit 0 = every published number holds)
"""
import csv
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
NEUTRAL_FILE = os.path.join(ROOT, "data", "international-2026.csv")

FAILURES = []
ROWS = []


def fail(msg):
    FAILURES.append(msg)
    print("FAIL " + msg)


def ok(msg):
    print("PASS " + msg)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pearson(xs, ys):
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def fisher_ci(r, n):
    if r is None or n < 4:
        return ("", "")
    r = max(-0.999999, min(0.999999, r))
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se
    inv = lambda v: (math.exp(2 * v) - 1) / (math.exp(2 * v) + 1)
    return (inv(lo), inv(hi))


def neutral_pairs():
    """The official International Games: a game played away has no home field."""
    out = set()
    for r in read_csv(NEUTRAL_FILE):
        out.add((r["away"], r["home"]))
    return out


def close(a, b, tol=5e-4):
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# 1. the desk correlations page: computed from the official game log
# ---------------------------------------------------------------------------
def check_desk_correlations():
    games = read_csv(os.path.join(ROOT, "data", "games-2026.csv"))
    standings = read_csv(os.path.join(ROOT, "data", "standings-wk10-2026.csv"))
    away = [int(g["away_pts"]) for g in games]
    home = [int(g["home_pts"]) for g in games]
    margins = [h - a for a, h in zip(away, home)]
    totals = [h + a for a, h in zip(away, home)]
    net = [int(r["net_pts"]) for r in standings]
    pct = [float(r["pct"]) for r in standings]
    pfg = [float(r["pf"]) / max(1, int(r["w"]) + int(r["l"]) + int(r["t"])) for r in standings]
    pag = [float(r["pa"]) / max(1, int(r["w"]) + int(r["l"]) + int(r["t"])) for r in standings]
    computed = {
        "away score ↔ home score": (away, home, "all %d completed games" % len(games)),
        "home margin ↔ game total": (margins, totals, "all %d completed games" % len(games)),
        "net points ↔ win percentage": (net, pct, "32 clubs"),
        "points for /g ↔ points allowed /g": (pfg, pag, "32 clubs"),
    }
    path = os.path.join(SITE, "correlations.html")
    if not os.path.exists(path):
        fail("site/correlations.html is missing")
        return
    html = open(path, encoding="utf-8").read()
    for label, (xs, ys, depth) in computed.items():
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, len(xs))
        pat = re.compile(r"<b>%s</b></td><td>r = ([-+0-9.]+)</td><td>\[([-+0-9.]+), ([-+0-9.]+)\]</td><td>(\d+)</td>"
                         % re.escape(label))
        m = pat.search(html)
        if not m:
            fail("site/correlations.html does not publish a row for %r" % label)
            continue
        pr, plo, phi, pn = m.group(1), m.group(2), m.group(3), int(m.group(4))
        if pn != len(xs):
            fail("%s: published n = %d but the value is computed on %d observations"
                 % (label, pn, len(xs)))
            continue
        if not close(pr, r, 5e-4) or not close(plo, lo, 5e-4) or not close(phi, hi, 5e-4):
            fail("%s: published r = %s [%s, %s] but the recomputation is %.4f [%.4f, %.4f]"
                 % (label, pr, plo, phi, r, lo, hi))
            continue
        ROWS.append([label, "%.4f" % r, "[%.4f, %.4f]" % (lo, hi), str(len(xs)), depth,
                     "site/correlations.html"])
        ok("%s: r = %.4f on n = %d matches the published row" % (label, r, len(xs)))


# ---------------------------------------------------------------------------
# 2. the legacy correlation rows: computed from the weeks 6-9 sample
# ---------------------------------------------------------------------------
def check_legacy_correlations():
    games = read_csv(os.path.join(ROOT, "research", "data", "games_weeks6-9_2026.csv"))
    teams = read_csv(os.path.join(ROOT, "research", "data", "standings_2026_through_week10_tnf.csv"))
    neutral = {(g["away"], g["home"]) for g in games if g["neutral_site"] == "1"}
    away = [int(g["away_score"]) for g in games]
    home = [int(g["home_score"]) for g in games]
    keep = [i for i, g in enumerate(games) if g["neutral_site"] == "0"]
    margins = [int(games[i]["home_score"]) - int(games[i]["away_score"]) for i in keep]
    totals = [int(games[i]["home_score"]) + int(games[i]["away_score"]) for i in keep]
    net = [int(t["net"]) for t in teams]
    wpct = [(int(t["w"]) + 0.5 * int(t["t"])) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
    pfg = [int(t["pf"]) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
    pag = [int(t["pa"]) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
    computed = {
        "away_vs_home_scores": (away, home),
        "margin_vs_total": (margins, totals),
        "net_pts_vs_win_pct": (net, wpct),
        "pts_per_game_vs_pts_allowed_per_game": (pfg, pag),
    }
    stats_path = os.path.join(ROOT, "research", "computed_stats.json")
    stats = json.load(open(stats_path, encoding="utf-8"))
    path = os.path.join(SITE, "gates.html")
    if not os.path.exists(path):
        fail("site/gates.html is missing")
        return
    html = open(path, encoding="utf-8").read()
    for key, (xs, ys) in computed.items():
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, len(xs))
        published = stats["correlations"][key]
        if published["n"] != len(xs):
            fail("%s: computed_stats.json records n = %d but the value is computed on %d observations"
                 % (key, published["n"], len(xs)))
            continue
        if not close(published["r"], r, 5e-5):
            fail("%s: computed_stats.json records r = %s but the recomputation is %.4f"
                 % (key, published["r"], r))
            continue
        pat = re.compile(r"%s</span></td><td>[^<]*</td><td class=\"num\">([-+0-9.]+)</td>"
                         r"<td class=\"num\">\[([-+0-9.]+), ([-+0-9.]+)\]</td>"
                         r"<td class=\"num\">(\d+)</td>" % re.escape(key))
        m = pat.search(html)
        if not m:
            fail("site/gates.html does not publish a row for %r" % key)
            continue
        pr, plo, phi, pn = m.group(1), m.group(2), m.group(3), int(m.group(4))
        if pn != len(xs):
            fail("%s: site/gates.html publishes n = %d but the value is computed on %d observations"
                 % (key, pn, len(xs)))
            continue
        if not close(pr, r, 5e-5) or not close(plo, lo, 5e-5) or not close(phi, hi, 5e-5):
            fail("%s: site/gates.html publishes r = %s [%s, %s] but the recomputation is %.4f [%.4f, %.4f]"
                 % (key, pr, plo, phi, r, lo, hi))
            continue
        ROWS.append([key, "%.4f" % r, "[%.4f, %.4f]" % (lo, hi), str(len(xs)),
                     "weeks 6-9 sample" + (", neutral-site games removed" if key == "margin_vs_total" else ""),
                     "site/gates.html"])
        ok("%s: r = %.4f on n = %d matches the published row and the committed stats file"
           % (key, r, len(xs)))


# ---------------------------------------------------------------------------
# 3. the published home-edge constants
# ---------------------------------------------------------------------------
def home_edge_stats(margins):
    n = len(margins)
    m = sum(margins) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in margins) / (n - 1))
    se = sd / math.sqrt(n)
    return n, m, (m - 1.96 * se, m + 1.96 * se)


def check_home_edge():
    games = read_csv(os.path.join(ROOT, "data", "games-2026.csv"))
    neutral = neutral_pairs()
    corpus = [int(g["home_pts"]) - int(g["away_pts"]) for g in games
              if (g["away"], g["home"]) not in neutral]
    n_corpus, m_corpus, ci_corpus = home_edge_stats(corpus)

    week69 = read_csv(os.path.join(ROOT, "research", "data", "games_weeks6-9_2026.csv"))
    w69 = [int(g["home_score"]) - int(g["away_score"]) for g in week69 if g["neutral_site"] == "0"]
    n_69, m_69, ci_69 = home_edge_stats(w69)

    # the desk executive summary publishes both, with their windows
    path = os.path.join(SITE, "executive-summary.html")
    html = open(path, encoding="utf-8").read()
    want_corpus = "home margin <b>%+.1f</b> points on <b>n = %d of %d</b>" % (m_corpus, n_corpus, len(games))
    if want_corpus not in html:
        fail("site/executive-summary.html does not publish the corpus home margin %r" % want_corpus)
    else:
        ok("the corpus home margin is published with its n and window: %+.2f points on n = %d of %d"
           % (m_corpus, n_corpus, len(games)))
    want_69 = "give %+.2f on n&nbsp;=&nbsp;%d" % (m_69, n_69)
    if want_69 not in html:
        fail("site/executive-summary.html does not publish the weeks 6-9 home edge %r" % want_69)
    else:
        ok("the weeks 6-9 home edge is published with its window and n: %+.2f on n = %d" % (m_69, n_69))
    ROWS.append(["home-field edge, official corpus (neutral-site games excluded)",
                 "%+.3f" % m_corpus, "[%+.2f, %+.2f]" % ci_corpus, str(n_corpus),
                 "weeks 1-%d of the official game log" % max(int(g["week"]) for g in games),
                 "site/executive-summary.html"])
    ROWS.append(["home-field edge, weeks 6-9 (neutral-site games excluded)",
                 "%+.3f" % m_69, "[%+.2f, %+.2f]" % ci_69, str(n_69),
                 "weeks 6-9 sample, the window the line lab's h is fitted on",
                 "site/executive-summary.html"])

    # the strategy lab must name the window its home-edge strategy is fitted on
    path = os.path.join(SITE, "signals.html")
    if os.path.exists(path):
        html = open(path, encoding="utf-8").read()
        if "Game results Wks 6–9" not in html:
            fail("site/signals.html does not name the window the home-edge strategy is fitted on")
        else:
            ok("the strategy lab names the window its home-edge strategy is fitted on (weeks 6-9)")
    else:
        fail("site/signals.html is missing")


def main():
    check_desk_correlations()
    check_legacy_correlations()
    check_home_edge()

    report = os.path.join(ROOT, "research", "verification", "published-statistics-2026-11-19.csv")
    os.makedirs(os.path.dirname(report), exist_ok=True)
    with open(report, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["quantity", "value", "95% interval", "n", "depth", "published on"])
        w.writerows(ROWS)

    print("")
    if FAILURES:
        print("FAILED: %d published number(s) do not hold" % len(FAILURES))
        return 1
    print("ALL PUBLISHED STATISTICS HOLD: %d correlations and home-edge constants re-derived "
          "from the official data" % len(ROWS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
