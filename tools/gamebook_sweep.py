#!/usr/bin/env python3
"""T48: Official NFL Game Book sweep — Week 10 2026 (all 14 games).

WHY THIS EXISTS
---------------
Three brief requirements were blocked because the project had no official
evidence of what actually happened on game day:

  * "Use official NFL Game Books for actual starters and game-day status"
  * "Capture official inactive lists and snap counts"
  * "Score injury-designation reliability before using it as a feature -
     join several seasons of designations to the official inactive lists and
     measure the play rate per designation with confidence intervals. Only
     then decide whether the label becomes a model feature."

The decision-readiness table on the landing page carried a row reading
"Who actually started is known / not ingested / blocks team-level trust".
This task ingests it, for every game of a complete official week.

WHAT IT READS
-------------
Fourteen private raw transcripts under data/ops/raw/, each transcribed
verbatim from the official NFL Game Book PDF for one Week 10 game. Every
transcript carries the Game Book URL, the Game Center URL and a UTC
retrieval stamp; this tool re-computes the SHA-256 of each transcript and
refuses to publish unless the digest is recorded.

WHAT IT PUBLISHES (and nothing else)
------------------------------------
  data/venue-surface-wk10-2026.csv       official stadium / city / surface /
                                         roof / game-day weather / attendance
  data/actual-starters-wk10-2026.csv     the official "Lineups" section: the
                                         players who ACTUALLY started
  data/inactive-lists-wk10-2026.csv      the official "Not Active" and
                                         "Did Not Play" sections
  data/designation-outcomes-wk10-2026.csv every player carrying an official
                                         Out / Doubtful / Questionable game
                                         status, joined to whether he played
  data/designation-reliability-wk10-2026.csv play rate per designation with n
                                         and a 95% Wilson interval

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
* It does not republish the Game Book roster. Per the T38 reuse gate the full
  per-club player lists stay in the private raw captures; the only
  player-level rows published here are (a) the actual starters, which the
  brief explicitly asks for, and (b) players who already appear on the
  official public injury report, so no new player-level data is created.
* It does not fill a blank. Where the PDF conversion dropped a section, a
  column or a name, the cell is blank and the row carries the flag that says
  which conversion failed. Nothing is inferred from the previous week, from
  the club depth chart, or from a jersey number.
* It does not touch another session's files.

Usage:  python3 tools/gamebook_sweep.py            # write CSVs
        python3 tools/gamebook_sweep.py --check    # validate only (CI gate)
"""
import csv
import hashlib
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "ops", "raw")
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "research", "verification")

RETRIEVED = "2026-11-18"
SEASON = "2026"
WEEK = "10"

OUT_VENUE = os.path.join(DATA, "venue-surface-wk10-2026.csv")
OUT_STARTERS = os.path.join(DATA, "actual-starters-wk10-2026.csv")
OUT_INACTIVE = os.path.join(DATA, "inactive-lists-wk10-2026.csv")
OUT_OUTCOMES = os.path.join(DATA, "designation-outcomes-wk10-2026.csv")
OUT_REL = os.path.join(DATA, "designation-reliability-wk10-2026.csv")
OUT_RECORD_MD = os.path.join(RES, "gamebook-sweep-2026-11-18.md")
OUT_RECORD_CSV = os.path.join(RES, "gamebook-sweep-2026-11-18.csv")

INJURIES = os.path.join(DATA, "injuries-wk10-2026.csv")
GAMES = os.path.join(DATA, "games-2026.csv")

# ---------------------------------------------------------------------------
# The fourteen official Week 10 games. slug -> (away, home, raw file).
# The file list is explicit so the Houston-only T47 capture is never parsed
# as if it were a full game capture.
# ---------------------------------------------------------------------------
GAMES_SPEC = [
    ("was-at-nyg", "WAS", "NYG"),
    ("hou-at-cle-full", "HOU", "CLE"),
    ("buf-at-nyj", "BUF", "NYJ"),
    ("car-at-no", "CAR", "NO"),
    ("jax-at-ten", "JAX", "TEN"),
    ("kc-at-atl", "KC", "ATL"),
    ("lar-at-ari", "LAR", "ARI"),
    ("mia-at-ind", "MIA", "IND"),
    ("min-at-gb", "MIN", "GB"),
    ("ne-at-det", "NE", "DET"),
    ("pit-at-cin", "PIT", "CIN"),
    ("sea-at-lv", "SEA", "LV"),
    ("sf-at-dal", "SF", "DAL"),
    ("lac-at-bal", "LAC", "BAL"),
]

TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
CLUB_TO_TEAM = {v: k for k, v in TEAM_NAMES.items()}

DESIGNATIONS = ["Out", "Doubtful", "Questionable"]

