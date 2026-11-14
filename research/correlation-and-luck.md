# Correlation and luck control

Computed by `tools/build.py` over the 105 out-of-sample games (Weeks 3-10). Underlying results: <https://www.nfl.com/schedules/2026/> and <https://www.nfl.com/standings/>.

## Why this is on the site at all

If two strategies make the same mistakes on the same games, they are one signal counted twice. Ranking them against each other tells the reader the desk holds more independent evidence than it does, and building a combination from the two looks like diversification when it is not.

## Spread-error correlation

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|---|
| S0 | 1.000 | 0.943 | 0.920 | 0.975 | 0.977 | 0.969 | 0.976 | 0.976 | 0.943 |
| S1 | 0.943 | 1.000 | 0.983 | 0.962 | 0.959 | 0.975 | 0.943 | 0.953 | 0.997 |
| S2 | 0.920 | 0.983 | 1.000 | 0.958 | 0.949 | 0.958 | 0.936 | 0.948 | 0.985 |
| S3 | 0.975 | 0.962 | 0.958 | 1.000 | 0.999 | 0.991 | 0.998 | 0.999 | 0.964 |
| S4 | 0.977 | 0.959 | 0.949 | 0.999 | 1.000 | 0.991 | 0.998 | 0.999 | 0.960 |
| S5 | 0.969 | 0.975 | 0.958 | 0.991 | 0.991 | 1.000 | 0.984 | 0.988 | 0.973 |
| S6 | 0.976 | 0.943 | 0.936 | 0.998 | 0.998 | 0.984 | 1.000 | 0.999 | 0.945 |
| S7 | 0.976 | 0.953 | 0.948 | 0.999 | 0.999 | 0.988 | 0.999 | 1.000 | 0.955 |
| S8 | 0.943 | 0.997 | 0.985 | 0.964 | 0.960 | 0.973 | 0.945 | 0.955 | 1.000 |

## What the matrix says

**Near-identical (0.98 and above):** S6-S7 (0.999), S3-S7 (0.999), S4-S7 (0.999), S3-S4 (0.999), S4-S6 (0.998), S3-S6 (0.998), S1-S8 (0.997), S4-S5 (0.991), S3-S5 (0.991), S5-S7 (0.988), S2-S8 (0.985), S5-S6 (0.984), S1-S2 (0.983).

**Strongly related (0.90 to 0.98):** S0-S4 (0.977), S0-S7 (0.976), S0-S6 (0.976), S0-S3 (0.975), S1-S5 (0.975), S5-S8 (0.973), S0-S5 (0.969), S3-S8 (0.964), S1-S3 (0.962), S4-S8 (0.960), S1-S4 (0.959), S2-S3 (0.958), S2-S5 (0.958), S7-S8 (0.955), S1-S7 (0.953), S2-S4 (0.949), S2-S7 (0.948), S6-S8 (0.945), S0-S8 (0.943), S1-S6 (0.943), S0-S1 (0.943), S2-S6 (0.936), S0-S2 (0.920).

**Largely independent (below 0.90):** .

## Prediction correlation

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|---|
| S0 | 1.000 | 0.005 | -0.159 | -0.101 | -0.052 | 0.021 | -0.058 | -0.081 | 0.000 |
| S1 | 0.005 | 1.000 | 0.885 | 0.572 | 0.527 | 0.749 | 0.293 | 0.438 | 0.976 |
| S2 | -0.159 | 0.885 | 1.000 | 0.686 | 0.578 | 0.678 | 0.415 | 0.558 | 0.903 |
| S3 | -0.101 | 0.572 | 0.686 | 1.000 | 0.984 | 0.832 | 0.941 | 0.985 | 0.604 |
| S4 | -0.052 | 0.527 | 0.578 | 0.984 | 1.000 | 0.847 | 0.958 | 0.985 | 0.549 |
| S5 | 0.021 | 0.749 | 0.678 | 0.832 | 0.847 | 1.000 | 0.698 | 0.776 | 0.730 |
| S6 | -0.058 | 0.293 | 0.415 | 0.941 | 0.958 | 0.698 | 1.000 | 0.985 | 0.329 |
| S7 | -0.081 | 0.438 | 0.558 | 0.985 | 0.985 | 0.776 | 0.985 | 1.000 | 0.473 |
| S8 | 0.000 | 0.976 | 0.903 | 0.604 | 0.549 | 0.730 | 0.329 | 0.473 | 1.000 |

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

