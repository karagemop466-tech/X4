# Live re-verification of the standings that every model number rests on (2026-11-18)

Session `arena/dee8092e-x4`, task **T48**. Every model number on the site — the power
ratings, the walk-forward evaluation, the leaderboard, the luck panel and the Week 11
lines — is derived from `data/standings-wk10-2026.csv`, which is itself derived from the
proved game log. This note records a fresh read of the official standings against the
committed file.

**Source read:** <https://www.nfl.com/standings/> — fetched 2026-11-18 UTC through the
page-fetch tool. Division view, all four AFC divisions.

## Result: 24 of 24 clubs match on W, L, T, PF and PA

| Club | Official page (W-L-T, PF, PA) | Committed CSV | Verdict |
|---|---|---|---|
| BUF | 8-1-0, 287, 199 | 8, 1, 0, 287, 199 | match |
| NE | 5-5-0, 221, 242 | 5, 5, 0, 221, 242 | match |
| NYJ | 2-8-0, 194, 254 | 2, 8, 0, 194, 254 | match |
| MIA | 1-8-0, 148, 224 | 1, 8, 0, 148, 224 | match |
| CIN | 7-2-0, 278, 193 | 7, 2, 0, 278, 193 | match |
| PIT | 6-3-0, 198, 182 | 6, 3, 0, 198, 182 | match |
| CLE | 6-4-0, 188, 220 | 6, 4, 0, 188, 220 | match |
| BAL | 4-6-0, 209, 259 | 4, 6, 0, 209, 259 | match |
| JAX | 7-2-0, 269, 144 | 7, 2, 0, 269, 144 | match |
| HOU | 3-6-0, 233, 219 | 3, 6, 0, 233, 219 | match |
| IND | 3-7-0, 208, 271 | 3, 7, 0, 208, 271 | match |
| TEN | 1-8-0, 167, 239 | 1, 8, 0, 167, 239 | match |
| KC | 7-2-0, 237, 156 | 7, 2, 0, 237, 156 | match |
| DEN | 7-2-0, 198, 186 | 7, 2, 0, 198, 186 | match |
| LV | 4-6-0, 251, 289 | 4, 6, 0, 251, 289 | match |
| LAC | 1-8-0, 144, 239 | 1, 8, 0, 144, 239 | match |
| NYG | 5-3-1, 203, 196 | 5, 3, 1, 203, 196 | match |
| DAL | 4-6-0, 286, 282 | 4, 6, 0, 286, 282 | match |
| WAS | 3-5-1, 196, 223 | 3, 5, 1, 196, 223 | match |
| PHI | 2-7-0, 148, 221 | 2, 7, 0, 148, 221 | match |
| DET | 7-2-0, 257, 199 | 7, 2, 0, 257, 199 | match |
| MIN | 7-2-0, 176, 126 | 7, 2, 0, 176, 126 | match |
| CHI | 7-2-0, 241, 184 | 7, 2, 0, 241, 184 | match |
| GB | 6-4-0, 226, 221 | 6, 4, 0, 226, 221 | match |

Net points were checked implicitly: `net_pts` is PF − PA, and every PF and PA matched, so
every net total follows.

## Two renderings that look wrong and are not

Two strings on the page invite a misread, and both were checked before being written up:

1. **`5 - 1 - 0` beside BUF.** That is the page's *conference* record column
   (5 conference wins, 1 conference loss), not a typo for the overall record. The overall
   record for the same row reads `8 | 1 | 0`. No correction is needed.
2. **`1 - 8 - 0` for LAC.** The Chargers really are 1–8 after **nine** games — the
   committed game log holds exactly one LAC win and eight LAC losses, and
   `tools/verify.py` proves that log against these same standings totals. The odd part is
   not the record but that LAC has played nine times while most clubs have played ten
   (the club's Week 11 game is still to come). It is counter-intuitive, which is why it is
   called out rather than silently accepted; it is not an error, and a first draft of this
   note that said "two wins in ten games" was wrong and is corrected here.

Neither is an irregularity. Both are recorded here so that a later reader does not
"solve" a problem that does not exist — the failure mode the F-60/F-70 venue entry
documents in the opposite direction.

## What this establishes and what it does not

**Establishes:** the input to every model number is a faithful transcription of the
official standings at the date read, on 24 clubs and five fields each (120 cells).

**Does not establish:** that the model is any good. The best strategy still fails its
gate — 0 of 9 eligible — and the paired sign test, while it now clears for two
strategies, is not the metric the gate uses (F-67, and S-15 remains the owner's decision).

**Not checked here:** the eight NFC clubs not listed above (the NFC divisions are served
in a second chunk of the page that was not read row by row in this pass). The committed
standings for **all 32** clubs are separately proved against the game log by
`tools/verify.py`, which is the stronger check because it ties every club's PF and PA to an
individual game score; this note is an independent, human read of one of its two inputs.

## Reproduce

```bash
python3 tools/verify.py    # the game log must reproduce all 32 official standings rows
```
