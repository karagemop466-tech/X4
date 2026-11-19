#!/usr/bin/env python3
"""
Official depth-chart acquisition and starter-out deficiency pipeline.

WHY THIS EXISTS
---------------
`nfl.com/teams/<club>/depth-chart` returns HTTP 404 for every club, which is why
depth-chart strings were previously published as unverifiable (flag F-02). The
clubs' *own* official sites - each club's official website, linked from its
nfl.com club page - do publish an ordered depth chart. The chart is a table whose
column position carries the depth position: the first name in a row is the
starter, the second is the backup, the third is third string.

That is an official, source-linkable statement of depth order, so it can be
captured without inference. This tool does exactly three things:

  1. TRANSCRIBE  (below, in CHARTS) each club's chart exactly as published.
                 A depth CHART CELL may hold one name, several names (the club
                 published co-starters in one cell) or no name at all (the club
                 published an empty cell). The transcription keeps that
                 distinction: a cell is a string (one name), a tuple (names in
                 one printed cell) or "" (a printed but empty cell).
  2. VALIDATE    every transcription against the committed, already-verified
                 official data: the club must exist in the standings file, every
                 injured player we pair it with must appear in the official Week
                 10 injury report with the same club, and the positional order
                 must be internally consistent (no player listed twice in one
                 cell, no empty cell carrying a name).
  3. BUILD       data/depth-wk11-2026.csv - one row per name in a printed
                 cell, plus one row per printed empty cell - and the
                 starter-out deficiency roll-up, which is computed on CELLS, so
                 a club that published two co-starters is never reported as
                 having lost its starter to one injury.

WHAT THIS TOOL DELIBERATELY DOES NOT DO
---------------------------------------
* It does not invent a depth rank where the club does not publish one. Houston
  publishes its chart as an image, so Houston has no rows here and the gap is
  flagged (F-21) rather than guessed.
* It does not call a backup "2nd string" where the club chart is not ordered.
* It does not touch data/**, tools/build.py, tools/verify.py or tools/pages.py
  numbers. The depth data is a separate input with its own sources.

Sources: each club's official depth chart page, plus nfl.com/injuries/ for the
official Week 10 injury report. Retrieval date 2026-11-14.

Usage:  python3 tools/depth.py            # validate + write the CSV
        python3 tools/depth.py --check    # validate only (CI gate)
"""
import csv
import os
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT_CSV = os.path.join(DATA, "depth-wk11-2026.csv")
INJ_CSV = os.path.join(DATA, "injuries-wk10-2026.csv")
STAND_CSV = os.path.join(DATA, "standings-wk10-2026.csv")
RETRIEVED = "2026-11-14"
# Clubs whose chart was read again, live, in a later session. The retrieval stamp
# is per club so a re-read row is never dated with the original capture.
RETRIEVED_BY_CLUB = {
    # Seattle Seahawks, https://www.seahawks.com/team/depth-chart/ - read 2026-11-19.
    # The chart is unchanged from the 2026-11-14 transcription; the only correction
    # is that the first WR cell publishes Cooper Kupp AND Rashid Shaheed together.
    "SEA": "2026-11-19",
    # Washington Commanders, https://www.commanders.com/team/depth-chart - read
    # 2026-11-19. The chart has changed since 2026-11-14 and now publishes an
    # empty cell (the third WR row names Antonio Williams and leaves cell 2
    # blank), so the rows below are the 2026-11-19 chart, not the 2026-11-14 one.
    "WAS": "2026-11-19",
}

# ---------------------------------------------------------------------------
# Official club depth-chart pages. Every URL below was fetched from the club's
# own official domain and returned an ordered depth chart.
# ---------------------------------------------------------------------------
CHART_URL = {
    "ARI": "https://www.azcardinals.com/team/depth-chart",
    "ATL": "https://www.atlantafalcons.com/team/depth-chart",
    "BAL": "https://www.baltimoreravens.com/team/depth-chart",
    "BUF": "https://www.buffalobills.com/team/depth-chart",
    "CAR": "https://www.panthers.com/team/depth-chart",
    "CHI": "https://www.chicagobears.com/team/depth-chart",
    "CIN": "https://www.bengals.com/team/depth-chart",
    "CLE": "https://www.clevelandbrowns.com/team/depth-chart",
    "DAL": "https://www.dallascowboys.com/team/depth-chart",
    "DEN": "https://www.denverbroncos.com/team/depth-chart",
    "DET": "https://www.detroitlions.com/team/depth-chart",
    "GB": "https://www.packers.com/team/depth-chart",
    # Houston publishes the chart as a single image: no machine-readable order.
    "HOU": "",
    "IND": "https://www.colts.com/team/depth-chart",
    "JAX": "https://www.jaguars.com/team/depth-chart",
    "KC": "https://www.chiefs.com/team/depth-chart",
    "LAC": "https://www.chargers.com/team/depth-chart",
    "LAR": "https://www.therams.com/team/depth-chart",
    "LV": "https://www.raiders.com/team/depth-chart",
    "MIA": "https://www.miamidolphins.com/team/depth-chart",
    "MIN": "https://www.vikings.com/team/depth-chart",
    "NE": "https://www.patriots.com/team/depth-chart",
    "NO": "https://www.neworleanssaints.com/team/depth-chart",
    "NYG": "https://www.giants.com/team/depth-chart",
    "NYJ": "https://www.newyorkjets.com/team/depth-chart",
    "PHI": "https://www.philadelphiaeagles.com/team/depth-chart",
    "PIT": "https://www.steelers.com/team/depth-chart/",
    "SEA": "https://www.seahawks.com/team/depth-chart/",
    "SF": "https://www.49ers.com/team/depth-chart",
    "TB": "https://www.buccaneers.com/team/depth-chart",
    "TEN": "https://www.tennesseetitans.com/team/depth-chart",
    "WAS": "https://www.commanders.com/team/depth-chart",
}

# The date the club stamps on its own chart, where it stamps one. Blank = the
# club publishes no date, which is recorded as-is rather than assumed.
CHART_DATE = {
    "TEN": "2026-11-10", "GB": "2026-11-10", "SF": "2026-11-10",
    "LV": "2026-11-10", "CHI": "2026-10-31",
}

# UNIT / position row -> depth order exactly as published (first = starter).
# Transcribed 2026-11-14. Where a club lists two co-starters in the first cell,
# both are recorded with the same depth position, because that is what the club
# prints - the tool never breaks a tie the club did not break.
CHARTS = OrderedDict()

