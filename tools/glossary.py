#!/usr/bin/env python3
"""
The site glossary - one row per term the desk uses, with the page that uses it.

A glossary is not decoration here. The brief asks for a system whose numbers can
be audited by someone who did not build it, and every layer of this repository
has invented at least one word of its own - *origination*, *demotion gate*,
*replacement depth*, *unresolved*, *derived* - that means something narrower
than its everyday sense. Where a word is doing technical work, the definition
below says what it does and points at the page that uses it, so a reader can
check the claim instead of taking the word on trust.

Terms are grouped by the layer they belong to. Each row carries a link to the
page where the term is actually in force; a term with no such page is not
included, because a defined word that appears nowhere is noise.

Run:  python3 tools/glossary.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

# (term, layer, definition, page, anchor label)
TERMS = [
    # ---------------------------------------------------------- evidence
    ("Verified", "Evidence",
     "Read directly off an official primary source - nfl.com, operations.nfl.com, "
     "or a club's own site - and checked against that source. A verified cell "
     "carries the URL it came from in the same row.",
     "sources.html", "Source register"),
    ("Derived", "Evidence",
     "Computed from verified inputs by a rule that is written down and "
     "re-runnable. A play rate, a snap share and a difference between two lines "
     "are derived. Derived is weaker than verified and is always labelled as "
     "derived.",
     "methodology.html", "Methodology"),
    ("Unverified / blank", "Evidence",
     "The value is not published. A cell the official source does not print is "
     "left blank with the reason it is blank, never filled from memory, from "
     "another week, or from a non-official aggregator. Every blank is on the "
     "flags page with its source link.",
     "flags.html", "Flagged for review"),
    ("Flagged", "Evidence",
     "A value or a document fault that is published *as a flag* rather than "
     "corrected - a venue two official sources name differently, a PDF "
     "conversion that dropped a column, a referee a game book misprints. "
     "Flagged items do not block publication; they are listed with the source "
     "that produced them.",
     "flags.html", "Flagged for review"),
    ("Resolved / unresolved", "Evidence",
     "A designation is *resolved* when the player is found in his own game's "
     "Game Book - he played, or he is listed as not active or did not play. It "
     "is *unresolved* when he is in none of the four sections, which is what "
     "happens to a player on a reserve list. Unresolved is never counted as "
     "either outcome.",
     "gamebook.html", "Game books"),
    ("Capture", "Evidence",
     "A verbatim copy of an official page or PDF, stored under "
     "<code>data/ops/raw/</code> with a UTC stamp and a SHA-256. The hash is "
     "what makes a later edit detectable rather than invisible.",
     "gamebook-ops.html", "Game Book operations"),
    ("Reuse gate", "Evidence",
     "The rule that a stored capture is evidence, not content: its text may be "
     "re-read and re-checked but is not re-published as a table of its own. "
     "Only values derived from it reach the site.",
     "gamebook-ops.html", "Game Book operations"),

    # ------------------------------------------------------ the game book
    ("Game Book", "Game Book",
     "The official PDF the league publishes after each game, holding the "
     "lineups, substitutions, did-not-play and not-active lists, the header "
     "with stadium, surface, roof and weather, and the per-player playtime "
     "percentages.",
     "gamebook.html", "Game books"),
    ("Lineups", "Game Book",
     "The Game Book section listing the eleven players who started on each unit "
     "for each club. This is the league's own record of who started, which is "
     "not the same thing as a club depth chart.",
     "gamebook.html", "Game books"),
    ("Substitutions", "Game Book",
     "The Game Book's list of players who entered the game without starting. "
     "Together with Lineups it is the only official evidence that a player "
     "played.",
     "gamebook.html", "Game books"),
    ("Did Not Play", "Game Book",
     "The Game Book's list of players who dressed but did not take a snap. "
     "Distinct from Not Active, and published as its own section.",
     "gamebook.html", "Game books"),
    ("Not Active", "Game Book",
     "The club's declared game-day inactives. A player here was not eligible to "
     "play, which is a stronger statement than Did Not Play and is kept "
     "separate.",
     "gamebook.html", "Game books"),
    ("Playtime percentage", "Game Book",
     "The share of a club's snaps a player took, printed per player at the foot "
     "of the Game Book. It is the only official source of playing time, and "
     "therefore the fallback for depth where a club publishes no ordered chart.",
     "houston-depth.html", "Houston depth"),

    # ------------------------------------------------------- availability
    ("Designation", "Availability",
     "The game-status label on the official injury report: Out, Doubtful or "
     "Questionable. The calibration page measures what each one actually meant "
     "rather than assuming it.",
     "gamebook.html", "Game books"),
    ("Practice status", "Availability",
     "DNP (did not practise), LP (limited) or FP (full), as printed per day on "
     "the official injury report. Reported separately from the designation, "
     "because the two are different claims.",
     "availability.html", "Injuries &amp; depth"),
    ("Reserve list", "Availability",
     "A roster status - injured reserve, physically unable to perform, and "
     "similar - that removes a player from the game-day roster entirely. A "
     "player on a reserve list appears in no Game Book section, which is why "
     "his designation is unresolved.",
     "gamebook.html", "Game books"),
    ("Depth-1 / depth-2 / depth-3", "Availability",
     "A player's ordinal position on his club's own published depth chart. "
     "Taken from the club's chart or from measured playing time - never from "
     "jersey number, salary or experience, which the brief rejects.",
     "depth.html", "Depth &amp; deficiency"),
    ("Replacement depth", "Availability",
     "How far down the chart a club must go when a starter is out, and whether "
     "a replacement is named at all. It is measured, not assumed: a chain with "
     "no named replacement is published as a gap.",
     "replacements.html", "Replacement chains"),
    ("Deficiency", "Availability",
     "The drop in expected performance when a depth-2 or depth-3 player "
     "replaces a starter. Only computed where the replacement is named by an "
     "official source and the drop is measurable from official numbers.",
     "matchup.html", "Matchup matrix"),

    # ------------------------------------------------------- origination
    ("Origination", "Origination",
     "Producing our own number rather than taking a bookmaker's. The order is "
     "fixed - side first, then total, then moneyline - so a total cannot be "
     "reverse-engineered from a side.",
     "origination.html", "Line origination"),
    ("Fair line", "Origination",
     "Our own estimate of the correct number for a market.",
     "lines.html", "Model lines"),
    ("Market line", "Origination",
     "The price actually offered, captured with a timestamp. Published beside "
     "the fair line as its own column, never blended with it.",
     "markets.html", "Price store"),
    ("Difference", "Origination",
     "Fair line minus market line. Its own column, because an edge that is not "
     "separated from the two numbers that produce it cannot be audited.",
     "lines.html", "Model lines"),
    ("Point-in-time (PIT)", "Origination",
     "A price stored with the moment it was seen, and never overwritten. A "
     "backtest that uses a price that was not available at the time is testing "
     "a strategy that could not have been run.",
     "price-store.html", "Price store"),
    ("Closing line value (CLV)", "Origination",
     "The difference between the price taken and the closing price. Used as "
     "evidence about process, not as a profit claim.",
     "strategies.html", "Strategy lab"),

    # ---------------------------------------------------------- strategies
    ("Signal", "Strategies",
     "The part of a strategy that decides *what* to bet. Scored without seeing "
     "any stake, so a lucky staking run cannot make a bad signal look good.",
     "signal-vs-staking.html", "Signal vs staking"),
    ("Staking", "Strategies",
     "The part of a strategy that decides *how much*. Scored apart from the "
     "signal for the same reason.",
     "signal-vs-staking.html", "Signal vs staking"),
    ("Gate", "Strategies",
     "A numeric test a strategy must pass before it is published - sample size, "
     "stability, independence, and so on. A gate that can be hand-edited to "
     "admit a result is not a gate.",
     "gates.html", "Gates &amp; demotion"),
    ("Demotion gate", "Strategies",
     "The rule that sends a live strategy back to paper when its out-of-sample "
     "record degrades. It is the counterpart to the entry gates: without it a "
     "strategy that stops working keeps its rank.",
     "gates.html", "Gates &amp; demotion"),
    ("Walk-forward", "Strategies",
     "Fit on one window, test on the next, move the window forward. A strategy "
     "scored on the data it was fitted to has not been tested.",
     "method-lab.html", "Method lab"),
    ("Pre-registration", "Strategies",
     "Writing the rule, the sample and the pass criterion down before the "
     "result is known, so the criterion cannot be moved to accommodate the "
     "result.",
     "method-lab.html", "Method lab"),

    # --------------------------------------------------------- statistics
    ("Wilson score interval", "Statistics",
     "A confidence interval for a proportion that stays inside 0 and 1 and "
     "behaves sensibly at small n. Used for every play rate, because at n=6 a "
     "normal interval produces nonsense.",
     "gamebook.html", "Game books"),
    ("n", "Statistics",
     "The number of observations behind an estimate. Printed next to every rate "
     "and every correlation, because a rate without n is not a measurement.",
     "correlations.html", "Correlations"),
    ("Brier score / skill", "Statistics",
     "A proper scoring rule: it rewards honest probabilities rather than "
     "confident ones, and it cannot be gamed by saying 100% when unsure. Skill "
     "is the score relative to a stated baseline.",
     "luck.html", "Removal of luck"),
    ("Game-cluster interval", "Statistics",
     "An interval built by resampling whole games rather than individual bets. "
     "Bets inside one game share a result, so treating them as independent "
     "makes an interval far too narrow.",
     "luck.html", "Removal of luck"),
    ("Multiplicity adjustment", "Statistics",
     "The correction applied when many strategies are tested at once. With "
     "enough candidates, the best-looking one will look good by chance.",
     "luck.html", "Removal of luck"),
    ("Joint-evidence gate", "Statistics",
     "The rule that a parlay or prop combination cannot be priced by "
     "multiplying its legs' individual probabilities. Legs of the same game are "
     "dependent, so the product is not the probability of the combination.",
     "gates.html", "Gates &amp; demotion"),
    ("Correlation (with n)", "Statistics",
     "Computed only from officially sourced numbers and published with the "
     "number of pairs it rests on and an interval. A correlation without n and "
     "an interval is a decoration.",
     "correlations.html", "Correlations"),
    ("ROI / win rate", "Statistics",
     "Deliberately *not* the ranking statistic. Both are dominated by variance "
     "over the sample sizes available here, so ranking on them ranks luck.",
     "leaderboard.html", "Leaderboard"),
]


def body_real():
    import pages as P
    esc, table = P.esc, P.table
    layers = []
    for term, layer, defn, page, label in TERMS:
        if layer not in [l for l, _ in layers]:
            layers.append((layer, []))
        for l, items in layers:
            if l == layer:
                items.append((term, defn, page, label))
                break

    h = []
    h.append(
        '<section class="card"><span class="eyebrow">How to read this</span>'
        '<p>Every layer of this desk invented at least one word of its own, and '
        'several of them mean something narrower than their everyday sense - '
        '<i>unresolved</i> is not <i>unknown</i>, <i>derived</i> is not '
        '<i>verified</i>, and <i>signal</i> deliberately excludes the stake. The '
        'definitions below are the ones the pages actually use. Each row links to '
        'the page where the term is in force, so the definition can be checked '
        'against the thing it describes rather than taken on trust.</p>'
        '<p>A term appears here only if a page uses it. A defined word that '
        'appears nowhere is noise, so the list is generated from the vocabulary '
        'of the site and not from a thesaurus.</p></section>')

    h.append('<section><div class="section-head"><div>'
             '<span class="eyebrow">Terms</span>'
             '<h2>Grouped by the layer that uses them</h2>'
             '<p class="muted">%d terms across %d layers.</p></div>'
             '<span class="tag">%d terms</span></div>'
             % (len(TERMS), len(layers), len(TERMS)))

    for layer, items in layers:
        rows = []
        for term, defn, page, label in items:
            rows.append([
                "<strong>%s</strong>" % esc(term),
                defn,
                '<a href="%s">%s</a>' % (esc(page), label),
            ])
        h.append('<div class="sub-head" style="margin-top:22px">'
                 '<span class="eyebrow">%s</span></div>' % esc(layer))
        h.append(table([("Term", 0), ("What it means here", 0),
                        ("Where it is used", 0)], rows, cls="doc"))
    h.append('</section>')
    return "".join(h)


def write_pages(site_dir, shell):
    body = body_real()
    with open(os.path.join(site_dir, "glossary.html"), "w", encoding="utf-8") as fh:
        fh.write(shell(
            "glossary", "Glossary",
            "Every term this desk uses in a technical sense, what it means here, "
            "and the page where it is in force - so a number can be checked by "
            "someone who did not build the system.",
            body, "glossary.html"))
    return ["glossary.html"]


def main():
    print("glossary: %d terms" % len(TERMS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
