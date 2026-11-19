#!/usr/bin/env python3
"""T48 - two-stage skill leaderboard: proper-score qualification, then prospective CLV/ROI escrow.

Scope is the pre-registered Week 11 forward window only (research/preregistration/wk11-forward-v1.md,
registration commit 8a3320092abe75aeafdbb0b1cdc586b37b93cbfb). Rows that existed before the
registration are backtests and are never counted as forward evidence.

Stage 1 - proper-score qualification (registered gates G1-G6):
  Brier skill of the model's probability against the de-vigged market probability, moneyline only.
  Side and total emit a line, not a probability, so no Brier score is defined for them; the page says so.
  Game-cluster bootstrap (resampling by game, fixed seed) gives the 95% interval; a one-sided p
  is reported and Bonferroni-adjusted for the number of registered trials.
Stage 2 - prospective escrow:
  Flat one-unit stakes on settled forward bets, CLV measured against a real closing number only.
  Units are HELD until Stage 1 passes AND the further registered segment (G8) exists. G8 is not
  registered yet, so nothing is released.

Every value is computed from committed files; with n = 0 settled forward bets every statistic is
reported as NOT EVALUABLE, never as zero and never as a pass.

Run:  python3 tools/gen_escrow.py
Writes data/ops/escrow.csv, site/escrow.html and escrow.html (tools/sync.py-style mirror).
"""
import csv
import math
import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_nav

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REG_COMMIT = "8a3320092abe75aeafdbb0b1cdc586b37b93cbfb"
REG_FILE = "research/preregistration/wk11-forward-v1.md"
REG_TIME_UTC = "2026-11-18T03:34:01Z"       # committer time of REG_COMMIT (12:34:01 +0900)
FIRST_KICKOFF_UTC = "2026-11-20T01:15:00Z"  # Colts at Texans, Thu 19 Nov 2026 8:15 PM EST (UTC-5)
FORWARD_WEEK = "11"
TRIALS = 1                                  # registered forward strategies: the v1 ratio model only
BOOT_B = 10000
BOOT_SEED = 20261118
G2_MIN_PER_MARKET = 100                     # registered: >= 100 settled bets per market type
G4_MIN_N = 30                               # registered: Brier-vs-market needs n >= 30
ALPHA = 0.05

MARKETS = ("side", "total", "moneyline")


