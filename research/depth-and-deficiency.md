# Injuries and depth: from the official report to a starter-out deficiency score

**Retrieved 2026-11-14. Every value below is a count of transcribed official rows, not an
estimate. Sources are listed at the end and linked row by row on the published page
(`depth.html`).**

This note covers the half of the brief that asks the system to know when a defense - or an
offense - is missing a starter and has to reach into its second, third or fourth string. The
first build recorded this as an open gap (**F-02**). It is now closed from an official source,
and closing it produced three findings that were not visible before.

## 1. The source problem, and the source that solves it

`https://www.nfl.com/teams/<club>/depth-chart` returns **HTTP 404** for every club, and the
league publishes no consolidated depth chart. That is why the first build left every depth
string blank rather than inferring one.

Each club, however, publishes its own chart on its own official website, and the chart is a
**table whose column position is the depth position**: the first name in a position row is the
starter, the second is his backup, the third is third string. That is an official statement of
depth order, published by the only party that decides it. Transcribing the order a club prints
is not an inference; assigning a rank the club does not print would be.

Result: **31 of 32 clubs** publish a machine-readable ordered chart. Houston publishes its
chart as a single image (no table markup, no ordered text) and is left blank - **F-18**.

1,558 depth positions were transcribed: 777 on offense, 781 on defense. Depth is distributed
1st: 705, 2nd: 629, 3rd: 189, 4th: 31, 5th: 4 - the tail is where a real cascade would have to
come from.

## 2. What the join shows for Week 10

The official NFL.com Week 10 report lists **76** players Out or Doubtful across the 28 clubs
playing that week. Joined by name to the club charts:

| Measure | Value |
|---|---|
| Out/Doubtful players who sit somewhere on their club's chart | 57 |
| ... at **depth 1** (the listed starter) | **40** |
| ... of those, on offense | 23 |
| ... of those, on defense | 17 |
| Clubs with at least one listed starter out or doubtful | 19 |
| Out/Doubtful players absent from their club's chart | 19 |

The clubs hit hardest by listed-starter losses: **Minnesota (5: 3 offense, 2 defense)**,
**Seattle (4)**, **Tennessee (4)**, **Dallas (3)**, **Green Bay (3)**, **Indianapolis (3)**.
Minnesota's five include its listed starting quarterback, its starting tight end and a starting
receiver - the shape of absence that moves a line.

## 3. The three findings

**No cascade exists in the official Week 10 data (F-22).** In no position row of any of the 31
clubs is both the listed starter and the next man ruled Out or Doubtful. The detector runs on
every build, so the week it happens the row appears automatically. Until then, any model that
assumes a second- or third-string cascade is occurring would be inventing it. This is a negative
result and it matters: it constrains what the strategy work may legitimately condition on.

**Two position rows have no published replacement.** Tennessee lists only **Peter Skoronski** at
left guard and only **Cody Barton** at linebacker, and the official report rules both out. These
are the sharpest availability facts in the dataset - the club itself has published no next man
up. It does not follow that nobody plays (a practice-squad elevation never appears on a depth
chart), only that the club has not said who.

**Nineteen ruled-out players are not on their club's chart (F-19).** Clubs update charts on
their own schedule. The 19 are named individually on the page rather than dropped or given a
guessed rank, which is why the starter-out figure is a **floor, not a ceiling** - 40 is the
minimum number of listed starters ruled out, not the true number of starters who will not play.

## 4. Why the numbers can be trusted, and what they still cannot say

The transcription is validated on every build by `tools/depth.py`:

- every club key must exist in the already-verified official standings file;
- every chart source must be an `https://` official club URL;
- no player may appear twice at the same position and depth (a transcription error);
- no row may list more than six players (an implausible depth);
- no injured player is matched to a chart silently: the join is by normalised name, so a
  mis-typed name surfaces as an *unmatched* player, and the count of unmatched players is
  printed on every build (19, all accounted for above).

The limit that remains is **F-21**: a published chart is not proof of who took the first snap.
There are no snap counts or official game books in this dataset, so the score measures *listed*
pre-kickoff availability, not realised participation. It is the right input for setting a line;
it is not an explanation of a result after the fact. Ingesting the official game books is the
single highest-value fix and is ranked in the suggestions queue.

