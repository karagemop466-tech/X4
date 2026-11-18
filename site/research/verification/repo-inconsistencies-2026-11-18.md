# Line-by-line repository review: claims that do not match the committed data (2026-11-18)

Session `arena/ad5e4c3d-x4`, task T46. Each item below was found by re-deriving a published
number from the committed CSV or JSON that the page cites. Nothing was edited outside this
session's scope; each item names the file that owns the fix.

## R-1 (medium) The margin-vs-total correlation: n is right, the label is not

**Published in two places, with two different n:**

| Where | Row label | r | CI | n |
|---|---|---|---|---|
| `signals.html` (generated from `research/computed_stats.json`) | "Margin ↔ game total" | -0.322 | [-0.54, -0.06] | **54** |
| executive summary, and the correlations page | "Margin ↔ game total (Wks 6–9)" | -0.32 | [-0.54, -0.06] | **57** |

**Committed data:** `tools/compute_stats.py` builds both series from games with
`neutral_site == "0"`, which is 54 of the 57 games in
`research/data/games_weeks6-9_2026.csv`; `pearson()` then records `n = 54`. The JSON holds
`{"n": 54, "r": -0.3224, "ci95": [-0.5432, -0.0598]}`.

So the generated table is **correct**, and the error is upstream of it: the row description
that reaches the executive summary and the correlations page attaches **57** — the size of the
input file — to a correlation computed on **54** observations. For a value the brief requires
to be published with its `n`, printing the file count instead of the observation count is the
one substitution that must not happen, because it makes an excluded-observation result look
like a complete one.

The exclusion itself is also unstated in the label: three neutral-site games (HOU at JAX
week 6, PIT at NO week 7, CIN at ATL week 9, per `research/data/international-2026.csv`) are
dropped, which the row label should say.

**Fix owner:** the description text for `margin_vs_total` wherever `n = 57` is attached
(`tools/content.py` / `tools/gen_data_html.py` / the console's `data/correlation.js`); the
value and its CI need no change.

## R-2 (medium) The same home-edge number is presented at two different values

**Published:** the executive summary says `+0.1 pts mean home margin, n = 54`; the line-lab
model text says `h = +0.07 (measured home edge, weeks 6–9)`. Both are the same quantity.

**Committed data:** `research/computed_stats.json` holds `home_edge.mean_home_margin = 0.074`,
`n = 54`, `ci95 = [-3.59, 3.74]`. Re-deriving from
`research/data/games_weeks6-9_2026.csv` gives `+0.074` on the same `n = 54` — so neither
published figure is wrong, but the two roundings of one number invite the reader to think
they are two measurements.

**Also relevant, and stated as a scope limit rather than an error:** the window is weeks 6–9
only. Re-deriving on the full verified corpus (weeks 1–10, neutral-site games excluded) gives
`n = 67` and a mean of `-1.49`, against `+0.07` on the four-week window. The line lab applies
`h` as an additive constant to every Week 11 spread. On the wider window that constant would
have the opposite sign, so the modelling choice is materially sensitive to the window. That
is a legitimate design question, but the page currently presents `h` as "measured" without
saying it is measured **only on weeks 6–9 while 150 games of data exist**.

**Fix owner:** `tools/gen_strategies_html.py` (the line-lab text) and the executive summary
row; the choice of window is a modelling decision for the owner of `tools/origination.py`.

## R-3 (high) 14 games were missing from the corpus; a further 15 now exist and are not in it

Already fixed and published: 13 missing Week 10 games were added (`data/week10-slate-2026.csv`,
`brief-register.html`). **This entry records what remains.** Week 11 is in progress — the
Thursday game (Colts at Texans, Nov 19) has not been played at the time of this reading — so
no Week 11 result can be added yet. When it is played, the same three-step pattern applies:
transcribe from the official schedule page, re-run `tools/verify.py` against a fresh standings
capture, and publish the reconciliation beside the corpus.

## R-4 (medium) Two charts are dated on the page but only five clubs print a date

**Published:** the depth page says a chart is dated where the club stamps one.

**Committed data:** `tools/depth.py` `CHART_DATE` has entries for five clubs only (TEN, GB,
SF, LV, CHI). The other 26 clubs' rows carry an empty `chart_date`, which the depth-audit
page now shows explicitly per club ("club prints no date"). This is a correct limitation, not
an error — recorded here so the "31 clubs' charts" figure is never read as "31 dated charts".

**But:** the live Seattle and Washington pages read today publish no date either, and their
content no longer matches the committed transcription for Washington (see R-5). So an undated
chart can be old, and the dataset cannot tell you how old.

## R-5 (high) The depth transcription is not a faithful render of the published tables

Measured in full in `research/verification/depth-slot-fidelity-2026-11-18.md` and summarised
on `depth-audit.html`: 1,558 rows, 705 club/unit/position columns, **0 cells holding two
players**, no special-teams row at all, and a four-club live sample in which 4 of 103 players
are missing and the one shared rank-1 cell is stored as depth 1 and 2.

## R-6 (low) Page counts and "n of N" statements are typed, not computed

Several pages carry counts in prose (`"57 final scores"`, `"12 unverified items"`,
`"1,558 positions"`). Three of those had drifted by this session: the executive summary's
results count, its flag count, and its standings total `6,291` (now `6,923`). The two
executive summaries and the two new desk pages are now generated from data so they cannot
drift; the rest of the site still types some counts.

## R-7 (informational) `research/data/games_weeks6-9_2026.csv` and `data/games-2026.csv` agree

Checked because they are two independent transcriptions of overlapping weeks: the 43 games
common to weeks 6–9 match on both scores in every case (0 conflicts). The week-10 additions
in `data/week10-slate-2026.csv` do not overlap that file at all (14 new games). This is
evidence for both transcriptions, and it is recorded because a silent disagreement between two
copies of the same game would be the most damaging possible defect.

## Sources

- `tools/compute_stats.py`, `research/computed_stats.json`, `research/data/games_weeks6-9_2026.csv`
  — committed artifacts, re-derived in this session.
- `research/data/international-2026.csv` — the neutral-site set the exclusion is keyed on.
- <https://www.nfl.com/standings/> — read 2026-11-18, used for R-3's standings capture.
- <https://www.nfl.com/schedules/2026/by-week/week-10> and `week-11` — read 2026-11-18.
- <https://www.seahawks.com/team/depth-chart>, <https://www.commanders.com/team/depth-chart>,
  <https://www.baltimoreravens.com/team/depth-chart>, <https://www.clevelandbrowns.com/team/depth-chart>
  — read 2026-11-18 for R-5.