CHARTS["ARI"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Reggie Virgil", "Harrison Wallace III"]),
        ("LT", ["Jayden Williams", "Jedrick Wills"]),
        ("LG", ["Isaac Seumalo", "Hayden Conner"]),
        ("C", ["Hjalte Froholdt", "Kingsley Eguakun"]),
        ("RG", ["Isaiah Adams", "Jon Gaines II"]),
        ("RT", ["Elijah Wilkinson", "Josh Fryar", "Albert Reese"]),
        ("TE", ["Trey McBride"]),
        ("TE2", ["Elijah Higgins", "Teagan Quitoriano"]),
        ("WR2", ["Simi Fehoko", "Devin Duvernay"]),
        ("QB", ["Carson Beck", "Josh Johnson", "Joey Aguilar"]),
        ("RB", ["Tyler Allgeier", "Bam Knight", "Evan Hull"]),
    ],
    "def": [
        ("DT", ["Dante Stills", "Darius Robinson"]),
        ("NT", ["Roy Lopez", "Andrew Billings"]),
        ("DT2", ["Walter Nolen III", "L.J. Collier"]),
        ("OLB", ["Josh Sweat", "Jordan Burch", "Eku Leota"]),
        ("ILB", ["Jack Gibbens", "Karson Sharar"]),
        ("ILB2", ["Mack Wilson Sr.", "Cody Simon"]),
        ("OLB2", ["Zaven Collins", "Baron Browning"]),
        ("CB", ["Denzel Burke", "Starling Thomas V"]),
        ("CB2", ["Max Melton", "Kei'Trel Clark"]),
        ("CB3", ["Kalen King", "Garrett Williams"]),
        ("S", ["Andrew Wingard", "Kitan Crawford"]),
        ("S2", ["Budda Baker", "Dadrion Taylor-Demerson"]),
    ],
}
CHARTS["ATL"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Drake London", "Chris Blair"]),
        ("LT", ["Jake Matthews", "Cameron Williams"]),
        ("LG", ["Matthew Bergeron", "Kyle Hinton"]),
        ("C", ["Corey Levin"]),
        ("RG", ["Chris Lindstrom", "Andrew Vorhees"]),
        ("RT", ["Jawaan Taylor", "Ethan Onianwa"]),
        ("TE", ["Kyle Pitts Sr.", "Austin Hooper"]),
        ("TE2", ["Charlie Woerner", "Nick Muse"]),
        ("RB", ["Bijan Robinson", "Khalil Herbert"]),
        ("QB", ["Michael Penix Jr.", "Tua Tagovailoa", "Andy Dalton", "Jack Strand"]),
        ("WR2", ["Olamide Zaccheaus", "Zachariah Branch"]),
        ("WR3", ["Jahan Dotson", "Beaux Collins"]),
    ],
    "def": [
        ("DE", ["Cameron Thomas", "Za'Darius Smith", "Charles Snowden"]),
        ("DL", ["Maason Smith", "Gervon Dexter Sr."]),
        ("DL2", ["LaCale London", "Zach Harrison"]),
        ("DE2", ["Brandon Dorlus", "Yasir Abdullah", "James Pearce Jr."]),
        ("ILB", ["Divine Deablo", "Christian Harris", "Josh Woods"]),
        ("ILB2", ["Kendal Daniels", "Harold Perkins Jr."]),
        ("CB", ["A.J. Terrell Jr.", "Robert Longerbeam"]),
        ("S", ["DeMarcco Hellams"]),
        ("S2", ["Xavier Watts", "Sydney Brown"]),
        ("CB2", ["C.J. Henderson", "Mike Hughes", "Mike Ford Jr"]),
        ("NB", ["Avieon Terrell", "Billy Bowman Jr."]),
    ],
}
CHARTS["BAL"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Zay Flowers", "Devontez Walker", "Elijah Sarratt"]),
        ("WR2", ["Rashod Bateman", "Ja'Kobi Lane", "LaJohntay Wester"]),
        ("LT", ["Ronnie Stanley", "Carson Vinson"]),
        ("LG", ["John Simpson", "Ryan Neuzil"]),
        ("C", ["Cam Jurgens", "Ryan Neuzil"]),
        ("RG", ["Vega Ioane", "Emery Jones Jr."]),
        ("RT", ["Roger Rosengarten", "Carson Vinson"]),
        ("TE", ["Mark Andrews", "Josh Cuevas"]),
        ("TE2", ["Matt Hibner"]),
        ("QB", ["Jacoby Brissett", "Joe Fagnano", "Kedon Slovis"]),
        ("RB", ["Derrick Henry", "Justice Hill", "Rasheen Ali"]),
    ],
    "def": [
        ("DT", ["Nnamdi Madubuike", "Broderick Washington Jr."]),
        ("NT", ["Travis Jones", "John Jenkins"]),
        ("DE", ["Calais Campbell", "Aeneas Peebles"]),
        ("RUSH", ["Trey Hendrickson", "Mike Green"]),
        ("MLB", ["Roquan Smith", "Jay Higgins IV"]),
        ("WLB", ["Trenton Simpson", "Teddye Buchanan"]),
        ("SAM", ["Mike Green", "Zion Young", "Ethan Burke"]),
        ("CB", ["Marlon Humphrey", "Chidobe Awuzie"]),
        ("DB", ["Kyle Hamilton", "Keyon Martin", "Chandler Rivers"]),
        ("SS", ["Jaylinn Hawkins", "Keondre Jackson"]),
        ("FS", ["Malaki Starks", "K'Von Wallace"]),
        ("CB2", ["Nate Wiggins", "T.J. Tampa Jr."]),
    ],
}
CHARTS["BUF"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["DJ Moore", "Skyler Bell"]),
        ("LT", ["Dion Dawkins", "Jude Bowry"]),
        ("LG", ["Alec Anderson", "Austin Corbett"]),
        ("C", ["Connor McGovern", "Lloyd Cushenberry"]),
        ("RG", ["O'Cyrus Torrence", "Ar'maj Reed-Adams"]),
        ("RT", ["Spencer Brown", "Tylan Grable"]),
        ("TE", ["Dalton Kincaid", "Dawson Knox", "Jackson Hawes", "Keleki Latu"]),
        ("QB", ["Josh Allen", "Kyle Allen"]),
        ("RB", ["James Cook III", "Ray Davis", "Ty Johnson"]),
        ("WR2", ["Khalil Shakir", "Greg Dortch"]),
        ("WR3", ["Keon Coleman"]),
    ],
    "def": [
        ("DL", ["Ed Oliver", "DeWayne Carter"]),
        ("DL2", ["Deone Walker", "Greg Gaines"]),
        ("DL3", ["T.J. Sanders", "Landon Jackson"]),
        ("OLB", ["Greg Rousseau", "Michael Hoecht", "Mike Danna"]),
        ("OLB2", ["Bradley Chubb", "TJ Parker", "Javon Solomon"]),
        ("ILB", ["Dorian Williams", "Kaleb Elarms-Orr"]),
        ("ILB2", ["Terrel Bernard", "Joe Andreessen"]),
        ("CB", ["Christian Benford", "Dee Alford"]),
        ("CB2", ["Davison Igbinosun", "Maxwell Hairston"]),
        ("NCB", ["Dee Alford", "Te'Cory Couch"]),
        ("S", ["Damar Hamlin", "Sam Franklin Jr."]),
        ("S2", ["Cole Bishop", "Jalon Kilgore"]),
    ],
}
CHARTS["CAR"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Tetairoa McMillan", "Brycen Tremayne"]),
        ("WR2", ["Jalen Coker"]),
        ("LT", ["Rasheed Walker", "Stone Forsythe"]),
        ("LG", ["Damien Lewis", "Corey Bullock"]),
        ("C", ["Luke Fortner", "Sam Hecht"]),
        ("RG", ["Robert Hunt", "Torricelli Simpkins III"]),
        ("RT", ["Monroe Freeling", "Stone Forsythe"]),
        ("TE", ["Tommy Tremble", "Mitchell Evans", "Darren Waller",
                "Ja'Tavion Sanders", "Feleipe Franks"]),
        ("WR3", ["John Metchie III"]),
        ("QB", ["Bryce Young", "Kenny Pickett", "Haynes King"]),
        ("RB", ["Chuba Hubbard", "Trevor Etienne", "AJ Dillon", "Anthony Tyus III"]),
    ],
    "def": [
        ("DL", ["Bobby Brown III", "TeRah Edwards"]),
        ("DL2", ["Tershawn Wharton", "Lee Hunter"]),
        ("DL3", ["Derrick Brown", "Aaron Hall"]),
        ("OLB", ["Patrick Jones II", "Trevis Gipson", "Nick Hampton"]),
        ("LB", ["Devin Lloyd", "Jackson Kuwatch", "Bam Martin-Scott"]),
        ("LB2", ["Bobby Okereke", "Tyrel Dodson"]),
        ("OLB2", ["Jaelan Phillips", "Princely Umanmielen"]),
        ("CB", ["Chau Smith-Wade", "Malcolm DeWalt IV"]),
        ("CB2", ["Will Lee III"]),
        ("S", ["Tre'von Moehrig", "Zakee Wheatley"]),
        ("S2", ["Nick Scott", "Lathan Ransom", "Isaiah Simmons"]),
    ],
}
CHARTS["CHI"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Rome Odunze", "Zavion Thomas"]),
        ("LT", ["Theo Benedet", "Ozzy Trapilo"]),
        ("LG", ["Joe Thuney", "Jordan McFadden"]),
        ("C", ["Garrett Bradbury", "Logan Jones"]),
        ("RG", ["Jonah Jackson", "Luke Newman"]),
        ("RT", ["Darnell Wright", "Ozzy Trapilo"]),
        ("TE", ["Colston Loveland", "Sam Roush"]),
        ("WR2", ["Kalif Raymond"]),
        ("WR3", ["Luther Burden III", "Jahdae Walker"]),
        ("QB", ["Caleb Williams", "Tyson Bagent", "Case Keenum"]),
        ("RB", ["D'Andre Swift", "Kyle Monangai", "Roschon Johnson"]),
    ],
    "def": [
        ("DL", ["Austin Booker", "Shemar Turner", "James Lynch"]),
        ("DL2", ["Grady Jarrett", "Neville Gallimore", "Jayden Loving"]),
        ("DL3", ["Jeffery Simmons", "Kentavius Street", "Jordan van den Berg"]),
        ("DL4", ["Montez Sweat", "Daniel Hardy"]),
        ("LB", ["T.J. Edwards", "D'Marco Jackson", "Keyshaun Elliott"]),
        ("LB2", ["Devin Bush", "Noah Sewell", "Jack Sanborn"]),
        ("S", ["Dillon Thieneman", "Elijah Hicks"]),
        ("S2", ["Cam Lewis", "Skyler Thomas"]),
        ("DB", ["Kyler Gordon", "Malik Muhammad II"]),
        ("CB", ["Tyrique Stevenson Sr.", "Clark Phillips III"]),
        ("CB2", ["Jaylon Johnson", "Josh Blackwell"]),
    ],
}
CHARTS["CIN"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Ja'Marr Chase", "Mitch Tinsley"]),
        ("LOT", ["Orlando Brown Jr.", "Javon Foster"]),
        ("LG", ["Dylan Fairchild", "Jalen Rivers"]),
        ("C", ["Ted Karras", "Connor Lew"]),
        ("RG", ["Dalton Risner", "Jacob Bayer"]),
        ("ROT", ["Amarius Mims", "Myles Hinton"]),
        ("TE", ["Drew Sample", "Mike Gesicki", "Jack Endries", "Cam Grandy"]),
        ("WR2", ["Dohnte Meyers"]),
        ("WR3", ["Tee Higgins", "Colbie Young"]),
        ("QB", ["Joe Burrow", "Joe Flacco"]),
        ("HB", ["Chase Brown", "Samaje Perine", "Tahj Brooks"]),
    ],
    "def": [
        ("LDE", ["Myles Murphy", "Shemar Stewart", "Cedric Johnson"]),
        ("NT", ["Dexter Lawrence II", "T.J. Slaton Jr."]),
        ("DT", ["Jonathan Allen", "B.J. Hill", "Kris Jenkins Jr.", "Landon Robinson"]),
        ("RDE", ["Boye Mafe", "Cashius Howell"]),
        ("LB", ["Barrett Carter", "Joe Giles-Harris", "Jack Kiser"]),
        ("LB2", ["Demetrius Knight Jr.", "Oren Burks"]),
        ("NCB", ["Dax Hill", "Josh Newton"]),
        ("CB", ["DJ Ivey", "Tacario Davis"]),
        ("CB2", ["DJ Turner II", "Tacario Davis"]),
        ("S", ["Bryan Cook", "PJ Jules"]),
        ("S2", ["Jordan Battle", "Kyle Dugger", "Russ Yeast"]),
    ],
}
CHARTS["CLE"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Jerry Jeudy", "Tylan Wallace"]),
        ("LT", ["Spencer Fano"]),
        ("LG", ["Zion Johnson", "Zak Zinter"]),
        ("C", ["Elgton Jenkins", "Luke Wypler", "Parker Brailsford"]),
        ("RG", ["Austin Barber"]),
        ("RT", ["Tytus Howard", "Dawand Jones"]),
        ("WR2", ["Denzel Boston", "Malachi Corley"]),
        ("QB", ["Deshaun Watson", "Shedeur Sanders", "Dillon Gabriel", "Taylen Green"]),
        ("RB", ["Quinshon Judkins", "Dylan Sampson", "Michael Burton",
                "Jaleel McLaughlin"]),
        ("TE", ["Harold Fannin Jr.", "Blake Whiteheart"]),
        ("WR3", ["KC Concepcion Jr.", "Isaiah Bond"]),
    ],
    "def": [
        ("LDE", ["Jared Verse", "Sam Williams"]),
        ("LDT", ["Maliek Collins", "Mike Hall Jr.", "Sam Kamara"]),
        ("RDT", ["Mason Graham", "Adin Huntington"]),
        ("RDE", ["Isaiah McGuire", "Derek Barnett"]),
        ("WILL", ["Carson Schwesinger"]),
        ("MIKE", ["Quincy Williams", "Justin Jefferson"]),
        ("SAM", ["Easton Mascarenas-Arnold", "Winston Reid"]),
        ("CB", ["Tyson Campbell", "Myles Harden", "Noah Igbinoghene"]),
        ("CB2", ["Denzel Ward", "Mekhi Blackmon", "Toriano Pride Jr."]),
        ("SS", ["Grant Delpit", "Emmanuel McNeil-Warren", "Daniel Thomas"]),
        ("FS", ["Ronnie Hickman", "Donovan McMillon"]),
    ],
}
CHARTS["DAL"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["George Pickens", "Camden Brown"]),
        ("LT", ["Tyler Guyton", "Drew Shelton"]),
        ("LG", ["Tyler Smith", "T.J. Bass"]),
        ("C", ["Cooper Beebe", "T.J. Bass"]),
        ("RG", ["Tyler Booker", "Ajani Cornelius"]),
        ("RT", ["Terence Steele", "Broderick Jones"]),
        ("TE", ["Jake Ferguson", "Brevyn Spann-Ford", "Luke Schoonmaker"]),
        ("WR2", ["Ryan Flournoy", "KaVontae Turpin"]),
        ("WR3", ["CeeDee Lamb", "Jonathan Mingo"]),
        ("QB", ["Dak Prescott", "Sam Howell"]),
        ("RB", ["Javonte Williams", "Tyler Goodson"]),
        ("FB", ["Hunter Luepke"]),
    ],
    "def": [
        ("DT", ["Otito Ogbonnia", "Elijah Garcia"]),
        ("DT2", ["Kenny Clark"]),
        ("DT3", ["Quinnen Williams", "LT Overton"]),
        ("OLB", ["Donovan Ezeiruaku", "James Houston", "Tyrus Wheat"]),
        ("LB", ["DeMarvion Overshown", "Dee Winters", "Justin Barron"]),
        ("LB2", ["Shemar James", "Jaishawn Barham"]),
        ("OLB2", ["Rashan Gary", "Von Miller", "Marist Liufau"]),
        ("CB", ["Joey Porter Jr.", "Shavon Revel Jr.", "Ameer Speed"]),
        ("DB", ["Caleb Downs"]),
        ("CB2", ["DaRon Bland", "Cobie Durant"]),
        ("S", ["P.J. Locke", "Markquese Bell", "Juanyeh Thomas"]),
        ("S2", ["Malik Hooker", "Alijah Clark"]),
    ],
}
CHARTS["DEN"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Marvin Mims Jr.", "Troy Franklin"]),
        ("WR2", ["Jaylen Waddle", "Lil'Jordan Humphrey"]),
        ("LT", ["Garett Bolles", "Matt Peart"]),
        ("LG", ["Ben Powers", "Kage Casey"]),
        ("C", ["Luke Wattenberg", "Alex Forsyth"]),
        ("RG", ["Quinn Meinerz", "Kage Casey"]),
        ("RT", ["Mike McGlinchey", "Alex Palczewski"]),
        ("TE", ["Evan Engram", "Adam Trautman", "Nate Adkins", "Dallen Bentley"]),
        ("WR3", ["Courtland Sutton"]),
        ("RB", ["J.K. Dobbins", "Jonah Coleman"]),
        ("FB", ["Adam Prentice"]),
        ("QB", ["Bo Nix", "Jarrett Stidham", "Sam Ehlinger"]),
    ],
    "def": [
        ("DE", ["Zach Allen", "Jordan Jackson", "Tyler Onyedim"]),
        ("NT", ["D.J. Jones", "Sai'vion Jones"]),
        ("DE2", ["Malcolm Roach", "Eyioma Uwazurike"]),
        ("SLB", ["Nik Bonitto", "Que Robinson"]),
        ("WLB", ["Jonathon Cooper", "Dondrea Tillman"]),
        ("ILB", ["Alex Singleton", "Jordan Turner"]),
        ("ILB2", ["Justin Strnad", "Karene Reid"]),
        ("LCB", ["Pat Surtain II", "Jahdae Barron"]),
        ("RCB", ["Riley Moss", "Kris Abrams-Draine"]),
        ("NCB", ["Ja'Quan McMillian", "Jahdae Barron"]),
        ("S", ["Talanoa Hufanga", "JL Skinner", "Tycen Anderson"]),
        ("S2", ["Brandon Jones", "Devon Key", "Taylor Rapp"]),
    ],
}
CHARTS["DET"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Jameson Williams"]),
        ("WR2", ["Amon-Ra St. Brown", "DeAndre Carter"]),
        ("LT", ["Penei Sewell"]),
        ("LG", ["Christian Mahogany", "Miles Frazier"]),
        ("C", ["Cade Mays", "Juice Scruggs"]),
        ("RG", ["Tate Ratledge", "Seth McLaughlin"]),
        ("RT", ["Blake Miller", "Larry Borom"]),
        ("TE", ["Sam LaPorta", "Brock Wright", "Tyler Conklin", "Jackson Meeks"]),
        ("WR3", ["Isaac TeSlaa", "Tay Martin"]),
        ("QB", ["Jared Goff", "Joshua Dobbs"]),
        ("RB", ["Jahmyr Gibbs", "Sione Vaki", "Jacob Saylors"]),
    ],
    "def": [
        ("EDGE", ["Aidan Hutchinson", "Derrick Moore", "Eric O'Neill"]),
        ("DL", ["Alim McNeill", "Skyler Gill-Howard", "Mekhi Wingo"]),
        ("DL2", ["Tyleik Williams", "Levi Onwuzurike"]),
        ("EDGE2", ["DJ Wonnum", "Tyler Lacy", "Ahmed Hassanein"]),
        ("LB", ["Derrick Barnes", "Joe Bachie"]),
        ("LB2", ["Malcolm Rodriguez", "K.J. Britt"]),
        ("LB3", ["Trevor Nowaske", "Amen Ogbongbemiga"]),
        ("CB", ["D.J. Reed", "Rock Ya-Sin", "Khalil Dorsey", "Nick Whiteside"]),
        ("CB2", ["Roger McCreary", "Ennis Rakestraw Jr.", "Keith Abney II"]),
        ("S", ["Chuck Clark"]),
        ("S2", ["Brian Branch", "Christian Izien"]),
    ],
}
CHARTS["GB"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Christian Watson", "Bo Melton"]),
        ("WR2", ["Matthew Golden", "J. Michael Sturdivant"]),
        ("LT", ["Jordan Morgan", "John Williams"]),
        ("LG", ["Aaron Banks", "Travis Glover", "Donovan Jennings"]),
        ("C", ["Sean Rhyan", "Jager Burton"]),
        ("RG", ["Laken Tomlinson", "Kevin Zeitler"]),
        ("RT", ["Anthony Belton", "Mekhi Becton Sr."]),
        ("TE", ["Tucker Kraft", "Jonnu Smith", "Mark Redman", "Josh Whyle"]),
        ("WR3", ["Savion Williams", "Coleman Owen"]),
        ("QB", ["Jordan Love", "Tyrod Taylor"]),
        ("RB", ["Josh Jacobs", "MarShawn Lloyd", "Pierre Strong Jr.", "Kaleb Johnson"]),
    ],
    "def": [
        ("DT", ["Karl Brooks", "Jordon Riley", "Anthony Campbell"]),
        ("DT2", ["Devonte Wyatt", "Chris McClellan"]),
        ("EDGE", ["Lukas Van Ness", "Brenton Cox Jr"]),
        ("LB", ["Zaire Franklin", "Ty'Ron Hopper", "Kristian Welch"]),
        ("LB2", ["Isaiah McDuffie", "Nick Niemann"]),
        ("EDGE2", ["Barryn Sorrell", "Dani Dennis-Sutton"]),
        ("CB", ["Keisean Nixon", "Carrington Valentine"]),
        ("CB2", ["Brandon Cisse", "Benjamin St-Juste"]),
        ("S", ["Xavier McKinney", "Kitan Oladapo"]),
        ("S2", ["Evan Williams", "Kitan Oladapo"]),
        ("NB", ["Javon Bullard", "Kamal Hadden"]),
    ],
}
CHARTS["HOU"] = {"unit": "OFF", "rows": [], "def": []}
CHARTS["IND"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Laquon Treadwell", "Nick Westbrook-Ikhine"]),
        ("LT", ["Bernhard Raimann", "Charlie Heck"]),
        ("LG", ["Jalen Farmer", "Dalton Tucker"]),
        ("C", ["Tanor Bortolini", "Sedrick Van Pran-Granger"]),
        ("RG", ["Matt Goncalves"]),
        ("RT", ["Jalen Travis", "Luke Tenuta"]),
        ("TE", ["Tyler Warren", "Mo Alie-Cox", "Drew Ogletree", "Will Mallory",
                "Pharaoh Brown"]),
        ("WR2", ["Anthony Gould"]),
        ("WR3", ["Ashton Dulin", "Deion Burks"]),
        ("QB", ["Daniel Jones", "Anthony Richardson Sr.", "Riley Leonard"]),
        ("RB", ["Jonathan Taylor", "Seth McGowan", "DJ Giddens"]),
    ],
    "def": [
        ("DE", ["Jaylahn Tuimoloau", "George Gumbs Jr."]),
        ("DT", ["Adetomiwa Adebawore", "Kevin Givens"]),
        ("NT", ["Grover Stewart", "Jerry Tillery", "Tim Smith"]),
        ("DE2", ["Laiatu Latu", "Caden Curry"]),
        ("WLB", ["Jaylon Carlies", "Bryce Boettcher", "Tahj Chambers"]),
        ("MLB", ["Akeem Davis-Gaither", "CJ Allen", "Austin Ajiake"]),
        ("CB", ["Charvarius Ward", "Kenneth Harris"]),
        ("FS", ["Cam Bynum", "Jonathan Owens"]),
        ("SS", ["AJ Haulcy", "Hunter Wohler"]),
        ("N", ["Justin Walley", "Kapena Gushiken"]),
        ("CB2", ["Sauce Gardner"]),
    ],
}
CHARTS["JAX"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Parker Washington", "Josh Cameron"]),
        ("RT", ["Cole Van Lanen"]),
        ("RG", ["Ezra Cleveland", "Wyatt Milum"]),
        ("C", ["Robert Hainsey", "Jonah Monheim"]),
        ("LG", ["Emmanuel Pregnon", "Daniel Faalele"]),
        ("LT", ["Walker Little"]),
        ("TE", ["Brenton Strange", "Nate Boerkircher", "Quintin Morris",
                "Tanner Koziol"]),
        ("QB", ["Trevor Lawrence", "Quinn Ewers"]),
        ("RB", ["Bhayshul Tuten", "Chris Rodriguez Jr.", "LeQuint Allen Jr.",
                "Ameer Abdullah"]),
        ("WR2", ["Brian Thomas Jr.", "Travis Hunter"]),
        ("WR3", ["Jakobi Meyers", "CJ Williams"]),
    ],
    "def": [
        ("NT", ["Jordan Davis", "Davon Godchaux", "Matt Dickerson"]),
        ("DT", ["Arik Armstead", "Ruke Orhorhoro", "Albert Regis"]),
        ("DE", ["Josh Hines-Allen", "Bryan Thomas Jr."]),
        ("DE2", ["Travon Walker", "Danny Striggow", "Wesley Williams"]),
        ("LB", ["Foyesade Oluokun", "Jahlani Tavai"]),
        ("LB2", ["Ventrell Miller", "Branson Combs"]),
        ("LB3", ["Dennis Gardeck", "Jalen McLeod"]),
        ("CB", ["Montaric Brown", "Jaylon Jones"]),
        ("CB2", ["Jourdan Lewis", "Jarrian Jones"]),
        ("CB3", ["Travis Hunter"]),
        ("S", ["Jessie Bates III", "Kaevon Merriweather", "Rayuan Lane III"]),
        ("S2", ["Antonio Johnson", "Jalen Huskey"]),
    ],
}
CHARTS["KC"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Rashee Rice", "Jalen Royals", "Andrew Armstrong"]),
        ("LT", ["Kahlil Benson", "Diego Pounds"]),
        ("LG", ["Kingsley Suamataia", "Joshua Ezeudu"]),
        ("C", ["Creed Humphrey", "Hunter Nourzad"]),
        ("RG", ["Trey Smith", "Mike Caliendo"]),
        ("RT", ["Jaylon Moore", "Joshua Ezeudu"]),
        ("TE", ["Travis Kelce", "Noah Gray", "Jared Wiley", "Jake Briningstool"]),
        ("QB", ["Patrick Mahomes", "Justin Fields", "Garrett Nussmeier"]),
        ("RB", ["Kenneth Walker", "Emmett Johnson", "Jaydn Ott"]),
        ("FB", ["Ben VanSumeren"]),
        ("WR2", ["Xavier Worthy", "Cyrus Allen", "Josh Downs"]),
    ],
    "def": [
        ("DE", ["Felix Anudike-Uzomah", "Ashton Gillotte"]),
        ("DT", ["Chris Jones", "Peter Woods", "Marcus Harris"]),
        ("DT2", ["Khyiris Tonga", "Bryson Eason"]),
        ("DE2", ["George Karlaftis", "R Mason Thomas"]),
        ("LB", ["Jack Cochrane", "Cooper McDonald"]),
        ("LB2", ["Nick Bolton", "Jack Cochrane"]),
        ("LB3", ["Drue Tranquill", "Jeffrey Bassa"]),
        ("CB", ["Nohl Williams", "Jadon Canady"]),
        ("CB2", ["Mansoor Delane", "Kristian Fulton", "Melvin Smith"]),
        ("S", ["Alohi Gilman", "Chris Roland-Wallace"]),
        ("S2", ["Chamarri Conner", "Jaden Hicks", "Xavier Nwankpa"]),
    ],
}
CHARTS["LAC"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Ladd McConkey", "Tre' Harris", "Derius Davis", "Theo Wease Jr."]),
        ("LT", ["Travis Burke", "Branson Taylor"]),
        ("LG", ["Kayode Awosika", "Logan Taylor"]),
        ("C", ["Jake Slaughter", "Jacob Spomer"]),
        ("RG", ["Cole Strange", "Logan Taylor"]),
        ("RT", ["Joe Alt", "Alex Harkey"]),
        ("TE", ["Charlie Kolar", "Oronde Gadsden"]),
        ("WR2", ["Quentin Johnston", "Brenen Thompson"]),
        ("QB", ["Justin Herbert", "DJ Uiagalelei"]),
        ("FB", ["Alec Ingold", "Scott Matlock"]),
        ("RB", ["Omarion Hampton", "Keaton Mitchell", "Kimani Vidal"]),
    ],
    "def": [
        ("EDGE", ["Khalil Mack", "Akheem Mesidor"]),
        ("DL", ["Jamaree Caldwell", "Nick Barrett"]),
        ("DL2", ["Dalvin Tomlinson", "Justin Eboigbe"]),
        ("DL3", ["Teair Tart"]),
        ("EDGE2", ["Tuli Tuipulotu", "Bud Dupree"]),
        ("LB", ["Daiyan Henley", "Troy Dye"]),
        ("LB2", ["Del'Shawn Phillips", "Marlowe Wax"]),
        ("CB", ["Tarheeb Still", "Cam Hart", "Deane Leonard"]),
        ("S", ["Derwin James Jr.", "Tony Jefferson", "RJ Mickens"]),
        ("S2", ["Elijah Molden", "Genesis Smith", "Kendall Williamson"]),
        ("CB2", ["Donte Jackson", "Cam Hart", "Rodney Shelley"]),
    ],
}
CHARTS["LAR"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Konata Mumpfield", "CJ Daniels"]),
        ("TE", ["Davis Allen", "Tyler Higbee"]),
        ("LT", ["Alaric Jackson", "David Quessenberry"]),
        ("LG", ["Steve Avila", "Bill Murray"]),
        ("C", ["Coleman Shelton", "Dylan McMahon"]),
        ("RG", ["Kevin Dotson", "Beaux Limmer"]),
        ("RT", ["Warren McClendon Jr.", "Keagen Trost"]),
        ("TE2", ["Colby Parkinson", "Max Klare"]),
        ("WR2", ["Puka Nacua", "Jordan Whittington", "Tutu Atwell"]),
        ("QB", ["Matthew Stafford", "Stetson Bennett IV", "Ty Simpson"]),
        ("RB", ["Kyren Williams", "Blake Corum", "Ronnie Rivers"]),
    ],
    "def": [
        ("OLB", ["Byron Young", "Wesley Bailey"]),
        ("DE", ["Braden Fiske"]),
        ("NT", ["Tyler Davis", "Ty Hamilton"]),
        ("DE2", ["Aaron Donald", "Larrell Murchison"]),
        ("OLB2", ["Myles Garrett", "Josaiah Stewart", "Desjuan Johnson"]),
        ("ILB", ["Omar Speights", "Grant Stuard"]),
        ("ILB2", ["Nate Landman", "Shaun Dolac"]),
        ("CB", ["Trent McDuffie", "Cam Lampkin"]),
        ("S", ["Quentin Lake", "Kamren Kinchens", "Maximus Pulley"]),
        ("S2", ["Kam Curl", "Jaylen McCollough"]),
        ("CB2", ["Emmanuel Forbes Jr.", "Josh Wallace"]),
    ],
}
CHARTS["LV"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Jalen Nailor", "Malik Benson", "Dont'e Thornton Jr."]),
        ("LT", ["Kolton Miller", "Charles Grant"]),
        ("LG", ["Spencer Burford", "Bryce Cabeldue"]),
        ("C", ["Tyler Linderbaum"]),
        ("RG", ["Jackson Powers-Johnson", "Caleb Rogers"]),
        ("RT", ["DJ Glaze", "Trey Zuhn III"]),
        ("TE", ["Brock Bowers", "Michael Mayer", "Ian Thomas"]),
        ("WR2", ["Tre Tucker", "Jack Bech", "Dareke Young", "Cody White"]),
        ("QB", ["Fernando Mendoza", "Aidan O'Connell"]),
        ("RB", ["Ashton Jeanty", "Mike Washington Jr.", "Dylan Laube"]),
        ("FB", ["Connor Heyward"]),
    ],
    "def": [
        ("DE", ["Maxx Crosby", "Malcolm Koonce"]),
        ("DT", ["Tonka Hemingway", "JJ Pegues", "Tim Keenan III"]),
        ("DT2", ["Adam Butler", "Folorunso Fatukasi", "Thomas Booker IV"]),
        ("EDGE", ["Kwity Paye"]),
        ("LB", ["Nakobe Dean", "Tommy Eichenberg", "Segun Olubi"]),
        ("LB2", ["Quay Walker", "Cody Lindenberg"]),
        ("CB", ["Eric Stokes", "Jermod McCoy", "Darrell Luter Jr."]),
        ("CB2", ["Darien Porter", "Hezekiah Masses"]),
        ("CB3", ["Taron Johnson"]),
        ("FS", ["Treydan Stukes", "Isaiah Pola-Mao", "Tristin McCollum"]),
        ("SS", ["Jeremy Chinn", "Dalton Johnson"]),
    ],
}
CHARTS["MIA"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Caleb Douglas", "Jared Wayne"]),
        ("LT", ["Patrick Paul", "Chukwuebuka Godrick"]),
        ("LG", ["Kadyn Proctor", "Jarrett Kingston"]),
        ("C", ["Aaron Brewer", "Andrew Meyer"]),
        ("RG", ["Jonah Savaiinaea", "Caedan Wallace", "Christian Haynes"]),
        ("RT", ["Austin Jackson", "Caedan Wallace"]),
        ("TE", ["Greg Dulcich", "Will Kacmarek", "Seydou Traore", "Justin Joly"]),
        ("FB", ["DJ Herman"]),
        ("RB", ["Ollie Gordon II", "Jaylen Wright", "Kaytron Allen"]),
        ("QB", ["Kyle McCord"]),
        ("WR2", ["Malik Washington", "Kevin Coleman Jr."]),
        ("WR3", ["Chris Bell", "Jalen Tolbert"]),
    ],
    "def": [
        ("DT", ["Jordan Phillips", "Kenneth Grant"]),
        ("DT2", ["Zeek Biggers"]),
        ("EDGE", ["Chop Robinson", "Malik Herring", "Rodney McGraw"]),
        ("EDGE2", ["Josh Uche", "Jamree Kromah"]),
        ("ILB", ["Jordyn Brooks", "Jackson Woodard", "Shaka Heyward"]),
        ("ILB2", ["Jacob Rodriguez", "Willie Gay Jr."]),
        ("NB", ["Chris Johnson"]),
        ("CB", ["JuJu Brents", "Marcellas Dial Jr."]),
        ("CB2", ["Jason Marshall Jr.", "Jaylin Simpson"]),
        ("S", ["Michael Taaffe", "Zayne Anderson"]),
        ("S2", ["Dante Trader Jr.", "Kyle Louis", "Julius Wood"]),
    ],
}
CHARTS["MIN"] = {
    "unit": "OFF",
    "rows": [
        ("QB", ["Kyler Murray", "Carson Wentz", "Max Brosmer", "Kirk Cousins"]),
        ("RB", ["Aaron Jones Sr.", "Jordan Mason", "Demond Claiborne", "DeeJay Dallas"]),
        ("FB", ["Max Bredeson"]),
        ("WR", ["Justin Jefferson", "Tai Felton"]),
        ("WR2", ["Jordan Addison"]),
        ("WR3", ["Jauan Jennings", "Myles Price"]),
        ("TE", ["T.J. Hockenson", "Gavin Bartholomew"]),
        ("LT", ["Christian Darrisaw", "Ryan Van Demark"]),
        ("LG", ["Joe Huber"]),
        ("C", ["Blake Brandel", "Michael Jurgens", "Nick Samac"]),
        ("RG", ["Will Fries"]),
        ("RT", ["Brian O'Neill", "Caleb Tiernan"]),
    ],
    "def": [
        ("OLB", ["Dallas Turner", "Kyle Van Noy", "Chaz Chambliss"]),
        ("DL", ["Jalen Redmond", "Caleb Banks"]),
        ("DL2", ["Levi Drake Rodriguez", "Domonique Orange"]),
        ("DL3", ["Tyrion Ingram-Dawkins", "Elijah Williams"]),
        ("OLB2", ["Andrew Van Ginkel", "Bo Richter"]),
        ("LB", ["Blake Cashman", "Ivan Pace Jr."]),
        ("LB2", ["Eric Wilson", "Jake Golday"]),
        ("CB", ["Isaiah Rodgers", "James Pierre", "Zemaiah Vaughn"]),
        ("CB2", ["Byron Murphy Jr.", "Charles Demmings"]),
        ("S", ["Harrison Smith", "Theo Jackson", "Jacob Thomas"]),
        ("S2", ["Joshua Metellus", "Jay Ward", "Jakobe Thomas"]),
    ],
}
CHARTS["NE"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["A.J. Brown", "Efton Chism III"]),
        ("LT", ["Will Campbell", "Dametrious Crownover", "Marcus Bryant"]),
        ("LG", ["Ben Brown", "Walter Rouse"]),
        ("C", ["Jared Wilson", "Ben Brown"]),
        ("RG", ["Matt Pryor", "Walter Rouse"]),
        ("RT", ["Morgan Moses", "Caleb Lomu"]),
        ("TE", ["Hunter Henry", "Eli Raridon", "Cameron Latu"]),
        ("WR2", ["DeMario Douglas", "Kyle Williams"]),
        ("WR3", ["Efton Chism III", "Kyle Williams"]),
        ("RB", ["Rhamondre Stevenson", "TreVeyon Henderson", "Corey Kiner",
                "Lan Larison"]),
        ("QB", ["Drake Maye", "Tommy DeVito", "Behren Morton"]),
    ],
    "def": [
        ("OLB", ["Dre'Mont Jones", "Gabe Jacas"]),
        ("DT", ["Christian Barmore", "Leonard Taylor III"]),
        ("DT2", ["Cory Durden", "DaQuan Jones"]),
        ("DT3", ["Milton Williams", "Joshua Farmer"]),
        ("OLB2", ["Elijah Ponder", "Gabe Jacas"]),
        ("LB", ["Robert Spillane", "Darius Muasau", "Erick Hunter"]),
        ("LB2", ["Christian Elliss", "Namdi Obiazor"]),
        ("CB", ["Carlton Davis III", "Channing Canada"]),
        ("S", ["Craig Woodson", "Mike Brown"]),
        ("S2", ["Kevin Byard III", "Jaylen Reed", "Brenden Schooler"]),
        ("CB2", ["Marcus Jones", "Charles Woods"]),
        ("CB3", ["Christian Gonzalez", "Karon Prunty"]),
    ],
}
CHARTS["NO"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Chris Olave", "Barion Brown"]),
        ("LT", ["Kelvin Banks Jr.", "Asim Richards"]),
        ("LG", ["David Edwards", "Jeremiah Wright"]),
        ("C", ["Erik McCoy", "William Sherman"]),
        ("RG", ["Cesar Ruiz", "Jeremiah Wright"]),
        ("RT", ["Taliese Fuaga", "Mason Murphy"]),
        ("TE", ["Juwan Johnson", "Noah Fant", "Oscar Delp"]),
        ("WR2", ["Devaughn Vele", "Bryce Lance"]),
        ("WR3", ["Jordyn Tyson", "Barion Brown"]),
        ("QB", ["Tyler Shough", "Spencer Rattler", "Zach Wilson"]),
        ("RB", ["Alvin Kamara", "Audric Estimé", "CJ Donaldson"]),
    ],
    "def": [
        ("EDGE", ["Chase Young", "Carl Granderson", "Anfernee Jennings"]),
        ("DL", ["Vernon Broughton", "John Ridgeway III"]),
        ("DL2", ["Khristian Boyd", "Christen Miller"]),
        ("DL3", ["Nathan Shepherd", "Colby Wooden"]),
        ("EDGE2", ["Cameron Jordan", "Tyree Wilson"]),
        ("LB", ["Pete Werner", "Chris Rumph II", "Isaiah Stalbird"]),
        ("LB2", ["Kaden Elliss", "Danny Stutsman", "Jaylan Ford"]),
        ("CB", ["Martin Emerson Jr.", "Quincy Riley"]),
        ("S", ["Julian Blackmon", "Jordan Howden"]),
        ("S2", ["Justin Reid", "Mike Reid"]),
        ("CB2", ["Kool-Aid McKinstry", "Decamerion Richardson"]),
        ("S3", ["Jonas Sanker", "Lorenzo Styles"]),
    ],
}
CHARTS["NYG"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Malik Nabers", "Malachi Fields", "Jalin Hyatt"]),
        ("WR2", ["Darnell Mooney", "Charlie Jones"]),
        ("LT", ["Andrew Thomas", "J.C. Davis"]),
        ("LG", ["Jon Runyan Jr.", "Aaron Stinnie", "Josh Sills"]),
        ("C", ["Bryan Hudson", "John Michael Schmitz Jr."]),
        ("RG", ["Francis \"Sisi\" Mauigoa", "Aaron Stinnie"]),
        ("RT", ["Jermaine Eluemunor", "Marcus Mbow"]),
        ("TE", ["Isaiah Likely", "Theo Johnson", "Chris Manhertz",
                "Thomas Fidone II"]),
        ("QB", ["J.J. McCarthy", "Jameis Winston"]),
        ("FB", ["Patrick Ricard"]),
        ("RB", ["Cam Skattebo", "Devin Singletary", "Gregory Desrosiers"]),
    ],
    "def": [
        ("DT", ["Shelby Harris", "Darius Alexander", "Bobby Jamison-Travis"]),
        ("NT", ["DJ Reader", "C.J. Okoye"]),
        ("DE", ["Darius Alexander"]),
        ("RUSH", ["Kayvon Thibodeaux", "Trace Ford"]),
        ("MLB", ["Micah McFadden", "Zaire Barnes"]),
        ("WLB", ["Arvell Reese", "Jack Kelly"]),
        ("SAM", ["Abdul Carter", "Kayvon Thibodeaux"]),
        ("CB", ["Deonte Banks", "Paulson Adebo", "Nikko Reed"]),
        ("SS", ["Tyler Nubin", "Jason Pinnock"]),
        ("FS", ["Jevón Holland", "Ar'Darius Washington", "Elijah Campbell"]),
        ("CB2", ["Greg Newsome II", "Colton Hood"]),
        ("NB", ["Dru Phillips", "Nic Jones"]),
    ],
}
CHARTS["NYJ"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Garrett Wilson", "Omar Cooper Jr.", "Isaiah Williams"]),
        ("TE", ["Jeremy Ruckert", "Jelani Woods"]),
        ("LT", ["Olu Fashanu"]),
        ("LG", ["Dylan Parham", "Jordan Meredith"]),
        ("C", ["Josh Myers", "Jordan Meredith"]),
        ("RG", ["Joe Tippmann", "Kohl Levao"]),
        ("RT", ["Armand Membou", "Chukwuma Okorafor"]),
        ("TE2", ["Mason Taylor", "Kenyon Sadiq"]),
        ("WR2", ["Adonai Mitchell", "Tim Patrick", "Malik McClain"]),
        ("QB", ["Geno Smith", "Cade Klubnik"]),
        ("FB", ["Andrew Beck"]),
        ("RB", ["Breece Hall", "Braelon Allen", "Isaiah Davis", "Kene Nwangwu"]),
    ],
    "def": [
        ("EDGE", ["Kingsley Enagbare", "Will McDonald IV"]),
        ("DL", ["Harrison Phillips", "Jack Heflin"]),
        ("DL2", ["Jack Heflin"]),
        ("DL3", ["Jowon Briggs", "Darrell Jackson Jr."]),
        ("EDGE2", ["David Bailey", "Joseph Ossai", "Nate Lynn"]),
        ("LB", ["Jamien Sherwood", "Trevin Wallace"]),
        ("LB2", ["Demario Davis", "Jaden Keller"]),
        ("NB", ["Jarvis Brownlee Jr.", "D'Angelo Ponds"]),
        ("CB", ["Brandon Stephens", "Qwan'tez Stiggers"]),
        ("CB2", ["Azareye'h Thomas", "Nahshon Wright"]),
        ("S", ["Minkah Fitzpatrick", "Malachi Moore"]),
        ("S2", ["Dane Belton"]),
    ],
}
CHARTS["PHI"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["DeVonta Smith", "Hollywood Brown"]),
        ("LT", ["Jordan Mailata"]),
        ("LG", ["Willie Lampkin"]),
        ("C", ["Drew Kendall", "Jake Majors"]),
        ("RG", ["Tyler Steen", "Micah Morris"]),
        ("RT", ["Markel Bell", "Fred Johnson"]),
        ("TE", ["Dallas Goedert", "Johnny Mundt"]),
        ("WR2", ["Makai Lemon", "Elijah Moore", "Britain Covey"]),
        ("WR3", ["Dontayvion Wicks", "Darius Cooper"]),
        ("RB", ["Saquon Barkley"]),
        ("QB", ["Tanner McKee", "Cole Payton", "Joe Milton"]),
    ],
    "def": [
        ("EDGE", ["Jalyx Hunt", "Jonathan Greenard", "Arnold Ebiketie"]),
        ("DT", ["Jalen Carter", "Byron Young"]),
        ("DT2", ["Ty Robinson"]),
        ("DT3", ["Moro Ojomo"]),
        ("EDGE2", ["Nolan Smith Jr.", "Jonathan Greenard", "A.J. Epenesa"]),
        ("LB", ["Zack Baun", "Smael Mondon Jr."]),
        ("LB2", ["Jihaad Campbell", "Jeremiah Trotter Jr."]),
        ("CB", ["Riq Woolen", "Jonathan Jones"]),
        ("CB2", ["Quinyon Mitchell", "Kelee Ringo"]),
        ("NCB", ["Cooper DeJean", "Mac McWilliams"]),
        ("S", ["Marcus Epps", "Michael Carter II"]),
        ("S2", ["Andrew Mukuba", "Kenny Moore II"]),
    ],
}
CHARTS["PIT"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["DK Metcalf", "Kaden Wetjen"]),
        ("LT", ["Troy Fautanu"]),
        ("LG", ["Mason McCormick"]),
        ("C", ["Zach Frazier", "Ryan McCollum"]),
        ("RG", ["Brock Hoffman", "Spencer Anderson"]),
        ("RT", ["Max Iheanachor", "Dylan Cook"]),
        ("TE", ["Pat Freiermuth", "Darnell Washington", "Robert Tonyan"]),
        ("WR2", ["Ben Skowronek", "Brandon Smith"]),
        ("WR3", ["Germie Bernard"]),
        ("QB", ["Aaron Rodgers", "Mason Rudolph", "Will Howard", "Drew Allar"]),
        ("RB", ["Jaylen Warren", "Rico Dowdle", "Eli Heidenreich",
                "Travis Homer", "Lew Nichols"]),
        ("FB", ["Riley Nowakowski"]),
    ],
    "def": [
        ("DE", ["Keeanu Benton", "Gabriel Rubio", "Kevin Jobity Jr."]),
        ("NT", ["Yahya Black"]),
        ("DT", ["Cameron Heyward"]),
        ("LOLB", ["T.J. Watt"]),
        ("LILB", ["Patrick Queen", "Carson Bruener"]),
        ("RILB", ["Payton Wilson", "Cole Holcomb"]),
        ("ROLB", ["Alex Highsmith", "Jack Sawyer"]),
        ("OLB", ["Nick Herbig"]),
        ("CB", ["Asante Samuel Jr.", "Sean Murphy-Bunting", "Doneiko Slaughter"]),
        ("NCB", ["Jalen Ramsey", "Brandin Echols"]),
        ("CB2", ["Jamel Dean", "Daylen Everette", "Terell Smith"]),
        ("S", ["Jaquan Brisker", "DeShon Elliott", "Robert Spears-Jennings"]),
    ],
}
CHARTS["SEA"] = {
    "unit": "OFF",
    "rows": [
        # The club's own chart (read live 2026-11-19,
        # https://www.seahawks.com/team/depth-chart/) prints Cooper Kupp AND
        # Rashid Shaheed in the FIRST wide-receiver cell. They are co-starters,
        # not first and second string, so the cell is stored as one cell with
        # two names and both carry depth 1.
        ("WR", [("Cooper Kupp", "Rashid Shaheed"), "Irvin Charles"]),
        ("LT", ["Charles Cross", "Josh Jones"]),
        ("LG", ["Quenton Nelson", "Anthony Bradford"]),
        ("C", ["Jalen Sundell", "Olu Oluwatimi"]),
        ("RG", ["Grey Zabel", "Anthony Bradford", "Beau Stephens"]),
        ("RT", ["Abraham Lucas", "Josh Jones"]),
        ("TE", ["AJ Barner", "Eric Saubert", "Nick Kallerup"]),
        ("WR2", ["Jaxon Smith-Njigba", "Tory Horton"]),
        ("QB", ["Sam Darnold", "Drew Lock", "Jalen Milroe"]),
        ("FB", ["Brady Russell"]),
        ("RB", ["Zach Charbonnet", "Jadarian Price", "Emanuel Wilson",
                "George Holani"]),
    ],
    "def": [
        ("DT", ["Leonard Williams", "Rylie Mills"]),
        ("NT", ["Byron Murphy II", "Brandon Pili", "Deven Eastern"]),
        ("DE", ["Jarran Reed", "Mike Morris"]),
        ("RUSH", ["DeMarcus Lawrence", "Derick Hall"]),
        ("MLB", ["Ernest Jones IV", "Patrick O'Connell"]),
        ("WLB", ["Drake Thomas", "Tyrice Knight", "Chazz Surratt"]),
        ("SLB", ["Uchenna Nwosu", "Dante Fowler Jr.", "Connor O'Toole"]),
        ("CB", ["Devon Witherspoon", "Nehemiah Pritchett"]),
        ("CB2", ["Josh Jobe", "Avery Smith"]),
        ("S", ["Ty Okada", "Rodney Thomas II"]),
        ("S2", ["Julian Love"]),
        ("S3", ["Nick Emmanwori"]),
    ],
}
CHARTS["SF"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Mike Evans", "Jordan Watkins", "Brandin Cooks"]),
        ("LT", ["Trent Williams", "Vederian Lowe", "Enrique Cruz Jr."]),
        ("LG", ["Connor Colby", "Carver Willis"]),
        ("C", ["Jake Brendel", "Jarrett Patterson"]),
        ("RG", ["Dominick Puni"]),
        ("RT", ["Colton McKivitz"]),
        ("TE", ["George Kittle", "Luke Farrell", "Brayden Willis"]),
        ("WR2", ["Deebo Samuel Sr.", "Demarcus Robinson", "Jacob Cowing"]),
        ("RB", ["Christian McCaffrey", "Kaelon Black", "Jordan James"]),
        ("FB", ["Kyle Juszczyk"]),
        ("QB", ["Brock Purdy", "Mac Jones", "Kurtis Rourke"]),
    ],
    "def": [
        ("LDE", ["Keion White", "Mykel Williams", "Khalid Kareem"]),
        ("LDT", ["DeForest Buckner", "Gracen Halton", "Sebastian Valdez"]),
        ("RDT", ["Osa Odighizuwa", "James Thompson Jr."]),
        ("RDE", ["Nick Bosa", "Romello Height"]),
        ("SAM", ["Jaden Dugger", "Luke Gifford"]),
        ("MIKE", ["Fred Warner", "Tatum Bethune"]),
        ("WILL", ["Dre Greenlaw", "Garret Wallow"]),
        ("LCB", ["Renardo Green"]),
        ("RCB", ["Deommodore Lenoir", "Ephesians Prysock"]),
        ("NB", ["Upton Stout"]),
        ("FS", ["Ji'Ayir Brown", "Siran Neal"]),
        ("SS", ["Malik Mustapha", "Marques Sigle", "Ashtyn Davis"]),
    ],
}
CHARTS["TB"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Ted Hurst III", "David Sills V"]),
        ("WR2", ["Chris Godwin Jr.", "Kameron Johnson"]),
        ("LT", ["Tristan Wirfs", "Benjamin Chukwuma"]),
        ("LG", ["Ben Bredeson", "Billy Schrauth"]),
        ("C", ["Graham Barton", "Dan Feeney"]),
        ("RG", ["Cody Mauch", "Trevor Keegan"]),
        ("RT", ["Luke Goedeke", "Justin Skule"]),
        ("WR3", ["Emeka Egbuka", "Tez Johnson"]),
        ("TE", ["Cade Otton", "Payne Durham", "Ko Kieft", "Bauer Sharp"]),
        ("QB", ["Baker Mayfield", "Jalon Daniels"]),
        ("RB", ["Bucky Irving", "Kenny Gainwell", "Sean Tucker"]),
    ],
    "def": [
        ("DL", ["Calijah Kancey", "Elijah Roberts"]),
        ("NT", ["Vita Vea", "Rakeem Nuñez-Roches", "Elijah Simmons"]),
        ("DL2", ["A'Shawn Robinson", "DeMonte Capehart"]),
        ("OLB", ["Yaya Diaby", "Anthony Nelson", "David Walker"]),
        ("ILB", ["Josiah Trotter", "SirVocea Dennis"]),
        ("ILB2", ["Alex Anzalone"]),
        ("OLB2", ["Rueben Bain Jr.", "Al-Quadin Muhammad"]),
        ("CB", ["Zyon McCollum", "Benjamin Morrison", "Ayden Garnes"]),
        ("CB2", ["Jacob Parrish", "Keionte Scott", "Kevin Knowles"]),
        ("S", ["Antoine Winfield Jr.", "Ifeatu Melifonwu"]),
        ("S2", ["Tykee Smith", "Miles Killebrew"]),
    ],
}
CHARTS["TEN"] = {
    "unit": "OFF",
    "rows": [
        ("WR", ["Calvin Ridley", "Chimere Dike"]),
        ("TE", ["Gunnar Helm", "Daniel Bellinger", "David Martin-Robinson",
                "Kylen Granson"]),
        ("LT", ["Dan Moore Jr.", "James Hudson III"]),
        ("LG", ["Peter Skoronski"]),
        ("C", ["Austin Schlottmann", "Pat Coogan"]),
        ("RG", ["Atonio Mafi", "Garrett Dellinger"]),
        ("RT", ["JC Latham", "Brandon Crenshaw-Dickson"]),
        ("WR2", ["Wan'Dale Robinson"]),
        ("WR3", ["Carnell Tate", "Elic Ayomanor"]),
        ("QB", ["Cam Ward", "Mitchell Trubisky"]),
        ("RB", ["Tony Pollard", "Tyjae Spears", "Nick Singleton", "Julius Chestnut",
                "Michael Carter"]),
    ],
    "def": [
        ("DE", ["Jermaine Johnson II", "Oluwafemi Oladejo"]),
        ("DT", ["Solomon Thomas", "Jonah Laulu", "Jackie Marshall"]),
        ("DL", ["John Franklin-Myers", "Nazir Stackhouse", "Timmy Horne"]),
        ("DE2", ["Jacob Martin", "Keldric Faulk", "Truman Jones"]),
        ("LB", ["Cody Barton"]),
        ("LB2", ["Cedric Gray"]),
        ("LB3", ["Anthony Hill Jr.", "Dorian Mausi"]),
        ("CB", ["Joshua Williams", "Alontae Taylor"]),
        ("NCB", ["Marcus Harris", "Alontae Taylor", "Micah Robinson"]),
        ("S", ["Tony Adams"]),
        ("S2", ["Kevin Winston Jr.", "Terrell Burgess"]),
        ("CB2", ["Cor'Dale Flotte", "Jaylon Jones"]),
    ],
}
CHARTS["WAS"] = {
    "unit": "OFF",
    # Read live on 2026-11-19 from https://www.commanders.com/team/depth-chart.
    # The chart has CHANGED since the 2026-11-14 capture: the third wide
    # receiver row now names Antonio Williams in the first cell and prints an
    # EMPTY second cell, which is stored as an empty cell (not dropped, and not
    # silently read as "there is no second receiver").
    "rows": [
        ("WR", ["Treylon Burks", "Van Jefferson"]),
        ("LT", ["Brandon Coleman", "Andrew Wylie"]),
        ("LG", ["Chris Paul", "Nick Allegretti"]),
        ("C", ["Lucas Patrick", "Matt Gulbin"]),
        ("RG", ["Sam Cosmi", "Tanoa Togiai"]),
        ("RT", ["Josh Conerly Jr.", "Andrew Wylie"]),
        ("TE", ["Chig Okonkwo", "Ben Sinnott"]),
        ("TE2", ["John Bates", "Colson Yankoff"]),
        ("WR2", ["Stefon Diggs", "Luke McCaffrey"]),
        ("WR3", ["Antonio Williams", ""]),
        ("QB", ["Jayden Daniels", "Marcus Mariota", "Athan Kaliakmanis"]),
        ("RB", ["Rachaad White", "Austin Ekeler", "Robert Henry Jr."]),
    ],
    "def": [
        ("DL", ["Charles Omenihu", "Jer'Zhan Newton"]),
        ("DL2", ["Tim Settle", "Shy Tuttle"]),
        ("DL3", ["Deatrich Wise Jr.", "Ricky Barber"]),
        ("OLB", ["Odafe Oweh", "Joshua Josephs"]),
        ("LB", ["Sonny Styles", "Kain Medrano"]),
        ("LB2", ["Frankie Luvu", "Jordan Magee"]),
        ("OLB2", ["K'Lavon Chaisson", "Dorance Armstrong"]),
        ("CB", ["Amik Robertson", "Rasul Douglas", "Isaac Yiadom"]),
        ("CB2", ["Trey Amos", "Mike Sainristil", "Fabian Moreau"]),
        ("SS", ["Nick Cross", "Tyler Owens"]),
        ("FS", ["Jeremy Reaves", "Quan Martin", "Percy Butler"]),
    ],
}


