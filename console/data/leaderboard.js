/* X4 — LEADERBOARD COMPETITION DESIGN & REWARDS
   Requirement R-08: treat it as a leaderboard competition that provides rewards for top
   performing strategies.

   Design principle: the leaderboard scores EVIDENCE, not profit. A strategy that earns
   money without beating the closing line is not ranked above one that does. That is the
   difference between a leaderboard and a lottery.

   STATUS: no strategy has entered. Zero rows in the standings table. */

(function () {
  const divisions = [
    { div: "Probation", entry: "Any newly registered strategy.",
      promote: "Reaches the minimum sample N (Q-16) with gates G0, G1 and G7 satisfied.",
      demote: "Fails G0 (data integrity) at any time.",
      stake: "Paper only. No stake.",
      src: S("DESIGN_SPEC"), status: "design" },

    { div: "Challenger", entry: "Promoted from Probation; or demoted from Validated.",
      promote: "Passes G2 (CLV), G3 (significance) and G4 (out-of-sample) on a full season.",
      demote: "Fails G4 (out-of-sample) or G5 (stability).",
      stake: "Paper, or smallest real unit if MODE = LIVE and approved per S-07.",
      src: S("DESIGN_SPEC"), status: "design" },

    { div: "Validated", entry: "Promoted from Challenger.",
      promote: "Passes G5 (stability) and G6 (correlation pricing, where applicable) across two consecutive seasons.",
      demote: "Any gate failure, or realised capacity falling below the modelled capacity (G7).",
      stake: "Standard unit.",
      src: S("DESIGN_SPEC"), status: "design" },

    { div: "Retired", entry: "Any strategy demoted twice, or withdrawn by its owner.",
      promote: "None. Retirement is terminal for the season.",
      demote: "n/a",
      stake: "No stake.",
      src: S("DESIGN_SPEC"), status: "design" },
  ];

  const scoring = [
    { metric: "Mean closing-line value (CLV)", weight: "Primary (60%)",
      why: "The most sensitive available test of skill. A bettor who beats the fair closing price systematically is moving the market, and that cannot be explained by luck.",
      note: "Requires the de-vig convention to be fixed first (Q-24).",
      src: S("CLV_SKILL_SPORTS_TRADING"), status: "design" },

    { metric: "Out-of-sample consistency", weight: "15%",
      why: "Rewards strategies whose holdout result matches their in-sample result — i.e. strategies that were not overfitted.",
      note: "Computed from the G4 holdout.",
      src: S("DESIGN_SPEC"), status: "design" },

    { metric: "Net-of-cost, net-of-tax ROI", weight: "15%",
      why: "Profit is real, even though it is the slowest statistic to separate from luck. It is included with a modest weight, not excluded.",
      note: "Requires Q-03 (tax) to be answered before it can be computed honestly.",
      src: S("DESIGN_SPEC"), status: "design" },

    { metric: "Stability (dispersion across seasons)", weight: "10%",
      why: "Persistence distinguishes a repeatable edge from one good season.",
      note: "Uses the G5 output.",
      src: S("LUCK_SKILL_PANEL"), status: "design" },

    { metric: "Realised capacity", weight: "Tie-break / cap",
      why: "If two strategies score alike, the one that can actually be executed at size wins. Capacity is also a hard cap, not a bonus.",
      note: "From G7.",
      src: S("DESIGN_SPEC"), status: "design" },

    { metric: "Raw profit", weight: "0% — deliberately excluded",
      why: "Including raw profit at any meaningful weight lets variance win the leaderboard. Even after 1,000 bets there was roughly a 1-in-10 chance that luck alone produced a 2% profit where the expectation was a 2% loss.",
      note: "Profit still appears on the page as reported context, but it is not scored.",
      src: S("CLV_SKILL_BET_SINCLAIR"), status: "design" },
  ];

  const rewards = [
    { tier: "1st", reward: "Not defined.",
      cond: "Top-ranked Validated strategy by weighted score at season end.",
      fund: "Not defined.",
      blocker: "Q-21 — the reward and its funding source have not been approved.",
      src: S("DESIGN_SPEC"), status: "unverified" },

    { tier: "2nd", reward: "Not defined.", cond: "Second-ranked Validated strategy.",
      fund: "Not defined.", blocker: "Q-21.", src: S("DESIGN_SPEC"), status: "unverified" },

    { tier: "3rd", reward: "Not defined.", cond: "Third-ranked Validated strategy.",
      fund: "Not defined.", blocker: "Q-21.", src: S("DESIGN_SPEC"), status: "unverified" },

    { tier: "Best new entrant", reward: "Not defined.",
      cond: "Highest-scoring strategy promoted out of Probation during the season.",
      fund: "Not defined.",
      blocker: "Q-21. Also depends on whether entrants are internal models only or external (Q-20).",
      src: S("DESIGN_SPEC"), status: "unverified" },

    { tier: "Integrity award", reward: "Not defined.",
      cond: "Best-documented negative result — a strategy that was killed by a gate, with a clear write-up of why.",
      fund: "Not defined.",
      blocker: "Q-21. Included deliberately: rewarding a well-documented kill discourages the temptation to keep a failing strategy alive until it looks good.",
      src: S("DESIGN_SPEC"), status: "unverified" },
  ];

  const standings = [
    // Intentionally empty. Populated only when a strategy passes G1.
    // Placeholder row documents why the table is empty rather than hiding it.
    {
      rank: "", strategy: "", division: "", n: "", clv: "", roi: "", status: "unverified",
      note: "No entries. No strategy has passed the minimum-sample gate (G1). The leaderboard will populate only when at least one strategy has a scored sample — see Q-16.",
      src: S("DESIGN_SPEC"),
    },
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.lbDivisions = {
    sortKey: "div", sortDir: "asc",
    cols: [
      { key: "div", label: "Division", nowrap: true },
      { key: "entry", label: "Entry condition" },
      { key: "promote", label: "Promotion rule" },
      { key: "demote", label: "Demotion rule" },
      { key: "stake", label: "Staking" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: divisions,
  };

  window.X4_TABLES.lbScoring = {
    sortKey: "metric", sortDir: "asc",
    cols: [
      { key: "metric", label: "Metric" },
      { key: "weight", label: "Weight", nowrap: true },
      { key: "why", label: "Why it is weighted this way" },
      { key: "note", label: "Dependency" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: scoring,
  };

  window.X4_TABLES.lbRewards = {
    sortKey: "tier", sortDir: "asc",
    cols: [
      { key: "tier", label: "Tier" },
      { key: "reward", label: "Reward" },
      { key: "cond", label: "Condition" },
      { key: "fund", label: "Funding source" },
      { key: "blocker", label: "Blocker" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: rewards,
  };

  window.X4_TABLES.lbStandings = {
    search: false,
    cols: [
      { key: "rank", label: "Rank" },
      { key: "strategy", label: "Strategy" },
      { key: "division", label: "Division" },
      { key: "n", label: "n" },
      { key: "clv", label: "Mean CLV" },
      { key: "roi", label: "Net ROI" },
      { key: "note", label: "Note" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: standings,
  };
})();
