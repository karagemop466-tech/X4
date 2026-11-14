/* X4 — shared navigation + small helpers.
   Injected into every page so the site has exactly one nav definition. */

const X4_NAV = [
  { group: "Overview", items: [
    { href: "index.html",            title: "Dashboard" },
    { href: "executive-summary.html", title: "Executive Summary" },
    { href: "requirements.html",      title: "Requirements" },
  ]},
  { group: "Decision Support", items: [
    { href: "questions.html",   title: "Open Questions" },
    { href: "suggestions.html", title: "Suggestions (Review Queue)" },
    { href: "flagged.html",     title: "Flagged for Review" },
  ]},
  { group: "Signals & Strategies", items: [
    { href: "lines-market.html", title: "Line Origination & Market" },
    { href: "strategies.html",   title: "Strategy Catalog" },
    { href: "validation.html",   title: "Validation Gates" },
    { href: "correlation.html",  title: "Correlation Reference" },
    { href: "leaderboard.html",  title: "Leaderboard & Rewards" },
  ]},
  { group: "Data", items: [
    { href: "nfl-data.html",  title: "NFL Data (Verified)" },
    { href: "injuries.html",  title: "Injuries & Depth" },
    { href: "sources.html",   title: "Source Register" },
  ]},
];

(function () {
  const here = (location.pathname.split("/").pop() || "index.html");
  let html = '<div class="brand"><div class="mark">X4</div>'
           + '<div class="sub">NFL Signal &amp; Strategy Console</div></div><nav>';
  let active = null;
  X4_NAV.forEach(g => {
    html += '<div class="grp">' + g.group + '</div>';
    g.items.forEach(it => {
      const on = (it.href === here);
      if (on) active = it.title;
      html += '<a class="item' + (on ? ' active' : '') + '" href="' + it.href + '">' + it.title + '</a>';
    });
  });
  html += '</nav><div class="foot">Static site · no build step<br>'
        + 'Data verified against primary sources only.<br>'
        + 'Unconfirmed values are left blank and flagged.<br>'
        + '<a href="../index.html" style="color:#8fb4e0">&larr; Back to the main NFL Decision Desk</a></div>';
  document.getElementById("sidebar").innerHTML = html;

  const t = document.getElementById("pagetitle");
  if (t && !t.textContent.trim()) t.textContent = active || "X4";
  document.title = (active ? active + " · " : "") + "X4 — NFL Signal & Strategy Console";
})();

/* Fill any <span data-stat="X4_FOO_STATS.key"> with the live value from the data files,
   so headline counts on a page can never drift away from the tables underneath them. */
function fillStats() {
  document.querySelectorAll("[data-stat]").forEach(el => {
    const parts = el.getAttribute("data-stat").split(".");
    const v = parts.length === 2
      ? (window[parts[0]] ? window[parts[0]][parts[1]] : undefined)
      : window[parts[0]];
    el.textContent = (v === undefined || v === null) ? "—" : String(v);
  });
}
(function () {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fillStats);
  } else { fillStats(); }
})();

/* escape for safe HTML interpolation */
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/* Render one source cell. `s` may be a string URL or {url,label}. */
function srcCell(s) {
  if (!s) return '<td class="srclink"><span class="b grey">no source</span></td>';
  if (typeof s === "string") {
    return '<td class="srclink"><a href="' + esc(s) + '" target="_blank" rel="noreferrer">source</a></td>';
  }
  const label = s.label || "source";
  return '<td class="srclink"><a href="' + esc(s.url) + '" target="_blank" rel="noreferrer">' + esc(label) + '</a></td>';
}

/* Status badge vocabulary used across every table. */
function statusBadge(st) {
  const map = {
    verified:   ["ok",   "verified"],
    primary:    ["ok",   "verified"],
    secondary:  ["grey", "secondary"],
    unverified: ["bad",  "unverified"],
    unknown:    ["bad",  "unverified"],
    blank:      ["bad",  "unverified"],
    design:     ["info", "design"],
    proposed:   ["warn", "proposed"],
    pending:    ["warn", "pending"],
    blocked:    ["bad",  "blocked"],
    partial:    ["warn", "partial"],
    met:        ["ok",   "met"],
    open:       ["warn", "open"],
    answered:   ["ok",   "answered"],
    hypothesis: ["grey", "hypothesis"],
    rejected:   ["bad",  "rejected"],
  };
  const m = map[String(st || "").toLowerCase()] || ["grey", esc(st)];
  return '<span class="b ' + m[0] + '">' + m[1] + "</span>";
}
