#!/usr/bin/env python3
"""
Originate our own NFL numbers, in the order the brief fixes.

  1. the SIDE (point spread)
  2. the TOTAL
  3. the MONEYLINE

Every output row keeps the three numbers apart, because they answer three
different questions and merging them would hide the one that matters:

    fair_*      our own number for the market
    market_*    what the book had, at the snapshot the store recorded
    diff_*      fair - market, signed so that a positive diff means we make the
                side we are quoting more likely than the market does

What "fair" means here, precisely
---------------------------------
A ratio model on opponent-adjusted scoring rates:

    strength(t) = (PF/g - PA/g) of t, shrunk toward 0 by k games' worth of
                  league-average prior  ->  strength'(t) = strength(t) * g/(g+k)
    total(t)    = (PF/g + PA/g)/2, shrunk the same way
    fair_side   = strength'(home) - strength'(away) + home_edge
    fair_total  = total'(home) + total'(away) + 0

`home_edge` is computed from the official game log, not assumed, and carries its
own n and confidence interval. The shrinkage is a prior, not a fudge: a club with
one game played is pulled hard toward the league mean and a club with sixteen is
pulled barely at all. Both parameters (`k`, and whether the home edge is applied)
are printed in the model card and are the only tunables.

What this file does NOT do
--------------------------
It does not invent a price for a market the store has no market number for. A
market with no cached reading is skipped and counted, never filled in.

Inputs   data/games-2026.csv, data/standings-wk10-2026.csv, data/ops/*.csv
Outputs  data/ops/markets.csv, fair_lines.csv, graded.csv,
         scores_signal.csv, scores_staking.csv, paper_demotions.csv, depth.csv,
         results.csv
"""
import csv
import glob
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = os.path.join(ROOT, "data", "ops")
DATA = os.path.join(ROOT, "data")
TXN = os.path.join(ROOT, "data", "transactions")

# ---- model card: the only tunables in the file -----------------------------
PRIOR_GAMES = 4.0        # k: how many league-average games to shrink toward
USE_HOME_EDGE = True     # the measured edge, not a constant
KICKOFF_BUFFER_MIN = 60  # a reading must precede kickoff by at least this much

# ---- the validation gates, with numeric thresholds ------------------------
GATES = [
    ("G1", "Data integrity", ">=1 reading per market, all with a source URL and a UTC stamp", None),
    ("G2", "Sample sufficiency", "n >= 100 settled bets per market type", 100),
    ("G3", "Out-of-sample", "graded on events never used to fit the model", None),
    ("G4", "Probability quality", "Brier score better than the market's Brier score", 0.0),
    ("G5", "Significance", "one-sided p < 0.05 on the skill score", 0.05),
    ("G6", "Multiplicity", "Bonferroni-adjusted p < 0.05 across all trials", 0.05),
    ("G7", "Stability", "no single week contributes more than 50% of the skill", 0.50),
    ("G8", "Shadow period", "a further pre-registered segment with no gate regression", None),
]


# ---------------------------------------------------------------------------
# small statistics helpers (standard library only, deterministic)
# ---------------------------------------------------------------------------
def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def sd(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def erf(x):
    """Abramowitz & Stegun 7.1.26, |error| < 1.5e-7. Deterministic, no scipy."""
    sign = -1 if x < 0 else 1
    x = abs(x)
    t = 1.0 / (1.0 + 0.3275911 * x)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t
                - 0.284496736) * t + 0.254829592) * t * math.exp(-x * x)
    return sign * y


def norm_cdf(x):
    return 0.5 * (1.0 + erf(x / math.sqrt(2.0)))


def two_sided_p(z):
    return max(0.0, min(1.0, 2.0 * (1.0 - norm_cdf(abs(z)))))


def poisson_line_prob(mu, line):
    """P(total > line) for a Poisson total with mean mu, and P(over) on a push-free line."""
    if line is None or mu <= 0:
        return ""
    k = math.floor(line)
    # P(X > k) for integer k
    cdf = 0.0
    term = math.exp(-mu)
    cdf = term
    for i in range(1, k + 1):
        term *= mu / i
        cdf += term
    return max(1e-6, min(1 - 1e-6, 1.0 - cdf))


def american_to_dec(a):
    if a in ("", None):
        return None
    try:
        x = float(str(a).replace("\u2212", "-"))
    except ValueError:
        return None
    if x == 0:
        return None
    return 1.0 + (x / 100.0 if x > 0 else 100.0 / abs(x))


def dec_to_american(d):
    if not d or d <= 1.0:
        return ""
    if d >= 2.0:
        return "%+.0f" % ((d - 1.0) * 100.0)
    return "%+.0f" % (-100.0 / (d - 1.0))


def fmt(x, nd=1):
    return "" if x in ("", None) else ("%." + str(nd) + "f") % float(x)


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------
def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def team_ratings(standings, through_week):
    """Opponent-adjusted scoring rates with a shrinkage prior toward the league mean."""
    rows = [r for r in standings if r.get("abbr")]
    pf = {r["abbr"]: float(r["pf"]) for r in rows}
    pa = {r["abbr"]: float(r["pa"]) for r in rows}
    gp = {r["abbr"]: float(int(r["w"]) + int(r["l"]) + int(r["t"])) for r in rows}
    league_pf = sum(pf.values()) / sum(gp.values()) if gp else 0.0
    league_pa = sum(pa.values()) / sum(gp.values()) if gp else 0.0
    out = {}
    for t in pf:
        g = gp[t]
        w = g / (g + PRIOR_GAMES) if (g + PRIOR_GAMES) else 0.0
        # shrunk toward the league mean, per game
        diff = ((pf[t] - pa[t]) / g) if g else 0.0
        tot = ((pf[t] + pa[t]) / 2.0 / g) if g else 0.0
        out[t] = {
            "gp": g,
            "diff_raw": diff,
            "diff": diff * w,
            "total_raw": tot,
            "total": tot * w + (1 - w) * ((league_pf + league_pa) / 2.0),
            "off": (pf[t] / g) if g else 0.0,
            "def": (pa[t] / g) if g else 0.0,
        }
    return out


# ---------------------------------------------------------------------------
# walk-forward inputs: nothing dated at or after kickoff may enter a line
# ---------------------------------------------------------------------------
def ratings_from_log(games, through_week):
    """Team ratings computed from the official game log through `through_week`.

    The log is the corpus tools/verify.py proves against NFL.com, so a rating
    built from it is built from official results. For through_week = 10 this
    reproduces data/standings-wk10-2026.csv exactly, and main() asserts it.
    """
    pf, pa, gp = {}, {}, {}
    for g in games:
        if int(g["week"]) > through_week:
            continue
        try:
            hp, ap = int(g["home_pts"]), int(g["away_pts"])
        except (ValueError, KeyError):
            continue
        h, a = g["home"], g["away"]
        pf[h] = pf.get(h, 0) + hp
        pa[h] = pa.get(h, 0) + ap
        gp[h] = gp.get(h, 0) + 1
        pf[a] = pf.get(a, 0) + ap
        pa[a] = pa.get(a, 0) + hp
        gp[a] = gp.get(a, 0) + 1
    if not gp:
        return {}
    league_pf = sum(pf.values()) / sum(gp.values())
    league_pa = sum(pa.values()) / sum(gp.values())
    out = {}
    for t in pf:
        g = gp[t]
        w = g / (g + PRIOR_GAMES) if (g + PRIOR_GAMES) else 0.0
        diff = (pf[t] - pa[t]) / g
        tot = ((pf[t] + pa[t]) / 2.0) / g
        out[t] = {"gp": float(g), "diff_raw": diff, "diff": diff * w,
                  "total_raw": tot,
                  "total": tot * w + (1 - w) * ((league_pf + league_pa) / 2.0),
                  "off": pf[t] / g, "def": pa[t] / g}
    return out


def edge_label(event_week):
    """The edge window as a range label, e.g. "weeks 6-9"."""
    w = edge_window(event_week)
    if not w:
        return "weeks 0-0"
    return "weeks %d-%d" % (w[0], w[-1])


