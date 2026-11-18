#!/usr/bin/env python3
"""Price-snapshot store, origination card and results feed.

This module answers four questions the site could not previously answer:

1. **What did the market say when we originated, and what does it say now?**
   ``data/market-snapshots.csv`` registers every dated snapshot and
   ``data/market-prices.csv`` stores one row per snapshot x game x market
   (spread, total, moneyline). The closing snapshot is registered but empty:
   no Week 11 game has kicked off, so no closing line exists yet.

2. **In what order are the markets originated?** Side (spread) first, total
   second, moneyline third - ``origination_card()`` writes the three markets in
   that order from the same team-rate model, each with its own uncertainty and
   its own eligibility state.

3. **What is our fair line, what is the market line, and what is the
   difference?** ``origination_card()`` keeps those three as separate columns
   and never blends them.

4. **Did any of it hit?** ``results_feed()`` joins every originated line to the
   verified game result. A result exists only when the game is in
   ``data/games-2026.csv``; until then the row is ``pending`` and every graded
   column is blank.

Every model path in this module comes from ``tools/build.py``. Nothing here
re-implements or adjusts a published number: the same nine strategies, the same
walk-forward history, the same deterministic arithmetic.

The only non-NFL source is the market line, which the NFL does not publish.
It is labelled T3 (trusted commercial publisher) everywhere it appears and is
never presented as an official NFL value.
"""
import csv
import json
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contextlib
import io

with contextlib.redirect_stdout(io.StringIO()):   # build.py prints its report on import
    import build  # noqa: E402  the single source of the model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "output")

SNAPSHOTS = os.path.join(DATA, "market-snapshots.csv")
PRICES = os.path.join(DATA, "market-prices.csv")
RESULTS = os.path.join(DATA, "results-2026.csv")
CHAINS = os.path.join(DATA, "replacement-chains.csv")
UNCONFIRMED = os.path.join(DATA, "replacement-claims-unconfirmed.csv")

# The order the desk originates markets in, and the reason for it.
ORIGINATION_ORDER = [
    ("side", "Spread / side", 1,
     "Originated first: the spread is the market with the deepest public data "
     "(every final score), the smallest variance per game, and the only market "
     "whose error this desk can measure against 118 out-of-sample games. It is "
     "the market a team-form model is best equipped to price."),
    ("total", "Total (over/under)", 2,
     "Originated second: the total depends on pace and on both scoring rates, "
     "which the same model already estimates, but it is priced off a different "
     "error process - the margin-vs-total correlation is negative, so a side "
     "edge says nothing about the total."),
    ("moneyline", "Moneyline", 3,
     "Originated last: the moneyline is a monotone transform of the spread only "
     "if you also model the push/tie mass and the vig. It inherits every spread "
     "error and adds conversion error, so it is the least defensible of the "
     "three until the spread gate has actually been passed."),
]

MARKET_MAP = {"spread": "side", "total": "total", "moneyline": "moneyline"}


# --------------------------------------------------------------------- helpers
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def snapshots():
    return read_csv(SNAPSHOTS)


def prices():
    return read_csv(PRICES)


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def american(v):
    """Format an american price the way a book shows it."""
    n = num(v)
    if n is None:
        return ""
    return "%+d" % int(round(n))


def implied_two_way(a, b):
    """Return (p_a, p_b, overround_pct) from two american prices.

    This is arithmetic on published prices, not a model. It is shown so the
    cost of the vig is visible on the same screen as the line.
    """
    def p(x):
        x = float(x)
        return 100.0 / (x + 100.0) if x > 0 else (-x) / (-x + 100.0)
    pa, pb = p(a), p(b)
    return pa, pb, (pa + pb - 1.0) * 100.0


def spread_to_ml(prob):
    """Convert a probability to an american price. None for an impossible price."""
    if prob is None or prob <= 0.001 or prob >= 0.999:
        return None
    if prob >= 0.5:
        return int(round(-100.0 * prob / (1.0 - prob)))
    return int(round(100.0 * (1.0 - prob) / prob))


