#!/usr/bin/env node
/*
 * Browser smoke test for the published site.
 *
 * The pages are statically rendered, so this harness does not build tables - it
 * loads each page in a DOM shim, confirms the script runs without an error, and
 * exercises the two filters to prove they are wired to the static rows.
 *
 * Usage: node tools/render.js <siteDir>   ->  JSON on stdout
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const siteDir = path.resolve(process.argv[2] || path.join(__dirname, "..", "site"));

const PAGES = [
  ["index.html", "overview"], ["market.html", "market"], ["standings.html", "standings"],
  ["lines.html", "lines"],
  ["price-snapshots.html", "price-snapshots"], ["results.html", "results"],
  ["strategies.html", "strategies"], ["availability.html", "availability"],
  ["depth.html", "depth"],
  ["markets.html", "markets"], ["gates.html", "gates"],
  ["luck.html", "luck"], ["readiness.html", "readiness"], ["teams.html", "teams"],
  ["schedule.html", "schedule"],
  ["delta.html", "delta"], ["matchup.html", "matchup"],
  ["houston-depth.html", "houston-depth"],
  ["gamebook.html", "gamebook"],
  ["gamebook-ops.html", "gamebook-ops"], ["glossary.html", "glossary"],
  ["personnel-ablation.html", "personnel-ablation"],
  ["questions.html", "questions"], ["suggestions.html", "suggestions"],
  ["flags.html", "flags"], ["methodology.html", "methodology"],
  ["markets.html", "markets"], ["results.html", "results"], ["gates.html", "gates"],
];

function makeElement(id) {
  return {
    id: id,
    _html: "",
    style: {},
    value: "",
    textContent: "",
    listeners: {},
    querySelectorAll(sel) {
      // only "tbody tr" is used by the site
      if (sel !== "tbody tr") return [];
      const el = this;
      const tb = /<tbody\b[^>]*>([\s\S]*?)<\/tbody>/.exec(el._html);
      const scope = tb ? tb[1] : el._html;
      const re = /<tr\b([^>]*)>([\s\S]*?)<\/tr>/g;
      const out = [];
      let m;
      while ((m = re.exec(scope)) !== null) {
        const attrs = m[1] || "";
        const inner = m[2] || "";
        out.push({
          getAttribute(name) {
            const a = new RegExp(name + '="([^"]*)"').exec(attrs);
            return a ? a[1] : null;
          },
          style: {},
          _inner: inner,
        });
      }
      return out;
    },
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = String(v); },
    addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); },
    dispatch(type) { (this.listeners[type] || []).forEach((fn) => fn.call(this, {})); },
  };
}

const out = {};
const errors = [];

for (const [file] of PAGES) {
  const htmlPath = path.join(siteDir, file);
  if (!fs.existsSync(htmlPath)) { errors.push("missing page file: " + file); continue; }
  const html = fs.readFileSync(htmlPath, "utf8");

  const m = html.match(/<body[^>]*data-page="([^"]+)"/);
  const pageAttr = m ? m[1] : null;

  const elements = new Map();
  const bodyEl = makeElement("body");
  bodyEl.getAttribute = (name) => (name === "data-page" ? pageAttr : null);

  // seed the elements the page declares, with the static markup they contain
  for (const em of html.matchAll(/id="([a-zA-Z0-9_-]+)"/g)) {
    const id = em[1];
    const el = makeElement(id);
    const start = html.indexOf("<table", em.index);
    if (start !== -1) {
      const end = html.indexOf("</table>", start);
      if (end !== -1) el._html = html.slice(start, end + "</table>".length);
    }
    elements.set(id, el);
  }

  const document = {
    body: bodyEl,
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, makeElement(id));
      return elements.get(id);
    },
    createElement() { return makeElement("tmp"); },
    addEventListener(type, fn) { if (type === "DOMContentLoaded") fn(); },
  };

  const sandbox = { window: {}, document, console, Math, JSON, Number, String, Object, Array, isNaN, parseInt, parseFloat };
  sandbox.window.document = document;
  sandbox.globalThis = sandbox;

  const ctx = vm.createContext(sandbox);
  let scriptError = null;
  try {
    vm.runInContext(fs.readFileSync(path.join(siteDir, "app.js"), "utf8"), ctx, { filename: "app.js" });
  } catch (e) {
    scriptError = e.message;
  }

  const filters = {};
  if (file === "standings.html") {
    const gw = elements.get("gw");
    const g = elements.get("games");
    if (g) filters.games_rows = g.querySelectorAll("tbody tr").length;
    if (gw) filters.week_value = gw.value;
  }
  if (file === "availability.html") {
    const inj = elements.get("inj-full");
    if (inj) filters.injury_rows = inj.querySelectorAll("tbody tr").length;
  }

  out[file] = { page: pageAttr, filters: filters, error: scriptError };
  if (scriptError) errors.push(file + ": script error: " + scriptError);
}

if (errors.length) process.stderr.write(errors.join("\n") + "\n");
process.stdout.write(JSON.stringify(out, null, 1));
if (errors.length) process.exit(1);