A second limit is editorial: the charts are club publications, not league records. Six clubs
stamp a date (2026-10-31 to 2026-11-10) and the rest do not; the Patriots state in writing that
their chart is compiled by writers and does not necessarily reflect the organization's view
(**F-20**). The date is shown where one exists and left blank where the club stamps none - it is
never assumed.

## 5. What this changes for the strategy work

The walk-forward scoring on the Strategy Lab page uses **results only**, because no point-in-time
availability record existed for weeks 1-9. This dataset is a **single-week snapshot** (Week 10),
which is exactly the right shape for next-week line-origination and the wrong shape for
backtesting. Adding an availability term to the model requires the same capture repeated weekly
and archived with retrieval dates, so that a Week-w forecast can see only what was known before
Week w. That is now the top-ranked data suggestion: the capture is proven to work, it just needs
to run every week and be kept.

## Sources (all fetched 2026-11-14)

**Injury data (official league):** `https://www.nfl.com/injuries/` (Week 10 report; also reachable
as `https://www.nfl.com/injuries/league/2026/reg10`). Note that requesting
`/injuries/league/2026/reg11` returned the Week 10 page - the Week 11 report had not been
published at retrieval time, so no Week 11 injury data is published anywhere in this repository.

**Club depth charts (official club sites, one per club):**

| Club | Official depth-chart page | Dated on the page |
|---|---|---|
| ARI | https://www.azcardinals.com/team/depth-chart | no |
| ATL | https://www.atlantafalcons.com/team/depth-chart | no |
| BAL | https://www.baltimoreravens.com/team/depth-chart | no |
| BUF | https://www.buffalobills.com/team/depth-chart | no |
| CAR | https://www.panthers.com/team/depth-chart | no |
| CHI | https://www.chicagobears.com/team/depth-chart | 2026-10-31 |
| CIN | https://www.bengals.com/team/depth-chart | no |
| CLE | https://www.clevelandbrowns.com/team/depth-chart | no |
| DAL | https://www.dallascowboys.com/team/depth-chart | no |
| DEN | https://www.denverbroncos.com/team/depth-chart | no |
| DET | https://www.detroitlions.com/team/depth-chart | no |
| GB | https://www.packers.com/team/depth-chart | 2026-11-10 |
| HOU | https://www.houstontexans.com/team/depth-chart | **image only - no transcription** |
| IND | https://www.colts.com/team/depth-chart | no |
| JAX | https://www.jaguars.com/team/depth-chart | no |
| KC | https://www.chiefs.com/team/depth-chart | no |
| LAC | https://www.chargers.com/team/depth-chart | no |
| LAR | https://www.therams.com/team/depth-chart | no |
| LV | https://www.raiders.com/team/depth-chart | 2026-11-10 |
| MIA | https://www.miamidolphins.com/team/depth-chart | no |
| MIN | https://www.vikings.com/team/depth-chart | no |
| NE | https://www.patriots.com/team/depth-chart | no (club states it is writers' opinion) |
| NO | https://www.neworleanssaints.com/team/depth-chart | no |
| NYG | https://www.giants.com/team/depth-chart | no |
| NYJ | https://www.newyorkjets.com/team/depth-chart | no |
| PHI | https://www.philadelphiaeagles.com/team/depth-chart | no |
| PIT | https://www.steelers.com/team/depth-chart/ | no |
| SEA | https://www.seahawks.com/team/depth-chart/ | no |
| SF | https://www.49ers.com/team/depth-chart | 2026-11-10 |
| TB | https://www.buccaneers.com/team/depth-chart | no |
| TEN | https://www.tennesseetitans.com/team/depth-chart | 2026-11-10 |
| WAS | https://www.commanders.com/team/depth-chart | no |

## Reproducing

```bash
python3 tools/depth.py          # validate the transcription, rebuild the CSV and depth.json
python3 tools/depth.py --check  # validate only, no write (used as a gate)
python3 tools/build.py && python3 tools/pages.py && python3 tools/sync.py  # rebuild the site
python3 site/check.py           # publication gate: every data row carries an official source
```
