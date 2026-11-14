/* X4 — OPEN QUESTIONS REGISTER
   "A clear list of questions, information and answers that need to be addressed before
   any decision can reasonably be made, based on the information we already have and do
   not have."

   Columns:
     know   — what is ALREADY established from an official source (status: verified)
     missing— what we do NOT have (status: unverified)
     how    — a concrete method to discover the missing information (suggestion)
   Nothing in the `missing` column has been filled in with a guess. */

(function () {
  const Q = (id, area, question, why, know, missing, how, blocks, pri) =>
    ({ id, area, question, why, know, missing, how, blocks, pri, status: "open" });

  const rows = [
    Q("Q-01","Legal & Jurisdiction","In which jurisdiction will wagering (if any) take place, and is it legal there?",
      "Determines which regulator applies, what data may be used, and whether an internal-only paper-trading mode is required instead of real stakes.",
      "PASPA's prohibition on state authorisation of sports gambling was struck down as violating the anti-commandeering rule, and no provision was severable, so the entire Act was invalid (Murphy v. NCAA, 138 S. Ct. 1461 (2018)).",
      "The user's jurisdiction, age eligibility, and whether any real-money betting is contemplated at all.",
      "Ask the user to select: (a) paper trading only, (b) legal US state, name it, (c) other jurisdiction, name it. Then confirm the current statute on the regulator's own site for that jurisdiction.",
      "R-06, R-07, R-08, S-01","P0"),

    Q("Q-02","Legal & Jurisdiction","Will this system place real wagers, or only record paper trades?",
      "Changes the whole risk surface: bankroll, KYC, tax, record-keeping, and whether 'rewards' are prize money.",
      "The NFL's gambling policy prohibits players, coaches, staff and league personnel from betting on NFL football; the additional rule for coaches/staff/personnel is a ban on betting on ANY sport.",
      "Whether the operator is an NFL-affiliated person (which would bar real wagering outright) and whether the user intends real stakes.",
      "Confirm the user is not a player, coach, club/league staff member or official. If they are, force paper-trading mode permanently and record that in COORDINATION.md.",
      "R-08, S-01, S-02","P0"),

    Q("Q-03","Legal & Jurisdiction","What is the tax treatment of betting / prize winnings in the operating jurisdiction?",
      "Net-of-tax expectation changes the required edge. A strategy with a small pre-tax edge can be negative after tax.",
      "",
      "No value recorded. Not verified from an official source this session.",
      "Pull the current guidance directly from the relevant revenue authority's own site (e.g. the national/state tax authority) rather than secondary summaries.",
      "R-08, S-03","P1"),

    Q("Q-04","Legal & Jurisdiction","Are there integrity-reporting obligations if the system detects anomalous line movement?",
      "A signal engine that flags unusual market movement may create a duty to report; also affects whether we keep or discard such signals.",
      "The NFL runs integrity monitoring and works with its sports-betting partners on that monitoring.",
      "Whether any contractual or regulatory reporting duty attaches to a private model operator.",
      "Read the terms of service of each intended sportsbook and the regulator's integrity rules; do not rely on secondary summaries.",
      "S-04","P2"),

    Q("Q-05","Capital & Risk","What is the bankroll, and is it a fixed amount or a replenishable allocation?",
      "Stake sizing (Kelly or fractional Kelly) is undefined without it, and drawdown limits cannot be set.",
      "Kelly (1956) gives the growth-optimal fraction of capital to wager under arbitrary odds — the standard reference for sizing.",
      "The actual bankroll figure and whether it is capped.",
      "Ask for a number, or default the system to a fixed unit size (e.g. 1 unit = 0.5% of a declared bankroll) so sizing stays defined without exposing the figure on a public site.",
      "R-08, S-05","P1"),

    Q("Q-06","Capital & Risk","What fraction of Kelly should be used?",
      "Full Kelly maximises growth but is extremely volatile and punishes model error; fractional Kelly is the usual practical choice.",
      "Kelly (1956), Bell System Technical Journal 35(4):917-926 — the growth-optimal sizing result.",
      "The chosen multiplier. No value recorded; not verified.",
      "Treat as a policy parameter. Suggested starting point (design, not verified): quarter Kelly. Must be set by the user before going live.",
      "R-14, S-05","P1"),

    Q("Q-07","Capital & Risk","What are the hard stop conditions (max drawdown, max daily exposure, single-market cap)?",
      "Without stop rules, a validation failure becomes an unbounded loss rather than a bounded experiment.",
      "",
      "No limits recorded.",
      "Propose a limits matrix in the Suggestions queue (S-06) and require approval before any live deployment.",
      "R-14, S-06","P1"),

    Q("Q-08","Capital & Risk","How much model risk is acceptable — i.e. what is the tolerance for a strategy that passes gates on historical data but fails live?",
      "Determines how strict the out-of-sample gate must be, and how much capital is allocated to a newly-promoted strategy.",
      "Closing-line value is a far more sensitive test of skill than realised profit/loss: in the worked practitioner example, 1,214 bets with a 2.19% average edge sat ~18.5 standard deviations from chance on CLV, while the same record's raw P&L could not rule out luck.",
      "A numeric tolerance. Not verified.",
      "Set via the promotion rules in the Leaderboard spec; require the user to approve the promotion thresholds.",
      "R-12, R-14, S-07","P1"),

    Q("Q-09","Data & Licensing","Where will official NFL data come from, and under what licence?",
      "Play-by-play, participation and snap data drive every offensive and defensive model; licensing governs whether derived output may be published.",
      "nfl.com publishes standings, schedules and the official injury report; operations.nfl.com publishes roster rules (53-man active list, standard elevation addendum, practice-squad eligibility).",
      "Whether play-by-play, snap counts and participation data are licensed, and on what terms. No licence in place.",
      "Read the NFL's own data/API licensing terms and any official partner programme documentation. Do not scrape in violation of terms of service.",
      "R-06, R-07, S-08","P0"),

    Q("Q-10","Data & Licensing","How much history is available for backtesting, and at what granularity?",
      "Sample size determines whether any strategy can clear the significance gate at all.",
      "A practitioner reference used a 162,672-match odds population for soccer; a worked CLV example used 1,214 bets. These are soccer, not NFL — they indicate the order of magnitude required, not an NFL number.",
      "The size and granularity of the NFL dataset we hold. Not verified — the repo contains no historical dataset.",
      "Inventory what is obtainable under licence, then size the validation gates to that sample rather than the other way round.",
      "R-07, R-12, S-09","P0"),

    Q("Q-11","Data & Licensing","Where will betting lines and prices come from?",
      "Without a price feed there is no line to originate against, and no closing line to measure CLV against.",
      "NEGATIVE FINDING: there is no official league source for betting prices. Lines are commercial products of licensed operators. This is recorded as F-02 on Flagged for Review.",
      "A price-feed provider and its licence. Not verified.",
      "Evaluate official operator APIs / licensed market-data vendors; record the provider's own documentation as the source. Until then, all odds-dependent gates are blocked.",
      "R-06, R-12, R-13, S-10","P0"),

    Q("Q-12","Data & Licensing","Will we store the price at the moment each bet is struck AND the closing price?",
      "CLV cannot be computed without both. This is the single most important field in the whole schema.",
      "CLV is widely treated as the strongest available indicator that a betting record reflects skill rather than luck (expert panel: Buchdahl, Holden, Nenko).",
      "Whether the capture pipeline exists. It does not yet.",
      "Build the bet log schema first (see Suggestions S-11) with immutable timestamps and a mandatory closing-price field; a bet without a closing price must be unscoreable.",
      "R-12, R-14, S-11","P0"),

    Q("Q-13","Data & Licensing","Do we have player-prop market history, or only game-level markets?",
      "Prop-combination strategies (R-11) are impossible to validate without prop-level price history.",
      "",
      "No prop history in the repo. Not verified.",
      "Check whether the chosen price-feed provider retains prop-level history; if not, restrict the first season to game-level markets.",
      "R-11, S-12","P1"),

    Q("Q-14","Model & Method","On what sample will correlation values be estimated, and over what window?",
      "Parlay and same-game-combo pricing is entirely dependent on correlation. Guessing a correlation is worse than refusing to price.",
      "Academic work on real-time line movement finds betting market forecasts were close to reliable, with deviations concentrated in closing lines — i.e. these markets are near-efficient and mispriced edges are small.",
      "Every numeric correlation value for this project. Deliberately blank.",
      "Estimate empirically from the licensed play-by-play and price history once Q-09/Q-11 are answered; publish the estimation window and standard error alongside each value.",
      "R-13, S-13","P0"),

    Q("Q-15","Model & Method","Will correlation be estimated per-season, rolling, or pooled across seasons?",
      "Pooling increases sample size but assumes stability; per-season avoids that assumption but is noisy.",
      "",
      "Not decided. Not verified.",
      "Estimate both and report the disagreement as a stability metric in gate G5.",
      "R-13, S-13","P1"),

    Q("Q-16","Model & Method","What is the minimum sample before a strategy is allowed to be scored on the leaderboard?",
      "Too small a sample and the leaderboard ranks noise; too large and nothing ever gets ranked.",
      "Significance testing on raw P&L separates skill from luck far more slowly than CLV does; even after 1,000 bets there was roughly a 1-in-10 chance that luck alone produced a 2% profit where the expectation was a 2% loss.",
      "The threshold for this project. Not verified.",
      "Set a minimum in the Leaderboard spec and require approval (S-14).",
      "R-08, R-14, S-14","P0"),

    Q("Q-17","Data & Licensing","Where will depth-chart / second-string information come from?",
      "The requirement to know when a 2nd/3rd/4th-string player is replacing a starter cannot be met without a depth source.",
      "NEGATIVE FINDING: NFL.com returns 404 for /teams/<club>/depth-chart. Individual club sites do publish depth charts (verified for detroitlions.com), but they list players in order WITHOUT labelling 1st/2nd/3rd/4th string.",
      "A source that labels depth strings. Not verified. Recorded as F-03.",
      "Either (a) license a provider that labels depth order, or (b) derive order from official club depth charts plus snap-count data and label every derived value as derived, not official.",
      "R-16, R-17, S-15","P0"),

    Q("Q-18","Data & Licensing","How will in-game elevations and late scratches be captured before kickoff?",
      "The most valuable injury information arrives after the last injury report.",
      "Official rule: practice-squad players may be elevated for a maximum of three regular-season games per league year, and a club may expand to 54 or 55 players only via the standard elevation addendum.",
      "Timing of the official inactive list. A secondary source says ~90 minutes before kickoff; this was NOT confirmed on an official page.",
      "Confirm the exact release requirement on the NFL's official football-operations pages; until confirmed, leave the value blank (see F-04).",
      "R-15, R-16, S-15","P1"),

    Q("Q-19","Markets & Execution","Which sportsbooks will be used, and do they permit this type of activity?",
      "Account limits and closures are the real capacity constraint on any winning strategy.",
      "",
      "Not answered. Not verified.",
      "Read each operator's own terms; assume that consistent winning will attract limits and plan capacity accordingly.",
      "R-06, R-08, S-16","P1"),

    Q("Q-20","Competition Design","Who are the competitors in the leaderboard — internal models only, or external entrants?",
      "Determines whether the leaderboard is a model-selection tool or a public contest with prize obligations.",
      "",
      "Not answered. Not verified.",
      "Decide in the Suggestions queue (S-17). Internal-only is the lower-risk default and needs no prize-terms legal review.",
      "R-08, S-17","P0"),

    Q("Q-21","Competition Design","What are the rewards, and who funds them?",
      "'Rewards for top performing strategies' is only meaningful once the reward and the funding source are named.",
      "",
      "Not answered. No reward structure has been funded. Not verified.",
      "Approve the reward ladder in the Suggestions queue before publishing the leaderboard (S-17).",
      "R-08, S-17","P0"),

    Q("Q-22","Competition Design","What stops an entrant from submitting many strategies and letting the tail of the distribution win?",
      "Multiple-comparisons bias is the most common way a 'skill' leaderboard actually ranks luck.",
      "A distribution-based test — plot the distribution of possible betting histories under the null and see where the actual record falls — is the standard remedy, alongside CLV and persistence testing.",
      "The specific correction policy for this leaderboard. Not verified.",
      "Implement a submission cap plus a multiplicity correction in the scoring rule (S-18).",
      "R-08, R-14, S-18","P0"),

    Q("Q-23","Model & Method","What is the null hypothesis each strategy is tested against?",
      "Without a stated null, 'passing a gate' is meaningless.",
      "A practitioner estimate: a bettor must beat the fair closing price about 70% of the time to have any positive expected value at all.",
      "The null and alternative for each gate in this project. Partially specified — see the Validation page.",
      "Formalise per-gate hypotheses on the Validation page and require sign-off.",
      "R-12, S-19","P1"),

    Q("Q-24","Model & Method","How will the model handle the vig / overround when comparing to market prices?",
      "Raw market prices embed a margin; comparing a fair model price to a raw price manufactures false edges.",
      "",
      "The de-vig convention for this project. Not verified.",
      "Specify one convention (proportional de-vig) and apply it universally; document it on the Line Origination page.",
      "R-06, S-20","P1"),

    Q("Q-25","Operations","Who owns the decision to promote a strategy from paper to live?",
      "Diffuse ownership is how unvalidated strategies reach real money.",
      "",
      "Not assigned. Not verified.",
      "Name an owner in COORDINATION.md and make promotion require an explicit approval record.",
      "R-12, S-21","P1"),

    Q("Q-26","Operations","What is the change-control process for the model itself?",
      "A model that is edited after the fact invalidates every prior result.",
      "",
      "No process defined. Not verified.",
      "Version every model, freeze parameters per season, and require a new validation run after any change (S-21).",
      "R-12, S-21","P1"),

    Q("Q-27","Operations","How long is the paper-trading probation before a strategy is eligible for rewards?",
      "Too short and luck is rewarded; too long and the competition stalls.",
      "",
      "Not decided. Not verified.",
      "Set in the Leaderboard spec with the minimum-sample answer to Q-16.",
      "R-08, S-14","P1"),

    Q("Q-28","Data & Licensing","Are we permitted to publish derived data on a public GitHub Pages site?",
      "This site is public. Licence terms may prohibit republication.",
      "",
      "Not verified. No licence in place.",
      "Read the licence before publishing any licensed data; this site currently publishes only data already public on nfl.com plus our own design artifacts.",
      "R-20, S-08","P0"),

    Q("Q-29","Model & Method","Do we treat the market as efficient (so we must find only tiny edges) or exploitable (so large edges exist)?",
      "Sets the prior, which sets how strong the evidence must be before we believe a backtest.",
      "The academic literature summarised in the line-movement paper finds these markets efficient, or inefficient only within transaction-cost bounds. A separate analysis found forecasts close to reliable with deviations concentrated in closing lines.",
      "The project's own prior. Not verified — it is a modelling stance, not a fact.",
      "Adopt the conservative prior (market is near-efficient) and require gates sized accordingly. Record the stance explicitly rather than leaving it implicit.",
      "R-14, S-19","P0"),

    Q("Q-30","Markets & Execution","What markets are actually available at the intended books — do they offer the props and combos our strategies assume?",
      "A strategy on an unavailable market is not a strategy.",
      "",
      "Not verified. No operator selected (Q-19).",
      "Inventory actual offered markets per operator before finalising the strategy catalog.",
      "R-09, R-10, R-11, S-16","P1"),

    Q("Q-31","Governance","What does 'useful signal' mean numerically for this project?",
      "'Generate useful signals' is the vaguest requirement in the brief and needs an operational definition before anything can be accepted or rejected.",
      "",
      "No numeric definition. Not verified.",
      "Define as: positive expected CLV after costs, sustained out-of-sample, with a confidence interval excluding zero. Then encode it as gate G2.",
      "R-07, S-19","P0"),

    Q("Q-32","Governance","Which of the 18 suggestions on the Suggestions page are approved for implementation?",
      "The brief requires that suggestions be reviewed and a path chosen BEFORE implementation. None has been implemented for exactly that reason.",
      "",
      "No approvals recorded. Not verified — this is the user's decision.",
      "Review the Suggestions page and set each row to Approved, Rejected or Deferred; only Approved rows may be implemented.",
      "R-03, S-01..S-18","P0"),
  ];

  /* Each question's Source column points to the primary source that underpins its
     "What we already know" cell. Where nothing external has been established yet, it
     points to this project's own design spec. */
  const SRC_BY_Q = {
    "Q-01": "MURPHY_2018",
    "Q-02": "NFL_GAMBLING_SUMMARY",
    "Q-04": "NFL_GAMBLING_SUMMARY",
    "Q-05": "KELLY_1956",
    "Q-06": "KELLY_1956",
    "Q-08": "CLV_SKILL_SPORTS_TRADING",
    "Q-09": "NFL_ROSTER_RULES",
    "Q-10": "CLV_SKILL_BET_SINCLAIR",
    "Q-12": "LUCK_SKILL_PANEL",
    "Q-14": "LINE_MOVEMENT_PAPER",
    "Q-16": "CLV_SKILL_BET_SINCLAIR",
    "Q-17": "NFL_DEPTH_CHART_404",
    "Q-18": "NFL_ROSTER_RULES",
    "Q-22": "LUCK_SKILL_PANEL",
    "Q-23": "CLV_SKILL_BET_SINCLAIR",
    "Q-29": "LINE_MOVEMENT_PAPER",
  };
  rows.forEach(r => { r.src = S(SRC_BY_Q[r.id] || "DESIGN_SPEC"); });

  window.X4_QUESTION_STATS = {
    total: rows.length,
    p0: rows.filter(r => r.pri === "P0").length,
    p1: rows.filter(r => r.pri === "P1").length,
    p2: rows.filter(r => r.pri === "P2").length,
    open: rows.filter(r => r.status === "open").length,
    answered: rows.filter(r => r.status === "answered").length,
  };

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.questions = {
    sortKey: "id", sortDir: "asc",
    placeholder: "Filter by question, area, blocker…",
    facets: [
      { key: "area", label: "Area", options: ["Legal & Jurisdiction","Capital & Risk","Data & Licensing","Model & Method","Markets & Execution","Competition Design","Operations","Governance"] },
      { key: "pri", label: "Priority", options: ["P0","P1","P2"] },
      { key: "status", label: "Status", options: ["open","answered"] },
    ],
    cols: [
      { key: "id", label: "ID", nowrap: true },
      { key: "area", label: "Area", nowrap: true },
      { key: "question", label: "Question that must be answered" },
      { key: "why", label: "Why it matters" },
      { key: "know", label: "What we already know (verified)" },
      { key: "missing", label: "What we do NOT have (unverified)" },
      { key: "how", label: "How to discover the missing information" },
      { key: "blocks", label: "Blocks", nowrap: true },
      { key: "pri", label: "Pri", nowrap: true },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source for what we know" },
    ],
    rows: rows,
  };
})();
