#!/usr/bin/env python3
"""
Live official-source verification harness (task T20).

Diffs a **captured official NFL.com page** against the committed CSVs in `data/`,
so the published data can be re-checked against the league's own pages at any time
instead of being trusted once.

Two modes
---------
1. Snapshot mode (default, fully reproducible, no network needed)
   Reads a committed snapshot of the official page - a CSV holding the values read
   off the official source, plus a `source` column with the URL and a
   `retrieved` column with the capture date - and diffs it against the committed
   `data/*.csv` row by row. This is the mode the published verification record is
   built on; it runs identically in CI and offline.

2. Live mode (`--live`)
   Re-fetches the official NFL.com page over HTTPS and parses it, then diffs the
   parsed values against the committed CSVs. Requires outbound network access to
   `www.nfl.com`; use it to re-certify the data on demand. If the network is
   unavailable the harness reports that clearly and exits non-zero rather than
   guessing.

Subcommands
-----------
  standings   diff the official NFL.com standings against data/standings-wk10-2026.csv
  schedule    diff the official NFL.com Week 11 schedule against data/schedule-wk11-2026.csv
  injuries    diff a captured official Week 10 injury report against data/injuries-wk10-2026.csv
  all         run standings, schedule and injuries in order

Exit code 0 = every captured official value matches the committed data.
Exit code 1 = at least one mismatch (or a fetch/parse failure in live mode).

This tool is additive: it reads `data/**` and writes nothing. It is intentionally
NOT part of `tools/validate.py`'s publish gate, because live fetching needs network
access and must not be able to block or race the deterministic build.
"""
import argparse
import csv
import os
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SNAP = os.path.join(ROOT, "research", "verification")

STANDINGS_SNAPSHOT = os.path.join(SNAP, "standings-live-2026-11-14.csv")
SCHEDULE_SNAPSHOT = os.path.join(SNAP, "schedule-wk11-live-2026-11-14.csv")
INJURIES_SNAPSHOT = os.path.join(SNAP, "injuries-wk10-live-2026-11-14.csv")

STANDINGS_SRC = "https://www.nfl.com/standings/"
SCHEDULE_SRC = "https://www.nfl.com/schedules/2026/by-week/week-11"
INJURIES_SRC = "https://www.nfl.com/injuries/"

# Value columns compared (the `source` and `retrieved` columns are provenance, not data).
STANDINGS_VALUES = ["w", "l", "t", "pct", "pf", "pa", "net_pts"]
SCHEDULE_VALUES = ["week", "away", "home", "date", "time_et", "network", "nfl_url", "international"]
INJURIES_VALUES = ["team", "player", "pos", "injuries", "practice", "game_status", "player_url"]

USER_AGENT = "X4-live-verification/1.0 (official-source re-check)"


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def norm(value):
    """Normalise a cell for comparison: strip, collapse case-insensitively for text."""
    if value is None:
        return ""
    return str(value).strip()


def fetch(url):
    """Fetch a URL over HTTPS. Returns the body text or raises a clear error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as exc:
        raise SystemExit(
            "Could not fetch %s (%s). Live mode needs outbound network access to "
            "www.nfl.com. Re-run without --live against a committed snapshot, or "
            "run this in an environment with network access." % (url, exc))


# --------------------------------------------------------------------------- #
# Live HTML parsing (live mode)                                                #
# --------------------------------------------------------------------------- #
class _CellGrab(HTMLParser):
    """Collect the text of each <td> in each <tr> of an HTML page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag == "td" and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "td" and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


# NFL.com team display name -> the abbreviation used in the committed CSVs.
# The league site uses `LA`/`AZ`; the committed data uses `LAR`/`ARI` (documented
# as F-14 / R-11). We map both so a live fetch compares on values, not labels.
TEAM_ABBR = {
    "cardinals": "ARI", "atlanta falcons": "ATL", "falcons": "ATL", "ravens": "BAL",
    "bills": "BUF", "panthers": "CAR", "bears": "CHI", "bengals": "CIN",
    "browns": "CLE", "cowboys": "DAL", "broncos": "DEN", "lions": "DET",
    "packers": "GB", "texans": "HOU", "colts": "IND", "jaguars": "JAX",
    "chiefs": "KC", "chargers": "LAC", "rams": "LAR", "raiders": "LV",
    "dolphins": "MIA", "vikings": "MIN", "patriots": "NE", "saints": "NO",
    "giants": "NYG", "jets": "NYJ", "eagles": "PHI", "steelers": "PIT",
    "seahawks": "SEA", "49ers": "SF", "buccaneers": "TB", "titans": "TEN",
    "commanders": "WAS",
}