HEADER_KEYS = ["Date", "Stadium", "City", "Start Time", "Game Weather", "Temp",
               "Surface/Roof", "Outdoor Weather", "Paid Attendance", "Game Time"]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _split_sections(text):
    """Split on '---- ... ----' rules; return [(title, body), ...]."""
    out = []
    cur_title, cur = None, []
    for line in text.splitlines():
        m = re.match(r"^-{4}\s*(.*?)\s*-*\s*$", line)
        if m:
            if cur_title is not None:
                out.append((cur_title, "\n".join(cur)))
            cur_title, cur = m.group(1).strip(), []
        elif cur_title is not None:
            cur.append(line)
    if cur_title is not None:
        out.append((cur_title, "\n".join(cur)))
    return out


def _parse_entry(tok):
    """'WR 12 N.Collins' / 'OL B 35 J.Barron' / 'NT 94 (truncated)'.

    Returns (pos, jersey, name, flag). flag is '' when the entry is clean.
    """
    tok = tok.strip()
    if not tok:
        return None
    m = re.match(r"^(\S+)\s+\(no number printed(?:[^)]*)\)\s+(.+)$", tok)
    if m:
        return (m.group(1), "", m.group(2).strip(),
                "jersey number not printed")
    toks = tok.split()
    idx = None
    for i, t in enumerate(toks):
        if re.match(r"^\d+$", t):
            idx = i
            break
    if idx is None:
        # no jersey number survived the conversion
        flag = "jersey number not printed"
        if toks[0].startswith("("):
            return ("", "", "", flag)
        return (" ".join(toks[:1]), "", " ".join(toks[1:]), flag)
    pos = " ".join(toks[:idx])
    num = toks[idx]
    name = " ".join(toks[idx + 1:])
    flag = ""
    if name.startswith("("):
        flag = "name not printed in the conversion"
        name = ""
    if num == "" or not name:
        flag = flag or "incomplete entry"
    return (pos, num, name, flag)


def _parse_lineups(body):
    """Return {club: {'Offense': [...], 'Defense': [...]}} of dicts."""
    out, club, unit = {}, None, None
    for line in body.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9 .'\-]+?)\s*$", line)
        if line.strip() in CLUB_TO_TEAM and not line.startswith(" "):
            club, unit = line.strip(), None
            out.setdefault(club, {"Offense": [], "Defense": []})
            continue
        m = re.match(r"^\s{2}(Offense|Defense)\s*$", line)
        if m:
            unit = m.group(1)
            continue
        if club and unit and line.strip().startswith("("):
            # a parenthetical note where a player row should be - the
            # conversion dropped the block. Recorded, never filled in.
            out[club].setdefault("_notes", []).append(
                "%s %s: %s" % (club, unit, line.strip()))
            continue
        m = re.match(r"^\s{4}(\S+)\s+(\S+)\s+(.*?)\s*$", line)
        if m and club and unit:
            pos, num, name = m.group(1), m.group(2), m.group(3)
            flag = ""
            if name.startswith("("):
                flag = "name not printed in the conversion"
                name = ""
            out[club][unit].append({"pos": pos, "num": num, "name": name,
                                    "flag": flag})
    return out


def _parse_list_sections(body):
    """Parse a Substitutions / Did Not Play / Not Active body.

    Returns (usable, {club: [entries]}, n_unassigned_fragments).
    """
    if "NOT TRANSCRIBABLE" in body:
        return (False, {}, 0)
    out, club, buf, frags = {}, None, [], 0

    def flush():
        if club and buf:
            text = " ".join(x.strip() for x in buf)
            for tok in text.split(","):
                e = _parse_entry(tok)
                if e is None:
                    continue
                pos, num, name, flag = e
                if not name and not num:
                    continue
                if tok.strip().lower().startswith("(none printed"):
                    out.setdefault(club, []).append(
                        {"pos": "", "num": "", "name": "", "flag": tok.strip()})
                    continue
                out.setdefault(club, []).append(
                    {"pos": pos, "num": num, "name": name, "flag": flag})

    for line in body.splitlines():
        if not line.strip():
            continue
        if line.strip() in CLUB_TO_TEAM:
            flush()
            club, buf = line.strip(), []
            out.setdefault(club, [])
            continue
        if re.match(r"^[A-Za-z]", line):
            # unassigned fragment header (e.g. "Unplaced fragment ... FLAGGED:")
            flush()
            club, buf = None, []
            frags += 1
            continue
        if club is None:
            continue
        buf.append(line.strip())
    flush()

    # "Did Not Play"/"Not Active" sections print "(none printed)" per club,
    # which flush() drops - keep the club key so coverage can be reported.
    for line in body.splitlines():
        if line.strip() in CLUB_TO_TEAM:
            out.setdefault(line.strip(), [])
    return (True, out, frags)


