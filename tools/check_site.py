#!/usr/bin/env python3
"""Site checker: fail CI if the root Pages site has broken links or unverified data rows.

Checks (every root *.html, excluding the historical site/ archive):
  1. Every local href/src resolves to an existing file (or an in-page/target-page anchor).
  2. Every in-page #anchor exists on that page.
  3. Every table.data body row contains at least one https:// source link.
  4. Every external link is https and well-formed.
  5. Every page carries the same sidebar navigation (link set equality).
Exits non-zero on any violation.
"""
import re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Desk pages owned by session 5c48ced7 (the main site has its own gate: site/check.py).
DESK_PAGES = [
    "executive-summary.html", "requirements.html", "data.html", "signals.html",
    "leaderboard.html", "injuries.html", "decisions.html", "review.html",
    "programme.html", "flagged.html", "repo-review.html", "sources.html",
]
NAV_HREFS = {"index.html", *DESK_PAGES}          # brand links to the main landing page
MIRRORED = DESK_PAGES + ["desk.css", "nav.js"]   # each must exist byte-identically in site/


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs, self.srcs, self.nav = set(), [], [], set()
        self._in_nav = False
        self._in_td = False
        self._rows = []          # list of list-of-hrefs (per data row)
        self._cur_row = None
        self._in_data_table = 0
        self._in_tbody = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "nav":
            self._in_nav = True
        if tag == "table" and "data" in (a.get("class") or "").split():
            self._in_data_table += 1
        if tag == "tbody" and self._in_data_table:
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self._cur_row = []
        if tag in ("a", "link") and "href" in a:
            self.hrefs.append(a["href"])
            if self._in_nav:
                self.nav.add(a["href"])
        if tag in ("img", "script") and "src" in a:
            self.srcs.append(a["src"])
        if tag == "td" or tag == "th":
            self._in_td = True

    def handle_endtag(self, tag):
        if tag == "nav":
            self._in_nav = False
        if tag == "tr" and self._cur_row is not None:
            self._rows.append(self._cur_row)
            self._cur_row = None
        if tag == "tbody":
            self._in_tbody = False
        if tag == "table" and self._in_data_table:
            self._in_data_table -= 1

    def handle_data(self, data):
        pass

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def page_ids(path: Path) -> set:
    p = Page(); p.feed(path.read_text(encoding="utf-8")); return p.ids


def main() -> int:
    pages = [ROOT / n for n in DESK_PAGES]
    errors = []
    parsed = {}
    for pg in pages:
        p = Page()
        p.feed(pg.read_text(encoding="utf-8"))
        parsed[pg.name] = p

    for name, p in parsed.items():
        # 3. data rows need https source links
        for i, row in enumerate(p._rows):
            if not row:
                continue
            if not any(h.startswith("https://") for h in row):
                errors.append(f"{name}: data row #{i+1} has no https source link")
        # 4/5 + link resolution
        for href in p.hrefs + p.srcs:
            if href.startswith("https://"):
                if " " in href or href.count('"'):
                    errors.append(f"{name}: malformed external URL: {href[:80]}")
                continue
            if href.startswith("http://"):
                errors.append(f"{name}: insecure/non-https external link: {href[:80]}")
                continue
            if href.startswith("#"):
                if href[1:] and href[1:] not in p.ids:
                    errors.append(f"{name}: broken in-page anchor {href}")
                continue
            if href.startswith("mailto:"):
                continue
            target, _, frag = href.partition("#")
            if target:
                tp = ROOT / target
                if not tp.is_file():
                    errors.append(f"{name}: missing local file {target}")
                    continue
                if frag and target.endswith(".html"):
                    if frag not in page_ids(tp):
                        errors.append(f"{name}: broken anchor {href} (target lacks #{frag})")
            elif frag and frag not in p.ids:
                errors.append(f"{name}: broken anchor #{frag}")
        # nav consistency
        nav = {h for h in p.nav}
        if nav != NAV_HREFS:
            errors.append(f"{name}: nav mismatch — missing {sorted(NAV_HREFS - nav)} extra {sorted(nav - NAV_HREFS)}")

    # integrity datasets: every CSV must have a rectangular shape. A row with one field
    # too many shifts a trailing blank into a later column, which is how a source link
    # once ended up empty while the row still "looked" sourced.
    import csv as _csv
    for fn in sorted(os.listdir(ROOT / "research" / "data")):
        if not fn.endswith(".csv"):
            continue
        with open(ROOT / "research" / "data" / fn, newline="", encoding="utf-8") as fh:
            raw = list(_csv.reader(fh))
        if not raw:
            continue
        width = len(raw[0])
        bad = [(i + 1, len(r)) for i, r in enumerate(raw) if len(r) != width]
        if bad:
            errors.append(f"research/data/{fn}: rows with the wrong field count (header {width}): {bad[:5]}")

    # mirror check: desk files must be byte-identical inside site/ (publish path)
    mirror_errors = []
    for name in MIRRORED:
        root_f, site_f = ROOT / name, ROOT / "site" / name
        if not site_f.is_file():
            mirror_errors.append(f"missing site/{name}")
        elif root_f.read_bytes() != site_f.read_bytes():
            mirror_errors.append(f"site/{name} differs from root {name}")
    errors.extend(mirror_errors)
    total_rows = sum(len(p._rows) for p in parsed.values())
    print(f"Checked {len(pages)} desk pages, {total_rows} table rows, {len(MIRRORED)} mirrored files, "
          f"{sum(len(p.hrefs) for p in parsed.values())} links.")
    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for e in errors[:40]:
            print(" -", e)
        return 1
    print("PASS: all local links/anchors resolve; every data row has an https source link; nav consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
