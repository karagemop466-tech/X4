#!/usr/bin/env python3
"""Removal-of-luck panel: controls for the originated staking record.

The question this module answers is narrow and deliberately uncomfortable:
could the staking record that the desk reports have appeared by chance?

Inputs (all already in the repository, all traceable to an official NFL.com game
page through ``data/ops/results.csv``):

  data/ops/graded.csv          the originated bets as graded by tools/origination.py
  data/ops/price_snapshots.csv the recorded lines and prices for BOTH sides of every
                               market (T3 third-party prices, labelled as such)
  data/ops/results.csv         the official final score of every game
  data/ops/markets.csv         event -> week, away, home

What is computed
----------------
1. Our record, as recorded (graded.csv) and re-settled from the official score and
   the recorded line for the side we took. A mismatch between the two is reported
   row by row; it is never silently replaced.
2. Control C1 - random picks. Every originated market gets a side chosen by a seeded
   coin flip, settled the same way, at the same recorded price. 10,000 draws.
3. Control C2 - favourites only. Each market bets the favourite: the side laying
   points (side), the shorter price (moneyline), and the more negative price on
   totals, with a fixed tie-break to "over".
4. A game-cluster bootstrap interval for our ROI. The three markets of one game
   are not independent, so events - not bets - are resampled.

Every number is recomputed from the files above on each build. Seeds are fixed, so
the page is byte-reproducible.
"""
import csv
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = os.path.join(ROOT, "data", "ops")
OUT_JSON = os.path.join(ROOT, "data", "output", "luck.json")

SEED = 20261115          # fixed: the panel is reproducible
DRAWS = 10000            # random-pick draws
BOOT = 10000             # cluster-bootstrap resamples
MIN_BETS_PER_TYPE = 100  # gate G2 in data/ops/gates.csv

# Official-source reference for the origination code path that settles side bets.
ORIGINATION_FILE = "tools/origination.py"
ORIGINATION_LINES = "575-578"


