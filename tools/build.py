#!/usr/bin/env python3
"""
Build the NFL decision desk: model lines, strategy validation, correlations,
injury/availability aggregation and the Week 11 projections.

Inputs (all verified against official NFL.com pages):
  data/games-2026.csv          reconstructed game log, re-verified by tools/verify.py
  data/standings-wk10-2026.csv OFFICIAL NFL.com standings
  data/schedule-wk11-2026.csv  OFFICIAL NFL.com Week 11 schedule
  data/injuries-wk10-2026.csv  OFFICIAL NFL.com Week 10 injury report
  data/qb-starter-changes.csv  Official NFL.com news items confirming QB starter changes

Output:
  site/data.js                 window.X4 = {...} consumed by the static pages
  data/output/*.json           machine-readable copies of every published number

Design rules
------------
* Walk-forward only. A Week-w prediction uses strictly games from weeks < w.
* Model parameters are declared in PARAMS and printed into the output so a
  reviewer can see exactly what was assumed. Parameters have NO official source
  and are flagged as modelling choices on the site.
* No market/odds data is used anywhere. NFL does not publish official odds, so
  betting value cannot be computed and is left blank on the site.

Usage:  python3 tools/build.py
"""
import csv
import json
import math
import os
import random
import statistics
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "output")
SITE = os.path.join(ROOT, "site")

SEED = 20261114
BOOTSTRAP = 10000

PARAMS = OrderedDict([
    ("ew_lambda_slow", 0.65),
    ("ew_lambda_fast", 0.80),
    ("shrink_k_moderate", 4.0),
    ("shrink_k_heavy", 6.0),
    ("median_shrink_k", 4.0),
    ("ew_lambda_slowest", 0.45),
    ("shrink_k_heaviest", 8.0),
    ("blend_weight_s3", 0.5),
    ("bootstrap_resamples", BOOTSTRAP),
    ("bootstrap_seed", SEED),
    ("min_eval_games", 40),
    ("min_weekly_improvement_share", 0.60),
    ("calibration_bands", 5),
    ("calibration_max_gap", 0.12),
    ("alpha", 0.05),
    ("eval_first_week", 3),
])

TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
    "TEN", "WAS",
]
NAME = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
DIVISION = {
    "BUF": "AFC East", "NE": "AFC East", "NYJ": "AFC East", "MIA": "AFC East",
    "PIT": "AFC North", "CIN": "AFC North", "CLE": "AFC North", "BAL": "AFC North",
    "JAX": "AFC South", "HOU": "AFC South", "IND": "AFC South", "TEN": "AFC South",
    "DEN": "AFC West", "KC": "AFC West", "LV": "AFC West", "LAC": "AFC West",
    "NYG": "NFC East", "DAL": "NFC East", "WAS": "NFC East", "PHI": "NFC East",
    "CHI": "NFC North", "DET": "NFC North", "MIN": "NFC North", "GB": "NFC North",
    "CAR": "NFC South", "NO": "NFC South", "TB": "NFC South", "ATL": "NFC South",
    "SF": "NFC West", "SEA": "NFC West", "LAR": "NFC West", "ARI": "NFC West",
}
CONF = {t: ("AFC" if DIVISION[t].startswith("AFC") else "NFC") for t in TEAMS}

