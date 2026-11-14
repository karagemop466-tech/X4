#!/usr/bin/env python3
"""
Publication gate for the site in this directory.

The tables are built in the browser from window.X4, so the check does not read
the static HTML alone: it executes site/app.js against site/data.js with a DOM
shim (tools/render.js), then inspects the RESULTING markup.

Checks
  1. every page exists, is non-trivial, and declares a title, description and viewport
  2. every internal link resolves to a file that exists
  3. every local asset referenced by a page exists
  4. every external link uses https:// and carries rel="noreferrer"
  5. every rendered table row that holds data contains at least one official
     source link (nfl.com, operations.nfl.com or ftc.gov)
  6. no page contains a placeholder marker
  7. the page that renders each table exists and produced rows (no silent empty table)

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
PAGES = ["index.html", "standings.html", "lines.html", "strategies.html",
         "availability.html", "questions.html", "suggestions.html", "flags.html",
         "methodology.html"]
ASSETS = ["styles.css", "app.js", "data.js"]
PLACEHOLDERS = ["TODO", "FIXME", "lorem ipsum", "undefined;", "NaN"]

LINK = re.compile(r"<(?:a|link)\b[^>]*?href=\"([^\"]+)\"[^>]*>", re.I)
EXTERNAL = re.compile(r"<a\b[^>]*?href=\"(https?://[^\"]+)\"[^>]*>", re.I)
ROW = re.compile(r"<tr\b.*?</tr>", re.S | re.I)
TD = re.compile(r"<td\b", re.I)
TH = re.compile(r"<th\b", re.I)
OFFICIAL = re.compile(
    r"<a\b[^>]*href=\"https://(?:www\.)?(?:nfl\.com|operations\.nfl\.com|ftc\.gov)/[^\"]*\"",
    re.I)

# Tables whose rows are explanatory/framework content rather than sourced data.
NO_SOURCE_EXPECTED = set()


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


def main():
    problems = []
    checked_pages = 0
    total_rows = 0
    sourced_rows = 0
    total_tables = 0

    # ---- 1. render every page with the real renderer ----
    render = os.path.join(ROOT, "tools", "render.js")
    if not os.path.exists(render):
        print("FATAL: tools/render.js is missing; the site cannot be checked.")
        return 1
    proc = subprocess.run(["node", render, SITE], capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        problems.append("renderer failed: %s" % (proc.stderr.strip()[:500] or "no output"))
        rendered = {}
    else:
        try:
            rendered = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            problems.append("renderer output is not valid JSON: %s" % e)
            rendered = {}

    # ---- 2. static checks on each page ----
    for page in PAGES:
        path = os.path.join(SITE, page)
        if not os.path.exists(path):
            problems.append("missing page: %s" % page)
            continue
        checked_pages += 1
        html = open(path, encoding="utf-8").read()

        if len(html) < 800:
            problems.append("%s: suspiciously small (%d bytes)" % (page, len(html)))
        for needle, label in (("<title>", "title"), ('name="viewport"', "viewport"),
                              ('name="description"', "description"),
                              ("data-page=", "data-page marker")):
            if needle not in html:
                problems.append("%s: missing %s" % (page, label))

        low = html.lower()
        for bad in PLACEHOLDERS:
            if bad.lower() in low:
                problems.append("%s: contains placeholder marker %r" % (page, bad))

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

    # ---- 3. row-level checks on the RENDERED markup ----
    EXPECTED_TABLES = {
        "index.html": ["lb-preview", "flag-preview"],
        "standings.html": ["standings", "power", "games"],
        "lines.html": ["lines", "strat-list"],
        "strategies.html": ["lb", "gates", "calib", "weekly"],
        "availability.html": ["avail", "qb", "news", "inj-full"],
        "questions.html": ["qa"],
        "suggestions.html": ["sugg-frame"],
        "flags.html": ["flags"],
        "methodology.html": ["params", "verify"],
    }
    for page, expected in EXPECTED_TABLES.items():
        data = rendered.get(page)
        if not data:
            problems.append("%s: page did not render" % page)
            continue
        for el_id in expected:
            html = data["elements"].get(el_id)
            if not html:
                problems.append("%s: element #%s rendered empty" % (page, el_id))
                continue
            parser = RowParser()
            parser.feed(html)
            total_tables += len(parser.tables)
            if not parser.tables:
                problems.append("%s: #%s produced no table" % (page, el_id))
                continue
            for t_i, rows in enumerate(parser.tables):
                for r_i, (row, has_td) in enumerate(rows):
                    cells = "".join(row)
                    if not has_td:
                        continue  # header row
                    total_rows += 1
                    if OFFICIAL.search(cells):
                        sourced_rows += 1
                    elif page + "#" + el_id not in NO_SOURCE_EXPECTED:
                        problems.append("%s: #%s table %d row %d has no official source link"
                                        % (page, el_id, t_i + 1, r_i + 1))

    # ---- 4. numeric consistency: derived columns must match the official columns ----
    def cells_of(html):
        rows = []
        for m in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", html, re.S | re.I):
            cs = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", m.group(1), re.S | re.I)
            if cs:
                rows.append([re.sub(r"<[^>]+>", "", c).replace("\u00a0", " ").strip() for c in cs])
        return rows

    st_rows = cells_of(rendered.get("standings.html", {}).get("elements", {}).get("standings", ""))
    checked_rows = 0
    for r in st_rows:
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

    print("pages checked: %d" % checked_pages)
    print("numeric consistency checked: %d team rows" % checked_rows)
    print("rendered tables checked: %d" % total_tables)
    print("data rows checked: %d (with an official source link: %d)" % (total_rows, sourced_rows))
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems[:80]:
            print("  - %s" % p)
        if len(problems) > 80:
            print("  ... and %d more" % (len(problems) - 80))
        return 1
    print("RESULT: PASS - site is publishable: every rendered data row has an official source link, no broken links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