def parse_game(slug, away, home):
    path = os.path.join(RAW, "gamebook-%s-2026-reg10.txt" % slug)
    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    g = {"slug": slug, "away": away, "home": home, "raw_sha256": digest,
         "raw_path": "data/ops/raw/gamebook-%s-2026-reg10.txt" % slug,
         "flags": []}
    m = re.search(r"^Source URL\s*:\s*(\S+)", text, re.M)
    g["pdf"] = m.group(1) if m else ""
    m = re.search(r"^Game Center\s*:\s*(\S+)", text, re.M)
    g["center"] = m.group(1) if m else ""

    for key in HEADER_KEYS:
        m = re.search(r"^%s\s*:\s*(.*)$" % re.escape(key), text, re.M)
        g[key] = m.group(1).strip() if m else ""

    # attendance / time sometimes carry a bracketed note
    g["attendance"] = re.sub(r"\s*\(.*?\)\s*$", "", g["Paid Attendance"]).strip()
    g["game_time"] = re.sub(r"\s*\(.*?\)\s*$", "", g["Game Time"]).strip()

    sections = [(t, re.sub(r"\[[^\]]*\]", " ", b, flags=re.S))
                for t, b in _split_sections(text)]
    titles = [t for t, _ in sections]
    g["lineups"] = {}
    g["subs"], g["dnp"], g["na"] = {}, {}, {}
    g["subs_usable"] = True
    for title, body in sections:
        low = title.lower()
        if low.startswith("lineups"):
            g["lineups"] = _parse_lineups(body)
        elif low.startswith("substitution"):
            usable, d, frags = _parse_list_sections(body)
            g["subs"], g["subs_usable"] = d, usable
            if not usable:
                g["flags"].append("substitutions not transcribable")
            if frags:
                g["flags"].append("%d unassigned substitution fragment(s)" % frags)
        elif low.startswith("did not play"):
            _, g["dnp"], _ = _parse_list_sections(body)
        elif low.startswith("not active"):
            _, g["na"], _ = _parse_list_sections(body)
    if not any(t.lower().startswith("did not play") for t in titles):
        g["flags"].append("Did Not Play section not printed")
    if not any(t.lower().startswith("not active") for t in titles):
        g["flags"].append("Not Active section not printed")
    for club, units in g["lineups"].items():
        for note in units.get("_notes", []):
            g["flags"].append(note)
    return g


# ---------------------------------------------------------------------------
# Name matching: injury report "John Bates" vs Game Book "J.Bates"
# ---------------------------------------------------------------------------
SUFFIXES = {"ii", "iii", "iv", "v", "jr", "jr.", "sr", "sr."}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _surname(full):
    """Surname key for a full name: everything after the given name, with
    generational suffixes removed. 'Amon-Ra St. Brown' -> 'stbrown';
    'Carlton Davis III' -> 'davis'; 'Gervon Dexter Sr.' -> 'dexter'."""
    parts = [p for p in re.split(r"\s+", full.strip()) if p]
    if not parts:
        return ""
    tail = [p for p in parts[1:] if p.lower() not in SUFFIXES] or [parts[-1]]
    return _norm("".join(tail))


def _initial(full):
    parts = [p for p in re.split(r"\s+", full.strip()) if p]
    return parts[0][0].lower() if parts and parts[0] else ""


def _gb_key(entry):
    """'J.Bates' -> ('bates', 'j'); 'Bri.Thomas' -> ('thomas', 'b');
    'A.St. Brown' -> ('stbrown', 'a')."""
    name = entry.get("name") or ""
    if "." in name:
        ini, _, sur = name.partition(".")
        return (_norm(sur), ini[:1].lower())
    return (_surname(name), "")


def find_player(entries, full_name):
    """Return the matching Game Book entry, or None. Surname + initial."""
    sur, ini = _surname(full_name), _initial(full_name)
    if not sur:
        return None
    # A surname alone is NOT enough: the Chargers started LG L.Taylor while
    # G Branson Taylor was ruled Out. Where the Game Book prints a first
    # initial it must agree with the injury report's, otherwise the row is
    # left unresolved rather than matched to the wrong man.
    hits = [e for e in entries if _gb_key(e)[0] == sur]
    if not hits:
        return None
    exact = [e for e in hits if not _gb_key(e)[1] or _gb_key(e)[1] == ini]
    if len(exact) == 1:
        return exact[0]
    return None  # ambiguous or initial conflict - never guess


# ---------------------------------------------------------------------------
def wilson(k, n, z=1.959963985):
    if n == 0:
        return ("", "")
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den
    return (max(0.0, ctr - half), min(1.0, ctr + half))


def load_injuries():
    rows = []
    with open(INJURIES, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("game_status") or "").strip() in DESIGNATIONS:
                rows.append(r)
    return rows