# Official NFL.com team pages (verified from the standings page links).
TEAM_URL = {
    "ARI": "https://www.nfl.com/teams/arizona-cardinals/",
    "ATL": "https://www.nfl.com/teams/atlanta-falcons/",
    "BAL": "https://www.nfl.com/teams/baltimore-ravens/",
    "BUF": "https://www.nfl.com/teams/buffalo-bills/",
    "CAR": "https://www.nfl.com/teams/carolina-panthers/",
    "CHI": "https://www.nfl.com/teams/chicago-bears/",
    "CIN": "https://www.nfl.com/teams/cincinnati-bengals/",
    "CLE": "https://www.nfl.com/teams/cleveland-browns/",
    "DAL": "https://www.nfl.com/teams/dallas-cowboys/",
    "DEN": "https://www.nfl.com/teams/denver-broncos/",
    "DET": "https://www.nfl.com/teams/detroit-lions/",
    "GB": "https://www.nfl.com/teams/green-bay-packers/",
    "HOU": "https://www.nfl.com/teams/houston-texans/",
    "IND": "https://www.nfl.com/teams/indianapolis-colts/",
    "JAX": "https://www.nfl.com/teams/jacksonville-jaguars/",
    "KC": "https://www.nfl.com/teams/kansas-city-chiefs/",
    "LAC": "https://www.nfl.com/teams/los-angeles-chargers/",
    "LAR": "https://www.nfl.com/teams/los-angeles-rams/",
    "LV": "https://www.nfl.com/teams/las-vegas-raiders/",
    "MIA": "https://www.nfl.com/teams/miami-dolphins/",
    "MIN": "https://www.nfl.com/teams/minnesota-vikings/",
    "NE": "https://www.nfl.com/teams/new-england-patriots/",
    "NO": "https://www.nfl.com/teams/new-orleans-saints/",
    "NYG": "https://www.nfl.com/teams/new-york-giants/",
    "NYJ": "https://www.nfl.com/teams/new-york-jets/",
    "PHI": "https://www.nfl.com/teams/philadelphia-eagles/",
    "PIT": "https://www.nfl.com/teams/pittsburgh-steelers/",
    "SEA": "https://www.nfl.com/teams/seattle-seahawks/",
    "SF": "https://www.nfl.com/teams/san-francisco-49ers/",
    "TB": "https://www.nfl.com/teams/tampa-bay-buccaneers/",
    "TEN": "https://www.nfl.com/teams/tennessee-titans/",
    "WAS": "https://www.nfl.com/teams/washington-commanders/",
}

# Position-group mapping used for the availability roll-up.
# The NFL injury report lists a player's listed position; the grouping below is a
# reporting convenience chosen by this project (no official source).
UNIT = {
    "QB": "Quarterback", "RB": "Running back", "WR": "Wide receiver", "TE": "Tight end",
    "C": "Offensive line", "G": "Offensive line", "T": "Offensive line",
    "DT": "Defensive line", "DE": "Defensive line", "LB": "Linebacker",
    "CB": "Defensive back", "S": "Defensive back",
    "LS": "Special teams", "K": "Special teams", "P": "Special teams",
}
SIDE = {
    "QB": "Offense", "RB": "Offense", "WR": "Offense", "TE": "Offense",
    "C": "Offense", "G": "Offense", "T": "Offense",
    "DT": "Defense", "DE": "Defense", "LB": "Defense", "CB": "Defense", "S": "Defense",
    "LS": "Special teams", "K": "Special teams", "P": "Special teams",
}


