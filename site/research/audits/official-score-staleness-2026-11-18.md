# Official-score staleness audit — 2026-11-18

**Session:** `arena/2d57231a-x4` (task T46)
**Sources re-read:** [NFL.com Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) (all 14 games FINAL), [NFL.com standings](https://www.nfl.com/standings/) (post-Week-10, all 32 clubs)
**Register:** `research/audits/official-score-staleness-2026-11-18.csv` (one row per club) · live capture: `research/verification/standings-live-2026-11-18.csv`

## What was found

The committed corpus was jointly stale:

| Artifact | Held | Official state on 2026-11-18 |
|---|---|---|
| `data/games-2026.csv` | 137 rows: Weeks 1–9 complete, Week 10 = TNF WAS@NYG only | 10 completed weeks = 150 games |
| `data/standings-wk10-2026.csv` | pre-Week-10 standings (9 weeks for most clubs) | post-Week-10 standings |
| `data/ops/results.csv` | 138 rows, same gap | 150 games |

**13 completed Week-10 games were missing:** NE@DET (10–35), KC@ATL (35–13), HOU@CLE (24–27), MIN@GB (30–10), MIA@IND (22–24), CAR@NO (20–17), BUF@NYJ (31–12), JAX@TEN (40–23), LAR@ARI (34–6), SEA@LV (21–13), SF@DAL (46–40), PIT@CIN (18–38), LAC@BAL (23–20). Every score and game-URL slug was confirmed against the official Week-10 schedule page (both chunks), including the `49ers-at-cowboys` and `rams-at-cardinals` slug forms.

## Why earlier checks did not catch it

`tools/verify.py` reconciles the game log against `data/standings-wk10-2026.csv` — the same stale pair. A stale log and a stale standings snapshot agree with each other, so all 460 (pre-repair) assertions passed. A self-consistent pair is not a verified pair; only re-reading the external official page finds this class of drift (recorded as **F-66**; renumbered from F-58 after the merge with the parallel sessions' flags).

## Exact reconciliation (the staleness proof)

For every club: **official W/L/T/PF/PA = pre-repair log + exactly the missing Week-10 games** — 32 of 32 clubs reproduced exactly, with the expected single W/L flip for every club that played one of the 13 games. No club's delta required any score change to an already-logged game. Clubs on bye (CHI, DEN, PHI, TB) show no delta; NYG and WAS show no delta (their TNF game was already logged).

## Correction applied

- `data/standings-wk10-2026.csv` — all 32 rows rewritten to the official values captured in `research/verification/standings-live-2026-11-18.csv`.
- `data/games-2026.csv` — the 13 games appended (137 → 150 rows).
- `data/ops/results.csv` — the same 13 games appended (138 → 151 lines incl. header).
- `tools/verify.py` now passes **486 assertions** on 150 games, 32 teams: reconstructed scores reproduce every official W/L/T/PF/PA total exactly.

## Consequence for the strategy leaderboard (published as post-hoc, see F-67)

The walk-forward evaluation (Weeks 3–10, n=118) on the completed corpus shows S1 at **+9.49% spread-MAE improvement** over the S0 benchmark (spread MAE 9.484). The significance verdict is **not order-robust**: the deterministic bootstrap is a function of the row order of the identical game set, and the Bonferroni-adjusted 95% interval for the improvement nearly touches zero — [+0.03, +1.97] points on this audit's transcription order (G4 pass) versus [−0.00, +1.94] on the published sorted order (G4 fail). No significance claim is made. Independently, the result is **post-hoc**: the 13 games were ingested after `research/preregistration/wk11-forward-v1.md` froze the corpus. The leaderboard therefore evaluates an explicit **G8 shadow-period gate** (a pre-registered segment, actually graded), which a historical backtest cannot satisfy: S1 is published 6/8 (or 7/8 under the transcription order) and **ineligible** either way; every strategy is paper and reward is provisional until the registered Week-11 forward window is played and graded.

> **Merge note (2026-11-18):** parallel sessions `arena/bca9fb72-x4` and `arena/ad5e4c3d-x4` independently performed the same Week-10 completion and merged it to `main` first. The merged corpus holds the same 150 game tuples as this register (proved set-equal at merge); `main`'s sorted row order is the published one. Their `tools/reverify_2026_11_18.py` + `research/verification/standings-refresh-2026-11-18.csv` record is complementary to this audit's register and capture. Flags: this audit's two flags were renumbered F-58/F-59 → **F-66/F-67** after the ID collision with the merged flags.

## Flags

- **F-66** — jointly stale log/standings pair; the verification design (log vs the same pair) cannot detect it. Clears when the standings snapshot is pinned to an external retrieval with a timestamp/hash independent of the log.
- **F-67** — S1's post-hoc +9.49% improvement is not a pre-registered result, and its adjusted interval flips sign with row ordering of the identical game set; eligibility stays closed behind G8 until the Week-11 forward window settles.

## Audit tool

`tools/audit_score_staleness.py` re-runs this reconciliation at any later date: it rebuilds every club's W/L/T/PF/PA from the current `data/games-2026.csv`, compares them to a given live standings capture, and exits non-zero listing any club that does not reproduce.
