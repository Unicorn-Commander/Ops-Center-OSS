#!/usr/bin/env node
/**
 * CI gate: nav/route consistency between src/config/routes.js and src/App.jsx.
 *
 * routes.js is the single source of truth for the navigation menu; App.jsx is
 * the actual react-router <Route> table. They are maintained by hand in two
 * places, so this script asserts they cannot drift apart silently:
 *
 *   1. Every non-external route entry in routes.js has a matching <Route path>
 *      in App.jsx (normalizing the /admin/* nested-Routes prefix).
 *   2. Every redirect `from` in routes.redirects is actually implemented in
 *      App.jsx — either as a <Navigate>/<ParamRedirect> pointing at the same
 *      `to`, or as an alias route that renders the destination's component
 *      directly (equivalent content; flagged as a warning because the URL
 *      won't canonicalize).
 *   3. No nav-visible entry lacks a name/component (broken menu items).
 *   4. getAllRoutes() includes the personal section — regression guard for the
 *      2026-07 flattenRoutes bug where routes.personal (a namespace object
 *      without a `children` map) was invisible to getAllRoutes(), so personal
 *      pages never resolved titles/metadata.
 *
 * Runs with node builtins only (no npm install needed):
 *   node scripts/ci/check_nav_consistency.mjs
 *
 * Exits non-zero with a list of failures; warnings are informational.
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const routesPath = path.join(repoRoot, 'src', 'config', 'routes.js');
const appPath = path.join(repoRoot, 'src', 'App.jsx');

const failures = [];
const warnings = [];

// ---------------------------------------------------------------------------
// Load routes.js (plain ESM data module — package.json has "type": "module")
// ---------------------------------------------------------------------------
const mod = await import(pathToFileURL(routesPath).href);
const routes = mod.routes ?? mod.default;
const { getAllRoutes, getRedirects } = mod;

if (!routes || typeof routes !== 'object') {
  console.error('FATAL: could not load `routes` from src/config/routes.js');
  process.exit(2);
}
if (typeof getAllRoutes !== 'function' || typeof getRedirects !== 'function') {
  console.error('FATAL: routes.js no longer exports getAllRoutes()/getRedirects()');
  process.exit(2);
}

const normalize = (p) =>
  p && p.length > 1 && p.endsWith('/') ? p.slice(0, -1) : p;

const isExternal = (entry) =>
  entry.external === true || /^https?:\/\//.test(entry.path || '');

/**
 * Collect every path-bearing route entry. Mirrors flattenRoutes() semantics in
 * routes.js (entries may hang directly off a namespace object like
 * routes.personal, or under a section's `children` map) — but implemented
 * independently so a regression in flattenRoutes() is caught by check 4 rather
 * than silently shared.
 */
function collectEntries(node, acc = []) {
  if (!node || typeof node !== 'object' || Array.isArray(node)) return acc;
  if (typeof node.path === 'string') acc.push(node);
  if (node.children && typeof node.children === 'object') {
    Object.values(node.children).forEach((child) => collectEntries(child, acc));
  } else if (typeof node.path !== 'string') {
    Object.values(node).forEach((child) => collectEntries(child, acc));
  }
  return acc;
}

// ---------------------------------------------------------------------------
// Parse the <Route> table out of App.jsx
// ---------------------------------------------------------------------------
const app = readFileSync(appPath, 'utf8');

// Locate the nested admin <Routes> block: <Route path="/admin/*" ...> wraps an
// inner <Routes> whose child paths are RELATIVE to /admin.
const shellIdx = app.indexOf('path="/admin/*"');
if (shellIdx === -1) {
  console.error('FATAL: App.jsx no longer has a <Route path="/admin/*"> shell — update this checker.');
  process.exit(2);
}
const innerOpen = app.indexOf('<Routes>', shellIdx);
const innerClose = app.indexOf('</Routes>', innerOpen);
if (innerOpen === -1 || innerClose === -1) {
  console.error('FATAL: could not locate the nested <Routes> block inside the /admin/* shell.');
  process.exit(2);
}
if (app.slice(innerOpen + '<Routes>'.length, innerClose).includes('<Routes')) {
  console.error('FATAL: App.jsx now nests <Routes> more than one level deep — update this checker.');
  process.exit(2);
}

// Collect every <Route path="..."> with the source chunk up to the next Route,
// so we can inspect its element (Navigate / ParamRedirect / component).
const routeRe = /<Route\s+path="([^"]+)"/g;
const rawMatches = [];
let m;
while ((m = routeRe.exec(app)) !== null) {
  rawMatches.push({ raw: m[1], idx: m.index });
}

const appRoutes = rawMatches.map((r, i) => {
  const end = i + 1 < rawMatches.length ? rawMatches[i + 1].idx : app.length;
  const chunk = app.slice(r.idx, end);
  const nested = r.idx > innerOpen && r.idx < innerClose;
  let abs;
  if (nested) {
    abs = r.raw === '/' ? '/admin' : r.raw.startsWith('/') ? `/admin${r.raw}` : `/admin/${r.raw}`;
  } else {
    abs = r.raw;
  }
  const elMatch = chunk.match(/element=\{\s*<([A-Za-z_$][\w$]*)/);
  const toMatch = chunk.match(/\bto="([^"]+)"/);
  return {
    raw: r.raw,
    abs: normalize(abs),
    nested,
    component: elMatch ? elMatch[1] : null,
    to: toMatch ? normalize(toMatch[1]) : null,
  };
});

