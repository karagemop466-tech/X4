# Fourth Down Research — NFL Decision Desk

A source-first research system for **originating NFL lines**, **validating strategies behind gates**, and **tracking player availability** — published as a static GitHub Pages dashboard at **https://karagemop466-tech.github.io/X4/**.

Everything factual on the site carries a link to the official page it came from (retrieved 2026-11-14); anything that cannot be confirmed is left **blank and flagged**, never inferred.

## Browse

| Section | Page |
|---|---|
| Landing / dashboard | [`index.html`](index.html) |
| Executive summary | [`executive-summary.html`](executive-summary.html) |
| Requirements inventory (40 items) | [`requirements.html`](requirements.html) |
| Verified data tables (standings, schedules, odds, 57 results) | [`data.html`](data.html) |
| Line lab, signals, gates, correlations | [`strategies.html`](strategies.html) |
| Leaderboard & rewards design | [`leaderboard.html`](leaderboard.html) |
| Injury & depth-string tracking | [`injuries.html`](injuries.html) |
| Decision Q&A (30 questions) | [`decisions.html`](decisions.html) |
| Suggestions (review → select → build) | [`suggestions.html`](suggestions.html) |
| Flagged for review (12 blanks, 8 irregularities) | [`flagged.html`](flagged.html) |
| Repo review | [`repo-review.html`](repo-review.html) |
| Source register | [`sources.html`](sources.html) |

## Integrity rules

- Every factual table row includes a direct official source URL; the CI checker (`tools/check_site.py`) fails the build if a data row lacks an `https://` link or any local link/anchor breaks.
- Unknown values stay blank and appear on [Flagged for Review](flagged.html) with a reason and a clearing path.
- Computed values (home edge, correlations, baseline lines) are reproduced from committed CSVs: `python3 tools/compute_stats.py`.
- No strategy is eligible for leaderboard rank until it passes the eight gates on [the strategies page](strategies.html#gates); no performance, edge, or reward amount is claimed today.

## Reproduce the numbers

```bash
python3 tools/compute_stats.py    # recomputes research/computed_stats.json from research/data/*.csv
python3 tools/gen_data_html.py    # regenerates data.html tables from the same CSVs
python3 tools/check_site.py       # link + data-row verification for all pages
```

Data inputs (each row traced to an official fetch on 2026-11-14):
`research/data/games_weeks6-9_2026.csv` (57 games, nfl.com) ·
`research/data/standings_2026_through_week10_tnf.csv` (32 teams, nfl.com/standings) ·
`research/data/week11_odds_2026.csv` (13 games, ESPN/DraftKings snapshot).

## Deployment & coordination

- **Pages source:** `main` branch, repository root (legacy auto-build). CI (`.github/workflows/pages.yml`) runs `tools/check_site.py` on every push; the historical `site/` folder is an archive of earlier sessions and is not linked from the nav.
- **Coordination:** see [COORDINATION.md](COORDINATION.md) for the shared task board, session log, PR/merge record, sources and verification notes.
- This is research infrastructure, not betting advice. Legal scope, data licensing and reward structure remain open decisions ([Decision Q&A](decisions.html)).
