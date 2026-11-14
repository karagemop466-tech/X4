/* X4 — 2026 NFL WEEK 10 SCHEDULE (verified)
   Sources: https://www.nfl.com/schedules/2026/REG10  and  https://www.nfl.com/injuries/
   Retrieved 2026-11-14.
   Each row cites the page on which that game was actually observed. No odds are
   included: there is no official league source for betting prices (see Flagged for Review). */

(function () {
  // day, date, time ET, away, home, network, note, sourceId
  const raw = [
    ["Thu","Nov 12, 2026","8:15 PM","Washington Commanders","New York Giants","Prime Video",
     "FINAL — Commanders 24, Giants 21.","NFL_SCHED"],
    ["Sun","Nov 15, 2026","9:30 AM","New England Patriots","Detroit Lions","FOX",
     "International Game — Munich.","NFL_SCHED"],
    ["Sun","Nov 15, 2026","1:00 PM","Kansas City Chiefs","Atlanta Falcons","CBS","","NFL_SCHED"],
    ["Sun","Nov 15, 2026","1:00 PM","Houston Texans","Cleveland Browns","FOX",
     "Officially reported: Browns to start QB Deshaun Watson (NFL.com, Nov 11).","NFL_SCHED"],
    ["Sun","Nov 15, 2026","1:00 PM","Minnesota Vikings","Green Bay Packers","FOX","","NFL_SCHED"],
    ["Sun","Nov 15, 2026","1:00 PM","Miami Dolphins","Indianapolis Colts","CBS",
     "Officially reported: Dolphins QB Malik Willis (groin) placed on IR; Kyle McCord in line for first start.","NFL_SCHED"],
    ["Sun","Nov 15, 2026","1:00 PM","Carolina Panthers","New Orleans Saints","FOX","","NFL_SCHED"],
    ["Sun","Nov 15, 2026","1:00 PM","Jacksonville Jaguars","Tennessee Titans","FOX","","NFL_INJURY"],
    ["Sun","Nov 15, 2026","1:00 PM","Buffalo Bills","New York Jets","CBS","","NFL_INJURY"],
    ["Sun","Nov 15, 2026","4:05 PM","Los Angeles Rams","Arizona Cardinals","CBS",
     "Officially reported: Cardinals' Carson Beck to start (NFL.com, Nov 11).","NFL_INJURY"],
    ["Sun","Nov 15, 2026","4:05 PM","Seattle Seahawks","Las Vegas Raiders","CBS",
     "Officially reported: Sam Darnold ruled out; Drew Lock to start, no injury designation.","NFL_INJURY"],
    ["Sun","Nov 15, 2026","4:25 PM","San Francisco 49ers","Dallas Cowboys","FOX, FOX Deportes","","NFL_INJURY"],
    ["Sun","Nov 15, 2026","8:20 PM","Pittsburgh Steelers","Cincinnati Bengals","NBC, UNIVERSO","","NFL_INJURY"],
    ["Mon","Nov 16, 2026","8:15 PM","Los Angeles Chargers","Baltimore Ravens","ESPN, ABC, ESPN2, ESPN Deportes",
     "Officially reported: Ravens confirm Lamar Jackson expected to miss 6-10 weeks (NFL.com, Nov 13) — see Flagged for Review for a conflicting 6-9 week report.","NFL_SCHED"],
  ];

  const rows = raw.map(r => ({
    day: r[0], date: r[1], timeET: r[2],
    away: r[3], home: r[4], network: r[5], note: r[6],
    src: S(r[7]),
    status: "verified",
  }));

  const byes = ["Chicago Bears", "Denver Broncos", "Philadelphia Eagles", "Tampa Bay Buccaneers"].map(t => ({
    day: "—", date: "Week 10", timeET: "—",
    away: t, home: "BYE", network: "—",
    note: "Listed under 'Teams on Bye' on the official NFL.com Week 10 schedule page.",
    src: S("NFL_SCHED"),
    status: "verified",
  }));

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.schedule = {
    sortKey: "date", sortDir: "asc",
    placeholder: "Filter by team, date, network…",
    cols: [
      { key: "day", label: "Day" },
      { key: "date", label: "Date", nowrap: true },
      { key: "timeET", label: "Time (ET)", nowrap: true },
      { key: "away", label: "Away", nowrap: true },
      { key: "home", label: "Home", nowrap: true },
      { key: "network", label: "Network" },
      { key: "note", label: "Official note" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: rows.concat(byes),
  };
})();
