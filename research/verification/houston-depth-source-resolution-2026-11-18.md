# Houston depth-chart gap — authorized-source resolution (T47, 2026-11-18)

Task: T47 (session `arena/a2e2f988-x4`). Closes the actionable part of gate **S5**
("depth charts for all 32 clubs") and refines flag **F-24** for the Houston Texans.

## The gap

The Houston Texans publish their official depth chart only as a single bitmap image.
Re-fetched live on 2026-11-18, `https://www.houstontexans.com/team/depth-chart` renders
one `<img>` under the heading "Unofficial Depth Chart" with **no table markup and no
ordered text**. No authorized structured club chart exists for Houston, so Houston had
zero rows in `data/depth-wk11-2026.csv` and gate S5 was blocked at 31 of 32 clubs.

## Source-resolution verdict register

Every candidate authorized source for Houston's depth order was tested. A value is
`verified` only from an official primary source (NFL, an official club site, GSIS,
government/regulatory, or standards/academic). Third-party aggregators are structured
but non-official and are rejected.

| # | Candidate source | URL | What it publishes | Verdict |
|---|---|---|---|---|
| 1 | Houston Texans official depth-chart page | https://www.houstontexans.com/team/depth-chart | Chart renders as a single bitmap image; no table markup, no ordered text | no structured chart — rejected |
| 2 | NFL.com club depth-chart address | https://www.nfl.com/teams/houston-texans | `nfl.com/teams/<club>/depth-chart` returns HTTP 404 for every club (established by `tools/depth.py`); the NFL publishes no structured depth chart | no structured chart — rejected |
| 3 | NFL GSIS (`nflgsis.com`) | https://www.nflgsis.com/ | Official league data site (named official in the verification policy); publishes no depth-chart ordinal feed | no structured chart — rejected |
| 4 | Third-party Houston depth sources (ESPN, PFN, Statz, StatRankings, StickToTheModel) | https://www.espn.com/nfl/team/depth/_/name/hou | Structured depth tables exist, but all are non-official aggregators; the verification policy forbids using them to mark a value verified | non-official — rejected |
| 5 | Official NFL Game Book (Week 10, HOU at CLE) | https://static.www.nfl.com/image/upload/v1794829724/gamecenter/ab583279-4feb-11f1-abca-2c54536568a9.pdf | Authorized structured source: Lineups (actual starters) + Playtime Percentage (per-player snaps / snap share). Used to derive the indices. Reuse-gated: raw rows stored privately, indices only | authorized — used |

The Game Book is the source the brief names for this exact case: *"use snap counts as
the starter proxy when the depth chart is unavailable"* and *"do not model depth from
jersey order; model it from playing time."*

## What was captured and derived

The official Game Book for **Houston Texans at Cleveland Browns, 2026 REG 10,
2026-11-15 (HOU 24 – CLE 27)** was fetched and parsed in full. The raw capture is
stored privately at `data/ops/raw/gamebook-hou-at-cle-2026-reg10.txt` with a SHA-256
and a UTC stamp. Per the T38 reuse gate, raw Game Book player rows are **not**
republished; only **derived playing-time depth indices** are published on
`houston-depth.html`, each carrying the Game Center page and the PDF link.

Derived indices (n = 1 game):

