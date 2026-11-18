#!/usr/bin/env python3
"""
T48 - the paired sign test on the walk-forward corpus, recomputed and gated.

WHY THIS EXISTS
---------------
Three published documents quoted a paired sign test as
"68 of 105 games (64.8%), exact binomial p = 0.0016". The corpus has since grown
to 118 evaluated games (Weeks 3-10, 150 completed games through Week 10), so
those three numbers describe a corpus that no longer exists. The finding the
sentence supports -- "the bootstrap interval spans zero while the paired sign
test does not" -- is a live question (S-15) that the owner must decide, so the
numbers attached to it must be regenerated, never retyped.

This tool recomputes the sign test from tools/build.py's own walk-forward
predictions (it imports build, so it cannot drift from the model), writes the
result to data/output/sign_test.json, and refuses to publish a number it cannot
re-derive.

WHY A SIGN TEST AT ALL
----------------------
MAE is dominated by a handful of blowouts where no model does well. A paired
sign test asks a different, sharper question: in how many games does strategy S
land closer to the truth than the league-constant benchmark S0? It ignores
magnitude by construction, so it is immune to the blowout dominance -- and it is
also insensitive to how much closer S was, which is why it is published BESIDE
the bootstrap interval and never instead of it.

HONEST LIMITS
-------------
* Both statistics are computed on the same games, so they are not independent
  evidence. Publishing both is the point; deciding which one governs is the
  owner's call and remains open as S-15.
* The tails are exact (binomial), the multiplicity is handled by the same
  Bonferroni threshold build.py uses (alpha / number of strategies).

Usage:
  python3 tools/sign_test.py           # recompute + write data/output/sign_test.json
  python3 tools/sign_test.py --check   # fail if the committed JSON is stale
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
OUT = os.path.join(ROOT, "data", "output", "sign_test.json")


def binom_sf(k, n, p=0.5):
    """Exact one-sided P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def compute():
    import build  # importing runs the walk-forward evaluation
    baseline = "S0"
    base = [abs(x["spread_err"]) for x in build.preds[baseline]]
    n = len(base)
    alpha = build.PARAMS["alpha"]
    n_strat = len(build.STRATEGIES)
    bonf = alpha / n_strat
    out = {
        "note": ("Paired sign test: games in which the strategy's spread lands closer to the "
                 "actual result than the league-constant benchmark S0. Exact one-sided "
                 "binomial test on wins out of n. Published beside, never instead of, the "
                 "bootstrap MAE interval."),
        "eval_first_week": build.PARAMS["eval_first_week"],
        "n": n,
        "baseline": baseline,
        "bonferroni_alpha": bonf,
        "strategies": {},
    }
    for key in build.STRATEGIES:
        if key == baseline:
            continue
        err = [abs(x["spread_err"]) for x in build.preds[key]]
        wins = sum(1 for a, b in zip(err, base) if a < b)
        ties = sum(1 for a, b in zip(err, base) if a == b)
        losses = n - wins - ties
        p = binom_sf(wins, n)
        out["strategies"][key] = {
            "name": build.STRATEGIES[key]["name"],
            "wins": wins, "losses": losses, "ties": ties,
            "share": round(wins / n, 6),
            "p_one_sided": round(p, 8),
            "clears_bonferroni": p < bonf,
        }
    return out


def check(out):
    if not os.path.exists(OUT):
        print("FAIL: %s is missing" % os.path.relpath(OUT, ROOT))
        return 1
    old = json.load(open(OUT, encoding="utf-8"))
    if old != out:
        print("FAIL: committed sign_test.json does not match a fresh computation")
        for k, v in out["strategies"].items():
            o = old.get("strategies", {}).get(k, {})
            if o != v:
                print("  %s: committed %r != built %r" % (k, o, v))
        return 1
    best = max(out["strategies"].items(), key=lambda kv: kv[1]["wins"])
    print("sign test: PASS (n=%d, best %s %d/%d p=%.3g, Bonferroni %.5f)"
          % (out["n"], best[0], best[1]["wins"], out["n"], best[1]["p_one_sided"],
             out["bonferroni_alpha"]))
    return 0


def main():
    out = compute()
    if "--check" in sys.argv:
        return check(out)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s" % os.path.relpath(OUT, ROOT))
    print("n = %d evaluated games (weeks %d onward)"
          % (out["n"], out["eval_first_week"]))
    print("%-4s %-34s %6s %6s %6s %6s %10s %s"
          % ("id", "strategy", "wins", "loss", "ties", "share", "p", "clears"))
    for k, v in sorted(out["strategies"].items(), key=lambda kv: -kv[1]["wins"]):
        print("%-4s %-34s %6d %6d %6d %5.1f%% %10.3g %s"
              % (k, v["name"][:34], v["wins"], v["losses"], v["ties"],
                 v["share"] * 100, v["p_one_sided"],
                 "yes" if v["clears_bonferroni"] else "no"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
