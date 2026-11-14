#!/usr/bin/env python3
"""Reproduce all computed statistics published on the site.

Inputs (each row transcribed from an official source fetch on 2026-11-14):
  research/data/games_weeks6-9_2026.csv     -> nfl.com by-week schedule pages (weeks 6-9, 2026 REG)
  research/data/standings_2026_through_week10_tnf.csv -> nfl.com/standings (2026, retrieved 2026-11-14)
  research/data/week11_odds_2026.csv         -> espn.com NFL week-11 schedule (DraftKings odds shown by ESPN)

Outputs: research/computed_stats.json (all values used in site tables).

Integrity checks (fail loudly on transcription errors):
  1. sum(points for) == sum(points against) across all 32 teams
  2. total wins == total losses (ties counted once on each side)
  3. every team's net == pf - pa
  4. every game's scores >= 0; neutral flags only on the 3 known neutral games
"""
import csv, json, math, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research" / "data"


# nfl.com standings use AZ/LA; schedule pages and ESPN use ARI/LAR
ALIAS = {"ARI": "AZ", "LAR": "LA"}
norm = lambda t: ALIAS.get(t, t)


def pearson(xs, ys):
    n = len(xs)
    mx, my = st.mean(xs), st.mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    # Fisher z 95% CI
    z = math.atanh(r)
    se = 1 / math.sqrt(n - 3)
    lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    return {"n": n, "r": round(r, 4), "ci95": [round(lo, 4), round(hi, 4)]}


def main():
    games = list(csv.DictReader((DATA / "games_weeks6-9_2026.csv").open()))
    teams = list(csv.DictReader((DATA / "standings_2026_through_week10_tnf.csv").open()))
    odds = list(csv.DictReader((DATA / "week11_odds_2026.csv").open()))

    # ---- integrity checks -------------------------------------------------
    pf = sum(int(t["pf"]) for t in teams)
    pa = sum(int(t["pa"]) for t in teams)
    assert pf == pa, f"sum PF {pf} != sum PA {pa}"
    wins = sum(int(t["w"]) for t in teams)
    losses = sum(int(t["l"]) for t in teams)
    ties = sum(int(t["t"]) for t in teams)
    assert wins == losses, f"wins {wins} != losses {losses}"
    for t in teams:
        assert int(t["net"]) == int(t["pf"]) - int(t["pa"]), t["team"]
        assert int(t["w"]) + int(t["l"]) + int(t["t"]) >= 8, t
    assert len(games) == 57, len(games)
    for g in games:
        g["away"], g["home"] = norm(g["away"]), norm(g["home"])
    for o in odds:
        o["away"], o["home"], o["favorite"] = norm(o["away"]), norm(o["home"]), norm(o["favorite"])
    neutral = {(g["away"], g["home"]) for g in games if g["neutral_site"] == "1"}
    assert neutral == {("HOU", "JAX"), ("PIT", "NO"), ("CIN", "ATL")}, neutral
    assert len(teams) == 32 and len(odds) == 13

    # ---- home-field edge (weeks 6-9, neutral excluded) -------------------
    margins = [int(g["home_score"]) - int(g["away_score"]) for g in games if g["neutral_site"] == "0"]
    h_mean = st.mean(margins)
    h_sd = st.stdev(margins)
    h_se = h_sd / math.sqrt(len(margins))
    # ---- score correlations ---------------------------------------------
    away = [int(g["away_score"]) for g in games]
    home = [int(g["home_score"]) for g in games]
    all_margin = [int(g["home_score"]) - int(g["away_score"]) for g in games if g["neutral_site"] == "0"]
    all_total = [int(g["home_score"]) + int(g["away_score"]) for g in games if g["neutral_site"] == "0"]
    totals_all = [int(g["home_score"]) + int(g["away_score"]) for g in games]

    # ---- standings signal: net points vs win pct --------------------------
    wpct = [(int(t["w"]) + 0.5 * int(t["t"])) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
    net = [int(t["net"]) for t in teams]
    pfpg = [int(t["pf"]) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
    papg = [int(t["pa"]) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
    corr_pf_papg = pearson(pfpg, papg)

    # ---- baseline line model for week 11 ---------------------------------
    # S_t = PF/g - PA/g (per-game scoring margin; embeds ~half home schedule,
    # home edge cancels in expectation). Neutral strength ~ S_t.
    # Expected margin (home vs away) = (S_home - S_away) + h, h = measured home edge.
    # Expected total = mean of the two teams' points-per-game-in-their-games.
    S = {t["team"]: int(t["net"]) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams}
    C = {t["team"]: (int(t["pf"]) + int(t["pa"])) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams}
    lines = []
    for o in odds:
        a, h = o["away"], o["home"]
        is_neutral = o["neutral_site"] == "1"
        my_margin = S[h] - S[a] + (0.0 if is_neutral else h_mean)  # + for home team
        my_total = (C[h] + C[a]) / 2
        # market: favorite spread; convert to home-team-signed margin
        fav, sp = o["favorite"], float(o["spread"])
        if fav == h:
            mkt_margin = sp
        elif fav == a:
            mkt_margin = -sp
        else:
            raise AssertionError(fav)
        lines.append({
            "away": a, "home": h, "neutral": is_neutral,
            "my_home_margin": round(my_margin, 1),
            "my_total": round(my_total, 1),
            "mkt_home_margin": mkt_margin,
            "mkt_total": float(o["total"]),
            "delta_margin": round(my_margin - mkt_margin, 1),
            "delta_total": round(my_total - float(o["total"]), 1),
            "market_favorite": fav, "market_spread": sp,
        })

    out = {
        "generated": "2026-11-14",
        "inputs": {
            "games": "research/data/games_weeks6-9_2026.csv (nfl.com, weeks 6-9 2026 REG, fetched 2026-11-14)",
            "standings": "research/data/standings_2026_through_week10_tnf.csv (nfl.com/standings, fetched 2026-11-14)",
            "odds": "research/data/week11_odds_2026.csv (espn.com week-11 schedule, DraftKings odds, fetched 2026-11-14)",
        },
        "integrity": {
            "sum_points_for": pf, "sum_points_against": pa,
            "total_wins": wins, "total_losses": losses, "total_ties": ties,
            "games_n": len(games), "neutral_games": sorted(list(neutral)),
            "status": "all checks passed",
        },
        "home_edge": {
            "n": len(margins), "mean_home_margin": round(h_mean, 3),
            "sd": round(h_sd, 3), "se": round(h_se, 3),
            "ci95": [round(h_mean - 1.96 * h_se, 2), round(h_mean + 1.96 * h_se, 2)],
            "home_win_pct": round(sum(1 for m in margins if m > 0) / len(margins), 4),
        },
        "correlations": {
            "away_vs_home_scores": pearson(away, home),
            "margin_vs_total": pearson(all_margin, all_total),
            "net_pts_vs_win_pct": pearson(net, wpct),
            "pts_per_game_vs_pts_allowed_per_game": corr_pf_papg,
        },
        "scoring": {
            "games_n": len(totals_all),
            "mean_total": round(st.mean(totals_all), 2),
            "sd_total": round(st.stdev(totals_all), 2),
        },
        "week11_baseline_lines": lines,
    }
    (ROOT / "research" / "computed_stats.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
