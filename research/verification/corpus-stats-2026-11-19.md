# Corpus statistics, the declared split, and n on every published value

**Session:** `arena/9fc78d2e-x4` (task T74) · **Date:** 2026-11-19 UTC
**Scope:** `tools/corpus_stats.py` (new), `data/output/corpus_stats.json` (new),
`tools/pages.py` (correlation and home-edge table body), `tools/gen_exec_summary_desk.py`
(the scoring-environment sentence), `tools/content.py` (F-62, F-63, F-66, F-90 and one
verification row), `tools/validate.py` (two gate steps).

---

## 1. What was wrong

`research/computed_stats.json` is the file every published correlation was read from.
Its own header records how it was made:

```json
"generated": "2026-11-14",
"inputs": { "games": "research/data/games_weeks6-9_2026.csv (nfl.com, weeks 6-9 2026 REG, fetched 2026-11-14)" }
```

It is a snapshot of **57 games, weeks 6 to 9**, taken on 2026-11-14. It is not in
`tools/validate.py`'s step list, so nothing ever regenerated it. Meanwhile the
repository grew a complete verified corpus in `data/games-2026.csv`: **150 games,
weeks 1 to 10**, one official NFL.com game URL per row, which
`tools/verify.py` proves reproduces every official NFL.com standings total
(W, L, T, PF, PA) for all 32 clubs.

So the published correlation table was a description of a window that had been
superseded, and the three published defects followed from it:

| Flag | What it found |
|---|---|
| **F-62** | The margin-vs-total correlation was published with n = 57 (the size of the input file) on pages where it was computed on n = 54. |
| **F-63** | The home edge was published at two roundings (+0.1 and +0.07) for one quantity, on a weeks 6-9 window, while 150 games existed. |
| **F-66** | Numeric claims typed into prose are not on the publication gate, so they survive the corpus moving under them. |
| **F-68** | The Bonferroni threshold divided by 8 while performing 9 tests (already corrected in T48; confirmed here, not re-opened). |

## 2. What was built

### 2.1 `tools/corpus_stats.py` (new)

Recomputes every published descriptive statistic of the game log from the
complete verified corpus, per window, with the sample size on every value.

**Integrity checks (each fails loudly, exit code 1):**

1. every game row carries an `https://www.nfl.com/games/...` URL;
2. the standings derived from the corpus equal the official NFL.com standings for
   all 32 clubs (W, L, T, PF, PA);
3. total points scored = total points allowed, and wins = losses;
4. the neutral-site set equals the official International Games list (the five
   published games; the one not yet played, Week 11 in Mexico City, is listed as
   scheduled rather than counted as a neutral game of a window);
5. no duplicated fixture, no negative score.

431 checks pass on the committed corpus.

### 2.2 The declared split

| Window | Weeks | Games | Non-neutral | Role |
|---|---|---|---|---|
| `train` | 3–7 | 75 | 73 | the window the walk-forward model is fitted on |
| `validation` | 8 | 14 | 14 | checked, never chosen on |
| `final` | 9–10 | 29 | 27 | the most recent completed weeks |
| `full` | 1–10 | 150 | 146 | the whole verified corpus |
| `frozen` | 6–9 | 57 | 54 | the window the Week 11 pre-registration froze |

Weeks 1–2 are the walk-forward burn-in (`tools/build.py`
`PARAMS["eval_first_week"] = 3`): the model never evaluates them, so they are
part of the corpus but not a fitting window.

**Honest limitation, published rather than hidden.** The brief asks for train,
validation and final holdout **seasons**. One season cannot give three
seasons; what is published is the week-level analogue inside the single 2026
season. Weeks 9–10 are already inside the 118-game evaluation the leaderboard
reports, so they are a *reporting* window and **not** an untouched holdout. The
next genuinely untouched window is Week 11 onward, which is registered forward
in `research/preregistration/wk11-forward-v1.md`. The split was declared on
2026-11-19, before any Week 11 result existed.

### 2.3 The published numbers

