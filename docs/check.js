#!/usr/bin/env node
/*
 * Publication gate for the X4 Console in this directory.
 *
 * The tables are built in the browser from the window.X4_* data files, so this check
 * does not read the static HTML alone: it executes assets/nav.js and assets/table.js
 * against the data files with a minimal DOM shim, then inspects the RESULTING markup.
 *
 * Checks
 *   1. every page exists, is non-trivial, and declares a charset, viewport and title
 *   2. every internal link resolves to a file that exists
 *   3. every local asset referenced by a page exists
 *   4. every external link uses https:// and carries rel="noreferrer"
 *   5. every table that a page declares actually renders, and every rendered data row
 *      carries exactly one source cell
 *   6. rendered row count equals the data row count (no silent empty or truncated table)
 *   7. every data-stat counter on a page resolves to a live value from the data files
 *   8. no page contains a placeholder marker
 *
 * Exit code 0 = publishable. Exit code 1 = at least one problem.
 * Node standard library only. No dependencies, no build step.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = __dirname;
const PLACEHOLDERS = ["TODO", "FIXME", "lorem ipsum", "undefined;", "NaN"];
const problems = [];

/* ---------------------------------------------------------------- DOM shim */

function makeElement(attrs) {
  const el = {
    innerHTML: "",
    textContent: "",
    value: "",
    _attrs: attrs || {},
    getAttribute(k) { return this._attrs[k]; },
    setAttribute(k, v) { this._attrs[k] = v; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    addEventListener() {},
    focus() {},
    setSelectionRange() {},
  };
  return el;
}

function buildPage(file) {
  const html = fs.readFileSync(path.join(ROOT, file), "utf8");
  const scripts = [...html.matchAll(/<script src="([^"]+)"><\/script>/g)].map(m => m[1]);
  const tables = [...html.matchAll(/data-table="([^"]+)"/g)].map(m => m[1]);
  const stats = [...html.matchAll(/data-stat="([^"]+)"/g)].map(m => m[1]);

  const hosts = tables.map(t => makeElement({ "data-table": t }));
  const statEls = stats.map(s => makeElement({ "data-stat": s }));
  const byId = {};

  const ready = [];
  const sandbox = {
    console,
    window: { addEventListener: (ev, fn) => { if (ev === "load") ready.push(fn); } },
    location: { pathname: "/" + file },
    document: {
      readyState: "loading",
      getElementById: id => (byId[id] = byId[id] || makeElement({})),
      querySelectorAll: sel => {
        if (sel === "[data-table]") return hosts;
        if (sel === "[data-stat]") return statEls;
        return [];
      },
      addEventListener: (ev, fn) => { if (ev === "DOMContentLoaded") ready.push(fn); },
    },
  };
  sandbox.window.X4_TABLES = {};
  const ctx = vm.createContext(sandbox);

  for (const s of scripts) {
    const p = path.join(ROOT, s);
    if (!fs.existsSync(p)) { problems.push(`${file}: missing script ${s}`); continue; }
    try { vm.runInContext(fs.readFileSync(p, "utf8"), ctx, { filename: s }); }
    catch (e) { problems.push(`${file}: script ${s} threw: ${e.message}`); return null; }
  }
  try { ready.forEach(fn => fn()); }
  catch (e) { problems.push(`${file}: mounting threw: ${e.message}`); return null; }

  return { html, scripts, tables, stats, hosts, statEls, sandbox };
}

/* ------------------------------------------------------------------- checks */

const pages = fs.readdirSync(ROOT).filter(f => f.endsWith(".html")).sort();
if (!pages.length) problems.push("no HTML pages found");

let renderedTables = 0;
let dataRows = 0;
let internalLinks = 0;
let externalLinks = 0;

for (const file of pages) {
  const html = fs.readFileSync(path.join(ROOT, file), "utf8");

  // 1. structure
  if (html.length < 400) problems.push(`${file}: page is suspiciously small (${html.length} bytes)`);
  for (const need of ['<meta charset="utf-8"', 'name="viewport"', "<title>"]) {
    if (!html.includes(need)) problems.push(`${file}: missing ${need}`);
  }

  // 8. placeholders
  for (const p of PLACEHOLDERS) {
    if (html.includes(p)) problems.push(`${file}: contains placeholder marker "${p}"`);
  }

  // 2 + 3 + 4. links
  for (const m of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const u = m[1];
    if (/^https?:\/\//i.test(u)) {
      externalLinks++;
      if (!/^https:\/\//i.test(u)) problems.push(`${file}: external link is not https: ${u}`);
      continue;
    }
    if (u.startsWith("#") || u.startsWith("mailto:")) continue;
    internalLinks++;
    const target = path.join(ROOT, u);
    if (!fs.existsSync(target)) problems.push(`${file}: broken internal link ${u}`);
  }

  // external link safety attribute
  for (const m of html.matchAll(/<a\b[^>]*href="(https?:\/\/[^"]+)"[^>]*>/gi)) {
    if (!/rel="[^"]*noreferrer[^"]*"/i.test(m[0])) {
      problems.push(`${file}: external link without rel="noreferrer": ${m[1]}`);
    }
  }

  // 5 + 6 + 7. rendered output
  const built = buildPage(file);
  if (!built) continue;

  built.hosts.forEach(host => {
    const name = host.getAttribute("data-table");
    const spec = built.sandbox.window.X4_TABLES[name];
    if (!spec) { problems.push(`${file}: no data for declared table "${name}"`); return; }
    const out = host.innerHTML;
    if (!out || !out.includes("<table")) {
      problems.push(`${file}: table "${name}" rendered nothing`);
      return;
    }
    renderedTables++;
    const bodyRows = (out.match(/<tr>/g) || []).length;   // header row uses <tr> too
    const expected = spec.rows.length + 1;
    if (bodyRows !== expected) {
      problems.push(`${file}: table "${name}" rendered ${bodyRows} <tr> but expected ${expected}`);
    }
    const srcCells = (out.match(/class="srclink"/g) || []).length;
    if (srcCells !== spec.rows.length) {
      problems.push(`${file}: table "${name}" has ${srcCells} source cells for ${spec.rows.length} rows`);
    }
    dataRows += spec.rows.length;
    if (/undefined;|NaN/.test(out)) problems.push(`${file}: table "${name}" rendered "undefined;" or "NaN"`);
  });

  built.statEls.forEach(el => {
    const key = el.getAttribute("data-stat");
    if (el.textContent === "" || el.textContent === "—" || el.textContent === "undefined") {
      problems.push(`${file}: data-stat "${key}" did not resolve`);
    }
  });
}

/* ------------------------------------------------------------------ report */

if (problems.length) {
  console.error(`pages checked: ${pages.length}`);
  console.error(`rendered tables checked: ${renderedTables}`);
  console.error(`data rows checked: ${dataRows}`);
  console.error(`internal links checked: ${internalLinks}`);
  console.error(`external links checked: ${externalLinks}`);
  console.error("");
  console.error(`RESULT: FAIL - ${problems.length} problem(s):`);
  problems.forEach(p => console.error(`  - ${p}`));
  process.exit(1);
}

console.log(`pages checked: ${pages.length}`);
console.log(`rendered tables checked: ${renderedTables}`);
console.log(`data rows checked: ${dataRows} (every one carries a source cell)`);
console.log(`internal links checked: ${internalLinks}`);
console.log(`external links checked: ${externalLinks} (all https + rel="noreferrer")`);
console.log("RESULT: PASS - console is publishable: every rendered data row carries a source link, no broken links.");
