# Coordination board

| Task | Status | Owner session | File scope |
|---|---|---|---|
| Build NFL decision-support research dashboard and documented verification framework | done | 25459fae-x4 | `site/**`, `README.md`, `COORDINATION.md`, workflow config |

## Task log

- 2026-11-14 — Claimed dashboard/research framework task. Repository initially contained only a four-byte README and no coordination board or existing site/data. Scope avoids claiming verified current team, injury, or betting-line data. Initial source list to include official NFL and NFL injury-report documentation; all unconfirmed values remain blank and explicitly flagged.
- 2026-11-14 — Completed single-page dashboard, research and validation-gate documentation, open questions, source inventory, flags, and Pages workflow. Verified NFL injury-report policy text at https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693 and reviewed current official injury-report page at https://www.nfl.com/injuries/; confirmed the policy source describes practice status and game status categories. Reviewed official 2026 rulebook entry at https://operations.nfl.com/rules-officiating/2026-nfl-rulebook. Checked local HTML anchors (8 IDs, 19 links, no broken anchors). No current statuses or values copied into the tables; no line odds, performance, depth chart, or correlations verified. Irregularities: odds/props license and source, dated lineup history, jurisdiction/rewards definition, and data permissions remain unresolved. Claim commit 2a28121; implementation commit 809932e (rulebook URL correction is pending commit).
