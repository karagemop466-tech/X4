#!/usr/bin/env python3
"""
Diff a live capture of an official NFL.com page against the committed dataset.

The capture files live in research/verification/ and are verbatim excerpts of
the official page, fetched directly (never from a search snippet). This script
re-reads them and compares every field with the CSV the site publishes, so a
typo in a published number cannot survive a re-verification.

Usage:
    python3 tools/verify_live.py standings

Exit code 0 = the committed data matches the official source exactly.
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIF = os.path.join(ROOT, "research", "verification")

# The capture row is a markdown table row whose first cell holds the club logo
# markdown and the club name; the numeric columns follow, in the order the
# official page's own legend defines them: W, L, T, PCT, PF, PA, NET PTS.
ROW = re.compile(r"^\|\s*\[!\[[^\]]*\]\([^)]*\)\\?<br>\\?<br>(?P<name>[^<|]+?)<br>")
CELL = re.compile(r"(?<![\d.\-])\(?-?\d+(?:\.\d+)?\)?(?=\s*\|)")


def parse_capture(path):
    """Return {club name: (w, l, t, pct, pf, pa, net)} from a live capture file."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = ROW.match(line)
            if not m:
                continue
            name = m.group("name").strip()
            cells = [c.strip() for c in line.rstrip().rstrip("|").split("|")]
            # The first cell of a markdown row is empty; the second holds the
            # logo and the club name; the next seven are the official W, L, T,
            # PCT, PF, PA and NET PTS columns.
            nums = []
            for c in cells[2:]:
                c = c.strip()
                if re.fullmatch(r"-?\d+(?:\.\d+)?", c):
                    nums.append(c)
                elif re.fullmatch(r"\(-?\d+(?:\.\d+)?\)", c):
                    nums.append(c.strip("()"))
                else:
                    break
            if len(nums) < 7:
                raise SystemExit("capture row for %s has %d numeric cells, expected 7"
                                 % (name, len(nums)))
            out[name] = nums[:7]
    return out


def check_standings():
    live = parse_capture(os.path.join(VERIF, "standings-live-2026-11-14.md"))
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "standings-wk10-2026.csv"))))
    committed = {r["team"]: r for r in rows}

    problems = []
    checked = 0
    if len(live) != 32:
        problems.append("live capture holds %d clubs, expected 32" % len(live))
    if len(committed) != 32:
        problems.append("committed CSV holds %d clubs, expected 32" % len(committed))

    for name, vals in sorted(live.items()):
        c = committed.get(name)
        if c is None:
            problems.append("%s: on the official page but not in the committed CSV" % name)
            continue
        checked += 1
        fields = (("w", vals[0]), ("l", vals[1]), ("t", vals[2]), ("pct", vals[3]),
                  ("pf", vals[4]), ("pa", vals[5]), ("net_pts", vals[6]))
        for key, live_v in fields:
            got = c[key]
            if key == "pct":
                if abs(float(got) - float(live_v)) > 1e-9:
                    problems.append("%s: %s committed %s but official page says %s"
                                    % (name, key, got, live_v))
            elif int(got) != int(live_v):
                problems.append("%s: %s committed %s but official page says %s"
                                % (name, key, got, live_v))
        # internal arithmetic, proved on the official numbers
        if int(c["pf"]) - int(c["pa"]) != int(c["net_pts"]):
            problems.append("%s: net points is not points for minus points allowed" % name)

    for name in committed:
        if name not in live:
            problems.append("%s: in the committed CSV but not on the official page" % name)

    print("standings rows checked against the live NFL.com capture: %d" % checked)
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("RESULT: PASS - all 32 clubs match the official NFL.com standings on "
          "W, L, T, PCT, PF, PA and NET PTS.")
    return 0