| Unit | Group | Actual starters (Lineups) | Starter snap share | Backup snap share | Starters at 100% | Inactive at group |
|---|---|---|---|---|---|---|
| OFF | QB | C.Stroud | 100% | — | 1 | D.Mills (DNP) |
| OFF | RB | W.Marks | 45% | 33% | 0 | D.Montgomery (Not Active) |
| OFF | WR | N.Collins, K.Boutte, X.Hutchinson | 85% | 49% | 0 | M.Harrison (Not Active) |
| OFF | TE | D.Schultz | 66% | 33% | 0 | B.Jordan (Not Active) |
| OFF | OL | A.Ersery, F.Nwaiwu, E.Brown, E.Ingram, T.Brown | 100% | 12% | 5 | K.Rutledge, W.Teller, B.Smith |
| DEF | DE | J.Clowney, W.Anderson | 76% | 32% | 0 | D.Hunter (Not Active) |
| DEF | DT | T.Togiai, S.Rankins | 65% | 41% | 0 | — |
| DEF | CB | D.Stingley, K.Lassiter | 100% | 0% | 2 | — |
| DEF | LB | J.Hansen, H.To'oTo'o | 97% | 0% | 1 | A.Al-Shaair (Not Active) |
| DEF | S | C.Bullock, J.Pitre, M.Stewart | 100% | 3% | 2 | — |

Replacement pairing (inactive / DNP player → the actual starter at the same group):
D.Mills→C.Stroud; D.Montgomery→W.Marks; M.Harrison→Collins/Boutte/Hutchinson;
B.Jordan→D.Schultz; K.Rutledge/W.Teller/B.Smith→the five OL starters;
D.Hunter→Clowney/Anderson; A.Al-Shaair→Hansen/To'oTo'o.

## What stays open

The Houston **club-chart depth chain** (2nd/3rd/4th string) is not published by any
authorized structured source and remains blank and flagged (**F-24**). Gate S5 is
therefore closed for the **starter / playing-time** axis only; the ordinal chain is a
flagged gap. A single game is n = 1, so no per-position depth statistic is claimed
beyond this game.

## Verification performed

- Raw capture hash recomputed and matched: `a9acbb8c8b417147afab7ca5f02a9a99c8656acb93d5fb2c73d1f1f9ea9db2ad`
  (`data/ops/raw/gamebook-hou-at-cle-2026-reg10.txt`).
- `python3 tools/houston_depth.py --check` — PASS (raw hash, every lineup player in the
  snap table, snap shares within [0,100], inactive/DNP players are not starters, 10
  group rows built).
- `python3 tools/validate.py` — **VALIDATION PASSED** (full publication gate:
  standings proof, injury capture check, SHA-256 capture verify, market re-derivation,
  two-capture reconciliation, site gate, root mirror byte-identical, determinism, data
  hygiene, console gate).
- `python3 site/check.py` — PASS (17 pages; 3,275 data rows, every one with an official
  source link; no broken links).
- `python3 tools/check_site.py` — PASS (26 desk pages; 0 desk rows without an https
  source link).
- `node tools/render.js site` — no JavaScript error on the new page.
- Live official re-verification (fetched 2026-11-18 UTC): the Houston chart page
  (image-only), the Game Center page (HOU 24–CLE 27, Huntington Bank Field), and the
  Game Book PDF (Lineups, Substitutions, Not Active, Did Not Play, Playtime Percentage)
  were all read directly and agree with the transcribed dataset.

## Irregularities

1. **Checker allowlist corrected (additive).** `site/check.py`'s official-domain regex
   did not include `nflgsis.com`, although the verification policy explicitly names GSIS
   as an official primary source. Added `nflgsis.com` to the allowlist. This is a
   correction, not a weakening: it only admits an already-designated official domain.
2. **Not blocking.** The Houston ordinal depth chain remains unavailable; this is the
   honest limit recorded on F-24 and the page, not a data error.

## Sources (all fetched live 2026-11-18 UTC)

- [Houston Texans official depth chart (image only)](https://www.houstontexans.com/team/depth-chart)
- [NFL Game Center — Texans at Browns, 2026 REG 10](https://www.nfl.com/games/texans-at-browns-2026-reg-10)
- [Official NFL Game Book PDF (HOU at CLE, Week 10)](https://static.www.nfl.com/image/upload/v1794829724/gamecenter/ab583279-4feb-11f1-abca-2c54536568a9.pdf)
- [NFL GSIS](https://www.nflgsis.com/)
- [NFL.com teams hub](https://www.nfl.com/teams/houston-texans)
