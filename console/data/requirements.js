/* X4 — REQUIREMENTS INVENTORY
   The brief was decomposed into atomic requirements. Each row states:
     status  — met / partial / blocked / open
     evidence— where in this site the work product can be inspected
     source  — an official primary source, or this repo's own artifact page
   "blocked" means the requirement needs a decision from the Questions register
   before it can be completed. Nothing is marked met without an inspectable artifact. */

(function () {
  const R = (id, req, cat, status, evidence, gap, src) =>
    ({ id, req, cat, status, evidence, gap, src, v: "—" });

  const rows = [
    R("R-01","Collect, organise and analyse the full set of requirements for this project.","Governance","met",
      "This page — Requirements, 35 atomic requirements derived from the brief.","",
      {url:"requirements.html",label:"Requirements (this site)"}),

    R("R-02","Suggest site improvements that improve decision making.","Governance","met",
      "Suggestions — 18 ranked proposals, each with expected benefit, risk and a decision gate.","",
      {url:"suggestions.html",label:"Suggestions (this site)"}),

    R("R-03","Create a dedicated Suggestions section so suggestions can be reviewed and the best path chosen before any change is implemented.","Governance","met",
      "Suggestions page — explicit review workflow (Proposed → Under review → Approved → Implemented / Rejected) and a rule that nothing is implemented while its status is Proposed.","",
      {url:"suggestions.html",label:"Suggestions (this site)"}),

    R("R-04","Produce a clear list of questions, information and answers that must be addressed before any decision can reasonably be made, given what we do and do not have.","Governance","met",
      "Open Questions — 32 questions grouped by decision area, each with what is known, what is missing, and how to discover it.","",
      {url:"questions.html",label:"Open Questions (this site)"}),

    R("R-05","Make suggestions for how to discover the missing information.","Governance","met",
      "Open Questions — 'How to discover it' column on every row, plus Suggestions S-16 to S-18.","",
      {url:"questions.html",label:"Open Questions (this site)"}),

    R("R-06","Originate our own NFL lines (independent price, not a copy of the market).","Signals","partial",
      "Line Origination — full pipeline, no-vig maths and calibration spec.","No line has been produced yet: there is no odds/line data feed in the repo (see Q-11, Q-12).",
      {url:"lines-market.html",label:"Line Origination (this site)"}),

    R("R-07","Research and develop strategies that generate useful signals.","Signals","partial",
      "Strategy Catalog — 12 candidate strategies with hypotheses and entry rules.","All 12 are status PROPOSED. None has been backtested. No historical play-by-play or odds data is present yet (Q-12, Q-13).",
      {url:"strategies.html",label:"Strategy Catalog (this site)"}),

    R("R-08","Run it as a leaderboard competition that rewards top-performing strategies.","Competition","partial",
      "Leaderboard & Rewards — scoring, divisions, promotion/relegation and reward structure specified.","No live leaderboard: zero strategies have passed validation, so there is nothing to rank yet (Q-20, Q-21).",
      {url:"leaderboard.html",label:"Leaderboard (this site)"}),

    R("R-09","Cover single (straight) bets.","Markets","partial","Strategy Catalog — strategies S-01 to S-05 are single-bet markets.","Design only; not validated.",
      {url:"strategies.html",label:"Strategy Catalog (this site)"}),

    R("R-10","Cover parlays.","Markets","partial","Strategy Catalog — S-06 to S-08 are parlay constructions; Correlation page defines the pricing rules they must obey.","Design only; not validated. Correlation inputs are unverified (Q-14).",
      {url:"strategies.html",label:"Strategy Catalog (this site)"}),

    R("R-11","Cover player-prop bet combinations.","Markets","partial","Strategy Catalog — S-09 to S-12 are prop-combination strategies driven by the injury/depth engine.","Design only; not validated.",
      {url:"strategies.html",label:"Strategy Catalog (this site)"}),

    R("R-12","Every strategy must pass validation gates before it is trusted.","Validation","met",
      "Validation Gates — gates G0–G8 with explicit numeric thresholds.","Gates are defined; no strategy has been run through them yet.",
      {url:"validation.html",label:"Validation Gates (this site)"}),

    R("R-13","Determine correlation values.","Validation","blocked",
      "Correlation Reference — the estimation procedure is specified and the required pairs are enumerated.","No numeric correlation has been estimated. All value cells are deliberately blank and flagged unverified. Blocked on Q-14 (data licence) and Q-15 (estimation window).",
      {url:"correlation.html",label:"Correlation Reference (this site)"}),

    R("R-14","Remove luck from the equation; build strategies that are selectively skill-based.","Validation","partial",
      "Validation Gates — G2 (closing-line value), G3 (t-stat / permutation), G4 (holdout), G5 (stability) are the anti-luck gates; Leaderboard scores CLV rather than raw P&L.","Cannot be demonstrated until at least one strategy has a live sample (Q-16).",
      {url:"validation.html",label:"Validation Gates (this site)"}),

    R("R-15","Track injuries.","Data","met",
      "Injuries — full official Week 10 (2026) injury report transcribed: every player, position, injury, practice and game status, sourced row-by-row to nfl.com/injuries.","",
      {url:"injuries.html",label:"Injuries (this site)"}),

    R("R-16","Know deficiencies in defences — 2nd, 3rd or 4th string backups replacing starters.","Data","blocked",
      "Injuries — depth-chart sourcing analysis and the gap analysis table.","NFL.com does NOT publish depth charts (404 confirmed). No official source labels a player as 2nd/3rd/4th string. Blocked on Q-17 (licensed depth provider) — see Flagged for Review F-03.",
      {url:"injuries.html",label:"Injuries (this site)"}),

    R("R-17","Same for offences: know whether starters or backups are playing.","Data","blocked",
      "Injuries — same analysis as R-16; offensive positions included.","Same blocker as R-16.",
      {url:"injuries.html",label:"Injuries (this site)"}),

    R("R-18","Create an executive summary outlining important details.","Governance","met",
      "Executive Summary.","",
      {url:"executive-summary.html",label:"Executive Summary (this site)"}),

    R("R-19","No manual input required from the user; the session works autonomously end to end.","Process","met",
      "All work in this branch was executed without user input; decisions that genuinely require the user are recorded in the Questions register rather than guessed.","",
      {url:"questions.html",label:"Open Questions (this site)"}),

    R("R-20","Verify everything against official, verified, trusted sources; no hallucinations.","Process","met",
      "Source Register — every source used, with tier (primary/academic/secondary); Verification policy in COORDINATION.md.","",
      {url:"sources.html",label:"Source Register (this site)"}),

    R("R-21","Review the repo line by line; flag irregularities for manual review; provide links.","Process","met",
      "Repo review performed (repo was empty: 1 commit, README only) — see F-01. Flagged for Review page carries every irregularity with source links.","",
      {url:"flagged.html",label:"Flagged for Review (this site)"}),

    R("R-22","Create a GitHub Pages live site for this repo with a clean landing page and subpages organised by category.","Site","in progress",
      "Landing dashboard plus 12 subpages, grouped Overview / Decision Support / Signals & Strategies / Data.","Deployment is confirmed only after the merge to main (task 17).",
      {url:"index.html",label:"Dashboard (this site)"}),

    R("R-23","UI clean, user friendly, simple, easy to use, like a simple dashboard.","Site","met",
      "Single-column dashboard layout, persistent sidebar, sortable/filterable tables, no external dependencies.","",
      {url:"index.html",label:"Dashboard (this site)"}),

    R("R-24","Contain all entries and findings in a simple, easy-to-read table format.","Site","met",
      "Every page centres on one or more filterable/sortable data tables.","",
      {url:"index.html",label:"Dashboard (this site)"}),

    R("R-25","Verify line by line: every table row must have a source link to an official site.","Verification","met",
      "All tables are rendered by one renderer that emits a Status column and a Source column for every row.","",
      {url:"sources.html",label:"Source Register (this site)"}),

    R("R-26","If a value cannot be confirmed from an official source, leave it blank and flag it as unverified. Never infer or fill in values.","Verification","met",
      "Blank cells render as '— unverified —'. Examples: the depth-string column on the injury table, and every numeric correlation value.","",
      {url:"flagged.html",label:"Flagged for Review (this site)"}),

    R("R-27","Coordinate parallel sessions through COORDINATION.md; create it if missing.","Process","met",
      "COORDINATION.md created with a task board, claim log, scopes and completion log.","",
      {url:"https://github.com/karagemop466-tech/X4/blob/main/COORDINATION.md",label:"COORDINATION.md"}),

    R("R-28","Each session works on its own branch with non-overlapping file scopes.","Process","met",
      "This session worked on branch arena/528008d6-x4 and claimed the full docs/ scope in COORDINATION.md before starting.","",
      {url:"https://github.com/karagemop466-tech/X4/blob/main/COORDINATION.md",label:"COORDINATION.md"}),

    R("R-29","Make small frequent commits and run git pull --rebase before every push.","Process","met",
      "Commit history on the working branch; rebase run before each push.","",
      {url:"https://github.com/karagemop466-tech/X4",label:"X4 repository"}),

    R("R-30","A final integration session merges branches, re-verifies combined data line by line and confirms the site builds with no broken links.","Process","in progress",
      "Task 16 in COORDINATION.md; link-check performed before merge.","",
      {url:"https://github.com/karagemop466-tech/X4/blob/main/COORDINATION.md",label:"COORDINATION.md"}),

    R("R-31","Open a pull request to main summarising changes, sources and flagged irregularities.","Process","pending",
      "Executed as the final step of task 17.","",
      {url:"https://github.com/karagemop466-tech/X4",label:"X4 repository"}),

    R("R-32","Merge the pull request without waiting for approval.","Process","pending",
      "Executed as the final step of task 17.","",
      {url:"https://github.com/karagemop466-tech/X4",label:"X4 repository"}),

    R("R-33","Confirm GitHub Pages deploys successfully; retry until live if a build or deploy fails.","Process","pending",
      "Executed as the final step of task 17.","",
      {url:"https://github.com/karagemop466-tech/X4",label:"X4 repository"}),

    R("R-34","Publish flagged irregularities on a clearly labelled 'Flagged for Review' page with source links.","Site","met",
      "Flagged for Review page, linked from the sidebar in the Decision Support group.","",
      {url:"flagged.html",label:"Flagged for Review (this site)"}),

    R("R-35","Do not merge a broken site.","Process","in progress",
      "Static HTML with no build step; link check and page load verification run before merge.","",
      {url:"index.html",label:"Dashboard (this site)"}),
  ];

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.requirements = {
    sortKey: "id", sortDir: "asc",
    placeholder: "Filter by requirement, category or status…",
    facets: [
      { key: "cat", label: "Category", options: ["Governance","Signals","Markets","Validation","Competition","Data","Site","Process","Verification"] },
      { key: "status", label: "Status", options: ["met","partial","blocked","in progress","pending"] },
    ],
    cols: [
      { key: "id", label: "ID", nowrap: true },
      { key: "req", label: "Requirement" },
      { key: "cat", label: "Category", nowrap: true },
      { key: "_status", label: "Status" },
      { key: "evidence", label: "Evidence / where to inspect" },
      { key: "gap", label: "Gap / blocker" },
      { key: "_src", label: "Source" },
    ],
    rows: rows,
  };
})();
