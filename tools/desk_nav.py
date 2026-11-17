#!/usr/bin/env python3
"""
The single source of truth for the decision-desk sidebar.

Every desk page - the hand-written ones and the generated ones - must carry the
same navigation, because `tools/check_site.py` fails the build if any page's nav
link set differs from the others. Before this module existed the nav was copied
into four generators and into every page, which is how two of them drifted
apart and the build failed.

One list, one rendering, one place to change it.
"""

NAV = [
    ("index.html", "◫ &nbsp;Overview"),
    ("executive-summary.html", "★ &nbsp;Executive summary"),
    ("requirements.html", "☰ &nbsp;Requirements"),
    ("data.html", "▦ &nbsp;Verified data"),
    ("signals.html", "◎ &nbsp;Line lab &amp; signals"),
    ("leaderboard.html", "↗ &nbsp;Leaderboard"),
    ("origination.html", "⊞ &nbsp;Line origination"),
    ("price-store.html", "◈ &nbsp;Price store"),
    ("signal-vs-staking.html", "⚖ &nbsp;Signal vs staking"),
    ("correlations.html", "∿ &nbsp;Correlations"),
    ("replacements.html", "＋ &nbsp;Availability &amp; depth"),
    ("luck.html", "⚈ &nbsp;Removal of luck"),
    ("method-lab.html", "⌁ &nbsp;Method lab"),
    ("ops-review.html", "✧ &nbsp;Review gate"),
    ("verification.html", "✓ &nbsp;Verification"),
    ("requirements-closure.html", "☑ &nbsp;Requirement closure"),
    ("injuries.html", "＋ &nbsp;Availability"),
    ("teams.html", "＋ &nbsp;Per-team view"),
    ("decisions.html", "? &nbsp;Decision Q&amp;A"),
    ("review.html", "✳ &nbsp;Suggestions"),
    ("workbench.html", "✳ &nbsp;Suggestion workbench"),
    ("programme.html", "◫ &nbsp;Integrity &amp; programme"),
    ("readiness.html", "⚑ &nbsp;Decision readiness"),
    ("flagged.html", "⚑ &nbsp;Flagged for review"),
    ("repo-review.html", "§ &nbsp;Repo review"),
    ("sources.html", "↗ &nbsp;Sources"),
]


def side():
    """The full sidebar element, as HTML."""
    return ('<aside class="sidebar"><a class="brand" href="index.html">'
            '<span class="brand-mark">4D</span>'
            '<span>FOURTH DOWN<small>RESEARCH DESK</small></span></a>'
            '<div class="side-label">WORKSPACE</div><nav>' +
            "".join('<a href="%s">%s</a>' % (h, l) for h, l in NAV) +
            '</nav><div class="side-bottom"><span class="pulse"></span> Research mode '
            '<small>Snapshot 2026-11-14 \u00b7 no live feed</small></div></aside>')
