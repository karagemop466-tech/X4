/* X4 — VALIDATION GATES
   Requirement R-12 (every strategy must pass validation gates) and R-14 (remove luck,
   build selectively skill-based strategies).

   IMPORTANT DISTINCTION, stated once and applied everywhere on the site:
     - The STATISTICAL TECHNIQUES below are established. They are cited.
     - The THRESHOLDS below are OUR POLICY CHOICES. They are not verified facts and are
       labelled "design". They should be reviewed and re-set once Q-10 (dataset size)
       and Q-16 (minimum sample) are answered.

   No strategy has been run through any of these gates. */

(function () {
  const G = (id, name, question, method, threshold, fail, rationale, srcId, status) => ({
    id, name, question, method, threshold, fail, rationale,
    src: S(srcId), status: status || "design",
  });

  const gates = [
    G("G0","Data integrity","Is the data we are about to score on complete and internally consistent?",
      "Schema validation: non-null closing price, non-null strike timestamp, no duplicate market_id per strategy, clock and team identifiers consistent with the official schedule.",
      "0 violations. Any violation voids the run.","Void the run and fix the pipeline.",
      "A gate result computed on broken data is worse than no result, because it looks authoritative.",
      "DESIGN_SPEC"),

    G("G1","Minimum sample","Do we have enough observations for any inference to mean anything?",
      "Hard count of settled bets, plus a power calculation against the minimum effect size we care about.",
      "Not set — must be derived from the real dataset (Q-10, Q-16).","Do not rank; display as 'provisionally tracked, unranked'.",
      "The single most common way a leaderboard ranks luck is by ranking small samples.",
      "CLV_SKILL_BET_SINCLAIR"),

    G("G2","Closing-line value","Did our price beat the price the market finished at?",
      "CLV per bet = (price at strike) / (fair closing price), computed after de-vigging both. Test the mean across the sample against 1.00.",
      "Not set as a numeric threshold yet (Q-24 fixes the de-vig convention first). Direction: mean CLV must exceed 1.00 by more than the round-trip cost.",
      "Reject the strategy.","CLV is a far more sensitive skill test than realised P&L. In the cited worked example, 1,214 bets with a 2.19% average edge sat about 18.5 standard deviations from chance on CLV, while the same record's raw P&L could not rule out luck.",
      "CLV_SKILL_SPORTS_TRADING"),

    G("G3","Significance vs chance","Could this record have arisen by chance?",
      "Two tests, both required: (a) a t-test on per-bet CLV against the null of zero edge; (b) a permutation/bootstrap test of the actual P&L record against the distribution of possible records under the null.",
      "Not set as a numeric threshold yet (Q-23).","Reject.",
      "Plotting the actual record against the null distribution is the standard remedy for 'my record looks good but so would someone's'.",
      "LUCK_SKILL_PANEL"),

    G("G4","Out-of-sample holdout","Does it work on data it has never seen?",
      "Strict temporal split: fit on seasons 1..k-1, test on season k. No parameter may be chosen using holdout data.",
      "Holdout performance must be directionally consistent with the in-sample result.","Reject — do not fall back to the in-sample number.",
      "In-sample edge is nearly free to manufacture. This is the gate that most often kills a strategy, which is the point.",
      "DESIGN_SPEC"),

    G("G5","Stability","Is the effect stable across seasons, or is it one good season?",
      "Per-season CLV and ROI with confidence intervals; compare the dispersion across seasons to the within-season dispersion.",
      "Not set as a numeric threshold yet (Q-15).","Demote to probation rather than reject.",
      "Persistence is one of the recognised markers distinguishing skill from a lucky run.",
      "LUCK_SKILL_PANEL"),

    G("G6","Correlation / parlay pricing","For multi-leg bets, is the correlation correctly priced?",
      "Recompute the parlay price using the estimated leg-leg correlation matrix and compare to the offered price; re-run gates G2 and G3 on the recomputed price.",
      "Requires an estimated correlation with a published estimation window and standard error. If the correlation is unestimated, the parlay CANNOT be priced and the gate fails closed.",
      "Fail closed — do not substitute a guessed correlation.",
      "Correlated legs change both the expected value and the variance. A wrong correlation produces a confidently wrong price.",
      "CORRELATION_SPEC"),

    G("G7","Capacity and limits","Can it actually be executed at the size the backtest assumes?",
      "Measure acceptance rate, effective stake after limits, and slippage between the price we model and the price we get.",
      "Realised capacity must be at least the size the backtest assumed, after observed limits.",
      "Cap the strategy at the realised capacity rather than the modelled capacity.",
      "Account limits, not edge, are what usually ends a betting operation. A backtest that assumes unlimited acceptance is fiction.",
      "DESIGN_SPEC"),

    G("G8","Execution and cost","Does it survive the round-trip cost?",
      "Net-of-cost ROI including the margin, any commission, and tax where applicable.",
      "Net-of-cost, net-of-tax ROI must be positive with a confidence interval excluding zero.",
      "Reject.","A strategy that beats the closing line by less than the cost of crossing it is not a strategy.",
      "DESIGN_SPEC"),
  ];

  const luck = [
    { stat: "Closing-line value (CLV)",
      tests: "Whether our price beat the market's closing price.",
      why: "The strongest practical indicator that a record reflects skill. A conservative measure: if you have it, it is hard to argue your results were luck.",
      thresh: "Not set (Q-24, Q-23)",
      src: S("CLV_SKILL_SPORTS_TRADING"), status: "design" },

    { stat: "Distribution test (permutation / bootstrap)",
      tests: "Where the actual P&L history falls within the distribution of histories possible under the null.",
      why: "Directly answers 'could luck alone have produced this?'. Recommended by practitioners as one of three core skill tests.",
      thresh: "Not set (Q-23)",
      src: S("LUCK_SKILL_PANEL"), status: "design" },

    { stat: "Persistence",
      tests: "Whether performance repeats rather than wandering.",
      why: "The third of the three recognised skill markers. A profit curve that wanders like a random walk is not evidence of skill.",
      thresh: "Not set (Q-15)",
      src: S("LUCK_SKILL_PANEL"), status: "design" },

    { stat: "t-statistic on per-bet edge",
      tests: "Whether mean per-bet CLV differs from 1.00 by more than sampling error.",
      why: "Standard parametric test; complements the distribution test rather than replacing it.",
      thresh: "Not set (Q-23)",
      src: S("CLV_SKILL_SPORTS_TRADING"), status: "design" },

    { stat: "Multiple-comparisons correction",
      tests: "Whether the result survives after accounting for how many strategies were tried.",
      why: "Prevents the leaderboard from systematically promoting the luckiest entrant when many strategies are submitted.",
      thresh: "Not set (Q-22)",
      src: S("LUCK_SKILL_PANEL"), status: "design" },

    { stat: "Perceived-control check (human bias)",
      tests: "Not a model test — a guard against our own judgement.",
      why: "Peer-reviewed survey evidence finds participants in both DFS and sports betting rate their activity as more skill than luck (means 6.10 and 5.90 on an 11-point scale where 10 = pure skill), and that false perception of control is positively related to gambling problems. Treat our own conviction about a strategy as evidence of nothing.",
      thresh: "n/a",
      src: S("UNLV_GRRJ"), status: "verified" },
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.gates = {
    sortKey: "id", sortDir: "asc",
    cols: [
      { key: "id", label: "Gate", nowrap: true },
      { key: "name", label: "Name" },
      { key: "question", label: "Question it answers" },
      { key: "method", label: "Method" },
      { key: "threshold", label: "Threshold" },
      { key: "fail", label: "On failure" },
      { key: "rationale", label: "Why this gate exists" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: gates,
  };

  window.X4_TABLES.luckTests = {
    sortKey: "stat", sortDir: "asc",
    cols: [
      { key: "stat", label: "Statistic" },
      { key: "tests", label: "What it tests" },
      { key: "why", label: "Why it separates skill from luck" },
      { key: "thresh", label: "Threshold" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: luck,
  };
})();
