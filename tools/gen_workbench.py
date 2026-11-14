#!/usr/bin/env python3
"""Generate workbench.html - the suggestion review workbench.

Reads tools/workbench.json (hand-curated, rubric-scored), computes the weighted score of
every item, ranks them, and renders:
  - the rubric, so a reviewer can re-score any item and disagree with the ranking
  - every item with its four scores, its evidence and what it unblocks
  - a review control (Accept / Hold / Reject) that stores the reviewer's decision in the
    browser and shows the resulting shortlist

The score is explicitly labelled a demo prioritisation model. The reviewer's decision is
the only thing that decides.

Run:  python3 tools/gen_workbench.py
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desk_nav

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WB = json.load(open(os.path.join(ROOT, "tools", "workbench.json"), encoding="utf-8"))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


W = WB["weights"]
CRIT = [c["criterion"] for c in WB["rubric"]]
for it in WB["items"]:
    it["score"] = round(sum(it["scores"][c] * W[c] for c in CRIT), 3)

ranked = sorted(WB["items"], key=lambda i: (-i["score"], i["id"]))
for n, it in enumerate(ranked, 1):
    it["rank"] = n

by_category = {}
for it in ranked:
    by_category.setdefault(it["category"], []).append(it)

CAT_ORDER = ["Data integrity", "Statistics", "Model", "Markets", "Leaderboard",
             "Governance", "Interface"]
assert set(by_category) <= set(CAT_ORDER), set(by_category) - set(CAT_ORDER)

# ------------------------------------------------------------------ score helpers
def bar(score):
    pct = int(round((score - 1) / 4 * 100))
    tone = "ok" if score >= 4.5 else ("info" if score >= 3 else "warn")
    return ('<span class="wb-bar"><span class="wb-bar-fill %s" style="width:%d%%"></span></span>'
            '<b>%.1f</b>' % (tone, pct, score))


def score_cells(it):
    return [bar(it["score"])] + ["%d" % it["scores"][c] for c in CRIT]


head_scores = ["Weighted score"] + ["%s (%s)" % (c, W[c]) for c in CRIT]

# ------------------------------------------------------------------ item cards
cards = []
for it in ranked:
    cards.append(
        '<article class="sug-card wb-card" id="%s" data-id="%s" data-score="%.3f">'
        '<div class="wb-card-head"><span class="wb-rank">#%d</span>'
        '<h3>%s</h3><span class="pill info">%s</span></div>'
        '<p class="wb-summary">%s</p>'
        '<table class="wb-mini"><tbody>'
        '%s'
        '<tr><th>Evidence</th><td>%s</td></tr>'
        '<tr><th>Cost</th><td>%s</td></tr>'
        '<tr><th>Unblocks</th><td>%s</td></tr>'
        '</tbody></table>'
        '<div class="sug-controls" data-id="%s">'
        '<span class="sug-label">Your decision</span>'
        '<button class="sug-pick" data-pick="accept">Accept</button>'
        '<button class="sug-pick" data-pick="hold">Hold</button>'
        '<button class="sug-pick" data-pick="reject">Reject</button>'
        '<span class="sug-status" data-id="%s">not reviewed</span>'
        '</div></article>' % (
            it["id"], it["id"], it["score"], it["rank"], esc(it["title"]), esc(it["category"]),
            esc(it["summary"]),
            "".join("<tr><th>%s</th><td>%s</td></tr>" % (c, bar(it["scores"][c]))
                    for c in CRIT),
            esc(it["evidence"]), esc(it["cost"]), esc(it["blocks_if_skipped"]),
            it["id"], it["id"]))

# ------------------------------------------------------------------ tables
table_rows = []
for it in ranked:
    table_rows.append(
        ['<b>#%d</b>' % it["rank"], '<b>%s</b><br><span class="muted">%s</span>' % (esc(it["title"]), it["id"]),
         esc(it["category"])] + score_cells(it) +
        ['<a href="#%s">review &darr;</a>' % it["id"]])

cat_rows = []
for cat in CAT_ORDER:
    items = by_category.get(cat, [])
    if not items:
        continue
    cat_rows.append([esc(cat), str(len(items)),
                     ", ".join("#%d" % i["rank"] for i in items),
                     "%.2f" % (sum(i["score"] for i in items) / len(items))])

rubric_rows = [[("<b>%s</b>" % esc(c["criterion"])), "%s" % W[c["criterion"]],
                esc(c["question"]), esc(c["scale"])] for c in WB["rubric"]]

side = desk_nav.side()

top = ranked[0]
body = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Suggestion workbench: twelve proposals scored against one documented rubric, ranked, and reviewable with An accept / hold / reject decision that is stored in the browser."><title>Suggestion workbench | Fourth Down Research</title><link rel="stylesheet" href="desk.css"></head>
<body>
{side}
<main>
<header class="topbar"><div><span class="eyebrow">15 &middot; SUGGESTION WORKBENCH</span><h1>Suggestion workbench</h1></div><span class="status-pill"><i></i> {len(WB['items'])} proposals &middot; 0 decided here</span></header>

<section class="section" id="how"><div class="section-head"><div><span class="eyebrow">HOW THIS WORKS</span><h2>Score first, decide second</h2><p class="muted">Every proposal is scored on the same four dimensions, 1 to 5, by one rubric printed below. The weighted score orders the list; it does not decide anything. Your Accept / Hold / Reject choice is stored in this browser and builds a shortlist you can act on. Nothing on this page is implemented by reading it.</p></div><span class="tag green">RUBRIC v{WB['version']}</span></div>
<div class="cards">
  <div class="card"><span class="k">TOP OF THE LIST</span><h3>#{top['rank']} &middot; {esc(top['title'])}</h3><p>Weighted score {top['score']:.2f} of 5. {esc(top['cost'])}</p></div>
  <div class="card"><span class="k">HOW TO READ THE SCORE</span><h3>4 &times; 1&ndash;5, weighted</h3><p>Decision value {W['decision_value']}, confidence {W['confidence']}, effort {W['effort']}, risk {W['risk']}. A high score means "worth considering first", never "approved".</p></div>
  <div class="card"><span class="k">YOUR SHORTLIST</span><h3><span id="wb-accepted">0</span> accepted &middot; <span id="wb-held">0</span> held &middot; <span id="wb-rejected">0</span> rejected</h3><p>Stored locally in this browser. <a href="#" id="wb-clear">Clear all decisions</a></p></div>
</div>
<div class="note"><b>Why a rubric and not a vote.</b> A ranked list with hidden criteria cannot be argued with. A list with the criteria exposed can: if you think "one scheduled capture job" should not outrank "resolve the absence-window conflict", you can see the four numbers that put it there and change the number you disagree with. The weights are in <code>tools/workbench.json</code> and the page is regenerated from it.</div>
</section>

<section class="section" id="rubric"><div class="section-head"><div><span class="eyebrow">THE RUBRIC</span><h2>Four dimensions, one definition each</h2></div><span class="tag">1&ndash;5 SCALE</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Criterion</th><th>Weight</th><th>Question it asks</th><th>How to score it</th></tr></thead><tbody>
{"".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in rubric_rows)}
</tbody></table></div>
<div class="note"><b>Two dimensions are deliberately inverted.</b> Effort and risk are scored so that <b>higher is better</b> (5 = cheapest, 5 = safest), which keeps every bar comparable. The labels say so on every card. A naive "effort" column where low is good would silently invert the weighting.</div></section>

<section class="section" id="ranking"><div class="section-head"><div><span class="eyebrow">THE RANKING</span><h2>Twelve proposals, one order</h2><p class="muted">Sorted by weighted score, ties broken by id. The individual scores are shown so the order can be audited score by score.</p></div><span class="tag green">DEMO MODEL</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Rank</th><th>Proposal</th><th>Category</th>{''.join('<th>%s</th>' % esc(h) for h in head_scores)}<th>Review</th></tr></thead><tbody>
{"".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in table_rows)}
</tbody></table></div>
<h3>By category</h3>
<div class="table-wrap"><table class="data"><thead><tr><th>Category</th><th>Proposals</th><th>Ranks</th><th>Mean score</th></tr></thead><tbody>
{"".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in cat_rows)}
</tbody></table></div></section>

<section class="section" id="review"><div class="section-head"><div><span class="eyebrow">REVIEW</span><h2>Decide on each proposal</h2><p class="muted">Each card carries its scores, the evidence behind it, what it costs and what stays blocked if it is skipped. Accept means "build this next"; Hold means "not yet, and say why later"; Reject means "close it". The choice is stored in your browser and is not published anywhere.</p></div><span class="tag amber">NOTHING IS APPLIED AUTOMATICALLY</span></div>
<div class="suggestion-grid">
{"".join(cards)}
</div></section>

<section class="section" id="next"><div class="section-head"><div><span class="eyebrow">AFTER REVIEW</span><h2>What to do with a shortlist</h2></div><span class="tag">SEQUENCE</span></div>
<div class="table-wrap"><table class="data"><thead><tr><th>Step</th><th>Action</th><th>Why in this order</th></tr></thead><tbody>
<tr><td>1</td><td><b>Accept at most two items per cycle</b></td><td>A shortlist of eight is a wish list; the repository's whole value is that each step is finished and verified before the next begins.</td></tr>
<tr><td>2</td><td><b>Build the highest-scoring accepted item end to end</b></td><td>Including its gate, its data source and its page. A half-built suggestion is worse than an unbuilt one because it looks done.</td></tr>
<tr><td>3</td><td><b>Re-score after it lands</b></td><td>Most of these items change each other's scores: the capture job raises the confidence of everything that needs a price, and settling Weeks 1&ndash;9 raises the sample on everything else.</td></tr>
<tr><td>4</td><td><b>Publish the decision and the reason</b></td><td>On <a href="review.html">Suggestions</a>, beside the proposal. A rejected suggestion with a stated reason is more useful than one that quietly disappears.</td></tr>
</tbody></table></div>
<div class="callout"><b>The honest summary.</b><p>Two items dominate: <b>#{ranked[0]['rank']}</b> and <b>#{ranked[1]['rank']}</b>. Both are cheap, both are already evidenced inside the repository, and together they unblock the closing-line gate, the sample-size gate and four of the five demotion rules. Every other proposal on this page is worth less until those two are done, which is why they rank first and why the page recommends accepting at most two at a time.</p></div>
</section>

<footer><span>FOURTH DOWN RESEARCH &middot; Suggestion workbench</span><span><a href="review.html">&larr; Suggestions</a> &middot; <a href="programme.html">Integrity &amp; programme &rarr;</a></span></footer>
</main>
<script src="nav.js"></script>
<script>
(function () {{
  var KEY = "4d-workbench-v1";
  var state = {{}};
  try {{ state = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{ state = {{}}; }}
  var counts = {{accept: 0, hold: 0, reject: 0}};

  function paint() {{
    counts = {{accept: 0, hold: 0, reject: 0}};
    document.querySelectorAll(".sug-controls").forEach(function (box) {{
      var id = box.getAttribute("data-id");
      var pick = state[id] || "";
      box.querySelectorAll(".sug-pick").forEach(function (b) {{
        b.classList.toggle("st-selected", b.getAttribute("data-pick") === pick);
      }});
      var st = box.querySelector(".sug-status");
      if (st) {{ st.textContent = pick ? pick + "ed" : "not reviewed"; }}
      if (counts[pick] !== undefined) {{ counts[pick] += 1; }}
      var card = box.closest(".wb-card");
      if (card) {{ card.setAttribute("data-decision", pick || "none"); }}
    }});
    var a = document.getElementById("wb-accepted");
    var h = document.getElementById("wb-held");
    var r = document.getElementById("wb-rejected");
    if (a) a.textContent = counts.accept;
    if (h) h.textContent = counts.hold;
    if (r) r.textContent = counts.reject;
  }}

  document.querySelectorAll(".sug-pick").forEach(function (b) {{
    b.addEventListener("click", function () {{
      var box = b.closest(".sug-controls");
      var id = box.getAttribute("data-id");
      var pick = b.getAttribute("data-pick");
      if (state[id] === pick) {{ delete state[id]; }} else {{ state[id] = pick; }}
      try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}}
      paint();
    }});
  }});

  var clear = document.getElementById("wb-clear");
  if (clear) {{
    clear.addEventListener("click", function (ev) {{
      ev.preventDefault();
      state = {{}};
      try {{ localStorage.removeItem(KEY); }} catch (e) {{}}
      paint();
    }});
  }}
  paint();
}})();
</script>
</body>
</html>
"""

for target in (os.path.join(ROOT, "site", "workbench.html"),
               os.path.join(ROOT, "workbench.html")):
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(body)
print("wrote site/workbench.html and workbench.html (%d bytes), %d items ranked"
      % (len(body), len(WB["items"])))
print("ranking: " + ", ".join("#%d %s %.2f" % (i["rank"], i["id"], i["score"]) for i in ranked))
