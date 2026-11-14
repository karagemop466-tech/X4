# Week 11 model lines

Schedule source: <https://www.nfl.com/schedules/2026/by-week/week-11> (official NFL.com, retrieved 14 November 2026).
Underlying results: <https://www.nfl.com/schedules/2026/> and <https://www.nfl.com/standings/> (official).

Every number below is a **model estimate** produced by `tools/build.py` from the official results. The market-line column is deliberately empty: the NFL publishes no official betting lines and no licensed odds feed has been authorised for this repository (flag F-01).

| Away | Home | Date | Kickoff (ET) | TV | Spread range | Total range | S3 line | Market line | Source |
|---|---|---|---|---|---|---|---|---|---|
| IND | HOU | 2026-11-19 | 8:15 PM | PRIME | -0.02 to 9.28 | 45.92 to 51.78 | 3.44 / 47.63 | *(blank)* | [NFL.com](https://www.nfl.com/games/colts-at-texans-2026-reg-11) |
| MIA | BUF | 2026-11-22 | 1:00 PM | CBS | -0.02 to 8.10 | 41.87 to 48.42 | 2.10 / 43.84 | *(blank)* | [NFL.com](https://www.nfl.com/games/dolphins-at-bills-2026-reg-11) |
| BAL | CAR | 2026-11-22 | 1:00 PM | FOX | -0.02 to 5.03 | 45.03 to 49.52 | 1.93 / 45.78 | *(blank)* | [NFL.com](https://www.nfl.com/games/ravens-at-panthers-2026-reg-11) |
| NO | CHI | 2026-11-22 | 1:00 PM | FOX | -0.02 to 5.00 | 45.92 to 52.13 | 1.71 / 48.24 | *(blank)* | [NFL.com](https://www.nfl.com/games/saints-at-bears-2026-reg-11) |
| TEN | DAL | 2026-11-22 | 1:00 PM | FOX | -0.02 to 3.77 | 45.92 to 54.62 | 1.35 / 49.50 | *(blank)* | [NFL.com](https://www.nfl.com/games/titans-at-cowboys-2026-reg-11) |
| TB | DET | 2026-11-22 | 1:00 PM | FOX | -2.86 to 1.61 | 40.38 to 46.91 | -1.68 / 43.72 | *(blank)* | [NFL.com](https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11) |
| ARI | KC | 2026-11-22 | 1:00 PM | CBS | -0.99 to 5.31 | 43.21 to 47.56 | 0.50 / 45.31 | *(blank)* | [NFL.com](https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11) |
| PIT | PHI | 2026-11-22 | 1:00 PM | CBS | -9.77 to -0.02 | 37.67 to 45.92 | -3.27 / 42.42 | *(blank)* | [NFL.com](https://www.nfl.com/games/steelers-at-eagles-2026-reg-11) |
| NYJ | LAC | 2026-11-22 | 4:05 PM | FOX | -2.76 to 0.75 | 42.86 to 48.37 | 0.06 / 46.48 | *(blank)* | [NFL.com](https://www.nfl.com/games/jets-at-chargers-2026-reg-11) |
| JAX | NYG | 2026-11-22 | 4:25 PM | CBS | -9.07 to -0.02 | 43.53 to 47.03 | -4.13 / 45.10 | *(blank)* | [NFL.com](https://www.nfl.com/games/jaguars-at-giants-2026-reg-11) |
| LV | DEN | 2026-11-22 | 4:25 PM | CBS | -0.02 to 8.83 | 45.92 to 52.99 | 4.37 / 48.97 | *(blank)* | [NFL.com](https://www.nfl.com/games/raiders-at-broncos-2026-reg-11) |
| MIN | SF | 2026-11-22 | 8:20 PM | NBC | -0.02 to 4.87 | 37.49 to 45.92 | 1.14 / 43.16 | *(blank)* | [NFL.com](https://www.nfl.com/games/vikings-at-49ers-2026-reg-11) |
| CIN | WAS | 2026-11-23 | 8:15 PM | ESPN | -5.74 to -0.02 | 45.92 to 50.54 | -2.36 / 48.54 | *(blank)* | [NFL.com](https://www.nfl.com/games/bengals-at-commanders-2026-reg-11) |

## Reading the range

The spread range spans all nine strategies and the total range likewise. A narrow range means the strategies agree and the verified data supports a directional view; a wide range means the model is close to indifferent, and any pick built on that game is a coin flip dressed up as analysis.

## Team strength behind the lines

Opponent-adjusted rates: a team's points-for rate minus the average points allowed by the opponents it has faced, plus the league average, and the mirror image for points allowed. These are model estimates. The raw official columns are in `data/standings-wk10-2026.csv` and on the Standings page.

| Rank | Team | Adj. points for | Adj. points allowed | Adj. margin | Official PF | Official PA | Source |
|---|---|---|---|---|---|---|---|
| 1 | JAX | 26.00 | 20.18 | 5.83 | 229 | 121 | [NFL.com](https://www.nfl.com/teams/jacksonville-jaguars/) |
| 2 | GB | 26.44 | 21.59 | 4.85 | 216 | 191 | [NFL.com](https://www.nfl.com/teams/green-bay-packers/) |
| 3 | BUF | 25.19 | 20.50 | 4.69 | 256 | 187 | [NFL.com](https://www.nfl.com/teams/buffalo-bills/) |
| 4 | DEN | 25.60 | 20.96 | 4.64 | 198 | 186 | [NFL.com](https://www.nfl.com/teams/denver-broncos/) |
| 5 | CIN | 28.28 | 23.73 | 4.55 | 240 | 175 | [NFL.com](https://www.nfl.com/teams/cincinnati-bengals/) |
| 6 | TB | 24.48 | 19.97 | 4.51 | 202 | 178 | [NFL.com](https://www.nfl.com/teams/tampa-bay-buccaneers/) |
| 7 | HOU | 26.07 | 21.88 | 4.19 | 209 | 192 | [NFL.com](https://www.nfl.com/teams/houston-texans/) |
| 8 | PIT | 22.93 | 19.94 | 3.00 | 180 | 144 | [NFL.com](https://www.nfl.com/teams/pittsburgh-steelers/) |

| Rank | Team | Adj. points for | Adj. points allowed | Adj. margin | Official PF | Official PA | Source |
|---|---|---|---|---|---|---|---|
| 25 | CAR | 22.98 | 25.46 | -2.47 | 199 | 219 | [NFL.com](https://www.nfl.com/teams/carolina-panthers/) |
| 26 | IND | 22.29 | 25.03 | -2.74 | 184 | 249 | [NFL.com](https://www.nfl.com/teams/indianapolis-colts/) |
| 27 | PHI | 19.23 | 22.73 | -3.50 | 148 | 221 | [NFL.com](https://www.nfl.com/teams/philadelphia-eagles/) |
| 28 | LV | 23.62 | 27.76 | -4.14 | 238 | 268 | [NFL.com](https://www.nfl.com/teams/las-vegas-raiders/) |
| 29 | TEN | 22.71 | 27.22 | -4.51 | 144 | 199 | [NFL.com](https://www.nfl.com/teams/tennessee-titans/) |
| 30 | LAC | 20.09 | 24.60 | -4.52 | 121 | 219 | [NFL.com](https://www.nfl.com/teams/los-angeles-chargers/) |
| 31 | NYJ | 21.79 | 26.47 | -4.68 | 182 | 223 | [NFL.com](https://www.nfl.com/teams/new-york-jets/) |
| 32 | BAL | 18.37 | 24.75 | -6.38 | 189 | 236 | [NFL.com](https://www.nfl.com/teams/baltimore-ravens/) |

The eight strongest opponent-adjusted margins and the eight weakest are separated by more than thirty points per game, which is the gap the model is reading when it puts San Francisco and Jacksonville above Los Angeles and Baltimore in Week 11.

## Why no line is presented as a recommendation

Three reasons, in order of importance. First, there is no market price, so there is nothing to compare an estimate against - a model line without a price is not a bet. Second, the improvement over the league-constant benchmark has a confidence interval that still contains zero (flag F-07), so the model has not demonstrated skill over noise. Third, the public Week 10 injury report omits players on injured reserve, so a material part of the availability picture is missing from the inputs (flag F-03).

Note the one place where the two ends of the table meet: San Francisco has the league's best adjusted margin and faces Minnesota, while Jacksonville has the second-best and faces a New York Giants team whose own numbers are mid-pack. Neither the injury picture nor a price is available to refine either matchup further.

## Source links

- Official Week 11 schedule: <https://www.nfl.com/schedules/2026/by-week/week-11>
- Official standings: <https://www.nfl.com/standings/>
- Official Week 10 injury report: <https://www.nfl.com/injuries/>
- Official team pages: linked per row.

