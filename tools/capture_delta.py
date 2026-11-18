#!/usr/bin/env python3
"""
Cell-level delta between a stored official injury-report capture and the committed dataset.

WHY THIS EXISTS
---------------
data/captures/ holds the raw bytes of every official injury-report read. The brief asks for
the DELTA between reads, not the level. This tool reads one stored capture (by default the
newest schema-valid injuries capture in data/captures/manifest.jsonl), extracts every row of
the official report's tables, maps the official wording onto the dataset's codes, and reports
each cell that differs from data/injuries-wk10-2026.csv.

RULES (no inference)
--------------------
* Team: the club name printed above each table (a nickname such as "Commanders") is matched
  to the official standings file by its last word. A nickname that matches no club is reported
  as UNMAPPED, never guessed.
* Practice wording is mapped only from the three exact official phrases:
    "Full Participation in Practice" -> Full, "Limited Participation in Practice" -> Limited,
    "Did Not Participate In Practice" -> DNP, blank -> blank. Anything else is UNKNOWN.
* Game status is compared as printed (blank, Questionable, Doubtful, Out).
* Keys are (team, player). A key on one side only is reported as ADDED or DROPPED.

USAGE
-----
    X4_CAPTURE_RAW_DIR=/private/store python3 tools/capture_delta.py      # newest valid capture
    X4_CAPTURE_RAW_DIR=/private/store python3 tools/capture_delta.py <f.gz>  # a specific capture
    python3 tools/capture_delta.py --write         # also write the delta CSV for the record

Exit status: 0 = reported (see the summary; drift is data, not an error);
             2 = the capture could not be parsed to the expected shape.
"""
import csv
import gzip
import json
import os
import re
import sys
import hashlib
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMITTED = os.path.join(ROOT, "data", "injuries-wk10-2026.csv")
STANDINGS = os.path.join(ROOT, "data", "standings-wk10-2026.csv")
MANIFEST = os.path.join(ROOT, "data", "captures", "manifest.jsonl")
OUT = os.path.join(ROOT, "research", "verification", "capture-delta-2026-11-18.csv")

PRACTICE_WORDS = {
    "Full Participation in Practice": "Full",
    "Limited Participation in Practice": "Limited",
    "Did Not Participate In Practice": "DNP",
    "": "",
}


class _Report(HTMLParser):
    """Collects (club nickname, cells) for every body row of every table in the report."""

    def __init__(self):
        super().__init__()
        self.rows = []          # list of (nickname_or_None, [cell texts])
        self.nick = None        # latest club nickname seen above a table
        self.in_nick = False
        self.in_th = False
        self.row = None
        self.cell = None
        self.header_row = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag == "div" and cls.startswith("d3-o-section-sub-title"):
            self.in_nick = True
        if tag == "tr":
            self.row = []
            self.header_row = False
        if tag == "th" and self.row is not None:
            self.header_row = True
        if tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag == "div" and self.in_nick:
            self.in_nick = False
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            if self.row and not self.header_row and any(self.row):
                self.rows.append((self.nick, self.row))
            self.row = None

    def handle_data(self, data):
        if self.in_nick:
            text = data.strip()
            if text:
                self.nick = text
        if self.cell is not None:
            self.cell.append(data)


def locate(entry):
    """The private raw copy of a manifest entry, looked up by kind and file name in the owner's
    store (X4_CAPTURE_RAW_DIR). Returns None when the bytes are not in this environment."""
    raw_dir = os.environ.get("X4_CAPTURE_RAW_DIR")
    if not raw_dir:
        return None
    path = os.path.join(raw_dir, entry["kind"], os.path.basename(entry["file"]))
    return path if os.path.exists(path) else None


def latest_valid_capture():
    best = None
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            e = json.loads(line)
            if e.get("kind") == "injuries" and e.get("schema_ok") and e.get("file") and e.get("http_status") == 200:
                best = e
    if best is None:
        raise SystemExit("no schema-valid injuries capture in the manifest")
    return best


