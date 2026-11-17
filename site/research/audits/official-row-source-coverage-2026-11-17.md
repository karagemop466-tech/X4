# Official-domain link coverage audit — 2026-11-17

> **Important:** this is a static URL/host inventory, not a live-source or value-verification pass. A link on an allowlisted host does not establish that the linked page supports every number or claim in its row. No page data was changed or marked verified.

## Finding

The audit parsed **1,045 data rows** across **22 legacy desk pages**. The current F-39 inventory lists **191 rows without any HTTPS link**. Under the stricter official-domain-presence test used here, **366 rows have no allowlisted official-domain link**: 175 have only non-official HTTPS links, and 191 have no HTTPS link.

Of the rows, **624** have an allowlisted official-domain link and no other HTTPS link; **55** combine an allowlisted link with a non-official HTTPS link; **175** have only non-official HTTPS links; and **191** have no HTTPS link. The 55 mixed-source rows still need source-to-value attribution; an NFL fixture link does not verify a third-party odds value in the same row.

This is a wider source-link gap than the existing F-39 count represents. It does **not** show that the 366 rows are false; it shows that this repository does not currently attach an allowlisted official-domain URL to those rendered rows. Treat those rows as unverified under the requested rule until individually sourced or left blank and flagged.

## Row-level inventory

[Download the full CSV inventory](../verification/official-row-source-coverage-2026-11-17.csv). It has one record per data row, the rendered row text, classification, and the exact URLs present in that row. Review those URLs directly; they were not fetched by this audit.

| Page | Official host only | Official + non-official | Non-official HTTPS only | No HTTPS link | Total |
|---|---:|---:|---:|---:|---:|
| [`executive-summary.html`](../../executive-summary.html) | 1 | 0 | 1 | 27 | 29 |
| [`requirements.html`](../../requirements.html) | 0 | 0 | 1 | 39 | 40 |
| [`data.html`](../../data.html) | 103 | 13 | 0 | 0 | 116 |
| [`signals.html`](../../signals.html) | 34 | 0 | 17 | 0 | 51 |
| [`leaderboard.html`](../../leaderboard.html) | 12 | 0 | 1 | 10 | 23 |
| [`injuries.html`](../../injuries.html) | 31 | 0 | 0 | 2 | 33 |
| [`decisions.html`](../../decisions.html) | 24 | 0 | 6 | 0 | 30 |
| [`review.html`](../../review.html) | 0 | 0 | 0 | 0 | 0 |
| [`flagged.html`](../../flagged.html) | 13 | 3 | 10 | 0 | 26 |
| [`repo-review.html`](../../repo-review.html) | 0 | 0 | 10 | 1 | 11 |
| [`sources.html`](../../sources.html) | 13 | 0 | 5 | 0 | 18 |
| [`origination.html`](../../origination.html) | 41 | 12 | 18 | 1 | 72 |
| [`price-store.html`](../../price-store.html) | 4 | 0 | 78 | 0 | 82 |
| [`signal-vs-staking.html`](../../signal-vs-staking.html) | 11 | 0 | 0 | 19 | 30 |
| [`correlations.html`](../../correlations.html) | 14 | 0 | 0 | 2 | 16 |
| [`replacements.html`](../../replacements.html) | 245 | 0 | 0 | 0 | 245 |
| [`method-lab.html`](../../method-lab.html) | 27 | 0 | 0 | 0 | 27 |
| [`ops-review.html`](../../ops-review.html) | 12 | 0 | 0 | 10 | 22 |
| [`verification.html`](../../verification.html) | 5 | 0 | 1 | 10 | 16 |
| [`requirements-closure.html`](../../requirements-closure.html) | 0 | 0 | 0 | 12 | 12 |
| [`workbench.html`](../../workbench.html) | 0 | 0 | 0 | 27 | 27 |
| [`programme.html`](../../programme.html) | 34 | 27 | 27 | 31 | 119 |

## Classification method and official-source references

