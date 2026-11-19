# T62 live official re-verification and integration pass (2026-11-19)

Session `arena/a66163eb-x4`. Claimed as T60, renumbered T61 at the first merge (`arena/cd239f59-x4` also took T60), and renumbered T62 at the second merge (`arena/f2865351-x4` also took T61). Row-level data: `integration-live-2026-11-19.csv` (same folder).

## What was read live, and the result

| Check | Result | Official source |
|---|---|---|
| 32 club standings rows (W, L, T, PF, PA, net points) against `data/standings-wk10-2026.csv` | **32 of 32 match**; net = PF minus PA for every official row | https://www.nfl.com/standings/ |
| 14 Week 10 final scores against `data/games-2026.csv` | **14 of 14 match** | https://www.nfl.com/schedules/2026/by-week/week-10 (each game page linked in the CSV) |
| Live injury report | Shows the **Week 11** report (title and heading). The committed injury data is still Week 10. | https://www.nfl.com/injuries/ |
| Scheduled capture job | Last six runs failed. The injuries freshness check fails: last valid read 2026-11-18T03:44:00Z, 27.2 hours old against a 13-hour limit. | https://github.com/karagemop466-tech/X4/actions/runs/44393037693 |
| Open PR #96 (T46 audit) | Premise not current on `main`: `main` has all 14 Week 10 games. PR diverges from `main` (413 commits, 232 files) and is not mergeable. Not merged or closed here. | https://github.com/karagemop466-tech/X4/pull/96 |

## Flags

- **F-83** (already on `main`, filed by `arena/cd239f59-x4`): the Week 11 injury capture fails the schema gate; cause not confirmed.
- **F-85** (this session): the publication gate passes while the injury capture is past its freshness limit. The gate's capture steps run on synthetic fixtures, and the scheduled workflow tolerates a freshness failure (`continue-on-error`).
- **F-61**: superseded. The Week 11 report exists on 2026-11-19.

## Limits

- nfl.com cannot be reached over TLS from the bash sandbox (`curl` and `urlopen` fail). Live reads were made with the page-fetch tool. Values were transcribed from the rendered pages and compared by script.
- The Week 11 injury rows were not transcribed. Doing so by hand is not allowed by the verification policy.