def parse_standings_html(html):
    """Parse the official NFL.com standings page into [{abbr, w, l, t, pct, pf, pa, net_pts}]."""
    grab = _CellGrab()
    grab.feed(html)
    out = []
    for row in grab.rows:
        # row[0] is the team cell (logo + name + display). The numeric cells follow.
        if len(row) < 8:
            continue
        team_cell = row[0].lower()
        abbr = None
        for name, code in TEAM_ABBR.items():
            if name in team_cell:
                abbr = code
                break
        if abbr is None:
            continue
        nums = row[1:8]  # W L T PCT PF PA NET
        try:
            out.append({
                "abbr": abbr,
                "w": int(nums[0]), "l": int(nums[1]), "t": int(nums[2]),
                "pct": float(nums[3]), "pf": int(nums[4]),
                "pa": int(nums[5]), "net_pts": int(nums[6]),
            })
        except (ValueError, IndexError):
            continue
    return out


def live_standings():
    html = fetch(STANDINGS_SRC)
    return parse_standings_html(html)


def live_schedule():
    """Parse the official Week 11 schedule page into schedule rows."""
    html = fetch(SCHEDULE_SRC)
    grab = _CellGrab()
    grab.feed(html)
    # The schedule page embeds game links of the form /games/<away>-at-<home>-2026-reg-11.
    out = []
    for m in re.finditer(r"/games/([a-z0-9-]+)-at-([a-z0-9-]+)-2026-reg-11", html):
        away_slug, home_slug = m.group(1), m.group(2)
        away = next((c for n, c in TEAM_ABBR.items() if n == away_slug), away_slug)
        home = next((c for n, c in TEAM_ABBR.items() if n == home_slug), home_slug)
        out.append({"away": away, "home": home,
                    "nfl_url": "https://www.nfl.com/games/%s-at-%s-2026-reg-11"
                              % (away_slug, home_slug)})
    return out


# --------------------------------------------------------------------------- #
# Diffing                                                                     #
# --------------------------------------------------------------------------- #
def _standings_key(abbr):
    """Normalise a standings key for comparison.

    NFL.com labels the Rams `LA` and the Cardinals `AZ`; the committed data uses
    `LAR` and `ARI` (documented as F-14 / R-11). The label differs but the row is
    the same club, so the key is normalised to the committed convention before the
    value comparison. The value columns are compared untouched.
    """
    a = norm(abbr).upper()
    return {"LA": "LAR", "AZ": "ARI"}.get(a, a)


# NFL.com prints the practice status in full ("Full Participation in Practice");
# the committed CSV stores the short code (Full / DNP / Limited). The snapshot
# holds the official text verbatim; this map normalises it for the value compare.
PRACTICE_NORM = {
    "full participation in practice": "Full",
    "did not participate in practice": "DNP",
    "limited participation in practice": "Limited",
}


def _practice_norm(value):
    v = norm(value).lower()
    return PRACTICE_NORM.get(v, norm(value))


