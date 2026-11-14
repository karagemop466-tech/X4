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
NAV_HREFS = {
    "index.html", "executive-summary.html", "requirements.html", "data.html",
    "strategies.html", "leaderboard.html", "injuries.html", "decisions.html",
    "suggestions.html", "flagged.html", "repo-review.html", "sources.html",
}


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
    pages = sorted(p for p in ROOT.glob("*.html"))
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

    total_rows = sum(len(p._rows) for p in parsed.values())
    print(f"Checked {len(pages)} pages, {total_rows} table rows, "
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