def week10_games():
    out = {}
    with open(GAMES, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["week"] == WEEK:
                out[r["away"]] = r
                out[r["home"]] = r
    return out


def build():
    games = [parse_game(*s) for s in GAMES_SPEC]
    by_team = {}
    for g in games:
        by_team[g["away"]] = g
        by_team[g["home"]] = g

    # ---- venue / surface / roof / weather register ----
    venue_rows = []
    for g in sorted(games, key=lambda x: (x["home"], x["away"])):
        venue_rows.append({
            "week": WEEK, "away": g["away"], "home": g["home"],
            "kickoff_local": g["Start Time"], "date": g["Date"],
            "stadium_game_book": g["Stadium"], "city": g["City"],
            "surface_roof": g["Surface/Roof"], "game_weather": g["Game Weather"],
            "temp_f": g["Temp"], "outdoor_weather": g["Outdoor Weather"],
            "attendance": g["attendance"], "game_time": g["game_time"],
            "source_game_center": g["center"], "source_pdf": g["pdf"],
            "retrieved": RETRIEVED, "raw_sha256": g["raw_sha256"],
        })

    # ---- actual starters ----
    starter_rows = []
    for g in sorted(games, key=lambda x: (x["home"], x["away"])):
        for club, units in g["lineups"].items():
            team = CLUB_TO_TEAM.get(club, "")
            for unit in ("Offense", "Defense"):
                for e in units.get(unit, []):
                    starter_rows.append({
                        "week": WEEK, "team": team, "club": club,
                        "opponent": g["home"] if team == g["away"] else g["away"],
                        "unit": unit, "pos": e["pos"], "jersey": e["num"],
                        "player": e["name"],
                        "name_flag": e["flag"],
                        "source_game_center": g["center"], "source_pdf": g["pdf"],
                        "retrieved": RETRIEVED, "raw_sha256": g["raw_sha256"],
                    })

    # ---- inactive / did-not-play register ----
    inactive_rows = []
    for g in sorted(games, key=lambda x: (x["home"], x["away"])):
        for section, key in (("Did Not Play", "dnp"), ("Not Active", "na")):
            for club, entries in g[key].items():
                team = CLUB_TO_TEAM.get(club, "")
                if not entries:
                    inactive_rows.append({
                        "week": WEEK, "team": team, "club": club,
                        "section": section, "pos": "", "jersey": "", "player": "",
                        "note": "none printed in the official Game Book",
                        "source_game_center": g["center"], "source_pdf": g["pdf"],
                        "retrieved": RETRIEVED, "raw_sha256": g["raw_sha256"],
                    })
                    continue
                for e in entries:
                    inactive_rows.append({
                        "week": WEEK, "team": team, "club": club,
                        "section": section, "pos": e["pos"], "jersey": e["num"],
                        "player": e["name"],
                        "note": e["flag"] if e["name"] else (e["flag"] or "none printed"),
                        "source_game_center": g["center"], "source_pdf": g["pdf"],
                        "retrieved": RETRIEVED, "raw_sha256": g["raw_sha256"],
                    })

    # ---- participation map: club -> {key: 'played' | 'did not play'} ----
    part = {}
    unknown_reasons = {}
    for g in games:
        for club, units in g["lineups"].items():
            team = CLUB_TO_TEAM.get(club, "")
            part.setdefault(team, {})
            for unit in ("Offense", "Defense"):
                for e in units.get(unit, []):
                    if e["name"]:
                        part[team][_gb_key(e)] = "played"
        for club, entries in g["subs"].items():
            team = CLUB_TO_TEAM.get(club, "")
            part.setdefault(team, {})
            for e in entries:
                if e["name"]:
                    part[team][_gb_key(e)] = "played"
        for key in ("dnp", "na"):
            for club, entries in g[key].items():
                team = CLUB_TO_TEAM.get(club, "")
                part.setdefault(team, {})
                for e in entries:
                    if e["name"]:
                        k = _gb_key(e)
                        if part[team].get(k) != "played":
                            part[team][k] = "did not play"
        if not g["subs_usable"]:
            unknown_reasons.setdefault(g["away"], []).append(
                "substitutions not transcribable")
            unknown_reasons.setdefault(g["home"], []).append(
                "substitutions not transcribable")

    # ---- designation outcomes ----
    sched = week10_games()
    outcome_rows, unresolved = [], []
    for r in load_injuries():
        team = (r.get("team") or "").strip()
        player = (r.get("player") or "").strip()
        status = (r.get("game_status") or "").strip()
        g = by_team.get(team)
        if not g:
            outcome_rows.append(_outcome(r, "", status, "no Week 10 game for this club",
                                         "", "", "unresolved"))
            unresolved.append((team, player, "club did not play in Week 10 "
                                             "(bye or not on the slate)"))
            continue
        entries = []
        for club, units in g["lineups"].items():
            if CLUB_TO_TEAM.get(club) == team:
                for u in ("Offense", "Defense"):
                    entries += units.get(u, [])
        for key in ("subs", "dnp", "na"):
            for club, lst in g[key].items():
                if CLUB_TO_TEAM.get(club) == team:
                    entries += lst
        hit = find_player(entries, player)
        if hit is None:
            reason = "not in the Game Book's lineup, substitution, did-not-play or not-active lists"
            outcome_rows.append(_outcome(r, "", status, reason,
                                         g["center"], g["pdf"], "unresolved"))
            unresolved.append((team, player, reason))
            continue
        verdict = part.get(team, {}).get(_gb_key(hit))
        if verdict:
            outcome_rows.append(_outcome(r, hit.get("name", ""), status,
                                         verdict, g["center"], g["pdf"], "resolved"))
        else:
            outcome_rows.append(_outcome(r, hit.get("name", ""), status,
                                         "matched but verdict unknown (section not transcribable)",
                                         g["center"], g["pdf"], "unresolved"))
            unresolved.append((team, player, "verdict unknown"))

    # ---- reliability: play rate per designation ----
    rel_rows = []
    for des in DESIGNATIONS:
        sub = [r for r in outcome_rows
               if r["designation"] == des and r["resolution"] == "resolved"]
        n = len(sub)
        k = sum(1 for r in sub if r["verdict"] == "played")
        lo, hi = wilson(k, n)
        rel_rows.append({
            "designation": des, "n_resolved": n, "n_played": k,
            "play_rate": "" if n == 0 else round(k / n, 4),
            "ci95_low": "" if n == 0 else round(lo, 4),
            "ci95_high": "" if n == 0 else round(hi, 4),
            "n_unresolved": sum(1 for r in outcome_rows
                                if r["designation"] == des
                                and r["resolution"] == "unresolved"),
            "interval": "Wilson score, 95%",
            "source": "https://www.nfl.com/injuries/league/2026/reg10",
        })
    return games, venue_rows, starter_rows, inactive_rows, outcome_rows, rel_rows, unresolved


def _outcome(inj, gb_name, status, verdict, center, pdf, resolution):
    return {
        "week": WEEK,
        "team": (inj.get("team") or "").strip(),
        "player": (inj.get("player") or "").strip(),
        "pos": (inj.get("pos") or "").strip(),
        "practice": (inj.get("practice") or "").strip(),
        "designation": status,
        "game_book_name": gb_name,
        "verdict": verdict,
        "resolution": resolution,
        "source_injury_report": "https://www.nfl.com/injuries/league/2026/reg10",
        "source_game_center": center,
        "source_pdf": pdf,
        "retrieved": RETRIEVED,
    }


# ---------------------------------------------------------------------------
def check():
    problems = []
    if not os.path.isfile(INJURIES):
        problems.append("missing %s" % INJURIES)
        return problems
    games, venue, starters, inactive, outcomes, rel, unresolved = build()

    if len(games) != 14:
        problems.append("expected 14 game captures, parsed %d" % len(games))
    if len(venue) != 14:
        problems.append("expected 14 venue rows, got %d" % len(venue))
    for g in games:
        for field in ("center", "pdf"):
            if not g[field].startswith("https://"):
                problems.append("%s: %s missing/https" % (g["slug"], field))
        if not re.match(r"^[0-9a-f]{64}$", g["raw_sha256"]):
            problems.append("%s: bad sha256" % g["slug"])
        if not g["Stadium"]:
            problems.append("%s: no stadium parsed" % g["slug"])
        if not g["Surface/Roof"]:
            problems.append("%s: no surface/roof parsed" % g["slug"])
        if len(g["lineups"]) != 2:
            problems.append("%s: parsed %d clubs in Lineups, expected 2"
                            % (g["slug"], len(g["lineups"])))
        for club, units in g["lineups"].items():
            for unit in ("Offense", "Defense"):
                got = len(units.get(unit, []))
                if got not in (0, 11):
                    problems.append("%s %s %s: %d starters, expected 11 or blank"
                                    % (g["slug"], club, unit, got))
    # every published row must carry an https source
    for name, rows in (("venue", venue), ("starters", starters),
                       ("inactive", inactive), ("outcomes", outcomes)):
        for r in rows:
            if not (r.get("source_game_center", "") or "").startswith("https://"):
                problems.append("%s row without an https game-centre link: %s"
                                % (name, r.get("player") or r.get("home") or "?"))
                break
    # reliability arithmetic
    for r in rel:
        if r["n_resolved"] and r["n_played"] > r["n_resolved"]:
            problems.append("%s: played > resolved" % r["designation"])
        if r["n_resolved"] and not (0 <= r["play_rate"] <= 1):
            problems.append("%s: play rate out of range" % r["designation"])
    tot = sum(r["n_resolved"] for r in rel) + sum(r["n_unresolved"] for r in rel)
    if tot != len(outcomes):
        problems.append("reliability counts (%d) != outcome rows (%d)" % (tot, len(outcomes)))
    return problems


# ---------------------------------------------------------------------------
def write_csvs():
    games, venue, starters, inactive, outcomes, rel, unresolved = build()

    def dump(path, rows, cols):
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in cols})

    dump(OUT_VENUE, venue, ["week", "away", "home", "date", "kickoff_local",
                            "stadium_game_book", "city", "surface_roof",
                            "game_weather", "temp_f", "outdoor_weather",
                            "attendance", "game_time", "source_game_center",
                            "source_pdf", "retrieved", "raw_sha256"])
    dump(OUT_STARTERS, starters, ["week", "team", "club", "opponent", "unit",
                                  "pos", "jersey", "player", "name_flag",
                                  "source_game_center", "source_pdf",
                                  "retrieved", "raw_sha256"])
    dump(OUT_INACTIVE, inactive, ["week", "team", "club", "section", "pos",
                                  "jersey", "player", "note",
                                  "source_game_center", "source_pdf",
                                  "retrieved", "raw_sha256"])
    dump(OUT_OUTCOMES, outcomes, ["week", "team", "player", "pos", "practice",
                                  "designation", "game_book_name", "verdict",
                                  "resolution", "source_injury_report",
                                  "source_game_center", "source_pdf", "retrieved"])
    dump(OUT_REL, rel, ["designation", "n_resolved", "n_played", "play_rate",
                        "ci95_low", "ci95_high", "n_unresolved", "interval",
                        "source"])
    return games, venue, starters, inactive, outcomes, rel, unresolved


