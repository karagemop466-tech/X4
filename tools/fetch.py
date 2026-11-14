#!/usr/bin/env python3
"""
The single network edge of this build.

Every published number in the T21 layer comes from a body cached in
``data/ops/raw/``. This file is the only writer of that directory and the only
reader of the network, which is what makes the provenance record complete: if a
value is not in a cached body, it is not published.

Commands
--------
``plan``
    Writes ``data/ops/fetch_plan.json``: every URL, why it is wanted, and the
    exact cache filename it must be stored under. No network access. Being a
    committed artifact, the plan is reviewable without running anything.

``ingest``
    Reads every cached body, records its sha256 and the UTC time it was read in
    ``data/ops/snapshots.csv``, and folds the bodies into:

      events.csv          one row per event, with ESPN ids and the pairing
      team_ids.csv         ESPN team id -> NFL abbreviation, with its evidence
      price_snapshots.csv  the price-snapshot store (open and close, per market)
      transactions.csv     official NFL transactions (replacement depth)

    Ingest never edits a cached body and never overwrites a snapshot: re-running
    it after a fresh retrieval appends the new reading and diffs it against the
    previous one, so a line movement is recorded rather than lost.

Cached bodies are produced from the URL in the plan and stored byte for byte in
``data/ops/raw/<filename>``; the retrieval time is written beside the body as
``<filename>.stamp``. A body whose sha256 no longer matches the manifest is a
detectable edit, which is the point.
"""
import csv
import datetime
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = os.path.join(ROOT, "data", "ops")
RAW = os.path.join(OPS, "raw")
TXN = os.path.join(ROOT, "data", "transactions")

CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
NFL = "https://www.nfl.com"

# Weeks we originate. Week 9 is settled, so its odds carry a final `close`; week 11
# is unplayed (its odds carry the live book). Originating both is deliberate: it
# proves the store records a real movement and a settled close, not a live guess.
EVENT_WEEKS = [9, 10, 11]

# Official NFL.com transaction pages used for replacement depth. November is the
# window in which the Week 11 unavailable list is decided; October supplies the
# reserve-list entries that predate it and are still in force.
TXN_MONTHS = ["2026/10", "2026/11"]
TXN_KINDS = ["trades", "signings", "reserve-list", "waivers", "terminations"]


def event_list_url(week):
    return "%s/seasons/2026/types/2/weeks/%d/events?limit=20" % (CORE, week)


def odds_url(event_id, book="100"):
    """One book per event. `100` is the provider id the payload itself names."""
    return "%s/events/%s/competitions/%s/odds/%s" % (CORE, event_id, event_id, book)


def nfl_week_url(week):
    return "%s/schedules/2026/by-week/week-%d" % (NFL, week)


def txn_url(month, kind):
    return "%s/transactions/league/%s/%s" % (NFL, kind, month)


def plan():
    items = []
    for wk in EVENT_WEEKS:
        items.append({"kind": "event_list", "week": wk, "url": event_list_url(wk),
                      "file": "events-week-%d.json" % wk,
                      "why": "The event ids that exist in week %d; the odds endpoint is per event" % wk})
        items.append({"kind": "nfl_results", "week": wk, "url": nfl_week_url(wk),
                      "file": "nfl-week-%d.md" % wk, "optional": True,
                      "why": "Official NFL.com results and kickoff times for week %d - the source "
                             "of record for the results feed and for the event pairing" % wk})
    for week, ids in event_ids().items():
        for ev in ids:
            items.append({"kind": "odds", "week": week, "event_id": ev, "url": odds_url(ev),
                          "file": "odds-%s.json" % ev,
                          "why": "Open, close and current prices for the spread, total and "
                                 "moneyline of this event, per book"})
    for month in TXN_MONTHS:
        for kind in TXN_KINDS:
            items.append({"kind": "nfl_transactions", "month": month, "txn": kind,
                          "url": txn_url(month, kind),
                          "file": "nfl-%s-%s.md" % (kind, month.replace("/", "-")),
                          "why": "Official record of who a club lost and when - the date a player "
                                 "was lost is what decides the depth of his replacement"})
    return items