def nickname_map():
    out = {}
    with open(STANDINGS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["team"].split()[-1]] = r["abbr"]
    return out


def parse(path):
    with gzip.open(path, "rb") as f:
        raw = f.read()
    rep = _Report()
    rep.feed(raw.decode("utf-8", errors="replace"))
    players = []
    for nick, cells in rep.rows:
        if len(cells) != 5:
            continue
        name, pos, inj, prac, game = cells
        players.append({"nick": nick, "player": name, "pos": pos, "injuries": inj,
                        "practice_raw": prac, "game_status": game})
    return players, hashlib.sha256(raw).hexdigest()


def main(argv):
    write = "--write" in argv
    args = [a for a in argv if a != "--write"]
    entry = None
    if args:
        path = os.path.abspath(args[0])
        file_rel = os.path.relpath(path, ROOT)
        captured = "(argument)"
    else:
        entry = latest_valid_capture()
        path = locate(entry)
        if path is None:
            raise SystemExit("raw bytes for %s are not in this environment; set X4_CAPTURE_RAW_DIR "
                             "to the private store (raw bytes are never committed)" % entry.get("file"))
        file_rel = "private-store:" + entry["file"]
        captured = entry["fetched_utc"]
    players, sha = parse(path)
    if len(players) < 250:
        print("PARSE FAILURE: %d player rows (expected about 347)" % len(players))
        return 2
    nicks = nickname_map()
    unmapped = sorted({p["nick"] for p in players if p["nick"] not in nicks})
    captured_rows = {}
    unknown_practice = []
    for p in players:
        team = nicks.get(p["nick"], "UNMAPPED:%s" % p["nick"])
        prac = PRACTICE_WORDS.get(p["practice_raw"])
        if prac is None:
            unknown_practice.append(p["practice_raw"])
            prac = "UNKNOWN:" + p["practice_raw"]
        captured_rows[(team, p["player"])] = {"pos": p["pos"], "injuries": p["injuries"],
                                              "practice": prac, "game_status": p["game_status"]}

    with open(COMMITTED, encoding="utf-8") as f:
        committed = {(r["team"], r["player"]): r for r in csv.DictReader(f)}

    diffs = []
    fields = ("pos", "injuries", "practice", "game_status")
    for key in sorted(set(committed) | set(captured_rows)):
        if key not in committed:
            diffs.append((key[0], key[1], "row", "", "ADDED"))
            continue
        if key not in captured_rows:
            diffs.append((key[0], key[1], "row", "present", "DROPPED"))
            continue
        for fld in fields:
            cv = committed[key][fld]
            kv = captured_rows[key][fld]
            if cv != kv:
                diffs.append((key[0], key[1], fld, cv, kv))

    cells_compared = len(set(committed) & set(captured_rows)) * len(fields)
    print("capture: %s (sha256 %s, fetched %s)" % (file_rel, sha[:16], captured))
    print("official rows read: %d across %d clubs; committed rows: %d; keys in both: %d"
          % (len(players), len({k[0] for k in captured_rows}), len(committed),
             len(set(committed) & set(captured_rows))))
    print("cells compared: %d; cells that differ: %d" % (cells_compared, len(diffs)))
    print("unmapped club nicknames: %s" % (unmapped or "none"))
    print("unknown practice wording: %s" % (sorted(set(unknown_practice)) or "none"))
    for d in diffs[:60]:
        print("  %-4s %-24s %-10s committed=%r captured=%r" % (d[0], d[1], d[2], d[3], d[4]))
    if len(diffs) > 60:
        print("  ... %d more" % (len(diffs) - 60))

    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["capture_file", "capture_sha256", "captured_utc", "team", "player", "field",
                        "committed_value", "captured_value", "source_url"])
            for d in diffs:
                w.writerow([file_rel, sha, captured, d[0], d[1], d[2], d[3], d[4],
                            "https://www.nfl.com/injuries/league/2026/reg10"])
        print("wrote %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