# The club heading printed on the official injury page, mapped to the
# abbreviation this repository uses in data/injuries-wk10-2026.csv.
PRACTICE = {
    "Full Participation in Practice": "Full",
    "Limited Participation in Practice": "Limited",
    "Did Not Participate In Practice": "DNP",
}
PLAYER_ROW = re.compile(
    r"^\|\s*\[([^\]]+)\]\((https://www\.nfl\.com/players/[^)]+)\)\s*"
    r"\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")

# The club nickname printed on the official schedule and injury pages, mapped
# to the abbreviation this repository uses.
NICKNAME = {
    "Commanders": "WAS", "Giants": "NYG", "Patriots": "NE", "Lions": "DET",
    "Chiefs": "KC", "Falcons": "ATL", "Vikings": "MIN", "Packers": "GB",
    "Jaguars": "JAX", "Titans": "TEN", "Bills": "BUF", "Jets": "NYJ",
    "Dolphins": "MIA", "Colts": "IND", "Panthers": "CAR", "Saints": "NO",
    "Texans": "HOU", "Browns": "CLE", "Rams": "LAR", "Cardinals": "ARI",
    "Seahawks": "SEA", "Raiders": "LV", "49ers": "SF", "Cowboys": "DAL",
    "Steelers": "PIT", "Bengals": "CIN", "Chargers": "LAC", "Ravens": "BAL",
    "Bears": "CHI", "Buccaneers": "TB", "Eagles": "PHI", "Broncos": "DEN",
}


def read_injury_capture():
    """Return the live injury rows as {team: [row, ...]}, in page order."""
    text = ""
    for i in range(8):
        with open(os.path.join(VERIF, "injuries-chunk%d.md" % i), encoding="utf-8") as fh:
            part = fh.read()
        # The capture files were written by hand, so each one carries extra
        # trailing newlines; drop them. The fetch tool then splits the page at
        # arbitrary character offsets, so the chunks are rejoined exactly: a
        # chunk that ends on a table row's final "|" was followed by a newline
        # in the original page, and a chunk that ends mid-row was not.
        part = part.rstrip("\n")
        if text and text.endswith("|"):
            text += "\n"
        text += part
    # The tool splits mid-token; repair the URL joins it produced so the row
    # parser sees a whole URL.
    text = re.sub(r"https:(//?)www\.nfl\.com", r"https://www.nfl.com", text)

    live, team = [], None
    for line in text.splitlines():
        head = re.match(r"^###\s+(\S+)\s*$", line)
        if head:
            name = head.group(1)
            if name not in NICKNAME:
                raise SystemExit("unknown club heading in the capture: %r" % name)
            team = NICKNAME[name]
            continue
        m = PLAYER_ROW.match(line)
        if not m:
            continue
        player, url, pos, injuries, practice, status = m.groups()
        if team is None:
            raise SystemExit("player row before any club heading: %s" % player)
        live.append({
            "team": team, "player": player, "pos": pos,
            "injuries": injuries, "practice": PRACTICE.get(practice, practice),
            "game_status": status, "player_url": url,
        })
    return live


def check_injuries():
    live = read_injury_capture()
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "injuries-wk10-2026.csv"))))
    key = lambda r: (r["team"], r["player"])
    live_by_key = {key(r): r for r in live}
    csv_by_key = {key(r): r for r in rows}

    problems = []
    if len(live) != len(rows):
        problems.append("live report has %d player rows, the committed CSV has %d"
                        % (len(live), len(rows)))
    for k in sorted(csv_by_key):
        c = csv_by_key[k]
        l = live_by_key.get(k)
        if l is None:
            problems.append("%s %s: in the committed CSV but not on the official page"
                            % (k[0], k[1]))
            continue
        for field in ("pos", "injuries", "practice", "game_status", "player_url"):
            if c[field] != l[field]:
                problems.append("%s %s: %s committed %r but the official page says %r"
                                % (k[0], k[1], field, c[field], l[field]))
    for k in sorted(live_by_key):
        if k not in csv_by_key:
            problems.append("%s %s: on the official page but missing from the committed CSV"
                            % k)

    print("injury rows checked against the live NFL.com capture: %d" % len(live))
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems[:60]:
            print("  - %s" % p)
        if len(problems) > 60:
            print("  ... and %d more" % (len(problems) - 60))
        return 1
    print("RESULT: PASS - all %d players on the official Week 10 injury report match "
          "the committed CSV on team, position, injury, practice status, game status "
          "and player URL." % len(live))
    return 0