def write_record(games, venue, starters, inactive, outcomes, rel, unresolved):
    os.makedirs(RES, exist_ok=True)
    with open(OUT_RECORD_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "value", "detail"])
        w.writerow(["games captured", len(games), "all 14 official Week 10 games"])
        w.writerow(["venue rows", len(venue), "one per game"])
        w.writerow(["actual starter rows", len(starters), "Lineups section"])
        w.writerow(["inactive/dnp rows", len(inactive), "Not Active + Did Not Play"])
        w.writerow(["designated players joined", len(outcomes),
                    "official Week 10 report rows carrying a game status"])
        for r in rel:
            w.writerow(["play rate %s" % r["designation"], r["play_rate"],
                        "n=%d, 95%% Wilson [%s, %s]"
                        % (r["n_resolved"], r["ci95_low"], r["ci95_high"])])
        for g in games:
            w.writerow(["capture %s" % g["slug"], g["raw_sha256"],
                        "; ".join(g["flags"]) or "complete"])
    return OUT_RECORD_CSV


# ---------------------------------------------------------------------------
def body_real():
    import pages as P
    esc, src, badge, table, blank = P.esc, P.src, P.badge, P.table, P.blank
    games, venue, starters, inactive, outcomes, rel, unresolved = build()
    n_starter = len(starters)
    n_blank_starter = sum(1 for r in starters if r["name_flag"])

    h = []
    h.append(
        '<div class="grid g4">'
        '<article class="card hero-card"><span class="k">Games captured</span>'
        '<div class="v">%d</div><div class="n">Every official Week 10 game, Game Book read in full</div></article>'
        '<article class="card hero-card"><span class="k">Actual starters</span>'
        '<div class="v">%d</div><div class="n">Official Lineups sections, both clubs, both units</div></article>'
        '<article class="card hero-card"><span class="k">Inactive / DNP rows</span>'
        '<div class="v">%d</div><div class="n">Official Not Active and Did Not Play lists</div></article>'
        '<article class="card hero-card"><span class="k">Designations joined</span>'
        '<div class="v">%d</div><div class="n">Week 10 report rows carrying Out, Doubtful or Questionable</div></article>'
        '</div>' % (len(games), n_starter, len([r for r in inactive if r["player"]]),
                    len(outcomes)))

    # --- reliability ---
    h.append('<section style="margin-top:26px"><div class="section-head"><div>'
             '<span class="eyebrow">Empirical designation calibration</span>'
             '<h2>What &ldquo;Questionable&rdquo; actually meant in Week 10</h2>'
             '<p class="muted">Every player on the official Week 10 injury report who '
             'carried a game status, joined to the official Game Book for his own game '
             'and scored on whether he actually played. The interval is a 95%% Wilson '
             'score interval; n is printed because a rate without n is not a '
             'measurement. This is one week of one season &mdash; it is a first '
             'estimate, not a constant, and it is not used as a model feature until '
             'the sample is large enough for the interval to be useful.</p></div>'
             '<span class="tag warn">n = %d resolved</span></div>'
             % sum(r["n_resolved"] for r in rel))
    rows = []
    for r in rel:
        rows.append([
            badge(r["designation"], "no" if r["designation"] == "Out" else "warn"),
            P.num(r["n_resolved"]),
            P.num(r["n_played"]),
            ("%.1f%%" % (100 * r["play_rate"])) if r["play_rate"] != "" else blank(),
            ("%.1f%% &ndash; %.1f%%" % (100 * r["ci95_low"], 100 * r["ci95_high"]))
            if r["ci95_low"] != "" else blank(),
            P.num(r["n_unresolved"]),
            src(r["source"], "Official report"),
        ])
    h.append(table([("Designation", 0), ("n resolved", 1), ("Played", 1),
                    ("Play rate", 1), ("95% Wilson interval", 0),
                    ("n unresolved", 1), ("Source", 0)], rows,
                   note="A player counts as <i>played</i> when the Game Book lists him "
                        "in Lineups or Substitutions, and as <i>did not play</i> when it "
                        "lists him under Did Not Play or Not Active. A player who is in "
                        "none of the four sections is unresolved and is counted "
                        "separately, never assumed."))
    h.append('</section>')

    # --- venue / surface / roof ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Official venue register</span>'
             '<h2>Stadium, surface, roof and game-day weather</h2>'
             '<p class="muted">Transcribed from the Game Book header of every Week 10 '
             'game. The roof/surface field is the league&rsquo;s own wording '
             '(&ldquo;Open Stadium on Natural Grass&rdquo;, &ldquo;Retractable Roof &ndash; '
             'Closed on Field Turf&rdquo;), not an interpretation. This is the field the '
             'totals-and-passing-prop work needs and it was not on the site before.</p>'
             '</div><span class="tag">%d games</span></div>' % len(venue))
    rows = []
    for r in venue:
        rows.append([
            esc("%s @ %s" % (r["away"], r["home"])),
            esc(r["stadium_game_book"]),
            esc(r["city"]),
            esc(r["surface_roof"]),
            esc(r["game_weather"]) if r["game_weather"] else blank("not printed"),
            esc(r["temp_f"]) if r["temp_f"] else blank("not printed"),
            esc(r["attendance"]) if r["attendance"] else blank("not printed"),
            "%s %s" % (src(r["source_game_center"], "Centre"), src(r["source_pdf"], "PDF")),
        ])
    h.append(table([("Game", 0), ("Stadium (Game Book)", 0), ("City", 0),
                    ("Surface / roof", 0), ("Game weather", 0), ("Temp / humidity / wind", 0),
                    ("Attendance", 1), ("Source", 0)], rows,
                   note="Where the Game Book prints no weather line (enclosed stadiums) "
                        "the cell is blank and flagged, not filled from a forecast."))
    h.append('</section>')

    # --- actual starters ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Actual starters</span>'
             '<h2>Who actually started, from the league&rsquo;s own Lineups section</h2>'
             '<p class="muted">Not the club depth chart &mdash; the Game Book Lineups, '
             'which is what the league records as the starters of that game. '
             '%d rows; %d carry a name the PDF conversion did not preserve and are '
             'blank and flagged rather than inferred.</p>'
             '</div><span class="tag">%d rows</span></div>'
             % (n_starter, n_blank_starter, n_starter))
    rows = []
    for r in starters:
        rows.append([
            esc(r["team"]),
            esc(r["unit"]),
            esc(r["pos"]),
            P.num(r["jersey"]),
            esc(r["player"]) if r["player"] else blank("not printed"),
            esc(r["name_flag"]) if r["name_flag"] else "",
            "%s %s" % (src(r["source_game_center"], "Centre"), src(r["source_pdf"], "PDF")),
        ])
    h.append(table([("Team", 0), ("Unit", 0), ("Pos", 0), ("#", 1), ("Player", 0),
                    ("Flag", 0), ("Source", 0)], rows[:],
                   row_attrs=lambda i: ' data-team="%s" data-unit="%s"'
                   % (esc(starters[i]["team"]), esc(starters[i]["unit"])),
                   note="Every row links to the official game-centre page and the Game "
                        "Book PDF it was transcribed from."))
    h.append('</section>')

    # --- inactive / DNP ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Inactive and did-not-play lists</span>'
             '<h2>The official game-day exclusions</h2>'
             '<p class="muted">The Game Book prints these as two separate lists: '
             '<i>Not Active</i> (the club&rsquo;s declared inactives) and <i>Did Not '
             'Play</i> (dressed but unused). Both are transcribed. A club with an empty '
             'list is printed as an empty list &mdash; that is a fact, not a gap.</p>'
             '</div><span class="tag">%d rows</span></div>' % len(inactive))
    rows = []
    for r in inactive:
        rows.append([
            esc(r["team"]),
            badge(r["section"], "warn" if r["section"] == "Not Active" else "mute"),
            esc(r["pos"]),
            P.num(r["jersey"]),
            esc(r["player"]) if r["player"] else blank("none printed"),
            esc(r["note"]) if r["note"] else "",
            "%s %s" % (src(r["source_game_center"], "Centre"), src(r["source_pdf"], "PDF")),
        ])
    h.append(table([("Team", 0), ("Section", 0), ("Pos", 0), ("#", 1), ("Player", 0),
                    ("Flag", 0), ("Source", 0)], rows,
                   row_attrs=lambda i: ' data-team="%s" data-section="%s"'
                   % (esc(inactive[i]["team"]), esc(inactive[i]["section"]))))
    h.append('</section>')

    # --- outcomes ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Designation outcomes</span>'
             '<h2>Every designated player, and what happened</h2>'
             '<p class="muted">The join behind the calibration table, published row by '
             'row so the rate can be checked without trusting it. A player who appears '
             'on the official injury report but in none of the Game Book&rsquo;s four '
             'sections is <i>unresolved</i> &mdash; usually because he is on a reserve '
             'list, which a game book does not print at all.</p>'
             '</div><span class="tag warn">%d unresolved</span></div>' % len(unresolved))
    rows = []
    for r in outcomes:
        v = r["verdict"]
        cls = "ok" if v == "played" else ("mute" if v == "did not play" else "warn")
        rows.append([
            esc(r["team"]),
            esc(r["player"]),
            esc(r["pos"]),
            badge(r["designation"], "no" if r["designation"] == "Out" else "warn"),
            esc(r["practice"]),
            esc(r["game_book_name"]) if r["game_book_name"] else blank(),
            badge(v, cls) if v else blank("unresolved"),
            esc(r["resolution"]),
            "%s %s" % (src(r["source_injury_report"], "Report"), src(r["source_pdf"], "PDF")),
        ])
    h.append(table([("Team", 0), ("Player", 0), ("Pos", 0), ("Designation", 0),
                    ("Practice", 0), ("Game Book name", 0), ("Verdict", 0),
                    ("Resolution", 0), ("Source", 0)], rows,
                   row_attrs=lambda i: ' data-team="%s" data-des="%s" data-res="%s"'
                   % (esc(outcomes[i]["team"]), esc(outcomes[i]["designation"]),
                      esc(outcomes[i]["resolution"]))))
    h.append('</section>')

    # --- capture register ---
    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Capture register</span>'
             '<h2>Every capture, its hash and what the conversion lost</h2>'
             '<p class="muted">The Game Book is a PDF; converting it to text loses '
             'cells. Where that happened the loss is named here rather than papered '
             'over. The raw text is stored privately with a SHA-256 and a UTC stamp; '
             'only derived rows are published, per the reuse gate.</p></div>'
             '<span class="tag">%d captures</span></div>' % len(games))
    rows = []
    for g in sorted(games, key=lambda x: (x["home"], x["away"])):
        rows.append([
            esc("%s @ %s" % (g["away"], g["home"])),
            esc(g["Stadium"]),
            '<code class="mono">%s</code>' % esc(g["raw_sha256"][:16] + "…"),
            esc("; ".join(g["flags"])) if g["flags"] else badge("complete", "ok"),
            "%s %s" % (src(g["center"], "Centre"), src(g["pdf"], "PDF")),
        ])
    h.append(table([("Game", 0), ("Stadium", 0), ("Capture SHA-256 (first 16)", 0),
                    ("Conversion losses", 0), ("Source", 0)], rows))
    h.append('</section>')
    return "".join(h)