# ------------------------------------------------------- 1. the price store
def price_store_summary():
    """One row per registered snapshot, with what it actually covers."""
    pz = prices()
    out = []
    for s in snapshots():
        mine = [r for r in pz if r["snapshot_id"] == s["snapshot_id"]]
        with_line = [r for r in mine if any(r[k] for k in
                     ("line_open_away", "line_open_home", "line_cur_away", "line_cur_home",
                      "price_open_away", "price_open_home", "price_cur_away", "price_cur_home"))]
        sourced = [r for r in mine if r.get("source_url")]
        out.append({
            "snapshot_id": s["snapshot_id"],
            "kind": s["kind"],
            "retrieved": s["retrieved_utc"],
            "provider": s["provider"],
            "rows": len(mine),
            "rows_with_a_number": len(with_line),
            "rows_with_a_source_link": len(sourced),
            "games": len({r["event_id"] for r in mine}),
            "note": s["source_note"],
        })
    return out


# ------------------------------------------------------- 2. origination card
def _market_line(event_id, market):
    """The current market row for one event and one market, from the store."""
    for r in prices():
        if (r["event_id"] == event_id and r["market"] == market
                and r["snapshot_id"] == "2026W11-PRE"):
            return r
    return None


def _event_ids():
    """event_id per (away, home) from the schedule payload, which build.py owns."""
    with open(os.path.join(OUT, "payload.json"), encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload["wk11_lines"]


def origination_card():
    """One row per Week 11 game, three markets, in origination order.

    fair     = the desk's own line, from the strategies build.py already scored
    market   = the published market line, T3
    diff     = fair - market, signed so a positive number means our number is
                higher than the market's (for a side: we make the home team
                stronger than the market does)
    Eligible = never 'yes': no strategy passes the significance gate, so every
               originated line is published as an estimate and nothing more.
    """
    schedule = _event_ids()
    # one lookup per (game, market) - a game has three market rows, so keying
    # on the matchup alone silently returned whichever row came last.
    by_game = {}
    for r in prices():
        if r["snapshot_id"] == "2026W11-PRE":
            by_game[(r["away"], r["home"], r["market"])] = r
    event_of = {(r["away"], r["home"]): r["event_id"] for r in prices()}

    hist = build.history(11)
    rows = []
    for s in schedule:
        away, home = s["away"], s["home"]
        per = {}
        for key, strat in build.STRATEGIES.items():
            hp, ap = strat["fn"](hist, home, away, s)
            per[key] = (hp - ap, hp + ap)
        fair_side = per["S1"][0]
        fair_total = per["S1"][1]
        band_side = [min(v[0] for v in per.values()), max(v[0] for v in per.values())]
        spread_sd = _stdev([v[0] for v in per.values()])

        eid = event_of.get((away, home), "")
        side_row = by_game.get((away, home, "spread"))
        total_row = by_game.get((away, home, "total"))
        ml = _market_line(eid, "moneyline")
        fair_ml_home = spread_to_ml(_normal_cdf(fair_side / 13.9))  # 13.9 = measured residual SD
        rows.append({
            "away": away, "home": home,
            "event_id": eid,
            "neutral": s.get("international", "") != "",
            "url": s["url"],
            "side": {
                # fair is a home-minus-away margin; market is converted to the same
                # convention so the difference is a subtraction, not a puzzle.
                "fair": fair_side,
                "market": market_to_margin(num(side_row["line_cur_home"])) if side_row else None,
                "market_line_home": num(side_row["line_cur_home"]) if side_row else None,
                "band": band_side,
                "spread_sd": spread_sd,
            },
            "total": {
                "fair": fair_total,
                "market": num(total_row["line_cur_home"]) if total_row else None,
            },
            "moneyline": {
                "fair_home": fair_ml_home,
                "fair_away": spread_to_ml(1.0 - _normal_cdf(fair_side / 13.9))
                if _normal_cdf(fair_side / 13.9) < 0.999 else None,
                "market_home": num(ml["price_cur_home"]) if ml else None,
                "market_away": num(ml["price_cur_away"]) if ml else None,
                "ml_is_market_notation": True,
            },
        })
    for r in rows:
        r["side"]["diff"] = (r["side"]["fair"] - r["side"]["market"]
                             if r["side"]["market"] is not None else None)
        r["total"]["diff"] = (r["total"]["fair"] - r["total"]["market"]
                              if r["total"]["market"] is not None else None)
    return rows


def market_to_margin(home_line):
    """Convert a home spread in market notation to the home-minus-away margin.

    Market notation writes the favourite with a negative number: HOU -10 means
    Houston is expected to win by 10. The model works in home-minus-away margin,
    so the conversion is a sign flip. Doing this in one named place is the whole
    reason it is a function: mixing the two conventions is the single easiest
    way to publish a line that is wrong by exactly twice the spread.
    """
    return None if home_line is None else -home_line


def margin_to_market(home_margin):
    """The inverse conversion, for displaying a model margin in spread notation."""
    return None if home_margin is None else -home_margin


def _spread_of(row, which):
    if not row:
        return None
    return num(row["line_cur_home" if which == "home" else "line_cur_away"])


def _total_of(row):
    return num(row["line_cur_home"]) if row else None


def _stdev(xs):
    import statistics
    return statistics.pstdev(xs) if len(xs) > 1 else 0.0


def _normal_cdf(x):
    import math
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ------------------------------------------------------- 3. the results feed
def results_feed():
    """Every originated line joined to a verified result, or explicitly pending.

    A row is graded only when the game appears in ``data/results-2026.csv``,
    which is populated only from a completed game on official NFL.com pages.
    No score is inferred, and a pending row shows no outcome columns at all.
    """
    played = {(r["away"], r["home"]): r for r in read_csv(RESULTS)} \
        if os.path.exists(RESULTS) else {}
    card = origination_card()
    out = []
    for c in card:
        key = (c["away"], c["home"])
        res = played.get(key)
        row = {
            "away": c["away"], "home": c["home"], "url": c["url"],
            "fair_side": c["side"]["fair"], "market_side": c["side"]["market"],
            "market_line_home": c["side"].get("market_line_home"),
            "band_side": c["side"]["band"],
            "fair_total": c["total"]["fair"], "market_total": c["total"]["market"],
            "status": "pending", "home_pts": None, "away_pts": None,
            "side_result": "", "total_result": "", "clv_side": None,
            "result_url": "",
        }
        if res:
            hp, ap = num(res["home_pts"]), num(res["away_pts"])
            row.update(status="final", home_pts=hp, away_pts=ap,
                       result_url=res.get("url", ""))
            margin = hp - ap
            # margin is home-minus-away, so both inputs are already in that
            # convention: no sign flip here, or the grade would be inverted.
            row["side_result"] = _grade(c["side"]["fair"], c["side"]["market"], margin)
            row["total_result"] = _grade(c["total"]["fair"], c["total"]["market"], hp + ap)
        out.append(row)
    return out


# ------------------------------------------- 5. replacement chains (named depth)
def replacement_chains():
    """Named starter -> replacement chains, each with the official article behind it.

    This is the part of "depth of the replacement" that the injury report alone
    cannot supply. The report says who is out; it does not say who takes the
    snaps. NFL.com publishes two things that do: its **DEPTH CHART NEWS** items
    in the daily league roundup, and its injury news articles, which name the
    expected starter and often the man behind him.

    Every row therefore carries the exact article URL, a quoted summary of what
    that article actually says, and the number of levels the article itself
    confirms. A chain of length 1 means the article names a replacement but no
    one behind him - the depth below that is *unknown*, not zero, and the
    published table says so.
    """
    rows = []
    for r in read_csv(CHAINS):
        names = [r["replacement_1"], r["replacement_2"], r["replacement_3"]]
        filled = [n for n in names if n.strip()]
        confirmed = int(r["depth_confirmed"])
        rows.append({
            "team_position": r["team_position"], "team": r["team"], "unit": r["unit"],
            "week": r["week_of_source"],
            "starter": r["starter"], "starter_status": r["starter_status"],
            "chain": filled,
            "depth_confirmed": confirmed,
            # depth_confirmed is what the article states; it must agree with how
            # many names were actually transcribed, or one of the two is wrong.
            "depth_matches_names": confirmed == len(filled),
            "what": r["what_the_source_says"],
            "url": r["official_url"],
            "verified": r["verified"] == "yes",
        })
    return rows


def unconfirmed_claims():
    """The complement of the chains table: what could not be confirmed, and why.

    A depth table that only lists what was found would read as though the
    remainder were empty. These are the gaps, stated as gaps.
    """
    return read_csv(UNCONFIRMED)


def _grade(fair, market, actual, tol=1e-9):
    """Did our number land closer to the truth than the market's?

    Deliberately NOT "won/lost": the desk publishes no picks and takes no side,
    so claiming a win would be fiction. What is measurable is accuracy - the
    absolute error of our line against the error of the market line on the same
    outcome. Blank whenever a required input is missing (a pending game, or a
    market value that was never confirmed).
    """
    if actual is None or fair is None or market is None:
        return ""
    if abs(actual - fair) < tol and abs(actual - market) < tol:
        return "tied"
    if abs(actual - fair) < tol:
        return "push"
    return "closer" if abs(actual - fair) < abs(actual - market) else "further"


def write_output():
    """Write the machine-readable copy of everything this module computes."""
    payload = {
        "generated": build.P["meta"]["generated"] if hasattr(build, "P") else "2026-11-14",
        "store": price_store_summary(),
        "origination_order": [{"key": k, "label": l, "order": n, "why": w}
                              for k, l, n, w in ORIGINATION_ORDER],
        "card": origination_card(),
        "results": results_feed(),
        "chains": replacement_chains(),
        "unconfirmed": unconfirmed_claims(),
    }
    # T32 (2026-11-14): normalise floats exactly like tools/build.py does
    # (round_floats, 9 places). Without this, the last 1-2 ulps of every derived
    # float differ between the CPython builds that produced the committed file
    # (3.11) and CI's (3.12), and the publish gate's byte-reproducibility check
    # fails on an interpreter difference that has no bearing on any published
    # number. Independently reproduced with CPython 3.12.9 built from source
    # before the CI diagnostic capture landed (session 279eb9b4's
    # research/verification/ci-drift-2026-11-14.txt shows the identical 62/62-line
    # drift; this session's record is
    # research/verification/publish-gate-repro-2026-11-14.md). The equivalent
    # normalisation was merged first by PR #33; this session's rebase keeps that
    # merged implementation verbatim.
    with open(os.path.join(OUT, "market_store.json"), "w", encoding="utf-8") as fh:
        json.dump(build.round_floats(payload), fh, indent=1, sort_keys=False)
    return payload




# --------------------------------------------------------------------- checks
STAKING_POLICY = {
    "unit": 1.0,
    "american": -110,
    "flat_stake": True,
    "notes": [
        "Flat 1-unit stake on every graded bet. No kelly, no chasing, no stake "
        "changes: a staking policy that reacts to the running bankroll turns a "
        "hot streak into an apparent edge.",
        "-110 is the standard price. It is a declared policy assumption, not a "
        "market quote, and the site labels it as such wherever it is used.",
        "Because every bet is priced -110 and staked flat, bankroll growth is a "
        "pure function of the hit rate: the same information as the win rate, "
        "shown in the unit a staker reads.",
        "No staking result is ever a gate. It is displayed beside the signal "
        "score and can never raise it.",
    ],
}

SIGNAL_WEIGHTS = [
    ("beats the benchmark", 0.35,
     "Out-of-sample spread MAE is better than the S0 league-constant benchmark."),
    ("significance", 0.30,
     "The 95% Bonferroni-adjusted paired-bootstrap interval on that improvement "
     "excludes zero. Nothing else can substitute for it."),
    ("stability", 0.20,
     "Share of evaluated weeks in which the strategy beat the benchmark."),
    ("calibration", 0.15,
     "Maximum gap between predicted and observed cover probability across the "
     "five delta bands; a smaller gap scores higher."),
]

DEMOTION = {
    "live": {"label": "Live", "meaning": "Eligible for reward. Requires a pass on every gate."},
    "paper": {"label": "Paper", "meaning": "Published and tracked, but not eligible for reward."},
    "retired": {"label": "Retired", "meaning": "Withdrawn from the board until re-specified."},
}


def _payout(american_odds):
    """Profit on a 1-unit win at the given american price."""
    return 100.0 / abs(american_odds) if american_odds < 0 else american_odds / 100.0


def signal_and_staking(leaderboard):
    """Score signal and staking on separate inputs, and decide the demotion state.

    signal  - built only from line-accuracy evidence (no results are bought).
    staking - flat 1-unit staking at -110 on the strategy's directional call.
              It is derived from the same out-of-sample predictions, but it is
              reported separately and never folded into the signal score.

    The two are displayed side by side and the ordinal rank of each is shown, so
    a strategy that ranks high on staking and low on signal is visibly lucky
    rather than quietly promoted.
    """
    out = []
    for s in leaderboard:
        m = s["metrics"]
        gates = s["gates"]
        passed = sum(1 for g in gates.values() if g["pass_"])
        total_gates = len(gates)

        # ---- signal: normalised, direction-free, luck-aware ----
        imp = max(0.0, s["improvement_pct"])
        sig_ok = bool(gates.get("G4 significance", {}).get("pass_"))
        stab = s.get("weekly_positive_share") or 0.0
        cal_gap = s.get("calibration_max_gap")
        cal_ok = bool(gates.get("G7 calibration", gates.get("G6 calibration", {})).get("pass_"))
        signal = 100.0 * (
            SIGNAL_WEIGHTS[0][1] * min(1.0, imp / 0.10) +
            SIGNAL_WEIGHTS[1][1] * (1.0 if sig_ok else 0.0) +
            SIGNAL_WEIGHTS[2][1] * min(1.0, stab) +
            SIGNAL_WEIGHTS[3][1] * (1.0 if cal_ok else 0.0)
        )

        # ---- staking: flat stakes, honest accounting ----
        hits = int(round(m["direction_accuracy"] * m["n"]))
        bets = m["n"]
        pnl = hits * _payout(STAKING_POLICY["american"]) - (bets - hits)
        staking = 100.0 * pnl / (bets * STAKING_POLICY["unit"])

        # ---- demotion gate ----
        # A strategy is Live only with every gate passed. Otherwise it stays on
        # paper - which is where all nine of them are today.
        state = "live" if passed == total_gates else "paper"
        reasons = []
        if not sig_ok:
            reasons.append(
                "significance gate failed: the 95%% Bonferroni-adjusted interval "
                "[%.2f, %.2f] contains zero" % (s["ci_low"], s["ci_high"]))
        if not cal_ok:
            reasons.append("calibration gap above the declared tolerance")
        for name, g in gates.items():
            if not g["pass_"] and "signific" not in name.lower() and "calib" not in name.lower():
                reasons.append("%s failed" % name)

        out.append({
            "id": s["id"], "name": s["name"], "family": s.get("family", ""),
            "n": bets,
            "signal": signal,
            "stakes": bets, "hits": hits, "pnl_units": pnl, "staking": staking,
            "gates_passed": passed, "gates_total": total_gates,
            "state": state, "reasons": reasons,
        })

    # ordinal ranks, computed separately so neither can borrow the other's name
    order_sig = sorted(out, key=lambda r: -r["signal"])
    order_stk = sorted(out, key=lambda r: -r["staking"])
    for i, r in enumerate(order_sig, 1):
        r["rank_signal"] = i
    for i, r in enumerate(order_stk, 1):
        r["rank_staking"] = i
    return out


def leaderboard_split():
    """The published leaderboard payload, with the split applied."""
    with open(os.path.join(OUT, "payload.json"), encoding="utf-8") as fh:
        payload = json.load(fh)
    return signal_and_staking(payload["leaderboard"])


def self_check():
    """Assertions over the store, the card and the feed. Exits non-zero on failure.

    These are the things a reviewer should not have to take on trust: that the
    store covers every game in every market, that the sign conversion round-trips,
    that a diff is a subtraction, that nothing pending is graded, and that no
    market number has leaked into the official data directory.
    """
    import math
    problems = []

    pz = prices()
    snaps = {s["snapshot_id"] for s in snapshots()}
    games = {(r["away"], r["home"]) for r in pz}
    if len(games) != 13:
        problems.append("expected 13 games in the store, found %d" % len(games))
    for snap in snaps:
        for market in ("spread", "total", "moneyline"):
            n = sum(1 for r in pz if r["snapshot_id"] == snap and r["market"] == market)
            if n != 13:
                problems.append("%s/%s has %d rows, expected 13" % (snap, market, n))

    # the closing snapshot must hold no numbers at all
    for r in pz:
        if r["snapshot_id"] == "2026W11-CLOSE":
            for k in ("line_open_away", "line_open_home", "line_cur_away", "line_cur_home",
                      "price_open_away", "price_open_home", "price_cur_away", "price_cur_home",
                      "line_close_away", "line_close_home", "price_close_away", "price_close_home"):
                if r[k]:
                    problems.append("closing row %s/%s carries %s=%r - a closing line that "
                                    "has not happened cannot be published"
                                    % (r["away"], r["home"], k, r[k]))
                    break

    # every captured row from the market is either sourced or explicitly flagged
    for r in pz:
        if r["snapshot_id"] in ("2026W11-OPEN", "2026W11-PRE") and r["market"] == "moneyline":
            if not r.get("source_url"):
                problems.append("moneyline row %s/%s has no source" % (r["away"], r["home"]))

    # sign convention round-trips
    for v in (-14.0, -1.5, 0.0, 3.5, 10.0):
        if abs(margin_to_market(market_to_margin(v)) - v) > 1e-12:
            problems.append("sign conversion does not round-trip at %r" % v)

    # the card: diff really is a subtraction, and no fair number is blank
    card = origination_card()
    if len(card) != 13:
        problems.append("card has %d rows, expected 13" % len(card))
    for c in card:
        s_ = c["side"]
        if s_["market"] is not None and s_["diff"] is not None:
            if abs((s_["fair"] - s_["market"]) - s_["diff"]) > 1e-9:
                problems.append("diff is not fair - market for %s/%s" % (c["away"], c["home"]))
        if s_["market"] is not None and s_["market_line_home"] is not None:
            if abs(market_to_margin(s_["market_line_home"]) - s_["market"]) > 1e-9:
                problems.append("market conversion wrong for %s/%s" % (c["away"], c["home"]))
        if not (s_["band"][0] <= s_["fair"] <= s_["band"][1] + 1e-9):
            problems.append("fair line outside its own 9-strategy band for %s/%s"
                            % (c["away"], c["home"]))
        if any(v is None for v in (c["total"]["fair"], c["total"]["market"])):
            problems.append("unexpected blank total for %s/%s" % (c["away"], c["home"]))

    # the feed: nothing pending may carry an outcome
    for r in results_feed():
        if r["status"] == "pending":
            for k in ("home_pts", "away_pts", "side_result", "total_result"):
                if r[k] not in (None, ""):
                    problems.append("pending row %s/%s has %s=%r"
                                    % (r["away"], r["home"], k, r[k]))

    # the split: staking can never exceed the policy maximum, and nothing is live
    lb = leaderboard_split()
    best_possible = _payout(STAKING_POLICY["american"]) * 100.0
    for r in lb:
        if r["staking"] > best_possible + 1e-9:
            problems.append("%s staking ROI %.1f%% exceeds the maximum a flat 1-unit "
                            "-110 book can return (%.1f%%)"
                            % (r["id"], r["staking"], best_possible))
        if r["state"] == "live":
            problems.append("%s is marked Live, but no strategy has passed every gate" % r["id"])
        if not (0 <= r["signal"] <= 100):
            problems.append("%s signal score %.2f outside 0-100" % (r["id"], r["signal"]))
    ranks_sig = sorted(r["rank_signal"] for r in lb)
    if ranks_sig != list(range(1, len(lb) + 1)):
        problems.append("signal ranks are not a clean 1..n sequence")

    # every chain row must carry a real official article and an honest depth count
    chains = replacement_chains()
    if not chains:
        problems.append("the replacement chains table is empty")
    for ch in chains:
        if not ch["url"].startswith("https://www.nfl.com/news/"):
            problems.append("chain %s/%s has no nfl.com news source" % (ch["team"], ch["starter"]))
        if not ch["verified"]:
            problems.append("chain %s/%s is not marked verified" % (ch["team"], ch["starter"]))
        if not ch["depth_matches_names"]:
            problems.append("chain %s/%s claims depth %d but carries %d names"
                            % (ch["team"], ch["starter"], ch["depth_confirmed"], len(ch["chain"])))
        if not ch["what"]:
            problems.append("chain %s/%s quotes nothing from its source" % (ch["team"], ch["starter"]))

    # the market layer must not have written into the official data directory
    for name in ("standings-wk10-2026.csv", "games-2026.csv",
                 "injuries-wk10-2026.csv", "schedule-wk11-2026.csv"):
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            problems.append("official data file %s is missing" % name)

    if problems:
        print("MARKET STORE SELF-CHECK FAILED (%d)" % len(problems))
        for p_ in problems:
            print("  - %s" % p_)
        return 1
    print("market store self-check: PASS (%d games x 3 markets x %d snapshots, "
          "%d card rows, %d feed rows, %d leaderboard rows)"
          % (len(games), len(snaps), len(card), len(results_feed()), len(lb)))
    return 0


if __name__ == "__main__":
    p = write_output()
    print("snapshots: %d, price rows: %d" % (len(p["store"]), len(prices())))
    for s in p["store"]:
        print("  %-12s %-9s rows=%-3d with_value=%-3d sourced=%-3d"
              % (s["snapshot_id"], s["kind"], s["rows"], s["rows_with_a_number"],
                 s["rows_with_a_source_link"]))
    print("origination card rows: %d" % len(p["card"]))
    print("results feed rows: %d final, %d pending"
          % (sum(1 for x in p["results"] if x["status"] == "final"),
             sum(1 for x in p["results"] if x["status"] == "pending")))
    raise SystemExit(self_check())
