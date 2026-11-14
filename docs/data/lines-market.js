/* X4 — LINE ORIGINATION & MARKET STRUCTURE
   Requirement R-06: "I want to originate my own NFL lines."

   KEY FINDING, stated up front because it constrains everything:
   There is NO official league source for betting prices. The NFL publishes standings,
   schedules and injury reports, but sportsbooks' prices are commercial products. Any
   price we compare against must come from a licensed operator or a licensed market-data
   vendor, and that means this project's verification policy ("official source only")
   cannot be satisfied by an official source for odds. Recorded as F-02. */

(function () {
  const pipeline = [
    { step: "1", name: "Ingest official inputs",
      detail: "Standings, schedule, official injury report, roster rules. All of these ARE available from official sources and are already verified on this site.",
      have: "Yes — verified", src: S("NFL_STANDINGS"), status: "verified" },

    { step: "2", name: "Ingest performance data",
      detail: "Play-by-play, snap counts, participation. Required to estimate team strength and player usage.",
      have: "No — no licence in place", src: S("DESIGN_SPEC"), status: "unverified" },

    { step: "3", name: "Estimate team strength",
      detail: "Produce a rating (points better than average) per team, with an uncertainty, on a neutral field.",
      have: "No — blocked on step 2", src: S("DESIGN_SPEC"), status: "unverified" },

    { step: "4", name: "Add situational adjustments",
      detail: "Home field, rest, bye context, travel, and injury-driven personnel adjustments.",
      have: "Partial — schedule and injury data verified; adjustment coefficients not estimated",
      src: S("NFL_SCHED"), status: "unverified" },

    { step: "5", name: "Produce a fair price",
      detail: "Convert the spread and total distribution into fair (zero-margin) probabilities.",
      have: "Method specified; not computed", src: S("DESIGN_SPEC"), status: "design" },

    { step: "6", name: "De-vig the market price",
      detail: "Remove the book's margin from the published price so we compare like with like. Comparing a fair model price to a raw market price manufactures false edges.",
      have: "Method specified; convention not ratified (Q-24)", src: S("DESIGN_SPEC"), status: "design" },

    { step: "7", name: "Compare and size the disagreement",
      detail: "Edge exists only where the disagreement exceeds the model's own error AND the round-trip cost.",
      have: "Not computed — no price feed", src: S("DESIGN_SPEC"), status: "unverified" },

    { step: "8", name: "Strike and log",
      detail: "Record the price at the instant of the bet, plus the closing price. Without both, CLV is uncomputable and gate G2 cannot run.",
      have: "Schema specified; not built", src: S("DESIGN_SPEC"), status: "design" },

    { step: "9", name: "Score against the closing line",
      detail: "CLV per bet; test the mean against 1.00. This is the primary skill measurement.",
      have: "Not run", src: S("CLV_SKILL_SPORTS_TRADING"), status: "unverified" },
  ];

  const inputs = [
    { input: "Team ratings / strength", official: "Not published as such by the league.",
      note: "Must be derived. Derivation makes it a modelled value, not an official one.",
      src: S("DESIGN_SPEC"), status: "unverified" },

    { input: "Standings", official: "Yes — nfl.com/standings.",
      note: "Verified for 2026 and reproduced on the NFL Data page.",
      src: S("NFL_STANDINGS"), status: "verified" },

    { input: "Schedule and byes", official: "Yes — nfl.com/schedules.",
      note: "Verified for Week 10 2026, including the official 'Teams on Bye' list.",
      src: S("NFL_SCHED"), status: "verified" },

    { input: "Injury report", official: "Yes — nfl.com/injuries.",
      note: "Verified in full for Week 10 2026. Practice status and game status are official; severity and diagnosis are not disclosed.",
      src: S("NFL_INJURY"), status: "verified" },

    { input: "Roster and elevation rules", official: "Yes — operations.nfl.com.",
      note: "53-man active/inactive list; standard elevation addendum to 54/55; up to three elevations per practice-squad player per league year.",
      src: S("NFL_ROSTER_RULES"), status: "verified" },

    { input: "Depth chart (2nd/3rd/4th string)", official: "NO official league source. NFL.com returns 404 for depth-chart paths.",
      note: "Club sites publish ordered depth charts but do not label strings. Recorded as F-03.",
      src: S("NFL_DEPTH_CHART_404"), status: "unverified" },

    { input: "Betting prices / lines", official: "NO official league source exists.",
      note: "Prices are commercial products of licensed operators. Recorded as F-02.",
      src: S("DESIGN_SPEC"), status: "unverified" },

    { input: "Weather", official: "Not published by the league on the pages verified this session.",
      note: "Would need an official meteorological source. Not sourced yet.",
      src: S("DESIGN_SPEC"), status: "unverified" },

    { input: "Officials' assignments", official: "Not verified this session.",
      note: "Leave blank until confirmed from an official source.",
      src: S("DESIGN_SPEC"), status: "unverified" },
  ];

  const marketFacts = [
    { fact: "There is no official league source for betting prices.",
      detail: "Consequence: every odds-dependent number in this project is unverifiable against an official primary source. The honest options are to license a provider (and cite that provider's documentation) or to leave the field blank.",
      src: S("DESIGN_SPEC"), status: "verified" },

    { fact: "Player prop bets are inside the NFL's gambling prohibition for covered persons.",
      detail: "The prohibition covers 'any wager involving NFL outcomes', and published summaries of the policy explicitly list player prop bets.",
      src: S("NFL_GAMBLING"), status: "verified" },

    { fact: "Coaches, staff and personnel are barred from betting on any sport, not just the NFL.",
      detail: "This is an additional rule that applies only to coaches, staff and personnel, not to players.",
      src: S("NFL_GAMBLING_SUMMARY"), status: "verified" },

    { fact: "Betting markets are close to efficient, so genuine edges are small.",
      detail: "Academic work on real-time line movement finds market probability forecasts were close to reliable, with deviations concentrated in closing lines; the wider literature finds these markets efficient, or inefficient only within transaction-cost bounds.",
      src: S("LINE_MOVEMENT_PAPER"), status: "verified" },

    { fact: "Beating the closing line is a far more sensitive skill test than realised profit.",
      detail: "In the cited worked example of 1,214 bets, a 2.19% average edge was about 18.5 standard deviations from chance on CLV, whereas the same record's raw profit could not rule out luck. Practitioner guidance is that a bettor must beat the fair closing price roughly 70% of the time to have any positive expected value at all.",
      src: S("CLV_SKILL_SPORTS_TRADING"), status: "verified" },

    { fact: "The dispersion of opening-to-closing price ratios grows with the odds.",
      detail: "Reported standard deviation of the opening-to-closing price ratio was about 0.043 at odds of 1.25 and about 0.14 at odds of 5.0 — i.e. longshots move much more, so CLV thresholds must be odds-dependent.",
      src: S("CLV_SKILL_SPORTS_TRADING"), status: "verified" },

    { fact: "Late-season kickoff dates and times can change, so scheduling signals must be recomputed.",
      detail: "Under the NFL's 2026 flexible scheduling procedures, Sunday Night Football may be flexed up to twice in Weeks 5-10 and in any week in Weeks 11-17; Monday Night Football in any week in Weeks 12-17; Thursday Night Football up to twice in Weeks 13-17. Decisions are announced no later than 12 days in advance (SNF Weeks 5-13, MNF Weeks 12-17), 6 days in advance (SNF Weeks 14-17) and 21 days in advance (TNF Weeks 13-17). Consequence: any rest, travel or short-week signal must be recomputed when a game is flexed, and a signal built on a pre-flex schedule is not the same signal after the flex.",
      src: S("NFL_FLEX"), status: "verified" },

    { fact: "Participants systematically over-rate their own skill.",
      detail: "Peer-reviewed survey evidence: on an 11-point scale from 0 (luck) to 10 (skill), DFS participants averaged 6.10 and sports-betting participants 5.90. False perception of control is positively related to gambling problems.",
      src: S("UNLV_GRRJ"), status: "verified" },
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.pipeline = {
    sortKey: "step", sortDir: "asc",
    cols: [
      { key: "step", label: "#", nowrap: true },
      { key: "name", label: "Step" },
      { key: "detail", label: "What happens" },
      { key: "have", label: "Do we have it?" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: pipeline,
  };

  window.X4_TABLES.lineInputs = {
    sortKey: "input", sortDir: "asc",
    cols: [
      { key: "input", label: "Model input" },
      { key: "official", label: "Official source?" },
      { key: "note", label: "Note" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: inputs,
  };

  window.X4_TABLES.marketFacts = {
    sortKey: "fact", sortDir: "asc",
    cols: [
      { key: "fact", label: "Market fact" },
      { key: "detail", label: "Detail" },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Source" },
    ],
    rows: marketFacts,
  };
})();