def edge_window(event_week):
    """The weeks the home edge is fitted on, for an event in `event_week`.

    The registered rule (Week 11: weeks 6-9) is weeks [W-5, W-2] of the event's
    own week. Applied to Week 11 that is exactly weeks 6, 7, 8 and 9, so the
    pre-registered forward window is unchanged; applied walk-forward it never
    uses a week at or after the event's own week.
    """
    return [w for w in range(event_week - 5, event_week - 1) if w >= 1]


def walk_forward_rows(games, min_week=4):
    """One prediction per official game, made only from what was known before it.

    A game in week W is predicted from ratings through week W-1 and a home edge
    fitted on weeks [W-5, W-2]. The residual of that prediction against the
    official final score is the model's out-of-sample error.
    """
    rows = []
    for g in games:
        wk = int(g["week"])
        if wk < min_week:
            continue
        rt = ratings_from_log(games, wk - 1)
        if g["home"] not in rt or g["away"] not in rt:
            continue
        edge = home_edge(games, edge_window(wk))
        hh = 0.0 if (g["away"], g["home"]) in NEUTRAL else (edge["mean"] if edge["n"] else 0.0)
        mu_margin = (rt[g["home"]]["diff"] - rt[g["away"]]["diff"]) + hh
        mu_total = rt[g["home"]]["total"] + rt[g["away"]]["total"]
        try:
            margin = int(g["home_pts"]) - int(g["away_pts"])
            total = int(g["home_pts"]) + int(g["away_pts"])
        except (ValueError, KeyError):
            continue
        rows.append({"week": wk, "away": g["away"], "home": g["home"], "url": g["url"],
                     "edge_n": edge["n"], "edge": hh,
                     "mu_margin": mu_margin, "mu_total": mu_total,
                     "margin": margin, "total": total,
                     "res_margin": margin - mu_margin, "res_total": total - mu_total})
    return rows


def model_dispersion(rows, games):
    """The model's own predictive dispersion, measured out of sample.

    Two dispersions are published for every market because they answer
    different questions: the residual dispersion of the walk-forward prediction
    (how wide the model is, given the model) and the league dispersion of the
    same quantity (how wide the league is, given the official results). The
    brief asks for both to stay visible with the gap between them until a
    walk-forward comparison says which one to use.
    """
    res_m = [r["res_margin"] for r in rows]
    res_t = [r["res_total"] for r in rows]
    margins = [int(g["home_pts"]) - int(g["away_pts"]) for g in games]
    totals = [int(g["home_pts"]) + int(g["away_pts"]) for g in games]
    weeks = sorted({r["week"] for r in rows})
    return {
        "sigma_margin_model": sd(res_m),
        "sigma_total_model": sd(res_t),
        "n": len(rows),
        "window": ("weeks %d-%d of the official game log" % (weeks[0], weeks[-1])) if weeks else "",
        "sigma_margin_league": sd(margins),
        "sigma_total_league": sd(totals),
        "league_n": len(margins),
        "method": ("residual standard deviation of the walk-forward prediction (ratings through W-1, "
                   "home edge over weeks [W-5, W-2]) against the official final score"),
    }


def interval_coverage(rows, resid_key, sigma):
    """Share of walk-forward outcomes inside the model's own 95% interval."""
    if not rows or not sigma:
        return 0.0
    inside = sum(1 for r in rows if abs(r[resid_key]) <= 1.96 * sigma)
    return inside / len(rows)


def brier(probs, outcomes):
    """Mean squared error of a probability forecast."""
    if not probs:
        return 0.0
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def norm_ppf(p):
    """Inverse standard normal CDF by bisection on norm_cdf (deterministic)."""
    p = min(1.0 - 1e-9, max(1e-9, float(p)))
    lo, hi = -12.0, 12.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def home_edge(games, weeks):
    """Measured home-field margin from the official log, with n and a 95% interval."""
    margins = []
    for g in games:
        if int(g["week"]) not in weeks:
            continue
        try:
            margins.append(int(g["home_pts"]) - int(g["away_pts"]))
        except (ValueError, KeyError):
            continue
    n = len(margins)
    if n < 2:
        return {"n": n, "mean": 0.0, "sd": 0.0, "ci": ("", ""), "home_win_pct": ""}
    m, s = mean(margins), sd(margins)
    se = s / math.sqrt(n)
    return {"n": n, "mean": m, "sd": s, "se": se,
            "ci": (m - 1.96 * se, m + 1.96 * se),
            "home_win_pct": 100.0 * sum(1 for x in margins if x > 0) / n,
            "push_pct": 100.0 * sum(1 for x in margins if x == 0) / n}


# ---------------------------------------------------------------------------
# event identity
# ---------------------------------------------------------------------------
MARKET_ORDER = {"side": 0, "total": 1, "moneyline": 2}


def neutral_games():
    """The 2026 international games, read from the official schedule labels.

    A game played abroad is a neutral-site game, so the home-field term must not
    be applied on top of it. This used to be a hand-typed set of three pairs and
    it was wrong: week 10's Munich game (Patriots at Lions) was missing, and a
    home edge was being applied to a game played in Germany. The set is now read
    from data/international-2026.csv, where every row carries the official weekly
    schedule page that labels the game as an International Game.
    """
    path = os.path.join(DATA, "international-2026.csv")
    return {(r["away"], r["home"]) for r in read_csv(path)}


NEUTRAL = neutral_games()


def resolve_events(events, games):
    """Bind each ESPN event to its official NFL pairing, and prove the binding.

    The odds payload names a team only in its `details` string ("HOU -10"), and
    only when there is a favourite. That gives us one anchor per game: the id of
    the favourite equals the abbreviation in `details`. The opponent is then read
    off the *official* NFL game log - the event must match exactly one game whose
    favourite is on the side the payload says it is on - and the binding is only
    accepted if the resulting pair is unique in that week.

    Anything ambiguous is left unresolved and reported. A wrong pairing would
    silently mis-grade every market on that game, so this is a fail-closed step.
    """
    by_week = {}
    for g in games:
        by_week.setdefault(int(g["week"]), []).append(g)

    resolved, unresolved = [], []
    for e in events:
        wk = int(e["week"])
        fav = (e.get("favorite_name") or "").upper()
        side = e.get("favorite_side") or ""
        if not fav or not side:
            unresolved.append({"event_id": e["event_id"], "week": wk,
                               "reason": "no cached odds body for this event, or the payload "
                                         "names no favourite (pick'em)"})
            continue
        cands = []
        for g in by_week.get(wk, []):
            if side == "home" and g["home"] == fav:
                cands.append(g)
            elif side == "away" and g["away"] == fav:
                cands.append(g)
        if len(cands) != 1:
            unresolved.append({"event_id": e["event_id"], "week": wk,
                               "reason": "%d official games match favourite %s at %s"
                                         % (len(cands), fav, side)})
            continue
        g = cands[0]
        resolved.append({
            "event_id": e["event_id"], "week": wk,
            "away": g["away"], "home": g["home"],
            "away_espn_id": e["away_espn_id"], "home_espn_id": e["home_espn_id"],
            "favorite": fav, "favorite_side": side,
            "anchor": "favourite %s == ESPN id on the %s side" % (fav, side),
            "official_url": g["url"],
            "binding_proof": "unique official Week %d game with %s at %s" % (wk, fav, side),
        })
        # the opponent's id is the other id on the payload
        opp_id = e["home_espn_id"] if side == "away" else e["away_espn_id"]
        opp = g["home"] if side == "away" else g["away"]
        resolved[-1]["opponent_id"] = opp_id
        resolved[-1]["opponent"] = opp

    # a resolved pair must be unique within its week
    seen = {}
    final = []
    for r in resolved:
        key = (r["week"], r["away"], r["home"])
        if key in seen:
            unresolved.append({"event_id": r["event_id"], "week": r["week"],
                               "reason": "pair %s at %s duplicated in week %d"
                                         % (r["away"], r["home"], r["week"])})
            continue
        seen[key] = r
        final.append(r)
    return final, unresolved


