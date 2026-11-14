/* X4 — SUGGESTIONS REGISTER (review queue)
   Requirement R-03: a dedicated section where suggestions can be reviewed and the best
   path chosen BEFORE anything is implemented.

   Workflow: Proposed → Under review → Approved → Implemented   (or Rejected / Deferred)
   Hard rule encoded on the page: nothing with status "Proposed" may be implemented.
   Every row below currently sits at "Proposed" — i.e. nothing here has been built yet,
   apart from this review mechanism itself.

   `src` points to the official source that motivates the suggestion (or to this site's
   own design spec where the row is our engineering proposal). */

(function () {
  const Sg = (id, cat, title, problem, proposal, benefit, risk, effort, deps, decision, rating, srcId) =>
    ({ id, cat, title, problem, proposal, benefit, risk, effort, deps, decision, rating,
       status: "proposed", src: S(srcId) });

  const rows = [
    Sg("S-01","Governance","Lock the operating mode: paper trading vs real money",
      "The brief asks for a leaderboard with rewards, but never states whether real money moves. Every downstream design decision depends on this.",
      "Add a single top-level switch in the config: MODE = PAPER | LIVE. Default PAPER. Refuse to start in LIVE until Q-01 and Q-02 are answered and recorded.",
      "Removes legal and financial ambiguity before any engineering is done.",
      "If left undecided, someone will eventually ship real stakes by accident.",
      "XS","Q-01, Q-02","Approve MODE default = PAPER and name who may flip it.","High","DESIGN_SPEC"),

    Sg("S-02","Governance","Add an eligibility self-check before any wagering feature is enabled",
      "NFL players, coaches, staff, officials and league personnel are barred from betting on NFL football; for coaches/staff/personnel the ban covers any sport.",
      "Require an explicit attestation that no operator is an NFL-affiliated person. If the attestation fails, permanently pin MODE = PAPER.",
      "Prevents an integrity breach that would be unrecoverable.",
      "None material.","XS","Q-02","Approve the attestation gate.","High","NFL_GAMBLING_SUMMARY"),

    Sg("S-03","Governance","Model taxation as a first-class cost in the edge calculation",
      "A pre-tax edge can disappear after tax, yet most backtests ignore tax entirely.",
      "Add a NET_OF_TAX field per bet and require every gate to be evaluated net of tax.",
      "Stops strategies being promoted on an edge that does not survive tax.",
      "Requires the jurisdiction to be known (Q-03).","S","Q-03","Approve: gates evaluate net-of-tax ROI only.","Medium","DESIGN_SPEC"),

    Sg("S-04","Governance","Define an integrity-escalation path for anomalous market movement",
      "A signal engine may detect line movement that suggests non-public information or manipulation. There is currently no defined response.",
      "Log the observation, do not act on it, and escalate per the operator's own terms of service and the league's integrity framework.",
      "Keeps the project on the right side of integrity obligations.",
      "None.","S","Q-04","Approve: detect-and-escalate, never detect-and-trade.","High","NFL_GAMBLING_SUMMARY"),

    Sg("S-05","Risk","Fix a fractional-Kelly staking policy",
      "Full Kelly is maximally aggressive to model error; there is currently no sizing rule at all.",
      "Set stake = f × Kelly, with f fixed for the season and recorded. Reference: Kelly (1956).",
      "Converts 'size the bet' from an ad-hoc judgement into a reproducible rule.",
      "Still needs the bankroll and f to be chosen by the user.","S","Q-05, Q-06","Approve the fraction f (design default: 0.25) and the bankroll convention.","High","KELLY_1956"),

    Sg("S-06","Risk","Introduce a hard limits matrix",
      "No drawdown, exposure or per-market caps exist, so a validation failure would be unbounded.",
      "Limits: max daily exposure, max single-market stake, max concurrent same-game exposure, season stop-loss, and an automatic freeze on breach.",
      "Bounds the loss from a strategy that passes backtest but fails live.",
      "A stop-loss can lock in losses that would otherwise recover; that is intentional and should be accepted explicitly.","M","Q-07","Approve each limit value.","High","DESIGN_SPEC"),

    Sg("S-07","Validation","Make promotion-to-live a gated event with an audit record",
      "There is currently nothing that prevents an unvalidated strategy reaching real stakes.",
      "Promotion requires: all gates G0-G8 passed, a named approver, a recorded timestamp, and the exact model version hash.",
      "Creates accountability for the single riskiest action in the system.",
      "Adds process friction by design.","S","Q-08, Q-25","Approve the promotion checklist and name the approver.","High","DESIGN_SPEC"),

    Sg("S-08","Data","Resolve data licensing before building any model",
      "Play-by-play, participation and price data are all licensed. Building first and licensing later risks throwing the work away.",
      "Inventory required datasets, then read the NFL's own licensing terms and each vendor's documentation before ingestion.",
      "Avoids rework and avoids publishing data we are not licensed to publish.",
      "May delay modelling.","M","Q-09, Q-28","Approve the licensing budget and the permitted republication scope.","High","NFL_ROSTER_RULES"),

    Sg("S-09","Data","Size the validation gates to the data we can actually obtain",
      "Gates written for a sample we cannot obtain are theatre.",
      "After Q-10 is answered, set the minimum-sample gate to a value achievable with the real dataset, and record the resulting statistical power.",
      "Makes the gates honest rather than aspirational.",
      "May force us to admit some strategies cannot be validated at all.","S","Q-10","Approve the minimum-sample value.","High","DESIGN_SPEC"),

    Sg("S-10","Data","Contract a price feed and make the closing line mandatory",
      "There is no official league source for betting prices, and without a closing price the single best skill test (CLV) is unavailable.",
      "Choose a licensed provider; capture opening, strike-time and closing price for every market we model.",
      "Unblocks the CLV gate, which is the core anti-luck mechanism.",
      "Cost; and no provider has been evaluated yet.","M","Q-11","Approve a provider and its cost.","High","CLV_SKILL_SPORTS_TRADING"),

    Sg("S-11","Data","Build the bet-log schema first, before any strategy code",
      "If the log does not capture what the gates need, no result can ever be validated retroactively.",
      "Immutable append-only log: strategy_id, model_version, market_id, timestamp_utc, price_at_strike, closing_price, stake, result, and a mandatory non-null constraint on closing_price.",
      "Makes every later gate computable. This is the highest-leverage engineering task in the project.",
      "None.","M","Q-12","Approve the schema as the single source of truth for scoring.","High","DESIGN_SPEC"),

    Sg("S-12","Markets","Restrict season one to markets we can actually price",
      "Prop-combination strategies are in the brief, but prop price history may not be available.",
      "Ship game-level markets first; add props only once Q-13 is answered positively.",
      "Prevents a strategy catalog full of unpriceable entries.",
      "Narrows scope in year one.","S","Q-13, Q-30","Approve a season-one market list.","Medium","DESIGN_SPEC"),

    Sg("S-13","Model","Estimate correlations empirically and publish the estimation window with each value",
      "The brief asks for correlation values. Inventing them would be worse than not having them, because parlay pricing would be confidently wrong.",
      "Estimate from licensed play-by-play + price history; publish n, window, estimator and standard error next to every value; leave the value blank if it cannot be estimated.",
      "Turns the weakest part of the system into an auditable one.",
      "Blocked until Q-11 and Q-14 are answered; some correlations will remain unestimatable.","L","Q-14, Q-15","Approve the estimation protocol and the policy of never substituting a guessed value.","High","LINE_MOVEMENT_PAPER"),

    Sg("S-14","Competition","Set a minimum sample before a strategy may appear on the leaderboard",
      "A leaderboard that ranks small samples ranks luck.",
      "Minimum N before a strategy is ranked; below N it is displayed as 'provisionally tracked, unranked'.",
      "Makes the leaderboard a ranking of evidence rather than of noise.",
      "Slow initial population of the board.","S","Q-16, Q-27","Approve N and the probation length.","High","CLV_SKILL_BET_SINCLAIR"),

    Sg("S-15","Data","Build a depth/string pipeline with an explicit 'derived, not official' label",
      "NFL.com does not publish depth charts; club sites publish ordered lists without string labels. The 2nd/3rd/4th-string requirement therefore has no official numeric source.",
      "Ingest official club depth charts + snap counts, derive an ordinal depth, and label every derived value DERIVED. Never present a derived value as official.",
      "Delivers the requirement while being honest about provenance.",
      "Derived depth will sometimes be wrong, especially early in a week.","L","Q-17, Q-18","Approve: derive and label, do not fabricate.","High","LIONS_DC"),

    Sg("S-16","Execution","Treat account limits as the binding capacity constraint",
      "Consistent winning at a licensed operator attracts staking limits. Capacity, not edge, usually ends a betting operation.",
      "Track per-operator, per-market acceptance and limits; treat realised capacity as a gate (G7) rather than an afterthought.",
      "Makes the plan survivable rather than theoretical.",
      "None.","M","Q-19, Q-30","Approve: capacity is a scored gate, not a footnote.","Medium","DESIGN_SPEC"),

    Sg("S-17","Competition","Define the reward ladder and its funding before publishing the leaderboard",
      "'Rewards for top performing strategies' is undefined: no prize, no funding source, no eligibility terms.",
      "Publish a fixed reward ladder, an explicit funding source, and eligibility terms tied to passing the gates — not to raw profit.",
      "Aligns incentives with skill rather than with variance-chasing.",
      "Prize terms may have legal implications depending on jurisdiction.","M","Q-20, Q-21","Approve the ladder, the funding source, and internal-only vs external entrants.","High","DESIGN_SPEC"),

    Sg("S-18","Competition","Add a multiplicity correction to the leaderboard scoring rule",
      "If entrants may submit many strategies, the best of N submissions will look skilled under pure chance. Panel guidance is to test the actual record against the distribution of possible histories, and to require persistence.",
      "Cap submissions per entrant, score on a risk-adjusted statistic, and apply an explicit multiple-comparisons correction to promotion decisions.",
      "Prevents the leaderboard from systematically rewarding the luckiest entrant.",
      "Reduces the number of strategies that can be promoted.","M","Q-22","Approve the submission cap and the correction method.","High","LUCK_SKILL_PANEL"),
  ];

  window.X4_SUGGESTION_STATS = {
    total: rows.length,
    proposed: rows.filter(r => r.status === "proposed").length,
    approved: rows.filter(r => r.status === "approved").length,
    rejected: rows.filter(r => r.status === "rejected").length,
    high: rows.filter(r => r.rating === "High").length,
  };

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.suggestions = {
    sortKey: "id", sortDir: "asc",
    placeholder: "Filter by title, category, dependency…",
    facets: [
      { key: "cat", label: "Category", options: ["Governance","Risk","Validation","Data","Markets","Model","Competition","Execution"] },
      { key: "rating", label: "Rating", options: ["High","Medium"] },
      { key: "effort", label: "Effort", options: ["XS","S","M","L"] },
      { key: "status", label: "Review status", options: ["proposed","under review","approved","deferred","rejected"] },
    ],
    cols: [
      { key: "id", label: "ID", nowrap: true },
      { key: "title", label: "Suggestion" },
      { key: "cat", label: "Category", nowrap: true },
      { key: "problem", label: "Problem it solves" },
      { key: "proposal", label: "Proposal" },
      { key: "benefit", label: "Expected benefit" },
      { key: "risk", label: "Risk / trade-off" },
      { key: "effort", label: "Effort", nowrap: true },
      { key: "deps", label: "Depends on", nowrap: true },
      { key: "decision", label: "Decision required before implementation" },
      { key: "rating", label: "Rating", nowrap: true },
      { key: "_status", label: "Review status" },
      { key: "_src", label: "Source" },
    ],
    rows: rows,
  };
})();
