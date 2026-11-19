# Depth slots as groups: shared cells and empty cells, stored as published

**Session:** `arena/9fc78d2e-x4` (task T75) · **Date:** 2026-11-19 UTC
**Scope:** `tools/depth.py` (transcription model, CSV, roll-up),
`tools/pages.py` (the depth table body), `tools/desk_extension.py` (the per-team
view), `tools/gen_depth_audit.py` (the fidelity panel), `data/depth-wk11-2026.csv`,
`data/output/depth.json`, `tools/content.py` (F-64, F-91).

---

## 1. What the brief asks, and what the dataset did

The brief asks for two things about depth order:

> "Model depth slots as groups, not a single starter — 149 club/unit/position slots list
> more than one rank-1 player (three receivers at rank 1, three inside linebackers at
> rank 1). Treating column 1 as 'the starter' would fabricate a starter the club never named."

> "Represent shared and empty depth slots faithfully — Seattle puts two players in one slot
> and Washington leaves a slot empty; both are currently indistinguishable from a ranked list."

Both were true of the dataset and false of the requirement. `tools/depth.py`
transcribed each chart row as an ordered list of names and then enumerated it:

```python
for depth, player in enumerate(order, start=1):
```

so **every name became its own depth number**. The committed file
(`data/depth-wk11-2026.csv`, 1,558 rows) held **0 cells with more than one
player** and **no record of a printed-but-empty cell**. The T46 audit
(`research/verification/depth-slot-fidelity-2026-11-18.md`) measured this and
named the two clubs the brief names.

A club that publishes two men in one cell has published **co-starters**. Storing
the second man as depth 2 does not just lose information: it makes the
deficiency pipeline report a backup where the club published a partner, so the
brief's "who was expected to start, who actually did" graph would carry a
fabricated string.

## 2. The change

### 2.1 The transcription model

A depth-chart **cell** is now one of:

| In the transcription | What the club printed | `slot_kind` |
|---|---|---|
| `"Name"` | one name in the cell | `single` |
| `("A", "B")` | several names in the **same** cell | `shared` |
| `""` | a cell printed with no name in it | `empty` |

The format is backwards compatible: every one of the 31 clubs that has not been
re-read still transcribes as a flat list of names, and each of those names is a
single-player cell, which is what the 2026-11-14 capture can support.

### 2.2 The published file

`data/depth-wk11-2026.csv` gains two columns:

- `slot_kind` — `single` / `shared` / `empty`
- `slot_size` — how many names the club printed in that cell (0 for an empty one)

`depth` keeps its meaning: the **cell number**, so both names in a shared cell
carry the same depth number and the empty cell keeps the position it was printed
in. An empty cell is published as a row with an empty player, so "the club left
this cell blank" is distinguishable from "we did not record it".

Current state of the file: 1,559 rows — 1,556 `single`, 2 `shared` (one cell,
two names), 1 `empty`.

### 2.3 The roll-up now runs on cells

`tools/depth.py`'s deficiency roll-up grouped rows by position row and then
compared "depth 1" with "depth 2". It now groups by **cell**:

- a **shared** first cell with one name out is a *shared slot with one absence* —
  the position still has a starter, so it is **not** a hole and **not** a cascade;
- a **shared** first cell with every name out *is* a hole, and the hole names
  both players;
- a **cascade** now means "the first cell's only name is out and every name in the
  second cell is out", and it prints the whole second cell;
- an **empty** cell is recorded in `empty_slots` and never counted as a person.

The per-team view (`tools/desk_extension.py`) was changed the same way: it
counted "depth 1 rows that are Out" as starters out, which would have listed a
co-starter as a lost starter. It now counts a cell whose **every** published name
is out, and prints both names when a shared slot is lost.

### 2.4 The pages

- `depth.html` — the per-club depth table gains a **"Cell as published"** column:
  `cell 1`, `cell 1 · 2 named in one cell (co-starters)`, or `cell 2 · printed
  empty`. The player cell for an empty slot reads "no name printed in this cell".
- `depth-audit.html` — the fidelity panel now **evaluates** its four tests
  against the committed file instead of describing them: the shared-cell test
  reads the Seattle WR row out of the CSV and prints the depths it actually
  holds; the empty-cell test reads Washington's third WR row; the two remaining
  tests (special teams, chart versioning) report what is still missing. The
  prose about "a shared cell of 0 is not a clean sheet" is now computed from the
  file, so it cannot survive the fix it describes.

## 3. The two clubs re-read live, and what the reads showed

### Seattle Seahawks — <https://www.seahawks.com/team/depth-chart/>

Read 2026-11-19. The chart is **unchanged** from the 2026-11-14 capture: same
names, same order, in every offensive and defensive row. The first
wide-receiver cell prints **two** names:

```
| WR | Cooper Kupp | Rashid Shaheed | Irvin Charles |  |  |  |
```

so the row is now stored as one shared cell of two names at depth 1, and
Irvin Charles at depth 2. Before the change the file read Kupp 1, Shaheed 2,
Charles 3 — a ranking the club never published.

