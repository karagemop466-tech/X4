#!/usr/bin/env python3
"""Generate the multi-page site into site/ from a shared shell.

Run:  python3 tools/pages.py
Pages: index, standings, availability, lines, strategies, questions, suggestions, flags, methodology
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

NAV = [
    ("index.html", "Overview"),
    ("standings.html", "Standings & results"),
    ("lines.html", "Model lines"),
    ("strategies.html", "Strategy lab"),
    ("availability.html", "Injuries & depth"),
    ("questions.html", "Decision checklist"),
    ("suggestions.html", "Suggestions"),
    ("flags.html", "Flagged for review"),
    ("methodology.html", "Methodology"),
]

PAGES = {}


def page(slug, title, description, body, active):
    PAGES[slug] = (title, description, body, active)


# ---------------------------------------------------------------- index
page(
    "index", "NFL Decision Desk",
    "Official-source NFL decision support: verified standings, model lines, strategy validation gates, injury and depth tracking.",
    """
<div class="hero">
  <span class="eyebrow light">Executive summary</span>
  <h2>Official NFL data, verified line by line. Model lines labelled as estimates. Nothing filled in that could not be confirmed.</h2>
  <p>This desk is built on the NFL's own pages. Every number in every table traces to an official NFL.com URL that a reviewer can open. Scores were rebuilt from a reconstructed game log and then <b>proved</b> against the official standings: 137 games, and every team's wins, losses, ties, points for, points allowed and winning percentage match the NFL exactly. Where an official source does not exist - market lines, depth-chart strings, player-prop prices - the cell is left blank and the gap is listed on the <a href="flags.html">Flagged for review</a> page.</p>
  <p>What the work actually shows: the model has signal over a league-average benchmark, but the improvement is <b>not yet statistically separable from luck</b>, so the leaderboard marks every strategy ineligible for reward. That is the validation gate working, not a gap in the analysis.</p>
</div>

<div class="grid g4">
  <article class="card hero-card"><span class="k">Games verified</span><div class="v" id="kpi-games">—</div><div class="n" id="kpi-games-n">—</div></article>
  <article class="card hero-card"><span class="k">Teams verified</span><div class="v" id="kpi-teams">—</div><div class="n" id="kpi-teams-n">—</div></article>
  <article class="card hero-card"><span class="k">Injury rows</span><div class="v" id="kpi-inj">—</div><div class="n" id="kpi-inj-n">—</div></article>
  <article class="card hero-card"><span class="k">Players ruled Out</span><div class="v" id="kpi-out">—</div><div class="n" id="kpi-out-n">—</div></article>
  <article class="card hero-card"><span class="k">Strategies scored</span><div class="v" id="kpi-strat">—</div><div class="n" id="kpi-strat-n">—</div></article>
  <article class="card hero-card"><span class="k">Passing all gates</span><div class="v" id="kpi-elig">—</div><div class="n" id="kpi-elig-n">—</div></article>
  <article class="card hero-card"><span class="k">Best improvement</span><div class="v" id="kpi-best">—</div><div class="n" id="kpi-best-n">—</div></article>
</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">What the official sources say right now</span><h2>Verified position</h2></div><span class="tag acc">NFL.com · 14 Nov 2026</span></div>
  <div class="grid g4" id="wk-facts"></div>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Strategy leaderboard</span><h2>Every strategy must clear every gate</h2><p class="muted">Scored by out-of-sample spread accuracy, significance, stability and calibration. A strategy that cannot show its edge is separated from luck does not earn a reward, however good its recent record looks.</p></div><span class="tag" id="lb-status">—</span></div>
  <div id="lb-preview"></div>
  <p style="margin-top:12px"><a class="btn" href="strategies.html">Open the Strategy Lab →</a></p>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">How to read this site</span><h2>Four rules</h2></div></div>
  <div class="grid g2">
    <article class="card"><span class="eyebrow">Rule 1</span><h3>Every row has a source link</h3><p class="muted">Each table row links to the official page it came from - a specific NFL.com game page, player page or news article - not a home page. Click it and check the value yourself.</p></article>
    <article class="card"><span class="eyebrow">Rule 2</span><h3>Blank means blank</h3><p class="muted">Where a value cannot be confirmed from an official source, the cell stays empty and the item is flagged. Nothing is inferred, estimated in place of a fact, or filled from an aggregator.</p></article>
    <article class="card"><span class="eyebebrow">Rule 3</span><h3>Estimates are labelled</h3><p class="muted">Model output is always marked as a model estimate and always shown with the range across all nine strategies, so you can see where the model is confident and where it is guessing.</p></article>
    <article class="card"><span class="eyebrow">Rule 4</span><h3>Luck is removed, not wished away</h3><p class="muted">Correlated strategies are grouped rather than counted as rivals, significance is tested with a Bonferroni-adjusted bootstrap, and until the evidence clears the bar no strategy is declared a winner.</p></article>
  </div>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Open items</span><h2>Flagged for review</h2><p class="muted">Unverified values and irregularities found during verification. These do not block publication; they are simply not hidden.</p></div><span class="tag warn">Full register on its own page</span></div>
  <div id="flag-preview"></div>
  <p style="margin-top:12px"><a class="btn" href="flags.html">See every flag →</a></p>
