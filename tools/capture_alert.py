#!/usr/bin/env python3
"""
Freshness and schema watchdog for the official captures (T67).

WHY THIS EXISTS
---------------
The capture workflow records every read, but nothing before this file turned a bad
read into an alert. A failed scheduled run only notifies the workflow's creator (if notifications are enabled), and a
scheduled run that never fires leaves no record at all (flag F-89 measured a 13.0-hour
gap between two injury reads). This watchdog reads the committed manifest, decides
whether every expected source has a recent, schema-valid capture, and exits non-zero
when it does not. The scheduled workflow `.github/workflows/capture-watchdog.yml` turns
that exit status into one GitHub issue, and closes the issue when the sources recover.

WHAT IT READS
-------------
  data/captures/manifest.jsonl     the append-only record written by tools/capture_official.py

It does not fetch anything, does not write anything, and does not change the schema
or the freshness rule in tools/capture_official.py. It imports both so the two gates
cannot disagree about which read counts as valid.

STATUS PER SOURCE
-----------------
  OK                 newest valid read is within --max-hours, and the newest attempt passed
  PARTIAL            as OK, but the newest valid injury read covers fewer games than scheduled
                     (a warning only: it does not fail the check)
  STALE              newest valid read is older than --max-hours
  FAILED_LAST        the newest attempt failed (HTTP error or schema) and is newer than the newest valid read
  MISSING            no valid read has ever been recorded for the source

EXIT STATUS
-----------
  0  every expected source is OK or PARTIAL
  1  at least one source is STALE, FAILED_LAST or MISSING
  2  the manifest could not be read

USAGE
-----
  python3 tools/capture_alert.py check [--max-hours 13] [--now 2026-11-19T20:00:00Z]
                                       [--report PATH] [--kind all|injuries|depth]
"""
import argparse
import datetime as dt
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import capture_official as capture  # noqa: E402

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def parse_stamp(text):
    return dt.datetime.strptime(text, TIME_FORMAT)


def is_valid_read(entry):
    """The same test capture_official.freshness applies to a read."""
    return bool(entry.get("schema_ok") and entry.get("sha256")
                and entry.get("http_status") == 200 and not entry.get("error"))


def evaluate(entries, expected, max_hours, now):
    """Return one dict per expected source. Pure function: no clock, no I/O."""
    by_kind = {}
    for entry in entries:
        kind = entry.get("kind")
        if kind not in expected:
            continue
        try:
            stamp = parse_stamp(entry["fetched_utc"])
        except (KeyError, TypeError, ValueError):
            continue
        by_kind.setdefault(kind, []).append((stamp, entry))

    rows = []
    for source in expected:
        reads = sorted(by_kind.get(source, []), key=lambda pair: pair[0])
        valid = [pair for pair in reads if is_valid_read(pair[1])]
        last_valid = valid[-1] if valid else None
        last_attempt = reads[-1] if reads else None
        row = {
            "source": source,
            "last_attempt_utc": capture.iso(last_attempt[0]) if last_attempt else None,
            "last_attempt_ok": bool(last_attempt and is_valid_read(last_attempt[1])),
            "last_valid_utc": capture.iso(last_valid[0]) if last_valid else None,
            "age_hours": None,
            "coverage": None,
            "status": None,
            "detail": "",
        }
        if last_valid is None:
            row["status"] = "MISSING"
            row["detail"] = "no schema-valid read has ever been recorded"
            rows.append(row)
            continue

        age = (now - last_valid[0]).total_seconds() / 3600.0
        row["age_hours"] = round(age, 1)
        schema = last_valid[1].get("schema") or {}
        row["coverage"] = schema.get("coverage")

        if last_attempt is not None and last_attempt[0] > last_valid[0] and not row["last_attempt_ok"]:
            row["status"] = "FAILED_LAST"
            row["detail"] = ("newest attempt %s failed the gate (HTTP %s, schema_ok false); "
                             "the newest valid read is %s" % (
                                 row["last_attempt_utc"], last_attempt[1].get("http_status"),
                                 row["last_valid_utc"]))
        elif age < 0 or age > max_hours:
            row["status"] = "STALE"
            row["detail"] = "newest valid read is %.1f h old; limit %.1f h" % (age, max_hours)
        elif row["coverage"] == "partial":
            row["status"] = "PARTIAL"
            row["detail"] = ("newest valid read is fresh but covers only %s of %s scheduled games"
                             % (schema.get("games_published"), schema.get("games_scheduled")))
        else:
            row["status"] = "OK"
            row["detail"] = "newest valid read is %.1f h old; limit %.1f h" % (age, max_hours)
        rows.append(row)
    return rows


FAILING = ("STALE", "FAILED_LAST", "MISSING")


def render_report(rows, max_hours, now):
    failing = [r for r in rows if r["status"] in FAILING]
    partial = [r for r in rows if r["status"] == "PARTIAL"]
    lines = ["## Official capture alert",
             "",
             "Checked at %s by `tools/capture_alert.py check --max-hours %g`." % (capture.iso(now), max_hours),
             "",
             "**%d of %d sources failing; %d partial; %d ok.**" % (
                 len(failing), len(rows), len(partial),
                 sum(1 for r in rows if r["status"] == "OK")),
             ""]
    if failing:
        lines += ["### Failing sources", "",
                  "| Source | Status | Newest valid read (UTC) | Newest attempt (UTC) | Detail |",
                  "|---|---|---|---|---|"]
        for r in failing:
            lines.append("| %s | %s | %s | %s | %s |" % (
                r["source"], r["status"], r["last_valid_utc"] or "none",
                r["last_attempt_utc"] or "none", r["detail"]))
        lines.append("")
    if partial:
        lines += ["### Partial coverage (warning only)", ""]
        for r in partial:
            lines.append("- %s: %s" % (r["source"], r["detail"]))
        lines.append("")
    lines += ["Capture manifest: https://github.com/karagemop466-tech/X4/blob/main/data/captures/manifest.jsonl",
              "Workflow: https://github.com/karagemop466-tech/X4/actions/workflows/capture.yml",
              "",
              "_This issue is opened and updated by `.github/workflows/capture-watchdog.yml` and closed automatically when every source is fresh again. Nothing was fetched or changed by the watchdog._",
              ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("--max-hours", type=float, default=13.0)
    p.add_argument("--now", default=None, help="UTC time as YYYY-MM-DDTHH:MM:SSZ (tests and replays)")
    p.add_argument("--report", default=None, help="write a markdown report here (issue body)")
    p.add_argument("--kind", default="all", choices=["all", "injuries", "depth"])
    args = ap.parse_args(argv)

    try:
        entries = capture.read_manifest()
    except (OSError, ValueError) as exc:
        print("cannot read the capture manifest: %s" % exc)
        return 2
    now = parse_stamp(args.now) if args.now else capture.utc_now().replace(tzinfo=None)
    expected = capture.expected_kinds(args.kind)
    rows = evaluate(entries, expected, args.max_hours, now)

    for r in rows:
        print("%-12s %-12s last_valid=%s age_h=%s coverage=%s %s" % (
            r["source"], r["status"], r["last_valid_utc"], r["age_hours"], r["coverage"] or "-", r["detail"]))
    failing = [r for r in rows if r["status"] in FAILING]
    print("sources checked: %d; failing: %d; partial: %d" % (
        len(rows), len(failing), sum(1 for r in rows if r["status"] == "PARTIAL")))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(render_report(rows, args.max_hours, now))
    if failing:
        print("CAPTURE ALERT: %d source(s) need attention" % len(failing))
        return 1
    print("capture watchdog: every source is fresh and schema-valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
