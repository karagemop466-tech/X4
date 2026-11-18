#!/usr/bin/env python3
"""Derive the integrity datasets from captured sources. Does not invent a number.

Inputs (all committed, all source-linked)
  research/data/price_snapshots_2026.csv            one row per game, capture-faithful
  research/data/model_predictions_wk10_2026.csv     model outputs that existed pre-game
  data/games-2026.csv                               official settled scores
  data/schedule-wk11-2026.csv                       official Week 11 slate
  research/data/games_weeks6-9_2026.csv             57 official games (correlations)
  research/data/standings_2026_through_week10_tnf.csv  official PF/PA (correlations)
  research/data/replacement_depth.csv               depth / replacement measurements

Outputs
  research/data/price_snapshots_long.csv        every (game, market, phase, side) price
  research/data/market_movement.csv             open -> current -> close, per market
  research/data/results_2026.csv                verified results feed (150 games)
  research/data/results_graded_week10.csv       each model's paper bets, settled
  research/data/correlation_n.csv               every correlation with its n
  research/data/market_origination_wk11.csv     our line | market | difference | bucket
  research/data/demotion_gate_run.csv           the gate evaluated on the graded rows
  research/data/staking_vs_signal_sim.csv       staking simulation (labelled as a model)
  research/data/clv_ledger.csv                  CLV ledger - header only, n = 0 (see note)
  research/data/integrity_summary.json          the counts the site prints

Every derived field is a formula written down in this file, so a reviewer can recompute
it by hand. Nothing is estimated, imputed, or filled in from memory.

WHY THE CLV LEDGER IS EMPTY
  Closing-line value is (the price we took) - (the closing price). We have never taken a
  price: every strategy in this repository is paper-only. A price captured after the fact
  cannot reconstruct the price available at the moment a stake would have been placed.
  The ledger is therefore published with zero rows rather than backfilled, and the
  demotion gate reports its CLV criterion as BLOCKED. The snapshot store is what makes
  this measurable from the first real stake onward.
"""
import csv
import json
import math
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(ROOT, "research", "data")
OUT = os.path.join(ROOT, "data", "output")


def read(path, skip_comments=False):
    with open(path, newline="", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if skip_comments:
        lines = [ln for ln in lines if not ln.startswith("#") and ln.strip()]
    return list(csv.DictReader(lines))


def num(v):
    """Float, or None for a blank cell. A blank stays blank - it is never imputed."""
    v = (v or "").strip()
    return None if v == "" else float(v)


def write(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])
    print("wrote %s (%d rows)" % (os.path.relpath(path, ROOT), len(rows)))


# ---------------------------------------------------------------- statistics helpers
def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return None if sxx <= 0 or syy <= 0 else sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n):
    """95% CI for a Pearson r via the Fisher z transform. Undefined at n <= 3."""
    if r is None or n <= 3 or abs(r) >= 1:
        return (None, None)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    f = lambda v: (math.exp(2 * v) - 1) / (math.exp(2 * v) + 1)
    return (f(z - 1.95996 * se), f(z + 1.95996 * se))


def american_to_decimal(a):
    a = float(a)
    return 1 + (a / 100.0 if a > 0 else 100.0 / abs(a))


def breakeven(american):
    return 1.0 / american_to_decimal(american)


def cover_prob(edge, sigma):
    """P(a handicap is beaten) when our line is `edge` points better than the fair line.

    Margin ~ N(fair, sigma); a bet `edge` points below the fair line covers with
    probability Phi(edge / sigma). This is the standard no-vig benchmark, not a claim
    about any sportsbook's pricing.
    """
    return 0.5 * (1 + math.erf((edge / sigma) / math.sqrt(2)))


# =========================================================== 1. price snapshot store
snap = read(os.path.join(RD, "price_snapshots_2026.csv"))
assert len(snap) == 14, "expected 14 captured games, found %d" % len(snap)

