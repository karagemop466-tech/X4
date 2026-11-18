# Week 11 model lines

Schedule source: <https://www.nfl.com/schedules/2026/by-week/week-11> (official NFL.com, retrieved 14 November 2026).
Underlying results: <https://www.nfl.com/schedules/2026/> and <https://www.nfl.com/standings/> (official).

Every number below is a **model estimate** produced by `tools/build.py` from the official results. The market-line column is deliberately empty: the NFL publishes no official betting lines and no licensed odds feed has been authorised for this repository (flag F-01).

| Away | Home | Date | Kickoff (ET) | TV | Spread range | Total range | S3 line | Market line | Source |
|---|---|---|---|---|---|---|---|---|---|
| IND | HOU | 2026-11-19 | 8:15 PM | PRIME | -0.53 to 7.22 | 46.15 to 49.62 | 1.70 / 47.36 | *(blank)* | [NFL.com](https://www.nfl.com/games/colts-at-texans-2026-reg-11) |
| MIA | BUF | 2026-11-22 | 1:00 PM | CBS | -0.53 to 8.11 | 42.84 to 48.03 | 2.06 / 44.53 | *(blank)* | [NFL.com](https://www.nfl.com/games/dolphins-at-bills-2026-reg-11) |
| BAL | CAR | 2026-11-22 | 1:00 PM | FOX | -0.53 to 3.96 | 43.47 to 48.40 | 1.34 / 44.95 | *(blank)* | [NFL.com](https://www.nfl.com/games/ravens-at-panthers-2026-reg-11) |
| NO | CHI | 2026-11-22 | 1:00 PM | FOX | -0.53 to 4.24 | 46.15 to 49.78 | 1.03 / 47.82 | *(blank)* | [NFL.com](https://www.nfl.com/games/saints-at-bears-2026-reg-11) |
| TEN | DAL | 2026-11-22 | 1:00 PM | FOX | -0.53 to 3.17 | 46.15 to 61.61 | 0.56 / 52.50 | *(blank)* | [NFL.com](https://www.nfl.com/games/titans-at-cowboys-2026-reg-11) |
| TB | DET | 2026-11-22 | 1:00 PM | FOX | -1.19 to 2.65 | 41.57 to 47.04 | -0.78 / 44.45 | *(blank)* | [NFL.com](https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11) |
| ARI | KC | 2026-11-22 | 1:00 PM | CBS | -0.53 to 10.29 | 42.05 to 47.45 | 1.98 / 45.84 | *(blank)* | [NFL.com](https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11) |
| PIT | PHI | 2026-11-22 | 1:00 PM | CBS | -7.49 to -0.35 | 40.25 to 46.15 | -2.00 / 43.39 | *(blank)* | [NFL.com](https://www.nfl.com/games/steelers-at-eagles-2026-reg-11) |
| NYJ | LAC | 2026-11-22 | 4:05 PM | FOX | -2.39 to 2.17 | 42.93 to 46.44 | 0.84 / 45.81 | *(blank)* | [NFL.com](https://www.nfl.com/games/jets-at-chargers-2026-reg-11) |
| JAX | NYG | 2026-11-22 | 4:25 PM | CBS | -9.14 to -0.53 | 44.66 to 49.15 | -4.33 / 46.52 | *(blank)* | [NFL.com](https://www.nfl.com/games/jaguars-at-giants-2026-reg-11) |
| LV | DEN | 2026-11-22 | 4:25 PM | CBS | -0.53 to 7.90 | 46.15 to 50.14 | 3.67 / 47.47 | *(blank)* | [NFL.com](https://www.nfl.com/games/raiders-at-broncos-2026-reg-11) |
| MIN | SF | 2026-11-22 | 8:20 PM | NBC | -1.90 to 2.15 | 40.73 to 48.19 | -1.36 / 46.71 | *(blank)* | [NFL.com](https://www.nfl.com/games/vikings-at-49ers-2026-reg-11) |
| CIN | WAS | 2026-11-23 | 8:15 PM | ESPN | -7.40 to -0.53 | 46.15 to 51.20 | -3.18 / 48.29 | *(blank)* | [NFL.com](https://www.nfl.com/games/bengals-at-commanders-2026-reg-11) |

## Reading the range

The spread range spans all nine strategies and the total range likewise. A narrow range means the strategies agree and the verified data supports a directional view; a wide range means the model is close to indifferent, and any pick built on that game is a coin flip dressed up as analysis.

## Team strength behind the lines

Opponent-adjusted rates: a team's points-for rate minus the average points allowed by the opponents it has faced, plus the league average, and the mirror image for points allowed. These are model estimates. The raw official columns are in `data/standings-wk10-2026.csv` and on the Standings page.

| Rank | Team | Adj. points for | Adj. points allowed | Adj. margin | Official PF | Official PA | Source |
|---|---|---|---|---|---|---|---|
| 1 | BUF | 25.79 | 20.28 | 5.50 | 287 | 199 | [NFL.com](https://www.nfl.com/teams/buffalo-bills/) |
| 2 | CIN | 28.65 | 23.17 | 5.48 | 278 | 193 | [NFL.com](https://www.nfl.com/teams/cincinnati-bengals/) |
| 3 | DEN | 25.93 | 20.58 | 5.35 | 198 | 186 | [NFL.com](https://www.nfl.com/teams/denver-broncos/) |
| 4 | JAX | 26.99 | 21.98 | 5.01 | 269 | 144 | [NFL.com](https://www.nfl.com/teams/jacksonville-jaguars/) |
| 5 | TB | 24.20 | 20.03 | 4.16 | 202 | 178 | [NFL.com](https://www.nfl.com/teams/tampa-bay-buccaneers/) |
| 6 | LAR | 23.11 | 19.41 | 3.71 | 248 | 187 | [NFL.com](https://www.nfl.com/teams/los-angeles-rams/) |
| 7 | DET | 24.16 | 20.50 | 3.67 | 257 | 199 | [NFL.com](https://www.nfl.com/teams/detroit-lions/) |
| 8 | MIN | 21.60 | 18.89 | 2.71 | 176 | 126 | [NFL.com](https://www.nfl.com/teams/minnesota-vikings/) |

| Rank | Team | Adj. points for | Adj. points allowed | Adj. margin | Official PF | Official PA | Source |
|---|---|---|---|---|---|---|---|
| 25 | NYG | 20.74 | 23.33 | -2.60 | 203 | 196 | [NFL.com](https://www.nfl.com/teams/new-york-giants/) |
| 26 | ATL | 20.96 | 23.70 | -2.74 | 201 | 258 | [NFL.com](https://www.nfl.com/teams/atlanta-falcons/) |
| 27 | LV | 22.70 | 25.74 | -3.04 | 251 | 289 | [NFL.com](https://www.nfl.com/teams/las-vegas-raiders/) |
| 28 | PHI | 19.20 | 22.52 | -3.32 | 148 | 221 | [NFL.com](https://www.nfl.com/teams/philadelphia-eagles/) |
| 29 | ARI | 20.54 | 24.00 | -3.46 | 184 | 289 | [NFL.com](https://www.nfl.com/teams/arizona-cardinals/) |
| 30 | TEN | 23.51 | 27.80 | -4.29 | 167 | 239 | [NFL.com](https://www.nfl.com/teams/tennessee-titans/) |
| 31 | NYJ | 20.75 | 25.75 | -5.00 | 194 | 254 | [NFL.com](https://www.nfl.com/teams/new-york-jets/) |
| 32 | BAL | 18.93 | 24.31 | -5.38 | 209 | 259 | [NFL.com](https://www.nfl.com/teams/baltimore-ravens/) |

## Why no line is presented as a recommendation

Three reasons, in order of importance. First, there is no market price, so there is nothing to compare an estimate against - a model line without a price is not a bet. Second, the improvement over the league-constant benchmark has a confidence interval that still contains zero (flag F-07), so the model has not demonstrated skill over noise. Third, the public Week 10 injury report omits players on injured reserve, so a material part of the availability picture is missing from the inputs (flag F-03).

## Source links

- Official Week 11 schedule: <https://www.nfl.com/schedules/2026/by-week/week-11>
- Official standings: <https://www.nfl.com/standings/>
- Official Week 10 injury report: <https://www.nfl.com/injuries/>
- Official team pages: linked per row.