def event_ids():
    """Event ids per week, read from the cached event-list bodies (empty if absent)."""
    out = {}
    for wk in EVENT_WEEKS:
        path = os.path.join(RAW, "events-week-%d.json" % wk)
        if not os.path.exists(path):
            continue
        doc = json.load(open(path, encoding="utf-8"))
        ids = []
        for it in doc.get("items", []):
            m = re.search(r"/events/(\d+)", it.get("$ref", ""))
            if m:
                ids.append(m.group(1))
        out[wk] = ids
    return out


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_stamp(name):
    path = os.path.join(RAW, name + ".stamp")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read().strip()
    return datetime.datetime.fromtimestamp(
        os.path.getmtime(os.path.join(RAW, name)), datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def unwrap(text):
    """A cached body may carry the markdown fence the retrieval layer adds."""
    t = text.strip()
    if t.startswith("```"):
        nl = t.find("\n")
        t = t[nl + 1:] if nl >= 0 else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def load_json(name):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        return None
    try:
        return json.loads(unwrap(open(path, encoding="utf-8").read()))
    except json.JSONDecodeError as e:
        print("  ! %s is not valid JSON (%s)" % (name, e))
        return None


def american_to_decimal(am):
    """American odds -> decimal, or empty string. No guessing: empty in, empty out."""
    if am in (None, ""):
        return ""
    s = str(am).strip().replace("\u2212", "-")
    if s.upper() in ("EVEN", "EV"):
        return "2.0000"
    try:
        a = float(s)
    except ValueError:
        return ""
    if a == 0:
        return ""
    d = 1.0 + (a / 100.0 if a > 0 else 100.0 / abs(a))
    return "%.4f" % d


def implied_pct(decimal):
    if decimal in ("", None):
        return ""
    try:
        d = float(decimal)
    except ValueError:
        return ""
    return "%.4f" % (100.0 / d) if d > 1.0 else ""


def num(x):
    """The number in an ESPN odds node, whatever shape it arrives in."""
    if isinstance(x, dict):
        v = x.get("alternateDisplayValue")
        if v in (None, ""):
            v = x.get("american")
        return "" if v is None else str(v).strip()
    return "" if x is None else str(x).strip()


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------
def ingest_odds(manifest, events, team_ids, rows):
    for wk, ids in event_ids().items():
        for ev in ids:
            name = "odds-%s.json" % ev
            path = os.path.join(RAW, name)
            if not os.path.exists(path):
                continue
            manifest.append({"file": "raw/" + name, "kind": "odds", "url": odds_url(ev),
                             "retrieved_utc": read_stamp(name), "bytes": os.path.getsize(path),
                             "sha256": sha256(path)})
            doc = load_json(name)
            if not doc:
                continue
            books = doc.get("items") if isinstance(doc, dict) and "items" in doc else [doc]
            for o in books:
                book = (o.get("provider") or {}).get("name", "")
                book_id = (o.get("provider") or {}).get("id", "")
                home_tb = o.get("homeTeamOdds") or {}
                away_tb = o.get("awayTeamOdds") or {}

                def tid(tb):
                    m = re.search(r"/teams/(\d+)", ((tb.get("team") or {}).get("$ref") or ""))
                    return m.group(1) if m else ""

                home_id, away_id = tid(home_tb), tid(away_tb)
                details = (o.get("details") or "").strip()
                fav_side = "home" if home_tb.get("favorite") else ("away" if away_tb.get("favorite") else "")
                # The favorite's name arrives inside `details` ("HOU -10"). It is the
                # only place the payload names a team, so it is the hinge of the
                # identity map. A pick'em names nobody and is recorded as unresolved.
                fav_name = re.sub(r"\s*[-+]?\d+(\.\d+)?\s*$", "", details).strip()
                if fav_name.upper() in ("EVEN", "PK", "PICK", ""):
                    fav_name = ""
                if fav_side and fav_name:
                    team_ids.setdefault(fav_side == "home" and home_id or away_id, fav_name)
                events[(ev, wk)] = {
                    "event_id": ev, "week": wk,
                    "home_espn_id": home_id, "away_espn_id": away_id,
                    "details": details, "favorite_side": fav_side,
                    "favorite_name": fav_name, "book": book, "book_id": book_id,
                }

                stamp = read_stamp(name)
                base = {"event_id": ev, "week": wk, "book": book, "book_id": book_id, "tier": "T3"}

                def add(market, selection, o_line, o_price, o_ml, c_line, c_price, c_ml, kind):
                    rows.append(dict(base, market=market, selection=selection,
                                     open_line=o_line, open_price=o_price, open_ml=o_ml,
                                     close_line=c_line, close_price=c_price, close_ml=c_ml,
                                     close_kind=kind, retrieved_utc=stamp,
                                     source_url=odds_url(ev)))

                for tb, side in ((away_tb, "away"), (home_tb, "home")):
                    op, cl = tb.get("open") or {}, tb.get("close") or {}
                    cur = tb.get("current") or {}
                    kind = "close" if cl else ("current_as_close" if cur else "")
                    c_ps = num((cl.get("pointSpread") or {})) or num((cur.get("pointSpread") or {}))
                    c_sp = num((cl.get("spread") or {})) or num((cur.get("spread") or {}))
                    c_ml = num((cl.get("moneyLine") or {})) or num((cur.get("moneyLine") or {}))
                    add("side", side,
                        num(op.get("pointSpread")), num(op.get("spread")), num(op.get("moneyLine")),
                        c_ps, c_sp, c_ml, kind)
                    add("moneyline", side, "", "", num(op.get("moneyLine")),
                        "", "", c_ml, kind)

                o_blk = o.get("open") or {}
                c_blk = o.get("close") or o.get("current") or {}
                o_tot = num(o_blk.get("total") or {})
                c_tot = num(c_blk.get("total") or {})
                for side_name in ("over", "under"):
                    add("total", side_name, o_tot, num(o_blk.get(side_name) or {}), "",
                        c_tot, num(c_blk.get(side_name) or {}), "",
                        "close" if o.get("close") else "current_as_close")


TXN_LINE = re.compile(r"^\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(\d{1,2}/\d{1,2})\s*\|\s*\[?([^|\]]+?)\]?(?:\(([^)]+)\))?\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")


def teams_in(cell):
    m = re.search(r"/teams/([a-z0-9-]+)/", cell)
    return m.group(1) if m else ""


def ingest_transactions(manifest):
    rows = []
    for month in TXN_MONTHS:
        for kind in TXN_KINDS:
            name = "nfl-%s-%s.md" % (kind, month.replace("/", "-"))
            path = os.path.join(RAW, name)
            if not os.path.exists(path):
                continue
            body = open(path, encoding="utf-8").read()
            manifest.append({"file": "raw/" + name, "kind": "nfl_transactions",
                             "url": txn_url(month, kind), "retrieved_utc": read_stamp(name),
                             "bytes": os.path.getsize(path), "sha256": sha256(path)})
            for line in unwrap(body).splitlines():
                line = line.strip()
                if not line.startswith("|") or line.startswith("| ---"):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) < 5:
                    continue
                if cells[0].lower().startswith("from"):
                    continue          # header
                date_i = next((i for i, c in enumerate(cells) if re.fullmatch(r"\d{1,2}/\d{1,2}", c)), None)
                if date_i is None:
                    continue
                frm = teams_in(cells[0]) or re.sub(r"!\[[^\]]*\]\([^)]*\)", "", cells[0])[:40]
                to = teams_in(cells[1]) if len(cells) > 1 else ""
                player_cell = cells[date_i + 1] if len(cells) > date_i + 1 else ""
                pm = re.search(r"\[([^\]]+)\]\(([^)]+)\)", player_cell)
                player = pm.group(1) if pm else re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", player_cell).strip()
                purl = pm.group(2) if pm else ""
                pos = cells[date_i + 2].strip() if len(cells) > date_i + 2 else ""
                txn = cells[date_i + 3].strip() if len(cells) > date_i + 3 else ""
                rows.append({"month": month, "txn_type": kind, "date": cells[date_i],
                             "from": frm, "to": to, "player": player, "pos": pos,
                             "transaction": txn, "player_url": purl,
                             "source_url": txn_url(month, kind),
                             "retrieved_utc": read_stamp(name)})
    return rows, manifest


