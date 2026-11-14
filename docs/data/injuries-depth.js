/* X4 — DEPTH / "STRING" COVERAGE
   Requirements R-16 and R-17: know when a 2nd, 3rd or 4th string player is replacing a
   starter, on defence and on offence.

   FINDING (this is the crux of R-16/R-17):
     - NFL.com does NOT publish depth charts. /teams/<club>/depth-chart returns 404.
     - Individual club sites DO publish depth charts (verified for detroitlions.com), but
       they list players in ORDER and do NOT label 1st / 2nd / 3rd / 4th string.
   Therefore no official source consulted this session states a player's "string".
   Every string value in this project is therefore blank and flagged. See F-03.

   The club depth-chart URL column is populated ONLY where it was verified. It is left
   blank for the other 31 clubs rather than guessed, because a guessed URL is a broken
   link. */

(function () {
  // Club, nfl.com team page (verified link from the official standings page)
  const clubs = [
    ["Buffalo Bills","buffalo-bills"],["New England Patriots","new-england-patriots"],
    ["New York Jets","new-york-jets"],["Miami Dolphins","miami-dolphins"],
    ["Pittsburgh Steelers","pittsburgh-steelers"],["Cincinnati Bengals","cincinnati-bengals"],
    ["Cleveland Browns","cleveland-browns"],["Baltimore Ravens","baltimore-ravens"],
    ["Jacksonville Jaguars","jacksonville-jaguars"],["Houston Texans","houston-texans"],
    ["Indianapolis Colts","indianapolis-colts"],["Tennessee Titans","tennessee-titans"],
    ["Denver Broncos","denver-broncos"],["Kansas City Chiefs","kansas-city-chiefs"],
    ["Las Vegas Raiders","las-vegas-raiders"],["Los Angeles Chargers","los-angeles-chargers"],
    ["New York Giants","new-york-giants"],["Dallas Cowboys","dallas-cowboys"],
    ["Washington Commanders","washington-commanders"],["Philadelphia Eagles","philadelphia-eagles"],
    ["Chicago Bears","chicago-bears"],["Detroit Lions","detroit-lions"],
    ["Minnesota Vikings","minnesota-vikings"],["Green Bay Packers","green-bay-packers"],
    ["Carolina Panthers","carolina-panthers"],["New Orleans Saints","new-orleans-saints"],
    ["Tampa Bay Buccaneers","tampa-bay-buccaneers"],["Atlanta Falcons","atlanta-falcons"],
    ["San Francisco 49ers","san-francisco-49ers"],["Seattle Seahawks","seattle-seahawks"],
    ["Los Angeles Rams","los-angeles-rams"],["Arizona Cardinals","arizona-cardinals"],
  ];

  const rows = clubs.map(c => {
    const isDetroit = c[1] === "detroit-lions";
    return {
      club: c[0],
      nflTeamPage: '<a href="https://www.nfl.com/teams/' + c[1] + '/" target="_blank" rel="noopener">nfl.com/teams/' + c[1] + '</a>',
      clubDepthChart: isDetroit
        ? '<a href="https://www.detroitlions.com/team/depth-chart" target="_blank" rel="noopener">detroitlions.com/team/depth-chart</a>'
        : "",   // intentionally blank — not verified; not guessed
      stringsLabelled: isDetroit ? "No" : "",   // Detroit verified: ordered list, no string labels
      src: S(isDetroit ? "LIONS_DC" : "NFL_STANDINGS"),
      status: isDetroit ? "verified" : "unverified",
      note: isDetroit
        ? "Verified: club publishes an ordered depth chart by position, but does not label 1st/2nd/3rd/4th string."
        : "Club depth-chart URL not verified this session. Left blank rather than guessed — see F-03.",
    };
  });

  const gaps = [
    { req: "R-16 (defence)",
      need: "Identity of the 2nd/3rd/4th-string defender who will actually replace an injured starter, and a measure of how much worse he is.",
      exists: "Official injury report (player, position, injury, practice status, game status) — verified, Week 10 2026, in full.",
      gap: "The injury report names the injured player. It does NOT name his replacement, and it does NOT say whether the replacement is 2nd, 3rd or 4th string.",
      severity: "Blocking",
      action: "Source a depth provider that labels order, or derive order from official club depth charts plus snap counts and label it DERIVED (S-15, Q-17).",
      src: S("NFL_INJURY"), status: "verified" },

    { req: "R-17 (offence)",
      need: "Same as R-16 for offensive positions.",
      exists: "Same official injury report; same limitation.",
      gap: "Identical gap. Additionally, offensive-line absences are particularly consequential and are currently only identifiable by position code (T, G, C).",
      severity: "Blocking",
      action: "Same as R-16.",
      src: S("NFL_INJURY"), status: "verified" },

    { req: "R-15 (injury tracking)",
      need: "Weekly, machine-readable injury data.",
      exists: "Official NFL.com injury report, published by week, with practice status and game status.",
      gap: "Captured as a point-in-time snapshot this session. A recurring automated ingestion job has not been built.",
      severity: "Medium",
      action: "Build a weekly ingestion job against the official injury report URL.",
      src: S("NFL_INJURY"), status: "verified" },

    { req: "R-15 (late changes)",
      need: "Elevations and late scratches after the final injury report.",
      exists: "Official rule: practice-squad players may be elevated up to three times per league year; clubs may expand to 54/55 only via the standard elevation addendum.",
      gap: "The timing of the official inactive list was NOT confirmed on an official page this session.",
      severity: "Medium",
      action: "Confirm the release requirement on official NFL football-operations pages; until then leave the time blank (F-04).",
      src: S("NFL_ROSTER_RULES"), status: "partial" },

    { req: "R-16 / R-17 (severity)",
      need: "Injury severity and expected recovery time.",
      exists: "Body part or condition only (e.g. knee, ankle, concussion).",
      gap: "The official report does not identify precise diagnosis, severity, treatment or recovery timetable. Recovery estimates seen in news headlines are journalistic, not official data.",
      severity: "Medium",
      action: "Never treat a reported recovery timeline as official data. Use only the published game status.",
      src: S("NFL_INJ_POLICY"), status: "verified" },

    { req: "R-16 / R-17 (designations)",
      need: "A reliable mapping from designation to the probability a player appears.",
      exists: "Official definitions: Out = will not play; Doubtful = unlikely to participate; Questionable = uncertain whether the player will play. Practice report: DNP / Limited (<100% of normal repetitions) / Full (100%).",
      gap: "No official source gives a play-probability per designation. Any such number must be estimated and labelled as estimated.",
      severity: "Low — estimation is acceptable here",
      action: "Estimate play-probability per designation from our own data once available, and publish the estimation window with it.",
      src: S("NFL_INJ_POLICY"), status: "verified" },
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.depthCoverage = {
    sortKey: "club", sortDir: "asc",
    placeholder: "Filter by club…",
    facets: [
      { key: "status", label: "Status", options: ["verified","unverified"] },
    ],
    cols: [
      { key: "club", label: "Club", nowrap: true },
      { key: "nflTeamPage", label: "Official league team page" },
      { key: "clubDepthChart", label: "Official club depth chart (verified only)" },
      { key: "stringsLabelled", label: "Does it label 1st/2nd/3rd/4th?" },
      { key: "note", label: "Note" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: rows,
  };

  window.X4_TABLES.depthGaps = {
    sortKey: "req", sortDir: "asc",
    cols: [
      { key: "req", label: "Requirement", nowrap: true },
      { key: "need", label: "What is needed" },
      { key: "exists", label: "What we have (verified)" },
      { key: "gap", label: "The gap" },
      { key: "severity", label: "Severity", nowrap: true },
      { key: "action", label: "Proposed action" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: gaps,
  };
})();