def _read(name):
    with open(os.path.join(OPS, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(x):
    return float(str(x).replace("\u2212", "-").replace("+", ""))


def payoff_per_unit(price):
    """Profit on a winning 1-unit stake at an American price."""
    p = _f(price)
    return p / 100.0 if p > 0 else 100.0 / abs(p)


def pct(sorted_vals, q):
    """Linear-interpolated quantile of an already sorted list."""
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def load():
    markets = {}
    for r in _read("markets.csv"):
        markets.setdefault(r["event_id"], {"week": int(r["week"]),
                                           "away": r["away"], "home": r["home"]})
    results = {}
    for r in _read("results.csv"):
        results[(int(r["week"]), r["away"], r["home"])] = r
    prices = {}
    for r in _read("price_snapshots.csv"):
        prices[(r["event_id"], r["market"], r["selection"])] = r
    graded = _read("graded.csv")
    return markets, results, prices, graded


def settle(eid, market, sel, markets, results, prices):
    """Settle one selection against the official score and the recorded line.

    Returns (outcome, line, price, official) where outcome is won / lost / push.
    """
    m = markets[eid]
    res = results[(m["week"], m["away"], m["home"])]
    ap, hp = int(res["away_pts"]), int(res["home_pts"])
    total = ap + hp
    row = prices[(eid, market, sel)]
    official = {"away_pts": ap, "home_pts": hp, "url": res["official_url"]}
    if market == "side":
        line = _f(row["close_line"])
        price = row["close_price"]
        margin = (ap - hp) if sel == "away" else (hp - ap)
        cover = margin + line
        if cover == 0:
            return "push", line, price, official
        return ("won" if cover > 0 else "lost"), line, price, official
    if market == "total":
        line = _f(row["close_line"])
        price = row["close_price"]
        if total == line:
            return "push", line, price, official
        over_hit = total > line
        won = over_hit if sel == "over" else (not over_hit)
        return ("won" if won else "lost"), line, price, official
    # moneyline: winner takes all
    price = row["close_ml"]
    if ap == hp:
        return "push", None, price, official
    winner = "away" if ap > hp else "home"
    return ("won" if winner == sel else "lost"), None, price, official


def pnl_of(outcome, price):
    if outcome == "push":
        return 0.0
    if outcome == "won":
        return payoff_per_unit(price)
    return -1.0


def roi(pnls, stakes):
    s = sum(stakes)
    return (sum(pnls) / s) if s else None


def favourite(eid, market, markets, prices):
    """The favourite under the fixed C2 rule. Ties go to the first named selection."""
    if market == "side":
        a = _f(prices[(eid, "side", "away")]["close_line"])
        return "away" if a <= 0 else "home"
    if market == "total":
        po = _f(prices[(eid, "total", "over")]["close_price"])
        pu = _f(prices[(eid, "total", "under")]["close_price"])
        return "over" if po <= pu else "under"
    aw = _f(prices[(eid, "moneyline", "away")]["close_ml"])
    hm = _f(prices[(eid, "moneyline", "home")]["close_ml"])
    return "away" if aw <= hm else "home"


def other(market, sel):
    if market == "total":
        return "under" if sel == "over" else "over"
    return "home" if sel == "away" else "away"


def compute():
    markets, results, prices, graded = load()

    # ------------------------------------------------ our record, two ways
    units = []   # one per originated market in the graded log
    for g in graded:
        eid, mk, bet = g["event_id"], g["market"], g["bet"]
        out, line, close_price, official = settle(eid, mk, bet, markets, results, prices)
        price_used = g["price"]
        recorded_pnl = _f(g["pnl"])
        units.append({
            "event_id": eid,
            "week": int(g["week"]),
            "market": mk,
            "bet": bet,
            "price": price_used,
            "recorded_outcome": g["outcome"],
            "recorded_pnl": recorded_pnl,
            "resettled_outcome": out,
            "resettled_pnl": pnl_of(out, price_used),
            "line": line,
            "official": official,
            "matches": (out == g["outcome"]),
            "away": markets[eid]["away"],
            "home": markets[eid]["home"],
        })
    events = sorted({u["event_id"] for u in units})
    mismatches = [u for u in units if not u["matches"]]
    n = len(units)
    ours_rec = [u["recorded_pnl"] for u in units]
    ours_res = [u["resettled_pnl"] for u in units]
    stakes = [0.0 if u["resettled_outcome"] == "push" else 1.0 for u in units]

    # ------------------------------------------- the universe for the controls
    # the same 12 event x market units, each priced on both sides
    keys = []
    seen = set()
    for u in units:
        k = (u["event_id"], u["market"])
        if k not in seen:
            seen.add(k)
            keys.append(k)

    # C2 favourites, deterministic
    fav_pnl, fav_out = [], []
    for eid, mk in keys:
        sel = favourite(eid, mk, markets, prices)
        out, _line, price, _o = settle(eid, mk, sel, markets, results, prices)
        fav_out.append(out)
        fav_pnl.append(pnl_of(out, price))
    fav_stakes = [0.0 if o == "push" else 1.0 for o in fav_out]

    # C1 random picks: a seeded coin per unit, DRAWS times
    rng = random.Random(SEED)
    settled_units = []
    for eid, mk in keys:
        sides = ("over", "under") if mk == "total" else ("away", "home")
        cell = {}
        for s in sides:
            out, _line, price, _o = settle(eid, mk, s, markets, results, prices)
            cell[s] = (out, pnl_of(out, price))
        settled_units.append((sides, cell))
    draw_roi = []
    for _ in range(DRAWS):
        total = 0.0
        staked = 0.0
        for sides, cell in settled_units:
            s = sides[0] if rng.random() < 0.5 else sides[1]
            out, p = cell[s]
            total += p
            staked += 0.0 if out == "push" else 1.0
        draw_roi.append(total / staked if staked else 0.0)
    draw_sorted = sorted(draw_roi)
    rand_mean = sum(draw_roi) / len(draw_roi)

    # --------------------------------------- cluster bootstrap on our ROI (events)
    brng = random.Random(SEED + 1)
    by_event = {e: [i for i, u in enumerate(units) if u["event_id"] == e] for e in events}

    def boot(series):
        vals = []
        for _ in range(BOOT):
            pick = [brng.choice(events) for _ in events]
            num = 0.0
            den = 0.0
            for e in pick:
                for i in by_event[e]:
                    num += series[i]
                    den += stakes[i]
            vals.append(num / den if den else 0.0)
        vals.sort()
        return pct(vals, 0.025), pct(vals, 0.975)

    boot_rec = boot(ours_rec)
    boot_res = boot(ours_res)

    def share_ge(x):
        return sum(1 for v in draw_roi if v >= x) / len(draw_roi)

    ours_rec_roi = roi(ours_rec, [1.0] * n)
    ours_res_roi = roi(ours_res, stakes)
    fav_roi = roi(fav_pnl, fav_stakes)

    per_type = {}
    for mk in ("side", "total", "moneyline"):
        k = [u for u in units if u["market"] == mk]
        per_type[mk] = {
            "n": len(k),
            "need": max(0, MIN_BETS_PER_TYPE - len(k)),
            "wins_resettled": sum(1 for u in k if u["resettled_outcome"] == "won"),
            "losses_resettled": sum(1 for u in k if u["resettled_outcome"] == "lost"),
        }

    d = {
        "generated_from": ["data/ops/graded.csv", "data/ops/price_snapshots.csv",
                           "data/ops/results.csv", "data/ops/markets.csv"],
        "seed": SEED,
        "draws": DRAWS,
        "bootstrap_resamples": BOOT,
        "n_bets": n,
        "n_events": len(events),
        "min_bets_per_type": MIN_BETS_PER_TYPE,
        "per_type": per_type,
        "ours_recorded": {
            "roi": ours_rec_roi,
            "pnl_units": sum(ours_rec),
            "ci95_cluster": list(boot_rec),
        },
        "ours_resettled": {
            "roi": ours_res_roi,
            "pnl_units": sum(ours_res),
            "ci95_cluster": list(boot_res),
            "wins": sum(1 for u in units if u["resettled_outcome"] == "won"),
            "losses": sum(1 for u in units if u["resettled_outcome"] == "lost"),
            "pushes": sum(1 for u in units if u["resettled_outcome"] == "push"),
        },
        "control_random": {
            "roi_mean": rand_mean,
            "roi_ci95": [pct(draw_sorted, 0.025), pct(draw_sorted, 0.975)],
            "share_ge_ours_recorded": share_ge(ours_rec_roi),
            "share_ge_ours_resettled": share_ge(ours_res_roi),
        },
        "control_favourites": {
            "roi": fav_roi,
            "pnl_units": sum(fav_pnl),
            "wins": sum(1 for o in fav_out if o == "won"),
            "losses": sum(1 for o in fav_out if o == "lost"),
            "pushes": sum(1 for o in fav_out if o == "push"),
        },
        "mismatches": [
            {"event_id": u["event_id"], "market": u["market"], "bet": u["bet"],
             "recorded": u["recorded_outcome"], "resettled": u["resettled_outcome"],
             "line": u["line"], "official_away": u["official"]["away_pts"],
             "official_home": u["official"]["home_pts"], "official_url": u["official"]["url"]}
            for u in mismatches
        ],
        "units": [
            {"event_id": u["event_id"], "week": u["week"], "market": u["market"],
             "bet": u["bet"], "price": u["price"], "recorded_outcome": u["recorded_outcome"],
             "resettled_outcome": u["resettled_outcome"], "line": u["line"],
             "away": u["away"], "home": u["home"],
             "official_away": u["official"]["away_pts"], "official_home": u["official"]["home_pts"],
             "official_url": u["official"]["url"], "matches": u["matches"]}
            for u in units
        ],
        "origination_settlement_note": {
            "file": ORIGINATION_FILE, "lines": ORIGINATION_LINES,
            "finding": ("side bets are graded on the straight-up winner (margin > 0 compared "
                        "with the side picked) and the spread line is not applied"),
        },
        "favourite_rule": ("side: the side laying points; total: the shorter (more negative) "
                           "price, ties to over; moneyline: the shorter price, ties to away"),
    }
    return d


def main():
    d = compute()
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)
        fh.write("\n")
    o = d["ours_recorded"]
    print("luck: n=%d bets, %d events; ours recorded ROI %.1f%%, re-settled %.1f%%; "
          "random-pick mean %.1f%%, share of draws >= ours (re-settled) %.3f; "
          "favourites ROI %.1f%%; mismatches %d"
          % (d["n_bets"], d["n_events"], 100 * o["roi"], 100 * d["ours_resettled"]["roi"],
             100 * d["control_random"]["roi_mean"],
             d["control_random"]["share_ge_ours_resettled"],
             100 * d["control_favourites"]["roi"], len(d["mismatches"])))


if __name__ == "__main__":
    main()
