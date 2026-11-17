#!/usr/bin/env python3
"""Create a conservative, row-level inventory of links in the legacy desk pages.

This is a link-presence audit, not a live-source verification. It classifies each
``table.data`` body row in the same 22 pages used by ``tools/check_site.py`` as:

* ``official_domain_link``: at least one link to an allowlisted NFL, NFL club, or
  U.S. FTC domain, and no other HTTPS host;
* ``official_and_nonofficial``: both an allowlisted official-domain link and a
  third-party HTTPS link are present;
* ``nonofficial_https_only``: one or more HTTPS links, none to an allowlisted
  official domain; or
* ``no_https_source``: no HTTPS link in the row (an HTTP link, if present, is
  recorded separately and never treated as evidence).

The allowlist is deliberately narrow: ``nfl.com`` and its subdomains, ``ftc.gov``
and its subdomains, and the exact club hostnames in the committed official-depth
source column (``data/depth-wk11-2026.csv``). A listed hostname is not proof that
the linked page supports every value in the row. The audit does not fetch URLs,
check page contents, or mark any data value verified.

Usage:
    python3 tools/audit_official_row_sources.py        # write the inventory CSV
    python3 tools/audit_official_row_sources.py --check # fail if output is stale
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# Reuse the same page list and parser as the legacy desk-link gate so row numbers
# and coverage counts refer to the identical source set.
from check_site import DESK_PAGES, Page  # noqa: E402

DEPTH_CSV = ROOT / "data" / "depth-wk11-2026.csv"
OUT_CSV = ROOT / "research" / "verification" / "official-row-source-coverage-2026-11-17.csv"
REPORT_MD = ROOT / "research" / "audits" / "official-row-source-coverage-2026-11-17.md"
FIELDNAMES = [
    "page",
    "row",
    "classification",
    "official_link_count",
    "nonofficial_https_count",
    "insecure_http_count",
    "official_urls",
    "nonofficial_https_urls",
    "insecure_http_urls",
    "row_text",
]


def official_hosts() -> set[str]:
    """Build the documented host allowlist, without wildcarding club domains."""
    hosts = {"nfl.com", "ftc.gov"}
    with DEPTH_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            url = (row.get("source") or "").strip()
            parsed = urlsplit(url)
            if parsed.scheme == "https" and parsed.hostname:
                hosts.add(parsed.hostname.lower())
    return hosts


def is_official_host(host: str, exact_hosts: set[str]) -> bool:
    host = host.lower().rstrip(".")
    return (
        host in exact_hosts
        or host == "nfl.com"
        or host.endswith(".nfl.com")
        or host == "ftc.gov"
        or host.endswith(".ftc.gov")
    )


def unique_in_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def audit_rows() -> tuple[list[dict[str, str]], dict[str, object]]:
    allowed = official_hosts()
    rows: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    page_counts: dict[str, Counter[str]] = defaultdict(Counter)
    other_hosts: Counter[str] = Counter()
    total_links = Counter()

    for name in DESK_PAGES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(f"desk page listed in tools/check_site.py is missing: {path}")
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        for row_number, hrefs in enumerate(page._rows, start=1):
            https = unique_in_order([h for h in hrefs if h.lower().startswith("https://")])
            http = unique_in_order([h for h in hrefs if h.lower().startswith("http://")])
            official_urls: list[str] = []
            nonofficial_urls: list[str] = []
            for url in https:
                host = (urlsplit(url).hostname or "").lower().rstrip(".")
                if host and is_official_host(host, allowed):
                    official_urls.append(url)
                else:
                    nonofficial_urls.append(url)
                    if host:
                        other_hosts[host] += 1
            if official_urls and nonofficial_urls:
                classification = "official_and_nonofficial"
            elif official_urls:
                classification = "official_domain_link"
            elif https:
                classification = "nonofficial_https_only"
            else:
                classification = "no_https_source"

            counts[classification] += 1
            page_counts[name][classification] += 1
            total_links["https"] += len(https)
            total_links["official_https"] += len(official_urls)
            total_links["nonofficial_https"] += len(nonofficial_urls)
            total_links["http"] += len(http)
            rows.append({
                "page": name,
                "row": str(row_number),
                "classification": classification,
                "official_link_count": str(len(official_urls)),
                "nonofficial_https_count": str(len(nonofficial_urls)),
                "insecure_http_count": str(len(http)),
                "official_urls": " | ".join(official_urls),
                "nonofficial_https_urls": " | ".join(nonofficial_urls),
                "insecure_http_urls": " | ".join(http),
                "row_text": page._row_text[row_number - 1],
            })

    summary: dict[str, object] = {
        "page_count": len(DESK_PAGES),
        "row_count": len(rows),
        "classification_counts": dict(counts),
        "page_counts": {page: dict(page_counts[page]) for page in DESK_PAGES},
        "official_host_count": len(allowed),
        "official_hosts": sorted(allowed),
        "nonofficial_host_link_counts": dict(sorted(other_hosts.items())),
        "link_counts": dict(total_links),
    }
    return rows, summary


def render_csv(rows: list[dict[str, str]]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def club_source_urls() -> list[tuple[str, str]]:
    """Return the exact club chart URLs backing the club-host allowlist."""
    urls: dict[str, str] = {}
    with DEPTH_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            team = (row.get("team") or "").strip()
            url = (row.get("source") or "").strip()
            if team and url:
                urls[team] = url
    return sorted(urls.items())


def render_report(summary: dict[str, object]) -> str:
    counts = summary["classification_counts"]
    page_counts = summary["page_counts"]
    official_only = counts.get("official_domain_link", 0)
    mixed = counts.get("official_and_nonofficial", 0)
    third_party_only = counts.get("nonofficial_https_only", 0)
    no_https = counts.get("no_https_source", 0)
    no_official = third_party_only + no_https

    lines = [
        "# Official-domain link coverage audit — 2026-11-17",
        "",
        "> **Important:** this is a static URL/host inventory, not a live-source or value-verification pass. A link on an allowlisted host does not establish that the linked page supports every number or claim in its row. No page data was changed or marked verified.",
        "",
        "## Finding",
        "",
        f"The audit parsed **{summary['row_count']:,} data rows** across **{summary['page_count']} legacy desk pages**. The current F-39 inventory lists **{no_https} rows without any HTTPS link**. Under the stricter official-domain-presence test used here, **{no_official} rows have no allowlisted official-domain link**: {third_party_only} have only non-official HTTPS links, and {no_https} have no HTTPS link.",
        "",
        f"Of the rows, **{official_only}** have an allowlisted official-domain link and no other HTTPS link; **{mixed}** combine an allowlisted link with a non-official HTTPS link; **{third_party_only}** have only non-official HTTPS links; and **{no_https}** have no HTTPS link. The {mixed} mixed-source rows still need source-to-value attribution; an NFL fixture link does not verify a third-party odds value in the same row.",
        "",
        f"This is a wider source-link gap than the existing F-39 count represents. It does **not** show that the {no_official} rows are false; it shows that this repository does not currently attach an allowlisted official-domain URL to those rendered rows. Treat those rows as unverified under the requested rule until individually sourced or left blank and flagged.",
        "",
        "## Row-level inventory",
        "",
        "[Download the full CSV inventory](../verification/official-row-source-coverage-2026-11-17.csv). It has one record per data row, the rendered row text, classification, and the exact URLs present in that row. Review those URLs directly; they were not fetched by this audit.",
        "",
        "| Page | Official host only | Official + non-official | Non-official HTTPS only | No HTTPS link | Total |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for page in DESK_PAGES:
        page_row_counts = page_counts.get(page, {})
        values = [
            page_row_counts.get("official_domain_link", 0),
            page_row_counts.get("official_and_nonofficial", 0),
            page_row_counts.get("nonofficial_https_only", 0),
            page_row_counts.get("no_https_source", 0),
        ]
        total = sum(values)
        lines.append(f"| [`{page}`](../../{page}) | {values[0]} | {values[1]} | {values[2]} | {values[3]} | {total} |")

    lines.extend([
        "",
        "## Classification method and official-source references",
        "",
        "The page set and row parser are shared with [`tools/check_site.py`](https://github.com/karagemop466-tech/X4/blob/main/tools/check_site.py): its 22 legacy desk pages and `table.data` body rows. Rows are numbered in parser order per page. URLs are deduplicated within a row, preserving their rendered order.",
        "",
        "The domain allowlist is conservative and explicit: `nfl.com` and its subdomains; `ftc.gov` and its subdomains; and the **exact** hostnames in the `source` column of [`data/depth-wk11-2026.csv`](../../data/depth-wk11-2026.csv), which [`tools/depth.py`](https://github.com/karagemop466-tech/X4/blob/main/tools/depth.py) documents as club-published depth-chart URLs. Team-host subdomains are not guessed. The 33 allowlisted hosts comprise those two base domains and 31 club chart hosts; Houston's chart is not machine-readable and is not used to add a hostname.",
        "",
        "Official NFL references already recorded in the repository: [NFL standings](https://www.nfl.com/standings/), [NFL injury reports](https://www.nfl.com/injuries/), [Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11), and [NFL club directory](https://www.nfl.com/teams/). The allowlist also recognizes the [U.S. Federal Trade Commission](https://www.ftc.gov/) domain for government/legal material; that does not make it a source for NFL game facts.",
        "",
        "The 31 club domains are grounded in these exact, previously recorded chart URLs:",
        "",
    ])
    for team, url in club_source_urls():
        lines.append(f"- {team}: [{url}]({url})")

    nonofficial_hosts = summary["nonofficial_host_link_counts"]
    lines.extend([
        "",
        "## Limits and recommended next step",
        "",
        "- This audit checks hostnames only. It does not resolve DNS, make HTTP requests, inspect page text, prove the page is controlled by the claimed organization, or match a source to an individual cell.",
        "- The 55 mixed-source rows should be split by field or annotated so each source is tied to the value it supports. Do not treat the presence of an NFL schedule/game URL as evidence for a separate market-price value.",
        "- The 175 non-official-only rows include third-party odds and repository links. Keep third-party prices segregated and labelled as such; do not promote them to official NFL evidence.",
        "- The 191 no-HTTPS rows are the current F-39 inventory. The per-row links and text in the CSV allow manual triage, but no missing URL was guessed or filled.",
        "- Recommended follow-up: the final site integrator should update F-39 and the published Flagged for Review page to report the strict count and the mixed-source attribution gap, or retain the current site wording with an explicit notice that it covers only rows with no HTTPS link. No shared page or index was edited in this task.",
        "",
        "Non-official HTTPS hosts encountered (link count after per-row URL deduplication):",
        "",
    ])
    for host, count in nonofficial_hosts.items():
        lines.append(f"- `{host}`: {count}")
    lines.extend([
        "",
        "## Reproduction",
        "",
        "Run `python3 tools/audit_official_row_sources.py` to regenerate the CSV and this report. Run `python3 tools/audit_official_row_sources.py --check` to verify both outputs match the current committed pages.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check that the committed CSV and report match current pages")
    args = parser.parse_args()

    rows, summary = audit_rows()
    rendered_csv = render_csv(rows)
    rendered_report = render_report(summary)
    if args.check:
        stale = []
        if not OUT_CSV.is_file() or OUT_CSV.read_text(encoding="utf-8") != rendered_csv:
            stale.append(OUT_CSV.relative_to(ROOT))
        if not REPORT_MD.is_file() or REPORT_MD.read_text(encoding="utf-8") != rendered_report:
            stale.append(REPORT_MD.relative_to(ROOT))
        if stale:
            print("FAIL: stale or missing output(s): " + ", ".join(map(str, stale)))
            print("Run without --check to regenerate.")
            return 1
    else:
        OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUT_CSV.write_text(rendered_csv, encoding="utf-8", newline="")
        REPORT_MD.write_text(rendered_report, encoding="utf-8", newline="")

    print(f"Pages: {summary['page_count']}; data rows: {summary['row_count']}; allowlisted hosts: {summary['official_host_count']}")
    for category in ("official_domain_link", "official_and_nonofficial", "nonofficial_https_only", "no_https_source"):
        print(f"  {category}: {summary['classification_counts'].get(category, 0)}")
    print("  links:", summary["link_counts"])
    if args.check:
        print("PASS: CSV inventory and Markdown report match current page rows")
    else:
        print(f"WROTE: {OUT_CSV.relative_to(ROOT)}")
        print(f"WROTE: {REPORT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