// First declaration wins (matches react-router matching order for duplicates).
const byAbs = new Map();
for (const r of appRoutes) {
  if (!byAbs.has(r.abs)) byAbs.set(r.abs, r);
}

// Parse-collapse sanity floors: if either side shrinks drastically the parser
// (or the config) broke — fail loudly instead of vacuously passing.
if (appRoutes.length < 60) {
  failures.push(`App.jsx parse collapsed: only ${appRoutes.length} <Route path> entries found (expected 100+)`);
}

const entries = [
  ...collectEntries(routes.personal),
  ...collectEntries(routes.organization),
  ...collectEntries(routes.system),
];
if (entries.length < 60) {
  failures.push(`routes.js traversal collapsed: only ${entries.length} route entries found (expected 100+)`);
}

// ---------------------------------------------------------------------------
// Check 1 — every non-external routes.js entry has a matching <Route> in App.jsx
// ---------------------------------------------------------------------------
let covered = 0;
for (const e of entries) {
  if (isExternal(e)) continue;
  const want = normalize(e.path);
  if (byAbs.has(want)) {
    covered += 1;
  } else {
    failures.push(`routes.js path "${e.path}" (${e.name || 'unnamed'}) has no matching <Route> in App.jsx`);
  }
}

// ---------------------------------------------------------------------------
// Check 2 — every redirect `from` is implemented in App.jsx
// ---------------------------------------------------------------------------
const redirects = getRedirects() || [];
if (redirects.length === 0) {
  warnings.push('routes.redirects is empty — nothing to verify');
}
for (const r of redirects) {
  const from = normalize(r.from);
  const to = normalize(r.to);
  const route = byAbs.get(from);
  if (!route) {
    failures.push(`redirect from "${r.from}" -> "${r.to}" has no <Route> in App.jsx at all`);
    continue;
  }
  if (route.component === 'Navigate' || route.component === 'ParamRedirect') {
    if (route.to !== to) {
      failures.push(`redirect "${r.from}": App.jsx navigates to "${route.to}" but routes.js says "${r.to}"`);
    }
  } else {
    // Alias route: old path renders a component directly. Acceptable only if
    // it renders the SAME component as the destination path (equivalent
    // content, URL just doesn't canonicalize).
    const target = byAbs.get(to);
    if (!target || !route.component || route.component !== target.component) {
      failures.push(
        `redirect from "${r.from}" is neither <Navigate>/<ParamRedirect> nor an alias of "${r.to}" ` +
          `(from renders <${route.component ?? '?'}>, destination renders <${target?.component ?? 'MISSING ROUTE'}>)`
      );
    } else {
      warnings.push(
        `redirect "${r.from}" is an alias (renders <${route.component}> in place); URL won't canonicalize to "${r.to}"`
      );
    }
  }
}

// Reverse direction (documentation drift, warn-only): nested App.jsx redirect
// routes that aren't recorded in routes.redirects. The redirects table is
// documentation — App.jsx is the implementation — so this doesn't fail CI.
const documentedFroms = new Set(redirects.map((r) => normalize(r.from)));
for (const route of appRoutes) {
  if (!route.nested) continue;
  if (route.component !== 'Navigate' && route.component !== 'ParamRedirect') continue;
  if (!documentedFroms.has(route.abs)) {
    warnings.push(`App.jsx redirect "${route.abs}" -> "${route.to}" is not documented in routes.redirects`);
  }
}

// ---------------------------------------------------------------------------
// Check 3 — nav-visible entries must have a name and a component
// ---------------------------------------------------------------------------
for (const e of entries) {
  if (e.nav === false) continue;
  if (!e.name) {
    failures.push(`nav-visible route "${e.path}" has no name (would render a blank menu item)`);
  }
  if (!isExternal(e) && !e.component) {
    failures.push(`nav-visible route "${e.path}" (${e.name || 'unnamed'}) has no component`);
  }
}

// ---------------------------------------------------------------------------
// Check 4 — getAllRoutes() includes the personal section (flattenRoutes guard)
// ---------------------------------------------------------------------------
const allPaths = new Set(getAllRoutes().map((r) => normalize(r.path)));
const personalEntries = collectEntries(routes.personal).filter((e) => !isExternal(e));
if (personalEntries.length === 0) {
  failures.push('collected zero personal entries from routes.personal — traversal or config broken');
}
for (const e of personalEntries) {
  if (!allPaths.has(normalize(e.path))) {
    failures.push(
      `getAllRoutes() is missing personal route "${e.path}" — flattenRoutes() regression (personal section invisible again)`
    );
  }
}
// Explicit sentinel for the exact page the original bug broke first.
if (!allPaths.has('/admin/account/profile')) {
  failures.push('getAllRoutes() sentinel missing: /admin/account/profile not returned');
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
for (const w of warnings) console.log(`WARN: ${w}`);

if (failures.length > 0) {
  console.error('\nNav consistency check FAILED:');
  for (const f of failures) console.error(`  FAIL: ${f}`);
  console.error(`\n${failures.length} failure(s). Fix src/config/routes.js and/or src/App.jsx so they agree.`);
  process.exit(1);
}

console.log(
  `\nNav consistency OK: ${covered} routes.js entries matched in App.jsx, ` +
    `${redirects.length} redirects verified, ${personalEntries.length} personal routes present in getAllRoutes() ` +
    `(${appRoutes.length} <Route> declarations scanned, ${warnings.length} warning(s)).`
);