### Washington Commanders — <https://www.commanders.com/team/depth-chart>

Read 2026-11-19. The chart **has changed** since the 2026-11-14 capture, and
its third wide-receiver row now prints an **empty second cell**:

```
| WR | Antonio Williams |  |  |  |  |  |
```

Comparing the committed 2026-11-14 rows with today's page, cell by cell:

| Cell | 2026-11-14 (committed) | 2026-11-19 (live) |
|---|---|---|
| WR 1 | Terry McLaurin | Treylon Burks |
| WR 2 | Treylon Burks | Van Jefferson |
| C 1 | Nick Allegretti | Lucas Patrick |
| LG 2 | Tanoa Togiai | Nick Allegretti |
| WR2 2 | Jaylin Lane | Luke McCaffrey |
| WR3 1 | Dyami Brown | Antonio Williams |
| WR3 2 | Antonio Williams | *(cell printed empty)* |
| WR3 3 | Luke McCaffrey | *(cell no longer printed)* |
| RB 1–3 | Jacory Croskey-Merritt / Rachaad White / Austin Ekeler | Rachaad White / Austin Ekeler / Robert Henry Jr. |
| DL 1 | Daron Payne | Charles Omenihu |
| DL3 1–2 | Javon Kinlaw / Charles Omenihu | Deatrich Wise Jr. / Ricky Barber |
| CB2 1–2 | Mike Sainristil / Fabian Moreau | Trey Amos / Mike Sainristil |
| CB 3 | *(not printed)* | Isaac Yiadom |
| DL 2 | *(not printed)* | Jer'Zhan Newton |
| CB2 3 | *(not printed)* | Fabian Moreau |
| OLB2 3 | Javontae Jean-Baptiste | *(cell no longer printed)* |

**17 cells differ: 15 names changed, 3 cells added, 2 cells removed.** The
Washington rows are therefore re-transcribed from today's page and stamped
`retrieved = 2026-11-19`; the Seattle rows carry the same stamp because the
chart was re-read and confirmed unchanged.

This is the staleness F-52 points at, now measured on a club whose chart the
project transcribes: a chart is true until the next transaction, and the
per-club retrieval stamp is what tells a reader which rows are from which read.

## 4. What this does not fix

- **29 of 31 clubs still carry the 2026-11-14 transcription**, and their shared
  and empty cells are therefore still not represented. The model can hold them;
  the data has to be re-read club by club, exactly as the T46 audit prescribed.
  The clubs re-read so far are the ones this session could open.
- **Special teams are transcribed for no club.** The live pages publish P, K, H,
  LS, PR and KR sections; the dataset holds no such rows, and the audit page
  reports that as an open test with the number of rows (0).
- **The player-absence gap** from the T46 audit (4 of 103 sampled live players
  absent from the dataset) is unchanged and still open.

## 5. Flags

| Flag | New state |
|---|---|
| **F-64** | Narrowed. The three elements are separated: (a) *shared cells* — the model now represents them and the two clubs the brief names are stored faithfully, with the other 29 clubs still to be re-read; (b) *special teams* — still zero for every club; (c) *sampled players absent* — unchanged. The audit page publishes each element's current number. |
| **F-91** | **New**: the committed Washington depth chart was stale — 17 cells differ between the 2026-11-14 capture and the 2026-11-19 live read, including a printed empty cell that the capture could not represent. The rows are now dated, and the general risk (a chart is true only until the next transaction) is recorded against every club whose chart has not been re-read. |

## 6. Sources (official, read this session)

| Fact | Official source | Read |
|---|---|---|
| Seattle publishes Cooper Kupp **and** Rashid Shaheed in the first WR cell | <https://www.seahawks.com/team/depth-chart/> | 2026-11-19 |
| Washington prints an empty second cell in its third WR row | <https://www.commanders.com/team/depth-chart> | 2026-11-19 |
| Washington chart names as listed in the table above | <https://www.commanders.com/team/depth-chart> | 2026-11-19 |
| Club chart URLs for every other club (unchanged, 2026-11-14) | the `source` column of `data/depth-wk11-2026.csv` | 2026-11-14 |

## 7. Verification performed

- `python3 tools/depth.py` → 31 clubs, 1,559 rows, 0 transcription problems; the
  shared cell is SEA/WR/1 (Kupp, Shaheed) and the empty cell is WAS/WR3/2.
- `python3 tools/depth.py --check` → transcriptions are internally consistent: no
  empty cell carries a name, no shared cell carries one name, no player is
  printed twice in one cell.
- `python3 tools/gen_depth_audit.py` → the panel prints PASS on the shared-cell
  test (Kupp 1, Shaheed 1, Charles 2) and on the empty-cell test, and OPEN with
  the measured number on the two tests that remain open.
- `python3 tools/validate.py` → the full publication gate; every rendered data
  row carries a source link, all local links resolve, the root mirror matches
  `site/`.

## 8. Reproduce

```
python3 tools/depth.py            # rebuild the depth dataset and the roll-up
python3 tools/depth.py --check    # transcription consistency gate
python3 tools/gen_depth_audit.py  # the fidelity panel
```