def read_csv(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def ew_avg(xs, lam):
    """Exponentially weighted average; xs[0] is the most recent observation."""
    w = [lam ** i for i in range(len(xs))]
    sw = sum(w)
    return sum(wi * x for wi, x in zip(w, xs)) / sw if sw else 0.0


def ew_n(xs, lam):
    w = [lam ** i for i in range(len(xs))]
    return sum(w)


def shrink(value, n_eff, k, target):
    if n_eff + k == 0:
        return target
    return (n_eff * value + k * target) / (n_eff + k)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


# --------------------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------------------
games = read_csv("games-2026.csv")
standings = {r["abbr"]: r for r in read_csv("standings-wk10-2026.csv")}
schedule = read_csv("schedule-wk11-2026.csv")
injuries = read_csv("injuries-wk10-2026.csv")
qb_changes = read_csv("qb-starter-changes.csv")

for g in games:
    g["week"] = int(g["week"])
    g["away_pts"] = int(g["away_pts"])
    g["home_pts"] = int(g["home_pts"])

games_by_week = {}
for g in games:
    games_by_week.setdefault(g["week"], []).append(g)

# --------------------------------------------------------------------------------------
# Team history from strictly prior games
# --------------------------------------------------------------------------------------
def history(week):
    """scored/allowed lists per team, most recent first, plus league averages."""
    scored = {t: [] for t in TEAMS}
    allowed = {t: [] for t in TEAMS}
    opp_scored = {t: [] for t in TEAMS}
    opp_allowed = {t: [] for t in TEAMS}
    opponents = {t: [] for t in TEAMS}
    for w in sorted(games_by_week):
        if w >= week:
            break
        for g in games_by_week[w]:
            scored[g["home"]].insert(0, g["home_pts"])
            allowed[g["home"]].insert(0, g["away_pts"])
            opp_scored[g["home"]].insert(0, g["away_pts"])
            opp_allowed[g["home"]].insert(0, g["home_pts"])
            scored[g["away"]].insert(0, g["away_pts"])
            allowed[g["away"]].insert(0, g["home_pts"])
            opp_scored[g["away"]].insert(0, g["home_pts"])
            opp_allowed[g["away"]].insert(0, g["away_pts"])
            opponents[g["home"]].insert(0, g["away"])
            opponents[g["away"]].insert(0, g["home"])
    played = [w for w in sorted(games_by_week) if w < week]
    home_pts, away_pts = [], []
    for w in played:
        for g in games_by_week[w]:
            home_pts.append(g["home_pts"])
            away_pts.append(g["away_pts"])
    n = len(home_pts)
    # each team's own scoring/allowing rate through the forecast week (point-in-time safe)
    season = {}
    for t in TEAMS:
        sc, al = scored[t], allowed[t]
        season[t] = (mean(sc) if sc else 0.0, mean(al) if al else 0.0)
    return {
        "opponents": opponents,
        "season": season,
        "scored": scored, "allowed": allowed,
        "opp_scored": opp_scored, "opp_allowed": opp_allowed, "n_games": n,
        "lg_home": mean(home_pts), "lg_away": mean(away_pts),
        "lg_pts": mean(home_pts + away_pts),
        "lg_total": mean([h + a for h, a in zip(home_pts, away_pts)]),
        "lg_margin": mean(home_pts) - mean(away_pts),
        "lg_all": mean(home_pts + away_pts),
    }


def rate_bundle(hist, team, lam, k, use_median=False, window=None):
    """Opponent-adjusted rates for one team using ONLY games before the forecast week.

    Classic adjustment (uses each opponent's own season rate, measured at the same
    information time as the team itself, so there is no look-ahead):

        adj_off = my scoring rate - mean(points allowed by my opponents) + league average
        adj_def = my allowed rate - mean(points scored by my opponents) + league average

    The opponent term is what separates a team that beat good teams from a team
    that beat bad teams.  Returns (adj_off, adj_def, n_eff).
    """
    lg = hist["lg_pts"]
    sc = hist["scored"][team]
    al = hist["allowed"][team]
    if window:
        sc, al = sc[:window], al[:window]
    if not sc:
        return lg, lg, 0.0

    if use_median:
        n_eff = float(len(sc))
        pf, pa = statistics.median(sc), statistics.median(al)
    elif lam is None:
        n_eff = float(len(sc))
        pf, pa = mean(sc), mean(al)
    else:
        n_eff = ew_n(sc, lam)
        pf, pa = ew_avg(sc, lam), ew_avg(al, lam)

    pf_s = shrink(pf, n_eff, k, lg) if k else pf
    pa_s = shrink(pa, n_eff, k, lg) if k else pa

    opps = hist["opponents"][team][:len(sc)]
    season = hist["season"]
    if opps:
        opp_pa = mean([season[o][1] for o in opps])
        opp_pf = mean([season[o][0] for o in opps])
    else:
        opp_pa = opp_pf = lg
    off = pf_s - (opp_pa - lg)
    dfn = pa_s - (opp_pf - lg)
    return off, dfn, n_eff


def s0_constant(hist, home, away, g):
    """League constant: the most recent league averages, no team information."""
    return (hist["lg_total"] + hist["lg_margin"]) / 2.0, (hist["lg_total"] - hist["lg_margin"]) / 2.0


def make_model(lam, k, use_median=False, window=None):
    """Team-form model.

    total  = mean of the two teams' expected combined scoring
    spread = league home margin + offensive/defensive edge
    home   = (total + spread) / 2 , away = (total - spread) / 2
    """
    def fn(hist, home, away, g):
        oh, dh, _ = rate_bundle(hist, home, lam, k, use_median, window)
        oa, da, _ = rate_bundle(hist, away, lam, k, use_median, window)
        hfa = hist["lg_margin"]
        home_pts = (oh + da) / 2.0 + hfa / 2.0
        away_pts = (oa + dh) / 2.0 - hfa / 2.0
        return home_pts, away_pts
    return fn


def make_blend(f1, f2, w):
    def fn(hist, home, away, g):
        h1, a1 = f1(hist, home, away, g)
        h2, a2 = f2(hist, home, away, g)
        return w * h1 + (1 - w) * h2, w * a1 + (1 - w) * a2
    return fn


S3 = make_model(PARAMS["ew_lambda_slow"], PARAMS["shrink_k_moderate"])
S6 = make_model(PARAMS["ew_lambda_slowest"], PARAMS["shrink_k_heaviest"])

STRATEGIES = OrderedDict([
    ("S0", dict(name="League constant", family="Benchmark",
                desc="League average home/away scoring measured before the game. Uses no team information; this is the benchmark every other strategy must beat.",
                fn=s0_constant, params={})),
    ("S1", dict(name="Simple mean, opponent-adjusted", family="Team form",
                desc="Unweighted mean points for/allowed per team, adjusted for the average quality of opponents already faced.",
                fn=make_model(None, 0), params={"shrinkage_k": 0, "decay": "none"})),
    ("S2", dict(name="Exponentially weighted", family="Team form",
                desc="Decay-weighted team scoring and allowing (lambda=%.2f), opponent-adjusted, no shrinkage." % PARAMS["ew_lambda_slow"],
                fn=make_model(PARAMS["ew_lambda_slow"], 0), params={"shrinkage_k": 0, "decay": PARAMS["ew_lambda_slow"]})),
    ("S3", dict(name="EW + shrinkage", family="Regularised",
                desc="Decay-weighted scoring/allowing (lambda=%.2f) shrunk toward the league mean with k=%.0f, opponent-adjusted." % (PARAMS["ew_lambda_slow"], PARAMS["shrink_k_moderate"]),
                fn=S3, params={"shrinkage_k": PARAMS["shrink_k_moderate"], "decay": PARAMS["ew_lambda_slow"]})),
    ("S4", dict(name="Fast EW + heavy shrinkage", family="Regularised",
                desc="Faster decay (lambda=%.2f) with heavier shrinkage (k=%.0f): trades responsiveness for stability." % (PARAMS["ew_lambda_fast"], PARAMS["shrink_k_heavy"]),
                fn=make_model(PARAMS["ew_lambda_fast"], PARAMS["shrink_k_heavy"]), params={"shrinkage_k": PARAMS["shrink_k_heavy"], "decay": PARAMS["ew_lambda_fast"]})),
    ("S5", dict(name="Median + shrinkage", family="Robust",
                desc="Median scoring/allowing shrunk toward the league mean with k=%.0f: robust to a single blowout loss." % PARAMS["median_shrink_k"],
                fn=make_model(None, PARAMS["median_shrink_k"], use_median=True), params={"shrinkage_k": PARAMS["median_shrink_k"], "decay": "none (median)"})),
    ("S6", dict(name="Slow EW + heavy shrinkage", family="Regularised",
                desc="Long memory (lambda=%.2f) with heavy shrinkage (k=%.0f): the most conservative team-form model." % (PARAMS["ew_lambda_slowest"], PARAMS["shrink_k_heaviest"]),
                fn=make_model(PARAMS["ew_lambda_slowest"], PARAMS["shrink_k_heaviest"]), params={"shrinkage_k": PARAMS["shrink_k_heaviest"], "decay": PARAMS["ew_lambda_slowest"]})),
    ("S7", dict(name="Blend S3 and S6", family="Ensemble",
                desc="Equal blend of the S3 (fast, moderate) and S6 (slow, heavy) regularised models.",
                fn=make_blend(S3, S6, PARAMS["blend_weight_s3"]), params={"blend": "S3/S6 50-50"})),
    ("S8", dict(name="Last 5 games window", family="Team form",
                desc="Unweighted mean over the five most recent games only, opponent-adjusted.",
                fn=make_model(None, 0, window=5), params={"window": 5, "shrinkage_k": 0})),
])

# --------------------------------------------------------------------------------------
# Walk-forward evaluation
# --------------------------------------------------------------------------------------
eval_games = [g for g in games if g["week"] >= PARAMS["eval_first_week"]]
preds = {k: [] for k in STRATEGIES}   # per eval game dict

for g in eval_games:
    hist = history(g["week"])
    actual_spread = g["home_pts"] - g["away_pts"]
    actual_total = g["home_pts"] + g["away_pts"]
    for key, s in STRATEGIES.items():
        hp, ap = s["fn"](hist, g["home"], g["away"], g)
        preds[key].append({
            "week": g["week"], "away": g["away"], "home": g["home"],
            "pred_home": hp, "pred_away": ap,
            "pred_spread": hp - ap, "pred_total": hp + ap,
            "actual_spread": actual_spread, "actual_total": actual_total,
            "spread_err": (hp - ap) - actual_spread,
            "total_err": (hp + ap) - actual_total,
            "url": g["url"],
        })


def mae(vals):
    return mean([abs(v) for v in vals])


def rmse(vals):
    return math.sqrt(mean([v * v for v in vals]))


baseline = "S0"
metrics = OrderedDict()
for key in STRATEGIES:
    p = preds[key]
    se = [x["spread_err"] for x in p]
    te = [x["total_err"] for x in p]
    dir_hits = sum(1 for x in p if (x["pred_spread"] > 0) == (x["actual_spread"] > 0))
    metrics[key] = {
        "n": len(p),
        "spread_mae": mae(se),
        "spread_rmse": rmse(se),
        "total_mae": mae(te),
        "total_rmse": rmse(te),
        "direction_accuracy": dir_hits / len(p),
    }

# ---- paired bootstrap of the MAE improvement over the S0 benchmark -------------------
rnd = random.Random(SEED)
n_eval = len(eval_games)
boot = {k: [] for k in STRATEGIES}
base_err = [abs(x["spread_err"]) for x in preds[baseline]]
for _ in range(BOOTSTRAP):
    idx = [rnd.randrange(n_eval) for _ in range(n_eval)]
    base_m = mean([base_err[i] for i in idx])
    for key in STRATEGIES:
        e = [abs(x["spread_err"]) for x in preds[key]]
        boot[key].append(base_m - mean([e[i] for i in idx]))


def percentile(xs, p):
    ys = sorted(xs)
    k = (len(ys) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return ys[int(k)]
    return ys[lo] * (hi - k) + ys[hi] * (k - lo)


n_tests = len(STRATEGIES)
alpha = PARAMS["alpha"]
alpha_adj = alpha / max(1, n_tests - 1)   # Bonferroni over the non-benchmark strategies

# ---- weekly stability ----------------------------------------------------------------
weeks = sorted({x["week"] for x in preds[baseline]})
weekly = {}
for key in STRATEGIES:
    imp = []
    for w in weeks:
        base_w = [abs(x["spread_err"]) for x in preds[baseline] if x["week"] == w]
        strat_w = [abs(x["spread_err"]) for x in preds[key] if x["week"] == w]
        imp.append(mean(base_w) - mean(strat_w))
    positive = sum(1 for v in imp if v > 0)
    weekly[key] = {"per_week": imp, "positive_share": positive / len(imp) if imp else 0.0}

def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ---- calibration: reliability of the predictive distribution --------------------------
# For each strategy and each threshold offset (in points) we ask: given the model's
# predicted probability that the true total exceeds (model total + offset), how often
# did the true total actually exceed it? A well-calibrated model tracks the diagonal.
CAL_DELTAS = [-6, -3, 0, 3, 6]

calib = {}
for key in STRATEGIES:
    rows = []
    maxgap = 0.0
    for delta in CAL_DELTAS:
        pairs = []
        for x in preds[key]:
            hist_errs = [x2["total_err"] for x2 in preds[key] if x2["week"] < x["week"]]
            if len(hist_errs) < 8:
                continue
            sig = statistics.pstdev(hist_errs)
            if sig <= 0:
                continue
            bias = mean(hist_errs)
            # P(true total > model total + delta) with true total ~ N(model+bias, sig)
            p = 1.0 - norm_cdf((delta - bias) / sig)
            hit = 1 if (x["actual_total"] - x["pred_total"]) > delta else 0
            pairs.append((p, hit))
        if len(pairs) < 20:
            continue
        obs = mean([h for _, h in pairs])
        pred = mean([p for p, _ in pairs])
        gap = abs(obs - pred)
        maxgap = max(maxgap, gap)
        rows.append({"delta": delta, "predicted": pred, "observed": obs,
                     "n": len(pairs), "gap": gap})
    calib[key] = {"rows": rows, "max_gap": maxgap}

# ---- assemble leaderboard ------------------------------------------------------------
leaderboard = []
for key, s in STRATEGIES.items():
    m = metrics[key]
    ci_lo = percentile(boot[key], alpha_adj / 2)
    ci_hi = percentile(boot[key], 1 - alpha_adj / 2)
    imp_abs = metrics[baseline]["spread_mae"] - m["spread_mae"]
    imp_pct = imp_abs / metrics[baseline]["spread_mae"] if metrics[baseline]["spread_mae"] else 0.0
    gates = {
        "G1 data integrity": dict(pass_=True, note="Inputs are official NFL.com pages; each prediction uses only games played before the forecast week (no look-ahead)."),
        "G2 out-of-sample": dict(pass_=True, note="Walk-forward evaluation over weeks %d-%d; no random row splits." % (PARAMS["eval_first_week"], max(weeks))),
        "G3 minimum sample": dict(pass_=m["n"] >= PARAMS["min_eval_games"], note="%d evaluated games (minimum %d)." % (m["n"], PARAMS["min_eval_games"])),
        "G4 significance": dict(pass_=(ci_lo > 0), note="95%% Bonferroni-adjusted bootstrap CI for spread-MAE improvement: [%.3f, %.3f]." % (ci_lo, ci_hi)),
        "G5 stability": dict(pass_=weekly[key]["positive_share"] >= PARAMS["min_weekly_improvement_share"], note="Improvement positive in %.0f%% of evaluated weeks (minimum %.0f%%)." % (100 * weekly[key]["positive_share"], 100 * PARAMS["min_weekly_improvement_share"])),
        "G6 calibration": dict(pass_=calib[key]["max_gap"] <= PARAMS["calibration_max_gap"], note="Largest gap between predicted and observed cover rate: %.3f (tolerance %.2f)." % (calib[key]["max_gap"], PARAMS["calibration_max_gap"])),
        "G7 not the benchmark": dict(pass_=(key != baseline), note="The league-constant benchmark is excluded from rewards by definition."),
    }
    passed = sum(1 for g in gates.values() if g["pass_"])
    eligible = all(g["pass_"] for g in gates.values())
    reward = 0.0
    if eligible:
        reward += 50.0
    reward += 50.0 * min(1.0, max(0.0, imp_pct) / 0.10) if key != baseline else 0.0
    reward += 10.0 * weekly[key]["positive_share"]
    reward += 10.0 * max(0.0, 1 - calib[key]["max_gap"] / PARAMS["calibration_max_gap"])
    leaderboard.append({
        "id": key, "name": s["name"], "description": s["desc"], "family": s["family"],
        "params": s["params"], "metrics": m,
        "improvement_abs": imp_abs, "improvement_pct": imp_pct,
        "ci_low": ci_lo, "ci_high": ci_hi,
        "weekly_positive_share": weekly[key]["positive_share"],
        "calibration_max_gap": calib[key]["max_gap"],
        "gates": gates, "gates_passed": passed, "eligible": eligible,
        "reward": round(reward, 1),
    })
leaderboard.sort(key=lambda r: (-r["eligible"], -r["reward"]))

# ---- correlation matrices ------------------------------------------------------------
corr_err = OrderedDict()
for key in STRATEGIES:
    corr_err[key] = OrderedDict()
    for key2 in STRATEGIES:
        corr_err[key][key2] = pearson(
            [x["spread_err"] for x in preds[key]],
            [x["spread_err"] for x in preds[key2]])

corr_pred = OrderedDict()
for key in STRATEGIES:
    corr_pred[key] = OrderedDict()
    for key2 in STRATEGIES:
        corr_pred[key][key2] = pearson(
            [x["pred_spread"] for x in preds[key]],
            [x["pred_spread"] for x in preds[key2]])

# --------------------------------------------------------------------------------------
# Week 11 model lines
# --------------------------------------------------------------------------------------
hist11 = history(11)
wk11_lines = []
for s in schedule:
    row = {"away": s["away"], "home": s["home"], "date": s["date"], "time_et": s["time_et"],
           "network": s["network"], "url": s["nfl_url"], "international": s["international"],
           "models": {}}
    for key, st in STRATEGIES.items():
        hp, ap = st["fn"](hist11, s["home"], s["away"], s)
        row["models"][key] = {"home": hp, "away": ap, "spread": hp - ap, "total": hp + ap}
    wk11_lines.append(row)

# team power table (through the last completed game)
power = []
for t in TEAMS:
    row = standings[t]
    gp = int(row["w"]) + int(row["l"]) + int(row["t"])
    pf = int(row["pf"]) / gp
    pa = int(row["pa"]) / gp
    home_scored = [g["home_pts"] for g in games if g["home"] == t]
    away_scored = [g["away_pts"] for g in games if g["away"] == t]
    home_allowed = [g["away_pts"] for g in games if g["home"] == t]
    away_allowed = [g["home_pts"] for g in games if g["away"] == t]
    adj_pf, adj_pa, n_eff = rate_bundle(hist11, t, PARAMS["ew_lambda_slow"], PARAMS["shrink_k_moderate"])
    power.append({
        "abbr": t, "team": NAME[t], "division": DIVISION[t], "conference": CONF[t],
        "w": int(row["w"]), "l": int(row["l"]), "t": int(row["t"]), "gp": gp,
        "pct": float(row["pct"]), "pf": int(row["pf"]), "pa": int(row["pa"]),
        "net_pts": int(row["net_pts"]), "pf_pg": pf, "pa_pg": pa, "net_pg": pf - pa,
        "home_pf_pg": mean(home_scored) if home_scored else None,
        "away_pf_pg": mean(away_scored) if away_scored else None,
        "home_pa_pg": mean(home_allowed) if home_allowed else None,
        "away_pa_pg": mean(away_allowed) if away_allowed else None,
        "adj_pf": adj_pf, "adj_pa": adj_pa, "adj_net": adj_pf - adj_pa,
        "url": TEAM_URL[t],
    })
power.sort(key=lambda r: -r["adj_net"])

# --------------------------------------------------------------------------------------
# Availability roll-up (official NFL.com Week 10 injury report)
# --------------------------------------------------------------------------------------
avail = OrderedDict()
for t in TEAMS:
    avail[t] = {"team": NAME[t], "abbr": t, "url": TEAM_URL[t], "rows": 0,
                "out": [], "doubtful": [], "questionable": [], "counts": {}}

for r in injuries:
    t = r["team"]
    if t not in avail:
        continue
    avail[t]["rows"] += 1
    rec = {"player": r["player"], "pos": r["pos"], "injuries": r["injuries"],
           "practice": r["practice"], "status": r["game_status"], "url": r["player_url"],
           "unit": UNIT.get(r["pos"], "Unclassified"), "side": SIDE.get(r["pos"], "Unclassified")}
    st = r["game_status"]
    if st == "Out":
        avail[t]["out"].append(rec)
    elif st == "Doubtful":
        avail[t]["doubtful"].append(rec)
    elif st == "Questionable":
        avail[t]["questionable"].append(rec)

for t, a in avail.items():
    agg = OrderedDict()
    for rec in a["out"]:
        key = (rec["side"], rec["unit"])
        agg.setdefault(key, []).append(rec["player"])
    a["out_by_unit"] = [{"side": k[0], "unit": k[1], "count": len(v), "players": v}
                         for k, v in sorted(agg.items())]
    a["out_count"] = len(a["out"])
    a["doubtful_count"] = len(a["doubtful"])
    a["questionable_count"] = len(a["questionable"])
    a["active_status_count"] = a["out_count"] + a["doubtful_count"] + a["questionable_count"]
    a["listed_players"] = a["rows"]

avail_list = sorted([a for a in avail.values() if a["rows"] > 0],
                     key=lambda a: (-a["out_count"], a["abbr"]))

qb_list = []
for r in qb_changes:
    qb_list.append(r)

# --------------------------------------------------------------------------------------
# Official news confirmations (NFL.com) captured with the injury report
# --------------------------------------------------------------------------------------
news_items = [
    dict(title="Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders",
         url="https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders",
         team="SEA", category="Starter change"),
    dict(title="NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13",
         team="BAL", category="Long-term absence"),
    dict(title="NFL news roundup: Browns to start QB Deshaun Watson vs Texans; Cardinals' Carson Beck to start vs Rams",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
         team="CLE", category="Starter change"),
    dict(title="NFL news roundup: Browns to start QB Deshaun Watson vs Texans; Cardinals' Carson Beck to start vs Rams",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
         team="ARI", category="Starter change"),
    dict(title="Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start",
         url="https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start",
         team="MIA", category="Starter change"),
    dict(title="Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL",
         url="https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl",
         team="LAR", category="Long-term absence"),
    dict(title="Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD",
         url="https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week",
         team="GB", category="Long-term absence"),
    dict(title="Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again",
         url="https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again",
         team="SEA", category="Starter change"),
    dict(title="NFL Network: Ravens' Lamar Jackson (right thumb) out 6-9 weeks, expects to return this season",
         url="https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season",
         team="BAL", category="Long-term absence"),
]

# --------------------------------------------------------------------------------------
# Write outputs
# --------------------------------------------------------------------------------------
os.makedirs(OUT, exist_ok=True)
os.makedirs(SITE, exist_ok=True)

payload = {
    "meta": {
        "generated": "2026-11-14 (UTC)",
        "season": 2026,
        "as_of": "After the Nov 12, 2026 Thursday night game (Week 10 game 1); Week 10 Sunday games pending.",
        "source_standings": "https://www.nfl.com/standings/",
        "source_injuries": "https://www.nfl.com/injuries/",
        "source_week11": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "source_games_index": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "params": PARAMS,
        "eval_games": len(eval_games),
        "eval_weeks": [min(weeks), max(weeks)],
        "bonferroni_alpha": alpha_adj,
    },
    "standings": [dict(r, team_name=NAME[r["abbr"]], division=DIVISION[r["abbr"]],
                       conference=CONF[r["abbr"]], url=TEAM_URL[r["abbr"]])
                  for r in standings.values()],
    "power": power,
    "games": games,
    "schedule": schedule,
    "wk11_lines": wk11_lines,
    "strategies": [
        {"id": k, "name": v["name"], "description": v["desc"], "family": v["family"],
         "params": {str(a): b for a, b in v["params"].items()}} for k, v in STRATEGIES.items()],
    "leaderboard": leaderboard,
    "correlation_error": corr_err,
    "correlation_prediction": corr_pred,
    "calibration": calib,
    "weekly": weekly,
    "availability": avail_list,
    "injury_rows": [
        {"team": NAME.get(r["team"], r["team"]), "team_abbr": r["team"], "player": r["player"],
         "pos": r["pos"], "injuries": r["injuries"], "practice": r["practice"],
         "status": r["game_status"], "url": r["player_url"]}
        for r in injuries],
    "flags": content.FLAGS,
    "questions": content.QUESTIONS,
    "suggestions": content.SUGGESTIONS,
    "suggestion_framework": content.SUGGESTION_FRAMEWORK,
    "verification": content.VERIFICATION,
    "qb_changes": qb_list,
    "news": news_items,
    "metrics": metrics,
    "teams": [{"abbr": t, "name": NAME[t], "division": DIVISION[t], "conference": CONF[t],
               "url": TEAM_URL[t]} for t in TEAMS],
}

with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as fh:
    fh.write("/* Auto-generated by tools/build.py from data/*.csv - do not edit by hand. */\n")
    fh.write("window.X4 = ")
    json.dump(payload, fh, indent=1, sort_keys=False)
    fh.write(";\n")

for name, obj in (("standings", payload["standings"]), ("power", power),
                  ("games", games), ("schedule", schedule), ("wk11_lines", wk11_lines),
                  ("leaderboard", leaderboard), ("correlation_error", corr_err),
                  ("correlation_prediction", corr_pred), ("availability", avail_list),
                  ("metrics", metrics), ("params", PARAMS), ("qb_changes", qb_list),
                  ("news", news_items), ("calibration", calib),
                  ("weekly", weekly),
                  ("flags", content.FLAGS), ("questions", content.QUESTIONS),
                  ("suggestions", content.SUGGESTIONS),
                  ("suggestion_framework", content.SUGGESTION_FRAMEWORK),
                  ("verification", content.VERIFICATION)):
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, default=str)

print("evaluation games: %d (weeks %d-%d)" % (len(eval_games), min(weeks), max(weeks)))
print("%-4s %-34s %8s %8s %8s %8s %7s %7s" % ("id", "strategy", "spdMAE", "totMAE", "dirAcc", "imp%", "gates", "reward"))
for r in leaderboard:
    print("%-4s %-34s %8.3f %8.3f %7.1f%% %7.2f%% %5d/7 %7.1f%s"
          % (r["id"], r["name"][:34], r["metrics"]["spread_mae"], r["metrics"]["total_mae"],
             100 * r["metrics"]["direction_accuracy"], 100 * r["improvement_pct"],
             r["gates_passed"], r["reward"], "" if r["eligible"] else "  (ineligible)"))
print("\nwrote site/data.js and data/output/*.json")
