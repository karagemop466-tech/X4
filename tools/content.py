# -*- coding: utf-8 -*-
"""
Narrative content published on the site.

Every "known" statement carries an official source URL. Every "missing" statement is
something that is genuinely absent from the official free sources captured so far.
Nothing here is a placeholder for data that exists.
"""

# ------------------------------------------------------------------ information requirements
QUESTIONS = [
    dict(q="What decision are we actually trying to make?",
         know="The repository now holds a verified game log of all 150 completed 2026 games through the end of Week 10, the official NFL.com standings for all 32 teams, the official Week 10 injury report and the official Week 11 schedule with kickoff times, networks and bye teams.",
         missing="The market definition (point spread, total, player prop, or a proprietary rating), the decision horizon (single game, week, or season) and whether the output is informational analytics, a paper-trading competition, or a wagering product.",
         blocks="Reward design, data budget, legal scope, and which of the strategies on the Strategy Lab page is even relevant.",
         close="Write a one-page charter naming the market, the horizon, the decision owner and what 'success' means, then re-score every suggestion against it.",
         url="https://www.nfl.com/schedules/2026/by-week/week-11"),

    dict(q="Where do betting lines come from, and do we price our own lines or trade them?",
         know="The NFL publishes no official betting lines. Every spread and total on this site is a model estimate derived from official NFL.com results, computed by tools/build.py. NFL Game Operations publishes the rules of the game itself.",
         missing="A licensed, timestamped odds feed; which sportsbook and market format; the vig-removal convention; whether prices are compared against a market or the model sets its own price.",
         blocks="Every expected-value, ROI, bankroll, Kelly and parlay-pricing calculation. Those cells are blank on this site and will stay blank until a feed is authorised.",
         close="Either obtain a licensed odds feed with a documented history, or formally decide the project is market-independent and scores predictions only.",
         url="https://www.nfl.com/"),

    dict(q="How will 'a 2nd- or 3rd-string player replaces a starter' be measured?",
         know="The official NFL.com injury report gives practice participation and game status for every listed player on all 28 teams that played in Week 10. NFL.com news confirms specific starter changes (Seattle, Cleveland, Arizona, Miami) and long-term absences (Baltimore, the LA Rams, Green Bay).",
         missing="An official league-wide depth chart, snap counts, and a point-in-time record of who actually started each game. NFL clubs publish their own depth charts, but the league publishes no consolidated version.",
         blocks="Quantifying what an absence is worth in points, ranking unit depth, and any player-prop model built on role.",
         close="Ingest the official NFL.com game books (box scores) to build snaps and starters, and archive club depth charts with retrieval timestamps.",
         url="https://www.nfl.com/injuries/"),

    dict(q="Which long-term absences are missing from the public injury report?",
         know="The public Week 10 injury page does not list players on injured reserve, reserve/nontheatre injured list or physically unable to perform. Baltimore's starting quarterback, for example, appears only in league news, not in the report table.",
         missing="A complete, machine-readable IR/PUP/NIR list per team, per week.",
         blocks="Multi-week absence tracking and any team-strength adjustment built from availability.",
         close="Pull each club's own weekly official injury report (clubs publish them and the league links them) and archive them weekly.",
         url="https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season"),

    dict(q="How many games are enough to call a strategy skilful rather than lucky?",
         know="118 out-of-sample games are available (Weeks 3-10 complete). The best strategy improves point-spread MAE over the league-constant benchmark by 9.5%, but its Bonferroni-adjusted bootstrap interval still contains zero, so no strategy passes the significance gate.",
         missing="More seasons of official history, and a pre-registered minimum sample size for the reward contest.",
         blocks="Awarding rewards, declaring a winner, or claiming an edge.",
         close="Pre-register the sample size and the metric now, then keep scoring prospective predictions so the evidence accrues on a published timeline.",
         url="https://www.nfl.com/schedules/2026/by-week/week-10"),

    dict(q="Is a 6-2 team actually good, or just fortunate?",
         know="Official points for and against are verified for every team. A Pythagorean-style check, an opponent-adjusted margin and a home/road split are all computable from those official totals.",
         missing="Drive-level data: snaps, possessions, explosives plays, red-zone rate, turnovers and play-call mix. None of these is exposed by the free official pages in a single fetch.",
         blocks="Separating a genuinely strong roster from one with a soft schedule and a few lucky wins.",
         close="Ingest the official game books (NFL.com box scores) to build drive and possession features on the same point-in-time discipline used here.",
         url="https://www.nfl.com/stats/"),

    dict(q="What counts as a bet, and how is it settled?",
         know="NFL Football Operations publishes the official rulebook that governs the games themselves. The published Week 11 schedule also carries the league's flexible-scheduling and future-week rules.",
         missing="Sportsbook-specific settlement: pushes and voids on postponed games, stat corrections on player props, and treatment of a cancelled game in a season.",
         blocks="Backtest correctness and any realised-profit figure.",
         close="Record the rulebook version and the market's settlement rules alongside every backtest, and keep a copy of both.",
         url="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"),

    dict(q="Who may take part, and in which jurisdictions?",
         know="This is a public research repository published with GitHub Pages. It publishes no picks, accepts no bets and pays no prizes.",
         missing="Jurisdiction, age gating, and the prize structure if rewards ever become monetary or wagering-related.",
         blocks="Any real-money reward mechanism or public competition.",
         close="Obtain jurisdiction-specific legal review before attaching value to a leaderboard position.",
         url="https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act"),

    dict(q="How will the data stay fresh and point-in-time?",
         know="Every official page used here is re-fetchable on a schedule, and the pipeline is scripted and reproducible: tools/verify.py proves the data, tools/build.py regenerates every published number.",
         missing="An automated fetcher with change detection and a dated snapshot archive, plus a nightly capture of the official injury report.",
         blocks="Prospective evaluation, which is the only way the significance gate can eventually be passed.",
         close="Add a scheduled job that stores a dated copy of the standings, the weekly injury report and the weekly schedule, then rebuild the site from the archive.",
         url="https://www.nfl.com/injuries/"),

    dict(q="Which metric decides the leaderboard?",
         know="The leaderboard currently scores seven gates: data integrity, out-of-sample discipline, minimum sample, statistical significance, weekly stability, calibration, and exclusion of the benchmark. Points are provisional until all seven pass.",
         missing="The reward scale, tie-breaks, disqualification rules, and the treatment of strategies that are statistically indistinguishable from each other.",
         blocks="A fair competition and any published reward.",
         close="Ratify the scoring formula and the correlation rule before the first prospective round.",
         url="https://www.nfl.com/schedules/2026/by-week/week-11"),
]

# ------------------------------------------------------------------ suggestions
SUGGESTIONS = [
    dict(priority="P0", priority_class="p0", area="Data", title="Archive a dated snapshot of every official page",
         body="Store the standings page, the weekly injury report and the weekly schedule on every fetch, with retrieval time, content hash and the source URL. Rebuild the site from the archive rather than from a live page.",
         why="Right now every table is a snapshot of a single moment. Without an archive we cannot prove what was known at decision time, and the significance gate can never be passed retrospectively.",
         verify="Re-running the build from an archived date reproduces byte-identical tables for that date.",
         effort="Low", impact="High",
         decision="Agree the retention window and the fetch schedule."),

    dict(priority="P0", priority_class="p0", area="Data", title="Repeat the depth capture every week and archive it, then add the official game books for snaps",
         body="The depth half of this suggestion is now delivered for one week: tools/depth.py transcribes all 31 clubs that publish an ordered chart (1,558 positions) and joins them to the official injury report, on the Depth &amp; deficiency page. The remaining work is (a) run that same capture every week and keep every snapshot with its retrieval date, and (b) ingest the official game books so that snap counts and the players who actually took the first snap are recorded.",
         why="A single-week snapshot is the right shape for originating next week's line and the wrong shape for backtesting: a Week-w forecast may only see what was known before Week w, so an availability term cannot enter the walk-forward model until the capture has been running for a stretch of weeks and been archived. The game books close the second half - a published chart is not proof of who started (F-21) - and they are what turns an absence into a measured point value.",
         verify="An availability term can be added to a Week-w forecast using only snapshots dated before Week w, and a starter can be confirmed from the game book rather than from the pre-game chart.",
         effort="Medium", impact="Very high",
         decision="Confirm the game-book format is acceptable to parse and redistribute, and commit to the weekly capture schedule plus the retention window."),

    dict(priority="P0", priority_class="p0", area="Market", title="Decide the market strategy before building any pricing",
         body="Either authorise a licensed odds feed, or state formally that the project prices its own lines and never compares them to a market. The current code deliberately contains no odds path.",
         why="Betting value, bankroll sizing, parlay pricing and player-prop economics are all undefined without prices. Leaving the decision open silently produces numbers that look like conclusions but are not.",
         verify="Either a signed feed agreement, or a published scope statement that removes every value claim from the site.",
         effort="Low", impact="Very high",
         decision="Market-independent research, or licensed market comparison."),

    dict(priority="P1", priority_class="p1", area="Strategy", title="Group the leaderboard by distinct signal family",
         body="Use the published error-correlation matrix to collapse near-duplicate strategies into families before ranking, and label each entry with its family instead of treating every model as an independent competitor.",
         why="The correlation matrix shows several strategies with an error correlation of 1.00 - they are the same signal expressed twice. A leaderboard that treats them as rivals overstates how much independent skill exists.",
         verify="Every family leader is separated from every other family leader by a correlation below the agreed threshold.",
         effort="Low", impact="High",
         decision="The correlation value at which two strategies count as the same signal."),

    dict(priority="P1", priority_class="p1", area="Presentation", title="Publish a band, not a number, for every model line",
         body="Show the full strategy range and the implied probability distribution next to each line, and label every model figure as an estimate derived from official results.",
         why="A single spread reads as a fact. The range across the nine strategies is the honest representation of what the current data supports, and it shows the reviewer exactly where the model is confident and where it is guessing.",
         verify="No page shows a bare model number without its range and its derivation note.",
         effort="Low", impact="Medium",
         decision="Whether the band should be the strategy range or a bootstrap percentile interval."),

    dict(priority="P1", priority_class="p1", area="Strategy", title="Run a shadow leaderboard of locked, pre-game predictions",
         body="Publish every model line before kickoff with a timestamp, then score it afterwards. No real money, no changes after the fact.",
         why="Backtesting on nine weeks of one season is the weakest evidence available. Prospective, timestamped predictions are what turns 'no strategy passes the significance gate' into an actual decision, and they are the only fair basis for a reward contest.",
         verify="After 50 locked games the paired bootstrap interval can be recomputed on prospective data alone.",
         effort="Medium", impact="Very high",
         decision="Who locks the predictions, and how is the lock enforced so a line cannot be revised after seeing the market."),

    dict(priority="P1", priority_class="p1", area="Strategy", title="Add model-disagreement and absence-impact watchlists",
         body="Flag games where the strategies disagree by more than a set threshold, and attach the availability summary for both teams, so extra research effort is aimed at the games that are actually uncertain.",
         why="Most games are not close calls. The value of more information is concentrated in a small number of games, and the current site shows the lines but not where uncertainty lives.",
         verify="A weekly shortlist of flagged games, each with the official injury link and the disagreement range.",
         effort="Medium", impact="Medium",
         decision="The disagreement threshold that makes a game worth extra research."),

    dict(priority="P1", priority_class="p1", area="Parlays", title="Price combinations from a joint model, never from marginals",
         body="For any parlay or prop combination, estimate the joint distribution and compare it to the offered payout and to the same legs taken singly. A correlation of 1.00 between two legs means the combination is one bet priced twice.",
         why="The correlation matrix already shows that several model legs are near-perfectly collinear. Multiplying marginals in that situation overstates the probability of the parlay winning and is the most common way a strategy loses money for reasons that have nothing to do with skill.",
         verify="Every published combination carries a joint estimate, an explicit dependence assumption and a comparison against the singles.",
         effort="High", impact="High",
         decision="Which combination types are eligible for the contest at all."),

    dict(priority="P2", priority_class="p2", area="Quality", title="Make data integrity a failing build, not a report",
         body="Wire tools/verify.py into continuous integration so that any edit which breaks agreement with the official standings totals fails the build before it can be published.",
         why="The verification in this session caught a genuine transcription error and a swapped score. That check should never be optional.",
         verify="A deliberately corrupted row makes the pipeline fail with a named team and the expected versus official totals.",
         effort="Low", impact="High",
         decision="Whether the committed standings snapshot is refreshed automatically or manually reviewed."),

    dict(priority="P2", priority_class="p2", area="Presentation", title="Add a per-team availability timeline",
         body="Show a week-by-week timeline of each team's absence count and unit hit, so a three-week absence is visible at a glance instead of only in the current week's report.",
         why="A single report snapshot hides exactly the pattern that matters most for a season-long model: a slowly degrading roster.",
         verify="A timeline view for every team, sourced to the weekly official report.",
         effort="Medium", impact="Medium",
         decision="How many weeks of history to retain and how absences that resolve are displayed."),

    dict(priority="P2", priority_class="p2", area="Presentation", title="Give every page its own visible flag list",
         body="Show the flags that apply to the page you are reading, next to the content, rather than only on the review page.",
         why="A reader who lands on the injury page should not have to visit another page to learn that the public report omits players on injured reserve.",
         verify="Each page carries an inline panel listing the flags that constrain it.",
         effort="Low", impact="Medium",
         decision="Whether the inline panel is collapsed by default for casual readers."),

    dict(priority="P3", priority_class="p3", area="Quality", title="Re-run the strategy search each week and publish the changelog",
         body="Recompute the leaderboard weekly from the archive and publish what changed, including strategies that fell out of contention.",
         why="Early-season rankings are unstable - the current spread between strategies is smaller than its own confidence interval. Publishing the movement is more honest than publishing a static ranking that looks settled.",
         verify="A dated weekly changelog showing the movement of each strategy's improvement and interval.",
         effort="Medium", impact="Medium",
         decision="Whether the leaderboard is frozen for a season or updated continuously."),

    dict(priority="P0", priority_class="p0", area="Validation", title="S-15 - Decide whether the significance gate measures mean error or paired win rate",
         body="The same 118 out-of-sample games give two different answers. On the bootstrap of the mean absolute-error improvement, the 95% Bonferroni-adjusted interval is [-0.00, +1.94] points: its upper bound has moved clear of zero after Week 10 completed, but its lower bound still touches it, so every strategy still fails G4. On a paired sign test, S1's spread lands closer to the truth than the league-constant benchmark in 78 of 118 games (66.1%), exact one-sided binomial p = 0.00030, and S8 (last-5-games) in 75 of 118 (63.6%), p = 0.00206. BOTH clear the Bonferroni threshold of 0.00556 (0.05 / 9 strategies, corrected in T48 from 0.05 / 8) &mdash; two strategies, not one, which is a materially different question from the one this entry was opened to decide. Both statistics are computed from the same predictions and both are correct. Every number here is regenerated by tools/sign_test.py and gated by the publication check; none is typed.",
         why="The gate currently asks 'is the average improvement distinguishable from zero'. The blowouts dominate that average, and no team-rate model can price a blowout. The sign test asks 'how often is this model better head-to-head', which is the question a staker and a reviewer both actually care about. Choosing one over the other changes whether the leaderboard can ever promote anything - and choosing it now, after seeing that one answer passes, is exactly what a pre-registered gate is supposed to prevent unless the choice is made in the open and recorded before the next evaluation window.",
         verify="Both statistics are published together on gates.html; the gate definition is committed before the next evaluation window; after 50 prospective locked games the two agree or the divergence is explained.",
         effort="Low", impact="Very high",
         decision="Define G4 on the mean error difference (current), on the paired win rate (proposed), or on both with a stated primary."),

    dict(priority="P0", priority_class="p0", area="Data", title="S-16 - Capture the closing line at kickoff, automatically, or lose CLV permanently",
         body="Take a dated snapshot of every market at or after each kickoff, store it under the same snapshot key as the opening and current rows, and recompute closing-line value from it. The store built this session already has the closing slot registered for all 13 games; it is empty only because no game has kicked off yet.",
         why="Closing-line value is the only economic measure a staking strategy cannot fake with a lucky run, and it is the only gate input that does not depend on the result at all. A closing line that was not captured at kickoff cannot be reconstructed afterwards from an official source, because there is no official source - so every missed kickoff is a permanently lost observation, not a delay.",
         verify="Every final game has a closing row with a value and a retrieval timestamp at or after kickoff, and CLV recomputes for that game.",
         effort="Medium", impact="Very high",
         decision="Who or what captures the snapshot, and at what clock offset from kickoff."),

    dict(priority="P1", priority_class="p1", area="Presentation", title="S-17 - Make the signal/staking split load-bearing, or label it decorative",
         body="Either introduce a staking rule that is not a monotone function of the hit rate (variable stake sizing, or staking only a selected subset of games), or state on the leaderboard that the two columns are expected to agree under the current flat-stake policy and are published as a cross-check rather than as independent evidence.",
         why="Under a flat 1-unit stake at -110, bankroll growth is a pure function of the hit rate, so the staking rank cannot diverge from the signal rank in any informative way. A split that is presented as independent protection while being mathematically collinear with the score it is meant to check gives a false sense of two-factor validation. Publishing the condition under which the split becomes informative is more honest and costs nothing.",
         verify="The leaderboard states the condition under which the ranks can diverge, and either the staking policy produces divergence or the collinearity is stated on the page.",
         effort="Low", impact="Medium",
         decision="Whether variable staking is in scope, and if so under what published rule."),
]

