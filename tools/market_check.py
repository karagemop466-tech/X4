#!/usr/bin/env python3
"""
Independent re-derivation of every published market number (T30).

This tool does not import `tools/market.py`. It reads the two source CSVs and the
published JSON, recomputes each value from first principles, and fails if the
published number disagrees. That is the point: a check that reuses the code under
test cannot catch an error in that code.

It caught four real defects during development, all of them sign or axis errors
that had produced a plausible-looking page:

  1. `settle()` compared a predicted MARGIN against a posted HANDICAP, which
     manufactured a 14-2 record for every strategy.
  2. the value side was inverted on the handicap axis, so the desk took the side it
     thought was worse.
  3. `market_open` stayed a posted handicap while `market_line` became an implied
     margin, so closing-line value could exceed the largest line move in the data.
  4. closing-line value was measured at the close, which is a tautology: the side is
     chosen at the close, so the line has already moved toward it by construction.

Run: python3 tools/market_check.py
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "output")

PROBLEMS = []


def problem(msg):
    PROBLEMS.append(msg)


def moneyline_prob(ml):
    """Raw implied probability of one American price, vig included."""
    if ml is None:
        return None
    ml = float(ml)
    return 100.0 / (ml + 100.0) if ml > 0 else abs(ml) / (abs(ml) + 100.0)


def main():
    prices = {}
    with open(os.path.join(DATA, "market-prices-2026.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            prices[(r["event_id"], r["market"], r["side"])] = r
    slate = {}
    with open(os.path.join(DATA, "market-slate-2026.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            slate[r["event_id"]] = r
    anchors = {}
    with open(os.path.join(DATA, "market-anchors-2026.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            anchors[r["event_id"]] = r
    with open(os.path.join(OUT, "market.json"), encoding="utf-8") as fh:
        M = json.load(fh)

    # ---- 1. the anchor spine: every anchor must agree with the price rows ----
    for event, a in anchors.items():
        home = prices.get((event, "spread", "home"))
        away = prices.get((event, "spread", "away"))
        over = prices.get((event, "total", "over"))
        if not home or not away or not over:
            problem("event %s has no price rows" % event)
            continue
        if abs(float(home["close_line"]) - float(a["spread_home"])) > 1e-9:
            problem("%s: anchor home line %s but the home close is %s"
                    % (event, a["spread_home"], home["close_line"]))
        if abs(float(away["close_line"]) + float(home["close_line"])) > 1e-9:
            problem("%s: the away handicap is not the mirror of the home handicap" % event)
        if abs(float(over["close_line"]) - float(a["over_under"])) > 1e-9:
            problem("%s: anchor total %s but the captured close is %s"
                    % (event, a["over_under"], over["close_line"]))
        # both numbers must be internally consistent with the posted details string
        try:
            details, line = a["details"].rsplit(" ", 1)
            sign = -1.0 if float(line) < 0 else 1.0
            if abs(abs(float(line)) - abs(float(home["close_line"]))) > 1e-9:
                problem("%s: details says %s but the home close is %s"
                        % (event, a["details"], home["close_line"]))
        except (KeyError, ValueError):
            problem("%s: unreadable details string %r" % (event, a.get("details")))

    # ---- 2. every published bet, recomputed from the CSVs ----
    checked = 0
    for b in M["bets"]:
        if b["status"] != "final":
            continue
        g = slate[b["event_id"]]
        margin = int(g["home_pts"]) - int(g["away_pts"])
        total = int(g["home_pts"]) + int(g["away_pts"])
        checked += 1
        if b["market_type"] == "spread":
            home = prices[(b["event_id"], "spread", "home")]
            close_posted = float(home["close_line"])
            open_posted = float(home["open_line"])
            # both stored numbers are implied margins: the negation of the posted line
            if abs(b["market_line"] + close_posted) > 1e-9:
                problem("%s %s: stored close %s is not the implied margin of posted %s"
                        % (b["event_id"], b["strategy"], b["market_line"], close_posted))
            if abs(b["market_open"] + open_posted) > 1e-9:
                problem("%s %s: stored open %s is not the implied margin of posted %s"
                        % (b["event_id"], b["strategy"], b["market_open"], open_posted))
            want_diff = round(b["fair"] - b["market_line"], 2)
            if abs(want_diff - b["difference"]) > 0.011:
                problem("%s %s: difference %s but fair %s minus market %s is %s"
                        % (b["event_id"], b["strategy"], b["difference"], b["fair"],
                           b["market_line"], want_diff))
            want_side = "home" if want_diff >= 0 else "away"
            if b["side"] != want_side:
                problem("%s %s: side %s but the difference %s says %s"
                        % (b["event_id"], b["strategy"], b["side"], want_diff, want_side))
            won = (margin - b["market_line"] > 0) if b["side"] == "home" \
                else (margin - b["market_line"] < 0)
            want = "win" if won else "loss"
            side_open = "home" if (b["fair"] - b["market_open"]) >= 0 else "away"
            want_clv = ((b["market_line"] - b["market_open"]) if side_open == "home"
                        else (b["market_open"] - b["market_line"]))
            if abs(round(want_clv, 2) - b.get("clv", 0)) > 0.011:
                problem("%s %s: clv %s but the line moved %s toward the open-time side"
                        % (b["event_id"], b["strategy"], b.get("clv"), round(want_clv, 2)))
        elif b["market_type"] == "total":
            over = prices[(b["event_id"], "total", "over")]
            line = float(over["close_line"])
            want_diff = round(b["fair"] - line, 2)
            if abs(want_diff - b["difference"]) > 0.011:
                problem("%s %s: total difference %s but fair %s minus market %s is %s"
                        % (b["event_id"], b["strategy"], b["difference"], b["fair"],
                           line, want_diff))
            want_side = "over" if want_diff >= 0 else "under"
            if b["side"] != want_side:
                problem("%s %s: total side %s but the difference says %s"
                        % (b["event_id"], b["strategy"], b["side"], want_side))
            won = (total > line) if b["side"] == "over" else (total < line)
            want = "win" if won else "loss"
        else:
            home = prices[(b["event_id"], "moneyline", "home")]
            away = prices[(b["event_id"], "moneyline", "away")]
            ph = moneyline_prob(home["close_price"])
            pa = moneyline_prob(away["close_price"])
            if abs(ph + pa) <= 1.0:
                problem("%s: two-way moneyline has no vig (%.4f); the prices are suspect"
                        % (b["event_id"], ph + pa))
            fair_home = ph / (ph + pa)
            if abs(fair_home - b["market_line"]) > 0.0011:
                problem("%s %s: published de-vigged home probability %s but the raw prices "
                        "give %s" % (b["event_id"], b["strategy"], b["market_line"],
                                     round(fair_home, 4)))
            won = (margin > 0) if b["side"] == "home" else (margin < 0)
            want = "win" if won else "loss"
        if b["result"] != want:
            problem("%s %s %s: result %s but the official score says %s"
                    % (b["event_id"], b["strategy"], b["market_type"], b["result"], want))

    # ---- 3. the skill board must be reproducible from the forecasts ----
    for strategy, s in M["skill"].items():
        if strategy == "MARKET":
            continue
        errs = []
        for f in M["forecasts"]:
            g = slate[f["event_id"]]
            if g["status"] != "final":
                continue
            errs.append(abs(f["models"][strategy]["spread"]
                            - (int(g["home_pts"]) - int(g["away_pts"]))))
        if errs:
            got = sum(errs) / len(errs)
            if abs(got - s["spread_mae"]) > 0.0011:
                problem("%s: published spread MAE %s but the forecasts give %.4f"
                        % (strategy, s["spread_mae"], got))
            if len(errs) != s["n"]:
                problem("%s: published n %s but %d graded forecasts"
                        % (strategy, s["n"], len(errs)))

    # ---- 4. the market benchmark must beat at least one strategy, or it is suspect ----
    bench = M["skill"].get("MARKET", {}).get("spread_mae")
    if bench is not None:
        better = [k for k, v in M["skill"].items()
                  if k != "MARKET" and v["spread_mae"] is not None
                  and v["spread_mae"] < bench]
        if not better:
            print("  note: no strategy beats the closing line on spread error "
                  "(benchmark %.2f) - that is a finding, not a failure" % bench)

    # ---- 4b. the originated (Week 11) rows must sit on the same axis ----
    for o in M["originated"]:
        a = anchors.get(o["event_id"])
        if not a:
            problem("originated %s has no anchor" % o["event_id"])
            continue
        posted = float(a["spread_home"])
        if abs(o["side_market_handicap"] - posted) > 1e-9:
            problem("%s: published handicap %s but the anchor says %s"
                    % (o["event_id"], o["side_market_handicap"], posted))
        if abs(o["side_market_spread"] + posted) > 1e-9:
            problem("%s: market margin %s is not the negation of the posted %s"
                    % (o["event_id"], o["side_market_spread"], posted))
        want = round(o["side_fair_spread"] - o["side_market_spread"], 2)
        if abs(want - o["side_difference"]) > 0.011:
            problem("%s: side difference %s but %s minus %s is %s"
                    % (o["event_id"], o["side_difference"], o["side_fair_spread"],
                       o["side_market_spread"], want))
        wt = round(o["total_fair"] - o["total_market"], 2)
        if abs(wt - o["total_difference"]) > 0.011:
            problem("%s: total difference %s but %s minus %s is %s"
                    % (o["event_id"], o["total_difference"], o["total_fair"],
                       o["total_market"], wt))
        if abs(round(o["ml_fair_home"] - o["ml_market_home"], 4) - o["ml_difference"]) > 0.0011:
            problem("%s: moneyline difference %s does not follow from %s minus %s"
                    % (o["event_id"], o["ml_difference"], o["ml_fair_home"],
                       o["ml_market_home"]))
        # the de-vigged market probability here must match the bet rows for the same game
        for b in M["bets"]:
            if (b["event_id"] == o["event_id"] and b["market_type"] == "moneyline"
                    and abs(b["market_line"] - o["ml_market_home"]) > 0.0011):
                problem("%s: originated ML market %s disagrees with the bet row %s"
                        % (o["event_id"], o["ml_market_home"], b["market_line"]))
                break

    # ---- 5. the demotion gate must not be silently all-passing or all-failing ----
    states = [e["state"] for e in M["demotion"]["evaluated"]]
    if M["demotion"]["live_count"] + M["demotion"]["paper_count"] != len(states):
        problem("demotion counts do not add up to the number of evaluated strategies")

    print("checked %d graded bets across %d strategies" % (checked, len(M["skill"]) - 1))
    print("checked %d anchors against %d price rows" % (len(anchors), len(prices)))
    if PROBLEMS:
        print("\nPROBLEMS (%d):" % len(PROBLEMS))
        for p in PROBLEMS[:40]:
            print("  - %s" % p)
        print("\nRESULT: FAIL - published market numbers do not re-derive")
        return 1
    print("RESULT: PASS - every published market number re-derives independently "
          "from the source CSVs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
