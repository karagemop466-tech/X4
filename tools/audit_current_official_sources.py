#!/usr/bin/env python3
"""Audit current desk-table row links against the repository's documented host allowlist.

This is a static link/hostname inventory, not a live fetch or semantic source check.
It must never be interpreted as proof that an official page supports a cell value.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_site import DESK_PAGES, Page  # noqa: E402

CSV_OUT = ROOT / "research/verification/official-row-source-coverage-current-2026-11-19.csv"
MD_OUT = ROOT / "research/audits/official-row-source-coverage-current-2026-11-19.md"
FIELDS = ["page", "row", "classification", "verification_status", "official_urls", "nonofficial_https_urls", "insecure_http_urls", "row_text"]


def allowlist() -> set[str]:
    hosts = {"nfl.com", "ftc.gov"}
    with (ROOT / "data/depth-wk11-2026.csv").open(encoding="utf-8", newline="") as f:
        for record in csv.DictReader(f):
            parsed = urlsplit((record.get("source") or "").strip())
            if parsed.scheme == "https" and parsed.hostname:
                hosts.add(parsed.hostname.lower())
    return hosts


def official(host: str, exact: set[str]) -> bool:
    host = host.lower().rstrip(".")
    return host in exact or host.endswith(".nfl.com") or host.endswith(".ftc.gov")


def main() -> int:
    exact = allowlist()
    all_rows: list[dict[str, str]] = []
    page_counts: dict[str, Counter] = defaultdict(Counter)
    counts: Counter = Counter()
    for name in DESK_PAGES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(path)
        parsed_page = Page()
        parsed_page.feed(path.read_text(encoding="utf-8"))
        for n, hrefs in enumerate(parsed_page._rows, 1):
            links = list(dict.fromkeys(hrefs))
            https = [u for u in links if u.lower().startswith("https://")]
            http = [u for u in links if u.lower().startswith("http://")]
            good = [u for u in https if (urlsplit(u).hostname and official(urlsplit(u).hostname or "", exact))]
            other = [u for u in https if u not in good]
            if good and other:
                cls = "official_and_nonofficial"
            elif good:
                cls = "official_domain_link_only"
            elif other:
                cls = "nonofficial_https_only"
            else:
                cls = "no_https_link"
            counts[cls] += 1
            page_counts[name][cls] += 1
            review_status = {
                "official_domain_link_only": "UNVERIFIED: official host present; value support not checked",
                "official_and_nonofficial": "UNVERIFIED: mixed sources; field attribution not checked",
                "nonofficial_https_only": "UNVERIFIED: no allowlisted official-host link in row",
                "no_https_link": "UNVERIFIED: no HTTPS source in row",
            }[cls]
            all_rows.append({
                "page": name,
                "row": str(n),
                "classification": cls,
                "verification_status": review_status,
                "official_urls": " | ".join(good),
                "nonofficial_https_urls": " | ".join(other),
                "insecure_http_urls": " | ".join(http),
                "row_text": parsed_page._row_text[n - 1],
            })

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    total = len(all_rows)
    official_only = counts["official_domain_link_only"]
    mixed = counts["official_and_nonofficial"]
    nonofficial_only = counts["nonofficial_https_only"]
    no_https = counts["no_https_link"]
    lines = [
        "# Current desk-row official-domain link inventory — 2026-11-19", "",
        "> **Scope and limit:** this is a static inventory of URLs rendered in each current desk table row. It does not fetch source pages, check source ownership, or establish that a cited page supports a particular value. No value is marked verified by this report.", "",
        "## Finding", "",
        f"The audit parsed **{total:,} data rows** across **{len(DESK_PAGES)} current desk pages**. **{official_only:,}** rows have allowlisted official-domain HTTPS links only; **{mixed:,}** have both official-domain and non-official HTTPS links; **{nonofficial_only:,}** have non-official HTTPS links only; and **{no_https:,}** have no HTTPS link. **{mixed + nonofficial_only + no_https:,}** rows contain non-official URLs or no HTTPS URL. This hostname classification does not establish field-level provenance for any row, including rows with official-domain links only.",  "",
        "A link to an NFL schedule in the same row as a third-party odds value does not support the odds. A repository link supports provenance to a project artifact, not an official NFL fact. For any claim/value not directly supported by a suitable source, the value must remain unverified or blank and be flagged; this audit does not infer a missing citation.", "",
        "## Row-level inventory", "",
        "The CSV below contains one record for every parsed row, its rendered text, classification and exact URLs. Empty `official_urls` means this audit found no allowlisted official-domain URL in that row; it is not proof the underlying fact is false.", "",
        "[Download row-level CSV](../verification/official-row-source-coverage-current-2026-11-19.csv)", "",
        "| Desk page | Official only | Official + other | Other HTTPS only | No HTTPS | Rows |", "|---|---:|---:|---:|---:|---:|",
    ]
    for name in DESK_PAGES:
        c = page_counts[name]
        lines.append(f"| [`{name}`](../../{name}) | {c['official_domain_link_only']} | {c['official_and_nonofficial']} | {c['nonofficial_https_only']} | {c['no_https_link']} | {sum(c.values())} |")
    lines += [
        "", "## Classification policy", "",
        "The desk row parser and page list are imported from [`tools/check_site.py`](https://github.com/karagemop466-tech/X4/blob/main/tools/check_site.py). The official-host allowlist is `nfl.com`/subdomains, `ftc.gov`/subdomains, and the exact club hostnames appearing in the committed depth-chart source column in [`data/depth-wk11-2026.csv`](../../data/depth-wk11-2026.csv). This host list is a conservative project policy; host presence is not semantic verification.", "",
        "Official reference locations for NFL facts include the [NFL standings](https://www.nfl.com/standings/), [NFL injury report](https://www.nfl.com/injuries/), [NFL schedule](https://www.nfl.com/schedules/2026/) and [NFL club directory](https://www.nfl.com/teams/). These general links do not validate individual rows in this inventory.", "",
        "## Action and unresolved risk", "",
        "The current site validator's HTTPS-presence pass and this official-domain inventory answer different questions. The former cannot be described as proof that every row has an official source. F-39 is therefore retained as a review item for the broader provenance requirement. Recommended next step: add source-to-field attribution and independent URL/content checks for each data-bearing column, beginning with mixed-source and non-official-only rows; until done, label those values as third-party, derived, or unverified rather than treating a row's other link as support.", "",
        "Reproduce with `python3 tools/audit_current_official_sources.py` after the page build. The run performs no network requests.", "",
    ]
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {CSV_OUT.relative_to(ROOT)} ({total} rows)")
    print(f"wrote {MD_OUT.relative_to(ROOT)}")
    print(f"official-only={official_only} mixed={mixed} nonofficial-only={nonofficial_only} no-https={no_https}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
