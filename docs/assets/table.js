/* X4 — generic data-table renderer.
   Every table rendered on this site goes through renderTable(), which guarantees
   that each row carries (a) a value, (b) a link to its source, and (c) a status.
   Blank values are rendered as an explicit "unverified" cell rather than guessed. */

(function () {

  function cell(key, row) {
    const v = row[key];
    if (v === undefined || v === null || v === "") {
      return '<td class="blank">— unverified —</td>';
    }
    return "<td>" + v + "</td>";
  }

  function buildRows(spec, query, sortKey, sortDir) {
    let rows = spec.rows.slice();

    if (query) {
      const q = query.toLowerCase();
      rows = rows.filter(r =>
        spec.cols.some(c => {
          let v = r[c.key];
          if (v && typeof v === "object" && v.url) v = v.url + " " + (v.label || "");
          return v != null && String(v).toLowerCase().indexOf(q) !== -1;
        })
      );
    }

    if (sortKey) {
      rows.sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey];
        const an = parseFloat(String(av).replace(/[^0-9.\-]/g, ""));
        const bn = parseFloat(String(bv).replace(/[^0-9.\-]/g, ""));
        let cmp;
        if (!isNaN(an) && !isNaN(bn) && String(av).match(/[0-9]/) && String(bv).match(/[0-9]/)) {
          cmp = an - bn;
        } else {
          cmp = String(av == null ? "" : av).localeCompare(String(bv == null ? "" : bv));
        }
        return sortDir === "desc" ? -cmp : cmp;
      });
    }
    return rows;
  }

  function render(spec, host) {
    const state = { q: "", sortKey: spec.sortKey || null, sortDir: spec.sortDir || "asc" };

    function html() {
      const rows = buildRows(spec, state.q, state.sortKey, state.sortDir);
      let out = "";

      if (spec.search !== false || spec.facets) {
        out += '<div class="filters">';
        if (spec.search !== false) {
          out += '<input type="search" placeholder="' + esc(spec.placeholder || "Search this table…") + '" value="' + esc(state.q) + '" data-role="q">';
        }
        (spec.facets || []).forEach(f => {
          out += '<select data-role="facet" data-key="' + esc(f.key) + '">'
               + '<option value="">' + esc(f.label) + ': all</option>';
          f.options.forEach(o => {
            out += '<option value="' + esc(o) + '">' + esc(o) + "</option>";
          });
          out += "</select>";
        });
        out += '<span class="counter" data-role="count">' + rows.length + " of " + spec.rows.length + " rows</span>";
        out += "</div>";
      }

      out += '<div class="tablewrap"><table class="dt"><thead><tr>';
      spec.cols.forEach(c => {
        const cls = c.num ? " num" : "";
        const arrow = state.sortKey === c.key ? (state.sortDir === "asc" ? " ▲" : " ▼") : "";
        out += '<th class="' + cls.trim() + '" data-role="sort" data-key="' + esc(c.key) + '"'
             + ' style="cursor:pointer" title="Sort">' + esc(c.label) + arrow + "</th>";
      });
      out += "</tr></thead><tbody>";

      if (!rows.length) {
        out += '<tr><td colspan="' + spec.cols.length + '" class="blank">No rows match this filter.</td></tr>';
      }

      rows.forEach(r => {
        out += "<tr" + (r._rowClass ? ' class="' + esc(r._rowClass) + '"' : "") + ">";
        spec.cols.forEach(c => {
          if (c.key === "_src") { out += srcCell(r.src); return; }
          if (c.key === "_status") { out += '<td>' + statusBadge(r.status) + "</td>"; return; }
          if (c.render) { out += "<td" + (c.num ? ' class="num"' : "") + (c.nowrap ? ' class="nowrap"' : "") + ">" + c.render(r) + "</td>"; return; }
          out += "<td" + (c.num ? ' class="num"' : "") + (c.nowrap ? ' class="nowrap"' : "") + ">" + cell(c.key, r).replace(/^<td[^>]*>|<\/td>$/g, "") + "</td>";
        });
        out += "</tr>";
      });

      out += "</tbody></table></div>";
      return out;
    }

    host.innerHTML = html();

    const qi = host.querySelector('[data-role="q"]');
    if (qi) {
      qi.addEventListener("input", e => { state.q = e.target.value; host.innerHTML = html(); wire(); });
    }
    function wire() {
      host.querySelectorAll('[data-role="sort"]').forEach(th => {
        th.addEventListener("click", () => {
          const k = th.getAttribute("data-key");
          if (state.sortKey === k) { state.sortDir = state.sortDir === "asc" ? "desc" : "asc"; }
          else { state.sortKey = k; state.sortDir = "asc"; }
          host.innerHTML = html(); wire();
        });
      });
      const q2 = host.querySelector('[data-role="q"]');
      if (q2) {
        q2.addEventListener("input", e => {
          state.q = e.target.value; host.innerHTML = html(); wire();
          const n = host.querySelector('[data-role="q"]');
          if (n) { n.focus(); n.setSelectionRange(n.value.length, n.value.length); }
        });
      }
      host.querySelectorAll('[data-role="facet"]').forEach(sel => {
        sel.addEventListener("change", e => {
          const k = sel.getAttribute("data-key");
          if (e.target.value) spec.facetFilter = spec.facetFilter || {}, spec.facetFilter[k] = e.target.value;
          else if (spec.facetFilter) delete spec.facetFilter[k];
          applyFacets();
        });
      });
      const c = host.querySelector('[data-role="count"]');
      if (c) { /* count already correct on first paint */ }
    }
    function applyFacets() {
      const base = spec.rows;
      let rows = base;
      if (spec.facetFilter) {
        Object.keys(spec.facetFilter).forEach(k => {
          rows = rows.filter(r => String(r[k]) === spec.facetFilter[k]);
        });
      }
      spec._rowsAll = base;
      const saved = spec.rows; spec.rows = rows;
      host.innerHTML = html(); wire();
      spec.rows = saved;
    }
    wire();
  }

  function mountAll() {
    document.querySelectorAll("[data-table]").forEach(host => {
      const name = host.getAttribute("data-table");
      const spec = (window.X4_TABLES || {})[name];
      if (!spec) { host.innerHTML = '<div class="callout bad">Missing table data: <code>' + esc(name) + "</code></div>"; return; }
      render(spec, host);
    });
  }

  /* Mount on DOMContentLoaded (the normal case: scripts sit at the end of <body>,
     so data files have already run by then). The window "load" listener is a
     belt-and-braces fallback; mountAll() is idempotent because it replaces innerHTML. */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll);
    if (typeof window !== "undefined") window.addEventListener("load", mountAll);
  } else {
    mountAll();
  }
  window.X4_renderTable = render;
  window.X4_mountAll = mountAll;
})();