Recomputed from `data/games-2026.csv` (150 official games):

| Window | Home margin (international games excluded) | n | Margin vs total | n | Away vs home | n |
|---|---|---|---|---|---|---|
| Weeks 3–7 | −0.70 pts, CI [−3.38, +1.98] | 73 | −0.2405, CI [−0.4459, −0.0111] | 73 | +0.1130 | 75 |
| Week 8 | **+8.79** pts, CI [+1.49, +16.09] | 14 | −0.3727, CI [−0.7542, +0.1968] | 14 | +0.1800 | 14 |
| Weeks 9–10 | **−5.78** pts, CI [−11.02, −0.54] | 27 | −0.0299, CI [−0.4053, +0.3542] | 27 | −0.0698 | 29 |
| Weeks 1–10 | −0.53 pts, CI [−2.72, +1.65] | 146 | −0.1433, CI [−0.2988, +0.0196] | 146 | +0.0486 | 150 |
| Weeks 6–9 (frozen) | +0.07 pts, CI [−3.59, +3.74] | 54 | −0.3224, CI [−0.5432, −0.0598] | 54 | +0.0182 | 57 |

Plus: mean combined score 46.15 pts (sd 14.18) on n = 150 games; and two
standings correlations recomputed from the current official standings capture
`data/standings-2026-11-18.csv` (n = 32 clubs): net points vs winning
percentage r = +0.8756, CI [+0.7584, +0.9379]; points per game vs points allowed
per game r = −0.2911, CI [−0.5808, +0.0641].

**Cross-check against the frozen artifact.** The weeks 6–9 window reproduces
`research/computed_stats.json` exactly — home margin +0.07 on n = 54, margin vs
total r = −0.3224 on n = 54, away vs home r = +0.0182 on n = 57. The new tool
reads a different input file, uses a different code path, and lands on the same
numbers to four decimals, so the frozen pre-registered model is reproduced
rather than re-derived by assertion.

### 2.4 The finding

The home margin is **not** a stable quantity in this league so far:

- −0.70 pts (n = 73) on the fitting window;
- **+8.79 pts (n = 14)** on week 8 alone — and that interval does *not* contain zero;
- **−5.78 pts (n = 27)** on weeks 9–10 — and that interval does *not* contain zero either, on the other side;
- −0.53 pts (n = 146) over the whole corpus, interval [−2.72, +1.65], containing zero;
- +0.07 pts (n = 54) on the window the pre-registered Week 11 model adds to every spread.

Two consecutive windows each show a "significant" home edge of opposite sign at
n = 14 and n = 27, and the pooled estimate is indistinguishable from zero. That
is the clearest possible demonstration that the constant is a property of the
window rather than a measured league effect — and it is why the site states
that **no home edge is assumed**.

### 2.5 What was published, and where

| Page | Change |
|---|---|
| `gates.html` § 04 "Corpus statistics" | **New table**, 18 rows: every statistic above, with its window, its value, its 95% interval and its n, each row linked to the official schedule page. |
| `gates.html` § 04b "Model correlations" | The 36 model-error correlations, unchanged, still carrying n = 118. |
| `executive-summary.html` | The scoring-environment sentence now quotes the train / validation / recent windows beside the full-corpus figure and links to the per-window table. |

The gates page description, the executive summary and the flag register all
carry the same numbers because they all read the same artifact.

### 2.6 The gate

Two new steps in `tools/validate.py`:

```
("re-derive the corpus statistics and the declared split (T74)",
 [PY, "tools/corpus_stats.py", "--check"]),
...
("check the published corpus statistics against the artifact (T74)",
 [PY, "tools/corpus_stats.py", "--check-page"]),
```

- `--check` re-derives everything and fails if the committed
  `data/output/corpus_stats.json` differs from a fresh derivation, or if any
  integrity check fails.
- `--check-page` parses the rendered `site/gates.html`, extracts the corpus
  table and compares **every row's statistic, value, interval and n** against
  the artifact. A page that prints a number the artifact does not hold now
  fails the build. This is the mechanical closure of F-62's class of defect.

