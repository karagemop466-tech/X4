/* X4 — builds the Source Register table from the source registry itself.
   Kept separate so the register has exactly one definition. */

(function () {
  const order = { primary: 0, academic: 1, secondary: 2 };
  const ids = Object.keys(window.X4_SOURCES).sort((a, b) => {
    const A = window.X4_SOURCES[a], B = window.X4_SOURCES[b];
    return (order[A.tier] - order[B.tier]) || A.publisher.localeCompare(B.publisher);
  });

  const rows = ids.map(id => {
    const s = window.X4_SOURCES[id];
    return {
      id: id,
      tier: s.tier,
      publisher: s.publisher,
      link: '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.label) + "</a>",
      confirms: s.confirms,
      retrieved: s.retrieved,
      src: { url: s.url, label: "link" },
      status: s.tier === "secondary" ? "secondary" : "verified",
    };
  });

  window.X4_SOURCE_STATS = {
    total: rows.length,
    primary: rows.filter(r => r.tier === "primary").length,
    academic: rows.filter(r => r.tier === "academic").length,
    secondary: rows.filter(r => r.tier === "secondary").length,
  };

  window.X4_TABLES = window.X4_TABLES || {};
  window.X4_TABLES.sourceRegister = {
    sortKey: "tier", sortDir: "asc",
    placeholder: "Filter by publisher, source or what it confirms…",
    facets: [
      { key: "tier", label: "Tier", options: ["primary", "academic", "secondary"] },
    ],
    cols: [
      { key: "id", label: "Key", nowrap: true },
      { key: "tier", label: "Tier", nowrap: true },
      { key: "publisher", label: "Publisher" },
      { key: "link", label: "Source" },
      { key: "confirms", label: "What it confirms" },
      { key: "retrieved", label: "Retrieved", nowrap: true },
      { key: "_status", label: "Status" },
      { key: "_src", label: "Link" },
    ],
    rows: rows,
  };
})();