SUGGESTION_FRAMEWORK = [
    dict(step="1", question="Name the decision in one sentence.", rule="If the decision cannot be written in a sentence, no data or model is worth building yet.", url="https://www.nfl.com/schedules/2026/by-week/week-11"),
    dict(step="2", question="What is the smallest data set that could change that decision?", rule="Prefer the narrowest official source that can overturn the current answer.", url="https://www.nfl.com/standings/"),
    dict(step="3", question="Is the source official, machine-readable and re-fetchable?", rule="Official beats secondary. Re-fetchable beats one-off. A source that cannot be re-read cannot be audited.", url="https://www.nfl.com/injuries/"),
    dict(step="4", question="How much would we trust the result if it were reversed?", rule="If a reversal would not change the decision, it is not worth the effort.", url="https://www.nfl.com/schedules/2026/"),
    dict(step="5", question="What metric and threshold decide success, before we measure?", rule="Pre-register the metric and the threshold; choosing them after seeing the result is how luck gets mistaken for skill.", url="https://www.nfl.com/schedules/2026/by-week/week-10"),
    dict(step="6", question="What would make this fail?", rule="Every proposal needs a named failure condition and a stop rule.", url="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"),
    dict(step="7", question="Who reviews the result, and is it published either way?", rule="Failures are published with the same prominence as successes, or the evidence is worthless.", url="https://www.ftc.gov/legal-library/browse/statutes/unlawful-internet-gambling-enforcement-act"),
]

