/* X4 — EXECUTIVE SUMMARY DATA
   Requirement R-18. Only verified facts plus explicitly-labelled design statements.
   Anything not confirmed from a primary source is left blank and appears on the
   Flagged for Review page instead. */

(function () {
  const E = (area, item, value, detail, srcId, status) => ({
    area, item, value, detail, src: S(srcId), status: status || "verified",
  });

  const facts = [
    E("Repo","State of the repository at session start","1 commit (4c5280a), README.md only",
      "The repo contained the single line '# X4'. There was no site, no code and no data to review. Everything on this site was built in this session. Flagged as F-01.","REPO_SELF"),

    E("Repo","Public site location","Published from docs/ on main",
      "Static HTML/CSS/JS with no build step, so there is no build to break.","REPO_SELF","design"),

    E("Season","Season and week currently published by the NFL","2026 regular season, Week 10",
      "NFL.com's official injury page is titled 'Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season'.","NFL_INJURY"),

    E("Data","Standings rows verified","32 of 32 clubs",
      "Every club's W-L-T, PCT, PF, PA, net points, home, road, division, conference, non-conference, streak and last-5 record transcribed from nfl.com/standings.","NFL_STANDINGS"),

    E("Data","Injury-report rows verified","345 player entries for Week 10",
      "Player, position, injury, practice status and game status for every club, transcribed from nfl.com/injuries. Empty cells on the official page are rendered as unverified, not filled in.","NFL_INJURY"),

    E("Data","Week 10 games verified","14 games + 4 clubs on bye",
      "Full Week 10 schedule with dates, Eastern kickoff times and networks, plus the official 'Teams on Bye' list: Chicago, Denver, Philadelphia, Tampa Bay.","NFL_SCHED"),

    E("Data","Week 10 result already final","Commanders 24, Giants 21",
      "Thursday Night Football, November 12, 2026, on Prime Video. This is the only completed Week 10 game at the time of capture.","NFL_SCHED"),

    E("Blocking gap","Official source for betting prices","None exists",
      "The NFL does not publish odds. Prices are commercial products of licensed operators. This is the single largest blocker in the project: it gates CLV, correlations and every odds-dependent validation. Flagged as F-02.","DESIGN_SPEC","unverified"),

    E("Blocking gap","Official source for depth / 'string'","None exists",
      "NFL.com returns 404 for team depth-chart pages. Club sites publish ordered depth charts but do not label 1st/2nd/3rd/4th string. Requirements R-16 and R-17 are blocked. Flagged as F-03.","NFL_DEPTH_CHART_404","unverified"),

    E("Strategies","Strategies defined","12",
      "Five single-bet, three parlay, four player-prop-combination designs. Every one is status PROPOSED. None has been backtested.","DESIGN_SPEC","design"),

    E("Strategies","Strategies validated","0",
      "Zero. There is no historical price or play-by-play data in the repository, so no backtest has been run and no edge has been measured.","DESIGN_SPEC","design"),

    E("Validation","Validation gates defined","9 (G0-G8)",
      "Data integrity, minimum sample, CLV, significance, out-of-sample holdout, stability, correlation pricing, capacity, and cost. Thresholds are our policy choices and are labelled as design, not as verified facts.","VALIDATION_SPEC","design"),

    E("Validation","Correlation values estimated","0 of 16",
      "Sixteen pairs are enumerated with a stated estimation method, but every value cell is deliberately blank. A guessed correlation would produce confidently wrong parlay prices. Flagged as F-11.","CORRELATION_SPEC","unverified"),

    E("Method","Core anti-luck mechanism","Closing-line value (CLV)",
      "CLV is a far more sensitive skill test than realised profit. In the cited worked example, 1,214 bets with a 2.19% average edge sat about 18.5 standard deviations from chance on CLV, while the same record's raw profit could not rule out luck.","CLV_SKILL_SPORTS_TRADING"),

    E("Method","Practical hurdle implied by CLV research","about 70%",
      "Practitioner estimate: a bettor must beat the fair closing price roughly 70% of the time to have any positive expected value at all.","CLV_SKILL_BET_SINCLAIR"),

    E("Method","Why longshots need a different CLV threshold","Odds-dependent dispersion",
      "Reported standard deviation of the opening-to-closing price ratio was about 0.043 at odds of 1.25 and about 0.14 at odds of 5.0. Longshots move far more.","CLV_SKILL_SPORTS_TRADING"),

    E("Risk","Market efficiency prior","Markets are close to efficient",
      "Academic analysis of real-time line movement found market probability forecasts close to reliable, with deviations concentrated in closing lines; the wider literature finds these markets efficient or inefficient only within transaction-cost bounds. Small edges, demanding evidence.","LINE_MOVEMENT_PAPER"),

    E("Risk","Documented human bias to guard against","Self-assessed skill is over-rated",
      "Peer-reviewed survey: on an 11-point 0=luck to 10=skill scale, DFS participants averaged 6.10 and sports-betting participants 5.90. False perception of control is positively related to gambling problems. Treat our own conviction about a strategy as evidence of nothing.","UNLV_GRRJ"),

    E("Legal","NFL gambling policy — players","No bet on NFL football; no fixing; no sharing non-public information",
      "The three core prohibitions restated by the league. Published summaries of the policy explicitly include player prop bets within the prohibition.","NFL_GAMBLING"),

    E("Legal","NFL gambling policy — coaches, staff, personnel","No betting on any sport",
      "An additional rule that applies only to coaches, staff and personnel. This is stricter than the player rule.","NFL_GAMBLING_SUMMARY"),

    E("Legal","US legal framework","PASPA struck down",
      "The Professional and Amateur Sports Protection Act's prohibition on state authorisation of sports gambling violates the anti-commandeering rule; no provision was severable, so the entire Act was invalid. Murphy v. National Collegiate Athletic Assn., 138 S. Ct. 1461 (2018). Official opinion URL not confirmed — see F-13.","MURPHY_2018","secondary"),

    E("Legal","Status of any actual wagering","UNDECIDED — paper trading assumed",
      "The brief does not say whether real money is involved. The recommended default is MODE = PAPER until Q-01 and Q-02 are answered. Nothing on this site places or has placed a wager.","DESIGN_SPEC","design"),

    E("Governance","Open questions requiring a decision","32 (9 at P0)",
      "Grouped into Legal & Jurisdiction, Capital & Risk, Data & Licensing, Model & Method, Markets & Execution, Competition Design, Operations and Governance. Nine are P0 — the project cannot proceed safely without them.","DESIGN_SPEC","design"),

    E("Governance","Suggestions awaiting review","18",
      "None has been implemented. Per the brief, suggestions must be reviewed and a path chosen before anything is built. Two High-rated exceptions were made for items that are pure review machinery rather than product changes: this page and the Suggestions page itself.","DESIGN_SPEC","design"),

    E("Sizing","Reference for bet sizing","Kelly (1956)",
      "J. L. Kelly Jr., 'A New Interpretation of Information Rate', Bell System Technical Journal 35(4):917-926. The growth-optimal sizing result. The fraction actually used is a policy choice and is not yet set.","KELLY_1956"),

    E("Operations","Roster rules confirmed","53-man active list; 54/55 only via standard elevation",
      "Gameday active list is 48 players if the club has at least eight offensive linemen on it, otherwise 47. A club may expand to 54 or 55 only by elevating practice-squad players, who revert the first business day after the game. NOTE: the same official page gives the per-player seasonal elevation limit as both two and three games — flagged as F-16, no value recorded.","NFL_ROSTER_RULES"),

    E("Operations","Scheduling can change late in the season","Flexible scheduling, Weeks 5-17",
      "Under the 2026 procedures, Sunday night may be flexed up to twice in Weeks 5-10 and any week in Weeks 11-17; Monday night any week in Weeks 12-17; Thursday night up to twice in Weeks 13-17. Decisions are announced 12, 6 or 21 days in advance depending on window, and Week 18 is scheduled after Week 17. Any rest or travel signal must be recomputed after a flex.","NFL_FLEX"),
  ];

  window.X4_EXEC_STATS = { total: facts.length };

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.execSummary = {
    sortKey: "area", sortDir: "asc",
    placeholder: "Filter by area, item or value…",
    facets: [
      { key: "area", label: "Area", options: ["Repo","Season","Data","Blocking gap","Strategies","Validation","Method","Risk","Legal","Governance","Sizing","Operations"] },
      { key: "status", label: "Status", options: ["verified","design","secondary","unverified"] },
    ],
    cols: [
      { key: "area", label: "Area", nowrap: true },
      { key: "item", label: "Item" },
      { key: "value", label: "Value" },
      { key: "detail", label: "Detail" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: facts,
  };
})();
