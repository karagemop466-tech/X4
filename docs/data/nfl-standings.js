/* X4 — 2026 NFL STANDINGS (verified)
   Source: https://www.nfl.com/standings/  (2026 REG, division view)
   Retrieved 2026-11-14. Values transcribed exactly as displayed on the official page.
   No value is interpolated, modelled, or inferred. Anything not displayed is left blank. */

(function () {
  // team, conf, division, W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, CONF, NONCONF, STRK, LAST5
  const raw = [
    ["Buffalo Bills","AFC","AFC East",7,1,0,"0.875",256,187,69,"3 - 1 - 0","4 - 0 - 0","0 - 1 - 0","4 - 1 - 0","3 - 0 - 0","4W","4 - 1 - 0"],
    ["New England Patriots","AFC","AFC East",5,4,0,"0.556",211,207,4,"3 - 1 - 0","2 - 3 - 0","3 - 0 - 0","5 - 1 - 0","0 - 3 - 0","1L","3 - 2 - 0"],
    ["New York Jets","AFC","AFC East",2,7,0,"0.222",182,223,-41,"1 - 3 - 0","1 - 4 - 0","0 - 2 - 0","2 - 4 - 0","0 - 3 - 0","4L","1 - 4 - 0"],
    ["Miami Dolphins","AFC","AFC East",1,7,0,"0.125",126,200,-74,"0 - 4 - 0","1 - 3 - 0","1 - 1 - 0","1 - 4 - 0","0 - 3 - 0","2L","1 - 4 - 0"],

    ["Pittsburgh Steelers","AFC","AFC North",6,2,0,"0.750",180,144,36,"4 - 0 - 0","2 - 2 - 0","2 - 1 - 0","3 - 2 - 0","3 - 0 - 0","4W","4 - 1 - 0"],
    ["Cincinnati Bengals","AFC","AFC North",6,2,0,"0.750",240,175,65,"2 - 1 - 0","4 - 1 - 0","1 - 1 - 0","4 - 2 - 0","2 - 0 - 0","4W","4 - 1 - 0"],
    ["Cleveland Browns","AFC","AFC North",5,4,0,"0.556",161,196,-35,"3 - 0 - 0","2 - 4 - 0","2 - 1 - 0","3 - 3 - 0","2 - 1 - 0","2L","2 - 3 - 0"],
    ["Baltimore Ravens","AFC","AFC North",4,5,0,"0.444",189,236,-47,"1 - 3 - 0","3 - 2 - 0","0 - 2 - 0","2 - 4 - 0","2 - 1 - 0","4L","1 - 4 - 0"],

    ["Jacksonville Jaguars","AFC","AFC South",6,2,0,"0.750",229,121,108,"4 - 1 - 0","2 - 1 - 0","1 - 1 - 0","5 - 2 - 0","1 - 0 - 0","2W","4 - 1 - 0"],
    ["Houston Texans","AFC","AFC South",3,5,0,"0.375",209,192,17,"0 - 4 - 0","3 - 1 - 0","2 - 1 - 0","3 - 3 - 0","0 - 2 - 0","1W","3 - 2 - 0"],
    ["Indianapolis Colts","AFC","AFC South",2,7,0,"0.222",184,249,-65,"1 - 3 - 0","1 - 4 - 0","1 - 2 - 0","1 - 5 - 0","1 - 2 - 0","5L","0 - 5 - 0"],
    ["Tennessee Titans","AFC","AFC South",1,7,0,"0.125",144,199,-55,"0 - 4 - 0","1 - 3 - 0","1 - 1 - 0","1 - 5 - 0","0 - 2 - 0","2L","1 - 4 - 0"],

    ["Denver Broncos","AFC","AFC West",7,2,0,"0.778",198,186,12,"4 - 0 - 0","3 - 2 - 0","2 - 1 - 0","3 - 1 - 0","4 - 1 - 0","5W","5 - 0 - 0"],
    ["Kansas City Chiefs","AFC","AFC West",6,2,0,"0.750",202,143,59,"4 - 0 - 0","2 - 2 - 0","3 - 1 - 0","6 - 1 - 0","0 - 1 - 0","1W","3 - 2 - 0"],
    ["Las Vegas Raiders","AFC","AFC West",4,5,0,"0.444",238,268,-30,"1 - 3 - 0","3 - 2 - 0","1 - 1 - 0","3 - 3 - 0","1 - 2 - 0","1L","1 - 4 - 0"],
    ["Los Angeles Chargers","AFC","AFC West",0,8,0,"0.000",121,219,-98,"0 - 4 - 0","0 - 4 - 0","0 - 3 - 0","0 - 5 - 0","0 - 3 - 0","8L","0 - 5 - 0"],

    ["New York Giants","NFC","NFC East",5,3,1,"0.611",203,196,7,"3 - 2 - 0","2 - 1 - 1","2 - 1 - 1","3 - 3 - 1","2 - 0 - 0","1L","2 - 2 - 1"],
    ["Dallas Cowboys","NFC","NFC East",4,5,0,"0.444",246,236,10,"1 - 3 - 0","3 - 2 - 0","2 - 1 - 0","2 - 4 - 0","2 - 1 - 0","1W","2 - 3 - 0"],
    ["Washington Commanders","NFC","NFC East",3,5,1,"0.389",196,223,-27,"2 - 2 - 1","1 - 3 - 0","2 - 2 - 1","3 - 4 - 1","0 - 1 - 0","1W","2 - 2 - 1"],
    ["Philadelphia Eagles","NFC","NFC East",2,7,0,"0.222",148,221,-73,"1 - 4 - 0","1 - 3 - 0","1 - 3 - 0","1 - 6 - 0","1 - 1 - 0","7L","0 - 5 - 0"],

    ["Chicago Bears","NFC","NFC North",7,2,0,"0.778",241,184,57,"4 - 1 - 0","3 - 1 - 0","0 - 2 - 0","5 - 2 - 0","2 - 0 - 0","4W","4 - 1 - 0"],
    ["Detroit Lions","NFC","NFC North",6,2,0,"0.750",222,189,33,"4 - 0 - 0","2 - 2 - 0","2 - 0 - 0","4 - 1 - 0","2 - 1 - 0","4W","4 - 1 - 0"],
    ["Minnesota Vikings","NFC","NFC North",6,2,0,"0.750",146,116,30,"3 - 1 - 0","3 - 1 - 0","2 - 1 - 0","4 - 1 - 0","2 - 1 - 0","2L","3 - 2 - 0"],
    ["Green Bay Packers","NFC","NFC North",6,3,0,"0.667",216,191,25,"3 - 1 - 0","3 - 2 - 0","1 - 2 - 0","4 - 3 - 0","2 - 0 - 0","2W","4 - 1 - 0"],

    ["Carolina Panthers","NFC","NFC South",3,5,0,"0.375",199,219,-20,"1 - 3 - 0","2 - 2 - 0","1 - 1 - 0","3 - 3 - 0","0 - 2 - 0","3L","2 - 3 - 0"],
    ["New Orleans Saints","NFC","NFC South",3,5,0,"0.375",185,216,-31,"1 - 4 - 0","2 - 1 - 0","0 - 1 - 0","1 - 3 - 0","2 - 2 - 0","1W","2 - 3 - 0"],
    ["Tampa Bay Buccaneers","NFC","NFC South",3,6,0,"0.333",202,178,24,"1 - 4 - 0","2 - 2 - 0","2 - 0 - 0","3 - 3 - 0","0 - 3 - 0","1L","3 - 2 - 0"],
    ["Atlanta Falcons","NFC","NFC South",3,6,0,"0.333",188,223,-35,"1 - 4 - 0","2 - 2 - 0","1 - 2 - 0","3 - 3 - 0","0 - 3 - 0","2L","1 - 4 - 0"],

    ["San Francisco 49ers","NFC","NFC West",7,1,0,"0.875",235,156,79,"5 - 0 - 0","2 - 1 - 0","3 - 0 - 0","4 - 1 - 0","3 - 0 - 0","1W","4 - 1 - 0"],
    ["Seattle Seahawks","NFC","NFC West",5,4,0,"0.556",202,162,40,"4 - 2 - 0","1 - 2 - 0","2 - 1 - 0","2 - 3 - 0","3 - 1 - 0","1W","2 - 3 - 0"],
    ["Los Angeles Rams","NFC","NFC West",5,4,0,"0.556",214,181,33,"2 - 3 - 0","3 - 1 - 0","0 - 2 - 0","3 - 2 - 0","2 - 2 - 0","3W","3 - 2 - 0"],
    ["Arizona Cardinals","NFC","NFC West",3,6,0,"0.333",178,255,-77,"0 - 3 - 0","3 - 3 - 0","1 - 3 - 0","2 - 5 - 0","1 - 1 - 0","1L","2 - 3 - 0"],
  ];

  const rows = raw.map(r => ({
    team: r[0], conf: r[1], division: r[2],
    w: r[3], l: r[4], t: r[5], pct: r[6],
    pf: r[7], pa: r[8], net: r[9],
    home: r[10], road: r[11], div: r[12], confRec: r[13], nonconf: r[14],
    strk: r[15], last5: r[16],
    src: S("NFL_STANDINGS"),
    status: "verified",
    note: "",
  }));

  // One cross-source conflict is recorded inline so the reviewer sees it where the number is.
  const lac = rows.find(r => r.team === "Los Angeles Chargers");
  if (lac) {
    lac.note = "Cross-source conflict: an aggregator omits the Chargers from its league table. NFL.com is the primary source and is what is shown here. See Flagged for Review.";
  }

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.standings = {
    sortKey: "pct", sortDir: "desc",
    placeholder: "Filter by team or division…",
    facets: [
      { key: "conf", label: "Conference", options: ["AFC", "NFC"] },
      { key: "division", label: "Division", options: ["AFC East","AFC North","AFC South","AFC West","NFC East","NFC North","NFC South","NFC West"] },
    ],
    cols: [
      { key: "team", label: "Team", nowrap: true },
      { key: "division", label: "Division", nowrap: true },
      { key: "w", label: "W", num: true },
      { key: "l", label: "L", num: true },
      { key: "t", label: "T", num: true },
      { key: "pct", label: "PCT", num: true },
      { key: "pf", label: "PF", num: true },
      { key: "pa", label: "PA", num: true },
      { key: "net", label: "Net Pts", num: true },
      { key: "home", label: "Home" },
      { key: "road", label: "Road" },
      { key: "div", label: "Div" },
      { key: "confRec", label: "Conf" },
      { key: "nonconf", label: "Non-Conf" },
      { key: "strk", label: "Streak", nowrap: true },
      { key: "last5", label: "Last 5" },
      { key: "note", label: "Review note" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: rows,
  };

  window.X4_STANDINGS = rows;
})();