# ------------------------------------------------------------------ flagged register
FLAGS = [
    dict(id="F-69", item="The Game Center injury widget says a club is injury-free while the official report lists that club's injuries",
         type="Irregularity", kind="bad", status="open",
         detail=("On 2026-11-18 the official Game Center for Cardinals at Chiefs (Week 11) rendered the panel "
                 "\"Cardinals have no active injuries at this time\" and \"Chiefs have no active injuries at this "
                 "time\". The official Week 10 report at nfl.com/injuries/league/2026/reg10 lists ARI with 15 rows "
                 "and 3 Out designations, and KC with 13 rows and 3 Out designations, three days earlier. The panel "
                 "is therefore not a substitute for the report, and the two official league surfaces disagree for "
                 "the same clubs. Note the likely explanation, published as a hypothesis and not as a finding: the "
                 "widget appears to read the week that has not been played yet (Week 11 has no published report, "
                 "F-61) rather than the week just completed, so it renders an empty set as 'no active injuries'."),
         why=("This is the failure mode the brief names most often - an absence of data presented as a clean bill of "
              "health. Any model or page that read this panel would understate a club's missing players for exactly "
              "the clubs that are most injured, and it would do so silently, with an official URL beside it. The "
              "site's policy already forbids treating 'not listed' as 'available' (see the reserve-list flag), and "
              "this is the same rule applied to a second official surface."),
         official_url="https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11",
         url="https://www.nfl.com/injuries/league/2026/reg10"),

    dict(id="F-70", item="Two Week 11 venue cells carry the venue's short name, and the dataset is a faithful transcription of the page that prints it",
         type="Unverified data", kind="info", status="limitation",
         detail=("data/venues-wk11-2026.csv carries stadium=RELIANT STADIUM for IND at HOU and stadium=ARROWHEAD "
                 "STADIUM for ARI at KC, with venue_source = 'NFL.com game centre, Game Info block' on both rows. "
                 "Both game centres were re-read on 2026-11-18 and both still print those exact strings: the Colts at "
                 "Texans Game Info block reads StadiumSTADIUMRELIANT STADIUM, and the Cardinals at Chiefs block reads "
                 "StadiumSTADIUMARROWHEAD STADIUM."),
         why=("F-60 framed this as a mismatch between the dataset and the official page. Re-reading both pages shows "
              "the dataset is a faithful transcription of its stated source and the mismatch claim was wrong: the "
              "short names are what the official page prints. The cell is still not the venue's present corporate "
              "name, but correcting it would introduce a value no cited source supports, which the publication "
              "policy forbids. The row stays as transcribed, and the difference is recorded here with both links so "
              "the reader can see both surfaces. F-60 remains the pointer; this entry is the verification result."),
         official_url="https://www.nfl.com/games/colts-at-texans-2026-reg-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/venues-wk11-2026.csv"),

    dict(id="F-68", item="The multiplicity correction divided by 8 while performing 9 tests",
         type="Irregularity", kind="warn", status="resolved",
         detail=("tools/build.py computed the Bonferroni threshold as alpha / (n_tests - 1), i.e. 0.05 / 8 = "
                 "0.00625, on the assumption that the benchmark S0 was excluded. It is not: the bootstrap loop "
                 "runs over every key in STRATEGIES, S0 included, so nine intervals are computed and nine "
                 "comparisons are made against one threshold. The gate's own published definition is "
                 "\"Bonferroni-adjusted p < 0.05 across all trials\", and the review page's S-15 text already "
                 "described the denominator as 0.05 / 8 strategies for nine strategies - that is, the site "
                 "published a rule it did not apply. Corrected in T48 to alpha / n_tests = 0.00556."),
         why=("A multiplicity correction that is one test too lenient is exactly the failure the correction "
              "exists to prevent: it makes each of the nine results look more significant than the family of "
              "nine tests permits. The correction was material: at 0.00625 two strategies (S1 at p = 0.00630 "
              "was not one of them, but the threshold decided S2 and S5's status at the margin) sat closer to "
              "the line than they do at 0.00556. After the correction S1 (p = 0.00030) and S8 (p = 0.00206) "
              "still clear, so no published conclusion flips - but the rule now matches its own definition, "
              "and that is the point."),
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4/blob/main/tools/build.py"),

    dict(id="F-66", item="Stale numbers survive in generated prose because prose is not on the gate",
         type="Irregularity", kind="warn", status="open",
         detail=("A line-by-line read on 2026-11-18 found numeric claims that described a corpus that no "
                 "longer exists, in places the publication gate does not read: tools/workbench.json "
                 "(\"results_2026.csv: 137 games\" and \"1,224\" settled bets) rendered onto workbench.html; "
                 "tools/build_integrity.py's docstring (\"verified results feed (137 games)\"); "
                 "research/decision-register.md and research/integrity-gates.md (\"137 games\", one of which "
                 "also said \"Weeks 1-10\" while holding 137 of the 150 games in that range); and "
                 "research/price-store.md (\"68 of 105 games (64.8%), exact binomial p = 0.0016\", a sign-test "
                 "result on a superseded corpus, now 78 of 118 at p = 0.00030). Every one of these was "
                 "correct when written and became wrong when the Week 10 finals were ingested. The pattern, "
                 "not any single number, is the finding: a count typed into prose or into a checker is a "
                 "future false statement, and F-59 was the same defect one level up."),
         why=("The site's central claim is that every published number is reproducible from the committed data. "
              "A stale number in a JSON evidence string or a research note defeats that claim just as surely as "
              "a stale number in a table, and it is harder to notice because no checker reads prose. The "
              "workbench example is the worst of them: it told a reviewer the results feed covers 137 games "
              "while the feed on the same site held 150."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/games-2026.csv"),

    dict(id="F-67", item="Two of the eight walk-forward strategies clear the Bonferroni sign test, and the primary metric is undecided",
         type="Method", kind="warn", status="open",
         detail=("tools/sign_test.py, added 2026-11-18, recomputes the paired sign test on the current corpus "
                 "(n = 118 evaluated games) instead of quoting a superseded 105-game figure. At n = 118 the result "
                 "has changed shape, not just size: S1 beats the league-constant benchmark in 78 of 118 games "
                 "(66.1%, exact one-sided p = 0.00030) and S8 in 75 of 118 (63.6%, p = 0.00206). Against the "
                 "Bonferroni threshold of 0.05 / 9 = 0.00556 (corrected in T48: the gate had divided by 8 while performing 9 tests), BOTH clear, where the previously published figure "
                 "named only S1. Meanwhile the mean-error bootstrap gate G4 still fails for every strategy, "
                 "with its lower bound touching zero. The two statistics are computed from the same predictions "
                 "and both are correct."),
         why=("This is question S-15 on the review page, and it is now materially larger than when it was "
              "opened: it is no longer 'one strategy passes one test', it is 'two strategies pass one test "
              "while all nine fail the other'. Choosing the primary metric now, after seeing which one passes "
              "and by how much, is the exact failure pre-registration exists to prevent. The honest action is "
              "to publish both, promote nothing, and require the owner to fix the primary metric in writing "
              "before the next evaluation window opens - which is what the site does."),
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/output/sign_test.json"),

    dict(id="F-01", item="Official market betting lines", type="Unverified data", kind="warn", status="limitation",
         detail=("Reconciled. Real prices now exist, but they are NOT official and they are NOT in this register's scope: "
                 "the NFL publishes no betting lines, so no price on this site is official. One licensed book's prices "
                 "(DraftKings, published by ESPN) were captured for 29 games - open and close, spread, total and "
                 "moneyline - and are on the Market & price archive page. Every one of those rows carries two "
                 "links: the NFL.com game page that proves the result, and the ESPN odds resource the price was "
                 "archived from. A second, independently taken capture of the same prices (14 games) fills the market "
                 "columns on the model-lines and price-snapshot pages; the two captures agree on all 112 comparable "
                 "numbers, which tools/reconcile_prices.py re-derives and the publication gate enforces. "
                 "What remains unverified is any price for a player prop or a prop combination: no "
                 "official or licensed source was confirmed for those, so those cells are still blank (F-35)."),
         why=("The capture is a transcription of one book's published numbers at a timestamped moment, not an "
              "official league figure and not a market consensus. It is sufficient to compute a backtest, a ROI and a "
              "closing-line value against a real price; it is not sufficient to claim a price is the best available, "
              "that a line is official, or that an arbitrage exists between books. Those claims are not made."),
         official_url="https://www.nfl.com/",
         url="https://www.nfl.com/"),

    dict(id="F-02", item="Depth-chart string: starter, 2nd, 3rd, 4th", type="Unverified data", kind="ok", status="resolved",
         detail="This was open in the first build: no player on the site was assigned a depth position, because nfl.com/teams/<club>/depth-chart returns HTTP 404 for every club. It is now closed from an official source. Each club's own official website publishes its depth chart as an ordered table, and the column order is the depth position - first name in a row = starter, second = backup, third = third string. 31 of the 32 clubs publish a machine-readable ordered chart, and all 1,558 depth rows are on the Depth & deficiency page with a link to the club page each one came from.",
         why="The league publishes no consolidated chart, but the clubs are the authority on their own depth and they publish it themselves. Recording the ordering the club itself prints is a transcription, not an inference: no rank is assigned where the club does not print one, co-starters are kept as co-starters, and a club that publishes its chart only as an image (Houston) is left blank and flagged as F-18 instead of being guessed at.",
         official_url="https://www.nfl.com/teams/",
         url="https://www.buffalobills.com/team/depth-chart"),

    dict(id="F-03", item="Players on injured reserve, PUP and NFI", type="Limitation", kind="warn", status="limitation",
         detail="The public Week 10 injury page omits players on IR/PUP/NIR. Baltimore's starting quarterback, for example, appears only in league news.",
         why="Any availability model built from the public page alone will silently miss long-term absences, which are exactly the absences that move a line.",
         official_url="https://www.nfl.com/injuries/",
         url="https://www.nfl.com/injuries/"),

    dict(id="F-04", item="Two official sources give different absence windows for the same player", type="Irregularity", kind="warn", status="irregularity",
         detail="One NFL.com item says the Ravens' Lamar Jackson is out 6-9 weeks; another says the Ravens confirm he is expected to miss 6-10 weeks.",
         why="Both are official league sources and they disagree. Neither is corrected on this site; the conflict is recorded so the discrepancy can be resolved by the club or the league before either figure is used.",
         official_url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"),

    dict(id="F-05", item="Player-level game logs, snaps, drives and EPA", type="Unverified data", kind="no", status="unverified",
         detail="No player-level season statistics are published here.",
         why="The official free pages fetched for this build did not expose a complete player-level dataset in a verifiable form. Player-prop strategies therefore remain framework only, with no measured performance.",
         official_url="https://www.nfl.com/stats/",
         url="https://www.nfl.com/stats/"),

    dict(id="F-06", item="Player-prop and parlay strategy performance", type="Unverified data", kind="no", status="unverified",
         detail="No player-prop strategy, no parlay price and no combined-bet performance figure is published.",
         why="Pricing a combination requires a joint distribution over player outcomes, which depends on F-02 and F-05. Publishing a number now would be a guess presented as a measurement.",
         official_url="https://www.nfl.com/injuries/",
         url="https://www.nfl.com/injuries/"),

    dict(id="F-07", item="No strategy has passed all seven validation gates", type="Result", kind="warn", status="limitation",
         detail="Across 118 out-of-sample games the best strategy's improvement over the league-constant benchmark has a Bonferroni-adjusted bootstrap interval whose lower bound still reaches zero (-0.0001 points), so it does not clear the gate.",
         why="This is the gate doing its job. A leaderboard that ranked strategies by point estimate alone would have declared a winner that the evidence does not support.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         url="https://www.nfl.com/schedules/2026/by-week/week-10"),

    dict(id="F-08", item="Model parameters have no official source", type="Limitation", kind="warn", status="limitation",
         detail="The decay factors, shrinkage weights, bootstrap settings and gate thresholds are analyst choices made by this project.",
         why="They are the first thing a reviewer should challenge, and changing any of them changes the ranking. They are published in full on the Methodology page so they can be argued with.",
         official_url="https://www.nfl.com/standings/",
         url="https://www.nfl.com/standings/"),

    dict(id="F-09", item="NFL.com deep links of the form /schedules/2026/REG<n>/ silently redirect to the current week", type="Irregularity", kind="warn", status="irregularity",
         detail="The URL pattern that appears to address an individual week resolves to whichever week is live.",
         why="Any automation built on that pattern would silently re-read the current week instead of the requested one. The working per-week pattern is /schedules/2026/by-week/week-<n>, which was confirmed directly for weeks 5 and 11.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-5",
         url="https://www.nfl.com/schedules/2026/by-week/week-5"),

    dict(id="F-10", item="Weeks 12 to 18 of the 2026 schedule are not published here", type="Limitation", kind="warn", status="limitation",
         detail="Only the completed Weeks 1-10 games and the official Week 11 schedule are published.",
         why="NFL itself lists several late-season matchups as to-be-determined, and the league's own notice explains that those dates, times and networks are only fixed later in the season.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://www.nfl.com/schedules/2026/by-week/week-11"),

    dict(id="F-11", item="Injury-report policy link carried over from an earlier session was not re-verified", type="Irregularity", kind="warn", status="irregularity",
         detail="The Competition Committee injury-report policy link recorded by an earlier session was not re-fetched during this build.",
         why="It is left in the repository as recorded by the session that verified it, and is not re-certified here. Nothing published on this site depends on it.",
         official_url="https://www.nfl.com/injuries/",
         url="https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693"),

    dict(id="F-12", item="Repository hygiene at the start of this build", type="Irregularity", kind="warn", status="resolved",
         detail="Before this work the repository contained exactly one tracked file - a four-byte README - with no licence, no contributing guide, no continuous integration, no tests, no data and no site.",
         why="Recorded for the audit trail. This build adds the verified datasets, the verification harness, the model engine and continuous integration that checks the site and the data before publication.",
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4"),

    dict(id="F-13", item="The published site exists in two copies that could drift apart", type="Irregularity", kind="warn", status="resolved",
         detail="GitHub Pages is configured to serve the repository root, while the publish workflow uploads the site/ directory as its artifact. If the two copies differ, a reader sees different numbers depending on which build served the page.",
         why="The root is now a byte-identical mirror of site/ and of the X4 Console in docs/, the publish workflow checks the mirror before it uploads, and the check step was re-run locally against the committed tree with exit code 0. The first version of that check failed on a clean checkout because it compared the build tools check.py and check.js as if they were site assets; both are now excluded.",
         official_url="https://www.nfl.com/",
         url="https://github.com/karagemop466-tech/X4/blob/main/.github/workflows/pages.yml"),

    dict(id="F-14", item="The same two clubs are labelled differently in the two layers", type="Irregularity", kind="warn", status="resolved",
         detail="NFL.com's own standings page labels the Los Angeles Rams LA and the Arizona Cardinals AZ. The main dataset keys them LAR and ARI - the abbreviations NFL.com itself uses in its game-page URLs - while the decision-desk layer keys them LA and AZ.",
         why="No value is wrong, but a reviewer comparing the two layers would otherwise read the same club as two teams. The mapping is written out explicitly in the desk generator rather than inferred, and the two independent transcriptions were compared club by club: all 32 agree on wins, losses, ties, points for, points allowed and net points.",
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4/blob/main/tools/gen_data_html.py"),

    dict(id="F-15", item="The X4 Console's no-JavaScript fallback counts were stale", type="Irregularity", kind="warn", status="resolved",
         detail="The console landing page printed 26 facts and 15 flagged items in the text that renders when JavaScript is unavailable, while the data files those counters are generated from hold 27 executive-summary facts and 16 flagged items.",
         why="A reader without JavaScript would have been told the register was one item shorter than it is. The fallback text now matches the data; both numbers were counted from the data files rather than read off the page.",
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4/blob/main/docs/data/exec-summary.js"),

    dict(id="F-16", item="Two different flagged registers reuse the same identifiers", type="Irregularity", kind="warn", status="resolved",
         detail="This site and the decision-desk layer each publish a flagged register, and both number their entries F-01, F-02, F-03 ... for different items. F-02 on the main site is the depth-chart gap; F-02 on the desk layer is the missing calibration metrics.",
         why="The two registers were built by parallel sessions working from the same brief, and neither knew the other's numbering. They have been left as they are and cross-referenced from the landing-page directory rather than renumbered, because renumbering one register would invalidate the cross-references the other already publishes.",
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4/blob/main/COORDINATION.md"),

    dict(id="F-17", item="The three published layers define three different validation gates", type="Irregularity", kind="warn", status="resolved",
         detail="The Strategy Lab on this site scores seven gates (G1 data integrity, G2 out-of-sample, G3 minimum sample, G4 significance, G5 stability, G6 calibration, G7 not the benchmark). The decision-desk layer specifies eight (adding probability quality, economic performance, multiplicity control, parlay and prop integrity, and a shadow period). The X4 Console specifies nine (G0 to G8). No two layers use the same inventory.",
         why="The main site's seven are the gates that can actually be scored from the official data that exists; the other two are written as designs for gates that cannot yet be evaluated. A reader comparing the layers would reasonably ask which inventory is authoritative, so each layer states its own count on its own page and the difference is recorded here rather than left to be discovered.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/COORDINATION.md"),

    dict(id="F-34", item="Official injury-report drift on two practice-status cells", type="Irregularity", kind="warn", status="resolved",
         detail="The committed Week-10 injury dataset records Greg Van Roten (G, NE) and Charles Woods (CB, NE) as Limited participation. The live official NFL.com injury report, re-fetched 2026-11-14 by the new live-verification harness (tools/verify_live.py), shows both as Full Participation in Practice. The league updates the report during the week, so the committed cells reflect an earlier snapshot.",
         why="SUPERSEDED on 2026-11-15 by F-41: the injury dataset was re-captured from the live official page and regenerated through the pipeline. The text below records the state on 2026-11-14. The committed data was deliberately not changed then - editing it would fork the published numbers away from the snapshot the rest of the build was verified against. Both values and both source links are recorded here and on the decision-desk register (R-14) so the drift can be reviewed and, if the current snapshot is adopted, regenerated through the normal pipeline rather than hand-patched. This entry records the two cells this session's live harness caught; F-29 records the broader set of practice-status moves found by a parallel live verification, and the two are complementary, not duplicate.",
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/injuries-wk10-2026.csv"),

    dict(id="F-18", item="Market betting lines are not an official NFL publication", type="Unverified data", kind="partial", status="resolved",
         detail=("The league publishes no betting lines. The market columns on this site are therefore filled from a "
                 "captured feed - DraftKings prices read through the ESPN odds endpoint on 2026-11-14 - and every such "
                 "figure is labelled with that provenance. The store on this page holds 14 games (the 13 official Week 11 "
                 "games and the one final Week 10 game) across 12 phase cells each - 168 cells in total, of which 116 "
                 "carry a price and 52 are genuinely empty because the closing phase is reserved for a game that has "
                 "actually been played and 13 of the 14 games have not."),
         why="A market column is required by the brief and no official source exists for one, so the honest options are to publish nothing or to publish a clearly-labelled non-official price next to the official game identity. This site does the second: the price is never presented as an NFL line, the source is printed in the row, and the difference column (fair minus market) is published as its own column so a disagreement is never read as an edge. Where the feed had no price, the cell stays blank and says so.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/401873066/competitions/401873066/odds"),

    dict(id="F-19", item="Staking / bankroll figures", type="Unverified data", kind="no", status="unverified",
         detail="No staking, bankroll, Kelly or position-sizing figure is published for any strategy. The staking column of the leaderboard is blank.",
         why="Staking requires market prices and bankroll rules. With no licensed odds feed, no staking figure can be computed, which is exactly what keeps a lucky staking run from masquerading as signal.",
         official_url="https://www.nfl.com/",
         url="https://www.nfl.com/"),

    dict(id="F-20", item="ROI and expected-value figures", type="Unverified data", kind="no", status="unverified",
         detail="No ROI, expected value or parlay price is published for any bet, combination or player prop.",
         why="ROI needs a settled result (available in the verified results feed) AND a price at which the bet was taken (not available, see F-18). Until a price feed is authorised, ROI cells stay blank rather than be invented.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         url="https://www.nfl.com/schedules/2026/by-week/week-10"),

    dict(id="F-21", item="Replacement depth: starter, 2nd, 3rd, 4th string", type="Unverified data", kind="no", status="unverified",
         detail="No player on this site is assigned a replacement depth. The replacement-depth table records who replaced whom and why, but the depth column is blank for every row.",
         why="The NFL publishes no consolidated league depth chart that labels 1st/2nd/3rd/4th string, so any depth rank would be an invention. The fact of a replacement is tracked from league reporting; the depth of that replacement is not.",
         official_url="https://www.nfl.com/teams/",
         url="https://www.nfl.com/teams/"),

    dict(id="F-22", item="Demotion gate basis", type="Limitation", kind="warn", status="limitation",
         detail="The demotion gate (live strategy -> paper trading) is a project design choice, not an official NFL rule.",
         why="No league or regulator publishes a demotion gate for betting strategies. The gate's thresholds (5-game rolling window, 0.12 calibration gap, 10-game paper return) are analyst choices and should be challenged before any live use.",
         official_url="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
         url="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"),

    dict(id="F-23", item="Price-snapshot store values are model estimates, not official lines", type="Limitation", kind="warn", status="limitation",
         detail="The price-snapshot store records the opening and closing fair lines we originate for each market. The opening values are model estimates (S3 recommended line) derived from official NFL.com results; the closing values are blank until the games close.",
         why="Because we originate our own lines, the snapshot store is our own record. It is not a market observation and must not be read as an official or sportsbook line.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://www.nfl.com/schedules/2026/by-week/week-11"),

    dict(id="F-24", item="The Houston Texans publish their depth chart only as an image", type="Unverified data", kind="no", status="unverified",
         detail="houstontexans.com/team/depth-chart renders its chart as a single bitmap image with no table markup and no ordered text, so no Houston depth position can be transcribed from it. Houston is the only club of the 32 with no rows on the Depth & deficiency page.",
         why="The five Houston players the official NFL injury report rules Out or Doubtful for Week 10 (Azeez Al-Shaair, Marvin Harrison Jr., Danielle Hunter, Brevin Jordan, Keylan Rutledge) therefore have no published depth position on this site. Reading a rank off a picture would be an eyeball inference, so those cells are blank and the five names are listed as unmatched instead. T47 (2026-11-18) resolved the starter axis from an authorized source: the official NFL Game Book for Houston's Week 10 game at Cleveland yields actual starters and per-player snap counts, published as derived playing-time depth indices on houston-depth.html (raw Game Book rows stored privately under data/ops/raw/ per the T38 reuse gate). The ordinal 2nd/3rd/4th-string chain remains unavailable from any authorized structured source and stays blank.",
         official_url="https://www.houstontexans.com/team/depth-chart",
         url="https://www.houstontexans.com/team/depth-chart"),

    dict(id="F-25", item="20 officially ruled-out or doubtful players do not appear on their own club's published depth chart", type="Irregularity", kind="warn", status="irregularity",
         detail="Of the 81 players the official Week 10 injury report lists as Out or Doubtful (70 Out, 11 Doubtful), 62 appear on their club's published depth chart (61 by exact name, plus one name-only match flagged in F-42) and 20 do not: Lucas Patrick (WAS), Kerby Joseph (DET), Omarr Norman-Lott (KC), Micah Parsons (GB), BJ Green II (JAX), Tommy Townsend (TEN), Luke Rhodes (IND), Jonathon Brooks and Mike Jackson (CAR), Terrance Ferguson (LAR), Zachary Carter (ARI), Jalen Davis, Andrei Iosivas and Brian Parker II (CIN), Isas Waxter (LAC), plus the five Houston players above.",
         why="A club's depth chart is editorial and lags roster moves, so an absent name is not evidence the player is not on the team. The effect on this site is conservative: those 20 absences are counted in the official injury totals but not in the depth-based starter-out score, so the starter-out figures are a floor, not a ceiling. Each is listed by name on the Depth & deficiency page so a reviewer can chase them individually. (The count was 19 of 76 before the 2026-11-15 re-capture in F-41.)",
         official_url="https://www.nfl.com/injuries/",
         url="https://www.tennesseetitans.com/team/depth-chart"),

    dict(id="F-26", item="Clubs disagree on what a depth chart is, and some say so in writing", type="Irregularity", kind="warn", status="irregularity",
         detail="The Patriots state that their chart 'is unofficial and is published by the writers of Patriots.com' and does not necessarily reflect the organization's view. The Jets and Eagles say theirs is compiled by their communications departments. The Chiefs, Vikings, Rams, Titans, Bears, Bengals and Cardinals stamp a date on theirs (10-31 to 11-10); the others do not. Section and position labels differ club to club - DL / DT / NT / EDGE / RUSH / LOLB / WILL / MIKE / SAM / NCB / NICKEL / DB.",
         why="The ordering is official in the sense that the club publishes it, but it is editorial rather than a league record, and its vintage varies by up to a fortnight. No attempt is made here to reconcile the label vocabularies into a single taxonomy; each row keeps the club's own position label, so a reviewer sees exactly what the club printed. The date each club stamps is shown where one exists and left blank where the club stamps none.",
         official_url="https://www.patriots.com/team/depth-chart",
         url="https://www.patriots.com/team/depth-chart"),

    dict(id="F-27", item="A published depth chart is not proof of who started", type="Limitation", kind="warn", status="limitation",
         detail="Nothing in this dataset records who actually took the first snap. A club can list a player first and start someone else; snap counts and official game books would settle it, and neither is captured here.",
         why="The starter-out score therefore measures listed depth, not realised participation. It is a pre-game availability signal, which is what a line is set from, but it cannot be used as a post-game explanation of a result without the game books. The suggestion queue ranks game-book ingestion as the fix.",
         official_url="https://www.nfl.com/schedules/2026/",
         url="https://www.nfl.com/schedules/2026/"),

    dict(id="F-28", item="Only two position rows have no published replacement, and no row has both starter and backup out", type="Result", kind="ok", status="verified",
         detail="Tennessee is the only club where a listed starter is ruled out at a position where the club names nobody behind him: left guard Peter Skoronski and linebacker Cody Barton. No club has both its listed starter and its listed backup ruled out at the same position for Week 10.",
         why="This is a negative result and it is published because it constrains the strategy work: the '2nd and 3rd string replace the starter' cascade that the brief asks to detect cannot be found in the official Week 10 data at all, so any model that assumes a cascade is happening would be inventing it. The detection is in place for the weeks where it does occur.",
         official_url="https://www.nfl.com/injuries/",
         url="https://www.tennesseetitans.com/team/depth-chart"),

    # --- added by arena/4e108e9a-x4; numbered from F-29 because F-18..F-28
    # --- were already taken on main when this branch was reconciled.
    dict(id="F-29", item="Four practice statuses moved between the committed injury snapshot and the 2026-11-14 read", type="Irregularity", kind="warn", status="resolved",
         detail="tools/build.py reads data/injuries-wk10-2026.csv. Re-reading the official NFL.com injury report on 2026-11-14 for eight clubs (101 players, 404 practice-status fields) found four cells that no longer match: Houston's Montgomery and Jaylin Smith are now Full where the snapshot says Limited, Cleveland's Denzel Ward is now Limited where the snapshot says Full, and Arizona's Andrew Wingard is now DNP where the snapshot says Limited.",
         why="The snapshot was not overwritten. Both transcriptions are committed (research/verification/injuries-week10-2026-11-14-session-4e108e9a.csv) so a reader can see the drift rather than a silently corrected number. An earlier version of this flag described three drifts and 401 of 404 fields because it was computed from a four-club subset; the eight-club re-read found four, and the smaller number is the wrong one.",
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/injuries-week10-2026-11-14-session-4e108e9a.csv"),

    dict(id="F-30", item="No official closing line can exist, so the closing snapshot is stored empty", type="Limitation", kind="warn", status="unverified",
         detail="A closing line is the last price before kickoff. Every Week 11 game is still in the future, so no closing line exists for any of the 39 registered closing rows. The rows are stored with every price cell blank rather than omitted or back-filled.",
         why="Storing the row and leaving it blank is the difference between 'not yet observed' and 'not tracked'. Back-filling it with the current price would produce a column that looks like data and is a guess. It also means closing-line value cannot be computed yet, which is stated on the results page rather than worked around.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/market-snapshots.csv"),

    dict(id="F-31", item="The opening snapshot records points, not the price on those points", type="Limitation", kind="warn", status="unverified",
         detail="The opening spread and total are recorded as points (-1.0, 43.5). The american price attached to those points at the open (-110, -105, +100) is not part of the same published payload, so the opening rows carry a line without a price on it.",
         why="Points and prices are different numbers and a strategy can be right about one and wrong about the other. An opening line at -110 and the same line at +100 are not the same bet. Recording the points alone is truthful; attaching an assumed -110 would not be.",
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/market-prices.csv"),

    dict(id="F-32", item="The publication gate rejected the surname Fagnano as a placeholder marker", type="Irregularity", kind="warn", status="resolved",
         detail="site/check.py ran a case-insensitive substring search for a three-letter not-a-number placeholder marker over every published page. The row naming the Ravens' third-string quarterback - Joe Fagnano, as stated by nfl.com news - contains those three letters and failed the build. The page was correct and the checker was wrong.",
         why="Recorded rather than silently fixed because it is a failure mode worth knowing about: a substring placeholder test will eventually collide with a real word, and the collision produces a build failure that looks like a data problem but is not. The fix is a word-boundary match on that one marker, with the other markers left as substrings. The alternative - renaming the player - would have put an inaccurate name on the site to satisfy a checker.",
         official_url="https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season",
         url="https://github.com/karagemop466-tech/X4/blob/main/site/check.py"),

    dict(id="F-33", item="The depth register on this site contradicted the official injury report for four of its seven rows", type="Irregularity", kind="bad", status="unverified",
         detail="data/replacement-depth.csv, merged in with PR #21, has seven rows and all seven are marked verified=unverified. Four of them name a replacement without naming who he replaced: Cleveland (Watson), Arizona (Beck), the Rams (Puka Nacua) and Green Bay (Josh Jacobs). Two more are wrong on their face. The Rams row lists Puka Nacua as a replacement_in, but the official Week 10 injury report also in this repository records Nacua as DNP - did not participate - so he is not a replacement for anyone that week. The Green Bay row lists Josh Jacobs as a replacement_in, but the nfl.com article cited in the same row is the report that Jacobs himself is having finger surgery: he is the starter who is out, not the man coming in. The replacement_depth column, which is the one number the whole register exists to carry, is blank on all seven rows.",
         why="Flagged rather than quietly overwritten, because the register is on a published page and the contradiction is with official data already in this repository. The corrected chains are on the gates page, where each link is quoted and the starter is named, so the accurate version is already live and the reader can compare. The discrepancy is: this register says Jacobs is the replacement for a blank starter; the article it links says Jacobs is the injured starter.",
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/replacement-depth.csv"),

    # --- added by arena/1b8b6e9e-x4 (PR #26) as F-29..F-31; renumbered F-35..F-37 at
    # --- T31 integration because F-29..F-34 were already taken on main. Content unchanged.
    dict(id="F-35", item="Player-prop and prop-combination prices", type="Unverified data", kind="no", status="unverified",
         detail=("No player-prop price, prop line or prop-combination correlation is published. The 174 captured prices cover "
                 "only the three game markets - spread, total and moneyline - for 29 games."),
         why=("A prop price needs a licensed feed that carries player markets. The one book captured here publishes them, but no "
              "timestamped, reversible archive of player props was obtained, and a prop correlation can only be computed from "
              "prices that were actually captured. Estimating one would be invention, so the cells are blank. This is the "
              "remaining honest gap in the market work, and it is the reason no prop-combination product is priced anywhere "
              "on this site."),
         official_url="https://www.nfl.com/",
         url="https://www.espn.com/nfl/"),

    dict(id="F-36", item="Prices are from one book and are not official", type="Unverified data", kind="warn", status="limitation",
         detail=("The 174 captured prices on the Market & price archive page come from a single licensed sportsbook "
                 "(DraftKings, as published by ESPN) at the moment of capture. The NFL publishes no betting lines at all, so "
                 "no price on this site is an official league figure."),
         why=("A single book's number is a transcription of what that book showed, not a market consensus and not the best "
              "available price. It is enough to compute error against a real closing line, a ROI and a closing-line value; "
              "it is not enough to claim an arbitrage between books, to claim a price was the best available, or to call a "
              "line official. None of those claims is made, and every price row carries both its NFL.com result link and its "
              "ESPN odds resource so a reviewer can re-read the number."),
         official_url="https://www.nfl.com/",
         url="https://www.espn.com/nfl/"),

    dict(id="F-37", item="Doubled HTML entity in the depth summary text", type="Irregularity", kind="warn", status="resolved",
         detail=("Found by session arena/1b8b6e9e-x4: several phrases in this register and on the landing-page flag preview "
                 "showed a literal escaped ampersand (the word 'amp;' visible to the reader) because the register strings "
                 "carried a pre-escaped ampersand into a renderer that escapes text again. Fixed at T31 integration by writing "
                 "bare ampersands in this register's strings; the pages now render a plain '&' in those phrases."),
         why=("Recorded because it is a failure mode worth knowing about: a text pipeline that escapes in two places produces "
              "output that looks like a data error but is not. The strings in this register are rendered through an escaping "
              "helper (tools/pages.py flags_table), so they must contain bare text. The alternative - leaving a visible escape "
              "sequence on a published page - misleads readers into thinking the underlying label is wrong."),
         official_url="https://www.nfl.com/",
         url="https://www.nfl.com/"),

    dict(id="F-38", item="The two price stores use the word 'close' differently", type="Irregularity", kind="warn", status="irregularity",
         detail=("The price archive calls the last line the book was showing at the moment of capture 'close', so it is "
                 "filled for every game, played or not. The integrity store on the price-snapshot page calls that same "
                 "number 'current', and reserves 'close' for the closing line of a game that has actually been played, so "
                 "it is empty for the 13 games still to come. The numbers agree - 112 of 112 comparable values match "
                 "between the two captures - but the labels do not."),
         why=("Recorded rather than silently renamed, because the collision is easy to misread: a reader who compares "
              "the two pages and sees an empty 'close' in one of them could think a price is missing when it is the "
              "same number under another name. The reconciliation table on the Market & price archive page "
              "publishes the comparison number by number, and this flag names the difference. Neither store is edited "
              "to hide it."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/data/price_capture_reconciliation.csv"),

    dict(id="F-39", item="Desk rows without an official source link: the row-source gate was not reading row links", type="Irregularity", kind="bad", status="resolved",
         detail=("The per-row source check in tools/check_site.py recorded each link in the page-level list but never attached it to its "
                 "table row, so every row was tested as empty and the check passed without testing anything. Found by the source-provenance "
                 "audit (arena/5092bd99-x4) and fixed at T31 integration. With the check reading row links, 191 desk-table rows on 13 pages "
                 "had no https link; they were listed one by one in research/verification/row-source-gaps-2026-11-14.csv. They were "
                 "decision and requirement text, rubric weights, simulation output, programme status, or computed statistics whose "
                 "inputs were not linked row by row. None of them was a sourced official value that the page presented as confirmed. "
                 "A second gap of the same kind was in the price store: 26 spread and total points in the 2026W11-OPEN snapshot of "
                 "data/market-prices.csv had no source link (their note reads 'points only'); the moneyline rows of that snapshot are all linked. "
                 "A row-level follow-up (T43, arena/a04ae774-x4, 2026-11-17) re-audited the same 1,045 rows under the stricter "
                 "allowlisted-official-domain test: 366 rows carry no allowlisted official-domain link (175 have non-official HTTPS "
                 "only, 191 have no HTTPS at all), 624 rows are official-host-only, and 55 rows mix an allowlisted link with a "
                 "non-official HTTPS link without cell-level source attribution, so an NFL fixture link in such a row does not "
                 "support a third-party odds value beside it. The wider inventory is "
                 "research/audits/official-row-source-coverage-2026-11-17.md with its row-level records in "
                 "research/verification/official-row-source-coverage-2026-11-17.csv; the 191 figure above is the narrower "
                 "no-HTTPS count from research/verification/row-source-gaps-2026-11-14.csv and both are kept."),
         why=("RESOLVED on 2026-11-17 (T41, session arena/550d7436-x4) by line-by-line closure, not by weakening the gate: every one of the "
              "1,045 desk-table rows on 22 pages now carries an https source link, and the checker re-run reports 0 rows without one. "
              "NFL-fact rows link to the official NFL page; computed and programme rows cite the committed artifact that produced the value "
              "(GitHub blob of the exact CSV/script); blank decision rows cite the official page checked plus the flag. Two honest limits remain, "
              "and neither is closed by this fix: (1) the checker verifies link presence, not that a link supports the exact value beside it — "
              "a per-value semantic source gate is still open work; (2) the 26 'points only' price rows keep their recorded gap and stay "
              "unverified rather than gaining a link that does not support the value. Any reader should still treat a computed row as the "
              "artifact's output, not as an official NFL fact."),
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/audits/official-row-source-coverage-2026-11-17.md"),

dict(id="F-40", item="Ten further injury practice-status cells differ from the official report (reported, not yet independently re-checked)", type="Irregularity", kind="warn", status="resolved",
         detail=("A parallel session's full capture of the Week 10 injury page (345 of 345 rows) found twelve practice-status cells that "
                 "differ from data/injuries-wk10-2026.csv. Two are already flagged as F-34 (Greg Van Roten, Charles Woods). The other ten "
                 "are: Savion Williams (WR, GB), Antonio Johnson (S, JAX), Kaytron Allen (RB, MIA), David Montgomery (RB, HOU), Jaylin Smith "
                 "(CB, HOU), Denzel Ward (CB, CLE), Andrew Wingard (S, ARI), C.J. West (DT, SF), Von Miller (LB, DAL), Rodney Shelley (CB, LAC). "
                 "Each row, with its committed value, its live value and its official player page, is in "
                 "research/verification/live-verification-2026-11-14-e6ee28a8.md."),
         why=("SUPERSEDED on 2026-11-15 by F-41. Nine of these ten reproduce on the live read; Rodney Shelley does not (see F-41). "
              "The official report is updated during the week, so the committed snapshot is older than the live page. The committed data "
              "is deliberately not edited, so the published numbers stay tied to the snapshot they were verified against. The live values "
              "were captured by the parallel session through the platform's web tools; they were not independently re-checked from this "
              "sandbox, which cannot reach nfl.com. Recommended: re-run the capture and then regenerate the injury dataset through the "
              "normal pipeline, not by hand."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/live-verification-2026-11-14-e6ee28a8.md"),

    dict(id="F-41", item="Week 10 injury dataset re-captured from the live official NFL.com report: 347 rows, 26 corrected cells, 2 added rows", type="Irregularity", kind="warn", status="resolved",
         detail=("On 2026-11-15 the official NFL.com Week 10 injury report was read in full (every row of all 28 team sections). The read holds 347 player rows. "
                 "The committed file held 345. Against it, 26 cells differed in practice or game status, and two Baltimore rows were absent: Calais Campbell (DNP) and Ronnie Stanley (DNP). "
                 "Twelve of the 26 are in the Chargers section (Kayode Awosika, Bud Dupree, Justin Eboigbe, Ladd McConkey, Keaton Mitchell, David Njoku, Denzel Perryman, Trey Pipkins, Branson Taylor, Brenen Thompson, Isas Waxter, Kendall Williamson). "
                 "The other fourteen: Van Roten and Woods (NE), Savion Williams (GB), Antonio Johnson (JAX), Kaytron Allen (MIA), Arden Key (IND), David Montgomery and Jaylin Smith (HOU), Denzel Ward (CLE), Andrew Wingard (ARI), C.J. West (SF), Von Miller (DAL), Jaylinn Hawkins and Adam Randall (BAL). "
                 "The three Detroit designations that were listed as blank (Kerby Joseph, Cade Mays, D.J. Reed) read Out on the live page and were already Out in the committed file, so no blank remains. "
                 "Two figures in the brief did not reproduce: the committed file held 345 rows, not 254, and the live page holds 347, not 279. "
                 "Rodney Shelley (LAC) was recorded as Full-to-Limited on 2026-11-14 (F-40); the live read shows Full, matching the committed value, so that one change is not reproduced. "
                 "Every corrected value is the value printed on the page, transcribed to research/verification/official-injury-report-wk10-capture-2026-11-15.csv and checked against the committed file by tools/capture_check.py."),
         why=("The live page changes during the week, so the committed file is a dated copy and not a standing fact. The regenerated site now carries the 2026-11-15 read: depth counts, availability rows and the starter-out figures were recomputed by the normal pipeline, not hand-patched. "
              "The read was made with the platform's page-fetch tool, which returns the page as text; this sandbox cannot reach nfl.com directly, so the capture is a transcription of that text rather than the raw HTTP bytes. "
              "A raw, hashed, timestamped capture is what the new capture workflow (tools/capture_official.py) is built to keep, daily, once it runs on GitHub's runners."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/official-injury-report-wk10-capture-2026-11-15.csv"),

    dict(id="F-42", item="Two hand-written depth figures disagreed with the tool that produces them, and one depth match is by name only", type="Irregularity", kind="warn", status="irregularity",
         detail=("The README and research/depth-and-deficiency.md published 57 of 76 Out or Doubtful players on a club chart and 40 at depth 1, and cited this flag as F-19. "
                 "The depth tool's own output held 58 at the committed snapshot, so the prose did not match the tool it cited, and F-19 is the staking flag, not the depth one. "
                 "Michael Burton (CLE) is matched by name only. The injury report lists him as FB, Calf, Out; the club's chart lists a Michael Burton at RB, depth 3, Out, Calf. "
                 "The match counts him toward the 62 on-chart figure and he does not enter any starter count, because depth 3 is not a starter."),
         why=("A figure in prose must come from the run that produced the data. The README and the depth note now quote the rebuilt values (62 of 81 on chart; 41 at depth 1, 23 offense and 18 defense; 20 clubs with a starter out or doubtful; 20 unmatched; two holes; zero cascades) and cite F-25. "
              "The Burton match is left in place and flagged: a reviewer should confirm from the club's own page whether the chart's RB row is the same man the report lists at FB before the join is treated as exact."),
         official_url="https://www.nfl.com/injuries/",
         url="https://www.clevelandbrowns.com/team/depth-chart"),

    # --- added by arena/d15ce403-x4 (T40, 2026-11-17): live re-verification of the brief's named claims.
    # Register: research/verification/brief-claims-2026-11-17.md (CSV copy alongside).
    dict(id="F-43", item="The NFL.com reserve-list reads disagree with each other, so 'not listed' cannot be read as 'available'", type="Irregularity", kind="warn", status="open",
         detail=("Two official reads of the November 2026 reserve-list page disagree. The 2026-11-14 capture held 17 rows, dated 11/07 to 11/12, and included Michael Wilson (ARI, 11/10). "
                 "The 2026-11-17 read holds 25 rows, dated 11/10 to 11/17, and does not include Wilson or any 11/07, 11/08 or 11/09 entry. "
                 "Malik Willis (MIA, 11/10) is in both reads and is confirmed on NFL.com's own article (see F-44 and the register)."),
         why=("A reserve-list read that drops rows cannot prove a player is absent from the list, and a player missing from the list is not evidence he is healthy. "
              "The cause is not determined from this sandbox: the page may show a fixed number of rows per view, or the reader may not have followed a pagination control. "
              "Until the page's controls are checked and the list is captured in full, the reserve list is used only as evidence of a listing, never as proof of absence. "
              "Transcription: research/verification/official-reserve-list-2026-11-17.csv (25 rows)."),
         official_url="https://www.nfl.com/transactions/league/reserve-list/2026/11",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/official-reserve-list-2026-11-17.csv"),

    dict(id="F-44", item="Lamar Jackson and Tyler Huntley: NFL.com articles say both were placed on injured reserve, but neither is on the November reserve-list reads", type="Irregularity", kind="warn", status="open",
         detail=("NFL.com reported on 1 Nov 2026 that Jesse Minter said Jackson 'will be placed on injured reserve' (at least four games). A later NFL.com article says 'With Jackson and Tyler Huntley placed on injured reserve, the Ravens were forced to start undrafted third-stringer Joe Fagnano'. "
                 "Neither name appears on the NFL.com November reserve-list read of 2026-11-17 or on the 2026-11-14 capture."),
         why=("Two official NFL.com records disagree on whether two players are on IR. The articles are reporting; the reserve list is the transaction record. "
              "Until the reserve list shows both names, or a transaction record says otherwise, the IR status is carried as reported and not as a confirmed transaction. "
              "F-43 (incomplete reads) is the likeliest explanation to test first, but no cause is established here."),
         official_url="https://www.nfl.com/news/ravens-qb-lamar-jackson-suffers-right-thumb-injury-bills",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/brief-claims-2026-11-17.md"),

    dict(id="F-45", item="Baltimore: the club's own depth chart is current, but the committed replacement row for the Baltimore quarterback is out of date", type="Irregularity", kind="bad", status="open",
         detail=("The Ravens' depth chart, read on 2026-11-17 (https://www.baltimoreravens.com/team/depth-chart), lists Jacoby Brissett, Joe Fagnano and Kedon Slovis at QB, not Lamar Jackson or Tyler Huntley. The brief's stale-row claim (VR-17, VQ-07) is therefore not reproduced on the club chart. "
                 "The committed row in data/replacement-depth.csv for Baltimore says 'no replacement starter named in league reporting'. NFL.com reports Brissett's trade (ARI to BAL, 11/06, on the November trades table) and Fagnano starting a Week 9 Thursday night game."),
         why=("The row is wrong in the one place the club's chart is current, and the NFL.com article it cites reports a replacement. It is left unedited here because F-33 describes that file's contents, and changing one row would leave F-33 describing data that no longer matches. "
              "The owner of F-33 should correct the Baltimore row (replacement_in: Jacoby Brissett, with the trade as evidence) in the same pass as the other F-33 rows."),
         official_url="https://www.baltimoreravens.com/team/depth-chart",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/replacement-depth.csv"),

    dict(id="F-46", item="Re-confirmed on 2026-11-17: the Texans depth chart is an image only, labelled 'Unofficial Depth Chart', so no structured source exists for the Texans row", type="Irregularity", kind="warn", status="open",
         detail=("The Texans' depth-chart page, read 2026-11-17 (https://www.houstontexans.com/team/depth-chart), carries the chart as an image and labels it 'Unofficial Depth Chart'. The page holds no text rows that could be parsed. "
                 "This re-confirms F-24, which records the same image-only chart from the earlier read; it adds only the club's own 'Unofficial' label."),
         why=("The brief requires an authorised structured source for the Texans rows, and says transcription by eye is not acceptable. No such source was found in this session, so the Texans depth remains unparsed and no Texans starter is stated on this site (F-24). "
              "The five Houston players on the Out or Doubtful list are therefore counted as absent from a chart, not as confirmed off a chart (see F-24). "
              "A decision is needed: an authorised data feed, a written permission to use the image, or the club's confirmation that a text version exists."),
         official_url="https://www.houstontexans.com/team/depth-chart",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/brief-claims-2026-11-17.md"),

    dict(id="F-47", item="No immutable multi-day availability capture history exists on this branch: data/captures/ is absent, and the capture workflow runs from the default branch", type="Irregularity", kind="bad", status="open",
         detail=("data/captures/ does not exist in the repository, so the repository holds no raw, hashed, dated capture of the injury report or any club depth page. "
                 "The capture workflow (.github/workflows/capture.yml) is scheduled on the default branch and has run four times there, and all four runs failed before any capture was stored (see F-48)."),
         why=("The brief requires a multi-day history so practice designations can be replayed as they were known. One reading cannot support that. "
              "Until the capture workflow completes on main and commits captures, the requirement is not met and must not be described as met. "
              "The first step is the failing line in the run log (F-48)."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/.github/workflows/capture.yml"),

    dict(id="F-48", item="The official-capture workflow has failed on all four of its runs on main, so no capture has been stored", type="Irregularity", kind="bad", status="open",
         detail=("The capture workflow (.github/workflows/capture.yml), which fetches the NFL.com injury report and the 32 club depth-chart pages every six hours, has four runs on main, and all four concluded failure: "
                 "2026-11-16 06:40 UTC (run 43818369872), 2026-11-16 22:13 UTC (run 43967865851), 2026-11-17 08:00 UTC (run 44043083196), and 2026-11-17 21:00 UTC (run 44175196682). "
                 "In each run the step 'Fetch, schema-check and store the official pages' failed, and the verification, freshness and commit steps were skipped. "
                 "The job log could not be downloaded from the sandbox (the archive download returned an end-of-file error), so the failing line is not read here."),
         why=("Candidate causes, none confirmed: (a) an HTTP error or timeout on any of the 33 fetches (the injury page and 32 club pages), which the tool records as a failure; "
              "(b) the depth schema check, which requires a table tag in the raw HTML of every club page, while Houston publishes its chart as an image (F-24) and may carry no table; "
              "(c) the injury schema check, which requires the week heading and at least 28 'Practice Status' and 28 'Game Status' markers. "
              "The owner should open the failing run on GitHub, read the failing line, fix the check or the fetch, run the workflow manually, and confirm a stored capture and a passing freshness step. "
              "Until then there is no multi-day history, and the immutability requirement is not met."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/actions/workflows/capture.yml"),


    # ---- T41 (session arena/c30d278a-x4, 2026-11-17): seven of the eight irregularities (I-4 is F-24 and F-46)
    # logged in COORDINATION.md (I-1 to I-8), each re-checked against its source
    # before it was registered. Official pages read on 2026-11-17 with the
    # page-fetch tool; the captured figures are in research/verification/.
    dict(id="F-49", item="Side bets were settled on the straight-up winner, not on the spread: one recorded result was wrong (Week 9, CLE +4.5). Fixed on main", type="Correction", kind="warn", status="resolved",
         detail=("Before the fix (code at commit fb8a6cb, lines 575-578 of the then tools/origination.py), a side bet was graded by comparing the straight-up margin with the pick, "
                 "ignoring the selected team's closing line. Week 9, Browns at Saints (ESPN event 401873039): against its own closing line Cleveland (margin -1, plus 4.5) covers and the "
                 "bet is won, but the recorded row said lost. Official NFL.com final re-read live on 2026-11-18: CLE 22 - NO 23, overtime (see official_url). "
                 "Fixed on main in PR #63 (commit 915bf42): settlement now grades the official margin plus the recorded home handicap, with an exact tie as a push, and three regression "
                 "tests were added (tools/test_origination.py, run by the publication gate). The recorded row now says won. "
                 "Re-verified 2026-11-18 by this session: tools/settlement_recheck.py on the current tree reports 24 settled bets (Weeks 9-10), 0 changed outcomes, recorded = re-settled; "
                 "the published signal-vs-staking.html shows +15.414 units and +64.224% ROI per bet on n=24 and luck.html shows the same 15.41 units - the old claim that an uncorrected "
                 "figure was still published is no longer true. The pre-fix row survives in git history at fb8a6cb, so the original record stays auditable."),
         why=("This is a settlement error, not a change of rule, so it is corrected rather than argued. "
              "Caveats that still stand: n = 24 bets over eight games - neither ROI is evidence of skill, a game-cluster interval would span zero, and the prices are one book's "
              "(DraftKings as published by ESPN, third-party, see F-01), not official lines. Reproducible: tools/settlement_recheck.py re-settles every bet from the committed files "
              "without reusing tools/luck.py, and tools/test_origination.py pins the rule."),
         official_url="https://www.nfl.com/games/browns-at-saints-2026-reg-9",
         url="https://github.com/karagemop466-tech/X4/pull/63"),

    dict(id="F-50", item="An earlier count of six graded mismatches was wrong: the independent re-check reproduces one (none after the F-49 fix)", type="Irregularity", kind="warn", status="resolved",
         detail=("A previous session's board note reported six mismatches between the graded log and an official re-settlement. That count came from a bug in its first check. "
                 "Re-running the check on the recorded closing lines gave one mismatch - the bet in F-49 - and data/output/luck.json listed exactly that one entry "
                 "(pre-fix reference: 2.0821 units / 17.351% recorded, 4.0345 units / 33.621% re-settled over 12 bets, all from commit fb8a6cb). "
                 "Since the F-49 fix (PR #63), luck.json was regenerated on 2026-11-18: its mismatches list is empty and tools/settlement_recheck.py reports changed: 0 across 24 settled bets."),
         why=("The six-mismatch count appeared only in the coordination log, not on a published page, so no published figure needed changing. It is recorded here so the correction is visible. "
              "The stale luck.json was a generated artifact the gate never re-ran (tools/luck.py main() is not a validate step); it is now regenerated and matches the recheck."),
         official_url="https://www.nfl.com/games/browns-at-saints-2026-reg-9",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/settlement-recheck-2026-11-17.md"),

    dict(id="F-51", item="Official Week 10 'Out' players missing from their club's depth file (I-3): the same players as F-25, re-read where stated", type="Irregularity", kind="warn", status="irregularity",
         detail=("The depth file has no row for Kerby Joseph (DET, S) or Micah Parsons (GB, LB), and none for Luke Rhodes (IND) or Lucas Patrick (WAS), all listed Out in the official Week 10 report. "
                 "Re-read on 2026-11-17 from the official NFL.com Week 10 page: Kerby Joseph is Out (Did Not Participate, Out; knee) and Lucas Patrick is Out (Did Not Participate, Out; concussion). "
                 "Micah Parsons and Luke Rhodes were not re-read in this session, so their status is carried from F-25 and not re-verified."),
         why=("This is the same gap as F-25, listed by club so each one can be chased. It means the starter-out counts on the site are a floor, not a ceiling. "
              "A missing name is not proof that the player is off the roster, because a club chart is editorial and can lag roster moves (F-26)."),
         official_url="https://www.nfl.com/injuries/league/2026/reg10",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/settlement-recheck-2026-11-17.md"),

    dict(id="F-52", item="The depth file dates five club charts, not one: an earlier note said only the Packers' (I-5)", type="Irregularity", kind="warn", status="irregularity",
         detail=("The chart_date column in data/depth-wk11-2026.csv is filled for five clubs: Chicago 2026-10-31, and Green Bay, Las Vegas, San Francisco and Tennessee 2026-11-10. "
                 "The other 26 clubs have no date, and the site shows those as 'not stated'. "
                 "The five dates were not re-read from the club pages in this session."),
         why=("The earlier note under-counted the dated charts, so it is corrected here. A date is recorded only when the club page states one, so 'not stated' is the honest value for the rest. "
              "Before any replay of a depth chart as of a date, each dated chart should be confirmed from its club page."),
         official_url="https://www.packers.com/team/depth-chart",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/depth-wk11-2026.csv"),

    dict(id="F-53", item="No full dated series of the official injury report exists yet: one full read and one partial read (I-6)", type="Limitation", kind="warn", status="limitation",
         detail=("The Week 10 report was read on 2026-11-14, but that read holds only 44 rows (research/verification/injuries-wk10-live-2026-11-14.csv), not the full report. "
                 "The full read is the 2026-11-15 capture of 347 rows. "
                 "The two reads use different practice-status wording (for example 'Full Participation in Practice' against 'Full'), so no change in a designation can be measured from the pair. "
                 "The 2026-11-15 capture is a transcription of the page text, not raw bytes (F-41). No later capture is committed in research/verification/ as of 2026-11-17."),
         why=("A week-over-week or day-over-day delta needs at least two full, hashed, timestamped reads of the same report. The capture workflow in tools/capture_official.py is built for this, but no run after 2026-11-15 is in the repository. "
              "Until a second full read exists, the site publishes no change series, and it should not."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/official-injury-report-wk10-capture-2026-11-15.csv"),

    dict(id="F-54", item="Two demotion rules have blank thresholds, so they cannot trigger (I-7)", type="Limitation", kind="warn", status="limitation",
         detail=("data/ops/demotion_rules.csv leaves the threshold column empty for D1 (Skill evidence collapses) and D6 (Signal decay). "
                 "D1's trigger text reads 'one-sided p > 0.20 ... over the last 50 settled bets', so the number sits in the trigger, not in the threshold column, which is inconsistent with the other rules. "
                 "The pre-registration (research/preregistration/wk11-forward-v1.md) says a rule with a blank threshold reports NOT EVALUABLE, never passed."),
         why=("Choosing a threshold is a decision for the owner, not something the data can supply, so none is set here. "
              "Requested: the owner states D1's and D6's thresholds in the rules file, and moves D1's p-value into the threshold column, before any gate can be evaluated."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/ops/demotion_rules.csv"),

    dict(id="F-55", item="The Week 11 injury report is not yet published, and the Week 11 link serves Week 10 content (I-8)", type="Limitation", kind="warn", status="limitation",
         detail=("On 2026-11-17, https://www.nfl.com/injuries/league/2026/reg11 returned the Week 10 report, titled 'Official NFL Injury Report for Players - Week 10 of the 2026 Season', and its address resolved to /reg10. "
                 "No Week 11 designation exists in any official source read, so none is published. "
                 "The silent fall-back is the same pattern as F-09 for the schedule links."),
         why=("Week 11 kicks off between 19 and 23 November (research/preregistration/wk11-forward-v1.md), so an absent Week 11 report is expected today, not a fault. "
              "The pre-registration forbids using any Week 11 designation before kickoff. Re-check the report after it is published, and capture it with its hash. Re-checked 2026-11-18 03:55 UTC (T46 sweep): the reg11 address still serves the Week 10 report (title 'Week 10 of the 2026 Season', resolves to /reg10); state unchanged."),
         official_url="https://www.nfl.com/injuries/league/2026/reg11",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/preregistration/wk11-forward-v1.md"),

    dict(id="F-56", item="Capture-workflow code-path risks: a partial successful capture is lost and freshness is global, not per source (T40 audit)", type="Irregularity", kind="warn", status="irregularity",
         detail=("The T40 audit (research/audits/capture-workflow-health-2026-11-17.md) confirmed two code-path risks that survive even after "
                 "the failing runs recorded in F-47 and F-48 are fixed. (1) A partial success is lost: tools/capture_official.py fetch --kind all "
                 "can store one source's capture and write its manifest line before exiting non-zero on another source, and the workflow's later "
                 "verify/freshness/commit steps have no if: always() condition, so the partial capture dies with the runner. (2) Freshness is "
                 "global: freshness() takes the newest fetched_utc over every manifest entry and does not require schema_ok or a stored file per "
                 "source, so one fresh error entry could make the whole store look current. The run-log download returned EOF for two independent "
                 "sessions (arena/bdf71572-x4 and arena/550d7436-x4), so the fetch failure's cause stays unknown and is not guessed at here."),
         why=("These are design findings, not a diagnosis of the current failures. They matter because fixing only the fetch error would still "
              "leave a store that can lose good data silently. Clears when: a scheduled run stores a capture and manifest, hash verification "
              "passes, freshness is evaluated per source, and the failing-fetch cause is identified from the run logs. Update 2026-11-18: both code-path risks are fixed by the capture hardening integrated at T46 (per-source failure records persisted before the run fails; per-source freshness against schema-valid HTTP 200 captures; the empty Houston chart URL no longer raises ValueError - five offline unit tests), but a successful scheduled run and the historical failure cause are still required to clear this entry."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/audits/capture-workflow-health-2026-11-17.md"),

    dict(id="F-57", item="Under the stricter official-domain criterion, 464 of 1,259 desk rows still have no official-domain link, and no row yet carries source-to-value attribution (T-INT audit, arena/0c86fc5d-x4)", type="Limitation", kind="warn", status="limitation",
         detail=("The final-integration audit committed with PR #70 measured the tree against a criterion stricter than F-39's: a row must link "
                 "an allowlisted official domain (nfl.com and its subdomains, ftc.gov, the 32 clubs' own sites), not just any https URL, and each "
                 "source link should be attributable to the specific value it supports. Its audit found 366 of 1,045 rows short at its commit; "
                 "re-measured on the current tree (1,259 rows on 26 desk pages, after the F-39 closure added delta/luck/readiness/teams and the "
                 "artifact links), the count is 464 rows with no official-domain link, concentrated on workbench (111), price-store (78) and "
                 "programme (58) - mostly rows whose evidence is this project's own committed artifact (a GitHub blob of the exact CSV or script) "
                 "rather than an official NFL page. Audit record: research/audits/official-row-source-coverage-2026-11-17.md with its row-level CSV at "
                 "research/verification/official-row-source-coverage-2026-11-17.csv (published mirror: site/research/verification/official-row-source-coverage-2026-11-17.csv)."),
         why=("This does not contradict the F-39 closure, which used the any-https criterion the checker has always published: every row now "
              "carries a link, and computed rows honestly cite the artifact that produced them instead of borrowing an official URL that does "
              "not support the value. What remains open is real: (1) an allowlisted official-domain gate as a separate, stricter check, (2) "
              "source-to-value attribution per row, and (3) a semantic check that a link supports the value beside it. Until those land, a row "
              "whose only link is a repository artifact must be read as the artifact's output, not as an official NFL fact."),
         official_url="https://www.nfl.com/standings/",
         url="https://github.com/karagemop466-tech/X4/blob/main/site/research/verification/official-row-source-coverage-2026-11-17.csv"),

    dict(id="F-58", item="The published tree was one week stale on 2026-11-18: 13 Week 10 finals were missing and every standings-derived number was a week old (T46)", type="Irregularity", kind="warn", status="resolved",
         detail=("Read live on 2026-11-18, the official Week 10 schedule page shows all 14 finals played (Nov 12-16), while the committed game log held only the Nov 12 Thursday game. "
                 "The official standings had therefore moved for 28 of 32 clubs, and every number derived from them - the power ratings, the walk-forward evaluation (105 games), the leaderboard, "
                 "the luck panel and the Week 11 lines - described a season that no longer existed. Cause: no scheduled ingest of completed results; the last refresh ran on 2026-11-14."),
         why=("This is the failure mode the brief calls out most often: a static snapshot presented as current. It was not a data-entry error but an evidence-freshness error, and it made a correct model look "
              "measurably worse than it was (S1's improvement read 8.31% on 105 games and reads 9.49% on 118). Cleared by: the 13 finals transcribed from the official page, the standings rebuilt from the proved log, "
              "130 changed cells audited in research/verification/standings-refresh-2026-11-18.csv, and every derived number regenerated. Record: research/verification/official-reverify-2026-11-18.md."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/official-reverify-2026-11-18.md"),

    dict(id="F-59", item="The site publication gate hard-coded 137 game rows, so a completed official week failed the build (T46)", type="Irregularity", kind="warn", status="resolved",
         detail=("site/check.py's JavaScript smoke test asserted that the standings page renders exactly 137 game rows. When the 13 remaining Week 10 finals were added, the gate failed with 'expected 137 game rows in the DOM, found 150'. "
                 "A gate that must be hand-edited to accept new official results punishes freshness and will be edited carelessly under time pressure."),
         why=("Structural, not cosmetic: the same pattern can hide a genuinely missing row behind a literal. The expectation now reads the row count from data/games-2026.csv and still proves the week filter renders every row. "
              "Cleared by: the rewrite plus a full tools/validate.py pass."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/site/check.py"),

    dict(id="F-60", item="Week 11 venue naming differs between the official schedule page and the committed venue dataset (Houston, Kansas City) - resolved: both spellings are official and both are published", type="Irregularity", kind="warn", status="resolved",
         detail=("The committed venue set (data/venues-wk11-2026.csv) says RELIANT STADIUM for Colts at Texans and ARROWHEAD STADIUM for Cardinals at Chiefs. The official Week 11 schedule page names NRG Stadium and "
                 "'GEHA Field at Arrowhead Stadium' in its ticket and hotel links for the same two fixtures. Both are in-use names for the same buildings, so this is a naming question, not a venue error."),
         why=("The Game Info block of both official game pages has now been read (T48, 2026-11-18): Colts at Texans prints RELIANT STADIUM and Cardinals at Chiefs prints ARROWHEAD STADIUM, exactly as committed, "
              "and the same reading was made independently by T49 the same day. Both spellings are therefore official and both are published: the game-centre field is what this dataset transcribes, and the "
              "schedule page's hotel/ticket deep links carry the venues' current commercial names. Renaming by inference stays forbidden, so the dataset is unchanged. Record: "
              "research/verification/venue-gameinfo-2026-11-18.{md,csv}. The residual is a modelling rule, not a data gap: a venue name is not a join key, so any roof/surface/altitude feature must key on a stable venue id."),
         official_url="https://www.nfl.com/games/colts-at-texans-2026-reg-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/venues-wk11-2026.csv"),

    dict(id="F-61", item="[Superseded 2026-11-19, see F-83] The Week 11 official injury report still did not exist on 2026-11-18; the reg11 address served Week 10 content (confirms F-55)", type="Limitation", kind="warn", status="limitation",
         detail=("Read 2026-11-18: https://www.nfl.com/injuries/league/2026/reg11 renders Week 10 (title and heading both say Week 10 of the 2026 season), and https://www.nfl.com/injuries/ presents the Week 10 report as the latest published one. "
                 "Re-read ~04:10 UTC 2026-11-18 (T54 sweep): the league reg11 page still serves Week 10, and the official game-centre page for Colts at Texans now carries Week 11 practice designations for both clubs in its injury module (e.g. J. Carlies and S. Gardner 'Did not participate' for IND; A. Al-Shaair DNP, R. Blankenship/T. Dell/B. Fisher 'Full participation' for HOU), while Cardinals at Chiefs shows 'no active injuries at this time' for both clubs. The league-level Week 11 page is still the gate for publishing a full dataset; game-centre-only practice statuses are not captured as data here."),
         why=("The brief asks for designations to be captured Wednesday to kickoff. For Week 11 that cannot yet be done from an official source, and importing a secondary feed would break the single rule this repository "
              "holds to. Nothing is published for Week 11. This does not contradict F-55; it re-confirms it on a later date, which is the point of a dated series."),
         official_url="https://www.nfl.com/injuries/league/2026/reg11",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/official-reverify-2026-11-18.md"),

    # ---- T46 (session arena/ad5e4c3d-x4), 2026-11-18: found by re-deriving published numbers (renumbered from F-58..F-61 to avoid clashing with the flags merged from arena/bca9fb72-x4)
    # ---- T46 (session arena/ad5e4c3d-x4), 2026-11-18: found by re-deriving published numbers ---
    dict(id="F-62", item="The margin-vs-total correlation is published with n = 57 on two pages while it is computed on n = 54",
         type="Irregularity", kind="bad", status="open",
         detail=("tools/compute_stats.py computes the margin series and the total series from games with neutral_site == '0', "
                 "which is 54 of the 57 games in research/data/games_weeks6-9_2026.csv, and records n = 54 in "
                 "research/computed_stats.json ({n: 54, r: -0.3224, ci95: [-0.5432, -0.0598]}). The generated signals table prints "
                 "54 correctly. The executive-summary row and the correlations page attach 57 - the size of the input file - to the "
                 "same r. The three neutral-site games dropped (HOU at JAX week 6, PIT at NO week 7, CIN at ATL week 9) are not named "
                 "in the row label either. The value and interval are correct; the n beside them is not."),
         why=("The brief requires every correlation to be published with its n. Printing the file count instead of the observation count "
              "makes a result computed on 54 games look like one computed on 57, which is the exact substitution the requirement exists "
              "to prevent."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-6",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/repo-inconsistencies-2026-11-18.md"),

    dict(id="F-63", item="One home-edge measurement is published at +0.1 and at +0.07, and is measured on weeks 6-9 while 150 games exist",
         type="Irregularity", kind="warn", status="open",
         detail=("research/computed_stats.json holds home_edge = {n: 54, mean_home_margin: 0.074, ci95: [-3.59, 3.74]}, which re-derives "
                 "exactly from research/data/games_weeks6-9_2026.csv. The executive summary publishes it as +0.1 and the line-lab model "
                 "text as h = +0.07: the same quantity at two roundings. Separately, the window is weeks 6-9 only. Re-deriving on the full "
                 "verified corpus (weeks 1-10, neutral-site games excluded) gives n = 67 and a mean of -1.49, the opposite sign to the +0.07 "
                 "the line lab adds to every Week 11 spread."),
         why=("A model constant that flips sign when four more weeks of official results are included is not a measured edge yet; it is a "
              "window-dependent number. Publishing it as 'measured' without the window and the wider result is the overclaim."),
         official_url="https://www.nfl.com/schedules/2026/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/repo-inconsistencies-2026-11-18.md"),

    dict(id="F-64", item="The depth dataset cannot represent a shared rank-1 cell, stores no special-teams row, and 4 of 103 sampled live players are absent",
         type="Unverified data", kind="bad", status="open",
         detail=("data/depth-wk11-2026.csv holds 1,558 rows across 705 club/unit/position columns, of which 76 name a single player and "
                 "0 cells hold more than one player. Every club chart read this session publishes at least one shared or empty cell "
                 "(Seattle WR cell 1 lists Cooper Kupp and Rashid Shaheed together; Washington WR cell 2 is empty), and the dataset stores "
                 "the Seattle pair at depth 1 and 2. No special-teams row (P, K, H, LS, PR, KR) exists in the dataset, although every live "
                 "chart read publishes a special-teams section. A four-club live sample of offence charts (SEA, CLE, BAL, WAS; 103 players) "
                 "found 4 players absent from the dataset and the one shared rank-1 cell not represented."),
         why=("The brief's deficiency signal is 'a backup replaced a starter'. With co-starters stored as starter-plus-backup, the dataset "
              "would report a deficiency at a position where both men start, and a missing player cannot be reported absent at all. The "
              "depth-audit page quantifies this per club rather than disclaiming it in prose."),
         official_url="https://www.seahawks.com/team/depth-chart",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/depth-slot-fidelity-2026-11-18.md"),

    dict(id="F-65", item="Every scheduled official-capture run has failed, and the cause is a code defect: an empty depth-chart URL raises an uncaught ValueError",
         type="Irregularity", kind="bad", status="open",
         detail=("Four scheduled runs (2026-11-16 06:40, 2026-11-16 22:13, 2026-11-17 08:00, 2026-11-17 21:00) all fail at step 4, "
                 "'Fetch, schema-check and store the official pages', within 8 seconds, and steps 5-7 are skipped, so no capture and no "
                 "manifest line was ever stored. tools/depth.py sets the Houston chart URL to the empty string; "
                 "tools/capture_official.py fetch() passes every URL straight to urllib.request.Request, which raises ValueError "
                 "('unknown url type: ...') for an empty URL, and ValueError is not in the caught (URLError, OSError, TimeoutError) tuple. "
                 "HOU sorts 11th of the 32 club targets, which fits an 8-second abort and rules out 33 sequential 60-second timeouts. "
                 "REPAIRED 2026-11-18 on this branch: a blank/invalid URL is now skipped loudly (stderr note, manifest line, non-zero exit) "
                 "so one missing club page no longer discards the other 31 targets; the scheduled workflow still needs to run green to confirm. "
                 "The log text itself could not be retrieved (the Actions log blob returns EOF), so the conclusion is drawn from the step "
                 "outcome, the duration and the code path, and is labelled as such."),
         why=("Until this is fixed no multi-day availability history can exist, which blocks every capture-dependent requirement in the "
              "brief: replayable practice designations, inactive lists, and the designation-reliability study."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/actions/runs/44175196682"),

    dict(id="F-74", item="The price-snapshot 'opening' record is recomputed every build: the first published model line is not pinned, and the 2026-11-18 ingest silently rewrote it", type="Irregularity", kind="bad", status="open",
         detail=("tools/build.py rewrites data/price-snapshots.csv on every build from the current game log (the Week 11 lines block), and stamps each row 'captured_at: 2026-11-14 (build)'. "
                 "The file's own comment says the opening fair line is the first published model line, but nothing pins it. Found line by line during the 2026-11-18 T49 sweep while assessing a corpus ingest; "
                 "the defect then materialized for real: the Week 10 ingest (F-58) rebuilt the file and 25 of the 39 opening rows changed value while still carrying the '2026-11-14 (build)' stamp, "
                 "so the recorded Week 11 opening forecasts are no longer the ones first published. The pre-ingest values remain recoverable from git history at the pre-2026-11-18 commits."),
         why=("A price-snapshot store exists to preserve what was published when. An append-only store (as data/ops/price_snapshots.csv is for market prices - 'a re-ingest must never silently replace a reading') is the pattern; the model-line store does not follow it yet. "
              "Until it does, no rebuild can be trusted to leave a forecast record intact, and closing-line value cannot be measured against the true opening. Clears when: the opening rows are written once and never rewritten (append-only with a recorded clock time), "
              "and a regression test fails the build if a rebuild changes an existing opening row. The first-published Week 11 lines should then be restored from git history as the dated record."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/live-reverification-2026-11-18.md"),
    dict(id="F-75", item="Raw availability captures are committed to a public repository while the brief requires a private data layer for raw row-level data", type="Limitation", kind="warn", status="open",
         detail=("The capture pipeline (tools/capture_official.py, .github/workflows/capture.yml) stores raw injury-report and club depth-page bytes under data/captures/ in this repository. "
                 "GitHub reports the repository public, so those raw pages are public repository content, while the brief's data-layer split requires raw row-level data to sit in a private store until the terms are read. "
                 "The published site is not affected: the Pages artifact is site/ only and never serves data/. Raised as a privacy request by the capture-hardening session (arena/7db594d1-x4) and surfaced here for the owner's decision."),
         why=("No private store exists in this environment, and the brief also requires immutable multi-day raw captures with retained hashes, so both requirements cannot be met at once today. "
              "The repo's own register treats missing captures as the irregularity (F-47), so captures run while the question stays visible. "
              "Clears when the owner chooses: keep the repository public and accept raw pages as repository content, or make the repository private, or move data/captures to an authorized external store with a terms/retention decision recorded."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/live-reverification-2026-11-18.md"),

    dict(id="F-71", item="The decision-readiness 'what would change our mind' table published hard-coded numbers that contradicted the gate table directly above it", type="Irregularity", kind="bad", status="resolved",
         detail=("readiness.html prints the eight gates from data/ops/gates.csv and then, immediately below, a keep table whose three 'observed now' cells were typed into "
                 "tools/desk_extension.py: n = 12 in total, p = 0.0918, largest week 90 percent. The gate table on the same page reads n = 24, p = 0.1028 (z = -1.63) and "
                 "largest week = 58% from the committed file. All six figures were pre-refresh values carried over from before the Week 10 completion took the sample from "
                 "105 to 118 games; the n = 12 is older still, from the four-game luck sample. A reader was shown two different answers to the same question, six lines apart, "
                 "with the un-updated number in the table that is supposed to state the keep condition."),
         why=("This is the failure the brief's own rule targets: a value that cannot be traced to a committed source is exactly the value that goes stale. The gate table is "
              "built from the file; the keep table was typed, so nothing regenerated it. FIXED 2026-11-18 in tools/desk_extension.py::readiness_page(): all three cells are now "
              "read from data/ops/gates.csv, and the n from the same ledger the gate table uses, so the two tables cannot disagree again. No published measurement moved: the "
              "gates were already correct, only the duplicate copy of them was wrong."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/tools/desk_extension.py"),

    dict(id="F-72", item="The teams page called the Week 10 injury report a level with 'no second dated snapshot', while the second capture and its published delta exist", type="Irregularity", kind="warn", status="resolved",
         detail=("The teams.html table note read 'Injury counts are the Week-10 official report as a LEVEL, not a change. No second dated snapshot exists, so no delta is "
                 "published (gate S4)'. Two dated official captures of the same Week 10 report exist (2026-11-14, 345 rows; 2026-11-15, 347 rows), tools/injury_delta.py "
                 "publishes the cell-level diff between them, delta.html carries it, and readiness.html's own S4 row records the same two snapshots. The note was written "
                 "before the second capture and was never regenerated."),
         why=("The statement is the kind that quietly excuses a missing feature, and it was contradicted by two other pages of the same site. FIXED 2026-11-18: the note now "
              "says a second snapshot exists and points at the published delta, while still stating correctly that this particular table is a level and not that delta."),
         official_url="https://www.nfl.com/injuries/league/2026/reg10",
         url="https://github.com/karagemop466-tech/X4/blob/main/tools/injury_delta.py"),

    dict(id="F-73", item="The venue requirement was verified for 11 of 13 Week 11 fixtures; the other two carried an open naming question (F-60)", type="Irregularity", kind="warn", status="resolved",
         detail=("data/venues-wk11-2026.csv transcribes the Game Info block of each official game-centre page - the field that names a fixture's venue - but it had only "
                 "been read for 11 of the 13 Week 11 fixtures. The two named in F-60 (Colts at Texans, Cardinals at Chiefs) still carried a 2026-11-15 stamp and an open "
                 "question about the schedule page's different spelling. Read 2026-11-18: all 13 fixtures were re-read from their own game-centre Game Info block, and 13 of "
                 "13 agree with the committed file on both the city and the stadium string - 0 disagreements. The two F-60 fixtures print RELIANT STADIUM and ARROWHEAD "
                 "STADIUM, exactly as committed, so the schedule page's NRG Stadium and GEHA Field at Arrowhead are a second, official spelling in a different field "
                 "(the hotel/ticket deep link), not a contradiction of the venue field."),
         why=("The requirement is that every fixture's venue be transcribed from the official game centre. It now has been, for all 13, and the dataset was not edited "
              "because there was nothing to change - renaming by inference stays forbidden. An independent session (T49, arena/cc97fdb0-x4) re-read the same two fixtures "
              "the same day and reached the same values, so this is a two-source agreement. Both spellings are published side by side in "
              "research/verification/venue-gameinfo-2026-11-18.{md,csv}. The residual is a modelling rule, not a data gap: a venue name is not a join key, because two "
              "official pages spell the same building differently, so any roof/surface/altitude feature must key on a stable venue id. The Mexico City fixture's blank "
              "'state' cell is a faithful transcription - that page publishes no US state - and is named here rather than filled with a guess."),
         official_url="https://www.nfl.com/games/colts-at-texans-2026-reg-11",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/venue-gameinfo-2026-11-18.md"),

    dict(id="F-76", item="Two official sources name the Munich venue differently: the Game Book says Allianz Arena, the game centre says FC Bayern Munich Stadium", type="Irregularity", kind="warn", status="irregularity",
         detail=("Read 2026-11-18 for Patriots at Lions (2026 REG 10). The official Game Book header prints 'Allianz Arena, Munich, Germany'. The official game-centre page for the same fixture prints Location 'MUNICH' "
                 "and Stadium 'FC BAYERN MUNICH STADIUM'. Both strings are transcribed into data/venue-surface-wk10-2026.csv and onto the Game books page; neither is treated as the corrected name."),
         why=("The requirement is that the venue be transcribed from the official game centre. Doing that silently would have overwritten the Game Book's own string, and doing the reverse would have overwritten the "
              "game centre's. A venue name is an input to any stadium/roof/weather overlay, so the disagreement has to be visible to whoever builds that overlay. Not edited, not reconciled."),
         official_url="https://www.nfl.com/games/patriots-at-lions-2026-reg-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/venue-surface-wk10-2026.csv"),

    dict(id="F-77", item="The Cleveland starting defence is absent from the Houston-at-Cleveland Game Book conversion", type="Limitation", kind="warn", status="limitation",
         detail=("The Game Book's Lineups table for that game converted with three of its four columns intact: Houston offence, Houston defence, Cleveland offence. The Cleveland defence column is empty in all eleven rows. "
                 "605 of the expected 616 starter rows for Week 10 are published; the 11 Cleveland defensive starters are blank and carry the flag."),
         why=("Re-running the PDF conversion produced the same loss, so it is a property of this document's conversion rather than a one-off read error. The eleven jersey numbers are not published either, because a number "
              "without a name is a guess waiting to be joined to the wrong player. Clears when the club's own game notes or a re-issued Game Book supplies the column."),
         official_url="https://www.nfl.com/games/texans-at-browns-2026-reg-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/actual-starters-wk10-2026.csv"),

    dict(id="F-78", item="The Carolina-at-New Orleans Game Book lost the Did Not Play and Not Active section headers", type="Limitation", kind="warn", status="limitation",
         detail=("Four blocks of non-starters survive in the conversion, but only the first two carry a printed label (the two Substitutions lists). Under the Game Book's fixed section order the two unlabelled blocks would be "
                 "Did Not Play and Not Active, but that order is a template inference, not a printed label, so the blocks are stored in the private capture and are NOT used to decide whether a player played. "
                 "Nine Carolina and New Orleans designations are therefore unresolved and are counted as unresolved, not as either outcome."),
         why=("The brief's rule is that a value that cannot be confirmed from an official source stays blank and flagged. Labelling the blocks by template order would be an inference presented as a fact, and it would move "
              "players into the calibration denominator on the strength of a guess. Leaving them out makes n smaller and the interval wider, which is the honest direction to be wrong in."),
         official_url="https://www.nfl.com/games/panthers-at-saints-2026-reg-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/designation-outcomes-wk10-2026.csv"),

    dict(id="F-79", item="The Seattle-at-Las Vegas substitution lists are interleaved and truncated by the conversion and could not be transcribed", type="Limitation", kind="warn", status="limitation",
         detail=("The conversion split both clubs' substitution lists into four fragments scattered across the top of the document, the Lineups table and the foot of the scoring-summary page, with entries cut mid-name "
                 "('RB 36', 'LB 52'). The Did Not Play and Not Active lists for both clubs converted cleanly and are published. Because a non-starter who entered the game can only be identified from the substitution list, "
                 "Seattle and Las Vegas non-starters cannot be classified as played and are unresolved."),
         why=("Publishing a fragment would attach players to the wrong club. The cost is real: two clubs' backup-level Questionable players drop out of the calibration sample. That is recorded in n and in the unresolved "
              "count rather than hidden by a lower coverage claim. Clears when the Game Book is re-converted with a layout-preserving parser."),
         official_url="https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/ops/raw/gamebook-sea-at-lv-2026-reg10.txt"),

    dict(id="F-80", item="The Steelers-at-Bengals Game Book prints a referee who cannot have worked that game", type="Irregularity", kind="warn", status="irregularity",
         detail=("The PIT@CIN Game Book (kickoff 8:22 PM EST, Sunday 11/15/2026) prints Referee 'Willard, Don (58)'. The Miami-at-Indianapolis Game Book for the same Sunday, kicking off 1:03 PM EST, prints the same referee. "
                 "One referee cannot work two simultaneous games. The rest of the two officiating crews differ, so it is the referee cell that is wrong, not the whole block."),
         why=("The referee field is not needed for any published number, so the cheap fix would have been to publish it and let an analyst trip over it later. It is transcribed into the private capture with the contradiction "
              "recorded and is excluded from the published venue register. Not corrected to a name that was not printed."),
         official_url="https://www.nfl.com/games/steelers-at-bengals-2026-reg-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/ops/raw/gamebook-pit-at-cin-2026-reg10.txt"),

    dict(id="F-81", item="37 of 171 Week 10 designations are unresolved because the player does not appear in his own Game Book at all", type="Limitation", kind="warn", status="limitation",
         detail=("Every Game Book prints exactly four player lists: Lineups, Substitutions, Did Not Play, Not Active. A player on injured reserve or another reserve list appears in none of them, so an official 'Out' "
                 "designation for such a player has no game-book row to join to. Kerby Joseph (DET, Out), Micah Parsons (GB, Out), TreVeyon Henderson (NE, Out) and Peter Skoronski (TEN, Out) are examples in this week. "
                 "They are counted as unresolved and excluded from the play-rate denominator, never counted as 'did not play'."),
         why=("This is precisely the failure the brief names: 'capture the reserve list so not listed never means available'. Treating absence from a game book as a game-day inactive would inflate n and bias the play rate "
              "downward. The calibration is published with n and the unresolved count side by side so the reader can see how large the unmeasured group is."),
         official_url="https://www.nfl.com/injuries/league/2026/reg10",
         url="https://github.com/karagemop466-tech/X4/blob/main/data/designation-reliability-wk10-2026.csv"),

    dict(id="F-82", item="56 rows on the Game Book operations and glossary pages are exempt from the every-row-has-a-source rule", type="Limitation", kind="warn", status="limitation",
         detail=("The publication gate requires every data row to carry an official source link. The pipeline, private-artefact, reuse-gate and glossary tables describe this repository's own process and vocabulary - "
                 "a pipeline stage, a file path, the definition of a Wilson interval - so there is no official source that could back them. Their tables are marked class='doc' and the gate now counts them aloud "
                 "(56 rows) instead of either failing or skipping them silently."),
         why=("The alternative was to attach an official link to a row it does not support, which would make the coverage number meaningless - the gate's whole value is that every data row points at a real source. "
              "A silent skip would have been worse than a declared exemption, so the count is printed on every run. If a documentation row ever starts asserting a fact about the world, the class should be removed "
              "and the row should carry its source."),
         official_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         url="https://github.com/karagemop466-tech/X4/blob/main/site/check.py"),
    dict(id="F-83", item="The scheduled official-capture job has failed on every run since 2026-11-16: the NFL.com injury report now carries Week 11, its captured HTML fails the Week 10 schema gate, and no Week 11 designation is captured or published", type="Irregularity", kind="warn", status="open",
         detail=("Live re-read 2026-11-19 (T60): https://www.nfl.com/injuries/ carries the title 'Official Latest NFL Injury Report for Players - Week 11 of the 2026 Season', with Thursday Colts-Texans and Sunday Steelers-Eagles tables in the rendered page. "
                 "The committed capture manifest (data/captures/manifest.jsonl) shows the injuries source returning HTTP 200 with schema_ok false on 2026-11-18T07:37:40Z and 2026-11-18T20:37:55Z: week 11, 2 game-status headers, 26 player links. "
                 "The 2026-11-18T03:40Z capture passed (week 10, 28 headers, 347 links). The gate in tools/capture_official.py requires a 'Injuries - WEEK n' heading, at least 28 practice-status and 28 game-status headers, and at least 250 player links. "
                 "The scheduled job (run 44393037693, 2026-11-18T20:37Z, and the five runs before it back to 2026-11-16) fails at its final step by design, after the injury check recorded schema_ok false. "
                 "Freshness: running tools/capture_official.py freshness --kind injuries --max-hours 13 on 2026-11-19 at 06:57Z returns 2026-11-18T03:44:00Z, 27.2 hours old, and exits 1 (failed). "
                 "The publication gate (tools/validate.py) still passes, because its capture steps exercise the gates on synthetic fixtures and the scheduled workflow tolerates the freshness failure (continue-on-error). That gap is itself recorded here. "
                 "The raw bytes are private and not retained, and this sandbox cannot reach nfl.com over TLS from bash, so the cause (a changed layout, or a partial server render that omits most game tables) is not determined here."),
         why=("The drift alarm is working as designed: it refuses to publish a page it cannot parse, so no Week 11 designation was published from a broken parse. The consequence is that the injury data on the site is the Week 10 capture, one report behind the official page. "
              "The fix is a parser change in tools/capture_official.py plus a test fixture from a retained raw capture. That file is outside this session's scope and is logged as a request on the board, not edited here."),
         official_url="https://www.nfl.com/injuries/",
         url="https://github.com/karagemop466-tech/X4/blob/main/research/verification/integration-live-2026-11-19.md"),
]

# ------------------------------------------------------------------ verification log
VERIFICATION = [
    dict(check="Reconstructed game log matches the official NFL.com standings", result="pass",
         url="https://www.nfl.com/standings/",
         how="tools/verify.py rebuilds wins, losses, ties, points for, points allowed, net points and winning percentage for all 32 teams from 150 games and compares them to the official NFL.com standings totals. Every value matched exactly, which also proves every individual score."),
    dict(check="Week 10 completed slate matches the official Week 10 schedule page (T46, 2026-11-18)", result="pass",
         url="https://www.nfl.com/schedules/2026/by-week/week-10",
         how="All 14 Week 10 finals were read off the official page and compared with the game log; 13 were missing and were transcribed. tools/reverify_2026_11_18.py then required the completed log to reproduce the independently transcribed official standings for all 32 clubs before writing the refreshed file: 486 checks, 0 failures. The 130 standings cells that moved are audited in research/verification/standings-refresh-2026-11-18.csv."),
    dict(check="Every game row carries a working official NFL.com game URL", result="pass",
         url="https://www.nfl.com/schedules/2026/",
         how="Each row's URL is checked against the official /games/<away>-at-<home>-<season>-reg-<week> pattern, and the Week 5 and Week 10 links were opened directly and confirmed to show the same scores."),
    dict(check="Week 11 schedule matches NFL.com", result="pass",
         url="https://www.nfl.com/schedules/2026/by-week/week-11",
         how="The 13 games, their dates, kickoff times, broadcast networks, the Mexico City international designation and the six teams on bye were read directly from the official NFL.com Week 11 page."),
    dict(check="Week 10 injury report matches NFL.com", result="pass",
         url="https://www.nfl.com/injuries/",
         how="Every listed player, position, injury description, practice designation and game status was transcribed from the official NFL.com injury report for the 28 teams playing."),
    dict(check="Starter-change and long-absence facts", result="pass",
         url="https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders",
         how="Each is linked to the official NFL.com article that states it, rather than asserted from the injury report alone."),
    dict(check="No look-ahead in the model", result="pass",
         url="https://www.nfl.com/schedules/2026/by-week/week-10",
         how="Every Week-w prediction is produced from games in weeks strictly less than w, and each opponent's season rate is also measured at the same information time."),
    dict(check="Bootstrap is deterministic", result="pass",
         url="https://www.nfl.com/schedules/2026/",
         how="A fixed seed and a fixed resample count mean re-running tools/build.py reproduces identical confidence intervals."),
    dict(check="A strategy's improvement is statistically distinguishable from zero", result="flag",
         url="https://www.nfl.com/schedules/2026/by-week/week-10",
         how="The paired bootstrap interval, Bonferroni-adjusted for the number of strategies compared, still contains zero for every strategy. No strategy is marked eligible."),
    dict(check="Official market lines", result="flag",
         url="https://www.nfl.com/",
         how="The NFL publishes none. Every market-line cell is blank and every value-based statement about edge, ROI or parlay pricing is omitted."),
    dict(check="Official depth-chart strings", result="flag",
         url="https://www.nfl.com/teams/",
         how="No consolidated league source exists. No player is assigned a depth rank."),
    dict(check="Weeks 12-18 of the schedule", result="flag",
         url="https://www.nfl.com/schedules/2026/by-week/week-11",
         how="NFL lists several of those matchups as to-be-determined, so only the completed weeks and the official Week 11 schedule are published."),

    dict(check="Official standings re-read live after the PR #90 merge and compared with the committed standings (T54, 2026-11-18 ~04:05 UTC)", result="pass",
         url="https://www.nfl.com/standings/",
         how="All 32 clubs' W-L-T, PCT, PF, PA and NET were re-read from the official standings page through the page-fetch tool and compared with data/standings-wk10-2026.csv: 0 differences. This is an independent second re-read on the same day as T46's (V3), after two more PRs merged."),
    dict(check="The Week 11 venue rows' cited Game Info blocks re-read live (T54, 2026-11-18 ~04:08 UTC)", result="pass",
         url="https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11",
         how="Both Game Info blocks were read live: Colts at Texans prints RELIANT STADIUM and Cardinals at Chiefs prints ARROWHEAD STADIUM - exactly the committed values, so no venue cell changed. This session's independent reading (research/verification/live-sync-2026-11-18.csv, B5) agrees with the resolution now published on main (F-60, resolved by PR #92 with the same reading and research/verification/venue-gameinfo-2026-11-18.md), which is kept as the flag row; the NRG/GEHA readings come from the schedule page's ticket/hotel widgets."),
    dict(check="Standings: all 32 clubs re-read live and compared line by line (T60, 2026-11-19)", result="pass",
         url="https://www.nfl.com/standings/",
         how="The 32 official rows (W, L, T, PF, PA, net points) were read from the live page and compared with data/standings-wk10-2026.csv: 32 of 32 match, and net points equal PF minus PA for every official row. Row-level register: research/verification/integration-live-2026-11-19.csv."),
    dict(check="Week 10: all 14 final scores re-read live from the official schedule and compared with data/games-2026.csv (T60, 2026-11-19)", result="pass",
         url="https://www.nfl.com/schedules/2026/by-week/week-10",
         how="All 14 Week 10 finals on the live official schedule match the committed log, game by game, including the Los Angeles (LA) to LAR mapping. Each row links its official game page in the register."),
    dict(check="Week 11 injury report: live official page against the committed capture pipeline (T60, 2026-11-19)", result="flag",
         url="https://www.nfl.com/injuries/",
         how="The live page is the Week 11 report. The scheduled capture has rejected its last two reads on the schema gate (week 11, 2 status headers, 26 player links), so the site still shows the Week 10 capture. Logged as F-83; the parser fix is a request on the board."),
    ]
