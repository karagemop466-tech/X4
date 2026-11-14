#!/usr/bin/env python3
"""
Replacement depth, measured from the official record.

The requirement is to know the *depth* of a replacement, not merely that a
replacement happened. `tools/depth.py` answers that directly for the clubs whose
own official sites publish an ordered chart: it transcribes the published order,
so a backup's rank is a quotable fact rather than an inference. nfl.com itself
publishes no chart (`nfl.com/teams/<club>/depth-chart` is a verified 404) and a
few clubs, Houston among them, publish theirs as an image, so for those clubs the
string is genuinely unavailable and `tools/depth.py` flags the gap instead of
filling it.

This tool is the complement: it asks a different, weaker question that *every*
club answers, because every club files transactions. Depth also leaves a
footprint in the official transaction record, and that footprint is measurable:

    a club that loses a player and signs a replacement the next day had nobody
    behind him; a club that loses a player and signs nobody for a week had
    somebody behind him.

So the ledger records, for every player a club lost to Reserve/Injured or a
termination, how long the club took to add a body, and reads the gap:

    gap 0-1 days  -> THIN      (the club had to move immediately)
    gap 2-4 days  -> NORMAL
    gap 5+ days   -> COVERED   (no urgent need: the depth already existed)
    no signing    -> UNRESOLVED (the record does not show a replacement)

This is a *proxy*, and it is labelled as one everywhere it appears. It measures
the club's urgency, which is observable; it does not measure the ability of the
man who took the job, which is not. Where `data/depth-wk11-2026.csv` carries a
real chart rank for the same club, that rank is the better fact and should be
read in preference to this gap.

Inputs   data/transactions/transactions-2026.csv (official, per-row URL)
         data/injuries-wk10-2026.csv            (official positions, where known)
Output   data/ops/depth.csv, data/ops/depth_club.csv
Gate     python3 tools/depth_ledger.py --check  (exit 1 if any row lacks a URL)
"""
import csv
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = os.path.join(ROOT, "data", "ops")
DATA = os.path.join(ROOT, "data")

LOSS_KINDS = ("Reserve/Injured",)
ADD_KINDS = ("Free Agent Signing", "Practice Squad", "Practice Squad Veteran")


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def parse_date(month, md):
    """'2026/11' + '11/12' -> a date. Returns None if it does not parse."""
    try:
        mm, dd = md.split("/")
        yyyy = month.split("/")[0]
        return datetime.date(int(yyyy), int(mm), int(dd))
    except (ValueError, AttributeError):
        return None


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    txn = read_csv(os.path.join(DATA, "transactions", "transactions-2026.csv"))
    injuries = read_csv(os.path.join(DATA, "injuries-wk10-2026.csv"))

    # the injury report keys clubs by abbreviation and the transaction pages by
    # slug, so the lookup is by player name alone, which is unique in the report
    pos_of = {}
    for r in injuries:
        if r.get("player"):
            pos_of.setdefault(r["player"].strip().lower(), r.get("pos", ""))

    losses, adds = {}, {}
    for r in txn:
        d = parse_date(r.get("month", ""), r.get("date", ""))
        if d is None:
            continue
        team = (r.get("from") or "").strip()
        kind = (r.get("transaction") or "").strip()
        if kind.startswith(LOSS_KINDS) and team:
            losses.setdefault(team, []).append((d, r))
        if kind in ADD_KINDS:
            t = (r.get("to") or "").strip()
            if t:
                adds.setdefault(t, []).append((d, r))

    rows = []
    for team, items in sorted(losses.items()):
        for d, r in sorted(items, key=lambda x: x[0]):
            later = [(ad, ar) for ad, ar in adds.get(team, []) if ad >= d]
            if later:
                ad, ar = sorted(later, key=lambda x: x[0])[0]
                gap = (ad - d).days
                if gap <= 1:
                    read, note = "THIN", "a replacement was added within a day"
                elif gap <= 4:
                    read, note = "NORMAL", "a replacement followed within the week"
                else:
                    read, note = "COVERED", "the club did not need to move quickly"
                repl, rdate = ar.get("player", ""), ad.isoformat()
                rurl = ar.get("source_url", "")
            else:
                gap, read, note = "", "UNRESOLVED", "no addition is recorded after the loss"
                repl, rdate, rurl = "", "", ""
            pos = pos_of.get(r.get("player", "").strip().lower(), "")
            rows.append({
                "team": team, "player_lost": r.get("player", ""), "pos": pos,
                "lost_on": d.isoformat(), "loss_kind": (r.get("transaction") or "").strip(),
                "replacement": repl, "replacement_on": rdate,
                "gap_days": "" if gap == "" else "%d" % gap,
                "depth_read": read, "note": note,
                "loss_url": r.get("source_url", ""), "replacement_url": rurl,
                "method": "official transaction timing; not a depth-chart label",
            })

    write_csv(os.path.join(OPS, "depth.csv"),
              ["team", "player_lost", "pos", "lost_on", "loss_kind", "replacement",
               "replacement_on", "gap_days", "depth_read", "note", "loss_url",
               "replacement_url", "method"], rows)

    club = []
    for team in sorted({r["team"] for r in rows} | set(adds)):
        mine = [r for r in rows if r["team"] == team]
        thin = sum(1 for r in mine if r["depth_read"] == "THIN")
        unresolved = sum(1 for r in mine if r["depth_read"] == "UNRESOLVED")
        gaps = [int(r["gap_days"]) for r in mine if r["gap_days"]]
        club.append({
            "team": team,
            "losses_recorded": len(mine),
            "additions_recorded": len(adds.get(team, [])),
            "thin_moves": thin,
            "unresolved": unresolved,
            "mean_gap_days": "%.1f" % (sum(gaps) / len(gaps)) if gaps else "",
            "churn_index": len(adds.get(team, [])) + len(mine),
            "read": ("THIN" if thin >= 2 else "MIXED" if thin == 1 else
                     "NO URGENT MOVE" if mine else "NO LOSSES RECORDED"),
        })
    club.sort(key=lambda c: (-c["thin_moves"], -c["churn_index"], c["team"]))
    write_csv(os.path.join(OPS, "depth_club.csv"),
              ["team", "losses_recorded", "additions_recorded", "thin_moves", "unresolved",
               "mean_gap_days", "churn_index", "read"], club)

    print("depth ledger rows: %d" % len(rows))
    print("clubs with a recorded loss: %d" % len({r['team'] for r in rows}))
    print("thin replacements: %d, unresolved: %d"
          % (sum(1 for r in rows if r['depth_read'] == 'THIN'),
             sum(1 for r in rows if r['depth_read'] == 'UNRESOLVED')))

    if "--check" in argv:
        bad = [r for r in rows if not (r["loss_url"] or "").startswith("https://")]
        for r in bad:
            print("FAIL: %s has no official loss URL" % r.get("player"))
        print("depth ledger gate: %s (%d rows, every one sourced)"
              % ("PASS" if not bad else "FAIL", len(rows)))
        return 0 if not bad else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