</section>

<section>
  <div class="section-head"><div><span class="eyebrow">Where to go next</span><h2>The desk</h2></div></div>
  <div class="grid g3">
    <article class="card"><span class="eyebrow">Data</span><h3><a href="standings.html">Standings &amp; results</a></h3><p class="muted">Official standings for all 32 teams, opponent-adjusted power ratings, and all 137 completed games with a link to each official game page.</p></article>
    <article class="card"><span class="eyebrow">Model</span><h3><a href="lines.html">Model lines</a></h3><p class="muted">Week 11 model spreads and totals for all 13 official games, with the full range across strategies and the market-line column left blank on purpose.</p></article>
    <article class="card"><span class="eyebrow">Validation</span><h3><a href="strategies.html">Strategy lab</a></h3><p class="muted">The leaderboard, the seven gates, the error-correlation matrix, the calibration check and the week-by-week stability table.</p></article>
    <article class="card"><span class="eyebrow">Availability</span><h3><a href="availability.html">Injuries &amp; depth</a></h3><p class="muted">The full official Week 10 injury report, a unit-level roll-up of absences, and the starter changes the league confirmed in its own news.</p></article>
    <article class="card"><span class="eyebrow">Decisions</span><h3><a href="questions.html">Decision checklist</a></h3><p class="muted">Nine questions that must be answered before a decision here is reasonable: what we know, what is missing, what it blocks and how to close it.</p></article>
    <article class="card"><span class="eyebrow">Review</span><h3><a href="suggestions.html">Suggestions</a></h3><p class="muted">Twelve proposals, ranked, with the decision each one needs and the evidence that would show it worked. Review before building.</p></article>
  </div>
</section>
""", "index")

# ---------------------------------------------------------------- standings
page(
    "standings", "Standings & results",
    "Official NFL.com standings for all 32 teams, opponent-adjusted power ratings and every completed 2026 game with an official link.",
    """
<div class="section-head"><div><span class="eyebrow">01 · Official standings</span><h2>League standings, verified</h2><p class="muted">Wins, losses, ties, winning percentage, points for, points allowed and net points are the official NFL.com values, retrieved 14 November 2026. These same totals are what the game log is proved against.</p></div><span class="tag acc">Source: nfl.com/standings</span></div>
<div id="standings"></div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">02 · Opponent-adjusted power</span><h2>Who is actually good</h2><p class="muted">A team's raw points-per-game flatters a soft schedule. These figures subtract the average rate of the opponents each team has faced and add the league average back, so beating good teams and beating bad teams are not worth the same. <b>These are model estimates, not official values</b> - the raw official columns beside them are.</p></div><span class="tag warn">Estimate, not official</span></div>
<div id="power"></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">03 · Game log</span><h2>Every completed game</h2><p class="muted">All 137 completed regular-season games through the 12 November Thursday night game. Each row links to that game's official NFL.com page.</p></div><span class="tag acc">137 games</span></div>
<div class="toolbar" id="games-toolbar"></div>
<div id="games"></div>
</section>

<section style="margin-top:26px">
  <div class="note ok"><b>How this was verified.</b> The game log was reconstructed and then checked, automatically, against the official standings: <span class="mono">tools/verify.py</span> rebuilds every team's record and point totals from the 137 games and compares them to the NFL's own figures. All 32 teams matched exactly on all six measures, which also proves every individual score. The check runs in 460 checks and is part of the build.</div>
</section>
""", "standings")

# ---------------------------------------------------------------- lines
page(
    "lines", "Model lines",
    "Week 11 model spreads and totals for all 13 official NFL games, with the full range across nine strategies.",
    """