def official_fixtures():
    """Every official NFL fixture we know of: played weeks from the game log,
    unplayed weeks from the published schedule. Used only to bind an ESPN event
    to an official pairing - never to invent a score."""
    fixtures = []
    for g in read_csv(os.path.join(DATA, "games-2026.csv")):
        fixtures.append({"week": int(g["week"]), "away": g["away"], "home": g["home"],
                         "played": "1", "url": g["url"],
                         "away_pts": g["away_pts"], "home_pts": g["home_pts"]})
    played = {(f["week"], f["away"], f["home"]) for f in fixtures}
    for path in sorted(glob.glob(os.path.join(DATA, "schedule-wk*.csv"))):
        for g in read_csv(path):
            key = (int(g["week"]), g["away"], g["home"])
            if key in played:
                continue          # a final already in the game log wins over the schedule
            fixtures.append({"week": int(g["week"]), "away": g["away"], "home": g["home"],
                             "played": "0", "url": g["nfl_url"],
                             "away_pts": "", "home_pts": ""})
    return fixtures


MODEL_OUTPUT_COLUMNS = [
    "event_id", "week", "away", "home", "market", "selection", "event",
    "model_line", "reference_line", "mu", "sigma", "sigma_n", "sigma_window",
    "sigma_method", "probability", "probability_pct", "probability_alt",
    "probability_alt_pct", "probability_gap_pts", "market_probability",
    "market_probability_basis", "away_gp", "home_gp", "away_diff", "home_diff",
    "away_total", "home_total", "home_edge", "edge_window", "edge_n",
    "ratings_through_week", "prior_games", "input_source", "official_url",
    "model", "notes",
]


def to_float(v):
    if v in ("", None):
        return None
    try:
        return float(str(v).replace("\u2212", "-").replace("+", ""))
    except (TypeError, ValueError):
        return None


def market_home_probability(snap_index, ev_id, phase="open"):
    """The de-vigged home probability from the captured moneyline prices.

    `phase` is "open" or "close". A missing price yields None: no probability
    is invented for a market the store never captured.
    """
    home = snap_index.get((ev_id, "moneyline", "home"), {})
    away = snap_index.get((ev_id, "moneyline", "away"), {})
    hp = to_float(home.get("%s_ml" % phase))
    ap = to_float(away.get("%s_ml" % phase))
    if not hp or not ap:
        return None
    ph = 100.0 / (hp + 100.0) if hp > 0 else (-hp) / (-hp + 100.0)
    pa = 100.0 / (ap + 100.0) if ap > 0 else (-ap) / (-ap + 100.0)
    if ph + pa <= 0:
        return None
    return ph / (ph + pa)


def probability_rows(ev_id, wk, away, home, fair_side_home, fair_total, p_home,
                     ra, rh, hh, sigma, edge, dispersion, snap_index, official_url,
                     ratings_through_week):
    """A probability and its inputs for every market we originate.

    The brief's rule is that a model output is a probability plus the inputs
    that produced it, never a bare pick. A side and a total are lines, so a
    probability only means something against a stated reference: the reference
    here is the market's captured opening line, and the event is spelled out on
    the row. Where no reference exists the probability is blank and the reason
    is recorded - it is never invented.
    """
    rows = []
    sig_m = dispersion["sigma_margin_model"]
    sig_t = dispersion["sigma_total_model"]
    sig_m_league = dispersion["sigma_margin_league"]
    sig_t_league = dispersion["sigma_total_league"]
    n_disp = dispersion["n"]
    win_disp = dispersion["window"]
    method = dispersion["method"]
    common = {
        "event_id": ev_id, "week": wk, "away": away, "home": home,
        "away_gp": "%d" % int(ra["gp"]), "home_gp": "%d" % int(rh["gp"]),
        "away_diff": fmt(ra["diff"], 2), "home_diff": fmt(rh["diff"], 2),
        "away_total": fmt(ra["total"], 2), "home_total": fmt(rh["total"], 2),
        "home_edge": fmt(hh, 2),
        "edge_window": edge_label(wk),
        "edge_n": str(edge["n"]),
        "ratings_through_week": str(ratings_through_week),
        "prior_games": fmt(PRIOR_GAMES, 1),
        "input_source": ("data/games-2026.csv (official game log, proved against NFL.com) "
                         "+ data/standings-wk10-2026.csv (official standings)"),
        "official_url": official_url,
        "model": "ratio, shrunk k=%s, walk-forward" % fmt(PRIOR_GAMES, 1),
    }

    # ---- the side: P(the home team covers the captured opening spread) -----
    side_snap = snap_index.get((ev_id, "side", "home"), {})
    line = to_float(side_snap.get("open_line"))
    row = dict(common)
    row.update({"market": "side", "selection": "home",
                "model_line": fmt(fair_side_home, 1),
                "reference_line": fmt(line, 1) if line is not None else "",
                "sigma": fmt(sig_m, 2), "sigma_n": str(n_disp), "sigma_window": win_disp,
                "sigma_method": method})
    if line is None:
        row.update({"event": "the home team covers the captured opening spread",
                    "mu": "", "probability": "", "probability_pct": "",
                    "probability_alt": "", "probability_alt_pct": "", "probability_gap_pts": "",
                    "market_probability": "",
                    "market_probability_basis": "no captured opening spread for this event",
                    "notes": "no market spread was captured for this event, so no cover event "
                             "is defined and no probability is published"})
    else:
        mu = fair_side_home + line          # distance from the model's margin to the cover threshold
        p = norm_cdf(mu / sig_m) if sig_m else 0.5
        p_alt = norm_cdf(mu / sig_m_league) if sig_m_league else p
        mkt = market_home_probability(snap_index, ev_id, "open")
        if mkt is not None:
            implied_margin = sig_m_league * norm_ppf(mkt)
            p_mkt = norm_cdf((implied_margin + line) / sig_m) if sig_m else 0.5
            basis = ("derived: the de-vigged captured opening moneyline probability (%s) converted "
                     "to an implied margin with the league margin dispersion (%s points, n = %d), "
                     "then to a cover probability at the captured opening spread"
                     % (fmt(mkt * 100.0, 1) + "%", fmt(sig_m_league, 2), dispersion["league_n"]))
        else:
            p_mkt, basis = "", ("no captured opening moneyline for this event, so no market "
                                "probability is derived")
        row.update({
            "event": "the home team covers the captured opening spread of %s" % fmt(line, 1),
            "mu": fmt(mu, 2),
            "probability": fmt(p, 4), "probability_pct": fmt(p * 100.0, 2),
            "probability_alt": fmt(p_alt, 4), "probability_alt_pct": fmt(p_alt * 100.0, 2),
            "probability_gap_pts": fmt((p - p_alt) * 100.0, 2),
            "market_probability": fmt(p_mkt, 4) if p_mkt != "" else "",
            "market_probability_basis": basis,
            "notes": ("primary sigma is the model's own out-of-sample margin dispersion; the "
                      "alternative column uses the league margin dispersion. Both are kept "
                      "visible with the gap until a walk-forward comparison says which to use."),
        })
    rows.append(row)

    # ---- the total: P(the game total goes over the captured opening total) --
    total_snap = snap_index.get((ev_id, "total", "over"), {})
    tot = to_float(total_snap.get("open_line"))
    row = dict(common)
    row.update({"market": "total", "selection": "over",
                "model_line": fmt(fair_total, 1),
                "reference_line": fmt(tot, 1) if tot is not None else "",
                "sigma": fmt(sig_t, 2), "sigma_n": str(n_disp), "sigma_window": win_disp,
                "sigma_method": method})
    if tot is None:
        row.update({"event": "the game total goes over the captured opening total",
                    "mu": "", "probability": "", "probability_pct": "",
                    "probability_alt": "", "probability_alt_pct": "", "probability_gap_pts": "",
                    "market_probability": "",
                    "market_probability_basis": "no captured opening total for this event",
                    "notes": "no market total was captured for this event, so no over/under "
                             "event is defined and no probability is published"})
    else:
        mu = fair_total - tot
        p = norm_cdf(mu / sig_t) if sig_t else 0.5
        p_alt = norm_cdf(mu / sig_t_league) if sig_t_league else p
        row.update({
            "event": "the game total goes over the captured opening total of %s" % fmt(tot, 1),
            "mu": fmt(mu, 2),
            "probability": fmt(p, 4), "probability_pct": fmt(p * 100.0, 2),
            "probability_alt": fmt(p_alt, 4), "probability_alt_pct": fmt(p_alt * 100.0, 2),
            "probability_gap_pts": fmt((p - p_alt) * 100.0, 2),
            "market_probability": "",
            "market_probability_basis": ("a posted total carries no probability: the market "
                                         "states a line, not a price for the over, so no market "
                                         "benchmark is defined for a total and none is invented"),
            "notes": ("primary sigma is the model's own out-of-sample total dispersion; the "
                      "alternative column uses the league total dispersion. Both are kept "
                      "visible with the gap until a walk-forward comparison says which to use."),
        })
    rows.append(row)

    # ---- the moneyline: P(the home team wins) -------------------------------
    p_mkt = market_home_probability(snap_index, ev_id, "open")
    p_alt = norm_cdf(fair_side_home / sig_m) if sig_m else p_home
    row = dict(common)
    row.update({
        "market": "moneyline", "selection": "home",
        "event": "the home team wins the game",
        "model_line": fmt(fair_side_home, 1), "reference_line": "",
        "mu": fmt(fair_side_home, 2),
        "sigma": fmt(sigma, 2), "sigma_n": str(edge["n"]),
        "sigma_window": "%s of the official game log" % edge_label(wk),
        "sigma_method": ("standard deviation of the official home margin in the model's own edge "
                         "window (the registered estimator)"),
        "probability": fmt(p_home, 4), "probability_pct": fmt(p_home * 100.0, 2),
        "probability_alt": fmt(p_alt, 4), "probability_alt_pct": fmt(p_alt * 100.0, 2),
        "probability_gap_pts": fmt((p_home - p_alt) * 100.0, 2),
        "market_probability": fmt(p_mkt, 4) if p_mkt is not None else "",
        "market_probability_basis": ("de-vigged from the captured opening moneyline prices"
                                     if p_mkt is not None else
                                     "no captured opening moneyline for this event"),
        "notes": ("the primary probability uses the registered sigma, so the pre-registered "
                  "Week 11 number is unchanged; the alternative column uses the model's own "
                  "out-of-sample margin dispersion and is the candidate for the next window, "
                  "which would have to be registered before it opens."),
    })
    rows.append(row)
    return rows


