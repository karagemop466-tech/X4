# Fourth Down — NFL Decision Desk

Official-source NFL decision support: verified data, model lines, a strategy leaderboard
that refuses to reward luck, injury and depth tracking, and a reviewable path from
questions to suggestions.

**Live site:** https://karagemop466-tech.github.io/X4/

## What is in the repository

| Path | What it holds |
|---|---|
| `data/` | The verified source data: 137 official games, the official standings for all 32 teams, the official Week 10 injury report, the official Week 11 schedule, and league-confirmed starter changes |
| `data/output/` | Machine-readable copies of every number the site publishes, regenerated on each build |
| `research/` | The written findings: model lines, correlations and luck control, strategy validation, injuries and depth, data verification, and the sources register |
| `tools/` | The pipeline: `verify.py` proves the data, `build.py` produces every published number, `pages.py` and `sync.py` build the site, `validate.py` runs the whole gate |
| `site/` | The published multi-page site (nine pages) and its data file |
| `COORDINATION.md` | The shared board for the parallel agent sessions working on this repository |

## The one rule everything follows

Every table row carries a direct link to the official NFL page it came from, and every
value that cannot be confirmed from an official source is left blank and flagged rather
than filled in. `site/check.py` enforces this: it executes the real renderer, inspects
the resulting markup, and fails the build if any rendered data row lacks an official
source link.

## Reproducing everything

```bash
python3 tools/verify.py     # prove the data against the official NFL.com standings
python3 tools/build.py      # regenerate every published number into site/data.js
python3 tools/pages.py      # regenerate the site pages
python3 tools/sync.py       # keep the root copies in step with site/
python3 site/check.py       # check the rendered site for broken links and unsourced rows
python3 tools/validate.py   # all of the above, plus determinism and repository hygiene
```

Python 3 standard library only for the pipeline. Node is used by `tools/render.js` to
execute the browser renderer during the site check; the published site itself needs no
build step and no server.

## The findings in one paragraph

The game log was reconstructed and then **proved** against the official NFL.com standings:
all 32 teams match on wins, losses, ties, points for, points allowed and net points,
which also proves every individual score. Nine strategies were then scored on 105
out-of-sample games under a walk-forward protocol with no look-ahead. The best strategy
beats a league-constant benchmark by about eight percent on point-spread error, and it is
well calibrated - but its Bonferroni-adjusted bootstrap interval still contains zero, so
**no strategy passes every validation gate and none is eligible for reward**. The
correlation matrix shows four of the nine strategies are effectively one signal, so they
cannot be counted as four independent pieces of evidence. Model lines for all 13 official
Week 11 games are published as a range across strategies, with the market-line column
deliberately empty: the NFL publishes no official betting lines and no licensed odds feed
has been authorised for this repository.

## What is deliberately missing, and why

Market lines, depth-chart strings, player-level statistics and player-prop performance are
not published, because no official source for them was confirmed. Each is recorded on the
site's *Flagged for review* page and in `research/data-verification.md`. The suggestions
page ranks the work that would close those gaps, with the decision each one needs.

## Coordination

This repository is worked on by several agent sessions in parallel. `COORDINATION.md`
records who owns which files, what has been claimed, what has been merged, and the
verification and deployment history.

## Sources

Official NFL.com pages only for published values: the league standings, the weekly injury
report, the weekly schedules, the team and player pages, and NFL.com news for starter
changes. Full register with URLs and retrieval dates in `research/sources-register.md`.

## Not advice

This is a research and decision-support project. It publishes no picks, accepts no bets,
pays no prizes and is not betting advice. Model figures are estimates derived from
official results and are labelled as such throughout.
