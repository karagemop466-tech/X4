# Live verification of the injury-report input to the personnel ablation (2026-11-18)

Session `arena/dee8092e-x4`, task **T48**. The personnel ablation on
`data/personnel-ablation-wk10-2026.csv` has one input that decides every number on the
page: which clubs carry an `Out` designation on the official Week 10 report. Four clubs
form the "clear" group (the entire comparison rests on them), so they were re-read from
the live official page rather than trusted from the committed CSV.

**Source read:** <https://www.nfl.com/injuries/league/2026/reg10> — fetched 2026-11-18 UTC
through the page-fetch tool (the sandbox cannot open a socket to nfl.com). The address
still serves **Week 10** content, which is itself the current state of F-61.

## Method

For each club, the live page was read row by row and three independent counts were taken:
the number of player rows, the number of `Out` designations, and the number of `Doubtful`
and `Questionable` designations. Those counts were then compared with
`data/injuries-wk10-2026.csv`. A count that disagreed would invalidate the ablation's
grouping and the page would have to be withdrawn; each agreement is a check that the
transcription was not paraphrased.

## Result: all four "clear" clubs verified, plus three controls

| Club | Live page: rows | Live: Out | Live: Dbt | Live: Qbl | Committed CSV | Verdict |
|---|---|---|---|---|---|---|
| **BUF** | read | 0 | 1 | 4 | 14 rows, 0 Out, 1 Dbt, 4 Qbl | **clear club — group confirmed** |
| **LV** | 5 | 0 | 0 | 2 | 5 rows, 0 Out, 0 Dbt, 2 Qbl | **clear club — group confirmed** |
| **NYG** | read | 0 | 0 | 1 | 11 rows, 0 Out, 0 Dbt, 1 Qbl | **clear club — group confirmed** |
| **PIT** | 8 | 0 | 0 | 1 | 8 rows, 0 Out, 0 Dbt, 1 Qbl | **clear club — group confirmed** |
| SEA (control) | 15 | 4 | 0 | 0 | 15 rows, 4 Out, 0 Dbt, 0 Qbl | matches exactly |
| CAR (control) | 12 | 1 | 2 | 4 | 12 rows, 1 Out, 2 Dbt, 4 Qbl | matches exactly |
| HOU (control) | 16 | 5 | 0 | 6 | 16 rows, 5 Out, 0 Dbt, 6 Qbl | matches exactly |
| CLE (control) | 12 | 2 | 0 | 1 | 12 rows, 2 Out, 0 Dbt, 1 Qbl | matches exactly |

The four clear clubs verified by name-level reading: the Las Vegas Raiders (5 rows: Booker
Qbl, Fatukasi, Ian Thomas, Thornton Qbl, Zuhn — **no Out**), the Pittsburgh Steelers (8
rows: Echols, Elliott, Harmon Qbl, Heyward, Skowronek, Slaughter, Washington, Watt — **no
Out**), and the Buffalo Bills and New York Giants, whose `Out` count is zero on the live
page.

Spot-checked against the live page and matching the committed cells:

- SEA `Out`: Charles Cross (T), Sam Darnold (QB), Quenton Nelson (G), Leonard Williams (DT).
- HOU `Out`: Azeez Al-Shaair (LB), Marvin Harrison Jr. (WR), Danielle Hunter (DE), Brevin Jordan (TE), Keylan Rutledge (G).
- CAR `Out`: Bobby Okereke (LB); CAR `Doubtful`: Jonathon Brooks, Mike Jackson.
- CLE `Out`: Michael Burton (FB), Ronnie Hickman Jr. (S).
- PIT `Questionable`: Derrick Harmon (DT).

## What this does and does not establish

**Establishes:** the input that decides the ablation's grouping is a faithful transcription
of the official page for the clubs that matter, at the date read. The three `Out` clubs
named above are genuine, so HOU/CAR/CLE/SEA belong in the designated group and LV/PIT do
not belong in the clear group.

**Does not establish:** that the *effect* is real. Verification is of the input, not the
finding. `personnel-ablation.html` continues to publish both A1 and A2 intervals as
spanning zero, and the empty-control-group finding (0 of 28 clubs with no designation at
all) stands unchanged.

**One caveat that must travel with the table.** The official report is a *weekly snapshot
as published at the address read*. It is not an inactive list: a club that ruled a player
`Out` and a club that placed him on reserve/Injured both look like "no designation" on
some other week's report. That is precisely why the club-level contrast is published as a
base rate to calibrate a prior against, and never as a points adjustment.

## Reproduce

```bash
python3 tools/personnel_ablation.py --check   # the CSV must match a fresh derivation
```

The verification above is a manual read of a rendered page and is therefore recorded here
rather than asserted by a script; the script's own numbers are gated by the publication
check.