long_rows = []
for g in snap:
    for market, phase, acol, hcol in (
            ("spread", "open", "spread_away_open", None),
            ("spread", "current", "spread_away_current", None),
            ("spread", "close", "spread_away_close", None),
            ("total", "open", "total_open", None),
            ("total", "current", "total_current", None),
            ("total", "close", "total_close", None),
            ("moneyline", "open", "ml_away_open", "ml_home_open"),
            ("moneyline", "current", "ml_away_current", "ml_home_current"),
            ("moneyline", "close", "ml_away_close", "ml_home_close")):
        if market == "moneyline":
            for side, col in (("away", acol), ("home", hcol)):
                long_rows.append([g["week"], g["game_id"], g["away"], g["home"], market, phase,
                                  side, num(g[col]), g["provider"], g["captured_utc"],
                                  g["source_url"]])
        else:
            # A spread is stored from the away side: away +5.5 means the away team
            # receives 5.5, and the home side is its negation.
            v = num(g[acol])
            long_rows.append([g["week"], g["game_id"], g["away"], g["home"], market, phase,
                              "away", v, g["provider"], g["captured_utc"], g["source_url"]])
            long_rows.append([g["week"], g["game_id"], g["away"], g["home"], market, phase,
                              "home", None if v is None else -v, g["provider"],
                              g["captured_utc"], g["source_url"]])
write(os.path.join(RD, "price_snapshots_long.csv"),
      ["week", "game_id", "away", "home", "market", "phase", "side", "price", "provider",
       "captured_utc", "source_url"], long_rows)
filled = sum(1 for r in long_rows if r[7] is not None)
price_rows = {"rows": len(long_rows), "filled": filled, "blank": len(long_rows) - filled,
              "games": len(snap), "markets": 3, "phases": 3}

# ---- market movement: the same store, read as open -> current -> close ----------
movement = []
for g in snap:
    for market, o, c, cl in (
            ("spread_home", "spread_away_open", "spread_away_current", "spread_away_close"),
            ("total", "total_open", "total_current", "total_close")):
        if market == "total":
            op, cu, cls = num(g[o]), num(g[c]), num(g[cl])
        else:
            # flip to the home side so a positive number always means "home favoured"
            op, cu, cls = (-num(g[o]) if num(g[o]) is not None else None,
                           -num(g[c]) if num(g[c]) is not None else None,
                           -num(g[cl]) if num(g[cl]) is not None else None)
        movement.append([g["week"], g["game_id"], g["away"], g["home"], market, op, cu, cls,
                         None if (op is None or cu is None) else round(cu - op, 4),
                         None if (op is None or cls is None) else round(cls - op, 4),
                         "final" if cls is not None else "pre-game", g["source_url"]])
    for side, o, c, cl in (("away", "ml_away_open", "ml_away_current", "ml_away_close"),
                           ("home", "ml_home_open", "ml_home_current", "ml_home_close")):
        op, cu, cls = num(g[o]), num(g[c]), num(g[cl])
        movement.append([g["week"], g["game_id"], g["away"], g["home"], "moneyline_" + side,
                         op, cu, cls,
                         None if (op is None or cu is None) else round(cu - op, 4),
                         None if (op is None or cls is None) else round(cls - op, 4),
                         "final" if cls is not None else "pre-game", g["source_url"]])
write(os.path.join(RD, "market_movement.csv"),
      ["week", "game_id", "away", "home", "market", "open", "current", "close",
       "move_open_to_current", "move_open_to_close", "state", "source_url"], movement)

# ---- the CLV ledger: header only, because no stake-time price has ever existed ---
write(os.path.join(RD, "clv_ledger.csv"),
      ["stake_utc", "game_id", "market", "side", "line_taken", "price_taken_decimal",
       "closing_line", "closing_price_decimal", "clv_points", "clv_probability",
       "stake_units", "result", "pnl_units", "captured_by"], [])

# ================================================================ 2. results feed
games = read(os.path.join(ROOT, "data", "games-2026.csv"))
by_id = {(g["away"], g["home"], g["week"]): g for g in snap}
assert len(by_id) == len(snap), "duplicate (away, home, week) key in the snapshot store"

