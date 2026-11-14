# NFL Decision Lab

A source-first research dashboard for developing and validating NFL betting signals. This repository currently contains **no verified historical odds, play-by-play, player-prop, depth-chart, or injury dataset**. The dashboard therefore publishes a research plan and explicit data gaps—not picks, live lines, player statuses, or performance claims.

## Browse

Open [`site/index.html`](site/index.html) locally, or use the GitHub Pages URL after Pages is enabled and a deployment succeeds. Pages deployment is configured in `.github/workflows/pages.yml`.

## Integrity rules

- Every factual data row must include a direct official source URL, an as-of timestamp, and a verification state. Unknown values stay blank.
- Distinguish observed official facts from model estimates and market-derived inputs. Never present a model estimate as an official fact.
- No strategy is eligible for rewards until it passes the gates documented on the site; preserve timestamped predictions, prices, and settlement rules.
- Backtests do not remove luck. Use out-of-sample and prospective results, uncertainty intervals, and multiple-testing controls.

## Current scope

The NFL official injury page and NFL rulebook are linked in the dashboard as primary references. This repository does not fetch or assert current injuries or odds. Official source availability and any data-use/licensing permissions must be checked before building ingestion. See [Flagged for Review](site/index.html#flags) for unresolved prerequisites.

## Integrated dashboard

The GitHub Pages source remains `site/`, using the existing Pages workflow. It now presents the research workspace as a responsive dashboard with executive summary, line lab, injury/availability, leaderboard, decision checklist, suggestions, flagged-for-review register and sources. No model/live feed or unverified performance is represented as complete. Review [COORDINATION.md](COORDINATION.md) for per-session evidence and known gaps.