def originate():
    games = read_csv(os.path.join(DATA, "games-2026.csv"))
    fixtures = official_fixtures()
    standings = read_csv(os.path.join(DATA, "standings-wk10-2026.csv"))
    snapshots = read_csv(os.path.join(OPS, "price_snapshots.csv"))
    events = read_csv(os.path.join(OPS, "events.csv"))
    team_ids = {r["espn_id"]: r["nfl_abbr"] for r in read_csv(os.path.join(OPS, "team_ids.csv"))}

    # ---- the results feed: official scores, one row per completed game ------
    results = []
    for g in games:
        results.append({
            "week": g["week"], "away": g["away"], "home": g["home"],
            "away_pts": g["away_pts"], "home_pts": g["home_pts"], "ot": g.get("ot", ""),
            "neutral": "1" if (g["away"], g["home"]) in NEUTRAL else "0",
            "status": "final", "official_url": g["url"],
        })
    write_csv(os.path.join(OPS, "results.csv"),
              ["week", "away", "home", "away_pts", "home_pts", "ot", "neutral", "status", "official_url"],
              sorted(results, key=lambda r: (int(r["week"]), r["away"])))

    # ---- the ratings the forward window uses (official standings date) ------
    # Kept for the model card and for the Week 11 forward rows; the walk-forward
    # rows below rebuild the same ratings from the official game log.
    ratings = team_ratings(standings, 10)
    log_ratings_10 = ratings_from_log(games, 10)
    for t in sorted(ratings):
        for k in ("gp", "diff", "total", "off", "def"):
            if abs(ratings[t][k] - log_ratings_10[t][k]) > 1e-9:
                raise AssertionError("walk-forward ratings disagree with the official "
                                     "standings for %s (%s)" % (t, k))

    # ---- the model's own dispersion, measured out of sample ----------------
    wf_rows = walk_forward_rows(games)
    dispersion = model_dispersion(wf_rows, games)
    comparison = dispersion_comparison(wf_rows, dispersion)

    # the forward window's edge: weeks [11-5, 11-2] = weeks 6-9, the registered value
    edge_forward = home_edge(games, edge_window(11))

    # ---- the market registry, built strictly in the mandated order -----------
    resolved, unresolved = resolve_events(events, fixtures)
    write_csv(os.path.join(OPS, "event_identity.csv"),
              ["event_id", "week", "away", "home", "favorite", "favorite_side", "anchor",
               "official_url", "binding_proof", "opponent_id", "opponent", "away_espn_id",
               "home_espn_id"], resolved)
    write_csv(os.path.join(OPS, "event_identity_unresolved.csv"),
              ["event_id", "week", "reason"], unresolved)

    # the snapshot index: the captured market numbers each probability refers to
    snap_index = {}
    for s in snapshots:
        snap_index.setdefault((s["event_id"], s["market"], s["selection"]), s)

    markets, fair, outputs = [], [], []
    ratings_cache = {}
    for r in sorted(resolved, key=lambda x: (x["week"], x["event_id"])):
        ev_id, wk = r["event_id"], int(r["week"])
        away, home = r["away"], r["home"]
        # walk-forward: a line may only use what was known before its own week
        rt = ratings_cache.get(wk - 1)
        if rt is None:
            rt = ratings_from_log(games, wk - 1)
            ratings_cache[wk - 1] = rt
        if away not in rt or home not in rt:
            continue
        ra, rh = rt[away], rt[home]
        edge = home_edge(games, edge_window(wk))
        h = edge["mean"] if USE_HOME_EDGE else 0.0
        hh = 0.0 if (away, home) in NEUTRAL else h
        fair_side_home = (rh["diff"] - ra["diff"]) + hh
        fair_total = rh["total"] + ra["total"]
        # moneyline from the fair side, using the league's observed margin spread
        sigma = edge["sd"] if edge["sd"] else 13.7
        p_home = norm_cdf(fair_side_home / sigma) if sigma else 0.5
        p_home = min(1 - 1e-4, max(1e-4, p_home))

        # one market row per market type we originate, in the mandated order
        for mtype in ("side", "total", "moneyline"):
            m = {"event_id": ev_id, "week": wk, "away": away, "home": home,
                 "market": mtype, "order": MARKET_ORDER[mtype], "book": "DraftKings"}
            if mtype == "side":
                m.update(fair_home=fmt(fair_side_home, 1), lineup="home")
            elif mtype == "total":
                m.update(fair_home=fmt(fair_total, 1), lineup="over")
            else:
                m.update(fair_home=fmt(p_home * 100.0, 2) + "%",
                         fair_home_dec="%.4f" % (1.0 / p_home),
                         fair_away_dec="%.4f" % (1.0 / (1.0 - p_home)))
            markets.append(m)

        fair.append({
            "event_id": ev_id, "week": wk, "away": away, "home": home,
            "fair_side_home": fmt(fair_side_home, 1),
            "fair_total": fmt(fair_total, 1),
            "fair_ml_home_pct": fmt(p_home * 100.0, 2),
            "fair_ml_away_pct": fmt((1 - p_home) * 100.0, 2),
            "away_gp": "%d" % int(ra["gp"]), "home_gp": "%d" % int(rh["gp"]),
            "away_diff": fmt(ra["diff"], 2), "home_diff": fmt(rh["diff"], 2),
            "away_total": fmt(ra["total"], 2), "home_total": fmt(rh["total"], 2),
            "home_edge": fmt(hh, 2), "sigma": fmt(sigma, 1),
            "neutral": "1" if (away, home) in NEUTRAL else "0",
            "prior_games": fmt(PRIOR_GAMES, 1),
            "ratings_through_week": str(wk - 1),
            "edge_window": edge_label(wk),
            "edge_n": str(edge["n"]),
            "model": "ratio, shrunk k=%s, home edge %s (walk-forward: ratings through week %d, edge weeks %s)"
                     % (fmt(PRIOR_GAMES, 1), fmt(h, 2), wk - 1, edge_label(wk)),
        })

        # ---- the probability for every market, with its inputs --------------
        outputs.extend(probability_rows(
            ev_id, wk, away, home, fair_side_home, fair_total, p_home,
            ra, rh, hh, sigma, edge, dispersion, snap_index, r.get("official_url", ""),
            wk - 1))

    markets.sort(key=lambda m: (int(m["week"]), m["event_id"], m["order"]))
    write_csv(os.path.join(OPS, "markets.csv"),
              ["event_id", "week", "away", "home", "market", "order", "book", "lineup", "fair_home"],
              markets)
    write_csv(os.path.join(OPS, "fair_lines.csv"),
              ["event_id", "week", "away", "home", "fair_side_home", "fair_total",
               "fair_ml_home_pct", "fair_ml_away_pct", "away_gp", "home_gp",
               "away_diff", "home_diff", "away_total", "home_total", "home_edge", "sigma",
               "neutral", "prior_games", "ratings_through_week", "edge_window", "edge_n", "model"],
              sorted(fair, key=lambda r: (int(r["week"]), r["event_id"])))

    # ---- the probability store: every market, a probability and its inputs --
    write_csv(os.path.join(OPS, "model_outputs.csv"), MODEL_OUTPUT_COLUMNS,
              sorted(outputs, key=lambda r: (int(r["week"]), r["event_id"], MARKET_ORDER[r["market"]])))
    write_csv(os.path.join(OPS, "dispersion_comparison.csv"),
              ["quantity", "candidate", "sigma", "coverage_95", "brier", "verdict", "n", "window"],
              comparison)

    # ---- the model card -----------------------------------------------------
    card = {
        "generated_utc": "",  # stamped by ops.py
        "order": ["side", "total", "moneyline"],
        "prior_games": PRIOR_GAMES,
        "use_home_edge": USE_HOME_EDGE,
        "home_edge": {"n": edge_forward["n"], "mean": round(edge_forward["mean"], 3),
                      "sd": round(edge_forward["sd"], 3),
                      "ci95": [round(edge_forward["ci"][0], 3) if edge_forward["ci"][0] != "" else "",
                               round(edge_forward["ci"][1], 3) if edge_forward["ci"][1] != "" else ""],
                      "home_win_pct": round(edge_forward["home_win_pct"], 2) if edge_forward["home_win_pct"] != "" else "",
                      "window": "weeks 6-9 2026 (the forward window's own edge window [W-5, W-2])"},
        "sigma_margin": round(edge_forward["sd"], 2),
        "walk_forward": {
            "rule": ("a line for a game in week W uses ratings through week W-1 and a home edge "
                     "fitted on weeks [W-5, W-2]; nothing dated at or after kickoff enters a line"),
            "ratings_source": ("data/games-2026.csv (official game log, proved against NFL.com) "
                               "cross-checked against data/standings-wk10-2026.csv at week 10"),
            "edge_source": "data/games-2026.csv (official home margins)",
            "n_predictions": dispersion["n"],
            "window": dispersion["window"],
        },
        "dispersion": {
            "sigma_margin_model": round(dispersion["sigma_margin_model"], 3),
            "sigma_margin_league": round(dispersion["sigma_margin_league"], 3),
            "sigma_total_model": round(dispersion["sigma_total_model"], 3),
            "sigma_total_league": round(dispersion["sigma_total_league"], 3),
            "n": dispersion["n"],
            "league_n": dispersion["league_n"],
            "window": dispersion["window"],
            "method": dispersion["method"],
        },
        "dispersion_comparison": comparison,
        "probability_rule": {
            "side": ("P(the home team covers the captured opening spread) = Phi((fair margin + "
                     "posted home handicap) / sigma_margin_model)"),
            "total": ("P(the game total goes over the captured opening total) = Phi((fair total - "
                      "posted total) / sigma_total_model)"),
            "moneyline": ("P(the home team wins) = Phi(fair margin / sigma_margin), the registered "
                          "sigma, so the pre-registered Week 11 number is unchanged"),
            "market_benchmark": ("moneyline: the de-vigged captured price; side: derived from that "
                                 "price and the posted spread, labelled as derived; total: none, "
                                 "because a posted total carries no probability"),
            "store": "data/ops/model_outputs.csv",
        },
        "ratings": {t: {k: round(v, 3) for k, v in r.items()} for t, r in ratings.items()},
        "gates": [{"id": g[0], "name": g[1], "rule": g[2], "threshold": g[3]} for g in GATES],
        "n_markets": len(markets),
        "n_events_seen": len(events),
        "n_events_resolved": len(resolved),
        "n_events_unresolved": len(unresolved),
        "n_priced_events": len(fair),
    }
    with open(os.path.join(OPS, "model_card.json"), "w", encoding="utf-8") as fh:
        json.dump(card, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return markets, fair, snapshots, events, results, dispersion


# ---------------------------------------------------------------------------
# fair / market / difference, and grading
# ---------------------------------------------------------------------------
def fair_market_difference(markets, snapshots, results_by_pair):
    """One row per market with fair, market and difference in separate columns."""
    snap = {}
    for s in snapshots:
        k = (s["event_id"], s["market"], s["selection"])
        snap.setdefault(k, []).append(s)

    rows = []
    for m in markets:
        ev, wk, mtype = m["event_id"], m["week"], m["market"]
        pair = results_by_pair.get((int(wk), m["away"], m["home"]))
        row = {"event_id": ev, "week": wk, "away": m["away"], "home": m["home"],
               "market": mtype, "book": m.get("book", ""),
               "fair": "", "market_open": "", "market_close": "",
               "diff_vs_open": "", "diff_vs_close": "",
               "close_kind": "", "snapshot_utc": "", "source_url": "",
               "settled": "", "result": "", "official_result_url": ""}
        if mtype == "side":
            sh = snap.get((ev, "side", "home"), [])
            if sh:
                s = sh[0]
                row.update(fair=m["fair_home"], market_open=s["open_line"],
                           market_close=s["close_line"], close_kind=s["close_kind"],
                           snapshot_utc=s["retrieved_utc"], source_url=s["source_url"])
                # the store holds the home side's line; convert to a home margin
                def to_margin(txt):
                    if txt in ("", None):
                        return None
                    t = str(txt).replace("\u2212", "-").replace("+", "")
                    try:
                        return -float(t)   # a home line of -5.5 is a +5.5 margin
                    except ValueError:
                        return None
                mo, mc = to_margin(s["open_line"]), to_margin(s["close_line"])
                if m["fair_home"] != "":
                    fv = float(m["fair_home"])
                    if mo is not None:
                        row["diff_vs_open"] = fmt(fv - mo, 1)
                    if mc is not None:
                        row["diff_vs_close"] = fmt(fv - mc, 1)
            if pair:
                row.update(settled="1",
                           result="push" if pair["margin"] == 0 else "home" if pair["margin"] > 0 else "away",
                           official_result_url=pair["url"])
        elif mtype == "total":
            o = snap.get((ev, "total", "over"), [])
            if o:
                s = o[0]
                row.update(fair=m["fair_home"], market_open=s["open_line"],
                           market_close=s["close_line"], close_kind=s["close_kind"],
                           snapshot_utc=s["retrieved_utc"], source_url=s["source_url"])
                for key, col in (("open_line", "diff_vs_open"), ("close_line", "diff_vs_close")):
                    if s[key] and m["fair_home"] != "":
                        try:
                            row[col] = fmt(float(m["fair_home"]) - float(s[key]), 1)
                        except ValueError:
                            pass
            if pair:
                row.update(settled="1",
                           result="push" if pair["total"] == 0 else "over" if pair["total"] > 0 else "under",
                           official_result_url=pair["url"])
        else:
            home = snap.get((ev, "moneyline", "home"), [])
            if home:
                s = home[0]
                row.update(fair=m.get("fair_home", ""), market_open=s["open_ml"],
                           market_close=s["close_ml"], close_kind=s["close_kind"],
                           snapshot_utc=s["retrieved_utc"], source_url=s["source_url"])
                fv = m.get("fair_home_dec", "")
                for key, col in (("open_ml", "diff_vs_open"), ("close_ml", "diff_vs_close")):
                    d = american_to_dec(s[key])
                    if d and fv:
                        # positive difference = we price the home side more likely
                        try:
                            row[col] = fmt((1.0 / d - 1.0 / float(fv)) * 100.0, 2)
                        except (ValueError, ZeroDivisionError):
                            pass
            if pair:
                row.update(settled="1",
                           result="push" if pair["margin"] == 0 else "home" if pair["margin"] > 0 else "away",
                           official_result_url=pair["url"])
        rows.append(row)
    return rows


def results_index(results):
    out = {}
    for r in results:
        try:
            margin = int(r["home_pts"]) - int(r["away_pts"])
            total = int(r["home_pts"]) + int(r["away_pts"])
        except (ValueError, KeyError):
            continue
        out[(int(r["week"]), r["away"], r["home"])] = {
            "margin": margin, "total": total, "url": r["official_url"],
            "home_pts": int(r["home_pts"]), "away_pts": int(r["away_pts"]),
        }
    return out


# ---------------------------------------------------------------------------
# signal vs staking: two scores, never one
# ---------------------------------------------------------------------------
def grade_and_score(fmd, results_by_pair, snapshots, prob_scores=()):
    """Grade every originated market and split the evidence into two scores.

    SIGNAL  - did our number beat the market's number? Measured as the change in
              Brier score against the closing number, and by the sign of the
              fair-market difference on settled markets. This is a skill claim
              about the number, and it is what the leaderboard ranks.
    STAKING - what a flat one-unit paper stake would have returned, and the
              largest drawdown of that paper bankroll. This is a luck-friendly
              number: a staking run can look superb on tiny samples, which is
              exactly why it is reported beside the signal score and never
              instead of it.
    """
    settled = []
    for r in fmd:
        pair = results_by_pair.get((int(r["week"]), r["away"], r["home"]))
        if not pair or r["fair"] == "":
            continue
        if r["market"] == "side" and r["market_close"]:
            try:
                # market_close is the home team's handicap (e.g. -4.5).
                # fair is expressed as the model's expected home margin, so a
                # bet settles on home_margin + home_line, not the straight-up
                # winner.  The old implementation ignored the line entirely.
                home_line = float(str(r["market_close"]).replace("\u2212", "-"))
            except ValueError:
                continue
            fair = float(r["fair"])
            market_home_margin = -home_line
            pick_home = fair > market_home_margin
            spread_margin = pair["margin"] + home_line
            if math.isclose(spread_margin, 0.0, abs_tol=1e-9):
                outcome = "push"
            else:
                home_covers = spread_margin > 0
                won = home_covers == pick_home
                outcome = "won" if won else "lost"
            bet = "home" if pick_home else "away"
            # the price of the side we took
            price = None
            for s in snapshots:
                if s["event_id"] == r["event_id"] and s["market"] == "side" and s["selection"] == bet:
                    price = s["close_price"] or s["open_price"]
            pnl = 0.0 if outcome == "push" else (
                (american_to_dec(price) - 1.0) if (outcome == "won" and american_to_dec(price)) else -1.0)
            settled.append({"event_id": r["event_id"], "week": r["week"], "market": "side",
                            "bet": bet, "price": price or "", "outcome": outcome,
                            "pnl": pnl, "fair_margin": fair - market_home_margin})
        elif r["market"] == "total" and r["market_close"]:
            try:
                line = float(r["market_close"])
            except ValueError:
                continue
            fair = float(r["fair"])
            pick_over = fair > line
            if pair["total"] == line:
                outcome = "push"
            else:
                won = (pair["total"] > line) == pick_over
                outcome = "won" if won else "lost"
            bet = "over" if pick_over else "under"
            price = None
            for s in snapshots:
                if s["event_id"] == r["event_id"] and s["market"] == "total" and s["selection"] == bet:
                    price = s["close_price"] or s["open_price"]
            pnl = 0.0 if outcome == "push" else (
                (american_to_dec(price) - 1.0) if (outcome == "won" and american_to_dec(price)) else -1.0)
            settled.append({"event_id": r["event_id"], "week": r["week"], "market": "total",
                            "bet": bet, "price": price or "", "outcome": outcome,
                            "pnl": pnl, "fair_margin": fair - line})
        elif r["market"] == "moneyline" and r["market_close"] and r["fair"] != "":
            p_home_fair = float(str(r["fair"]).replace("%", "")) / 100.0
            d = american_to_dec(r["market_close"])
            if not d:
                continue
            p_home_market = 1.0 / d
            pick_home = p_home_fair > p_home_market
            if pair["margin"] == 0:
                outcome = "push"
            else:
                outcome = "won" if ((pair["margin"] > 0) == pick_home) else "lost"
            price = r["market_close"] if pick_home else None
            if not pick_home:
                for s in snapshots:
                    if s["event_id"] == r["event_id"] and s["market"] == "moneyline" and s["selection"] == "away":
                        price = s["close_ml"]
            dec = american_to_dec(price) or 0.0
            pnl = 0.0 if outcome == "push" else ((dec - 1.0) if outcome == "won" else -1.0)
            settled.append({"event_id": r["event_id"], "week": r["week"], "market": "moneyline",
                            "bet": "home" if pick_home else "away", "price": price or "",
                            "outcome": outcome, "pnl": pnl,
                            "fair_margin": (p_home_fair - p_home_market) * 100.0})

    # ---- SIGNAL SCORE ------------------------------------------------------
    # the skill statistic: mean fair-market difference, and a one-sided t test.
    # If we are genuinely better at pricing than the closing number, our number
    # should be on the right side of it more often than not; the statistic is
    # reported with n and a confidence interval because n is tiny.
    diffs = [s["fair_margin"] for s in settled]
    n = len(diffs)
    if n >= 2:
        m, s_ = mean(diffs), sd(diffs)
        se = s_ / math.sqrt(n) if s_ else 0.0
        z = (m / se) if se else 0.0
        p = two_sided_p(z)
        ci = (m - 1.96 * se, m + 1.96 * se)
    else:
        m = s_ = se = z = 0.0
        p = 1.0
        ci = ("", "")
    wins = sum(1 for s in settled if s["outcome"] == "won")
    losses = sum(1 for s in settled if s["outcome"] == "lost")
    pushes = sum(1 for s in settled if s["outcome"] == "push")

    # ---- STAKING SCORE -----------------------------------------------------
    pnl = sum(s["pnl"] for s in settled)
    bank, peak, dd = 0.0, 0.0, 0.0
    for s in settled:
        bank += s["pnl"]
        peak = max(peak, bank)
        dd = min(dd, bank - peak)
    roi = (100.0 * pnl / n) if n else 0.0

    # ---- GATES ------------------------------------------------------------
    # Each gate is evaluated with the numbers we have, and reports the number it
    # used, so a reader can see which gate is the binding one.
    gate_rows = []
    for gid, name, rule, thr in GATES:
        status, value = "fail", ""
        if gid == "G1":
            priced = sum(1 for s in settled)
            status = "pass" if priced else "fail"
            value = "%d settled markets" % priced
        elif gid == "G2":
            value = "n = %d" % n
            status = "pass" if n >= thr else "fail"
        elif gid == "G3":
            weeks = sorted({s["week"] for s in settled})
            value = "%d weeks graded" % len(weeks)
            status = "pass" if len(weeks) >= 2 else "fail"
        elif gid == "G4":
            scored = [r for r in prob_scores if r.get("skill", "") != ""]
            if not scored:
                value = "not computed: no settled market has both a model probability and a market benchmark"
                status = "fail"
            else:
                value = "; ".join(
                    "%s: model Brier %s vs market %s, skill %s, 95%% game-cluster interval [%s, %s], n = %d"
                    % (r["market"], r["model_brier"], r["market_brier"], r["skill"],
                       r["ci_low"], r["ci_high"], r["n"]) for r in scored)
                status = "pass" if all(r["status"] == "pass" for r in scored) else "fail"
        elif gid == "G5":
            value = "p = %.4f (z = %.2f)" % (p, z)
            status = "pass" if (n >= 30 and p < thr) else "fail"
        elif gid == "G6":
            value = "not computed: needs the full trial log"
            status = "fail"
        elif gid == "G7":
            if settled:
                by_week = {}
                for s in settled:
                    by_week[s["week"]] = by_week.get(s["week"], 0.0) + abs(s["fair_margin"])
                tot = sum(by_week.values()) or 1.0
                value = "largest week = %.0f%% of total" % (100.0 * max(by_week.values()) / tot)
                status = "pass" if max(by_week.values()) / tot <= thr else "fail"
            else:
                status = "fail"
        elif gid == "G8":
            value = "needs a pre-registered future segment"
            status = "fail"
        gate_rows.append({"gate": gid, "name": name, "rule": rule, "observed": value,
                          "status": status})

    passes = sum(1 for g in gate_rows if g["status"] == "pass")
    signal = {
        "n": n, "mean_diff": round(m, 3), "sd": round(s_, 3), "se": round(se, 3),
        "z": round(z, 3), "p": round(p, 4),
        "ci95_low": round(ci[0], 3) if ci[0] != "" else "",
        "ci95_high": round(ci[1], 3) if ci[1] != "" else "",
        "wins": wins, "losses": losses, "pushes": pushes,
        "hit_rate_pct": round(100.0 * wins / max(1, wins + losses), 2),
        "gates_passed": passes, "gates_total": len(gate_rows),
        "eligible": passes == len(gate_rows),
    }
    staking = {
        "n": n, "pnl_units": round(pnl, 3), "roi_pct": round(roi, 3),
        "max_drawdown_units": round(dd, 3),
        "best_week": (max((s["week"] for s in settled), key=lambda w: sum(
            x["pnl"] for x in settled if x["week"] == w)) if settled else ""),
        "note": "a staking result on n<100 is noise; it is reported, never ranked alone",
    }
    return settled, signal, staking, gate_rows, ci


# ---------------------------------------------------------------------------
# proper scores: a probability is only useful if it can be scored
# ---------------------------------------------------------------------------
BOOT_B = 10000
BOOT_SEED = 20261119
PROB_MIN_N = 30          # the registered G4 floor: a skill score needs n >= 30
PROB_TRIALS = 3          # moneyline, side, total: the multiplicity factor


def cluster_bootstrap(by_cluster, stat, b=BOOT_B, seed=BOOT_SEED):
    """Resample whole games (clusters) and return the 2.5% and 97.5% quantiles."""
    rnd = random.Random(seed)
    keys = list(by_cluster)
    if not keys:
        return "", "", 1.0
    vals = []
    for _ in range(b):
        sample = []
        for _ in keys:
            sample.extend(by_cluster[rnd.choice(keys)])
        vals.append(stat(sample))
    vals.sort()
    return vals[int(0.025 * b)], vals[int(0.975 * b)], sum(1 for v in vals if v <= 0) / b


def de_vig(home_ml, away_ml):
    """Home probability from two American moneyline prices, with the vig removed."""
    hp, ap = to_float(home_ml), to_float(away_ml)
    if not hp or not ap:
        return None
    ph = 100.0 / (hp + 100.0) if hp > 0 else (-hp) / (-hp + 100.0)
    pa = 100.0 / (ap + 100.0) if ap > 0 else (-ap) / (-ap + 100.0)
    if ph + pa <= 0:
        return None
    return ph / (ph + pa)


def probability_scores(fmd, results_by_pair, snapshots, dispersion):
    """Score every settled market with a proper score, against a market benchmark.

    The model's probability and the market's probability must be about the same
    event, or the comparison is meaningless:
      * moneyline - the de-vigged captured closing price;
      * side      - derived from that same de-vigged price and the closing spread;
      * total     - none. A posted total carries no probability, so the model's
                    probability is scored on its own and no benchmark is invented.
    """
    sig_m = dispersion["sigma_margin_model"]
    sig_t = dispersion["sigma_total_model"]
    sig_league = dispersion["sigma_margin_league"]
    snap = {}
    for s in snapshots:
        snap.setdefault((s["event_id"], s["market"], s["selection"]), s)

    per_market = {"side": [], "total": [], "moneyline": []}
    for r in fmd:
        if r["settled"] != "1" or not r["fair"]:
            continue
        pair = results_by_pair.get((int(r["week"]), r["away"], r["home"]))
        if not pair:
            continue
        m = r["market"]
        ev = r["event_id"]
        if m == "side":
            line = to_float(r["market_close"])
            if line is None:
                continue
            fair = to_float(r["fair"])
            if fair is None:
                continue
            spread_margin = pair["margin"] + line
            if abs(spread_margin) < 1e-9:
                continue                      # a push is not a scored observation
            y = 1.0 if spread_margin > 0 else 0.0
            p_model = norm_cdf((fair + line) / sig_m) if sig_m else 0.5
            hp_s = snap.get((ev, "moneyline", "home"), {})
            ap_s = snap.get((ev, "moneyline", "away"), {})
            hp, ap = hp_s.get("close_ml", ""), ap_s.get("close_ml", "")
            p_mkt = None
            pm = de_vig(hp, ap)
            kind = hp_s.get("close_kind", "") or ap_s.get("close_kind", "")
            if pm is not None and sig_league:
                implied = sig_league * norm_ppf(pm)
                p_mkt = norm_cdf((implied + line) / sig_m) if sig_m else 0.5
        elif m == "total":
            line = to_float(r["market_close"])
            fair = to_float(r["fair"])
            if line is None or fair is None:
                continue
            if abs(pair["total"] - line) < 1e-9:
                continue
            y = 1.0 if pair["total"] > line else 0.0
            p_model = norm_cdf((fair - line) / sig_t) if sig_t else 0.5
            p_mkt = None
        else:
            fair = to_float(str(r["fair"]).replace("%", ""))
            if fair is None:
                continue
            if pair["margin"] == 0:
                continue
            y = 1.0 if pair["margin"] > 0 else 0.0
            p_model = fair / 100.0 if fair > 1.0 else fair
            hp_s = snap.get((ev, "moneyline", "home"), {})
            ap_s = snap.get((ev, "moneyline", "away"), {})
            hp, ap = hp_s.get("close_ml", ""), ap_s.get("close_ml", "")
            kind = hp_s.get("close_kind", "") or ap_s.get("close_kind", "")
            p_mkt = de_vig(hp, ap)
        per_market[m].append({"event_id": ev, "week": r["week"], "p_model": p_model,
                              "p_market": p_mkt, "y": y,
                              "kind": kind if m == "side" else r.get("close_kind", "")})

    rows = []
    for m in ("side", "total", "moneyline"):
        obs = per_market[m]
        n = len(obs)
        row = {"market": m, "n": n,
               "model_brier": "", "market_brier": "", "skill": "",
               "ci_low": "", "ci_high": "", "p_one_sided": "", "p_bonferroni": "",
               "multiplicity": PROB_TRIALS, "benchmark": "", "benchmark_rows": "",
               "status": "not evaluable", "note": ""}
        if n == 0:
            row["note"] = "no settled market of this type in the graded corpus"
            rows.append(row)
            continue
        bs_model = brier([o["p_model"] for o in obs], [o["y"] for o in obs])
        row["model_brier"] = fmt(bs_model, 4)
        bench = [o for o in obs if o["p_market"] is not None]
        if len(bench) < n:
            row["benchmark"] = ("none: a posted total carries no probability, so the model's "
                                "probability is scored on its own")
            row["note"] = ("model Brier %s on n = %d; no market benchmark exists for a total, "
                           "so no skill score is computed" % (fmt(bs_model, 4), n))
            rows.append(row)
            continue
        bs_market = brier([o["p_market"] for o in bench], [o["y"] for o in bench])
        row["market_brier"] = fmt(bs_market, 4)
        # the label has to be exact: a "close" that was really the last price
        # captured before the game is a close proxy, not a closing price
        kinds = {}
        for o in bench:
            k = o.get("kind") or "unlabelled"
            kinds[k] = kinds.get(k, 0) + 1
        if set(kinds) == {"close"}:
            quality = "a true closing price"
        elif kinds.get("current_as_close"):
            quality = ("a last-captured price used as the close in %d of %d rows, not a true close"
                       % (kinds["current_as_close"], len(bench)))
        else:
            quality = ", ".join("%s in %d rows" % (k, v) for k, v in sorted(kinds.items()))
        base = "de-vigged captured price (%s)" % quality
        row["benchmark"] = (base if m == "moneyline" else
                            base + ", converted to a cover probability at the captured spread")
        row["benchmark_rows"] = "; ".join("%s: %d" % (k, v) for k, v in sorted(kinds.items()))
        by_cluster = {}
        for o in bench:
            by_cluster.setdefault(o["event_id"], []).append((o["p_model"], o["p_market"], o["y"]))

        def skill(sample):
            bm = sum((pm - y) ** 2 for p, pm, y in sample) / len(sample)
            bk = sum((p - y) ** 2 for p, pm, y in sample) / len(sample)
            return 1.0 - bk / bm if bm > 0 else 0.0

        flat = [t for v in by_cluster.values() for t in v]
        sk = skill(flat)
        lo, hi, p_one = cluster_bootstrap(by_cluster, skill)
        bonf = min(1.0, p_one * PROB_TRIALS)
        row.update({"skill": fmt(sk, 4), "ci_low": fmt(lo, 4), "ci_high": fmt(hi, 4),
                    "p_one_sided": fmt(p_one, 4), "p_bonferroni": fmt(bonf, 4)})
        if n < PROB_MIN_N:
            row["status"] = "fail"
            row["note"] = ("model Brier %s vs market Brier %s on n = %d; skill %s (95%% game-cluster "
                           "interval [%s, %s]); the registered floor is n >= %d, so this is not "
                           "evidence of skill"
                           % (row["model_brier"], row["market_brier"], n, row["skill"],
                              row["ci_low"], row["ci_high"], PROB_MIN_N))
        elif lo > 0:
            row["status"] = "pass"
            row["note"] = ("model Brier %s vs market Brier %s on n = %d; skill %s with a 95%% "
                           "game-cluster lower bound of %s above zero"
                           % (row["model_brier"], row["market_brier"], n, row["skill"], row["ci_low"]))
        else:
            row["status"] = "fail"
            row["note"] = ("model Brier %s vs market Brier %s on n = %d; skill %s with a 95%% "
                           "game-cluster interval [%s, %s] that reaches zero"
                           % (row["model_brier"], row["market_brier"], n, row["skill"],
                              row["ci_low"], row["ci_high"]))
        rows.append(row)
    return rows


def dispersion_comparison(rows, dispersion):
    """Which dispersion should the model use? Both stay published until this says.

    The comparison is walk-forward: every game in the log is predicted from the
    information available before its week, and the two candidate dispersions are
    scored on those same predictions. The moneyline is scored with a proper
    score (the probability that the home team wins); the total is scored by
    interval coverage, because a probability taken at the model's own median is
    0.5 for any dispersion and cannot discriminate between them.
    """
    out = []
    if not rows:
        return out
    sig_m, sig_ml = dispersion["sigma_margin_model"], dispersion["sigma_margin_league"]
    sig_t, sig_tl = dispersion["sigma_total_model"], dispersion["sigma_total_league"]
    candidates = [
        ("margin", "model residual dispersion", sig_m, "res_margin"),
        ("margin", "league margin dispersion", sig_ml, "res_margin"),
        ("total", "model residual dispersion", sig_t, "res_total"),
        ("total", "league total dispersion", sig_tl, "res_total"),
    ]
    for quantity, name, sigma, resid_key in candidates:
        entry = {"quantity": quantity, "candidate": name, "sigma": fmt(sigma, 3),
                 "coverage_95": fmt(interval_coverage(rows, resid_key, sigma), 4),
                 "n": len(rows), "window": dispersion["window"], "brier": "", "verdict": ""}
        if quantity == "margin":
            probs = [norm_cdf(r["mu_margin"] / sigma) for r in rows]
            ys = [1.0 if r["margin"] > 0 else 0.0 for r in rows]
            entry["brier"] = fmt(brier(probs, ys), 4)
        out.append(entry)
    # the winner, stated: the margin candidate whose interval covers the outcomes
    # closest to 95 percent on the same walk-forward rows
    for quantity in ("margin", "total"):
        cands = [e for e in out if e["quantity"] == quantity]
        if len(cands) < 2:
            continue
        best = min(cands, key=lambda e: abs(float(e["coverage_95"]) - 0.95))
        for e in cands:
            e["verdict"] = ("closest to 95% coverage on the walk-forward corpus"
                            if e is best else "")
    return out


def demotion_gate(signal):
    """The demotion rule: a live strategy goes back to paper when any of these fires.

    Published as a table with numeric thresholds, and evaluated here on the only
    strategy we have actually originated (the v1 ratio model). The gate is
    deliberately asymmetric: it is cheap to demote and expensive to promote,
    because the cost of a false promotion is a real loss and the cost of a false
    demotion is a delayed entry.
    """
    rules = [
        ("D1", "Skill evidence collapses", "one-sided p > 0.20 on the skill score over the last 50 settled bets", None),
        ("D2", "Calibration breaks", "Brier score worse than the market's by > 0.02 over 50 settled bets", 0.02),
        ("D3", "Drawdown breach", "paper drawdown > 15 units at stake 1", 15),
        ("D4", "Data-integrity break", "any market graded without a source URL or a UTC stamp", 0),
        ("D5", "Stability break", "one week contributes > 50% of the skill statistic", 0.50),
        ("D6", "Signal decay", "the fair-market difference changes sign over 50 settled bets", None),
    ]
    return rules


def main():
    markets, fair, snapshots, events, results, dispersion = originate()
    results_by_pair = results_index(results)
    fmd = fair_market_difference(markets, snapshots, results_by_pair)
    write_csv(os.path.join(OPS, "fair_market_difference.csv"),
              ["event_id", "week", "away", "home", "market", "book", "fair",
               "market_open", "market_close", "diff_vs_open", "diff_vs_close",
               "close_kind", "snapshot_utc", "source_url", "settled", "result",
               "official_result_url"], fmd)

    prob_scores = probability_scores(fmd, results_by_pair, snapshots, dispersion)
    write_csv(os.path.join(OPS, "probability_scores.csv"),
              ["market", "n", "model_brier", "market_brier", "skill", "ci_low", "ci_high",
               "p_one_sided", "p_bonferroni", "multiplicity", "benchmark", "benchmark_rows",
               "status", "note"],
              prob_scores)

    settled, signal, staking, gate_rows, ci = grade_and_score(fmd, results_by_pair, snapshots,
                                                              prob_scores)
    write_csv(os.path.join(OPS, "graded.csv"),
              ["event_id", "week", "market", "bet", "price", "outcome", "pnl", "fair_margin"], settled)
    write_csv(os.path.join(OPS, "gates.csv"),
              ["gate", "name", "rule", "observed", "status"], gate_rows)
    write_csv(os.path.join(OPS, "scores_signal.csv"),
              ["n", "mean_diff", "se", "z", "p", "ci95_low", "ci95_high", "wins", "losses",
               "pushes", "hit_rate_pct", "gates_passed", "gates_total", "eligible"], [signal])
    write_csv(os.path.join(OPS, "scores_staking.csv"),
              ["n", "pnl_units", "roi_pct", "max_drawdown_units", "best_week", "note"], [staking])
    rules = demotion_gate(signal)
    live = signal["eligible"] and signal["gates_passed"] == signal["gates_total"]
    demotions = [{
        "strategy": "v1 ratio model (side, total, moneyline)",
        "from": "live" if live else "paper",
        "to": "live" if live else "paper",
        "rule_fired": "" if live else "P-ROMOTION-GATE",
        "reason": ("all %d gates passed" % signal["gates_total"]) if live else
                  ("%d of %d gates passed; stays on paper until the rest pass"
                   % (signal["gates_passed"], signal["gates_total"])),
        "n": signal["n"], "p_value": signal["p"],
    }]
    write_csv(os.path.join(OPS, "paper_demotions.csv"),
              ["strategy", "from", "to", "rule_fired", "reason", "n", "p_value"], demotions)
    write_csv(os.path.join(OPS, "demotion_rules.csv"), ["rule", "name", "trigger", "threshold"],
              [{"rule": r[0], "name": r[1], "trigger": r[2], "threshold": r[3]} for r in rules])

    print("markets originated: %d" % len(markets))
    print("fair/market/difference rows: %d" % len(fmd))
    print("settled and graded: %d" % len(settled))
    print("signal: n=%d mean diff=%s p=%s gates %d/%d eligible=%s"
          % (signal["n"], signal["mean_diff"], signal["p"],
             signal["gates_passed"], signal["gates_total"], signal["eligible"]))
    print("staking: pnl=%s units roi=%s%% maxDD=%s"
          % (staking["pnl_units"], staking["roi_pct"], staking["max_drawdown_units"]))
    for r in prob_scores:
        print("probability score %-9s n=%-3s model Brier %-8s market Brier %-8s skill %-8s %s"
              % (r["market"], r["n"], r["model_brier"], r["market_brier"], r["skill"], r["status"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