def ingest_results(manifest):
    """Official NFL.com week pages: kept for audit; scores come from the proven CSV."""
    for wk in EVENT_WEEKS:
        name = "nfl-week-%d.md" % wk
        path = os.path.join(RAW, name)
        if not os.path.exists(path):
            continue
        manifest.append({"file": "raw/" + name, "kind": "nfl_results", "url": nfl_week_url(wk),
                         "retrieved_utc": read_stamp(name), "bytes": os.path.getsize(path),
                         "sha256": sha256(path)})


def write_csv(name, cols, rows):
    path = os.path.join(OPS, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def ingest():
    os.makedirs(OPS, exist_ok=True)
    manifest, events, team_ids, price_rows = [], {}, {}, []

    for wk in EVENT_WEEKS:
        name = "events-week-%d.json" % wk
        if os.path.exists(os.path.join(RAW, name)):
            manifest.append({"file": "raw/" + name, "kind": "event_list",
                             "url": event_list_url(wk), "retrieved_utc": read_stamp(name),
                             "bytes": os.path.getsize(os.path.join(RAW, name)),
                             "sha256": sha256(os.path.join(RAW, name))})
            # register every event in the week, so a missing price is a visible
            # gap rather than an event that silently does not exist
            for ev in event_ids().get(wk, []):
                events.setdefault(
                    (ev, wk),
                    {"event_id": ev, "week": wk, "away_espn_id": "", "home_espn_id": "",
                     "details": "", "favorite_side": "", "favorite_name": "",
                     "book": "", "book_id": ""})

    ingest_odds(manifest, events, team_ids, price_rows)
    txn_rows, manifest = ingest_transactions(manifest)
    ingest_results(manifest)

    # ---- the store --------------------------------------------------------
    cols = ["event_id", "week", "market", "selection", "book", "book_id", "tier",
            "open_line", "open_price", "open_ml", "close_line", "close_price", "close_ml",
            "close_kind", "retrieved_utc", "source_url"]
    # a re-ingest must never silently replace a reading: keep what is already on disk
    prev = os.path.join(OPS, "price_snapshots.csv")
    old = []
    if os.path.exists(prev):
        old = list(csv.DictReader(open(prev, newline="", encoding="utf-8")))
    merged, seen = [], set()
    for r in price_rows:
        key = (r["event_id"], r["market"], r["selection"], r["book"], r["retrieved_utc"])
        if key in seen:
            continue
        seen.add(key)
        # append-only: an earlier reading of the same key is kept, the new one added
        merged.append(r)
    for r in old:
        key = (r["event_id"], r["market"], r["selection"], r["book"], r["retrieved_utc"])
        if key not in seen:
            merged.append(r)
            seen.add(key)
    merged.sort(key=lambda r: (int(r["week"] or 0), r["event_id"], r["market"], r["selection"],
                               r["retrieved_utc"]))
    write_csv("price_snapshots.csv", cols, merged)

    write_csv("events.csv",
              ["event_id", "week", "away_espn_id", "home_espn_id", "favorite_side",
               "favorite_name", "details", "book", "priced"],
              sorted((dict(e, priced="1" if e["favorite_name"] else "0")
                      for e in events.values()), key=lambda e: (e["week"], e["event_id"])))
    write_csv("team_ids.csv", ["espn_id", "nfl_abbr", "evidence"],
              [{"espn_id": k, "nfl_abbr": v,
                "evidence": "favorite named in ESPN `details` on an event where this id is on "
                            "the favorite's side"} for k, v in sorted(team_ids.items(), key=lambda x: int(x[0]))])
    write_csv("snapshots.csv", ["file", "kind", "url", "retrieved_utc", "bytes", "sha256"], manifest)

    if txn_rows:
        os.makedirs(TXN, exist_ok=True)
        path = os.path.join(TXN, "transactions-2026.csv")
        prev_rows = []
        if os.path.exists(path):
            prev_rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
        keys = {(r["month"], r["txn_type"], r["date"], r["from"], r["player"], r["transaction"])
                for r in txn_rows}
        for r in prev_rows:
            k = (r["month"], r["txn_type"], r["date"], r["from"], r["player"], r["transaction"])
            if k not in keys:
                txn_rows.append(r)
                keys.add(k)
        write_csv(os.path.join("..", "..", "data", "transactions", "transactions-2026.csv"),
                  ["month", "txn_type", "date", "from", "to", "player", "pos", "transaction",
                   "player_url", "source_url", "retrieved_utc"],
                  sorted(txn_rows, key=lambda r: (r["month"], r["date"], r["player"])))

    print("events: %d" % len(events))
    print("price-snapshot rows: %d (%d new this run)" % (len(merged), len(price_rows)))
    print("team ids resolved: %d / 32" % len(team_ids))
    print("official transactions: %d" % len(txn_rows))
    print("cached bodies in the manifest: %d" % len(manifest))
    unresolved = sorted({e["event_id"] for e in events.values() if not e["favorite_name"]})
    if unresolved:
        print("events with no favourite named (pick'em or missing odds): %s" % ", ".join(unresolved))
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("plan", "ingest"):
        print(__doc__)
        return 2
    if argv[1] == "plan":
        items = plan()
        os.makedirs(OPS, exist_ok=True)
        doc = {"generated_utc": utc_now(), "count": len(items), "items": items}
        path = os.path.join(OPS, "fetch_plan.json")
        # T32 (2026-11-14): leave the file untouched when the plan items have
        # not changed. The generated_utc stamp alone used to be rewritten on
        # every run, which dirtied the working tree after every full gate run
        # (validate.py executes this step) and invited a timestamp-only commit.
        # The plan's *content* is the deliverable; a fresh stamp is written only
        # when the content actually changes.
        try:
            with open(path, "r", encoding="utf-8") as fh:
                existing = json.load(fh)
            same = (isinstance(existing, dict) and existing.get("count") == len(items)
                    and existing.get("items") == items)
        except (OSError, ValueError):
            same = False
        if same:
            print("%d URLs planned -> data/ops/fetch_plan.json (unchanged, not rewritten)"
                  % len(items))
            return 0
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        print("%d URLs planned -> data/ops/fetch_plan.json" % len(items))
        return 0
    return ingest()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
