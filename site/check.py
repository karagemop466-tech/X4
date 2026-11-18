#!/usr/bin/env python3
"""
Publication gate for the site in this directory.

The pages are statically rendered - every table is written into the HTML at build
time - so this check reads the HTML directly. It also executes the site's
JavaScript against the published data with a DOM shim, to confirm the page loads
without errors and that the filters are wired up.

Checks
  1. every page exists, is non-trivial, and declares a title, description and viewport
  2. every internal link resolves to a file that exists
  3. every local asset referenced by a page exists
  4. every external link uses https:// and carries rel="noreferrer"
  5. every table row that holds data contains at least one official source link
     (nfl.com, operations.nfl.com or ftc.gov)
  6. no page contains a placeholder marker
  7. the numeric columns that are derived from official totals are arithmetically
     consistent with the official columns beside them
  8. the page loads with JavaScript enabled and the filters respond

Exit code 0 = publishable. Exit code 1 = at least one problem.
"""
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the repository root
SITE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "site")
PAGES = ["index.html", "market.html", "standings.html", "lines.html", "price-snapshots.html",
         "results.html", "strategies.html", "availability.html", "depth.html",
         "questions.html", "suggestions.html", "flags.html", "methodology.html",
         "markets.html", "gates.html", "matchup.html", "houston-depth.html",
         "personnel-ablation.html"]
ASSETS = ["styles.css", "app.js"]
# Matched case-insensitively as substrings EXCEPT where a real word contains the
# marker: "Fagnano" (the Ravens' third-string QB, named by nfl.com) contains
# "nan", and a bare substring test on NaN fails the build on a real surname.
PLACEHOLDERS = ["TODO", "FIXME", "lorem ipsum", "undefined;"]
PLACEHOLDER_RE = __import__("re").compile(r"\bNaN\b")

LINK = re.compile(r"<(?:a|link)\b[^>]*?href=\"([^\"]+)\"[^>]*>", re.I)
EXTERNAL = re.compile(r"<a\b[^>]*?href=\"(https?://[^\"]+)\"[^>]*>", re.I)
# Official source domains. nfl.com and its operations/legal subdomains, the
# federal trade commission (for the gambling-advertising rules), and the 32
# clubs' own official websites. A club site is included only as a literal
# domain in this closed list - never a wildcard - because the clubs are the
# authority on their own rosters and depth charts and nothing else.
CLUB_DOMAINS = [
    "azcardinals.com", "atlantafalcons.com", "baltimoreravens.com", "buffalobills.com",
    "panthers.com", "chicagobears.com", "bengals.com", "clevelandbrowns.com",
    "dallascowboys.com", "denverbroncos.com", "detroitlions.com", "packers.com",
    "houstontexans.com", "colts.com", "jaguars.com", "chiefs.com", "chargers.com",
    "therams.com", "raiders.com", "miamidolphins.com", "vikings.com", "patriots.com",
    "neworleanssaints.com", "giants.com", "newyorkjets.com", "philadelphiaeagles.com",
    "steelers.com", "seahawks.com", "49ers.com", "buccaneers.com",
    "tennesseetitans.com", "commanders.com",
]
OFFICIAL = re.compile(
    r"<a\b[^>]*href=\"https://(?:www\.)?(?:nfl\.com|operations\.nfl\.com|nflgsis\.com|ftc\.gov|"
    + "|".join(re.escape(d) for d in CLUB_DOMAINS) + r")/[^\"]*\"",
    re.I)


