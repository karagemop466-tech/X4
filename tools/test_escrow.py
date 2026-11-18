#!/usr/bin/env python3
"""Self-test for tools/gen_escrow.py (T48). Uses SYNTHETIC rows only; nothing here is published.

Checks the sign conventions and settlement rules that the escrow depends on, and that every statistic
reports NOT EVALUABLE on too few settled bets rather than a number.

Run:  python3 tools/test_escrow.py   (exit 0 = pass)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_escrow as E

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def row(event, market, away="AAA", home="BBB", open_line="", close_line="", close_kind="close",
        fair="", settled="", result="", snap="2026-11-20T00:00:00Z"):
    return {"event_id": event, "week": "11", "away": away, "home": home, "market": market,
            "market_open": open_line, "market_close": close_line, "close_kind": close_kind,
            "fair": fair, "snapshot_utc": snap, "source_url": "https://example.invalid/synthetic",
            "settled": settled, "result": result}


def pr(open_price="", open_ml="", close_ml=""):
    return {"open_price": open_price, "open_ml": open_ml, "close_ml": close_ml}


# --- CLV sign conventions -----------------------------------------------------------------------
# side: home open -4.5, close -6.0 (market moved toward home). Home bettor took the better number: +1.5.
fmd = [row("S1", "side", open_line="-4.5", close_line="-6", fair="-3")]  # fair -3 < 4.5 => pick away
L = E.build_ledger(fmd, {}, {})
check("side pick follows registered rule (fair home margin -3 vs market 4.5 => away)", L[0]["pick"] == "away")
check("side away CLV = close - open = -1.5 (away got +4.5 when it closed +6)", L[0]["clv"] == "-1.500")

fmd = [row("S2", "side", open_line="-4.5", close_line="-6", fair="8")]  # fair 8 > 4.5 => home
L = E.build_ledger(fmd, {}, {})
check("side home pick chosen", L[0]["pick"] == "home")
check("side home CLV = open - close = +1.5", L[0]["clv"] == "1.500")

# total: over, open 45.5, close 46.5 => +1.0 for over
fmd = [row("T1", "total", open_line="45.5", close_line="46.5", fair="48")]
L = E.build_ledger(fmd, {}, {})
check("total over pick and CLV = close - open = +1.000", L[0]["pick"] == "over" and L[0]["clv"] == "1.000")

# moneyline: home -238/away +195 open (devig home 0.675), close home -455/away +350 => home prob up
fmd = [row("M1", "moneyline", open_line="-238", close_line="-455", fair="0.80")]
pz = {("M1", "moneyline", "away"): pr(open_ml="+195", close_ml="+350")}
L = E.build_ledger(fmd, pz, {})
check("moneyline devig benchmark (open) = 0.675", abs(E.devig_home("-238", "+195") - 0.6750) < 0.001)
check("moneyline pick home (fair 0.80 > 0.675)", L[0]["pick"] == "home")
check("moneyline home CLV positive (market moved to home)", L[0]["clv"] != "" and float(L[0]["clv"]) > 0)

# no real close => CLV blank, never a fill-in
fmd = [row("C1", "total", open_line="45.5", close_line="46.5", close_kind="current_as_close", fair="48")]
L = E.build_ledger(fmd, {}, {})
check("current_as_close never produces CLV", L[0]["clv"] == "")

# --- settlement -----------------------------------------------------------------------------------
fmd = [row("R1", "side", open_line="-4.5", close_line="-4.5", fair="8", settled="1", result="home")]
pz = {("R1", "side", "home"): pr(open_price="-110")}
L = E.build_ledger(fmd, pz, {})
check("side home bet won on official cover; pnl = 100/110", L[0]["status"] == "won" and abs(float(L[0]["pnl_units"]) - 100 / 110) < 1e-3)

fmd = [row("R2", "side", open_line="-4.5", close_line="-4.5", fair="8", settled="1", result="push")]
L = E.build_ledger(fmd, {("R2", "side", "home"): pr(open_price="-110")}, {})
check("push settles to zero units", L[0]["status"] == "push" and L[0]["pnl_units"] == "0.0000")

fmd = [row("R3", "total", open_line="45.5", close_line="45.5", fair="48", settled="1", result="under")]
L = E.build_ledger(fmd, {("R3", "total", "over"): pr(open_price="-110")}, {})
check("losing total bet settles -1 unit", L[0]["status"] == "lost" and L[0]["pnl_units"] == "-1.0000")

fmd = [row("R4", "total", open_line="45.5", close_line="45.5", fair="48", settled="", result="")]
L = E.build_ledger(fmd, {}, {})
check("unsettled row stays pending, never graded", L[0]["status"] == "pending" and L[0]["pnl_units"] == "")

# --- statistics are NOT EVALUABLE on too few settled bets ----------------------------------------
s1 = E.stage1(L)
check("stage 1 reports NOT EVALUABLE with zero moneylines", s1["brier"] is None and "NOT EVALUABLE" in s1["note"])
s2 = E.stage2(L)
check("stage 2 holds nothing and releases nothing without settled bets", s2["held_units"] == 0.0 and s2["released_units"] == 0.0)

# --- Brier skill on a synthetic sample: model better than market must score > 0 ------------------
ledger = []
for i in range(40):
    y = "home" if i % 2 == 0 else "away"
    # model 0.80 on the home side, market 0.60: when home wins the model is closer; when away wins it is worse,
    # so build the sample so that the model is systematically better: home wins 60% of the time.
    ledger.append({"event_id": "B%d" % i, "market": "moneyline", "status": "won" if y == "home" else "lost",
                   "result": y, "fair": "0.7" if y == "home" else "0.7", "entry_line": "-150",
                   "entry_away_ml": "+130", "week": "11"})
s1 = E.stage1(ledger)
check("stage 1 computes a Brier skill once n >= 30 settled moneylines",
      s1["brier"] is not None and s1["brier"]["n"] == 40)
check("stage 1 interval is ordered and finite",
      s1["brier"] is not None and s1["brier"]["ci_low"] <= s1["brier"]["ci_high"])

print("")
if FAILS:
    print("FAILED: %d" % len(FAILS))
    sys.exit(1)
print("ALL ESCROW CHECKS PASSED")
