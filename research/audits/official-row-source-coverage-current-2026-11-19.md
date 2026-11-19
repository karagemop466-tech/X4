# Current desk-row official-domain link inventory — 2026-11-19

> **Scope and limit:** this is a static inventory of URLs rendered in each current desk table row. It does not fetch source pages, check source ownership, or establish that a cited page supports a particular value. No value is marked verified by this report.

## Finding

The audit parsed **1,138 data rows** across **29 current desk pages**. **725** rows have allowlisted official-domain HTTPS links only; **90** have both official-domain and non-official HTTPS links; **323** have non-official HTTPS links only; and **0** have no HTTPS link. **413** rows contain non-official URLs or no HTTPS URL. This hostname classification does not establish field-level provenance for any row, including rows with official-domain links only.

A link to an NFL schedule in the same row as a third-party odds value does not support the odds. A repository link supports provenance to a project artifact, not an official NFL fact. For any claim/value not directly supported by a suitable source, the value must remain unverified or blank and be flagged; this audit does not infer a missing citation.

## Row-level inventory

The CSV below contains one record for every parsed row, its rendered text, classification and exact URLs. Empty `official_urls` means this audit found no allowlisted official-domain URL in that row; it is not proof the underlying fact is false.

[Download row-level CSV](../verification/official-row-source-coverage-current-2026-11-19.csv)

| Desk page | Official only | Official + other | Other HTTPS only | No HTTPS | Rows |
|---|---:|---:|---:|---:|---:|
| [`executive-summary.html`](../../executive-summary.html) | 3 | 4 | 4 | 0 | 11 |
| [`requirements.html`](../../requirements.html) | 0 | 0 | 40 | 0 | 40 |
| [`data.html`](../../data.html) | 103 | 13 | 0 | 0 | 116 |
| [`signals.html`](../../signals.html) | 34 | 0 | 17 | 0 | 51 |
| [`leaderboard.html`](../../leaderboard.html) | 13 | 0 | 10 | 0 | 23 |
| [`injuries.html`](../../injuries.html) | 31 | 1 | 1 | 0 | 33 |
| [`decisions.html`](../../decisions.html) | 24 | 0 | 6 | 0 | 30 |
| [`review.html`](../../review.html) | 0 | 0 | 0 | 0 | 0 |
| [`flagged.html`](../../flagged.html) | 11 | 6 | 10 | 0 | 27 |
| [`repo-review.html`](../../repo-review.html) | 0 | 0 | 11 | 0 | 11 |
| [`sources.html`](../../sources.html) | 13 | 0 | 5 | 0 | 18 |
| [`origination.html`](../../origination.html) | 41 | 24 | 7 | 0 | 72 |
| [`price-store.html`](../../price-store.html) | 4 | 0 | 78 | 0 | 82 |
| [`signal-vs-staking.html`](../../signal-vs-staking.html) | 11 | 0 | 19 | 0 | 30 |
| [`correlations.html`](../../correlations.html) | 14 | 0 | 2 | 0 | 16 |
| [`replacements.html`](../../replacements.html) | 245 | 0 | 0 | 0 | 245 |
| [`method-lab.html`](../../method-lab.html) | 27 | 0 | 0 | 0 | 27 |
| [`ops-review.html`](../../ops-review.html) | 12 | 0 | 10 | 0 | 22 |
| [`verification.html`](../../verification.html) | 5 | 0 | 11 | 0 | 16 |
| [`requirements-closure.html`](../../requirements-closure.html) | 0 | 0 | 12 | 0 | 12 |
| [`workbench.html`](../../workbench.html) | 0 | 12 | 15 | 0 | 27 |
| [`programme.html`](../../programme.html) | 34 | 27 | 58 | 0 | 119 |
| [`luck.html`](../../luck.html) | 0 | 0 | 0 | 0 | 0 |
| [`readiness.html`](../../readiness.html) | 0 | 0 | 0 | 0 | 0 |
| [`teams.html`](../../teams.html) | 0 | 0 | 0 | 0 | 0 |
| [`delta.html`](../../delta.html) | 0 | 0 | 0 | 0 | 0 |
| [`brief-register.html`](../../brief-register.html) | 66 | 3 | 2 | 0 | 71 |
| [`depth-audit.html`](../../depth-audit.html) | 31 | 0 | 0 | 0 | 31 |
| [`open-questions.html`](../../open-questions.html) | 3 | 0 | 5 | 0 | 8 |

## Classification policy

The desk row parser and page list are imported from [`tools/check_site.py`](https://github.com/karagemop466-tech/X4/blob/main/tools/check_site.py). The official-host allowlist is `nfl.com`/subdomains, `ftc.gov`/subdomains, and the exact club hostnames appearing in the committed depth-chart source column in [`data/depth-wk11-2026.csv`](../../data/depth-wk11-2026.csv). This host list is a conservative project policy; host presence is not semantic verification.

Official reference locations for NFL facts include the [NFL standings](https://www.nfl.com/standings/), [NFL injury report](https://www.nfl.com/injuries/), [NFL schedule](https://www.nfl.com/schedules/2026/) and [NFL club directory](https://www.nfl.com/teams/). These general links do not validate individual rows in this inventory.

## Action and unresolved risk

The current site validator's HTTPS-presence pass and this official-domain inventory answer different questions. The former cannot be described as proof that every row has an official source. F-39 is therefore retained as a review item for the broader provenance requirement. Recommended next step: add source-to-field attribution and independent URL/content checks for each data-bearing column, beginning with mixed-source and non-official-only rows; until done, label those values as third-party, derived, or unverified rather than treating a row's other link as support.

Reproduce with `python3 tools/audit_current_official_sources.py` after the page build. The run performs no network requests.
