#!/usr/bin/env python3
"""The market layer: price snapshots, fair-vs-market differences, the skill and
staking boards, correlations with n, and the demotion gate.

What this adds to the desk
--------------------------
The desk already originates model lines and scores nine strategies on
out-of-sample point-spread error. That answers "how accurate is the forecast?"
It does not answer the four questions a person actually decides with:

  1. what did the market say, at the open and at the close, and how far did my
     number sit from it?
  2. does the forecast beat the market *and* the league constant, out of sample?
  3. is any of it skill, or is it a lucky staking run?
  4. what would send a live strategy back to paper?

This tool answers those from data that is committed to the repository, and it
records the price history of every market it originates.

Rule it does not break
----------------------
`tools/build.py` states that no market/odds data is used anywhere in the model.
That stays true: every fair number here is produced by the *same* engine
functions, from the *same* official game results, and the market price is only
compared with afterwards. The model never sees a price. `tools/market.py`
re-uses the model definitions by AST extraction from `tools/build.py` instead of
copying them, so a line cannot drift between the two pages.

Provenance tiers (published in every table)
-------------------------------------------
  T1  official NFL.com          - results, schedule, game pages, standings
  T2  licensed sportsbook       - DraftKings prices, published by ESPN's public
                                  odds endpoint; archived verbatim in
                                  `data/market-prices-2026.csv`
  T4  this repository           - model numbers derived from T1, and every
                                  statistic computed from T1 + T2

The NFL itself publishes no betting lines, so no price in this repository is
labelled official. Every price row links its ESPN source URL, every result row
links its NFL.com game page, and the difference columns are presented as
comparisons - never as claims about fairness, and never as betting advice.

Usage:  python3 tools/market.py
Output: data/output/market.json
"""
import csv
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "output")
sys.path.insert(0, os.path.join(ROOT, "tools"))

# --------------------------------------------------------------------------------------
# The engine, re-used rather than copied
# --------------------------------------------------------------------------------------
KEEP = {"mean", "ew_avg", "ew_n", "shrink", "sigmoid", "DetRand", "PARAMS", "read_csv",
        "TEAMS", "history", "rate_bundle", "s0_constant", "make_model", "make_blend",
        "S3", "S6", "STRATEGIES", "SEED", "BOOTSTRAP", "DATA", "OUT", "ROOT",
        "games", "games_by_week"}


def load_engine(root=ROOT):
    """Execute only the model definitions in tools/build.py, never its script body."""
    import ast
    import collections
    import contextlib
    import io
    src = open(os.path.join(root, "tools", "build.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    body = []
    for node in tree.body:
        name = None
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in KEEP:
            body.append(node)
    g = {"__name__": "engine_defs",
         "__file__": os.path.join(root, "tools", "build.py"),
         "OrderedDict": collections.OrderedDict, "csv": csv, "json": json,
         "math": math, "os": os, "statistics": __import__("statistics")}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                     "<build:defs>", "exec"), g)
    # build.py's loader leaves week and points as strings; history() needs ints.
    for game in g["games"]:
        game["week"] = int(game["week"])
        game["away_pts"] = int(game["away_pts"])
        game["home_pts"] = int(game["home_pts"])
    g["games_by_week"] = {}
    for game in g["games"]:
        g["games_by_week"].setdefault(game["week"], []).append(game)
    return g


ENGINE = load_engine()

# --------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------


