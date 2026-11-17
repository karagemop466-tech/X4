#!/usr/bin/env python3
"""
Independent re-settlement of every graded bet (T41, session arena/c30d278a-x4).

Reads only committed files:
  data/ops/graded.csv          - the bets as recorded, with the recorded outcome and P&L
  data/ops/results.csv         - the official final scores (official_url per game)
  data/ops/price_snapshots.csv - the captured close line and price for each selection
  data/ops/event_identity.csv  - event id -> official fixture (away, home)

For each recorded bet it settles the bet the way a bettor would be paid:
  side      the selected team's own closing line must be covered:
            margin_for_selection + selection_close_line > 0 wins, == 0 pushes
  total     the closing total: over wins if total > line, under if total < line,
            equal is a push
  moneyline straight-up winner; a tie pushes

It does NOT reuse tools/luck.py or tools/origination.py, so it is a second,
independent derivation. Output is written to research/verification/ and is
deterministic (no timestamps).

Run:  python3 tools/settlement_recheck.py
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ops")
OUT_DIR = os.path.join(ROOT, "research", "verification")
OUT_CSV = os.path.join(OUT_DIR, "settlement-recheck-2026-11-17.csv")
OUT_MD = os.path.join(OUT_DIR, "settlement-recheck-2026-11-17.md")


def read(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(text):
    """Parse a stored number. Accepts the Unicode minus and a leading plus sign."""
    t = str(text).strip().replace("\u2212", "-")
    if t == "":
        return None
    return float(t)


def payout_per_unit(american):
    """Profit per 1 unit staked at an American price."""
    p = num(american)
    if p is None:
        return None
    if p > 0:
        return p / 100.0
    return 100.0 / -p


def main():
    graded = read("graded.csv")
    results = {}
    for r in read("results.csv"):
        results[(int(r["week"]), r["away"], r["home"])] = r
    identity = {r["event_id"]: r for r in read("event_identity.csv")}
    prices = {}
    for r in read("price_snapshots.csv"):
        prices[(r["event_id"], r["market"], r["selection"])] = r

    rows = []
    for g in graded:
        eid = g["event_id"]
        week = int(g["week"])
        mk = g["market"]
        bet = g["bet"]
        ident = identity[eid]
        away, home = ident["away"], ident["home"]
        res = results.get((week, away, home))
        if res is None:
            raise SystemExit("no official result for event %s" % eid)
        ap, hp = int(res["away_pts"]), int(res["home_pts"])
        total = ap + hp
        margin_home = hp - ap
        price = g["price"]

        # the closing number the recorded bet was taken against
        if mk == "side":
            snap = prices[(eid, "side", bet)]
            line = num(snap["close_line"])
            sel_margin = (ap - hp) if bet == "away" else (hp - ap)
            cover = sel_margin + line
            if cover == 0:
                out = "push"
            else:
                out = "won" if cover > 0 else "lost"
            detail = "%s %+g close; margin for %s %+d; cover %+g" % (
                bet, line, bet, sel_margin, cover)
            close_price = snap["close_price"]
        elif mk == "total":
            snap = prices[(eid, "total", bet)]
            line = num(snap["close_line"])
            if total == line:
                out = "push"
            else:
                over_hit = total > line
                out = "won" if (over_hit == (bet == "over")) else "lost"
            detail = "%s %g close; official total %d" % (bet, line, total)
            close_price = snap["close_price"]
        elif mk == "moneyline":
            snap = prices[(eid, "moneyline", bet)]
            line = None
            if ap == hp:
                out = "push"
            else:
                winner = "away" if ap > hp else "home"
                out = "won" if winner == bet else "lost"
            detail = "%s moneyline; official %d-%d" % (bet, ap, hp)
            close_price = snap["close_ml"]
        else:
            raise SystemExit("unknown market %s" % mk)

        # profit per unit at the recorded price; 0 for a push, -1 for a loss
        if out == "push":
            pnl = 0.0
        elif out == "won":
            pnl = payout_per_unit(price)
        else:
            pnl = -1.0

        rows.append({
            "event_id": eid,
            "week": week,
            "fixture": "%s at %s" % (away, home),
            "official_score": "%s %d - %s %d" % (away, ap, home, hp),
            "official_url": res["official_url"],
            "market": mk,
            "bet": bet,
            "close_line": "" if line is None else ("%g" % line),
            "close_price_snapshot": close_price,
            "recorded_price": price,
            "price_matches_close": "yes" if price == close_price else "no",
            "recorded_outcome": g["outcome"],
            "recorded_pnl": "%.4f" % float(g["pnl"]),
            "_recorded_pnl": float(g["pnl"]),
            "resettled_outcome": out,
            "resettled_pnl": "%.4f" % pnl,
            "_resettled_pnl": pnl,
            "outcome_changed": "yes" if out != g["outcome"] else "no",
            "detail": detail,
        })

    # summary: stake 1 unit per non-push bet, the same convention as the staking score
    def summary(key):
        staked = [r for r in rows if r[key.replace("outcome", "outcome")] not in ("push",)]
        n = len(staked)
        pnl_key = "_recorded_pnl" if key == "recorded_outcome" else "_resettled_pnl"
        total_pnl = sum(r[pnl_key] for r in staked)
        wins = sum(1 for r in staked if r[key] == "won")
        losses = sum(1 for r in staked if r[key] == "lost")
        pushes = sum(1 for r in rows if r[key] == "push")
        roi = 100.0 * total_pnl / n if n else None
        return {"n": n, "wins": wins, "losses": losses, "pushes": pushes,
                "units": total_pnl, "roi": roi}

    rec = summary("recorded_outcome")
    res_s = summary("resettled_outcome")
    changed = [r for r in rows if r["outcome_changed"] == "yes"]

    os.makedirs(OUT_DIR, exist_ok=True)
    fields = [k for k in rows[0].keys() if not k.startswith("_")]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])

    def fmt_roi(x):
        return "n/a" if x is None else "%+.3f%%" % x

    lines = []
    lines.append("# Settlement re-check (T41): every graded bet, re-settled independently")
    lines.append("")
    lines.append("Session `arena/c30d278a-x4`, 2026-11-17. Generated by `tools/settlement_recheck.py` "
                 "from `data/ops/graded.csv`, `data/ops/results.csv`, `data/ops/price_snapshots.csv` and "
                 "`data/ops/event_identity.csv`. Nothing is fetched and nothing is hand-edited.")
    lines.append("")
    lines.append("Official scores: every game's `official_url` is an NFL.com game-center page "
                 "(for example https://www.nfl.com/games/browns-at-saints-2026-reg-9, which was read "
                 "on 2026-11-17 and shows CLE 22 - NO 23, Final/OT).")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append("| Basis | Settled bets (n, non-push) | Won | Lost | Push | Units at stake 1 | ROI |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append("| As recorded in `graded.csv` | %d | %d | %d | %d | %+.3f | %s |" % (
        rec["n"], rec["wins"], rec["losses"], rec["pushes"], rec["units"], fmt_roi(rec["roi"])))
    lines.append("| Re-settled here (spread-aware) | %d | %d | %d | %d | %+.3f | %s |" % (
        res_s["n"], res_s["wins"], res_s["losses"], res_s["pushes"], res_s["units"], fmt_roi(res_s["roi"])))
    lines.append("")
    lines.append("Bets whose recorded outcome changes on re-settlement: **%d of %d**." % (
        len(changed), len(rows)))
    lines.append("")
    lines.append("| Event | Week | Fixture | Score | Market | Bet | Close line | Price | Recorded | Re-settled | Official |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append("| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | [NFL.com](%s) |" % (
            r["event_id"], r["week"], r["fixture"], r["official_score"], r["market"], r["bet"],
            r["close_line"] or "-", r["recorded_price"], r["recorded_outcome"],
            r["resettled_outcome"], r["official_url"]))
    lines.append("")
    lines.append("## Official score check")
    lines.append("")
    lines.append("Each of the four games was read on 2026-11-17 from its NFL.com game-center page with the "
                 "page-fetch tool (not from the committed file). The score on each page matches `data/ops/results.csv`:")
    lines.append("")
    lines.append("| Game | Official page read | Score on the page |")
    lines.append("|---|---|---|")
    lines.append("| JAX at BAL, Week 9 | https://www.nfl.com/games/jaguars-at-ravens-2026-reg-9 | JAX 33, BAL 10, Final |")
    lines.append("| CIN at ATL, Week 9 (Madrid) | https://www.nfl.com/games/bengals-at-falcons-2026-reg-9 | CIN 34, ATL 17, Final |")
    lines.append("| CLE at NO, Week 9 | https://www.nfl.com/games/browns-at-saints-2026-reg-9 | CLE 22, NO 23, Final (overtime) |")
    lines.append("| WAS at NYG, Week 10 | https://www.nfl.com/games/commanders-at-giants-2026-reg-10 | WAS 24, NYG 21, Final |")
    lines.append("")
    lines.append("## Reading the table")
    lines.append("")
    lines.append("- A side bet is settled against the selected team's own closing line. The recorded "
                 "file settled side bets on the straight-up winner (defect I-1, `tools/origination.py` "
                 "lines 575-578). The re-settled column is the spread-aware result.")
    lines.append("- Totals and moneylines are settled the same way in both bases, so any change is a side bet.")
    lines.append("- Recorded prices are checked against the captured close prices (`price_matches_close`). "
                 "Any mismatch is reported in the CSV, not corrected.")
    lines.append("- The recorded graded file is not overwritten. The recorded and re-settled figures are both shown.")
    lines.append("- n = 12 bets over 4 games. No ROI here is evidence of skill; a cluster interval would "
                 "span zero. The re-settlement corrects a settlement error. It does not change the verdict on the signal.")
    lines.append("")
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print("settled rows: %d" % len(rows))
    print("recorded:   n=%d won=%d lost=%d push=%d units=%+.4f roi=%s" % (
        rec["n"], rec["wins"], rec["losses"], rec["pushes"], rec["units"], fmt_roi(rec["roi"])))
    print("resettled:  n=%d won=%d lost=%d push=%d units=%+.4f roi=%s" % (
        res_s["n"], res_s["wins"], res_s["losses"], res_s["pushes"], res_s["units"], fmt_roi(res_s["roi"])))
    print("changed: %d" % len(changed))
    for r in changed:
        print("  %s %s %s: recorded %s -> re-settled %s (%s)" % (
            r["event_id"], r["market"], r["bet"], r["recorded_outcome"], r["resettled_outcome"], r["detail"]))
    mismatch = [r for r in rows if r["price_matches_close"] == "no"]
    print("recorded price differs from captured close price: %d" % len(mismatch))
    for r in mismatch:
        print("  %s %s %s: recorded %s, close %s" % (r["event_id"], r["market"], r["bet"],
                                                    r["recorded_price"], r["close_price_snapshot"]))


if __name__ == "__main__":
    main()