# ---------------------------------------------------------------------------
# Defensive unit grouping. "Offense" and "Defense" are what the club chart calls
# its own sections; special teams are in the chart but are excluded from the
# deficiency score because they are not a unit that moves a spread the same way.
# ---------------------------------------------------------------------------
def normalize(name):
    """Compare names case-, punctuation- and suffix-insensitively."""
    n = name.lower().replace(".", "").replace("'", "").replace("-", " ")
    for suf in (" iii", " iv", " jr", " sr", " ii", " v"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    return " ".join(n.split())


def load_injuries():
    with open(INJ_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_teams():
    with open(STAND_CSV, newline="", encoding="utf-8") as fh:
        return {r["abbr"] for r in csv.DictReader(fh)}


def cell_names(cell):
    """The names printed in one depth-chart cell.

    A cell is one of:
      "Name"          - one name in the cell
      ("A", "B")      - several names printed in the SAME cell (co-starters)
      ""              - a printed cell with no name in it
    """
    if isinstance(cell, (tuple, list)):
        return [str(x) for x in cell]
    text = str(cell).strip()
    return [text] if text else []


def cell_kind(cell):
    names = cell_names(cell)
    if not names:
        return "empty"
    if len(names) > 1:
        return "shared"
    return "single"


def build():
    teams = load_teams()
    injuries = load_injuries()
    errors = []

    # 1. every club with a chart URL must be a real club in the official standings
    for club, url in CHART_URL.items():
        if club not in teams:
            errors.append("%s: not a club in the official standings file" % club)
        if club != "HOU" and not url.startswith("https://"):
            errors.append("%s: depth-chart source is not an https official URL" % club)

    # 2. internal consistency of every transcription: a cell is well formed and
    #    no player is printed twice in the same cell.
    for club, chart in CHARTS.items():
        for unit_key in ("rows", "def"):
            seen = {}
            for pos, order in chart[unit_key]:
                if len(order) > 6:
                    errors.append("%s %s %s: implausibly deep (%d)" % (club, unit_key, pos, len(order)))
                for depth, cell in enumerate(order, start=1):
                    names = cell_names(cell)
                    kind = cell_kind(cell)
                    if kind == "empty" and names:
                        errors.append("%s %s: empty cell carries a name" % (club, pos))
                    if kind == "shared" and len(names) < 2:
                        errors.append("%s %s: shared cell carries one name" % (club, pos))
                    if len(set(normalize(n) for n in names)) != len(names):
                        errors.append("%s %s: %s printed twice in one cell" % (club, pos, names))
                    for player in names:
                        key = normalize(player)
                        if key in seen:
                            # A player may legitimately appear at two positions
                            # (e.g. a tackle listed at RT and RG). Flag same-position
                            # duplicates only, which is a transcription error.
                            if seen[key] == (pos, depth):
                                errors.append("%s %s: %s listed twice at the same depth" % (club, pos, player))
                            else:
                                seen[key] = (pos, depth)
                        else:
                            seen[key] = (pos, depth)

    # 3. every injured player we score must be a real row in the official report
    injured = {}
    for r in injuries:
        injured.setdefault(r["team"], {})[normalize(r["player"])] = r

    rows = []
    for club in sorted(CHARTS):
        chart = CHARTS[club]
        url = CHART_URL.get(club, "")
        retrieved = RETRIEVED_BY_CLUB.get(club, RETRIEVED)
        for unit_key, unit_label in (("rows", "Offense"), ("def", "Defense")):
            for pos, order in chart[unit_key]:
                for depth, cell in enumerate(order, start=1):
                    names = cell_names(cell)
                    kind = cell_kind(cell)
                    if not names:
                        # a printed cell with nobody in it: recorded, not dropped
                        rows.append(OrderedDict([
                            ("team", club),
                            ("unit", unit_label),
                            ("position_row", pos),
                            ("depth", depth),
                            ("player", ""),
                            ("game_status", ""),
                            ("injury", ""),
                            ("chart_date", CHART_DATE.get(club, "")),
                            ("source", url),
                            ("retrieved", retrieved),
                            ("slot_kind", "empty"),
                            ("slot_size", 0),
                        ]))
                        continue
                    for player in names:
                        inj = injured.get(club, {}).get(normalize(player), {})
                        rows.append(OrderedDict([
                            ("team", club),
                            ("unit", unit_label),
                            ("position_row", pos),
                            ("depth", depth),
                            ("player", player),
                            ("game_status", inj.get("game_status", "")),
                            ("injury", inj.get("injuries", "")),
                            ("chart_date", CHART_DATE.get(club, "")),
                            ("source", url),
                            ("retrieved", retrieved),
                            ("slot_kind", kind),
                            ("slot_size", len(names)),
                        ]))

    # 4. coverage: every Out/Doubtful player must be either matched to a depth
    #    position or explicitly recorded as unmatched (not silently dropped).
    matched = {(r["team"], normalize(r["player"])) for r in rows if r["player"]}
    unmatched = []
    for r in injuries:
        if r["game_status"] not in ("Out", "Doubtful"):
            continue
        if (r["team"], normalize(r["player"])) not in matched:
            unmatched.append(r)
    return rows, unmatched, errors


def write_csv(rows):
    cols = ["team", "unit", "position_row", "depth", "player", "game_status",
            "injury", "chart_date", "source", "retrieved", "slot_kind", "slot_size"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def _cells_of(rows):
    """Every printed depth cell, keyed by (club, unit, position row, depth)."""
    cells = OrderedDict()
    for r in rows:
        if r.get("slot_kind") == "empty":
            continue
        cells.setdefault((r["team"], r["unit"], r["position_row"], int(r["depth"])), []).append(r)
    return cells


def rollup(rows, unmatched):
    """Per-club deficiency roll-up plus the two irregularity classes.

    Everything here is a count of sourced rows, not an estimate. A 'hole' means
    the club lists only one player at a position and he is ruled out; a
    'cascade' means the starter *and* his listed backup are both ruled out.
    """
    import json

    by_club = OrderedDict()
    for club in sorted(CHART_URL):
        by_club[club] = {
            "team": club,
            "has_chart": bool(CHART_URL[club]),
            "chart_url": CHART_URL[club],
            "chart_date": CHART_DATE.get(club, ""),
            "off_depth_rows": 0, "def_depth_rows": 0,
            "off_out": 0, "def_out": 0,
            "off_starter_out": 0, "def_starter_out": 0,
            "out_names": [], "starter_out_names": [],
        }
    for r in rows:
        c = by_club[r["team"]]
        if r["unit"] == "Offense":
            c["off_depth_rows"] += 1
        else:
            c["def_depth_rows"] += 1
        if r["game_status"] in ("Out", "Doubtful"):
            if r["unit"] == "Offense":
                c["off_out"] += 1
            else:
                c["def_out"] += 1
            entry = "%s %s (depth %s, %s)" % (r["position_row"], r["player"],
                                              r["depth"], r["game_status"])
            c["out_names"].append(entry)
            if int(r["depth"]) == 1:
                if r["unit"] == "Offense":
                    c["off_starter_out"] += 1
                else:
                    c["def_starter_out"] += 1
                c["starter_out_names"].append(entry)

    # position rows where the club publishes no replacement, and rows where the
    # starter and the listed backup are both ruled out.
    #
    # This runs on CELLS, not on rows. A club that publishes two names in one
    # cell has named co-starters: if one of them is out, the position still has
    # a starter and the club has NOT lost depth, so it is counted as a shared
    # slot with one absence - never as a hole and never as a cascade.
    groups = OrderedDict()
    for r in rows:
        groups.setdefault((r["team"], r["unit"], r["position_row"]), []).append(r)
    holes, cascades, shared_slots, empty_slots = [], [], [], []
    for (club, unit, pos), grp in groups.items():
        grp.sort(key=lambda r: int(r["depth"]))
        cells = OrderedDict()
        for r in grp:
            cells.setdefault(int(r["depth"]), []).append(r)
        first = cells.get(1, [])
        if not first:
            continue
        kind = first[0].get("slot_kind", "single")
        out_first = [r for r in first if r["game_status"] in ("Out", "Doubtful")]
        if kind == "shared":
            if out_first and len(out_first) < len(first):
                shared_slots.append({
                    "team": club, "unit": unit, "position": pos,
                    "names": [r["player"] for r in first],
                    "out": [r["player"] for r in out_first],
                    "source": first[0]["source"]})
            continue
        if kind == "empty":
            empty_slots.append({"team": club, "unit": unit, "position": pos,
                                 "source": first[0]["source"]})
            continue
        if not out_first:
            continue
        second = cells.get(2, [])
        if not second:
            holes.append({"team": club, "unit": unit, "position": pos,
                          "player": first[0]["player"],
                          "status": first[0]["game_status"],
                          "source": first[0]["source"]})
        else:
            second_out = [r for r in second if r["game_status"] in ("Out", "Doubtful")]
            if len(second_out) == len(second):
                cascades.append({"team": club, "unit": unit, "position": pos,
                                 "starter": first[0]["player"],
                                 "backup": ", ".join(r["player"] for r in second),
                                 "source": first[0]["source"]})
    for r in rows:
        if r.get("slot_kind") == "empty":
            empty_slots.append({"team": r["team"], "unit": r["unit"],
                                 "position": "%s (cell %s)" % (r["position_row"], r["depth"]),
                                 "source": r["source"]})

    payload = {
        "retrieved": RETRIEVED,
        "source_injuries": "https://www.nfl.com/injuries/",
        "clubs_with_chart": sum(1 for c in by_club.values() if c["has_chart"]),
        "clubs_without_chart": [c for c in by_club if not by_club[c]["has_chart"]],
        "depth_rows": len(rows),
        "out_rows": sum(1 for r in rows if r["game_status"] in ("Out", "Doubtful")),
        "starter_out_rows": sum(1 for r in rows
                                if int(r["depth"]) == 1
                                and r["game_status"] in ("Out", "Doubtful")
                                and r.get("slot_kind") != "shared"),
        "shared_cells": sum(1 for _k, grp in _cells_of(rows).items() if len(grp) > 1),
        "empty_cells": sum(1 for r in rows if r.get("slot_kind") == "empty"),
        "shared_slots_one_out": sorted(shared_slots,
                                        key=lambda h: (h["team"], h["unit"], h["position"])),
        "clubs": list(by_club.values()),
        "holes": sorted(holes, key=lambda h: (h["team"], h["unit"], h["position"])),
        "cascades": sorted(cascades, key=lambda h: (h["team"], h["unit"], h["position"])),
        "empty_slots": sorted(empty_slots, key=lambda h: (h["team"], h["unit"], h["position"])),
        "unmatched": [{"team": r["team"], "player": r["player"], "pos": r["pos"],
                       "status": r["game_status"], "injury": r["injuries"],
                       "url": r["player_url"]} for r in unmatched],
    }
    out = os.path.join(ROOT, "data", "output")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "depth.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
    return payload


def main(argv):
    rows, unmatched, errors = build()
    clubs_with_chart = sum(1 for c in CHARTS if CHARTS[c]["rows"])
    print("clubs with an ordered chart: %d of 32" % clubs_with_chart)
    print("depth rows written: %d" % len(rows))
    print("official Out/Doubtful players not matched to a published depth row: %d"
          % len(unmatched))
    for r in unmatched:
        print("  unmatched: %s %s (%s)" % (r["team"], r["player"], r["pos"]))
    if errors:
        print("FAIL: %d transcription problem(s)" % len(errors))
        for e in errors:
            print(" -", e)
        return 1
    if "--check" in argv:
        print("PASS: transcriptions are internally consistent.")
        return 0
    write_csv(rows)
    payload = rollup(rows, unmatched)
    print("hole rows (club lists no replacement): %d" % len(payload["holes"]))
    print("cascades (starter and backup both out):  %d" % len(payload["cascades"]))
    print("wrote %s and data/output/depth.json" % os.path.relpath(OUT_CSV, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