def check_schedule():
    path = os.path.join(VERIF, "schedule-wk11-live-2026-11-14.md")
    text = open(path, encoding="utf-8").read()
    games = re.findall(
        r"^- \[(.+?) at (.+?), (?:Thursday|Sunday|Monday), November (\d+)(?:st|nd|rd|th), "
        r"(\d+:\d+ [AP]M), ([A-Z0-9 ,]+)\]\((https://www\.nfl\.com/games/[^)]+)\)",
        text, re.M)
    byes = re.findall(r"^([A-Z]{2,3})[A-Z][A-Za-z ]+$", text, re.M)
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "schedule-wk11-2026.csv"))))

    problems = []
    if len(games) != len(rows):
        problems.append("live page lists %d games, the committed CSV has %d"
                        % (len(games), len(rows)))
    live_by_url = {g[5]: g for g in games}
    for r in rows:
        g = live_by_url.get(r["nfl_url"])
        if g is None:
            problems.append("%s at %s: not on the live official Week 11 page"
                            % (r["away"], r["home"]))
            continue
        nickname_away, nickname_home, day, kick, network, _ = g
        if NICKNAME.get(nickname_away) != r["away"]:
            problems.append("%s at %s: the live page lists %s as the away club"
                            % (r["away"], r["home"], nickname_away))
        if NICKNAME.get(nickname_home) != r["home"]:
            problems.append("%s at %s: the live page lists %s as the home club"
                            % (r["away"], r["home"], nickname_home))
        if kick != r["time_et"]:
            problems.append("%s at %s: committed kickoff %s but the live page says %s"
                            % (r["away"], r["home"], r["time_et"], kick))
        live_net = network.split(",")[0].strip()
        if live_net != r["network"]:
            problems.append("%s at %s: committed network %s but the live page says %s"
                            % (r["away"], r["home"], r["network"], live_net))
        if "November %s" % day != "November %s" % r["date"].split("-")[2].lstrip("0"):
            problems.append("%s at %s: committed date %s but the live page says November %s"
                            % (r["away"], r["home"], r["date"], day))
    # The six clubs on bye are printed by the official page; the committed
    # dataset does not restate them, so check the published list against it.
    expected_byes = {"ATL", "CLE", "GB", "LAR", "NE", "SEA"}
    if set(byes) != expected_byes:
        problems.append("live page lists these clubs on bye: %s (expected %s)"
                        % (sorted(set(byes)), sorted(expected_byes)))

    print("Week 11 games checked against the live NFL.com schedule: %d" % len(games))
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("RESULT: PASS - all %d Week 11 games match the official NFL.com schedule on "
          "matchup, date, kickoff and network, and the six clubs on bye match."
          % len(games))
    return 0


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    checks = {"standings": check_standings, "injuries": check_injuries,
              "schedule": check_schedule}
    if what == "all":
        rc = 0
        for name in ("standings", "schedule", "injuries"):
            print("\n=== %s ===" % name)
            rc = checks[name]() or rc
        print("\n%s" % ("RESULT: PASS - every live capture matches the committed data."
                        if rc == 0 else "RESULT: FAIL - see the problems above."))
        return rc
    if what not in checks:
        raise SystemExit("unknown check %r (expected one of %s)"
                         % (what, ", ".join(sorted(checks))))
    return checks[what]()


if __name__ == "__main__":
    sys.exit(main())