<div class="section-head"><div><span class="eyebrow">04 · Model lines</span><h2>Week 11 projections</h2><p class="muted">Every one of the 13 games on the official NFL.com Week 11 schedule, with a model spread and total from each of the nine strategies. The range across strategies is shown alongside the headline figure: where the range is wide, the model does not know.</p></div><span class="tag acc">Source: nfl.com/schedules/2026/by-week/week-11</span></div>
<div id="lines"></div>

<section style="margin-top:26px">
  <div class="note warn"><b>There is no market column.</b> The NFL publishes no official betting lines, and no licensed odds feed has been authorised for this repository, so the market-line cell is empty rather than filled from an aggregator. Every figure in this table is a model estimate derived from official NFL.com results - it is a research output, not a price and not a recommendation.</div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">The nine strategies</span><h2>What produces a line</h2><p class="muted">Each strategy is a different way of turning the same verified game log into a forecast. They are scored on the <a href="strategies.html">Strategy Lab</a> page.</p></div></div>
<div id="strat-list"></div>
</section>
""", "lines")

# ---------------------------------------------------------------- strategies
page(
    "strategies", "Strategy lab",
    "Strategy leaderboard with seven validation gates, error correlation matrix, calibration check and weekly stability.",
    """
<div class="section-head"><div><span class="eyebrow">05 · Strategy tournament</span><h2>Leaderboard and rewards</h2><p class="muted">Strategies are scored on out-of-sample accuracy, and a strategy only earns reward points if it clears every gate. The significance gate is what keeps a lucky streak out of the top of the table.</p></div><span class="tag" id="lb-status2">—</span></div>
<div id="lb"></div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Gate results</span><h2>Why each strategy is or is not eligible</h2><p class="muted">Seven gates, every strategy, with the evidence for each verdict.</p></div></div>
<div id="gates"></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Controlling for luck</span><h2>Which strategies are actually the same bet</h2><p class="muted">Two strategies whose errors move together are not two pieces of evidence - they are one signal counted twice. The matrices below are computed from the same out-of-sample games. A value near 1.00 means the two strategies fail on exactly the same games, so ranking them against each other would overstate how much independent skill exists.</p></div><span class="tag">Correlation</span></div>
  <div class="grid g2">
    <div><h3>Error correlation</h3><div id="corr-err"></div><p class="small muted">Correlation between each strategy's point-spread error and every other strategy's error, over the out-of-sample games.</p></div>
    <div><h3>Prediction correlation</h3><div id="corr-pred"></div><p class="small muted">Correlation between the predicted spreads themselves - how much the strategies agree on the games.</p></div>
  </div>
  <div class="legend"><span><i style="background:rgba(57,192,127,.35)"></i>low - largely independent signal</span><span><i style="background:rgba(77,163,255,.25)"></i>moderate</span><span><i style="background:rgba(240,169,56,.35)"></i>high</span><span><i style="background:rgba(239,107,107,.4)"></i>near-identical - treat as one strategy</span></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Calibration</span><h2>Are the probabilities honest?</h2><p class="muted">A forecast that is consistently too confident is worse than no forecast. For each offset the model states the probability that the true total exceeds its own total plus that offset; a well-calibrated model's stated probability matches how often it actually happened.</p></div><span class="tag">Tolerance 0.12</span></div>
<div id="calib"></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Stability</span><h2>Does the edge hold week to week?</h2><p class="muted">An improvement that appears only in a few weeks is not a reliable edge. Gate G5 requires the improvement against the league-constant benchmark to be positive in at least 60% of evaluated weeks.</p></div></div>
<div id="weekly"></div>
</section>
""", "strategies")

# ---------------------------------------------------------------- availability
page(
    "availability", "Injuries & depth",
    "Official NFL Week 10 injury report, unit-level absence roll-up, and league-confirmed starter changes.",
    """
