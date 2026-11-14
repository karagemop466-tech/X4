/* NFL Decision Desk - progressive enhancement only.
 *
 * Every table on this site is written into the HTML at build time from
 * data/output/payload.json (see tools/pages.py). Nothing here creates a value.
 * This script only adds two conveniences on top of the static page:
 *
 *   1. a week filter on the game log
 *   2. team and status filters on the full injury report
 *
 * Both work by hiding rows that carry a data attribute. If JavaScript is off,
 * the page still shows every row - just unfiltered.
 */
(function () {
  "use strict";

  function rowsFor(containerId) {
    var el = document.getElementById(containerId);
    if (!el) return [];
    return Array.prototype.slice.call(el.querySelectorAll("tbody tr"));
  }

  function setupWeekFilter() {
    var sel = document.getElementById("gw");
    if (!sel) return;
    var rows = rowsFor("games");
    var count = document.getElementById("gw-count");

    function apply() {
      var v = sel.value;
      var shown = 0;
      rows.forEach(function (tr) {
        var match = !v || tr.getAttribute("data-week") === v;
        tr.style.display = match ? "" : "none";
        if (match) shown++;
      });
      if (count) {
        count.textContent = shown + (shown === 1 ? " game shown" : " games shown");
      }
    }
    sel.addEventListener("change", apply);
    apply();
  }

  function setupInjuryFilters() {
    var teamSel = document.getElementById("it");
    var statusSel = document.getElementById("is");
    if (!teamSel && !statusSel) return;
    var rows = rowsFor("inj-full");
    var count = document.getElementById("is-count");

    function apply() {
      var t = teamSel ? teamSel.value : "";
      var s = statusSel ? statusSel.value : "";
      var shown = 0;
      rows.forEach(function (tr) {
        var okT = !t || tr.getAttribute("data-team") === t;
        var okS = !s || tr.getAttribute("data-status") === s;
        var match = okT && okS;
        tr.style.display = match ? "" : "none";
        if (match) shown++;
      });
      if (count) {
        count.textContent = shown + (shown === 1 ? " player shown" : " players shown");
      }
    }
    if (teamSel) teamSel.addEventListener("change", apply);
    if (statusSel) statusSel.addEventListener("change", apply);
    apply();
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      setupWeekFilter();
      setupInjuryFilters();
    } catch (e) {
      var b = document.getElementById("render-error");
      if (b) { b.style.display = "block"; b.textContent = "Filter error: " + e.message; }
    }
  });
})();
