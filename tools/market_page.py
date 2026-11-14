#!/usr/bin/env python3
"""
Render `market.html` - the page for the real captured market prices (T30).

Why this is a separate tool
---------------------------
`tools/pages.py` is owned by the T21-T29 work that landed as PR #21. This tool does
not edit that file. It imports its primitives (`shell`, `section()`, `table`, `src`,
`num`, `badge`, `blank`, `esc`) read-only, builds one page, and writes it to `site/`.
The page, its nav entry and its landing-page card are added by an additive hook that
`tools/pages.py` calls if and only if this module is importable, so the T21-T29
pipeline keeps working unchanged if this file is ever removed.

What the page refuses to do
---------------------------
It does not call a model number a price. Every value in every table is either
(a) a captured price with the ESPN odds resource it came from, (b) an officially
sourced result with its NFL.com game page, or (c) explicitly labelled a model
estimate with the strategy that produced it. Where a value does not exist - a
player-prop price, an order-book depth - the cell is blank and says so.
"""
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

DATA = os.path.join(ROOT, "data", "output")
SITE = os.path.join(ROOT, "site")


def _load_pages():
    """Import tools/pages.py without running its main()."""
    spec = importlib.util.spec_from_file_location(
        "pages", os.path.join(ROOT, "tools", "pages.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_market():
    with open(os.path.join(DATA, "market.json"), encoding="utf-8") as fh:
        return json.load(fh)


def fnum(v, d=2):
    """Format a number, or a visible blank. Never invent a zero for a missing value."""
    if v is None or v == "":
        return '<span class="blank">not available</span>'
    if isinstance(v, str):
        return v
    if d == 0:
        return "%d" % round(v)
    return ("%%.%df" % d) % v


def signed(v, d=2):
    if v is None:
        return '<span class="blank">not available</span>'
    return ("%+.*f" % (d, v))


KIND = {"acc": "ok", "warn": "warn", "no": "no", "mute": "mute"}


def build(M, P):
    esc, num, src = P.esc, P.num, P.src
    badge, blank, table, wrap = P.badge, P.blank, P.table, P.wrap
    meta = M["meta"]
    R = M["results"]
    skill = M["skill"]
    staking = M["staking"]
    dem = M["demotion"]
    anchor = M["market_anchoring"]

    final = [r for r in R if r["status"] == "final"]
    graded = [b for b in M["bets"] if b["status"] == "final"]

    # ---------------------------------------------------------------- summary cards
    cards = [
        ("Captured prices", "%d" % len(M["snapshots"]), "spread, total and moneyline rows, one per game and market"),
        ("Games priced", "%d" % len({s["event_id"] for s in M["snapshots"]}), "every game on the graded slate plus the Week 11 card"),
        ("Graded games", "%d" % len(final), "official NFL.com final scores, each with its game-page link"),
        ("Graded markets", "%d" % len(graded), "spread, total and moneyline across all nine strategies"),
        ("Live strategies", "%d" % dem["live_count"], "one breach of any demotion rule sends a strategy back to paper"),
        ("Price source", "1 book", "DraftKings, published by ESPN. Non-official; see Flag F-30"),
    ]
    kpis = "".join('<article class="card"><span class="eyebrow">%s</span>'
                   '<p class="big">%s</p><p class="muted small">%s</p></article>'
                   % (esc(a), esc(b), esc(c)) for a, b, c in cards)

    # ---------------------------------------------------------------- 1. origination
    order = " &rarr; ".join({"side": "Side (spread)", "total": "Total",
                             "moneyline": "Moneyline"}[k] for k in meta["origination_order"])
    orig_rows = []
    for o in M["originated"]:
        orig_rows.append([
            esc(o["away"] + " @ " + o["home"]),
            num(o["week"]),
            "%s <span class=\"small muted\">(fair)</span><br>%s <span class=\"small muted\">"
            "(market)</span><br><b>%s</b><br><span class=\"small muted\">board: %s</span>"
            % (signed(o["side_fair_spread"], 1), signed(o["side_market_spread"], 1),
               signed(o["side_difference"], 2), signed(o["side_market_handicap"], 1)),
            "%s<br>%s<br><b>%s</b>" % (fnum(o["total_fair"], 2), fnum(o["total_market"], 1),
                                        signed(o["total_difference"], 2)),
            "%s<br>%s<br><b>%s</b>" % (fnum(o["ml_fair_home"] * 100, 1) + "%",
                                       fnum(o["ml_market_home"] * 100, 1) + "%",
                                       signed(o["ml_difference"] * 100, 1) + " pts"),
            src(o["nfl_url"], "Game") + "<br>" + src(o["price_source_url"], "Price"),
        ])
    orig = wrap("originated", table(
        [("Game", 0), ("Wk", 1), ("1. Side", 0), ("2. Total", 0), ("3. Moneyline", 0),
         ("Sources", 0)], orig_rows,
        "Origination runs in the required order: the side is priced first, then the total, "
        "then the moneyline. Each market shows the desk's <b>fair</b> number, the <b>market</b> "
        "number and the <b>difference</b> as three separate values, in that order, never "
        "blended. A spread is written as the <b>margin the home team is expected to win by</b>, "
        "so both numbers sit on one axis and the subtraction is meaningful: the market margin "
        "is the negation of the posted home handicap, and a positive difference means the desk "
        "rates home more highly than the board does, so home is the value side. The posted "
        "handicap is on the snapshot table below for anyone who wants to read the number that "
        "was actually on the board. The moneyline difference is in probability points on the "
        "de-vigged close, not on the raw price, so the bookmaker's margin is removed before the "
        "comparison. Fair numbers are model estimates, not prices."))

    # ---------------------------------------------------------------- 2. snapshot store
    snap_rows = []
    for s in sorted(M["snapshots"], key=lambda x: (x["week"], x["event_id"], x["market"])):
        if s["market"] == "spread":
            o, c = s["open_home_line"], s["close_home_line"]
            po, pc = s["open_home_price"], s["close_home_price"]
        elif s["market"] == "total":
            o, c = s.get("open_home_line"), s.get("close_home_line")
            po, pc = s["open_home_price"], s["close_home_price"]
        else:
            o = c = None
            po, pc = s["open_home_price"], s["close_home_price"]
        snap_rows.append([
            esc(s["away"] + " @ " + s["home"]),
            num(s["week"]),
            esc(s["market"]),
            fnum(o, 1) if o is not None else blank("a price, not a line"),
            fnum(c, 1) if c is not None else blank("a price, not a line"),
            fnum(s.get("movement"), 1) if s.get("movement") is not None else blank("not a line"),
            fnum(po, 0), fnum(pc, 0),
            esc("moved" if s.get("moved") else ("flat" if s.get("moved") is False else "n/a")),
            src(s["nfl_url"], "Game") + "<br>" + src(s["price_source_url"], "Price"),
        ])
    snap = wrap("snapshots", table(
        [("Game", 0), ("Wk", 1), ("Market", 0), ("Open", 1), ("Close", 1), ("Movement", 1),
         ("Open price", 1), ("Close price", 1), ("Moved", 0), ("Sources", 0)], snap_rows,
        "Every captured price, archived verbatim. A spread row is the <b>posted home handicap</b> "
        "as the book published it, not the implied margin used on the origination table above; the away "
        "handicap is its mirror and is kept in <span class=\"mono\">data/market-prices-2026.csv</span>. "
        "A total row's Open and Close columns are the over/under number; the over price and the "
        "under price are both in the CSV. A moneyline row has no line to move, so those cells say so "
        "and the movement is read from the price columns. Closing numbers exist only for games that "
        "have closed: %d of %d games here are final." % (len(final), len(R))))

    # ---------------------------------------------------------------- 3. results feed
    res_rows = []
    for r in sorted(R, key=lambda x: (x["week"], x["event_id"])):
        if r["status"] == "final":
            score = "%d-%d" % (r["away_pts"], r["home_pts"])
            margin = r["home_pts"] - r["away_pts"]
            tot = r["home_pts"] + r["away_pts"]
        else:
            score = blank("not yet played")
            margin = tot = None
        res_rows.append([
            num(r["week"]),
            esc(r["away"] + " @ " + r["home"]),
            score,
            fnum(margin, 0) if margin is not None else blank("pending"),
            fnum(tot, 0) if tot is not None else blank("pending"),
            badge("final", "ok") if r["status"] == "final" else badge("scheduled", "mute"),
            src(r["nfl_url"], "NFL.com game"),
        ])
    res = wrap("results", table(
        [("Wk", 1), ("Game", 0), ("Away-Home", 1), ("Margin", 1), ("Total", 1),
         ("Status", 0), ("Official source", 0)], res_rows,
        "The verified results feed. Every final score comes from that game's own NFL.com page, "
        "and the same scores are proved against the official standings by "
        "<span class=\"mono\">tools/verify.py</span>. Margin is home minus away and total is "
        "home plus away, both computed from the official score, not entered by hand. This is the "
        "feed that makes a backtest possible: a bet can be settled because the result it settles "
        "against is on an official page."))

    # ---------------------------------------------------------------- 4. skill board
    skill_rows = []
    for k in sorted(skill, key=lambda x: (skill[x]["skill_rank"]
                                          if skill[x]["skill_rank"] else 99)):
        s = skill[k]
        name = s.get("name") or ("The closing line" if k == "MARKET" else k)
        skill_rows.append([
            num(s["skill_rank"]) if s["skill_rank"] else blank("benchmark"),
            "<b>%s</b> <span class=\"small muted\">%s</span>" % (esc(k), esc(name)),
            num(s["n"]),
            fnum(s["spread_mae"], 2), fnum(s["total_mae"], 2),
            fnum(s["market_spread_mae"], 2),
            signed(s["beats_market_spread"], 2) if s["beats_market_spread"] is not None else blank(),
            signed(s["mean_clv"], 2) if s["mean_clv"] is not None else blank("n/a"),
            src("https://www.nfl.com/schedules/2026/by-week/week-9", "NFL.com results"),
        ])
    skill_tbl = wrap("skill-board", table(
        [("Rank", 1), ("Strategy", 0), ("n", 1), ("Spread error", 1), ("Total error", 1),
         ("Market spread error", 1), ("vs market", 1), ("Closing-line value", 1),
         ("Results source", 0)], skill_rows,
        "The skill board. Ranking uses out-of-sample error only - the model's number against "
        "the official final score - and nothing on this board can see a stake. <b>vs market</b> is "
        "how many points better than the closing line the model is; a negative value means the "
        "closing line was better than the model, which is what a market with more information "
        "should look like. <b>Closing-line value</b> is measured the only way that can come out "
        "negative: take the side the desk favoured against the <b>opening</b> number, then ask how "
        "far the market moved that side's way by the close. Measuring it against the side picked "
        "<em>at</em> the close would be a tautology, because that side is defined by the close "
        "having already moved. A lucky staking run cannot move a strategy up this table, by "
        "construction: no stake is an input."))

    # ---------------------------------------------------------------- 5. staking board
    stake_rows = []
    for k in sorted(staking, key=lambda x: (staking[x]["staking_rank"]
                                            if staking[x]["staking_rank"] else 99)):
        s = staking[k]
        if k == "MARKET":
            continue
        gap = (s["skill_rank"] - s["staking_rank"]) if (s["skill_rank"] and s["staking_rank"]) else None
        stake_rows.append([
            num(s["staking_rank"]),
            "<b>%s</b>" % esc(k),
            num(s["n"]),
            "%d-%d" % (s["wins"], s["losses"]),
            fnum(s["flat_profit"], 2), fnum(s["flat_roi"] * 100 if s["flat_roi"] is not None else None, 1),
            fnum(s["kelly_profit"], 2),
            num(s["skill_rank"]) if s["skill_rank"] else blank(),
            (badge("staking flatters", "warn") if gap and gap >= 3
             else (badge("aligned", "ok") if gap is not None and abs(gap) <= 1 else badge("skill flatters", "acc"))),
            src("https://www.nfl.com/schedules/2026/by-week/week-9", "NFL.com results"),
        ])
    stake_tbl = wrap("staking-board", table(
        [("Stake rank", 1), ("Strategy", 0), ("Bets", 1), ("W-L", 1),
         ("Flat profit", 1), ("Flat ROI %", 1), ("Kelly profit", 1), ("Skill rank", 1),
         ("Ranks", 0), ("Results source", 0)], stake_rows,
        "The staking board. Flat profit is one unit per bet; the Kelly column is a 25%% Kelly "
        "stake capped at 5%% of a 100-unit bankroll, sized from the model's own probability and "
        "never from hindsight. This table is shown <b>beside</b> the skill board, not instead of "
        "it. Where the two disagree the Ranks column says so: a strategy whose staking rank is "
        "three or more places better than its skill rank is being flattered by its results, and "
        "the demotion gate below is what decides whether it stays live. All figures are on %d "
        "graded games, so any profit number here is noise with a decimal point." % len(final)))

    # ---------------------------------------------------------------- 6. depth
    depth_rows = []
    for mkt, d in M["depth"].items():
        depth_rows.append([
            esc(mkt),
            num(d["n"]),
            num(d["moved"]),
            num(d["unmoved"]),
            fnum(d["share_unmoved"] * 100, 1) + "%",
            fnum(d["mean_abs_move"], 2) if d["mean_abs_move"] is not None else blank(),
            fnum(d["max_abs_move"], 1) if d["max_abs_move"] is not None else blank(),
            src("https://www.nfl.com/schedules/2026/by-week/week-9", "NFL.com results"),
        ])
    depth_tbl = wrap("depth", table(
        [("Market", 0), ("Games", 1), ("Moved", 1), ("Unmoved", 1), ("Share unmoved", 1),
         ("Mean move (pts)", 1), ("Largest move (pts)", 1), ("Games source", 0)], depth_rows,
        "Depth of replacement, measured against the captured open and close. <b>Share unmoved</b> "
        "is the proportion of games whose originating number was still the closing number: a high "
        "share means the opening number was deep, a low share means it had to be replaced. This is "
        "the measurement this repository can actually make from prices. It is <b>not</b> order-book "
        "depth, which requires a level-2 feed this project does not have and does not pretend to."))

    # ---------------------------------------------------------------- 7. correlations
    corr_rows = []
    for c in M["correlations"]:
        corr_rows.append([
            "<b>%s</b><br><span class=\"small muted\">%s</span>" % (esc(c["label"]), esc(c["definition"])),
            num(c["n"]),
            signed(c["r"], 4),
            "%s to %s" % (signed(c["ci95"][0], 4), signed(c["ci95"][1], 4)),
            badge("excludes zero", "ok") if (c["ci95"][0] > 0 or c["ci95"][1] < 0)
            else badge("includes zero", "warn"),
            esc(c["source"]) + " " +
            src("https://www.nfl.com/schedules/2026/by-week/week-9", "NFL.com results"),
        ])
    corr_tbl = wrap("correlations", table(
        [("Relationship", 0), ("n", 1), ("r", 1), ("95% CI", 1), ("Reading", 0),
         ("Source of the numbers", 0)], corr_rows,
        "Correlations are computed only from numbers already in this repository that were "
        "derived from official results or from captured prices, and every value is published "
        "with the <b>n</b> it was computed on and a 95%% confidence interval from a Fisher z "
        "transform. A single r with no n and no interval is not a finding, it is a rumour. Where "
        "an interval includes zero the Reading column says so, and no parlay is priced on it."))

    # ---------------------------------------------------------------- 8. demotion gate
    rules = "".join("<li>%s</li>" % esc(r) for r in dem["rules"])
    dem_rows = []
    for e in sorted(dem["evaluated"], key=lambda x: x["strategy"]):
        checks = " &middot; ".join(
            "%s %s" % (("<b>%s</b>" % esc(c["id"])) if c["pass"] is False else esc(c["id"]),
                       badge("pass", "ok") if c["pass"] else badge("breach", "no"))
            for c in e["checks"])
        dem_rows.append([
            "<b>%s</b>" % esc(e["strategy"]),
            badge(e["state"], "ok" if e["state"] == "live" else "warn"),
            checks,
            esc(", ".join(e["failed"])) if e["failed"] else "&mdash;",
            src("https://www.nfl.com/schedules/2026/by-week/week-9", "NFL.com results"),
        ])
    dem_tbl = wrap("demotion", table(
        [("Strategy", 0), ("State", 0), ("Rule checks", 0), ("Rules breached", 0),
         ("Results source", 0)], dem_rows,
        "The demotion gate, and it is numeric: every threshold is a published number, not a "
        "judgement. The default is <b>paper</b>. A strategy that is live stays live only while "
        "every rule passes, and one breach sends it back to paper at the next build. Today every "
        "strategy breaches at least two rules, which is the correct output for a model that has "
        "not shown an edge against a closing line."))

    # ---------------------------------------------------------------- 9. anchoring
    anc_rows = []
    for k, v in sorted(anchor["by_strategy"].items(), key=lambda kv: kv[1]["compression_ratio"] or 0):
        anc_rows.append([
            "<b>%s</b>" % esc(k), num(v["n"]),
            fnum(v["mean_abs_fair_handicap"], 2),
            fnum(v["mean_abs_market_handicap"], 2),
            fnum(v["compression_ratio"], 3),
            signed(v["mean_difference"], 2),
            badge("compressed", "warn") if v["compression_ratio"] is not None and v["compression_ratio"] < 0.8
            else badge("comparable", "ok"),
            src("https://www.nfl.com/schedules/2026/by-week/week-9", "NFL.com results"),
        ])
    anc_tbl = wrap("anchoring", table(
        [("Strategy", 0), ("Games", 1), ("Mean |fair|", 1), ("Mean |market|", 1),
         ("Compression", 1), ("Mean edge claimed", 1), ("Reading", 0), ("Results source", 0)], anc_rows,
        "A diagnostic, published because it is uncomfortable and because a reader can check it "
        "from the same data. <b>Compression</b> is the desk's mean absolute handicap divided by "
        "the market's: a value below 1 means the desk's number sits closer to zero than the "
        "board's, so it takes the underdog side mechanically rather than because it knows "
        "something. This is the reason a pick's win rate is not used as evidence of skill "
        "anywhere on this site. It is reported here and <b>not</b> corrected: changing a model "
        "after seeing the results would be hindsight."))

    # ---------------------------------------------------- capture reconciliation
    # The site carries two price stores (the integrity capture and this archive).
    # They were taken independently, so the only thing that keeps them honest is a
    # published reconciliation of the numbers they share.
    recon_tbl = ""
    recon_note = ""
    recon_path = os.path.join(ROOT, "data", "output", "price_reconciliation.json")
    if os.path.exists(recon_path):
        with open(recon_path, encoding="utf-8") as fh:
            RC = json.load(fh)
        recon_tbl = wrap("reconciliation", table(
            [("What was compared", 0), ("Games", 1), ("Comparisons", 1), ("Agreements", 1),
             ("Disagreements", 1), ("Source", 0)],
            [["Spread, total and moneyline: the opening line and the last posted line",
              num(RC["integrity_games"]), num(RC["comparisons"]), num(RC["matches"]),
              num(RC["mismatches"]),
              src("https://www.nfl.com/schedules/2026/by-week/week-11", "NFL.com schedule")
              + ' &middot; <a href="research/data/price_capture_reconciliation.csv" '
                'target="_blank" rel="noreferrer">row-by-row CSV &#8599;</a>'],
             ["Archive store: games priced for the backtest",
              num(RC["archive_games"]), num(RC["archive_rows"]), "-", "-",
              src("https://www.nfl.com/standings/", "NFL.com standings")]],
            "Two captures of the same book, taken independently, compared number by number. "
            "The comparison is re-derived from the two CSVs by "
            "<code>tools/reconcile_prices.py</code>, which is part of the publication gate."))
        recon_note = (
            "<b>The one difference is a naming difference, and it is flagged.</b> In this "
            "archive the word <i>close</i> means the last line the book was showing when the "
            "capture was taken, so it is filled for every game, played or not. In the "
            "integrity store on the price-snapshot page the same number is called "
            "<i>current</i>, and <i>close</i> is reserved for a game that has actually been "
            "played. The numbers agree; the words do not. See flag F-38.")

    body = """
<div class="hero">
  <span class="eyebrow light">T30 &middot; real prices, not model estimates</span>
  <h2>What the market actually said, next to what the desk said</h2>
  <p>Every number on this page is one of three things, and the page never lets them be
  confused: a <b>captured price</b> from one licensed book published by ESPN, an
  <b>official NFL.com result</b> with the game page that proves it, or a <b>model
  estimate</b> labelled with the strategy that produced it. The NFL publishes no betting
  lines, so no price here is official, and every price row carries the resource URL it was
  archived from.</p>
  <p>The uncomfortable result: on %(n_final)d graded games the desk's spread error is
  <b>worse</b> than simply taking the closing line's implied margin (best strategy
  %(best_mae).2f points against %(mkt_mae).2f), and every strategy's fair numbers are
  <b>compressed</b> toward zero relative to the board. That is published on this page rather
  than buried, because a desk that only publishes its wins is not a decision desk.</p>
</div>

<div class="grid g3">%(kpis)s</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Requirement 1 &middot; origination order</span>
  <h2>%(order)s</h2><p class="muted">%(n_orig)d games originated, each with fair, market and difference
  as three separate columns.</p></div><span class="tag">Model numbers labelled</span></div>
  %(orig)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Requirement 2 &middot; the store</span>
  <h2>Open and close, kept verbatim</h2><p class="muted">%(n_snap)d captured price rows across
  %(n_games)d games: spread, total and moneyline, opening and closing.</p></div>
  <span class="tag">DraftKings via ESPN &middot; non-official</span></div>
  %(snap)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Requirement 3 &middot; results</span>
  <h2>The feed a backtest settles against</h2><p class="muted">Every score on an official page,
  and proved against the official standings.</p></div><span class="tag acc">NFL.com</span></div>
  %(res)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Requirement 4 &middot; signal</span>
  <h2>Skill board: no stake can reach it</h2><p class="muted">Out-of-sample error against the
  official result, and against the closing line.</p></div><span class="tag">Staking-independent</span></div>
  %(skill)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Requirement 4 &middot; money</span>
  <h2>Staking board: shown beside it, never instead of it</h2><p class="muted">A lucky run must
  not be able to hide a bad signal, so the two boards are ranked separately.</p></div>
  <span class="tag warn">%(n_final)d graded games</span></div>
  %(stake)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Requirement 5 &middot; depth</span>
  <h2>How often the opening number survived to the close</h2></div></div>
  %(depth)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Requirement 6 &middot; correlations</span>
  <h2>Every coefficient with its n and its interval</h2><p class="muted">Only from numbers already
  derived from official results or captured prices.</p></div><span class="tag">Fisher z CI</span></div>
  %(corr)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Requirement 7 &middot; the gate</span>
  <h2>The demotion gate</h2><p class="muted">%(policy)s</p></div>
  <span class="tag warn">%(live)d live &middot; %(paper)d paper</span></div>
  <div class="note"><b>The four rules, in full:</b><ul>%(rules)s</ul></div>
  %(dem)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Diagnostic</span>
  <h2>Why the win rate is not published as skill</h2></div><span class="tag warn">Published, not corrected</span></div>
  %(anc)s
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Integrity</span>
  <h2>The two price captures reconciled</h2><p class="muted">This site holds two independent
  captures of the same book's prices. They are compared number by number, and the comparison is
  part of the publication gate.</p></div><span class="tag acc">Re-derived from the CSVs</span></div>
  %(recon)s
  <div class="note">%(recon_note)s</div>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">What this page does not have</span>
  <h2>Blank, and why</h2></div></div>
  <div class="grid g2">
    <article class="card"><span class="eyebrow">No prop prices</span><h3>Player props and prop combos</h3>
    <p class="muted">No official or licensed source for player-level prices was confirmed for this
    slate, so no prop price, prop line or prop correlation is published. The cells are blank rather
    than estimated. That is a gap in the data, not a finding about the players.</p></article>
    <article class="card"><span class="eyebrow">No order book</span><h3>Depth is line survival, not liquidity</h3>
    <p class="muted">Depth here is how often the opening number was still the closing number. Real
    depth - how much money a book will take at a price - needs a level-2 feed this project does not
    have and will not invent.</p></article>
    <article class="card"><span class="eyebrow">One book</span><h3>No consensus, no arbitrage claim</h3>
    <p class="muted">Prices come from a single book. Nothing here is a market consensus and nothing
    here can support a claim about arbitrage, which needs two books and both prices.</p></article>
    <article class="card"><span class="eyebrow">Small sample</span><h3>%(n_final)d games is not a sample, it is a start</h3>
    <p class="muted">Every interval on this page is wide enough to swallow zero. The page reports
    that instead of rounding it away, and the demotion gate keeps every strategy on paper until
    the interval says otherwise.</p></article>
  </div>
</section>
""" % dict(kpis=kpis, order=order, n_orig=len(M["originated"]), orig=orig,
           n_snap=len(M["snapshots"]), n_games=len({s["event_id"] for s in M["snapshots"]}),
           snap=snap, res=res, skill=skill_tbl, stake=stake_tbl, n_final=len(final),
           depth=depth_tbl, corr=corr_tbl, dem=dem_tbl, rules=rules,
           policy=esc(dem["policy"]), live=dem["live_count"], paper=dem["paper_count"],
           anc=anc_tbl, recon=recon_tbl, recon_note=recon_note,
           best_mae=min(skill[k]["spread_mae"] for k in skill if k != "MARKET"),
           mkt_mae=skill["MARKET"]["spread_mae"])
    return body


def render(pages_mod=None):
    P = pages_mod or _load_pages()
    M = load_market()
    body = build(M, P)
    # exactly the strings the pages.py hook registers, so the two entry points cannot
    # disagree about the page they write
    html = P.shell("market", "Market &amp; price archive",
                   "Captured opening and closing prices for spread, total and moneyline, "
                   "with official NFL.com results, a staking-independent skill board, a "
                   "numeric demotion gate and correlations published with n and confidence.",
                   body, "market.html")
    os.makedirs(SITE, exist_ok=True)
    out = os.path.join(SITE, "market.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


if __name__ == "__main__":
    # tools/pages.py owns page generation and registers this page through its hook.
    # Running this file directly therefore delegates, so the nav, the active marker
    # and the page body can never drift between the two entry points.
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "pages.py")], check=True)
    p = os.path.join(SITE, "market.html")
    print("wrote %s (%d bytes, via tools/pages.py)" % (p, os.path.getsize(p)))
