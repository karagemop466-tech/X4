/* X4 — CORRELATION REFERENCE
   Requirement R-13 (determine correlation values) and R-10 (parlays).

   POLICY: THIS PROJECT DOES NOT PUBLISH A CORRELATION NUMBER IT HAS NOT ESTIMATED.
   Every `value` cell below is intentionally empty and renders as "— unverified —".
   The `hypothesisedSign` column is a stated HYPOTHESIS, not a measurement, and is
   labelled as such. Inventing a plausible-looking number here would be the single most
   damaging thing this project could do, because parlay pricing is entirely driven by it
   and a wrong correlation produces a confidently wrong price.

   The `estimator` and `dataRequired` columns say exactly how each value will be
   produced once Q-09, Q-11 and Q-14 are answered. */

(function () {
  const C = (id, pair, kind, sign, whySign, estimator, dataRequired, window) => ({
    id, pair, kind,
    hypothesisedSign: sign,
    whySign,
    value: "",        // NOT ESTIMATED — deliberately blank
    ci: "",           // NOT ESTIMATED — deliberately blank
    n: "",            // NOT ESTIMATED — deliberately blank
    estimator, dataRequired, window,
    status: "unverified",
    src: S("CORRELATION_SPEC"),
  });

  const rows = [
    C("C-01","Favourite covering the spread  ↔  game going over the total","Same game",
      "negative",
      "A favourite covering usually means a controlled, lower-scoring script; an underdog covering often means a higher-scoring game. Direction is a hypothesis only.",
      "Tetrachoric / phi correlation on the joint settle outcomes (cover yes/no × over yes/no), pooled over games with comparable closing spreads.",
      "Play-by-play or game results plus closing spread and closing total per game.","Not set (Q-15)"),

    C("C-02","Team A moneyline  ↔  Team A total (team total, not game total)","Same game",
      "positive",
      "The team scoring more is more likely to win. Direction is a hypothesis only.",
      "Joint distribution of team points and margin; estimate via copula or empirical joint frequencies.",
      "Final scores and team totals per game.","Not set (Q-15)"),

    C("C-03","Quarterback passing yards  ↔  his primary receiver's receiving yards","Same game, player props",
      "positive",
      "Receiving yards are a component of passing yards, so they are mechanically linked, not merely correlated.",
      "Pearson / Spearman on per-game paired prop outcomes; note the mechanical component means this is a structural relationship, not a free parameter.",
      "Per-game player statistics and player-prop market results.","Not set (Q-15)"),

    C("C-04","Opposing receiver's receiving yards  ↔  that receiver's team total","Same game, player props",
      "positive",
      "A receiver's production is a share of his team's total offence.",
      "Regression of receiver yards on team total with team and opponent fixed effects; report the partial correlation.",
      "Per-game team and player statistics.","Not set (Q-15)"),

    C("C-05","Running back rushing attempts  ↔  team total","Same game, player props",
      "positive",
      "More rushing volume is associated with offensive success and with a game script that keeps the offence on the field.",
      "As C-04, with a game-script control (point differential entering the fourth quarter).",
      "Per-game team and player statistics, plus drive-level data for the game-script control.","Not set (Q-15)"),

    C("C-06","Game total  ↔  total sacks in the same game","Same game, props",
      "negative",
      "Sacks end drives and suppress scoring; more sacks implies fewer points. Direction is a hypothesis only.",
      "Poisson-style joint model or Spearman correlation on per-game counts.",
      "Per-game team statistics.","Not set (Q-15)"),

    C("C-07","Leg A (game X spread)  ↔  Leg B (game Y spread), different games, no shared team","Cross game",
      "approximately zero",
      "Different games with no shared participants have no mechanical linkage. Any observed non-zero value should be treated as sampling noise unless it persists.",
      "Empirical correlation of settle outcomes across independent games; test against zero rather than assuming zero.",
      "Game results with a matching key that guarantees no shared team, no shared division race, and no shared weather system.","Not set (Q-15)"),

    C("C-08","Leg A (game X)  ↔  Leg B (game Y), games with a direct playoff-implication dependency","Cross game",
      "unknown",
      "Some late-season games are dependent through playoff seeding: the effort level or play-calling in one can depend on the other's result. Sign is genuinely unknown.",
      "Restrict to games with a documented seeding dependency, then estimate. Do not extrapolate to ordinary weeks.",
      "Game results plus official standings and tiebreaker rules to identify dependency weeks.","Not set (Q-15)"),

    C("C-09","Two legs involving the SAME team in the SAME game (e.g. team total and side)","Same game, correlated",
      "positive",
      "Both legs depend on the same team's scoring, so they are strongly and mechanically linked.",
      "Empirical joint distribution; this is typically the largest correlation a same-game parlay will contain and must never be assumed away.",
      "Per-game results for both markets.","Not set (Q-15)"),

    C("C-10","Outdoor game total  ↔  adverse weather","Exogenous driver",
      "negative",
      "Wind and precipitation suppress passing and scoring. Direction is a hypothesis only.",
      "Regression of realised total on an official weather observation, controlling for the closing total (which should already embed the forecast).",
      "Official game-day weather observations and closing totals.","Not set (Q-15)"),

    C("C-11","Starting-QB absence  ↔  team total","Injury-driven",
      "negative",
      "A backup quarterback is generally expected to produce less offence than the starter he replaces. Direction is a hypothesis only.",
      "Difference in realised team total with the starter versus with the replacement, matched on opponent defensive quality.",
      "Official injury reports, official participation data, and realised team totals.","Not set (Q-15)"),

    C("C-12","Multiple defensive-back absences  ↔  opposing passing yards","Injury-driven",
      "positive",
      "Weaker pass coverage should concede more passing yards. Direction is a hypothesis only.",
      "As C-11, with the count of absent defensive starters as the treatment variable.",
      "Official injury reports, a starter/backup label (Q-17), and per-game passing statistics.","Not set (Q-15)"),

    C("C-13","Offensive-line absences  ↔  pressure rate allowed","Injury-driven",
      "positive",
      "Weaker pass protection should concede more pressure. Direction is a hypothesis only.",
      "As C-12, restricted to offensive-line positions (T, G, C).",
      "Official injury reports, a starter/backup label (Q-17), and pressure-rate data.","Not set (Q-15)"),

    C("C-14","Leg returns within the SAME week across all active strategies","Portfolio",
      "unknown",
      "Strategies that fire on the same underlying signal are not independent even across different games. This is the correlation that most often breaks a portfolio.",
      "Estimate the correlation matrix of per-week strategy returns directly, rather than inferring it from leg-level correlations.",
      "Per-week strategy return series for every active strategy.","Not set (Q-15)"),

    C("C-15","Model error  ↔  market error","Model",
      "unknown",
      "If our errors are correlated with the market's errors, our model adds nothing; if they are independent, a combination is genuinely better than either alone.",
      "Correlation of (our forecast error) with (market implied forecast error) on the same games.",
      "Our own model outputs plus closing prices.","Not set (Q-15)"),

    C("C-16","Opening price  ↔  closing price","Market microstructure",
      "positive",
      "Prices move and the closing price contains the opening price's information. Magnitude matters for how much CLV can exist.",
      "Regression of closing on opening; the residual spread is what a CLV strategy is competing for.",
      "Opening and closing prices per market.","Not set (Q-15)"),
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.correlation = {
    sortKey: "id", sortDir: "asc",
    placeholder: "Filter by pair, type…",
    facets: [
      { key: "kind", label: "Type", options: ["Same game","Same game, player props","Same game, props","Same game, correlated","Cross game","Exogenous driver","Injury-driven","Portfolio","Model","Market microstructure"] },
      { key: "hypothesisedSign", label: "Hypothesised sign", options: ["positive","negative","approximately zero","unknown"] },
      { key: "status", label: "Status", options: ["unverified","verified"] },
    ],
    cols: [
      { key: "id", label: "ID", nowrap: true },
      { key: "pair", label: "Pair" },
      { key: "kind", label: "Type", nowrap: true },
      { key: "hypothesisedSign", label: "Hypothesised sign (NOT measured)" },
      { key: "whySign", label: "Reasoning (hypothesis, not evidence)" },
      { key: "value", label: "Correlation value" },
      { key: "ci", label: "95% CI" },
      { key: "n", label: "n" },
      { key: "estimator", label: "How it will be estimated" },
      { key: "dataRequired", label: "Data required" },
      { key: "window", label: "Estimation window" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: rows,
  };

  window.X4_CORR_COUNT = rows.length;
  window.X4_CORR_ESTIMATED = rows.filter(r => r.value !== "").length;
})();