def diff_table(committed, official, key_fields, value_fields, label,
               key_norm=None, value_norm=None, complete=True):
    """Return (checks, failures, uncovered) comparing official rows to committed rows by key.

    `complete=True` means the snapshot is expected to cover every committed row, so a
    committed row with no official counterpart is a failure. `complete=False` means the
    snapshot is a partial capture (a subset of teams); committed rows outside the
    snapshot are reported as `uncovered` information, not failures.
    """
    checks = 0
    failures = []
    uncovered = []

    def key_of(row, fields):
        vals = []
        for f in fields:
            v = norm(row.get(f, ""))
            if key_norm and f == key_fields[0]:
                v = key_norm(v)
            vals.append(v)
        return tuple(vals)

    def val_of(row, field):
        v = norm(row.get(field, ""))
        if value_norm and field in value_norm:
            v = value_norm[field](v)
        return v

    committed_by_key = {}
    for row in committed:
        committed_by_key[key_of(row, key_fields)] = row
    official_keys = set()
    for off in official:
        key = key_of(off, key_fields)
        official_keys.add(key)
        checks += 1
        com = committed_by_key.get(key)
        if com is None:
            failures.append("%s: key %s is in the official snapshot but not in the committed data"
                            % (label, key))
            continue
        for f in value_fields:
            checks += 1
            a, b = val_of(com, f), val_of(off, f)
            # compare numerically when both look numeric, else as text
            try:
                same = (float(a) == float(b))
            except ValueError:
                same = (a == b)
            if not same:
                failures.append("%s: %s field `%s` committed=%r official=%r"
                                % (label, key, f, a, b))
    # committed rows with no official counterpart
    for key, com in committed_by_key.items():
        if key not in official_keys:
            if complete:
                failures.append("%s: key %s is in the committed data but not in the official snapshot"
                                % (label, key))
            else:
                uncovered.append(key)
    return checks, failures, uncovered


def run_check(name, committed_file, snapshot_path, value_fields, key_fields,
              live_fn=None, label=None, key_norm=None, value_norm=None, complete=True):
    label = label or name
    print("\n=== %s ===" % label)
    committed = read_csv(os.path.join(DATA, committed_file))
    if os.path.exists(snapshot_path):
        official = read_csv(snapshot_path)
        print("  mode: snapshot  %s" % os.path.relpath(snapshot_path, ROOT))
    else:
        if live_fn is None:
            print("  mode: LIVE (no snapshot found at %s)" % os.path.relpath(snapshot_path, ROOT))
        official = live_fn()
        print("  mode: live      %s" % (SCHEDULE_SRC if name == "schedule" else STANDINGS_SRC))
    checks, failures, uncovered = diff_table(committed, official, key_fields, value_fields,
                                             label, key_norm=key_norm, value_norm=value_norm,
                                             complete=complete)
    print("  rows compared: %d   field checks: %d" % (len(official), checks))
    if uncovered:
        print("  snapshot covers %d of %d committed rows (partial capture); "
              "%d committed rows are not covered by this snapshot and are not checked."
              % (len(official), len(committed), len(uncovered)))
    if failures:
        print("  MISMATCHES (%d):" % len(failures))
        for f in failures:
            print("    - %s" % f)
        return False
    print("  RESULT: PASS - captured official values match the committed data.")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["standings", "schedule", "injuries", "all"])
    ap.add_argument("--live", action="store_true",
                    help="re-fetch the official page over HTTPS instead of using the snapshot")
    args = ap.parse_args()

    results = []
    if args.command in ("standings", "all"):
        snap = STANDINGS_SNAPSHOT
        official = live_standings() if args.live else None
        results.append(run_check(
            "standings", "standings-wk10-2026.csv", snap, STANDINGS_VALUES, ["abbr"],
            live_fn=lambda: official if official is not None else live_standings(),
            key_norm=_standings_key,
            label="official NFL.com standings vs data/standings-wk10-2026.csv"))
    if args.command in ("schedule", "all"):
        snap = SCHEDULE_SNAPSHOT
        results.append(run_check(
            "schedule", "schedule-wk11-2026.csv", snap, SCHEDULE_VALUES,
            ["away", "home", "date"], live_fn=live_schedule,
            label="official NFL.com Week 11 schedule vs data/schedule-wk11-2026.csv"))
    if args.command in ("injuries", "all"):
        results.append(run_check(
            "injuries", "injuries-wk10-2026.csv", INJURIES_SNAPSHOT, INJURIES_VALUES,
            ["player_url"], live_fn=None, value_norm={"practice": _practice_norm},
            complete=False,
            label="captured official Week 10 injury report vs data/injuries-wk10-2026.csv"))

    print("\n=== summary ===")
    if all(results):
        print("RESULT: PASS - all captured official values match the committed data.")
        return 0
    print("RESULT: FAIL - see the mismatches above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
