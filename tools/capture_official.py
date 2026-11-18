#!/usr/bin/env python3
"""
Immutable, timestamped captures of official NFL and club pages.

WHY THIS EXISTS
---------------
A committed table is a single reading. Practice designations move Wednesday to
Saturday, and a backtest cannot replay what was known at kickoff from one reading.
This tool keeps every distinct raw capture of the official pages, with its SHA-256,
its UTC fetch time and a schema check, so each later statement can point at the
exact bytes it came from.

WHAT IT WRITES
--------------
  data/captures/<kind>/<UTC stamp>_<sha12>.html.gz   raw bytes, gzip-compressed
  data/captures/manifest.jsonl                       append-only, one line per run

A new file is written only when the bytes differ from the previous capture of the
same page. Every run, changed or not, appends a manifest line, so freshness can be
read from the manifest even when nothing moved.

COMMANDS
--------
  fetch   [--kind injuries|depth|all]   fetch, check the schema, store, append
  verify                                recompute every stored hash; fail on any mismatch
  freshness --max-hours N               fail if the newest manifest line is older than N hours

EXIT STATUS
-----------
  0  success
  1  verification or freshness failure (hash mismatch, stale capture)
  2  fetch or schema failure - the page changed shape or could not be read; the
     workflow fails so the failure is visible rather than a silent gap

SOURCES
-------
  injuries  https://www.nfl.com/injuries/           (official NFL.com injury report)
  depth     each club's official depth-chart page   (CHART_URL in tools/depth.py)

NOTE ON VERIFICATION
--------------------
The schema check below is written against the markers the official report page
carries (section headings, the "Practice Status" and "Game Status" columns, and one
player link per row). It has not yet been run against the live HTML from inside
this sandbox, which cannot reach nfl.com; the first scheduled run on GitHub's
runners is the test, and a schema failure stops the run rather than storing an
unchecked page.

Usage: python3 tools/capture_official.py fetch --kind all
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP_DIR = os.path.join(ROOT, "data", "captures")
MANIFEST = os.path.join(CAP_DIR, "manifest.jsonl")
UA = "Mozilla/5.0 (compatible; X4-capture/1.0; +https://github.com/karagemop466-tech/X4)"
INJURY_URL = "https://www.nfl.com/injuries/"


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_manifest():
    if not os.path.exists(MANIFEST):
        return []
    with open(MANIFEST, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_manifest(entry):
    os.makedirs(CAP_DIR, exist_ok=True)
    with open(MANIFEST, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


def schema_injuries(raw):
    """Return (ok, detail). Markers the official report page must carry."""
    text = raw.decode("utf-8", errors="replace")
    heading = re.search(r"Injuries\s*-\s*WEEK\s*(\d+)", text, re.I)
    practice = len(re.findall(r"Practice Status", text))
    game = len(re.findall(r"Game Status", text))
    players = len(re.findall(r"nfl\.com/players/", text))
    detail = {"week": heading.group(1) if heading else None,
              "practice_status_headers": practice, "game_status_headers": game,
              "player_links": players}
    ok = bool(heading) and practice >= 28 and game >= 28 and players >= 250
    return ok, detail


def schema_depth(raw):
    text = raw.decode("utf-8", errors="replace")
    tables = len(re.findall(r"<table", text, re.I))
    ok = tables >= 1 and len(raw) > 2000
    return ok, {"tables": tables, "bytes": len(raw)}


def store(kind, url, raw, status, schema_ok, detail, previous):
    now = utc_now()
    digest = sha256(raw)
    last = previous[-1] if previous else None
    base = {"kind": kind, "url": url, "fetched_utc": iso(now), "http_status": status,
            "bytes": len(raw), "sha256": digest, "schema_ok": schema_ok, "schema": detail}
    same_kind = [e for e in previous if e.get("kind") == kind and e.get("file")]
    if same_kind and same_kind[-1]["sha256"] == digest:
        base.update({"file": same_kind[-1]["file"], "changed": False})
        return base
    folder = os.path.join(CAP_DIR, kind)
    os.makedirs(folder, exist_ok=True)
    name = "%s_%s.html.gz" % (now.strftime("%Y%m%dT%H%M%SZ"), digest[:12])
    rel = os.path.relpath(os.path.join(folder, name), ROOT)
    with open(os.path.join(ROOT, rel), "wb") as f:
        f.write(gzip.compress(raw, mtime=0))
    base.update({"file": rel, "changed": True, "previous_sha256": last["sha256"] if last else None})
    return base


def fetch(kind):
    previous = read_manifest()
    targets = []
    if kind in ("injuries", "all"):
        targets.append(("injuries", INJURY_URL, schema_injuries))
    if kind in ("depth", "all"):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import depth as depth_module  # CHART_URL: each club's official depth-chart page
        for club in sorted(depth_module.CHART_URL):
            targets.append(("depth/" + club, depth_module.CHART_URL[club], schema_depth))
    failed = False
    for label, url, schema in targets:
        kind_name = label
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            # A club whose official page is not a usable URL (e.g. the Texans publish their
            # depth chart as an image, so depth.CHART_URL stores the empty string) must not
            # abort the whole capture: urllib.request.Request raises ValueError, which the
            # except clause below does not catch, and every later target is lost. Skip it
            # loudly instead — manifest line, stderr note, non-zero exit — and keep capturing
            # the other clubs.
            print("FETCH SKIPPED %s: no usable URL (%r)" % (label, url), file=sys.stderr)
            append_manifest({"kind": kind_name, "url": url or "", "fetched_utc": iso(utc_now()),
                             "http_status": None, "error": "no usable URL in source register",
                             "schema_ok": False})
            failed = True
            continue
        try:
            status, raw = http_get(url)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            print("FETCH FAILED %s %s: %s" % (label, url, exc))
            append_manifest({"kind": kind_name, "url": url, "fetched_utc": iso(utc_now()),
                             "http_status": None, "error": str(exc), "schema_ok": False})
            failed = True
            continue
        ok, detail = schema(raw)
        entry = store(kind_name, url, raw, status, ok, detail, previous)
        append_manifest(entry)
        previous.append(entry)
        print("%-12s %s status=%s bytes=%d schema_ok=%s changed=%s" % (
            label, url, status, len(raw), ok, entry["changed"]))
        if not ok:
            print("  SCHEMA FAILURE %s: %s" % (label, detail))
            failed = True
    return 2 if failed else 0


def verify():
    bad = 0
    checked = 0
    for e in read_manifest():
        f = e.get("file")
        if not f:
            continue
        checked += 1
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            print("MISSING %s" % f)
            bad += 1
            continue
        with gzip.open(path, "rb") as g:
            raw = g.read()
        if sha256(raw) != e["sha256"]:
            print("HASH MISMATCH %s" % f)
            bad += 1
    print("verified %d stored captures; %d failure(s)" % (checked, bad))
    return 1 if bad else 0


def freshness(max_hours):
    entries = read_manifest()
    if not entries:
        print("no captures recorded yet")
        return 1
    newest = max(dt.datetime.strptime(e["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ") for e in entries)
    age = (utc_now().replace(tzinfo=None) - newest).total_seconds() / 3600.0
    print("newest capture %s (%.1f hours ago); limit %.1f" % (iso(newest.replace(tzinfo=dt.timezone.utc)), age, max_hours))
    return 0 if age <= max_hours else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fetch")
    p.add_argument("--kind", default="injuries", choices=["injuries", "depth", "all"])
    sub.add_parser("verify")
    p = sub.add_parser("freshness")
    p.add_argument("--max-hours", type=float, default=30.0)
    args = ap.parse_args(argv)
    if args.cmd == "fetch":
        return fetch(args.kind)
    if args.cmd == "verify":
        return verify()
    return freshness(args.max_hours)


if __name__ == "__main__":
    sys.exit(main())
