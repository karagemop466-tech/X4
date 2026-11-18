# Correlation and luck control

Computed by `tools/build.py` over the 118 out-of-sample games (Weeks 3-10). Underlying results: <https://www.nfl.com/schedules/2026/> and <https://www.nfl.com/standings/>.

## Why this is on the site at all

If two strategies make the same mistakes on the same games, they are one signal counted twice. Ranking them against each other tells the reader the desk holds more independent evidence than it does, and building a combination from the two looks like diversification when it is not.

## Spread-error correlation

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|---|
| S0 | 1.000 | 0.946 | 0.919 | 0.977 | 0.980 | 0.971 | 0.979 | 0.979 | 0.943 |
| S1 | 0.946 | 1.000 | 0.981 | 0.965 | 0.963 | 0.978 | 0.948 | 0.957 | 0.995 |
| S2 | 0.919 | 0.981 | 1.000 | 0.959 | 0.950 | 0.958 | 0.938 | 0.949 | 0.986 |
| S3 | 0.977 | 0.965 | 0.959 | 1.000 | 0.999 | 0.991 | 0.998 | 0.999 | 0.967 |
| S4 | 0.980 | 0.963 | 0.950 | 0.999 | 1.000 | 0.992 | 0.998 | 0.999 | 0.963 |
| S5 | 0.971 | 0.978 | 0.958 | 0.991 | 0.992 | 1.000 | 0.985 | 0.989 | 0.973 |
| S6 | 0.979 | 0.948 | 0.938 | 0.998 | 0.998 | 0.985 | 1.000 | 0.999 | 0.949 |
| S7 | 0.979 | 0.957 | 0.949 | 0.999 | 0.999 | 0.989 | 0.999 | 1.000 | 0.958 |
| S8 | 0.943 | 0.995 | 0.986 | 0.967 | 0.963 | 0.973 | 0.949 | 0.958 | 1.000 |

## What the matrix says

**Near-identical (0.98 and above):** S6-S7 (0.999), S4-S7 (0.999), S3-S7 (0.999), S3-S4 (0.999), S4-S6 (0.998), S3-S6 (0.998), S1-S8 (0.995), S4-S5 (0.992), S3-S5 (0.991), S5-S7 (0.989), S2-S8 (0.986), S5-S6 (0.985), S1-S2 (0.981).

**Strongly related (0.90 to 0.98):** S0-S4 (0.980), S0-S6 (0.979), S0-S7 (0.979), S1-S5 (0.978), S0-S3 (0.977), S5-S8 (0.973), S0-S5 (0.971), S3-S8 (0.967), S1-S3 (0.965), S1-S4 (0.963), S4-S8 (0.963), S2-S3 (0.959), S7-S8 (0.958), S2-S5 (0.958), S1-S7 (0.957), S2-S4 (0.950), S6-S8 (0.949), S2-S7 (0.949), S1-S6 (0.948), S0-S1 (0.946), S0-S8 (0.943), S2-S6 (0.938), S0-S2 (0.919).

**Largely independent (below 0.90):** .

## Prediction correlation

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|---|
| S0 | 1.000 | 0.059 | -0.081 | -0.040 | 0.003 | 0.073 | -0.020 | -0.031 | 0.059 |
| S1 | 0.059 | 1.000 | 0.877 | 0.602 | 0.563 | 0.772 | 0.322 | 0.472 | 0.953 |
| S2 | -0.081 | 0.877 | 1.000 | 0.720 | 0.613 | 0.697 | 0.443 | 0.593 | 0.914 |
| S3 | -0.040 | 0.602 | 0.720 | 1.000 | 0.983 | 0.835 | 0.936 | 0.984 | 0.650 |
| S4 | 0.003 | 0.563 | 0.613 | 0.983 | 1.000 | 0.853 | 0.954 | 0.985 | 0.590 |
| S5 | 0.073 | 0.772 | 0.697 | 0.835 | 0.853 | 1.000 | 0.699 | 0.781 | 0.740 |
| S6 | -0.020 | 0.322 | 0.443 | 0.936 | 0.954 | 0.699 | 1.000 | 0.983 | 0.371 |
| S7 | -0.031 | 0.472 | 0.593 | 0.984 | 0.985 | 0.781 | 0.983 | 1.000 | 0.520 |
| S8 | 0.059 | 0.953 | 0.914 | 0.650 | 0.590 | 0.740 | 0.371 | 0.520 | 1.000 |

## Consequence for the leaderboard

The regularised family (S3, S4, S6, S7) is effectively a single signal: those pairs fail on the same games. The leaderboard keeps them as separate rows for transparency, but a strategy that fails a gate on its own cannot borrow strength from a near-duplicate that passes it.

This is the concrete mechanism for removing luck from the equation. It is not enough for a strategy to beat the benchmark; it has to beat it with a signal that is not already being counted.

## Practical rule for combinations

A parlay or prop combination built from two legs whose error correlation is above roughly 0.95 is close to a single bet priced twice. Multiplying marginal probabilities in that situation overstates the joint probability of the combination winning, and the overstatement compounds with every extra leg. Each combination therefore has to be priced from a joint estimate and compared against the same legs taken singly.

## What is still missing

These correlations are between **model** strategies. The correlation that actually matters for a parlay is between **market legs** - two player props or two spreads priced by the same book - and that cannot be computed here, because no licensed odds feed has been authorised (flag F-01). The matrix above is the correlation between our own candidate signals, which is the part we can measure honestly.

## Source links

- Official schedule and results: <https://www.nfl.com/schedules/2026/>
- Official standings: <https://www.nfl.com/standings/>

