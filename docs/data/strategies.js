/* X4 — STRATEGY CATALOG
   Requirement R-07 (research and develop strategies that generate useful signals),
   R-09 (single bets), R-10 (parlays), R-11 (player-prop combos).

   HONEST STATUS: every strategy here is status "proposed". NOT ONE has been backtested,
   because the repository contains no historical play-by-play, participation or price data
   (see Q-09, Q-10, Q-11). A proposed strategy is a hypothesis with an entry rule, not a
   result. Do not read any row on this page as evidence that the strategy works.

   `expectedEdge` is deliberately blank everywhere. It has not been measured. */

(function () {
  const St = (id, name, type, market, signal, hypothesis, entryRule, minN, gates, corr, srcId) => ({
    id, name, type, market, signal, hypothesis, entryRule, minN, gates, corr,
    expectedEdge: "",          // not measured — intentionally blank
    realisedCLV: "",           // not measured — intentionally blank
    status: "proposed",
    reason: "No historical price or play-by-play data in the repo; backtest not run (Q-09, Q-10, Q-11).",
    src: S(srcId),
  });

  const rows = [
    /* ---------------- SINGLE BETS (R-09) ---------------- */
    St("S-01","Closing-line disagreement — side","Single","Point spread / moneyline",
      "Difference between our originated fair price and the market price, measured after de-vig.",
      "If our model price is more accurate than the market's on a narrow, well-defined subset of games, the disagreement is information, not noise.",
      "Bet only when |our fair price − de-vigged market price| exceeds the estimated model error, AND the disagreement exceeds the round-trip cost.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G7,G8","n/a","DESIGN_SPEC"),

    St("S-02","Closing-line disagreement — total","Single","Game total (over/under)",
      "Same as S-01 but on the total, where weather, pace and personnel are the dominant drivers.",
      "Totals are less efficiently priced than sides in some regimes because public money concentrates on sides.",
      "Same threshold rule as S-01, applied to the total.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G7,G8","n/a","DESIGN_SPEC"),

    St("S-03","Late-week line movement fade","Single","Point spread",
      "Direction and magnitude of price movement from the opening number to the closing number, with no model opinion attached.",
      "Some late movement is informed (professional money) and some is not (public sentiment). Fading the latter is the hypothesis.",
      "Requires a labelled dataset of movement causes. NOT IMPLEMENTABLE until Q-11 and Q-12 are answered — the cause labels do not exist.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G7,G8","n/a","LINE_MOVEMENT_PAPER"),

    St("S-04","Rest / scheduling disadvantage","Single","Point spread / moneyline",
      "Official schedule data: short weeks, bye-week context, and travel.",
      "Teams on a short week after a road game are systematically under-priced by a small amount.",
      "Entry when the official schedule shows a short-week road-to-home or road-to-road turnaround. Schedule data is available now (NFL.com).",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G7,G8","n/a","NFL_SCHED"),

    St("S-05","Bye-week return","Single","Point spread / moneyline",
      "Whether a team is coming off its bye, from the official 'Teams on Bye' list.",
      "Post-bye teams are believed to hold a preparation advantage; the question is whether the market already prices it.",
      "Entry when a team is in its first game after appearing on the official bye list. Verified bye data is available per week (NFL.com).",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G7,G8","n/a","NFL_SCHED"),

    /* ---------------- PARLAYS (R-10) ---------------- */
    St("S-06","Positive-expectation same-game combo","Parlay","Same-game side + total",
      "Two legs from the SAME game whose outcomes are mechanically linked (e.g. a high total and a favourite covering).",
      "Books price correlated same-game legs conservatively; where the true correlation exceeds the priced correlation, the combo is mispriced.",
      "REQUIRES a verified correlation estimate before a single ticket is written. Blocked on Q-14.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G6,G7,G8","Side–total correlation within a game","CORRELATION_SPEC"),

    St("S-07","Cross-game low-correlation accumulator","Parlay","Independent legs from different games",
      "Several legs chosen from games with no mechanical linkage.",
      "Where legs are genuinely independent, the parlay price compounds the book margin — which is normally a DISADVANTAGE. This strategy exists to test whether the compounding is ever favourable after each leg independently clears its own edge gate.",
      "Only allow a leg into the parlay if that leg independently passes the single-bet gates. Otherwise reject.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G6,G7,G8","Cross-game correlation ≈ 0 (to be estimated)","CORRELATION_SPEC"),

    St("S-08","Correlation-aware parlay sizing","Parlay","Any multi-leg",
      "Not a selection strategy — a sizing rule that shrinks stake as the estimated correlation between legs rises.",
      "Correlated legs increase variance; a naive stake size on a correlated parlay is materially larger than intended.",
      "Compute the portfolio variance using the estimated correlation matrix, then size to a target volatility.",
      "Not set (Q-16)","G0,G1,G6,G7","Full leg-leg correlation matrix","KELLY_1956"),

    /* ---------------- PLAYER PROP COMBOS (R-11) ---------------- */
    St("S-09","Backup-QB pass-volume suppression","Prop combo","QB passing yards / attempts, and WR- correlated unders",
      "Official injury report: a starting QB is Out or Doubtful, and the named replacement is a backup.",
      "When a starter is replaced, the replacement's expected volume is not the starter's, and correlated receiver props move with it.",
      "Trigger only on an official game status of Out or Doubtful for the listed starting QB. Current week's verified trigger set is on the Injuries page.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G6,G7,G8","QB-to-receiver prop correlation","NFL_INJURY"),

    St("S-10","Secondary-deficiency exploitation","Prop combo","Opposing skill-position props vs a defence missing starters",
      "Official injury report: multiple defensive backs or front-seven starters listed Out.",
      "A defence missing multiple starters concedes more to the opposing primary receiver or runner than the market implies.",
      "Trigger when the official report shows two or more starters at the same defensive position group listed Out. Requires a starter/backup label — blocked on Q-17.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G6,G7,G8","Defence-to-opponent-prop correlation","NFL_INJURY"),

    St("S-11","Offensive-line injury → sack / pressure prop","Prop combo","Sacks, QB pressures, team total",
      "Official injury report: offensive line starters (T, G, C) listed Out.",
      "Offensive-line absences degrade pass protection; pressure-rate and team-total markets are slow to adjust.",
      "Trigger on two or more offensive-line starters listed Out on the official report.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G6,G7,G8","OL-absence to pressure-rate correlation","NFL_INJURY"),

    St("S-12","Workhorse-back concentration","Prop combo","RB rushing attempts / yards, and receiving unders",
      "Official injury report: the primary running back is Out and the depth behind him is thin.",
      "A thin backfield concentrates volume on one replacement, whose prop lines are set off a committee baseline.",
      "Trigger when the primary RB is Out AND the club depth chart shows fewer than two healthy alternatives. Requires a depth source — blocked on Q-17.",
      "Not set (Q-16)","G0,G1,G2,G3,G4,G5,G6,G7,G8","RB-volume to team-total correlation","NFL_INJURY"),
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.strategies = {
    sortKey: "id", sortDir: "asc",
    placeholder: "Filter by strategy, market, signal…",
    facets: [
      { key: "type", label: "Bet type", options: ["Single","Parlay","Prop combo"] },
      { key: "status", label: "Status", options: ["proposed","backtested","validated","live","retired"] },
    ],
    cols: [
      { key: "id", label: "ID", nowrap: true },
      { key: "name", label: "Strategy" },
      { key: "type", label: "Type", nowrap: true },
      { key: "market", label: "Market" },
      { key: "signal", label: "Signal source" },
      { key: "hypothesis", label: "Hypothesis" },
      { key: "entryRule", label: "Entry rule" },
      { key: "minN", label: "Min N", nowrap: true },
      { key: "gates", label: "Gates" },
      { key: "corr", label: "Correlation input required" },
      { key: "expectedEdge", label: "Expected edge (measured)" },
      { key: "realisedCLV", label: "Realised CLV" },
      { key: "_status", label: "Status" },
      { key: "reason", label: "Why not validated" },
      { key: "_src", label: "Source" },
    ],
    rows: rows,
  };

  /* Status roll-up rendered above the table on the page. */
  window.X4_STRATEGY_SUMMARY = {
    total: rows.length,
    proposed: rows.filter(r => r.status === "proposed").length,
    backtested: 0,
    validated: 0,
    live: 0,
  };
})();