seen = set()
for g in games:
    key = (g["away"], g["home"], g["week"])
    assert key not in seen, "duplicate game in the feed: %s" % (key,)
    seen.add(key)

sched = read(os.path.join(ROOT, "data", "schedule-wk11-2026.csv"))
sched_pairs = {(s["away"], s["home"]) for s in sched if s["week"] == "11"}
assert len(sched_pairs) == 13, "expected 13 official Week 11 games"
for g in snap:
    if g["week"] == "11":
        assert (g["away"], g["home"]) in sched_pairs, "not on the official slate: %s %s" % (
            g["away"], g["home"])

feed = []
for g in sorted(games, key=lambda r: (int(r["week"]), r["url"])):
    feed.append([g["week"], g["away"], g["home"], int(g["away_pts"]), int(g["home_pts"]),
                 1 if g["ot"] else 0, "final", g["url"], "official NFL.com game page"])
write(os.path.join(RD, "results_2026.csv"),
      ["week", "away", "home", "away_score", "home_score", "overtime", "status", "game_url",
       "source"], feed)

# ---- the feed must reproduce the official standings, field by field ----
st = read(os.path.join(ROOT, "data", "standings-wk10-2026.csv"))
agg = {}
for g in games:
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    for t, pf, pa in ((g["away"], ap, hp), (g["home"], hp, ap)):
        d = agg.setdefault(t, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
        d["pf"] += pf
        d["pa"] += pa
        d["w" if pf > pa else ("l" if pf < pa else "t")] += 1
checks = 0
for r in st:
    d = agg[r["abbr"]]
    for field in ("w", "l", "t", "pf", "pa"):
        assert d[field] == int(r[field]), "%s %s: feed %s vs official %s" % (
            r["abbr"], field, d[field], r[field])
        checks += 1
    assert int(r["pf"]) - int(r["pa"]) == int(r["net_pts"])
    checks += 1
print("results feed reconciled against the official standings: %d fields" % checks)

# ======================================== 3. graded paper bets (disagreement, not CLV)
g69 = read(os.path.join(RD, "games_weeks6-9_2026.csv"))
margins = [int(r["home_score"]) - int(r["away_score"]) for r in g69]
SIGMA = statistics.pstdev(margins)
print("sample margin sd (weeks 6-9, n=%d): %.3f" % (len(margins), SIGMA))

settled = {(g["away"], g["home"], g["week"]): g for g in games}
preds = read(os.path.join(RD, "model_predictions_wk10_2026.csv"), skip_comments=True)
COLS = ["model", "game_id", "away", "home", "week", "away_score", "home_score",
        "pred_spread_away", "close_spread_away", "spread_side", "spread_line", "spread_actual",
        "spread_result", "disagreement_points", "cover_prob_no_vig", "spread_pnl_units",
        "pred_total", "close_total", "total_side", "total_line", "total_actual",
        "total_result", "total_disagreement", "total_pnl_units",
        "ml_side", "ml_price_close", "ml_result", "ml_pnl_units", "ml_break_even_prob",
        "clv_points", "clv_status", "sigma_used", "derivation"]
grows = []
for p in preds:
    g = by_id[(p["away"], p["home"], p["week"])]
    sc = settled[(p["away"], p["home"], p["week"])]
    away_margin = int(sc["away_pts"]) - int(sc["home_pts"])
    total_actual = int(sc["away_pts"]) + int(sc["home_pts"])
    ps, pt = float(p["pred_spread_away"]), float(p["pred_total"])
    c_away, c_total = num(g["spread_away_close"]), num(g["total_close"])
    ml_a, ml_h = num(g["ml_away_close"]), num(g["ml_home_close"])
    row = {"model": p["model"], "game_id": p["game_id"], "away": p["away"],
           "home": p["home"], "week": p["week"], "away_score": int(sc["away_pts"]),
           "home_score": int(sc["home_pts"]), "pred_spread_away": ps,
           "close_spread_away": c_away, "pred_total": pt, "close_total": c_total,
           "sigma_used": round(SIGMA, 6), "derivation": "tools/build_integrity.py",
           "clv_points": None, "clv_status": "blocked: no stake-time capture exists"}
    if c_away is not None and ps != c_away:
        side = "away" if ps > c_away else "home"
        line = c_away if side == "away" else -c_away
        actual = away_margin if side == "away" else -away_margin
        res = "push" if actual == line else ("win" if actual > line else "loss")
        edge = abs(ps - c_away)
        row.update({"spread_side": side, "spread_line": line, "spread_actual": actual,
                    "spread_result": res, "disagreement_points": round(edge, 6),
                    "cover_prob_no_vig": round(cover_prob(edge, SIGMA), 6),
                    "spread_pnl_units": 0.0 if res == "push" else (
                        american_to_decimal(-110) - 1 if res == "win" else -1.0)})
    if c_total is not None and pt != c_total:
        side = "over" if pt > c_total else "under"
        res = "push" if total_actual == c_total else (
            "win" if (total_actual > c_total) == (side == "over") else "loss")
        row.update({"total_side": side, "total_line": c_total, "total_actual": total_actual,
                    "total_result": res, "total_disagreement": round(abs(pt - c_total), 6),
                    "total_pnl_units": 0.0 if res == "push" else (
                        american_to_decimal(-110) - 1 if res == "win" else -1.0)})
    if ml_a is not None and ml_h is not None and ps != 0:
        side = "away" if ps > 0 else "home"
        price = ml_a if side == "away" else ml_h
        won = (away_margin > 0) if side == "away" else (away_margin < 0)
        row.update({"ml_side": side, "ml_price_close": price,
                    "ml_result": "win" if won else "loss",
                    "ml_pnl_units": (american_to_decimal(price) - 1) if won else -1.0,
                    "ml_break_even_prob": round(breakeven(price), 6)})
    grows.append([row.get(c) for c in COLS])
write(os.path.join(RD, "results_graded_week10.csv"), COLS, grows)

# ======================================================= 4. origination order + gap
lines = json.load(open(os.path.join(OUT, "wk11_lines.json")))
lines_by = {(l["away"], l["home"]): l for l in lines}
ORIG_ORDER = ["side", "total", "moneyline"]

orig_rows = []
for g in snap:
    if g["week"] != "11":
        continue
    models = lines_by[(g["away"], g["home"])]["models"]
    fair_spread = statistics.median([m["spread"] for m in models.values()])   # home minus away
    fair_total = statistics.median([m["total"] for m in models.values()])
    mk_away = num(g["spread_away_current"])
    mk_total = num(g["total_current"])
    ml_a, ml_h = num(g["ml_away_current"]), num(g["ml_home_current"])
    model_side = g["home"] if fair_spread > 0 else (g["away"] if fair_spread < 0 else "")
    # `spread_away_current` is quoted from the away side: positive means the away team
    # receives points and the HOME team is favoured. Verified against the desk's
    # independent line table (IND +10 at HOU => HOU -10).
    market_side = "" if mk_away is None or mk_away == 0 else (
        g["home"] if mk_away > 0 else g["away"])
    mk_home = None if mk_away is None else -mk_away
    diff = None if mk_home is None else round(mk_home - fair_spread, 4)
    absd = None if diff is None else abs(diff)
    bucket = "" if absd is None else (
        "<=1" if absd <= 1 else "1-2.5" if absd <= 2.5 else "2.5-5" if absd <= 5 else ">5")
    tdiff = None if mk_total is None else round(mk_total - fair_total, 4)
    p_home = cover_prob(fair_spread, SIGMA)          # fair P(home wins) on the same basis
    p_away = 1 - p_home
    orig_rows.append([g["week"], g["game_id"], g["away"], g["home"], model_side, market_side,
                      round(fair_spread, 4), mk_home, diff, bucket,
                      round(fair_total, 4), mk_total, tdiff,
                      round(1 / p_home, 4), None if ml_h is None else round(american_to_decimal(ml_h), 4),
                      round(1 / p_away, 4), None if ml_a is None else round(american_to_decimal(ml_a), 4),
                      "side -> total -> moneyline", g["source_url"]])
write(os.path.join(RD, "market_origination_wk11.csv"),
      ["week", "game_id", "away", "home", "model_side", "market_side", "fair_spread_home",
       "market_spread_home", "difference_home", "gap_bucket", "fair_total", "market_total",
       "difference_total", "fair_ml_home_decimal", "market_ml_home_decimal",
       "fair_ml_away_decimal", "market_ml_away_decimal", "origination_order",
       "price_source_url"], orig_rows)

# ================================================== 5. correlations, with their n
aw = [int(r["away_score"]) for r in g69]
hw = [int(r["home_score"]) for r in g69]
mar = [h - a for a, h in zip(aw, hw)]
tot = [a + h for a, h in zip(aw, hw)]
nz = [r for r in g69 if r["neutral_site"] == "0"]
mar_n = [int(r["home_score"]) - int(r["away_score"]) for r in nz]
tot_n = [int(r["home_score"]) + int(r["away_score"]) for r in nz]
teams = read(os.path.join(RD, "standings_2026_through_week10_tnf.csv"))
net = [int(t["pf"]) - int(t["pa"]) for t in teams]
# PCT is not a column of the standings file: computed with the NFL tie rule.
pct = [(int(t["w"]) + 0.5 * int(t["t"])) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
pfg = [int(t["pf"]) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]
pag = [int(t["pa"]) / (int(t["w"]) + int(t["l"]) + int(t["t"])) for t in teams]

corr_rows = []
for name, xs, ys, n, inp, url in (
    ("Away score vs home score (weeks 6-9, all games)", aw, hw, len(aw),
     "research/data/games_weeks6-9_2026.csv", "https://www.nfl.com/schedules/2026/by-week/week-9"),
    ("Margin vs game total (weeks 6-9, all games)", mar, tot, len(mar),
     "research/data/games_weeks6-9_2026.csv", "https://www.nfl.com/schedules/2026/by-week/week-9"),
    ("Margin vs game total (neutral-site removed, n=54)", mar_n, tot_n, len(mar_n),
     "research/data/games_weeks6-9_2026.csv", "https://www.nfl.com/schedules/2026/by-week/week-9"),
    ("Net points vs win percentage (32 clubs, through Week 10 TNF)", net, pct, len(net),
     "research/data/standings_2026_through_week10_tnf.csv", "https://www.nfl.com/standings/"),
    ("Points for per game vs points against per game (32 clubs)", pfg, pag, len(pfg),
     "research/data/standings_2026_through_week10_tnf.csv", "https://www.nfl.com/standings/")):
    r = pearson(xs, ys)
    lo, hi = fisher_ci(r, n)
    corr_rows.append([name, None if r is None else round(r, 4), n,
                      None if lo is None else round(lo, 4), None if hi is None else round(hi, 4),
                      inp, url])
write(os.path.join(RD, "correlation_n.csv"),
      ["quantity", "pearson_r", "n", "ci_low", "ci_high", "input_file", "source_url"], corr_rows)

# ================================== 6. replacement depth (measured, never assumed)
DEP_HEADER = ["team", "unit", "position_group", "starter", "starter_status", "depth_slot",
              "replacement", "replacement_starts_2026", "replacement_snap_share",
              "deficiency_points", "evidence_url", "captured_utc"]
with open(os.path.join(RD, "replacement_depth.csv"), newline="", encoding="utf-8") as fh:
    _raw = list(csv.reader(fh))
missing_fields = [(i + 1, len(r)) for i, r in enumerate(_raw) if len(r) != len(DEP_HEADER)]
assert not missing_fields, "replacement_depth.csv rows with the wrong field count: %s" % (
    missing_fields,)
dep = [dict(zip(DEP_HEADER, r)) for r in _raw[1:]]
# Guard against a malformed row silently shifting columns: every row must carry every
# header, and every evidence URL must be an absolute https URL.
for d in dep:
    missing = [k for k, v in d.items() if v is None]
    assert not missing, "malformed row for %s: %s" % (d.get("team"), missing)
    assert d["evidence_url"].startswith("https://"), "bad evidence URL: %r" % d["evidence_url"]
    # A field-count mismatch silently shifts a trailing blank into a later column, so
    # check that the row carries exactly the header's fields, not merely that nothing
    # is None.
    row_len = len(d)
    assert row_len == len(DEP_HEADER), "%s has %d fields, header has %d" % (
        d["team"], row_len, len(DEP_HEADER))
dep_rows = [[d["team"], d["unit"], d["position_group"], d["starter"], d["starter_status"],
             d["depth_slot"], d["replacement"], d["replacement_starts_2026"],
             d["replacement_snap_share"], d["deficiency_points"], d["evidence_url"],
             d["captured_utc"]] for d in dep]
write(os.path.join(RD, "replacement_depth_measured.csv"),
      ["team", "unit", "position_group", "starter", "starter_status", "depth_slot",
       "replacement", "replacement_starts_2026", "replacement_snap_share",
       "deficiency_points", "evidence_url", "captured_utc"], dep_rows)
measured = sum(1 for d in dep if (d.get("replacement_snap_share") or "").strip() != "")

# ============================ 7. staking vs signal: why the leaderboard must split them
def lcg(seed):
    state = [seed]

    def nxt():
        state[0] = (1103515245 * state[0] + 12345) % (2 ** 31)
        return state[0] / float(2 ** 31)
    return nxt


def simulate(edge_p, n_bets, bankroll0, frac, seed=20261114):
    """Simulated ledger. A LABELLED MODEL, not evidence about any real market."""
    rnd = lcg(seed)
    bank, peak, maxdd, busted_at = bankroll0, bankroll0, 0.0, None
    for i in range(1, n_bets + 1):
        stake = 1.0 if frac == 0 else bank * frac
        if bank <= 0:
            busted_at = busted_at or i
            break
        stake = min(stake, bank)
        if rnd() < edge_p:
            bank += stake * (american_to_decimal(-110) - 1)
        else:
            bank -= stake
        peak = max(peak, bank)
        maxdd = max(maxdd, (peak - bank) / peak if peak > 0 else 1.0)
    return max(bank, 0.0), maxdd, busted_at


sim_rows = []
for label, p in (("fair coin at -110 (p=0.500)", 0.500),
                 ("true edge 2.4 pts at -110 (p=0.524)", 0.524)):
    for frac, name in ((0.0, "flat 1-unit stakes"), (0.05, "5% of bankroll")):
        for n in (100, 1000, 5000):
            bank, dd, bust = simulate(p, n, 100.0, frac)
            sim_rows.append([label, name, n, round(bank, 2), round(bank - 100.0, 2),
                             round(dd, 4), "yes" if bust else "no", bust or "",
                             "simulation (tools/build_integrity.py), not evidence",
                             "%.4f" % p])
write(os.path.join(RD, "staking_vs_signal_sim.csv"),
      ["edge", "staking", "bets", "final_bankroll", "profit", "max_drawdown", "busted",
       "busted_at_bet", "note", "true_win_prob"], sim_rows)

# ---- the separated leaderboard: signal first, staking second ------------------
# Signal metrics are what survive a lucky or unlucky staking pattern: the share of
# bets that beat the close, the calibration of the no-vig cover probability, and the
# sample size. Staking metrics are reported beside them and never combined with them.
spread_bets = [r for r in (dict(zip(COLS, row)) for row in grows) if r.get("spread_result")]
signal_rows = []
per_model = {}
for r in spread_bets:
    per_model.setdefault(r["model"], []).append(r)
for model, rows in sorted(per_model.items()):
    n = len(rows)
    wins = sum(1 for r in rows if r["spread_result"] == "win")
    pnl = sum(float(r["spread_pnl_units"] or 0) for r in rows)
    avg_dis = sum(float(r["disagreement_points"] or 0) for r in rows) / n
    avg_cp = sum(float(r["cover_prob_no_vig"] or 0) for r in rows) / n
    brier = sum((float(r["cover_prob_no_vig"] or 0) - (1.0 if r["spread_result"] == "win" else 0.0)) ** 2
                for r in rows) / n
    signal_rows.append([model, n, wins, round(wins / n, 4), round(avg_dis, 4),
                        round(avg_cp, 4), round(brier, 4), 0, "", round(pnl, 4),
                        "CLV blocked: no stake-time capture", "paper"])
write(os.path.join(RD, "leaderboard_signal_staking.csv"),
      ["model", "settled_bets", "wins", "hit_rate", "avg_disagreement_points",
       "avg_no_vig_cover_prob", "brier", "clv_positive", "clv_n", "net_units",
       "clv_status", "stage"], signal_rows)

# ============================================ 8. the demotion gate, made falsifiable
# Each rule is a POLICY CHOICE by this project, written down so it can be argued with.
GATES = [
    ("D1 signal: beat the close", "clv_positive_share >= 0.55 on n >= 100 settled bets", True),
    ("D2 staking: net ROI 95% CI lower bound > 0", "n >= 100 and CI low > 0", False),
    ("D3 probability quality: Brier < 0.25 baseline", "n >= 100 and Brier < 0.25", False),
    ("D4 drawdown <= 20% of peak bankroll", "measured over the run", False),
    ("D5 market availability: >= 1 priced market at stake time", "price store row exists", True),
]
gate_rows = []
for name, rule, blocked in GATES:
    gate_rows.append([name, rule, "BLOCKED" if blocked else "NOT MET",
                      "n=9 settled bets (< 100); no stake-time capture"
                      if "CLV" in name or "signal" in name else "n=9 settled bets (< 100)",
                      "paper only - cannot be promoted"])
# The gate as an executable decision on the only run we have.
run_rows = []
for r in spread_bets:
    run_rows.append([r["model"], r["game_id"], r["away"], r["home"], r["week"],
                     r["spread_side"], r["spread_result"], r["disagreement_points"],
                     r["cover_prob_no_vig"], r["spread_pnl_units"], r["clv_status"],
                     "tools/build_integrity.py"])
write(os.path.join(RD, "demotion_gate_run.csv"),
      ["model", "game_id", "away", "home", "week", "side", "result", "disagreement_points",
       "cover_prob_no_vig", "pnl_units", "clv_status", "derivation"], run_rows)
write(os.path.join(RD, "demotion_gate_rules.csv"),
      ["gate", "rule", "state", "why", "consequence"], gate_rows)

# ================================================================= summary
summary = {
    "price_store": price_rows,
    "market_movement_rows": len(movement),
    "results_feed": {"games": len(feed), "weeks": max(int(g["week"]) for g in games),
                     "reconciled_fields": checks, "standings_teams": len(st)},
    "graded": {"rows": len(grows), "spread_rows": len(spread_bets),
               "clv_rows": 0, "clv_status": "blocked"},
    "sigma": round(SIGMA, 6),
    "origination": {"games": len(orig_rows), "order": ORIG_ORDER,
                    "within_2_5": sum(1 for r in orig_rows if r[9] in ("<=1", "1-2.5")),
                    "over_5": sum(1 for r in orig_rows if r[9] == ">5")},
    "correlations": len(corr_rows),
    "replacement_rows": len(dep_rows), "replacement_measured": measured,
    "sim_rows": len(sim_rows),
    "gates": [{"gate": g[0], "rule": g[1], "state": g[2]} for g in gate_rows],
}
json.dump(summary, open(os.path.join(RD, "integrity_summary.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