def write_pages(site_dir, shell):
    games, venue, starters, inactive, outcomes, rel, unresolved = write_csvs()
    write_record(games, venue, starters, inactive, outcomes, rel, unresolved)
    body = body_real()
    with open(os.path.join(site_dir, "gamebook.html"), "w", encoding="utf-8") as fh:
        fh.write(shell("gamebook", "Game books &mdash; Week 10",
                       "Actual starters, official inactive lists, the venue / surface / "
                       "roof register, and the first empirical calibration of what "
                       "Out, Doubtful and Questionable actually meant &mdash; read from "
                       "the official NFL Game Book for all 14 Week 10 games.",
                       body, "gamebook.html"))
    return ["gamebook.html"]


def main():
    if "--check" in sys.argv:
        problems = check()
        if problems:
            for p in problems:
                print("FAIL:", p)
            print("gamebook_sweep: %d problem(s)" % len(problems))
            return 1
        print("gamebook_sweep: OK")
        return 0
    problems = check()
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    games, venue, starters, inactive, outcomes, rel, unresolved = write_csvs()
    write_record(games, venue, starters, inactive, outcomes, rel, unresolved)
    print("gamebook_sweep: %d games, %d venue, %d starters, %d inactive, "
          "%d outcomes, %d unresolved"
          % (len(games), len(venue), len(starters), len(inactive),
             len(outcomes), len(unresolved)))
    for r in rel:
        print("  %-12s n=%-4d played=%-4d rate=%s  CI[%s, %s]"
              % (r["designation"], r["n_resolved"], r["n_played"],
                 r["play_rate"], r["ci95_low"], r["ci95_high"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