### 2.7 Flags

| Flag | New state |
|---|---|
| **F-62** | `open` → **resolved**. The n beside every published correlation is now the computed n of the window it was measured on, and the page is compared to the artifact by the gate. |
| **F-63** | `open` → **resolved** for the publication half: the two roundings are gone, every published home-edge figure carries its window, its n and its interval, and the per-window table is live. The *modelling* half — whether the registered model should keep adding a constant whose interval contains zero — is **not** closed here; it is recorded as F-90, because the Week 11 pre-registration freezes the model. |
| **F-66** | `open` → **limitation**, narrowed. The five named stale instances are corrected (150 games in the workbench, the integrity gates and the decision register; 78 of 118 in the price store). One class is now gated (the corpus statistics). Numbers typed into prose elsewhere remain ungated, and that is recorded rather than claimed as closed. |
| **F-68** | Already `resolved` (T48). Re-read and confirmed: `tools/build.py` computes `alpha_adj = alpha / max(1, n_tests)` with `n_tests = len(STRATEGIES)` = 9, i.e. 0.00556, and the published text quotes 0.05 / 9. Not re-opened. |
| **F-90** | **New**: the pre-registered Week 11 model adds a home-edge constant whose interval contains zero and whose sign changes with the window. Recorded, not silently changed — the fix is an owner decision for the next registration. |

## 3. Sources (official)

| Fact | Official source | How it was used |
|---|---|---|
| 150 game scores, weeks 1–10 | `data/games-2026.csv`, one `https://www.nfl.com/games/<away>-at-<home>-2026-reg-<n>` URL per row | the corpus every statistic is computed from |
| Official standings, all 32 clubs | <https://www.nfl.com/standings/> — captured in `data/standings-wk10-2026.csv` and `data/standings-2026-11-18.csv` | the completeness check on the corpus, and the two team-level correlations |
| Official International Games (2026) | `data/international-2026.csv`, each row carrying the official weekly schedule page (<https://www.nfl.com/schedules/2026/by-week/week-6> … <https://www.nfl.com/schedules/2026/by-week/week-11>) | which games are excluded from the home-margin statistic |
| Weekly schedules | <https://www.nfl.com/schedules/2026/> | the source link on every published row |
| Pre-registered Week 11 window | `research/preregistration/wk11-forward-v1.md` | the frozen weeks 6–9 window, and the reason F-90 is not "fixed" here |

No value was typed by hand into a published table. No official number was
inferred: every statistic is computed from the corpus, and the corpus is proved
against the official standings.

## 4. Verification performed

- `python3 tools/corpus_stats.py` → 431 integrity checks pass; the weeks 6–9
  window reproduces the frozen artifact to four decimals.
- `python3 tools/corpus_stats.py --check` → the committed artifact equals a fresh
  derivation.
- `python3 tools/corpus_stats.py --check-page` → 18 published rows match the
  artifact exactly (statistic, value, interval and n).
- `python3 tools/verify.py` → 486 checks, PASS: the reconstructed scores reproduce
  every official NFL.com W/L/T/PF/PA total exactly.
- `python3 tools/validate.py` → the full publication gate, including the two new
  steps; site checks report every primary data row carrying a source link, all
  local links resolved, root and site mirrors in step.
- `node docs/check.js` → PASS.

## 5. Left open (published, not blocking)

- **F-90** — the owner decision on the home-edge constant in the next
  registration. Not changed inside the registered window.
- **F-66** — prose outside the gated statistics is still ungated.
- **The multi-season split** — the brief asks for three *seasons*; one season
  gives the week-level analogue only. A second season of official results is the
  only way to close it, and it is published as a limitation on the page.

## 6. Reproduce

```
python3 tools/corpus_stats.py            # rebuild the artifact
python3 tools/corpus_stats.py --check    # the artifact gate
python3 tools/corpus_stats.py --check-page   # the published-page gate
```