def read(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


SLATE = {r["event_id"]: r for r in read("market-slate-2026.csv")}
ANCHORS = {r["event_id"]: r for r in read("market-anchors-2026.csv")}
PRICES = read("market-prices-2026.csv")

MARKETS = ("spread", "total", "moneyline")
# The order the brief requires origination in: the side first, the total second,
# the moneyline third. S1 in tools/build.py carries the best out-of-sample
# point-spread record, so it is the originating strategy for all three markets.
PRIMARY = "S1"
ORDER = ("side", "total", "moneyline")
MARKET_OF = {"side": "spread", "total": "total", "moneyline": "moneyline"}


def num(value):
    if value is None or value == "":
        return None
    return float(value)


# price index
PRICE = {}
for row in PRICES:
    PRICE[(row["event_id"], row["market"], row["side"])] = row


def price(event, market, side, which):
    row = PRICE.get((event, market, side))
    if not row:
        return None
    return num(row[which])


def american_to_decimal(ml):
    """Standard American odds conversion. Push-free markets only."""
    if ml is None:
        return None
    ml = float(ml)
    return 1.0 + ml / 100.0 if ml > 0 else 1.0 + 100.0 / -ml


def american_to_prob(ml):
    d = american_to_decimal(ml)
    return None if not d else 1.0 / d


def fair_two_way(ml_home, ml_away):
    """Remove the bookmaker's margin from a two-way moneyline. Raw American prices
    imply probabilities that sum to more than 1 (the vig). The model's fair
    probability is compared with the de-vigged market probability, never with the
    raw one, so the difference is not just the bookmaker's markup."""
    if ml_home is None or ml_away is None:
        return None
    ph = american_to_prob(ml_home)
    pa = american_to_prob(ml_away)
    if not ph or not pa or (ph + pa) <= 0:
        return None
    return round(ph / (ph + pa), 4)


def decimal_payout(dec, stake):
    """Profit on a winning bet: stake * (decimal - 1)."""
    return stake * (dec - 1.0)


def normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam ** k / math.factorial(k)


def win_prob_total(mean, sd, line, direction):
    """P(game total clears the line). Continuous normal approximation, as the desk
    already uses for calibration in tools/build.py."""
    if sd <= 0:
        return 1.0 if (mean > line) == (direction == "over") else 0.0
    z = (line - mean) / sd
    p_over = 1.0 - normal_cdf(z)
    return p_over if direction == "over" else 1.0 - p_over


# --------------------------------------------------------------------------------------
# 1. Results feed - the games every backtest is graded against
# --------------------------------------------------------------------------------------
RESULTS = []
for event, game in sorted(SLATE.items(), key=lambda kv: (int(kv[1]["week"]), kv[0])):
    graded = game["status"] == "final"
    RESULTS.append({
        "event_id": event, "week": int(game["week"]),
        "away": game["away"], "home": game["home"],
        "away_pts": int(game["away_pts"]) if graded else None,
        "home_pts": int(game["home_pts"]) if graded else None,
        "status": game["status"],
        "neutral_site": game["neutral_site"] == "1",
        "nfl_url": game["nfl_url"],
        "source_tier": "T1 official NFL.com game page",
        "verified": True,
        # below: filled in once prices are joined
        "prices_verified": event in ANCHORS,
    })
BY_EVENT = {r["event_id"]: r for r in RESULTS}


# --------------------------------------------------------------------------------------
# 2. Price snapshot store - open and close for every originated market
# --------------------------------------------------------------------------------------
def snapshot_row(event, market):
    game = BY_EVENT[event]
    if market == "spread":
        home = {k: price(event, "spread", "home", k) for k in
                ("open_line", "open_price", "close_line", "close_price")}
        away = {k: price(event, "spread", "away", k) for k in
                ("open_line", "open_price", "close_line", "close_price")}
        return {
            "market": "spread",
            "open_home_line": home["open_line"], "close_home_line": home["close_line"],
            "open_away_line": away["open_line"], "close_away_line": away["close_line"],
            "open_home_price": home["open_price"], "close_home_price": home["close_price"],
            "open_away_price": away["open_price"], "close_away_price": away["close_price"],
            # the line moved if the number on the board changed at all
            "moved": abs((home["close_line"] or 0) - (home["open_line"] or 0)) > 1e-9,
            # how far the number on the board travelled, in points, whichever way it went
            "movement": (round(abs(home["close_line"] - home["open_line"]), 1)
                         if home["open_line"] is not None and home["close_line"] is not None
                         else None),
        }
    if market == "total":
        over = {k: price(event, "total", "over", k) for k in
                ("open_line", "open_price", "close_line", "close_price")}
        under = {k: price(event, "total", "under", k) for k in
                 ("open_line", "open_price", "close_line", "close_price")}
        return {
            "market": "total",
            # unified schema: the "home" slots hold the over number, the "away"
            # slots hold the under number, so every market writes the same columns
            "open_line": over["open_line"], "close_line": over["close_line"],
            "open_home_line": over["open_line"], "close_home_line": over["close_line"],
            "open_away_line": under["open_line"], "close_away_line": under["close_line"],
            "open_home_price": over["open_price"], "close_home_price": over["close_price"],
            "open_away_price": under["open_price"], "close_away_price": under["close_price"],
            "open_over_price": over["open_price"], "close_over_price": over["close_price"],
            "open_under_price": under["open_price"], "close_under_price": under["close_price"],
            "moved": abs((over["close_line"] or 0) - (over["open_line"] or 0)) > 1e-9,
            "movement": (round(abs(over["close_line"] - over["open_line"]), 1)
                         if over["open_line"] is not None and over["close_line"] is not None
                         else None),
        }
    home_ml = {k: price(event, "moneyline", "home", k) for k in
               ("open_price", "close_price")}
    away_ml = {k: price(event, "moneyline", "away", k) for k in
               ("open_price", "close_price")}
    open_overround = close_overround = None
    if home_ml["open_price"] is not None and away_ml["open_price"] is not None:
        open_overround = round(american_to_prob(home_ml["open_price"])
                               + american_to_prob(away_ml["open_price"]), 4)
    if home_ml["close_price"] is not None and away_ml["close_price"] is not None:
        close_overround = round(american_to_prob(home_ml["close_price"])
                                + american_to_prob(away_ml["close_price"]), 4)
    # moneyline has no line to move: the price itself moves
    moved = None
    if home_ml["open_price"] is not None and home_ml["close_price"] is not None:
        moved = abs(home_ml["close_price"] - home_ml["open_price"]) > 1e-9
    return {
        "market": "moneyline",
        "open_line": None, "close_line": None,
        "open_home_line": None, "close_home_line": None,
        "open_away_line": None, "close_away_line": None,
        "open_home_price": home_ml["open_price"], "close_home_price": home_ml["close_price"],
        "open_away_price": away_ml["open_price"], "close_away_price": away_ml["close_price"],
        "open_overround": open_overround, "close_overround": close_overround,
        "moved": moved,
        "movement": None,
    }


SNAPSHOTS = []
for game in RESULTS:
    for market in MARKETS:
        if not game["prices_verified"]:
            continue
        snap = snapshot_row(game["event_id"], market)
        snap.update({
            "event_id": game["event_id"], "week": game["week"],
            "away": game["away"], "home": game["home"],
            "nfl_url": game["nfl_url"],
            "price_source_url": ANCHORS[game["event_id"]]["source_url"],
            "snapshot_utc": PRICES[0]["snapshot_utc"],
            "source_tier": "T2 licensed sportsbook (DraftKings via ESPN)",
        })
        SNAPSHOTS.append(snap)

# --------------------------------------------------------------------------------------
# 3. Out-of-sample fair numbers: weeks 9 and 10, which the desk never scored
# --------------------------------------------------------------------------------------
EVAL_WEEKS = (9, 10)
SD_TOTAL = 13.5    # per-game spread/total dispersion used for pricing only
SD_MARGIN = 13.5   # (a modelling choice, declared in params below)

FORECASTS = []
for game in RESULTS:
    if game["week"] not in EVAL_WEEKS or game["status"] != "final":
        continue
    hist = ENGINE["history"](game["week"])
    row = {"event_id": game["event_id"], "week": game["week"],
           "away": game["away"], "home": game["home"],
           "away_pts": game["away_pts"], "home_pts": game["home_pts"],
           "nfl_url": game["nfl_url"], "models": {}}
    for key, strat in ENGINE["STRATEGIES"].items():
        home_pts, away_pts = strat["fn"](hist, game["home"], game["away"], None)
        row["models"][key] = {"home": home_pts, "away": away_pts,
                              "spread": home_pts - away_pts,
                              "total": home_pts + away_pts}
    FORECASTS.append(row)

# --------------------------------------------------------------------------------------
# 4. Bets: origination order (side, total, moneyline) and fair/market/difference
# --------------------------------------------------------------------------------------
# The three lines every strategy is compared against, all computed the same way:
#   model  - that strategy's own number, from engine functions only
#   market - the price on the board (open, and close where the game is final)
#   diff   - model minus market, in points (spread, total) or probability (moneyline)
BETS = []
for game in RESULTS:
    event = game["event_id"]
    if not game["prices_verified"]:
        continue
    fc = next((f for f in FORECASTS if f["event_id"] == event), None)
    hist = ENGINE["history"](game["week"])
    for strategy in ENGINE["STRATEGIES"]:
        if fc:
            model = fc["models"][strategy]
        else:
            # week 11 is not final yet: model numbers come from the same engine
            home_pts, away_pts = ENGINE["STRATEGIES"][strategy]["fn"](
                hist, game["home"], game["away"], None)
            model = {"home": home_pts, "away": away_pts,
                     "spread": home_pts - away_pts, "total": home_pts + away_pts}
        for market_key in ORDER:
            market = MARKET_OF[market_key]
            if market == "spread":
                # Single axis, used for BOTH numbers so the subtraction is meaningful.
                # The board posts a handicap h on the home team: home covers when
                # (margin + h) > 0, so the margin the board implies is -h. The model
                # predicts a margin directly. Put the board on the model's axis and the
                # difference is a like-for-like points comparison:
                #     difference = fair margin - implied market margin
                # Positive means the desk rates home more highly than the board does,
                # so HOME is the value side. The posted handicap is kept alongside so
                # a reader can still see the number on the board.
                m_open = price(event, "spread", "home", "open_line")
                m_close = price(event, "spread", "home", "close_line")
                fair = round(model["spread"], 2)
                mkt_open = round(-m_open, 2) if m_open is not None else None
                mkt = round(-m_close, 2) if m_close is not None else None
                diff_open = round(fair - mkt_open, 2) if mkt_open is not None else None
                diff_close = round(fair - mkt, 2) if mkt is not None else None
                side = "home" if diff_close is None or diff_close >= 0 else "away"
                diff = diff_close
                unit = "pts"
            elif market == "total":
                m_open = price(event, "total", "over", "open_line")
                m_close = price(event, "total", "over", "close_line")
                diff_open = round(model["total"] - m_open, 2) if m_open is not None else None
                diff_close = round(model["total"] - m_close, 2) if m_close is not None else None
                side = "over" if diff_close is None or model["total"] >= (m_close or 0) else "under"
                fair, mkt, diff = round(model["total"], 2), m_close, diff_close
                unit = "pts"
            else:
                p_home = win_prob_total(model["spread"], SD_MARGIN, 0.0, "over")
                fair = round(p_home, 4)
                ml_open = price(event, "moneyline", "home", "open_price")
                ml_close = price(event, "moneyline", "home", "close_price")
                # de-vig both snapshots with the corresponding away price
                mkt_open = fair_two_way(ml_open, price(event, "moneyline", "away", "open_price"))
                mkt = fair_two_way(ml_close, price(event, "moneyline", "away", "close_price"))
                diff = round(fair - mkt, 4) if mkt is not None else None
                diff_open = round(fair - mkt_open, 4) if mkt_open is not None else None
                diff_close = diff
                side = "home" if diff is None or diff >= 0 else "away"
                unit = "prob"
            BETS.append({
                "event_id": event, "week": game["week"], "away": game["away"],
                "home": game["home"], "strategy": strategy,
                "market_order": ORDER.index(market_key) + 1,
                "market_key": market_key, "market_type": market, "market_line": mkt, "side": side,
                "fair": fair, "market": mkt,
                # market_open is on the SAME axis as market_line (implied margin), so a
                # subtraction between them means something. For the moneyline both are
                # probabilities, which is already one axis.
                "market_open": (mkt_open if market == "moneyline"
                                else (round(-m_open, 2) if m_open is not None else None)),
                "difference": diff, "difference_open": diff_open,
                "unit": unit, "status": game["status"],
                "nfl_url": game["nfl_url"],
                "price_source_url": ANCHORS[event]["source_url"],
            })

# --------------------------------------------------------------------------------------
# 5. Grading and the staking ledger
# --------------------------------------------------------------------------------------
STAKE = 1.0          # flat unit stake, so ROI is comparable across strategies
KELLY_FRACTION = 0.25
BANKROLL = 100.0
KELLY_CAP = 0.05     # never more than 5% of bankroll on one bet


def settle(bet, game):
    """Return (result, profit, detail). result in {win, loss, push, void}."""
    if game["status"] != "final":
        return "void", 0.0, "game not final"
    margin = game["home_pts"] - game["away_pts"]
    total = game["home_pts"] + game["away_pts"]
    if bet["market_type"] == "spread":
        line = bet["market_line"]
        if line is None:
            return "void", 0.0, "no line"
        # market_line is the margin the board implies (the negation of the posted
        # home handicap), so home covers exactly when the actual margin beats it.
        adjusted = margin - line
        if abs(adjusted) < 1e-9:
            return "push", 0.0, "exact push"
        won = (adjusted > 0) if bet["side"] == "home" else (adjusted < 0)
        dec = american_to_decimal(price(bet["event_id"], "spread", bet["side"], "close_price"))
        if dec is None:
            return "void", 0.0, "no price"
        return ("win" if won else "loss"), (decimal_payout(dec, STAKE) if won else -STAKE), \
            "margin %d vs implied margin %s = %s" % (margin, line, adjusted)
    if bet["market_type"] == "total":
        line = bet["market_line"]
        if line is None:
            return "void", 0.0, "no line"
        if abs(total - line) < 1e-9:
            return "push", 0.0, "exact push"
        won = (total > line) if bet["side"] == "over" else (total < line)
        dec = american_to_decimal(price(bet["event_id"], "total", bet["side"], "close_price"))
        if dec is None:
            return "void", 0.0, "no price"
        return ("win" if won else "loss"), (decimal_payout(dec, STAKE) if won else -STAKE), \
            "total %d vs line %s" % (total, line)
    # moneyline: home wins strictly more than away (a tie in the NFL is possible)
    if bet["market_type"] != "moneyline":
        return "void", 0.0, "unknown market"
    p = bet["market_line"]
    if p is None:
        return "void", 0.0, "no price"
    if margin == 0:
        return "push", 0.0, "tied game"
    home_won = margin > 0
    won = home_won if bet["side"] == "home" else not home_won
    dec = american_to_decimal(price(bet["event_id"], "moneyline", bet["side"], "close_price"))
    if dec is None:
        return "void", 0.0, "no price"
    return ("win" if won else "loss"), (decimal_payout(dec, STAKE) if won else -STAKE), \
        ("%s won by %d" % (("home" if home_won else "away"), abs(margin)))


def kelly_stake(prob, dec):
    """Fractional Kelly on a single bet, capped. prob is the model's probability of
    the side it selected; dec is the decimal price of that side."""
    if prob is None or dec is None or dec <= 1.0:
        return 0.0
    b = dec - 1.0
    edge = prob * b - (1.0 - prob)
    if edge <= 0:
        return 0.0
    raw = edge / b
    return min(raw * KELLY_FRACTION, KELLY_CAP)


for bet in BETS:
    game = BY_EVENT[bet["event_id"]]
    result, profit, detail = settle(bet, game)
    bet["result"] = result
    bet["profit"] = round(profit, 4) if result != "void" else None
    bet["detail"] = detail
    # staking: the stake is sized by the model's own probability, converted to the
    # side actually selected, and never by hindsight.
    if result in ("win", "loss", "push") and bet["market_type"] != "moneyline":
        if bet["market_type"] == "spread":
            # fair is a MARGIN, market_line is the posted HANDICAP. For the chosen side,
            # the probability it covers is P(model margin - threshold > 0) where the
            # threshold is what that side needs to beat.
            line = bet["market_line"]
            if bet["side"] == "home":
                p_sel = win_prob_total(bet["fair"], SD_MARGIN, line, "over")
            else:
                p_sel = 1.0 - win_prob_total(bet["fair"], SD_MARGIN, line, "over")
            dec = american_to_decimal(price(bet["event_id"], "spread", bet["side"], "close_price"))
        else:
            p_sel = win_prob_total(bet["fair"], SD_TOTAL, bet["market_line"],
                                   "over" if bet["side"] == "over" else "under")
            dec = american_to_decimal(price(bet["event_id"], "total", bet["side"], "close_price"))
        frac = kelly_stake(p_sel, dec)
    elif result in ("win", "loss", "push"):
        p_sel = bet["fair"] if bet["side"] == "home" else 1.0 - bet["fair"]
        dec = american_to_decimal(price(bet["event_id"], "moneyline", bet["side"], "close_price"))
        frac = kelly_stake(p_sel, dec)
    else:
        frac = 0.0
    bet["stake_units"] = round(min(frac * BANKROLL, KELLY_CAP * BANKROLL), 4)
    bet["stake_profit"] = (round(bet["profit"] * (bet["stake_units"] / STAKE), 4)
                           if bet["profit"] is not None else None)

# --------------------------------------------------------------------------------------
# 6. The two boards: skill (never sees a stake) and staking (never sets a rank)
# --------------------------------------------------------------------------------------
evals = [g for g in RESULTS if g["status"] == "final" and g["week"] in EVAL_WEEKS]
n_eval = len(evals)


def mae(vals):
    return sum(abs(v) for v in vals) / len(vals) if vals else None


def rmse(vals):
    return math.sqrt(sum(v * v for v in vals) / len(vals)) if vals else None


SKILL = {}
for strategy in ENGINE["STRATEGIES"]:
    rows = [b for b in BETS if b["strategy"] == strategy and b["status"] == "final"]
    fc = [f for f in FORECASTS]
    spread_err = [f["models"][strategy]["spread"] - (f["home_pts"] - f["away_pts"]) for f in fc]
    total_err = [f["models"][strategy]["total"] - (f["home_pts"] + f["away_pts"]) for f in fc]
    # market error, from the close - the number to be beaten
    mkt_spread_err, mkt_total_err = [], []
    for f in fc:
        line = price(f["event_id"], "spread", "home", "close_line")
        if line is not None:
            # a handicap (home -7) is the market's implied margin only after negation:
            # the market's predicted home margin is -line.
            mkt_spread_err.append(-line - (f["home_pts"] - f["away_pts"]))
        tot = price(f["event_id"], "total", "over", "close_line")
        if tot is not None:
            mkt_total_err.append(tot - (f["home_pts"] + f["away_pts"]))
    # closing line value: how much better than the closing number the side was taken at
    # Closing-line value, in points, for the spread only, and measured honestly.
    #
    # Naively computing "did the line move toward the side we picked" is a tautology
    # here: the side is picked AT THE CLOSE when the difference crosses zero, so the
    # close has already moved toward it by construction and every strategy would score
    # a positive CLV no matter how bad it was. That version was written first and it
    # reported +4 to +9 points for all nine strategies, which is how the artefact was
    # caught. A metric that cannot come out negative is not a metric.
    #
    # The honest question is about the model's opinion at the OPEN, before it knew what
    # the close would be: take the side the model favoured against the opening number,
    # then ask how far the market moved in that side's favour by the close. Both numbers
    # are implied margins (the negation of the posted home handicap). A home opinion is
    # vindicated when the closing implied margin rose (home became a bigger favourite
    # after we took it cheap): close - open. An away opinion is vindicated when it fell:
    # open - close.
    clv = []
    for b in rows:
        if b["market_type"] != "spread":
            continue
        o, c = b["market_open"], b["market_line"]
        if o is None or c is None:
            continue
        side_at_open = "home" if (b["fair"] - o) >= 0 else "away"
        # A home opinion profits when the closing line moved AWAY from home being cheap,
        # i.e. when home became a stronger favourite: the implied margin rose. An away
        # opinion profits when it fell. (market_open/market_line are already implied
        # margins, which is why the sign is the plain one here.)
        moved = (c - o) if side_at_open == "home" else (o - c)
        b["clv"] = round(moved, 2)
        b["side_at_open"] = side_at_open
        clv.append(moved)
    spread_hits = [b for b in rows if b["market_type"] == "spread" and b["result"] in ("win", "loss")]
    total_hits = [b for b in rows if b["market_type"] == "total" and b["result"] in ("win", "loss")]
    ml_hits = [b for b in rows if b["market_type"] == "moneyline" and b["result"] in ("win", "loss")]
    SKILL[strategy] = {
        "name": ENGINE["STRATEGIES"][strategy]["name"],
        "n": len(fc),
        "spread_mae": round(mae(spread_err), 4) if spread_err else None,
        "spread_rmse": round(rmse(spread_err), 4) if spread_err else None,
        "total_mae": round(mae(total_err), 4) if total_err else None,
        "total_rmse": round(rmse(total_err), 4) if total_err else None,
        "market_spread_mae": round(mae(mkt_spread_err), 4) if mkt_spread_err else None,
        "market_total_mae": round(mae(mkt_total_err), 4) if mkt_total_err else None,
        "beats_market_spread": (round(mae(mkt_spread_err) - mae(spread_err), 4)
                                if spread_err and mkt_spread_err else None),
        "beats_market_total": (round(mae(mkt_total_err) - mae(total_err), 4)
                               if total_err and mkt_total_err else None),
        "mean_clv": round(sum(clv) / len(clv), 4) if clv else None,
        "spread_record": "%d-%d" % (sum(1 for b in spread_hits if b["result"] == "win"),
                                    sum(1 for b in spread_hits if b["result"] == "loss")),
        "total_record": "%d-%d" % (sum(1 for b in total_hits if b["result"] == "win"),
                                   sum(1 for b in total_hits if b["result"] == "loss")),
        "moneyline_record": "%d-%d" % (sum(1 for b in ml_hits if b["result"] == "win"),
                                       sum(1 for b in ml_hits if b["result"] == "loss")),
        # skill rank is set by error alone; stakes are not an input
        "_rank_key": mae(spread_err) if spread_err else 9e9,
    }

# market benchmark as a "strategy" row so the leaderboard has a spine
SKILL["MARKET"] = {
    "n": n_eval,
    "spread_mae": SKILL[PRIMARY]["market_spread_mae"],
    "spread_rmse": None,
    "total_mae": SKILL[PRIMARY]["market_total_mae"],
    "total_rmse": None,
    "market_spread_mae": SKILL[PRIMARY]["market_spread_mae"],
    "market_total_mae": SKILL[PRIMARY]["market_total_mae"],
    "beats_market_spread": 0.0, "beats_market_total": 0.0,
    "mean_clv": 0.0, "spread_record": "-", "total_record": "-", "moneyline_record": "-",
    "_rank_key": SKILL[PRIMARY]["market_spread_mae"] or 9e9,
    "skill_rank": None,      # the benchmark has no rank: it is the line to be beaten
    "name": "The closing line",
}

skill_order = sorted([k for k in SKILL if k != "MARKET"], key=lambda k: SKILL[k]["_rank_key"])
for i, key in enumerate(skill_order, 1):
    SKILL[key]["skill_rank"] = i

STAKING = {}
for strategy in list(ENGINE["STRATEGIES"]) + ["MARKET"]:
    rows = [b for b in BETS if b["strategy"] == strategy and b["profit"] is not None]
    staked = sum((b["stake_profit"] or 0) for b in rows)
    units = sum(abs(b["stake_profit"] or 0) for b in rows)
    decided = [b for b in rows if b["result"] in ("win", "loss")]
    wins = sum(1 for b in decided if b["result"] == "win")
    staking_profit = sum((b["profit"] or 0) for b in rows)
    flat_staked = len(decided)
    STAKING[strategy] = {
        "n": len(rows),
        "decided": len(decided),
        "wins": wins,
        "losses": len(decided) - wins,
        "pushes": len([b for b in rows if b["result"] == "push"]),
        "flat_profit": round(staking_profit, 4),
        "flat_roi": round(staking_profit / flat_staked, 4) if flat_staked else None,
        "kelly_profit": round(staked, 4),
        "kelly_roi": round(staked / units, 4) if units else None,
        "growth_per_unit": round((staked / BANKROLL) / (sum(b["stake_units"] for b in rows) / BANKROLL), 4)
        if sum(b["stake_units"] for b in rows) else None,
    }
staking_order = sorted(STAKING, key=lambda k: -(STAKING[k]["kelly_profit"] or -9e9))
for i, key in enumerate(staking_order, 1):
    STAKING[key]["staking_rank"] = i

# The rule the brief demands: a lucky staking run cannot lift a skill rank.
for key, row in STAKING.items():
    row["skill_rank"] = SKILL.get(key, {}).get("skill_rank")
    row["skill_better_than_staking"] = (
        None if row["skill_rank"] is None else row["skill_rank"] < row["staking_rank"])
DISAGREEMENTS = [k for k in STAKING if k != "MARKET"
                 and STAKING[k]["skill_better_than_staking"] is not None]

# --------------------------------------------------------------------------------------
# 7. Depth: how often the number the side was taken at survived to the close
# --------------------------------------------------------------------------------------
DEPTH = {"spread": {}, "total": {}}
for market in ("spread", "total"):
    key = "close_home_line" if market == "spread" else "close_line"
    okey = "open_home_line" if market == "spread" else "open_line"
    graded = [s for s in SNAPSHOTS if s["market"] == market
              and BY_EVENT[s["event_id"]]["status"] == "final"]
    moved = [s for s in graded if s.get("moved")]
    unmoved = [s for s in graded if not s.get("moved")]
    moves = [abs(s["movement"]) for s in graded if s.get("movement") is not None]
    DEPTH[market] = {
        "n": len(graded),
        "moved": len(moved),
        "unmoved": len(unmoved),
        "share_unmoved": round(len(unmoved) / len(graded), 4) if graded else None,
        "mean_abs_move": round(sum(moves) / len(moves), 3) if moves else None,
        "max_abs_move": max(moves) if moves else None,
    }

# Depth of the *replacement*: for every bet whose side was taken at the open,
# count how many graded games closed on the same number and side.
DEPTH_BY_MARKET_ORDER = []
for mk in ORDER:
    rows = [b for b in BETS if b["market_key"] == mk and b["status"] == "final"]
    survived = 0
    total = 0
    for b in rows:
        if mk == "moneyline":
            continue
        line_open = b["market_open"]
        line_close = b["market_line"]
        if line_open is None or line_close is None:
            continue
        total += 1
        if abs(line_open - line_close) < 1e-9:
            survived += 1
    DEPTH_BY_MARKET_ORDER.append({
        "market_key": mk, "market": MARKET_OF[mk], "n": total,
        "same_number_at_close": survived,
        "share_same_number": round(survived / total, 4) if total else None,
        "note": ("the side is a price, not a number, so depth here is the price move "
                 "reported in the snapshot table" if mk == "moneyline"
                 else "how often the originating number was still the closing number"),
    })

# --------------------------------------------------------------------------------------
# 8. Correlations, computed only from in-repo official-derived data
# --------------------------------------------------------------------------------------
def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    z = math.atanh(max(min(r, 0.999999), -0.999999))
    se = 1.0 / math.sqrt(n - 3)
    return {"n": n, "r": round(r, 4),
            "ci95": [round(math.tanh(z - 1.96 * se), 4), round(math.tanh(z + 1.96 * se), 4)]}


def residuals(y, x):
    """Residuals of a simple OLS fit of y on x, aligned with the input order."""
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    b = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / sxx if sxx else 0.0
    a = my - b * mx
    return [yi - (a + b * xi) for xi, yi in zip(x, y)]


OFFICIAL_GAMES = [g for g in ENGINE["games"]]
margin_all = [g["home_pts"] - g["away_pts"] for g in OFFICIAL_GAMES]
total_all = [g["home_pts"] + g["away_pts"] for g in OFFICIAL_GAMES]
CORRELATIONS = []


def add_corr(label, xs, ys, definition, why, tier="T4 this repository, computed from T1 results"):
    res = pearson(xs, ys)
    CORRELATIONS.append({
        "label": label, "definition": definition, "why": why,
        "n": res["n"] if res else len(xs), "r": res["r"] if res else None,
        "ci95": res["ci95"] if res else None,
        "source": "data/games-2026.csv (150 official NFL.com game pages, proved by tools/verify.py)",
        "source_tier": tier,
    })


add_corr("margin vs total", margin_all, total_all,
         "Pearson r between the game's final margin (home - away) and its total points (home + away)",
         "The parlay-critical pair: if these co-move, a side leg and a total leg cannot be priced independently.")
add_corr("home points vs away points", [g["home_pts"] for g in OFFICIAL_GAMES],
         [g["away_pts"] for g in OFFICIAL_GAMES],
         "Pearson r between the home team's score and the away team's score",
         "Measures whether a game is a shootout for both teams or only one; the input to same-game sizing.")
add_corr("total vs home win", total_all,
         [1.0 if g["home_pts"] > g["away_pts"] else 0.0 for g in OFFICIAL_GAMES],
         "Pearson r between total points and a 1/0 home-win indicator",
         "A point-biserial check: does the home side win more often in high-scoring games?")
# two legs many people combine: the home side covering a spread and the total going over
add_corr("cover vs over", [margin_all[i] - 0.0 for i in range(len(margin_all))], total_all,
         "Pearson r between final margin and total points, the same pair expressed for a "
         "spread leg and a total leg",
         "The same-sample statement of margin-vs-total, reported separately because a parlay "
         "needs the leg-level view.")

# market-level correlations: open and close, from the price store only
open_spread = []
close_spread = []
close_total = []
for snap in SNAPSHOTS:
    if snap["market"] == "spread" and snap["close_home_line"] is not None:
        close_spread.append(snap["close_home_line"])
open_spread_by_event = {s["event_id"]: s.get("open_home_line") for s in SNAPSHOTS if s["market"] == "spread"}
close_total_by_event = {s["event_id"]: s.get("close_line") for s in SNAPSHOTS if s["market"] == "total"}
paired = [(open_spread_by_event[e], close_total_by_event[e]) for e in open_spread_by_event
          if open_spread_by_event[e] is not None and close_total_by_event.get(e) is not None]
if len(paired) >= 3:
    CORRELATIONS.append({
        "label": "opening spread vs closing total",
        "definition": "Pearson r between the home spread at the open and the game total at the close",
        "why": "Does the market move the number and the total together? If not, side and total legs "
               "are closer to independent than a same-game parlay would assume.",
        "n": pearson([p[0] for p in paired], [p[1] for p in paired])["n"],
        "r": pearson([p[0] for p in paired], [p[1] for p in paired])["r"],
        "ci95": pearson([p[0] for p in paired], [p[1] for p in paired])["ci95"],
        "source": "data/market-prices-2026.csv (DraftKings via ESPN, archived verbatim)",
        "source_tier": "T2 licensed sportsbook (DraftKings via ESPN)",
    })

# --------------------------------------------------------------------------------------
# 9. The demotion gate
# --------------------------------------------------------------------------------------
DEMOTION = {
    "policy": "A strategy is live only while every rule below passes. One breach sends it "
              "back to paper at the next build; the default is paper.",
    "min_graded_bets": 25,
    "min_clv": -0.5,
    "max_kelly_drawdown": -8.0,
    "max_error_vs_market": 0.0,
    "rules": [],
    "evaluated": [],
}
STARTING_BANKROLL_UNITS = BANKROLL


def running_drawdown(profits):
    bank = STARTING_BANKROLL_UNITS
    peak = bank
    worst = 0.0
    for p in profits:
        bank += p
        peak = max(peak, bank)
        worst = min(worst, bank - peak)
    return round(worst, 4)


for strategy in ENGINE["STRATEGIES"]:
    rows = [b for b in BETS if b["strategy"] == strategy and b["profit"] is not None]
    graded = [b for b in rows if b["result"] in ("win", "loss")]
    drawdown = running_drawdown([b["stake_profit"] or 0.0 for b in rows])
    clv = SKILL[strategy]["mean_clv"]
    beats = SKILL[strategy]["beats_market_spread"]
    checks = [
        {"id": "D1", "rule": "at least %d graded bets" % DEMOTION["min_graded_bets"],
         "value": len(graded), "pass": len(graded) >= DEMOTION["min_graded_bets"]},
        {"id": "D2", "rule": "spread error no worse than the market",
         "value": beats, "pass": beats is not None and beats > DEMOTION["max_error_vs_market"]},
        {"id": "D3", "rule": "mean closing-line value at least %.1f points" % DEMOTION["min_clv"],
         "value": clv, "pass": clv is not None and clv >= DEMOTION["min_clv"]},
        {"id": "D4", "rule": "kelly-staked drawdown no worse than %.1f units" % DEMOTION["max_kelly_drawdown"],
         "value": drawdown, "pass": drawdown >= DEMOTION["max_kelly_drawdown"]},
    ]
    failed = [c["id"] for c in checks if not c["pass"]]
    DEMOTION["evaluated"].append({
        "strategy": strategy, "name": ENGINE["STRATEGIES"][strategy]["name"],
        "checks": checks, "failed": failed,
        "state": "live" if not failed else "paper",
        "reason": ("every rule passes" if not failed else
                   "failed " + ", ".join(failed) + "; back to paper"),
    })
for rule in ("D1", "D2", "D3", "D4"):
    DEMOTION["rules"].append(next(c["rule"] for c in DEMOTION["evaluated"][0]["checks"]
                                  if c["id"] == rule))
DEMOTION["live_count"] = sum(1 for e in DEMOTION["evaluated"] if e["state"] == "live")
DEMOTION["paper_count"] = len(DEMOTION["evaluated"]) - DEMOTION["live_count"]

# --------------------------------------------------------------------------------------
# 10. Originated markets for week 11, in the required order
# --------------------------------------------------------------------------------------
def originate():
    out = []
    hist = ENGINE["history"](11)
    for game in [r for r in RESULTS if r["week"] == 11]:
        event = game["event_id"]
        home_pts, away_pts = ENGINE["STRATEGIES"][PRIMARY]["fn"](
            hist, game["home"], game["away"], None)
        model = {"home": home_pts, "away": away_pts,
                 "spread": home_pts - away_pts, "total": home_pts + away_pts}
        s_anchor = ANCHORS[event]
        # the posted home handicap as the book published it, and the same number on the
        # margin axis every model number uses (implied margin = -handicap)
        posted_home = num(s_anchor["spread_home"])
        mkt_margin = -posted_home
        fair_fav = game["home"] if model["spread"] >= 0 else game["away"]
        mkt_side = (game["home"] if posted_home < 0 else game["away"])
        out.append({
            "event_id": event, "week": 11, "away": game["away"], "home": game["home"],
            "nfl_url": game["nfl_url"], "price_source_url": s_anchor["source_url"],
            # 1. the side. fair and market are BOTH margins, so the difference is
            # like-for-like; the posted handicap travels alongside for the reader.
            "side_fair_spread": round(model["spread"], 2),
            "side_fair_favourite": fair_fav,
            "side_market_spread": round(mkt_margin, 2),
            "side_market_handicap": posted_home,
            "side_market_favourite": mkt_side,
            "side_difference": round(model["spread"] - mkt_margin, 2),
            # 2. the total
            "total_fair": round(model["total"], 2),
            "total_market": num(s_anchor["over_under"]),
            "total_difference": round(model["total"] - num(s_anchor["over_under"]), 2),
            # 3. the moneyline
            "ml_fair_home": round(win_prob_total(model["spread"], SD_MARGIN, 0.0, "over"), 4),
            "ml_market_home": fair_two_way(price(event, "moneyline", "home", "close_price"),
                                           price(event, "moneyline", "away", "close_price")),
            # the difference is fair minus the DE-VIGGED close, the same expression the
            # graded bet rows use, so the two can never disagree
            "ml_difference": round(
                win_prob_total(model["spread"], SD_MARGIN, 0.0, "over")
                - fair_two_way(price(event, "moneyline", "home", "close_price"),
                               price(event, "moneyline", "away", "close_price")), 4)
            if fair_two_way(price(event, "moneyline", "home", "close_price"),
                            price(event, "moneyline", "away", "close_price")) is not None else None,
            "ml_open_home": price(event, "moneyline", "home", "open_price"),
            "ml_close_home": price(event, "moneyline", "home", "close_price"),
            "open_spread_home": price(event, "spread", "home", "open_line"),
            "close_spread_home": price(event, "spread", "home", "close_line"),
            "open_total": price(event, "total", "over", "open_line"),
            "close_total": price(event, "total", "over", "close_line"),
        })
    return out


ORIGINATED = originate()


# --------------------------------------------------------------------------------------
# 10b. Diagnostic: how far the desk's numbers sit from the board, and in which direction
# --------------------------------------------------------------------------------------
# Two facts are published here rather than asserted in prose, because both are
# uncomfortable and both are checkable from the payload:
#   1. The desk's fair spreads are COMPRESSED relative to the market's. On the graded
#      sample the mean absolute fair handicap is smaller than the mean absolute market
#      handicap, so the model sits nearer zero than the board on most games. A model
#      that sits near zero picks the underdog whenever the board does not, which is a
#      mechanical source of picks that has nothing to do with information.
#   2. A pick's win rate is therefore NOT evidence of skill. The skill board is read on
#      error against the market, and the gate in section 9 uses closing-line value.
def _market_anchoring():
    graded = [b for b in BETS if b["status"] == "final" and b["market_type"] == "spread"]
    by_strategy = {}
    for strategy in ENGINE["STRATEGIES"]:
        rows = [b for b in graded if b["strategy"] == strategy]
        if not rows:
            continue
        mean_abs_fair = sum(abs(b["fair"]) for b in rows) / len(rows)
        mean_abs_mkt = sum(abs(b["market_line"]) for b in rows) / len(rows)
        by_strategy[strategy] = {
            "n": len(rows),
            "mean_abs_fair_handicap": round(mean_abs_fair, 3),
            "mean_abs_market_handicap": round(mean_abs_mkt, 3),
            "compression_ratio": (round(mean_abs_fair / mean_abs_mkt, 3)
                                  if mean_abs_mkt else None),
            "mean_difference": round(sum(b["difference"] for b in rows) / len(rows), 3),
        }
    return {
        "by_strategy": by_strategy,
        "definition": (
            "For every graded spread bet, the fair handicap and the market handicap are "
            "compared in absolute value. compression_ratio below 1 means the desk's number "
            "sits closer to zero than the board's, so the desk systematically takes the "
            "underdog side. mean_difference is the average signed edge claim."
        ),
        "source": "data/market-snapshots-2026.csv (T2 prices) and the model forecasts in this payload",
        "source_tier": "T4 this repository, computed from T2 prices",
        "why_it_matters": (
            "A compressed model wins the underdog side often in a season when underdogs "
            "cover, without that being skill. It is why the staking board is reported "
            "separately from the skill board and why the demotion gate reads closing-line "
            "value rather than the record."
        ),
        "status": "published, not corrected",
    }


MARKET_ANCHORING = _market_anchoring()

# --------------------------------------------------------------------------------------
# 11. Publish
# --------------------------------------------------------------------------------------
PAYLOAD = {
    "meta": {
        "generated_by": "tools/market.py",
        "primary_strategy": PRIMARY,
        "primary_strategy_name": ENGINE["STRATEGIES"][PRIMARY]["name"],
        "origination_order": list(ORDER),
        "eval_weeks": list(EVAL_WEEKS),
        "eval_games": n_eval,
        "graded_markets": len([b for b in BETS if b["status"] == "final"]),
        "originated_markets": len(ORIGINATED),
        "snapshot_utc": PRICES[0]["snapshot_utc"],
        "params": {
            "stake_units": STAKE, "kelly_fraction": KELLY_FRACTION,
            "bankroll_units": BANKROLL, "kelly_cap": KELLY_CAP,
            "sd_total": SD_TOTAL, "sd_margin": SD_MARGIN,
            "bootstrap_resamples": ENGINE["BOOTSTRAP"], "seed": ENGINE["SEED"],
        },
        "provenance": {
            "T1": "official NFL.com pages (results, schedule, game pages, standings)",
            "T2": "licensed sportsbook prices (DraftKings) published by ESPN; archived verbatim",
            "T4": "model numbers and statistics computed in this repository from T1 and T2",
            "note": "The NFL publishes no betting lines. No price here is labelled official.",
        },
        "limits": [
            "The graded sample is %d games (weeks 9-10). That is small, and every "
            "significance statement is reported against it rather than glossed over." % n_eval,
            "Depth is measured as line movement between the archived open and close. It is "
            "not order-book depth, which this repository has no source for.",
            "Player-prop markets and prop-combo correlations are not published: no official "
            "source for player-level prices was confirmed, so those cells are left blank.",
        ],
    },
    "results": RESULTS,
    "snapshots": SNAPSHOTS,
    "forecasts": FORECASTS,
    "bets": BETS,
    "skill": SKILL,
    "staking": STAKING,
    "staking_vs_skill": {
        "disagreements": DISAGREEMENTS,
        "rule": "A strategy's skill rank comes from out-of-sample error only. A staking run, "
                "however good, cannot change it. Where the two ranks disagree the table says so.",
    },
    "depth": DEPTH,
    "depth_by_market_order": DEPTH_BY_MARKET_ORDER,
    "correlations": CORRELATIONS,
    "demotion": DEMOTION,
    "market_anchoring": MARKET_ANCHORING,
    "originated": ORIGINATED,
}


def round_floats(obj, places=6):
    if isinstance(obj, float):
        return round(obj, places)
    if isinstance(obj, dict):
        return {k: round_floats(v, places) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [round_floats(v, places) for v in obj]
    return obj


def fmt(v):
    """CSV cell: blank for missing, one decimal for lines, integer for prices."""
    if v is None or v == "":
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    return ("%.1f" % float(v)) if abs(float(v) - round(float(v), 1)) < 1e-9 else str(v)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    # price-snapshot store, one row per game and market: the open and the close side by
    # side, so the movement and the depth of replacement are both readable
    import csv as _csv
    snap_path = os.path.join(DATA, "market-snapshots-2026.csv")
    snap_fields = ["event_id", "market", "week", "away", "home", "open_home_line",
                   "close_home_line", "open_away_line", "close_away_line",
                   "open_home_price", "close_home_price", "open_away_price",
                   "close_away_price", "movement", "moved", "snapshot_utc",
                   "nfl_url", "source_url"]
    with open(snap_path, "w", newline="", encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=snap_fields, lineterminator="\n")
        w.writeheader()
        for snap in SNAPSHOTS:
            w.writerow({
                "event_id": snap["event_id"], "market": snap["market"],
                "week": snap["week"], "away": snap["away"], "home": snap["home"],
                "open_home_line": fmt(snap.get("open_home_line")),
                "close_home_line": fmt(snap.get("close_home_line")),
                "open_away_line": fmt(snap.get("open_away_line")),
                "close_away_line": fmt(snap.get("close_away_line")),
                "open_home_price": fmt(snap.get("open_home_price")),
                "close_home_price": fmt(snap.get("close_home_price")),
                "open_away_price": fmt(snap.get("open_away_price")),
                "close_away_price": fmt(snap.get("close_away_price")),
                "movement": fmt(snap.get("movement")),
                "moved": "1" if snap.get("moved") else "0",
                "snapshot_utc": snap["snapshot_utc"],
                "nfl_url": snap["nfl_url"],
                "source_url": snap["price_source_url"],
            })
    print("snapshot store: %s (%d rows)" % (snap_path, len(SNAPSHOTS)))

    with open(os.path.join(OUT, "market.json"), "w", encoding="utf-8") as fh:
        json.dump(round_floats(PAYLOAD), fh, indent=1)
    print("results: %d games (%d final)" %
          (len(RESULTS), sum(1 for r in RESULTS if r["status"] == "final")))
    print("price snapshots: %d (%d games verified)" %
          (len(SNAPSHOTS), len({s["event_id"] for s in SNAPSHOTS})))
    print("graded markets: %d, originated: %d, eval games: %d" %
          (len([b for b in BETS if b["status"] == "final"]), len(ORIGINATED), n_eval))
    print("skill order:", ", ".join("%s(%s)" % (k, SKILL[k]["spread_mae"]) for k in skill_order))
    print("demotion: %d live, %d back to paper" %
          (DEMOTION["live_count"], DEMOTION["paper_count"]))
    print("depth: spread %s, total %s" % (DEPTH["spread"]["share_unmoved"],
                                          DEPTH["total"]["share_unmoved"]))
    print("correlations: " + ", ".join("%s r=%s n=%s" %
                                       (c["label"], c["r"], c["n"]) for c in CORRELATIONS))
    print("wrote data/output/market.json")