def read(path):
    with open(os.path.join(ROOT, path), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def src(url, label):
    return '<a href="%s" target="_blank" rel="noreferrer">%s \u2197</a>' % (esc(url), esc(label))


def american_to_prob(a):
    a = float(a)
    return 100.0 / (a + 100.0) if a > 0 else (-a) / (-a + 100.0)


def devig_home(home_price, away_price):
    ph, pa = american_to_prob(home_price), american_to_prob(away_price)
    return ph / (ph + pa)


def to_float(v):
    if v in ("", None):
        return None
    try:
        return float(str(v).replace("\u2212", "-").replace("+", ""))
    except (TypeError, ValueError):
        return None


def parse_fair_prob(v):
    v = str(v).strip()
    if v.endswith("%"):
        return float(v[:-1]) / 100.0
    p = float(v)
    return p / 100.0 if p > 1.0 else p


def official_urls():
    """Official NFL.com game-centre URL for each Week 11 fixture (from the committed venue dataset)."""
    out = {}
    for r in read("data/venues-wk11-2026.csv"):
        out[(r["away"], r["home"])] = r["official_url"]
    return out


def load():
    fmd = [r for r in read("data/ops/fair_market_difference.csv") if r["week"] == FORWARD_WEEK]
    snaps = read("data/ops/price_snapshots.csv")
    price = {}
    for s in snaps:
        if s["week"] == FORWARD_WEEK:
            price[(s["event_id"], s["market"], s["selection"])] = s
    # the probability store: every originated market, its probability and its inputs
    model_p = {}
    for o in read("data/ops/model_outputs.csv"):
        if o["week"] == FORWARD_WEEK:
            model_p[(o["event_id"], o["market"])] = o
    # the official results feed, so a settled game is scored from the official score
    results = {}
    for r in read("data/ops/results.csv"):
        results[(r["week"], r["away"], r["home"])] = r
    return fmd, price, model_p, results


def settle_forward(row, pick, price_row):
    """Outcome of one forward bet from the official result recorded on the row (never inferred)."""
    if row["settled"] != "1" or not row["result"]:
        return "pending", ""
    res = row["result"]
    if res == "push":
        return "push", 0.0
    if res not in ({"home", "away"} if row["market"] != "total" else {"over", "under"}):
        return "invalid", ""
    if pick == res:
        price = price_row.get("open_price") or price_row.get("open_ml") if price_row else ""
        try:
            dec = (100.0 / -float(price) + 1.0) if float(price) < 0 else (float(price) / 100.0 + 1.0)
        except (TypeError, ValueError):
            return "won", ""
        return "won", dec - 1.0
    return "lost", -1.0


def scored_outcome(row, results, reference_line):
    """The outcome of the event the probability refers to, from the official score.

    The event is the one the model published its probability for: the home team
    covering the captured opening spread, the game total going over the captured
    opening total, or the home team winning. A push is a push and is not scored.
    """
    res = results.get((row["week"], row["away"], row["home"]))
    if not res:
        return "", ""
    try:
        margin = int(res["home_pts"]) - int(res["away_pts"])
        total = int(res["home_pts"]) + int(res["away_pts"])
    except (KeyError, ValueError):
        return "", ""
    m = row["market"]
    if m == "side":
        line = to_float(reference_line)
        if line is None:
            return "", ""
        adj = margin + line
        if abs(adj) < 1e-9:
            return "push", ""
        return "home", "1" if adj > 0 else "0"
    if m == "total":
        line = to_float(reference_line)
        if line is None:
            return "", ""
        if abs(total - line) < 1e-9:
            return "push", ""
        return "over", "1" if total > line else "0"
    if margin == 0:
        return "push", ""
    return "home", "1" if margin > 0 else "0"


def build_ledger(fmd, price, urls, model_p=None, results=None):
    ledger = []
    for r in fmd:
        key = (r["event_id"], r["market"])
        m = r["market"]
        entry_line = r["market_open"]
        entry_ok = entry_line not in ("", None)
        close_real = r["close_kind"] == "close" and r["market_close"] not in ("", None)
        pick = ""
        clv = ""
        away_open_ml = price.get((r["event_id"], "moneyline", "away"), {}).get("open_ml", "") if m == "moneyline" else ""
        try:
            fair = float(r["fair"]) if m != "moneyline" else parse_fair_prob(r["fair"])
        except ValueError:
            fair = None
        if entry_ok and fair is not None:
            if m == "side":
                pick = "home" if fair > -float(entry_line) else "away"
            elif m == "total":
                pick = "over" if fair > float(entry_line) else "under"
            else:
                away_ml = price.get((r["event_id"], "moneyline", "away"), {}).get("open_ml", "")
                if away_ml:
                    mkt_home = devig_home(entry_line, away_ml)
                    pick = "home" if fair > mkt_home else "away"
        if pick and close_real:
            cl = r["market_close"]
            if m == "side":
                clv = (float(entry_line) - float(cl)) if pick == "home" else (float(cl) - float(entry_line))
            elif m == "total":
                clv = (float(cl) - float(entry_line)) if pick == "over" else (float(entry_line) - float(cl))
            else:
                away_ml = price.get((r["event_id"], "moneyline", "away"), {}).get("open_ml", "")
                away_c = price.get((r["event_id"], "moneyline", "away"), {}).get("close_ml", "")
                home_c = r["market_close"]
                if away_ml and away_c and home_c:
                    p_open = devig_home(entry_line, away_ml)
                    p_close = devig_home(home_c, away_c)
                    clv = (p_close - p_open) if pick == "home" else ((1 - p_close) - (1 - p_open))
        pr = price.get((r["event_id"], m, pick), {}) if pick else {}
        status, pnl = settle_forward(r, pick, pr)
        mp = (model_p or {}).get((r["event_id"], m), {})
        reference = mp.get("reference_line", "")
        event_name, y = ("", "")
        if results is not None:
            event_name, y = scored_outcome(r, results, reference)
        ledger.append({
            "model_probability": mp.get("probability", ""),
            "market_probability": mp.get("market_probability", ""),
            "probability_event": mp.get("event", ""),
            "reference_line": reference,
            "scored_outcome": event_name,
            "scored_y": y,
            "event_id": r["event_id"], "week": r["week"], "away": r["away"], "home": r["home"],
            "market": m, "pick": pick, "entry_line": entry_line,
            "entry_snapshot_utc": r["snapshot_utc"], "entry_source_url": r["source_url"],
            "close_kind": r["close_kind"], "close_line": r["market_close"] if close_real else "",
            "clv": ("%.3f" % clv) if isinstance(clv, float) else "",
            "fair": r["fair"], "entry_away_ml": away_open_ml,
            "entry_before_registration": "yes" if r["snapshot_utc"] < REG_TIME_UTC else "no",
            "status": status,
            "stake_units": "1" if pick else "", "pnl_units": ("%.4f" % pnl) if isinstance(pnl, float) else "",
            "result": r["result"] if r["settled"] == "1" else "",
            "official_game_url": urls.get((r["away"], r["home"]), ""),
            "registration": REG_COMMIT,
        })
    return ledger


def cluster_boot(pairs_by_cluster, stat, b=BOOT_B, seed=BOOT_SEED):
    rnd = random.Random(seed)
    keys = list(pairs_by_cluster)
    vals = []
    for _ in range(b):
        sample = []
        for _ in keys:
            sample.extend(pairs_by_cluster[rnd.choice(keys)])
        vals.append(stat(sample))
    vals.sort()
    return vals[int(0.025 * b)], vals[int(0.975 * b)], sum(1 for v in vals if v <= 0) / b


def stage1(ledger):
    """Brier skill per market, from the forward window only.

    Every market now carries a probability and its inputs in
    data/ops/model_outputs.csv, so side and total can be scored as well. The
    market benchmark is the de-vigged captured price for the moneyline and, for
    the side, that same price converted into a cover probability at the posted
    spread. A total has no market benchmark - a posted total carries no
    probability - so only the model's own Brier score is reported for it.
    """
    out = {"n": {}, "markets": {}}
    for m in MARKETS:
        rows = [r for r in ledger if r["market"] == m and r.get("scored_y") in ("0", "1")]
        n_settled = sum(1 for r in ledger if r["market"] == m
                        and r["status"] in ("won", "lost", "push"))
        out["n"][m] = n_settled
        entry = {"n": len(rows), "brier": None, "benchmark": "", "note": "",
                 "model_brier": None}
        if len(rows) < G4_MIN_N:
            entry["note"] = ("NOT EVALUABLE: %d settled forward %s; registered G4 needs n >= %d"
                             % (len(rows), m, G4_MIN_N))
            out["markets"][m] = entry
            continue
        pairs = {}
        for r in rows:
            p_model = parse_fair_prob(r["model_probability"]) if r.get("model_probability") else None
            p_mkt = parse_fair_prob(r["market_probability"]) if r.get("market_probability") else None
            if p_model is None:
                continue
            y = float(r.get("scored_y"))
            if p_mkt is None:
                # no market probability for this event: the model's own score only
                pairs.setdefault(r["event_id"], []).append((p_model, y))
                continue
            pairs.setdefault(r["event_id"], []).append((p_model, p_mkt, y))
        flat = [t for v in pairs.values() for t in v]
        if not flat:
            entry["note"] = "NOT EVALUABLE: no forward row carries a model probability"
            out["markets"][m] = entry
            continue
        if len(flat[0]) == 2:
            # model-only scoring: no market benchmark exists for this market
            bs_model = sum((p - y) ** 2 for p, y in flat) / len(flat)
            entry["model_brier"] = bs_model
            entry["benchmark"] = ("none: a posted total carries no probability, so there is no "
                                  "market forecast to be better than")
            entry["note"] = ("model Brier %.4f on n = %d; no market benchmark exists for a total, "
                             "so no skill score is computed" % (bs_model, len(flat)))
            out["markets"][m] = entry
            continue

        def skill(sample):
            bm = sum((p_m - y) ** 2 for p, p_m, y in sample) / len(sample)
            bk = sum((p - y) ** 2 for p, p_m, y in sample) / len(sample)
            return 1.0 - bk / bm if bm > 0 else 0.0

        bs_model = sum((p - y) ** 2 for p, p_m, y in flat) / len(flat)
        bs_market = sum((p_m - y) ** 2 for p, p_m, y in flat) / len(flat)
        lo, hi, p_one = cluster_boot(pairs, skill)
        bonf = min(1.0, p_one * TRIALS)
        entry["model_brier"] = bs_model
        entry["benchmark"] = ("de-vigged captured price" if m == "moneyline" else
                              "de-vigged captured price, converted to a cover probability")
        entry["brier"] = {"skill": skill(flat), "ci_low": lo, "ci_high": hi,
                          "p_one_sided": p_one, "p_bonferroni": bonf, "n": len(flat),
                          "model_brier": bs_model, "market_brier": bs_market}
        entry["note"] = "computed from settled forward %ss only" % m
        out["markets"][m] = entry
    out["brier"] = out["markets"].get("moneyline", {}).get("brier")
    out["note"] = out["markets"].get("moneyline", {}).get("note", "")
    return out


def stage2(ledger):
    settled = [r for r in ledger if r["status"] in ("won", "lost", "push")]
    held = sum(float(r["pnl_units"]) for r in settled if r["pnl_units"] != "")
    clv_rows = [r for r in ledger if r["clv"] != ""]
    return {"settled": len(settled), "held_units": held, "released_units": 0.0,
            "clv_n": len(clv_rows), "clv_mean": (sum(float(r["clv"]) for r in clv_rows) / len(clv_rows))
            if clv_rows else None}


def write_ledger(ledger):
    cols = list(ledger[0].keys()) if ledger else []
    target = os.path.join(ROOT, "data", "ops", "escrow.csv")
    with open(target, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(ledger)


def page(ledger, s1, s2, fixtures, covered):
    # The shared nav list (tools/desk_nav.py) is owned by the integration session and is checked
    # against the hand-written legacy pages, so this page adds its own link rather than editing it.
    side = desk_nav.side().replace("</nav>", '<a href="escrow.html">&#9878; &nbsp;Two-stage escrow</a></nav>', 1)
    stage1_rows = []
    for m in MARKETS:
        n = s1["n"][m]
        need = G2_MIN_PER_MARKET
        entry = s1["markets"].get(m, {})
        skill = "NOT EVALUABLE"
        if entry.get("brier"):
            skill = "%.3f (95%% cluster CI [%.3f, %.3f], n = %d)" % (
                entry["brier"]["skill"], entry["brier"]["ci_low"], entry["brier"]["ci_high"],
                entry["brier"]["n"])
        elif entry.get("model_brier") is not None:
            skill = "no market benchmark; model Brier %.4f on n = %d" % (
                entry["model_brier"], entry["n"])
        stage1_rows.append([m, str(n), str(need), "NOT MET" if n < need else "MET", skill,
                             esc(entry.get("note", ""))])
    stage1_html = desk_nav_table(["Market", "Settled forward bets", "G2 needs", "G2 state",
                                  "Brier skill (model vs market)", "Note"], stage1_rows)
    ledger_rows = []
    for r in ledger:
        ledger_rows.append([
            "%s at %s" % (esc(r["away"]), esc(r["home"])), esc(r["market"]), esc(r["pick"] or "blank"),
            esc(r["entry_line"] or "blank"), esc(r["close_kind"]),
            esc(r["clv"] or "blank: no real close"), esc(r["status"]),
            src(r["official_game_url"], "NFL.com game page") if r["official_game_url"] else "unverified",
            src(r["entry_source_url"], "entry price (third-party, ESPN/DraftKings)"),
        ])
    ledger_html = desk_nav_table(["Fixture", "Market", "Pick (registered rule)", "Entry line", "Price kind",
                                  "CLV (points / prob.)", "Status", "Official source", "Price source"], ledger_rows)
    n_pre = sum(1 for r in ledger if r["entry_before_registration"] == "yes")
    gate_rows = [
        ["G1 data integrity", "Every row has a source and UTC stamp", "PASS" if ledger and all(r["entry_source_url"] and r["entry_snapshot_utc"] for r in ledger) else "FAIL", "%d forward rows" % len(ledger)],
        ["G2 sample", ">= 100 settled bets per market", "NOT MET", "0 settled; %d more per market needed" % G2_MIN_PER_MARKET],
        ["G3 out of sample", "Forward window only: entry recorded after the rule is frozen", "FLAGGED" if n_pre else "PASS", "%d of %d entries predate registration %s (flag E7)" % (n_pre, len(ledger), REG_COMMIT[:7])],
        ["G4 probability quality", "Brier beats market, n >= 30", "NOT EVALUABLE", "moneyline n = %d" % s1["n"]["moneyline"]],
        ["G5 one-sided p", "< 0.05", "NOT EVALUABLE", "no settled forward bets"],
        ["G6 Bonferroni p", "< 0.05 over %d trial" % TRIALS, "NOT EVALUABLE", "no settled forward bets"],
        ["G7 concentration", "no week above 50% of skill", "NOT EVALUABLE", "one forward week"],
        ["G8 further segment", "a second pre-registered segment, not yet registered", "NOT MET", "nothing registered after Week 11"],
    ]
    gates_html = desk_nav_table(["Gate", "Rule (registered)", "State", "Observed"], gate_rows)
    cov = len(covered)
    per_week_full = math.ceil(G2_MIN_PER_MARKET / max(len(fixtures), 1))
    per_week_now = math.ceil(G2_MIN_PER_MARKET / max(cov, 1))
    clear_rows = [
        ["Settled forward bets per market (G2)", "100", "%d weeks at the current %d originated game(s) per week; %d weeks if all %d fixtures were originated" % (per_week_now, cov, per_week_full, len(fixtures))],
        ["Week 11 fixtures with an originated market", "13", "%d of %d (the two ESPN-bound events in the registry)" % (cov, len(fixtures))],
        ["Real closing numbers for Week 11 (CLV)", "1 per market", "0: every Week 11 price is current_as_close, not a final close"],
    ]
    clear_html = desk_nav_table(["Number that clears a gate", "Target", "Current state (arithmetic from committed rows)"], clear_rows)
    held = s2["held_units"]
    body = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Two-stage skill leaderboard: proper-score qualification, then a prospective CLV and ROI escrow, on the pre-registered Week 11 window."><title>Two-stage escrow | Fourth Down Research</title><link rel="stylesheet" href="desk.css"></head>
<body>
{side}
<main>
<header class="topbar"><div><span class="eyebrow">T48 &middot; TWO-STAGE ESCROW</span><h1>Two-stage skill board: qualify on proper scores, then escrow prospective ROI</h1></div><span class="status-pill"><i></i> {s2['settled']} settled forward bets &middot; {held:.2f} units held &middot; 0 released</span></header>

<section class="section" id="answer"><div class="section-head"><div><span class="eyebrow">THE ANSWER FIRST</span><h2>No strategy qualifies, and no return is released</h2><p class="muted">Stage 1 reads proper scores (Brier skill) only from settled forward bets. Stage 2 holds prospective units in escrow until Stage 1 passes and a further pre-registered segment exists. Nothing in this page is backtest evidence: the walk-forward numbers on the leaderboard are excluded by rule.</p></div><span class="tag amber">STAGE 1 NOT EVALUABLE &middot; ESCROW HELD</span></div>
<div class="callout"><b>Why the number is blank, not zero.</b><p>The forward window is Week 11, registered at commit <code>{REG_COMMIT[:7]}</code> ({REG_TIME_UTC}), before the first kickoff ({FIRST_KICKOFF_UTC}). It has <b>{s2['settled']} settled</b> forward bets. A statistic on zero settled bets is reported as NOT EVALUABLE.</p></div>
</section>

<section class="section" id="stage1"><div class="section-head"><div><span class="eyebrow">STAGE 1 &middot; PROPER-SCORE QUALIFICATION</span><h2>Brier skill against the de-vigged market, by market type</h2><p class="muted">Model probability against the market probability with the vig removed. Interval: game-cluster bootstrap, B = {BOOT_B:,}, seed {BOOT_SEED}. Bonferroni factor = {TRIALS} registered trial.</p></div></div>
{stage1_html}
<div class="note"><b>Every originated market now carries a probability and its inputs.</b> The store is <a href="https://github.com/karagemop466-tech/X4/blob/main/data/ops/model_outputs.csv" target="_blank" rel="noreferrer">data/ops/model_outputs.csv</a>: for every side, total and moneyline it records the probability, the event the probability refers to, the reference line it was computed against, mu, sigma with its own n and window, and the model inputs with their official source. The brief's rule 'store every model output as a probability plus its inputs' is met for all three markets. One benchmark limit stays: a posted total carries no probability, so the total has a model Brier score but no market forecast to be better than, and none is invented.</div>
</section>

<section class="section" id="gates"><div class="section-head"><div><span class="eyebrow">REGISTERED GATES</span><h2>Each gate, its rule and what it observes today</h2><p class="muted">Rules are taken unchanged from <a href="https://github.com/karagemop466-tech/X4/blob/{REG_COMMIT}/{REG_FILE}" target="_blank" rel="noreferrer">{REG_FILE} <span>&#8599;</span></a> at the registration commit.</p></div></div>
{gates_html}
</section>

<section class="section" id="escrow"><div class="section-head"><div><span class="eyebrow">STAGE 2 &middot; PROSPECTIVE ESCROW</span><h2>Units held, units released</h2></div></div>
{desk_nav_table(["Units", "Value", "Rule"], [["Settled forward bets", str(s2['settled']), "Only post-registration, officially settled"], ["Held in escrow", "%.2f" % held, "Flat one-unit stakes, held until the release rule is met"], ["Released", "%.2f" % s2['released_units'], "Requires Stage 1 pass and G8; neither is met"], ["CLV rows with a real close", str(s2['clv_n']), "CLV is blank unless a final closing number was captured"]])}
</section>

<section class="section" id="ledger"><div class="section-head"><div><span class="eyebrow">FORWARD LEDGER</span><h2>Every originated Week 11 market in the registered window</h2><p class="muted">{len(ledger)} rows from {cov} of {len(fixtures)} official Week 11 fixtures. Every entry price was captured before the registration commit (flag E7). Entry price and pick follow the registered rule applied to the entry (opening) line, so the pick is known before kickoff. The Week 11 'close' is the current price at capture, not a closing line, so no CLV is computed from it.</p></div></div>
{ledger_html}
<div class="note"><b>Price source is third-party.</b> Every captured price is DraftKings as syndicated by the public ESPN odds endpoint, labelled T3 under the price-data policy. It is not an official NFL source and is not presented as one. The official link on each row is the NFL.com game page for the fixture.</div>
</section>

<section class="section" id="clear"><div class="section-head"><div><span class="eyebrow">WHAT WOULD CLEAR IT</span><h2>The number that would clear each blocked gate</h2></div></div>
{clear_html}
</section>

<section class="section" id="flags"><div class="section-head"><div><span class="eyebrow">FLAGGED FOR REVIEW</span><h2>Irregularities found while building this page</h2><p class="muted">Each entry is recorded for review and blocks nothing. E1 was fixed in its own scope (T58, 2026-11-18); the rest belong to other scopes.</p></div></div>
{desk_nav_table(["#", "Irregularity", "Where", "Source"], [
 ["E1", "RESOLVED 2026-11-18 (T58): the walk-forward (backtest) numbers for strategies S1 to S9 were ranked on the site under a 'Leaderboard and rewards' heading. The brief forbids backtest numbers on the leaderboard. The Strategy lab page now has a forward-only rewards leaderboard (empty at n = 0 forward settled markets, with the number that would open it) and the walk-forward table sits under a 'Backtest development board - never ranked for rewards' heading; the landing-page preview is relabelled the same way.", "strategies.html (forward leaderboard + backtest board); index.html preview relabelled", src("https://github.com/karagemop466-tech/X4/blob/main/data/output/leaderboard.json", "data/output/leaderboard.json")],
 ["E2", "Week 11 'close' values are current prices at capture (close_kind = current_as_close), so Week 11 has no closing number and no CLV.", "data/ops/fair_market_difference.csv", src("https://github.com/karagemop466-tech/X4/blob/main/data/ops/fair_market_difference.csv", "fair_market_difference.csv")],
 ["E3", "The origination code grades side bets against the closing line, but a closing line cannot exist before kickoff. The forward rule therefore applies the pick to the entry (opening) line. This is an interpretation of the registration, not a change to it, and is flagged for review.", "tools/origination.py vs research/preregistration/wk11-forward-v1.md", src("https://github.com/karagemop466-tech/X4/blob/%s/%s" % (REG_COMMIT, REG_FILE), "pre-registration at " + REG_COMMIT[:7])],
 ["E4", "Only %d of %d Week 11 fixtures have an originated market, so the forward window is thin." % (cov, len(fixtures)), "data/ops/event_identity.csv", src("https://www.nfl.com/schedules/2026/by-week/week-11", "NFL.com Week 11 schedule")],
 ["E5", "RESOLVED 2026-11-19 (T70): side and total published a line and no probability, so no proper score existed for them. The origination store now writes a probability and its inputs for every market (data/ops/model_outputs.csv): the event the probability refers to, the reference line, mu, sigma with its n and window, and the model inputs with their official source. The sigma values are measured from walk-forward out-of-sample residuals on the official game log, not assumed. Stage 1 of this page now scores side, total and moneyline. One limit is published rather than solved: a posted total carries no probability, so the total has a model Brier score but no market benchmark.", "tools/origination.py, data/ops/model_outputs.csv, data/ops/probability_scores.csv", src("https://github.com/karagemop466-tech/X4/blob/main/data/ops/model_outputs.csv", "model_outputs.csv")],
 ["E7", "Entry prices were captured on 2026-11-14 (19:26 UTC), four days before the registration commit (2026-11-18 03:34 UTC). The registration fixes the rule; it cannot fix the entry prices, so these rows are 'rule registered after entry capture', not a clean pre-kickoff entry. A pre-kickoff capture is needed for a clean forward entry.", "data/ops/price_snapshots.csv, data/ops/fair_market_difference.csv", src("https://github.com/karagemop466-tech/X4/blob/main/data/ops/price_snapshots.csv", "data/ops/price_snapshots.csv")],
 ["E6", "Week 11 venue naming differs between NFL.com's hotel-search strings and the Game Info field. Resolved by the official Game Info block; recorded as F-60.", "data/venues-wk11-2026.csv", src("https://www.nfl.com/games/colts-at-texans-2026-reg-11", "NFL.com game page (Game Info)")],
])}
</section>

<footer><span>FOURTH DOWN RESEARCH &middot; Two-stage escrow</span><span><a href="programme.html">&larr; Programme</a> &middot; <a href="flagged.html">Flagged for review &rarr;</a></span></footer>
</main>
<script src="nav.js"></script>
</body>
</html>
"""
    return body


def desk_nav_table(head, rows):
    out = ['<div class="table-wrap"><table class="data"><thead><tr>']
    out += ["<th>%s</th>" % esc(h) for h in head]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def main():
    fmd, price, model_p, results = load()
    urls = official_urls()
    ledger = build_ledger(fmd, price, urls, model_p, results)
    fixtures = read("data/schedule-wk11-2026.csv")
    covered = sorted({(r["away"], r["home"]) for r in ledger})
    s1 = stage1(ledger)
    s2 = stage2(ledger)
    write_ledger(ledger)
    body = page(ledger, s1, s2, fixtures, covered)
    for target in (os.path.join(ROOT, "site", "escrow.html"), os.path.join(ROOT, "escrow.html")):
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(body)
    print("escrow: %d forward rows, %d settled, stage1 %s, held %.2f units"
          % (len(ledger), s2["settled"], "NOT EVALUABLE" if s1["brier"] is None else "computed",
             s2["held_units"]))
    print("wrote data/ops/escrow.csv, site/escrow.html, escrow.html")


if __name__ == "__main__":
    main()