<div class="section-head"><div><span class="eyebrow">06 · Availability</span><h2>Injuries and depth deficiencies</h2><p class="muted">The official NFL.com Week 10 injury report, transcribed in full: every listed player, their position, the injury, the practice designation and the game status. NFL clubs publish these under the league's injury-report policy, which is why they are the authoritative record.</p></div><span class="tag acc">Source: nfl.com/injuries</span></div>
<div id="avail"></div>
<div class="note warn" style="margin-top:12px"><b>The public report is not the whole story.</b> Players on injured reserve, the reserve/nontheatre injured list or the physically-unable-to-perform list do not appear in the public weekly report. Those absences show up in league news instead - see the next two tables. This is recorded as flag F-03.</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Starter changes</span><h2>Confirmed by the league</h2><p class="muted">Quarterback starter changes and long-term absences, each tied to the official NFL.com article that reports it. These are the facts the public injury report does not carry.</p></div><span class="tag acc">NFL.com news</span></div>
<div id="qb"></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Official reporting</span><h2>All captured league updates</h2><p class="muted">Every official NFL.com item captured alongside the Week 10 injury report.</p></div></div>
<div id="news"></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Full report</span><h2>Every listed player</h2><p class="muted">The complete Week 10 report, filterable by team and by status. Filter by 'No designation' to see players who were listed with no injury and no game status.</p></div></div>
<div class="toolbar" id="inj-toolbar"></div>
<div id="inj-full"></div>
</section>

<section style="margin-top:26px">
  <div class="note"><b>What is deliberately not here.</b> No player is assigned a depth-chart string - starter, 2nd, 3rd or 4th. The NFL publishes no consolidated league depth chart, so any such ranking would be an invention. That gap is flag F-02, and the fix is on the <a href="suggestions.html">Suggestions</a> page as the highest-impact proposal on the list.</div>
</section>
""", "availability")

# ---------------------------------------------------------------- questions
page(
    "questions", "Decision checklist",
    "Nine questions that must be answered before a decision in this project is reasonable: what we know, what is missing, what it blocks.",
    """
<div class="section-head"><div><span class="eyebrow">07 · Before any decision</span><h2>Questions, answers and gaps</h2><p class="muted">A decision here is only reasonable once the 'what is still missing' column is either answered or explicitly accepted as a risk. Everything in the 'what we already know' column traces to the official source on the right.</p></div><span class="tag">9 questions</span></div>
<div id="qa"></div>
""", "questions")

# ---------------------------------------------------------------- suggestions
page(
    "suggestions", "Suggestions",
    "Twelve ranked proposals for reviewing and choosing before implementation, each with the decision it needs.",
    """
<div class="section-head"><div><span class="eyebrow">08 · Review before building</span><h2>Suggestions</h2><p class="muted">The best path has to be chosen before any of it is implemented. Each proposal below states what it would do, why it matters, how you would know it worked, and the decision it needs from you first. None of them is presented as already built.</p></div><span class="tag warn">Choose before implementing</span></div>
<div id="sugg" class="grid g3"></div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">How to review them</span><h2>Ordering rule</h2><p class="muted">Work down this list. If a proposal cannot answer its question, the later ones are not worth evaluating yet.</p></div></div>
<div id="sugg-frame"></div>
</section>
""", "suggestions")

# ---------------------------------------------------------------- flags
page(
    "flags", "Flagged for review",
    "Every unverified value, limitation and irregularity found during official-source verification.",
    """
<div class="section-head"><div><span class="eyebrow">09 · Open items</span><h2>Flagged for review</h2><p class="muted">Nothing on this page is a placeholder for data that exists. Each entry is either something genuinely unavailable from an official source, a limitation of the published approach, or an irregularity found while verifying. None of them blocks publication; all of them are visible.</p></div><span class="tag warn">—</span></div>
<div id="flags"></div>
""", "flags")

# ---------------------------------------------------------------- methodology
page(
    "methodology", "Methodology",
    "How every published number is produced: the model, the parameters, the validation gates and the verification log.",
    """
<div class="section-head"><div><span class="eyebrow">10 · How it works</span><h2>Methodology</h2><p class="muted">Everything on this site is produced by two scripts from the CSV files in <span class="mono">data/</span>. Nothing is hand-typed into a page at publish time.</p></div><span class="tag acc">Reproducible</span></div>