The page set and row parser are shared with [`tools/check_site.py`](https://github.com/karagemop466-tech/X4/blob/main/tools/check_site.py): its 22 legacy desk pages and `table.data` body rows. Rows are numbered in parser order per page. URLs are deduplicated within a row, preserving their rendered order.

The domain allowlist is conservative and explicit: `nfl.com` and its subdomains; `ftc.gov` and its subdomains; and the **exact** hostnames in the `source` column of [`data/depth-wk11-2026.csv`](../../data/depth-wk11-2026.csv), which [`tools/depth.py`](https://github.com/karagemop466-tech/X4/blob/main/tools/depth.py) documents as club-published depth-chart URLs. Team-host subdomains are not guessed. The 33 allowlisted hosts comprise those two base domains and 31 club chart hosts; Houston's chart is not machine-readable and is not used to add a hostname.

Official NFL references already recorded in the repository: [NFL standings](https://www.nfl.com/standings/), [NFL injury reports](https://www.nfl.com/injuries/), [Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11), and [NFL club directory](https://www.nfl.com/teams/). The allowlist also recognizes the [U.S. Federal Trade Commission](https://www.ftc.gov/) domain for government/legal material; that does not make it a source for NFL game facts.

The 31 club domains are grounded in these exact, previously recorded chart URLs:

- ARI: [https://www.azcardinals.com/team/depth-chart](https://www.azcardinals.com/team/depth-chart)
- ATL: [https://www.atlantafalcons.com/team/depth-chart](https://www.atlantafalcons.com/team/depth-chart)
- BAL: [https://www.baltimoreravens.com/team/depth-chart](https://www.baltimoreravens.com/team/depth-chart)
- BUF: [https://www.buffalobills.com/team/depth-chart](https://www.buffalobills.com/team/depth-chart)
- CAR: [https://www.panthers.com/team/depth-chart](https://www.panthers.com/team/depth-chart)
- CHI: [https://www.chicagobears.com/team/depth-chart](https://www.chicagobears.com/team/depth-chart)
- CIN: [https://www.bengals.com/team/depth-chart](https://www.bengals.com/team/depth-chart)
- CLE: [https://www.clevelandbrowns.com/team/depth-chart](https://www.clevelandbrowns.com/team/depth-chart)
- DAL: [https://www.dallascowboys.com/team/depth-chart](https://www.dallascowboys.com/team/depth-chart)
- DEN: [https://www.denverbroncos.com/team/depth-chart](https://www.denverbroncos.com/team/depth-chart)
- DET: [https://www.detroitlions.com/team/depth-chart](https://www.detroitlions.com/team/depth-chart)
- GB: [https://www.packers.com/team/depth-chart](https://www.packers.com/team/depth-chart)
- IND: [https://www.colts.com/team/depth-chart](https://www.colts.com/team/depth-chart)
- JAX: [https://www.jaguars.com/team/depth-chart](https://www.jaguars.com/team/depth-chart)
- KC: [https://www.chiefs.com/team/depth-chart](https://www.chiefs.com/team/depth-chart)
- LAC: [https://www.chargers.com/team/depth-chart](https://www.chargers.com/team/depth-chart)
- LAR: [https://www.therams.com/team/depth-chart](https://www.therams.com/team/depth-chart)
- LV: [https://www.raiders.com/team/depth-chart](https://www.raiders.com/team/depth-chart)
- MIA: [https://www.miamidolphins.com/team/depth-chart](https://www.miamidolphins.com/team/depth-chart)
- MIN: [https://www.vikings.com/team/depth-chart](https://www.vikings.com/team/depth-chart)
- NE: [https://www.patriots.com/team/depth-chart](https://www.patriots.com/team/depth-chart)
- NO: [https://www.neworleanssaints.com/team/depth-chart](https://www.neworleanssaints.com/team/depth-chart)
- NYG: [https://www.giants.com/team/depth-chart](https://www.giants.com/team/depth-chart)
- NYJ: [https://www.newyorkjets.com/team/depth-chart](https://www.newyorkjets.com/team/depth-chart)
- PHI: [https://www.philadelphiaeagles.com/team/depth-chart](https://www.philadelphiaeagles.com/team/depth-chart)
- PIT: [https://www.steelers.com/team/depth-chart/](https://www.steelers.com/team/depth-chart/)
- SEA: [https://www.seahawks.com/team/depth-chart/](https://www.seahawks.com/team/depth-chart/)
- SF: [https://www.49ers.com/team/depth-chart](https://www.49ers.com/team/depth-chart)
- TB: [https://www.buccaneers.com/team/depth-chart](https://www.buccaneers.com/team/depth-chart)
- TEN: [https://www.tennesseetitans.com/team/depth-chart](https://www.tennesseetitans.com/team/depth-chart)
- WAS: [https://www.commanders.com/team/depth-chart](https://www.commanders.com/team/depth-chart)

## Limits and recommended next step

- This audit checks hostnames only. It does not resolve DNS, make HTTP requests, inspect page text, prove the page is controlled by the claimed organization, or match a source to an individual cell.
- The 55 mixed-source rows should be split by field or annotated so each source is tied to the value it supports. Do not treat the presence of an NFL schedule/game URL as evidence for a separate market-price value.
- The 175 non-official-only rows include third-party odds and repository links. Keep third-party prices segregated and labelled as such; do not promote them to official NFL evidence.
- The 191 no-HTTPS rows are the current F-39 inventory. The per-row links and text in the CSV allow manual triage, but no missing URL was guessed or filled.
- Recommended follow-up: the final site integrator should update F-39 and the published Flagged for Review page to report the strict count and the mixed-source attribution gap, or retain the current site wording with an explicit notice that it covers only rows with no HTTPS link. No shared page or index was edited in this task.

Non-official HTTPS hosts encountered (link count after per-row URL deduplication):

- `github.com`: 25
- `karagemop466-tech.github.io`: 2
- `site.api.espn.com`: 1
- `sports.core.api.espn.com`: 162
- `sportsbook.draftkings.com`: 1
- `www.espn.com`: 39

## Reproduction

Run `python3 tools/audit_official_row_sources.py` to regenerate the CSV and this report. Run `python3 tools/audit_official_row_sources.py --check` to verify both outputs match the current committed pages.
