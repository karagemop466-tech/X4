#!/usr/bin/env python3
"""T33 — independent live re-verification sweep (session arena/e6ee28a8-x4, 2026-11-14).

Parses the committed live captures of the official NFL.com pages
(`research/verification/captures-2026-11-14-e6ee28a8/*.md`, transcribed verbatim
from Arena fetch_page output) into rows, then diffs them field by field against
the committed CSVs in `data/`. Writes three snapshot CSVs (each row carrying its
source URL and retrieval date) and prints a full mismatch list.

Design rules carried over from T20's harness:
  - the sweep diffs, it never edits. Any drift is reported, not "fixed".
  - team-label mapping LA->LAR / AZ->ARI applies to the key only (F-14);
  - practice-status abbreviations map 1:1 (Full Participation in Practice ->
    Full, Did Not Participate In Practice -> DNP, Limited Participation in
    Practice -> Limited);
  - a parse problem fails loudly rather than silently dropping a row.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CAPS = os.path.join(HERE, "captures-2026-11-14-e6ee28a8")
RETRIEVED = "2026-11-14"
SRC_STANDINGS = "https://www.nfl.com/standings/"
SRC_SCHEDULE = "https://www.nfl.com/schedules/2026/by-week/week-11"
SRC_INJURIES = "https://www.nfl.com/injuries/"

TEAM_MAP = {"LA": "LAR", "AZ": "ARI"}  # NFL.com label -> dataset label (F-14)


def read_text(name):
    with open(os.path.join(CAPS, name), encoding="utf-8") as fh:
        return fh.read()


# ----------------------------------------------------------------- standings
def parse_standings():
    rows = []
    for m in re.finditer(r"\|\s*\[([A-Za-z .'\d]+)\]\(https://www\.nfl\.com/teams/[^)]+\)\s*"
                         r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|"
                         r"\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(-?\d+)\s*\|", read_text("standings.md")):
        rows.append(dict(team=m.group(1),
                         w=m.group(2), l=m.group(3), t=m.group(4), pct=m.group(5),
                         pf=m.group(6), pa=m.group(7), net_pts=m.group(8)))
    return rows


# ----------------------------------------------------------------- schedule
GAME_RE = re.compile(
    r"- (?:Mexico City: )?([A-Za-z\d][A-Za-z.&'\d ]+?) at ([A-Za-z\d][A-Za-z.&'\d ]+?), "
    r"(?:Thursday|Sunday|Monday)(?: Night Football)?, November (\d+).., "
    r"([\d:]+ [AP]M), ([A-Z][A-Z ,]+?) — (https://www\.nfl\.com/games/[a-z0-9-]+)")


def parse_schedule(name_to_abbr):
    text = read_text("schedule-wk11.md")
    rows = []
    for m in GAME_RE.finditer(text):
        away = name_to_abbr[m.group(1).strip()]
        home = name_to_abbr[m.group(2).strip()]
        net = m.group(5).strip()
        net = "PRIME" if net == "PRIME" else net.split(",")[0].strip()
        intl = "Mexico City" if "Mexico City" in m.group(0) else ""
        rows.append(dict(away=away, home=home, date="2026-11-%02d" % int(m.group(3)),
                         time_et=m.group(4), network=net, nfl_url=m.group(6),
                         international=intl))
    return rows


def parse_byes():
    text = read_text("schedule-wk11.md")
    m = re.search(r"Teams on Bye \(6\): (.+)$", text, re.M)
    names = re.findall(r"([A-Za-z\d][A-Za-z ]*?)(?=\s*\(|,|$)", m.group(1))
    return [n.strip() for n in names if n.strip()]


# ----------------------------------------------------------------- injuries
PRACTICE_MAP = {
    "Full Participation in Practice": "Full",
    "Did Not Participate In Practice": "DNP",
    "Limited Participation in Practice": "Limited",
}


def parse_injuries():
    rows = []
    team = None
    for line in read_text("injuries-wk10.md").splitlines():
        m = re.match(r"### [A-Za-z0-9'.& ]+ \(([A-Z]{2,3})\)\s*$", line)
        if m:
            team = m.group(1)
            continue
        m = re.match(r"\| (.+?) \| ([A-Z]{1,2}(?: [IVX]+)?) \| (.*?) \| (.*?) \| (.*?) \| (https://www\.nfl\.com/players/[a-z0-9-]+/?)\s*$",
                     line)
        if m and team:
            name, pos, inj, prac, game, url = m.groups()
            team = TEAM_MAP.get(team, team)  # the page labels LA/AZ; the dataset uses LAR/ARI (F-14)
            prac_s = prac.strip()
            if prac_s and prac_s not in PRACTICE_MAP:
                raise SystemExit("fail-loud: unrecognised practice status %r" % prac_s)
            rows.append(dict(team=team, player=name.strip(), pos=pos.strip(),
                             injuries=inj.strip(), practice=PRACTICE_MAP.get(prac_s, prac_s),
                             game_status=game.strip(), player_url=url))
    return rows


# ----------------------------------------------------------------- diffing
def diff_table(label, live, committed_keys, committed, fields, out_name, src_url):
    mismatches, missing = [], []
    for key in committed_keys:
        lv = live.get(key)
        cv = committed.get(key)
        if lv is None:
            missing.append(key)
            continue
        for f in fields:
            if lv[f] != cv[f]:
                mismatches.append((key, f, cv[f], lv[f]))
    with open(os.path.join(HERE, out_name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "source", "retrieved"] + list(fields))
        for key in committed_keys:
            lv = live.get(key)
            if lv is None:
                continue
            w.writerow([key if isinstance(key, str) else " ".join(key), src_url,
                        RETRIEVED] + [lv[f] for f in fields])
    print("\n=== %s ===" % label)
    print("  rows compared: %d of %d committed; missing from capture: %d"
          % (len(committed_keys) - len(missing), len(committed_keys), len(missing)))
    if missing:
        for k in missing[:10]:
            print("    - not in capture: %s" % (k,))
    if mismatches:
        for k, f, c, l in mismatches:
            print("    - MISMATCH %s field %s: committed=%r live=%r" % (k, f, c, l))
    else:
        print("  RESULT: PASS - every captured field matches the committed data.")
    return mismatches, missing


def main():
    problems = []

    # standings
    live = parse_standings()
    if len(live) != 32:
        raise SystemExit("fail-loud: expected 32 standings rows, parsed %d" % len(live))
    committed = list(csv.DictReader(open(os.path.join(ROOT, "data", "standings-wk10-2026.csv"))))
    name_to_abbr = {r["team"]: TEAM_MAP.get(r["abbr"], r["abbr"]) for r in committed}
    live_m = {r["team"]: r for r in live}
    ck = [r["abbr"] for r in committed]
    cd = {r["abbr"]: r for r in committed}
    live_by_abbr = {}
    for name, row in live_m.items():
        live_by_abbr[name_to_abbr[name]] = dict(row)
    m1, _ = diff_table("official NFL.com standings (live %s) vs data/standings-wk10-2026.csv" % RETRIEVED,
                       live_by_abbr, ck, cd, ["w", "l", "t", "pct", "pf", "pa", "net_pts"],
                       "live-sweep-standings-2026-11-14-e6ee28a8.csv", SRC_STANDINGS)
    problems += [("standings",) + x for x in m1]

    # schedule
    short_to_abbr = {name.split()[-1]: ab for name, ab in name_to_abbr.items()}
    live_g = parse_schedule(short_to_abbr)
    if len(live_g) != 13:
        raise SystemExit("fail-loud: expected 13 Week 11 games, parsed %d" % len(live_g))
    live_gm = {tuple(r[a] for a in ("away", "home")): r for r in live_g}
    committed_g = list(csv.DictReader(open(os.path.join(ROOT, "data", "schedule-wk11-2026.csv"))))
    cgk = [tuple(r[a] for a in ("away", "home")) for r in committed_g]
    cgd = {k: r for r, k in zip(committed_g, cgk)}
    m2, _ = diff_table("official NFL.com Week 11 schedule (live %s) vs data/schedule-wk11-2026.csv" % RETRIEVED,
                       live_gm, cgk, cgd, ["date", "time_et", "network", "nfl_url", "international"],
                       "live-sweep-schedule-2026-11-14-e6ee28a8.csv", SRC_SCHEDULE)
    problems += [("schedule",) + x for x in m2]
    short_to_abbr2 = {name.split()[-1]: ab for name, ab in name_to_abbr.items()}

    def resolve(token):
        t = token.strip()
        if not t:
            return t
        if t in short_to_abbr2:
            return short_to_abbr2[t]
        lw = t.split()[-1]
        if lw in short_to_abbr2:
            return short_to_abbr2[lw]
        for name, ab in name_to_abbr.items():
            if name.startswith(t):
                return ab
        return t

    byes_live = sorted(resolve(n) for n in parse_byes())
    print("\n=== Week 11 byes (live) ===")
    print("  %s" % ", ".join(byes_live))
    site = open(os.path.join(ROOT, "site", "index.html"), encoding="utf-8").read()
    ms = re.search(r"bye: (.+?)\.", site)
    if ms:
        raw = [x.strip() for x in ms.group(1).replace(" and ", ",").split(",")]
        site_byes = sorted(resolve(x) for x in raw if x)
        if site_byes == byes_live:
            print("  RESULT: PASS - the six live byes match the byes published on site/index.html (%s)." % ", ".join(site_byes))
        else:
            print("  RESULT: FAIL - site publishes %s" % site_byes)
            problems.append(("schedule", "byes", tuple(site_byes), tuple(byes_live)))

    # injuries (full capture, not the 44-row sample)
    live_i = parse_injuries()
    print("\n=== injuries capture ===")
    print("  parsed rows: %d" % len(live_i))
    live_im = {(r["player_url"], r["player"], r["team"]): r for r in live_i}
    committed_i = list(csv.DictReader(open(os.path.join(ROOT, "data", "injuries-wk10-2026.csv"))))
    cik = [(r["player_url"], r["player"], r["team"]) for r in committed_i]
    cid = {k: r for r, k in zip(committed_i, cik)}
    m3, missing3 = diff_table(
        "official NFL.com Week 10 injury report (live %s) vs data/injuries-wk10-2026.csv" % RETRIEVED,
        live_im, cik, cid, ["pos", "injuries", "practice", "game_status"],
        "live-sweep-injuries-2026-11-14-e6ee28a8.csv", SRC_INJURIES)
    problems += [("injuries",) + x for x in m3]

    print("\n=== summary ===")
    total_checked = (32 - 0) * 7 + (13 - 0) * 4 + (len(cik) - len(missing3)) * 4
    print("  field checks: standings %d, schedule %d, injuries %d (rows missing from capture: %d)"
          % (32 * 7, 13 * 4, (len(cik) - len(missing3)) * 4, len(missing3)))
    if problems:
        print("  RESULT: FAIL - %d mismatch(es); flagged, never edited." % len(problems))
        return 1
    print("  RESULT: PASS - every captured field matches the committed data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