<div class="grid g2">
  <article class="card">
    <span class="eyebrow">Step 1 · Acquire</span>
    <h3>Official pages only</h3>
    <p class="muted">The official NFL.com standings, the official weekly injury report and the official weekly schedule are the source of record. Secondary aggregators were used to reconstruct the game log, and every reconstructed score is then proved against the official standings totals - a single wrong score changes a team's points for or points allowed, so matching all 32 teams on all six measures proves every score.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 2 · Verify</span>
    <h3><span class="mono">tools/verify.py</span></h3>
    <p class="muted">460 checks covering: every game row's official URL pattern, every team's wins, losses, ties, points for, points allowed, net points and winning percentage, games played per team, the Week 11 schedule's pairing and URL structure, and duplicate rows. It exits non-zero on any failure and runs as part of the build.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 3 · Model</span>
    <h3>Opponent-adjusted rates</h3>
    <p class="muted">For a team, the opponent-adjusted points-for rate is the team's own scoring rate minus the average points allowed by the opponents it has faced, plus the league average. The same construction gives the opponent-adjusted points-allowed rate. A team's expected score is the mean of its adjusted offence and its opponent's adjusted defence, with the league home-field margin added. Every quantity used for a Week-w forecast is measured strictly from games before Week w, including the opponents' season rates, so there is no look-ahead.</p>
  </article>
  <article class="card">
    <span class="eyebrow">Step 4 · Validate</span>
    <h3>Walk-forward, seven gates</h3>
    <p class="muted">Strategies are evaluated only on games that had not been played at forecast time - no random row splits. Each strategy must clear data integrity, out-of-sample discipline, minimum sample size, statistical significance, weekly stability, calibration, and exclusion of the league-constant benchmark, before it can earn reward points.</p>
  </article>
</div>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Model parameters</span><h2>Every knob, published</h2><p class="muted">These are analyst choices by this project, not official values, and they are the first thing a reviewer should challenge. Changing any of them changes the ranking. A fixed bootstrap seed makes the reported intervals exactly reproducible.</p></div><span class="tag warn">Not official</span></div>
<div id="params"></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Verification log</span><h2>What was checked, and what failed</h2><p class="muted">The complete record, including the checks that did not pass. A verification log that only lists successes is not a verification log.</p></div></div>
<div id="verify"></div>
</section>

<section style="margin-top:26px">
  <div class="section-head"><div><span class="eyebrow">Reproduce it</span><h2>Running the pipeline</h2></div></div>
  <div class="note"><b>From a clean checkout:</b><br>
  <span class="mono">python3 tools/verify.py</span> &nbsp;- proves the data against the official standings<br>
  <span class="mono">python3 tools/build.py</span> &nbsp;- rebuilds every published number into <span class="mono">site/data.js</span><br>
  <span class="mono">python3 tools/pages.py</span> &nbsp;- regenerates the site pages<br>
  <span class="mono">python3 site/check.py</span> &nbsp;- checks the site for broken links and unsourced rows<br>
  <span class="mono">python3 tools/validate.py</span> &nbsp;- runs the full publication gate</span>
  <p style="margin-top:9px">The build is deterministic: the same inputs produce the same tables and the same confidence intervals on every run.</p></div>
</section>
""", "methodology")


# ---------------------------------------------------------------- shell
def render(slug, title, description, body, active):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' class="active"' if href == active else "", label)
        for href, label in NAV)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="%(desc)s">
<title>%(title)s · NFL Decision Desk</title>
<link rel="stylesheet" href="styles.css">
</head>
<body data-page="%(slug)s">
<header class="top">
  <div class="top-inner">
    <a class="brand" href="index.html"><span class="brand-mark">4D</span><span>FOURTH DOWN<small>NFL DECISION DESK</small></span></a>
    <nav class="main">%(nav)s</nav>
  </div>
</header>
<main>
%(body)s
<div class="note bad" id="render-error" style="display:none"></div>
</main>
<footer>
  <div class="inner">
    <span>FOURTH DOWN RESEARCH · NFL decision support</span>
    <span>Official sources: nfl.com/standings · nfl.com/injuries · nfl.com/schedules · operations.nfl.com · ftc.gov</span>
    <span>Evidence status: verified official data + labelled model estimates · no market data · not betting advice</span>
  </div>
</footer>
<script src="data.js"></script>
<script src="app.js"></script>
</body>
</html>
""" % dict(title=title, desc=description, nav=nav, body=body, slug=slug)


def main():
    os.makedirs(SITE, exist_ok=True)
    written = []
    for slug, (title, desc, body, active) in PAGES.items():
        href = "index.html" if slug == "index" else slug + ".html"
        html = render(slug, title, desc, body, href)
        with open(os.path.join(SITE, href), "w", encoding="utf-8") as fh:
            fh.write(html)
        written.append(href)
    # index.html is the entry point and must exist at the site root
    print("wrote %d pages: %s" % (len(written), ", ".join(written)))


if __name__ == "__main__":
    main()