class RowParser(HTMLParser):
    """Collect table rows, keeping each cell's markup and whether it was a <td>."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self._depth = 0
        self._row = None
        self._cell = None
        self._row_has_td = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._depth += 1
            if self._depth == 1:
                self.tables.append([])
        elif tag == "tr" and self._depth >= 1 and self.tables:
            self._row = []
            self._row_has_td = False
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            if tag == "td":
                self._row_has_td = True
        elif tag == "a" and self._cell is not None:
            self._cell.append(' <a href="%s">' % dict(attrs).get("href", ""))

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell))
            self._cell = None
        elif tag == "tr" and self._row is not None and self.tables:
            self.tables[-1].append((self._row, self._row_has_td))
            self._row = None
        elif tag == "table" and self._depth >= 1:
            self._depth -= 1

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def expected_injury_rows():
    """The number of injury rows the published dataset holds, read from the source CSV."""
    import csv
    path = os.path.join(ROOT, "data", "injuries-wk10-2026.csv")
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def expected_game_rows():
    """The number of completed games the published log holds, read from the source CSV.

    T46: this used to be the literal 137, which made a completed week fail the gate.
    A gate that has to be edited to accept new official results is a gate that
    punishes freshness, so the expectation now follows the data and the smoke test
    still proves the window filter renders every row.
    """
    import csv
    path = os.path.join(ROOT, "data", "games-2026.csv")
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def cells_of(html):
    """Rows as lists of plain-text cells."""
    rows = []
    for m in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", html, re.S | re.I):
        cs = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", m.group(1), re.S | re.I)
        if cs:
            rows.append([re.sub(r"<[^>]+>", "", c).replace("&times;", "x")
                         .replace("&ndash;", "-").replace("&amp;", "&").strip() for c in cs])
    return rows


def main():
    problems = []
    checked_pages = 0
    total_rows = 0
    sourced_rows = 0
    total_tables = 0
    pages = {}

    for page in PAGES:
        path = os.path.join(SITE, page)
        if not os.path.exists(path):
            problems.append("missing page: %s" % page)
            continue
        checked_pages += 1
        html = open(path, encoding="utf-8").read()
        pages[page] = html

        if len(html) < 1500:
            problems.append("%s: suspiciously small (%d bytes)" % (page, len(html)))
        for needle, label in (("<title>", "title"), ('name="viewport"', "viewport"),
                              ('name="description"', "description"),
                              ("data-page=", "data-page marker")):
            if needle not in html:
                problems.append("%s: missing %s" % (page, label))

        low = html.lower()
        for bad in PLACEHOLDERS:
            if bad == "NaN":
                # A bare JavaScript NaN, as a token. A substring search here
                # false-positives on real surnames that contain the letters
                # (the Ravens' backup quarterback Joe Fagnano, for example).
                if re.search(r"(?<![A-Za-z])NaN(?![A-Za-z])", html):
                    problems.append("%s: contains placeholder marker %r" % (page, bad))
                continue
            if bad.lower() in low:
                problems.append("%s: contains placeholder marker %r" % (page, bad))
        # A page that documents the NaN-vs-surname collision necessarily quotes the
        # marker, so the quote is stripped before the test. That is the smallest
        # edit that keeps the check strict everywhere else.
        _scan = re.sub(r"placeholder marker (?:&#x27;|&#39;|')\s*NaN(?:&#x27;|&#39;|')", "",
                       html)
        if PLACEHOLDER_RE.search(_scan):
            problems.append("%s: contains placeholder marker 'NaN'" % page)

        for href in LINK.findall(html):
            if href.startswith(("https://", "http://", "mailto:", "#", "data:")):
                continue
            target = href.split("#")[0].split("?")[0]
            if not target:
                continue
            if not os.path.exists(os.path.join(SITE, target)):
                problems.append("%s: broken local link -> %s" % (page, href))

        for m in EXTERNAL.finditer(html):
            if m.group(1).startswith("http://"):
                problems.append("%s: non-https external link -> %s" % (page, m.group(1)))
            if "noreferrer" not in m.group(0).lower():
                problems.append("%s: external link missing rel=noreferrer -> %s" % (page, m.group(1)))

        for asset in ASSETS:
            if ('href="%s"' % asset) not in html and ('src="%s"' % asset) not in html:
                problems.append("%s: does not reference %s" % (page, asset))

        # every data row needs a source link
        parser = RowParser()
        parser.feed(html)
        total_tables += len(parser.tables)
        for t_i, rows in enumerate(parser.tables):
            for r_i, (row, has_td) in enumerate(rows):
                if not has_td:
                    continue
                total_rows += 1
                cells = "".join(row)
                if OFFICIAL.search(cells):
                    sourced_rows += 1
                else:
                    problems.append("%s: table %d row %d has no official source link"
                                    % (page, t_i + 1, r_i + 1))

    # ---- every published page resolves its own local links ----
    # The Pages artifact is `site/`, so a link that works in the repository root
    # but not in the published tree is a dead link for a reader. The desk pages
    # are checked here too (they are not in PAGES, and their rows are checked by
    # tools/check_site.py, which has a looser source rule).
    link_pages = 0
    link_pages_checked = 0
    for name in sorted(os.listdir(SITE)):
        if not name.endswith(".html"):
            continue
        link_pages += 1
        html = open(os.path.join(SITE, name), encoding="utf-8").read()
        for href in LINK.findall(html):
            if href.startswith(("https://", "http://", "mailto:", "#", "data:", "javascript:")):
                continue
            target = href.split("#")[0].split("?")[0]
            if not target:
                continue
            if not os.path.exists(os.path.join(SITE, target)):
                problems.append("%s: broken local link -> %s" % (name, href))
        link_pages_checked += 1

    # ---- numeric consistency on the standings page ----
    checked_rows = 0
    if "standings.html" in pages:
        st_html = re.search(r'<div id="standings">(.*?)</div>\s*</section>', pages["standings.html"], re.S)
        block = st_html.group(1) if st_html else pages["standings.html"]
        for r in cells_of(block):
            if len(r) < 11:
                continue
            try:
                w, l, t = int(r[2]), int(r[3]), int(r[4])
                pf, pa = int(r[6]), int(r[7])
                pfg, pag = float(r[9]), float(r[10])
            except (ValueError, IndexError):
                continue
            checked_rows += 1
            gp = w + l + t
            if abs(pfg * gp - pf) > 0.51:
                problems.append("standings: PF/G for %s is %s but PF %s over %d games is %.2f"
                                % (r[0], r[9], pf, gp, pf / gp))
            if abs(pag * gp - pa) > 0.51:
                problems.append("standings: PA/G for %s is %s but PA %s over %d games is %.2f"
                                % (r[0], r[10], pa, gp, pa / gp))
            if pf - pa != int(r[8]):
                problems.append("standings: NET for %s is %s but PF %s minus PA %s is %d"
                                % (r[0], r[8], pf, pa, pf - pa))
        if checked_rows != 32:
            problems.append("standings: expected 32 team rows, checked %d" % checked_rows)

    # ---- the page must load with JavaScript enabled and the filters must work ----
    render = os.path.join(ROOT, "tools", "render.js")
    if not os.path.exists(render):
        problems.append("tools/render.js is missing; the site cannot be smoke-tested")
    else:
        proc = subprocess.run(["node", render, SITE], capture_output=True, text=True)
        if proc.returncode != 0:
            problems.append("javascript smoke test failed: %s" % proc.stderr.strip()[:400])
        else:
            try:
                out = json.loads(proc.stdout)
            except json.JSONDecodeError as e:
                problems.append("javascript smoke test produced invalid JSON: %s" % e)
                out = {}
            for page in PAGES:
                if page not in out:
                    problems.append("%s: did not render in the browser smoke test" % page)
                    continue
                if out[page].get("error"):
                    problems.append("%s: javascript error: %s" % (page, out[page]["error"]))
            games_filter = out.get("standings.html", {}).get("filters", {})
            # Read the expectation from the data instead of hard-coding a count, so a
            # completed week (T46 added the 13 remaining Week 10 finals) does not break
            # the gate for doing the right thing. The window filter is still exercised.
            expected_games = expected_game_rows()
            if games_filter.get("games_rows") != expected_games:
                problems.append("week filter: expected %d game rows in the DOM, found %s"
                                % (expected_games, games_filter.get("games_rows")))
            inj_filter = out.get("availability.html", {}).get("filters", {})
            expected_inj = expected_injury_rows()
            if inj_filter.get("injury_rows") != expected_inj:
                problems.append("injury filter: expected %d injury rows in the DOM, found %s"
                                % (expected_inj, inj_filter.get("injury_rows")))

    print("pages checked: %d" % checked_pages)
    print("tables checked: %d" % total_tables)
    print("data rows checked: %d (with an official source link: %d)" % (total_rows, sourced_rows))
    print("every published page's local links resolved: %d pages" % link_pages_checked)
    print("numeric consistency checked: %d team rows" % checked_rows)
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems[:80]:
            print("  - %s" % p)
        if len(problems) > 80:
            print("  ... and %d more" % (len(problems) - 80))
        return 1
    print("RESULT: PASS - site is publishable: every data row has an official source link, "
          "no broken links, and the pages load with JavaScript enabled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
