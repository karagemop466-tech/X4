#!/usr/bin/env node
/*
 * Render the site with a minimal DOM shim and dump the resulting HTML per element.
 *
 * The tables on this site are built in the browser from window.X4, so a static
 * HTML check would inspect empty placeholders. This harness actually executes
 * site/app.js against site/data.js for every page and emits the rendered
 * markup, which site/check.py then inspects row by row.
 *
 * Usage: node tools/render.js <siteDir>   ->  JSON on stdout
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const siteDir = path.resolve(process.argv[2] || path.join(__dirname, "..", "site"));

const PAGES = [
  ["index.html", "overview"], ["standings.html", "standings"], ["lines.html", "lines"],
  ["strategies.html", "strategies"], ["availability.html", "availability"],
  ["questions.html", "questions"], ["suggestions.html", "suggestions"],
  ["flags.html", "flags"], ["methodology.html", "methodology"],
];

function makeElement(id) {
  const el = {
    id: id,
    _html: "",
    style: {},
    value: "",
    textContent: "",
    listeners: {},
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = String(v); },
    addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); },
    dispatch(type) { (this.listeners[type] || []).forEach((fn) => fn.call(this, {})); },
  };
  return el;
}

const out = {};
const errors = [];

for (const [file, page] of PAGES) {
  const htmlPath = path.join(siteDir, file);
  if (!fs.existsSync(htmlPath)) { errors.push("missing page file: " + file); continue; }
  const html = fs.readFileSync(htmlPath, "utf8");

  const m = html.match(/<body[^>]*data-page="([^"]+)"/);
  const pageAttr = m ? m[1] : null;

  const elements = new Map();
  const bodyEl = makeElement("body");
  bodyEl.getAttribute = (name) => (name === "data-page" ? pageAttr : null);

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
  try {
    vm.runInContext(fs.readFileSync(path.join(siteDir, "data.js"), "utf8"), ctx, { filename: "data.js" });
    vm.runInContext(fs.readFileSync(path.join(siteDir, "app.js"), "utf8"), ctx, { filename: "app.js" });
  } catch (e) {
    errors.push(file + ": script error: " + e.message);
  }

  const rendered = {};
  for (const [id, el] of elements.entries()) {
    if (el._html && el._html.length > 0) rendered[id] = el._html;
  }
  out[file] = { page: pageAttr, elements: rendered };
}

if (errors.length) { process.stderr.write(errors.join("\n") + "\n"); }
process.stdout.write(JSON.stringify(out, null, 1));
if (errors.length) process.exit(1);
