/* X4 — FLAGGED FOR REVIEW
   Every item here is something this session could NOT verify against an official primary
   source, or an inconsistency between sources that a human should adjudicate.
   Nothing below blocks the merge; all of it is published here with source links so it can
   be reviewed after the site is live. */

(function () {
  const F = (id, area, observation, why, impact, resolution, sev, srcId) => ({
    id, area, observation, why, impact, resolution, sev,
    src: S(srcId), status: "unverified",
  });

  const rows = [
    F("F-01","Repo review",
      "The repository contained no code and no data when this session began: a single commit (4c5280a) on main, containing only README.md with the text '# X4'.",
      "The brief described reviewing and improving an existing site, but there was no site, no data and no prior content to review.",
      "There was nothing to audit line by line, so the entire deliverable was built from scratch rather than corrected.",
      "Confirm whether an earlier version of this project exists elsewhere. If it does, this build should be reconciled with it before further work.",
      "High","REPO_SELF"),

    F("F-02","Data sourcing",
      "There is no official league source for betting prices or lines.",
      "The NFL publishes standings, schedules, injury reports and roster rules, but sportsbook prices are commercial products of licensed operators.",
      "The project's verification policy ('official source only') cannot be satisfied for any odds-derived number. This blocks CLV (gate G2) and every correlation estimate that needs prices.",
      "Either license a market-data provider and cite that provider's own documentation, or leave every odds-derived field blank. Do not mix the two.",
      "High","DESIGN_SPEC"),

    F("F-03","Requirement R-16 / R-17",
      "NFL.com does not publish depth charts: https://www.nfl.com/teams/detroit-lions/depth-chart returns HTTP 404. Club sites do publish depth charts (verified for detroitlions.com), but they list players in order and do NOT label 1st/2nd/3rd/4th string.",
      "The requirement to know when a 2nd, 3rd or 4th string player replaces a starter has no official source that states the string.",
      "R-16 and R-17 are marked blocked. The injury table's 'Depth string' column is blank for every row by design.",
      "License a depth provider that labels order, or derive an ordinal from official club charts plus snap counts — and label every derived value DERIVED, never official (see S-15 / Q-17).",
      "High","NFL_DEPTH_CHART_404"),

    F("F-04","Official timing",
      "The pre-game inactive-list release time (reported by a secondary source as about 90 minutes before kickoff) was NOT confirmed on any official NFL page this session.",
      "Only primary sources are admissible for verified values.",
      "Late-scratch handling cannot be scheduled precisely.",
      "Confirm the requirement on the NFL's official football-operations pages, then record the official URL. Until then the value stays blank.",
      "Medium","INJ_EXPLAINER_WEBMD"),

    F("F-05","Cross-source conflict",
      "NFL.com's official 2026 standings show the Los Angeles Chargers at 0-8. A third-party aggregator's league table omits the Chargers entirely and differs from NFL.com for several clubs.",
      "Two sources disagree. Only one is official.",
      "NFL.com is used throughout and is what is published here. If the aggregator is right, the standings page needs correcting.",
      "Adjudicate by re-reading nfl.com/standings and, if doubt remains, the club's own site. Do not silently average or reconcile.",
      "Medium","AGG_STANDINGS_CONFLICT"),

    F("F-06","Cross-source conflict (same publisher)",
      "Two NFL.com articles report different recovery timelines for Ravens QB Lamar Jackson: one says out 6-9 weeks (right thumb), a later roundup says the Ravens confirmed 6-10 weeks.",
      "The same official publisher carries two different numbers, so neither can be treated as settled.",
      "Any model that consumes recovery timelines would inherit the conflict.",
      "Treat all reported recovery timelines as journalistic, not as official data. Use only the published game status. Left blank here.",
      "Medium","NFL_NEWS_NOV13"),

    F("F-07","Data interpretation",
      "The official Week 10 injury report leaves the Game Status cell empty for a large number of listed players.",
      "The official page does not state on its face what an empty Game Status cell means.",
      "Interpreting it as 'expected to play' would be an inference, not a verified value.",
      "Empty cells are rendered as '— unverified —' and left uninterpreted. Confirm the convention from an official policy page before relying on it.",
      "Medium","NFL_INJURY"),

    F("F-08","Data quality",
      "The official injury report's 'Injuries' column sometimes carries non-injury reasons, e.g. 'Not injury related - resting player' (Jaguars S Jessie Bates, Jaguars DT Jordan Davis; Rams LB Myles Garrett appears with a knee issue plus a resting-player note).",
      "A naive parser would count these as injuries and inflate an injury signal.",
      "Injury-count features would be wrong for the affected clubs.",
      "Any ingestion job must parse the Injuries column as free text and exclude non-injury reasons explicitly.",
      "Medium","NFL_INJURY"),

    F("F-09","Method warning",
      "Roster composition for the 2026 league year differs materially from prior seasons — verified example: Aaron Donald announced retirement in 2024 and then unretired to play for the Los Angeles Rams in 2026.",
      "An analyst carrying prior-season knowledge would wrongly flag these entries as data errors.",
      "False-positive flags would waste review time and, worse, could cause valid data to be discarded.",
      "Rule: never flag a roster, team or injury entry as anomalous on the basis of prior-season knowledge. Flag only internal inconsistencies or conflicts between sources retrieved in the same session.",
      "High","NFL_DONALD_UNRETIRE"),

    F("F-10","Possible stale source page",
      "An NFL.com news roundup (Nov 10) reports that the Broncos traded for Chargers LB Daiyan Henley, yet Henley still appears on the Chargers' Week 10 injury report (LAC at BAL, Monday Nov 16).",
      "The two official pages are inconsistent with each other; one of them is stale.",
      "Personnel-based signals for that game would be wrong.",
      "Re-check both pages closer to kickoff. Do not build a signal on a player whose club is ambiguous.",
      "Medium","NFL_NEWS_NOV10"),

    F("F-11","Requirement R-13",
      "All 16 correlation values on the Correlation page are blank. Zero have been estimated.",
      "Estimating them requires licensed play-by-play and price history, neither of which is in the repository.",
      "Parlay and same-game-combination strategies (S-06, S-07, S-08) cannot be priced. Gate G6 fails closed.",
      "Answer Q-09, Q-11 and Q-14, then estimate with a published window and standard error. Never substitute a plausible-looking number.",
      "High","CORRELATION_SPEC"),

    F("F-12","Requirement R-08",
      "The leaderboard rewards are undefined: no prize, no funding source, no eligibility terms.",
      "These are business decisions, not engineering ones.",
      "The competition cannot be launched as specified.",
      "Answer Q-20 and Q-21, then fill in the reward ladder on the Leaderboard page.",
      "Medium","DESIGN_SPEC"),

    F("F-13","Citation completeness",
      "Murphy v. National Collegiate Athletic Assn., 138 S. Ct. 1461 (2018) is cited by case name and reporter citation, but the official supremecourt.gov opinion URL was NOT confirmed this session.",
      "Only sources actually retrieved may be cited with a URL.",
      "A reader cannot click through to the primary document from that row.",
      "Retrieve and confirm the official opinion URL from supremecourt.gov, then replace the homepage link on the Source Register row.",
      "Low","MURPHY_2018"),

    F("F-14","Interpretation caution",
      "On the official 2026 standings page, clubs have played different numbers of games (8 or 9) because of bye weeks and the Thursday night game. Points-for and points-against are therefore not like-for-like across clubs.",
      "Comparing raw PF/PA across clubs at this point in the season is misleading, but the page presents them in one table.",
      "Any model consuming PF or PA as a season-to-date rate must normalise by games played.",
      "Normalise all counting statistics by games played before use. Flagged so the normalisation is not forgotten.",
      "Medium","NFL_STANDINGS"),

    F("F-15","Scope",
      "No odds, no play-by-play, no snap-count and no prop-market data exists anywhere in this repository.",
      "Every strategy in the catalog is therefore a hypothesis with an entry rule, not a result.",
      "Nothing in the Strategy Catalog should be read as evidence that a strategy works.",
      "Answer Q-09 through Q-13 before treating any strategy row as more than a proposal.",
      "High","DESIGN_SPEC"),
    F("F-16","Cross-source conflict (same publisher)",
      "The NFL's own contract-language page states the practice-squad standard elevation addendum 'can be used by a team for a maximum of two regular-season or postseason games per player per season', and then, in the following paragraph, that 'each practice squad player can be elevated for a maximum of three regular season games in the same League Year'.",
      "The same official page gives two different limits, so neither can be recorded as a verified value.",
      "A personnel model that assumes the wrong limit will mis-forecast late-week availability for practice-squad players.",
      "Confirm the correct limit with the NFL's football-operations team or the current CBA text. Until then no value is recorded — the Rules page on this site quotes both sentences verbatim.",
      "Medium","NFL_ROSTER_RULES"),
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.flagged = {
    sortKey: "id", sortDir: "asc",
    placeholder: "Filter by item, area, severity…",
    facets: [
      { key: "area", label: "Area", options: ["Repo review","Data sourcing","Requirement R-16 / R-17","Official timing","Cross-source conflict","Cross-source conflict (same publisher)","Data interpretation","Data quality","Method warning","Possible stale source page","Requirement R-13","Requirement R-08","Citation completeness","Interpretation caution","Scope"] },
      { key: "sev", label: "Severity", options: ["High","Medium","Low"] },
    ],
    cols: [
      { key: "id", label: "ID", nowrap: true },
      { key: "area", label: "Area", nowrap: true },
      { key: "observation", label: "What was observed" },
      { key: "why", label: "Why it is flagged" },
      { key: "impact", label: "Impact" },
      { key: "resolution", label: "Proposed resolution" },
      { key: "sev", label: "Severity", nowrap: true },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: rows,
  };

  window.X4_FLAG_COUNT = rows.length;
  window.X4_FLAG_STATS = {
    total: rows.length,
    high: rows.filter(r => r.sev === "High").length,
    medium: rows.filter(r => r.sev === "Medium").length,
    low: rows.filter(r => r.sev === "Low").length,
  };
})();
