# Fourth Down — NFL Decision Desk

Official-source NFL decision support: verified data, model lines, a strategy leaderboard
that refuses to reward luck, injury and depth tracking, and a reviewable path from
questions to suggestions.

**Live site:** https://karagemop466-tech.github.io/X4/

## What is in the repository

| Path | What it holds |
|---|---|
| `data/` | The verified source data: 137 official games, the official standings for all 32 teams, the official Week 10 injury report, the official Week 11 schedule, and league-confirmed starter changes |
| `data/output/` | Machine-readable copies of every number the site publishes (`payload.json`, `payload.js` and one file per table), regenerated on each build |
| `research/` | The written findings: model lines, correlations and luck control, strategy validation, injuries and depth, data verification, and the sources register |
| `tools/` | The pipeline: `verify.py` proves the data, `build.py` produces every published number, `pages.py` and `sync.py` build the site, `validate.py` runs the whole gate |
| `site/` | The published multi-page site (nine statically rendered pages) |
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
python3 tools/build.py      # regenerate every published number into data/output/
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

## X4 Console (`docs/`) — a second, independent build

A parallel session (`arena/528008d6-x4`) produced a second, self-contained console under
`docs/` at the same time as the build described above. It is published alongside this one
at **`/console/`** on the same Pages site.

| | Main site (`site/`) | X4 Console (`docs/`) |
|---|---|---|
| Built by | `arena/25459fae-x4`, `arena/70ac0cf1-x4`, `arena/59059060-x4` | `arena/528008d6-x4` |
| Pages | 9 | 15 (incl. 404) |
| Pipeline | Python generator (`tools/`) → static output | No generator; hand-written static files |
| Publication gate | `python3 site/check.py` | `node docs/check.js` |

Both builds follow the same one rule — every table row links to the official source it
came from, and anything unconfirmable is left blank and flagged — and both reached the
same two structural conclusions independently:

1. **The NFL publishes no betting lines.** (`site/`: market-line column empty.
   `docs/`: flagged as **F-02**.)
2. **No official source labels depth-chart strings.** `nfl.com/teams/<club>/depth-chart`
   returns HTTP 404; club sites publish ordered charts without 1st/2nd/3rd/4th labels.
   (`docs/`: flagged as **F-03**.)

They also independently caught the same source conflict: two official NFL.com items give
different absence windows for the same player (6-9 weeks vs 6-10 weeks) — **F-04** on the
`site/` board, **F-06** on the `docs/` board.

Reproducing the console's checks:

```bash
node docs/check.js     # 15 pages, 22 tables, 682 rows, 142 internal links, 27 external
```

The reconciliation of the two builds — including the merge conflict on `COORDINATION.md`
and `README.md`, and the file-scope statement — is logged in the
*Appendix — session `arena/528008d6-x4`* at the bottom of `COORDINATION.md`.
