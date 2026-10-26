#!/usr/bin/env python3
"""Offline test runner for the Asdale web-app starter template.

Validation happens in two layers, with no browser and no packages:

1. Structural checks (pure Python) — confirm template.html, LICENSE, and
   README.md contain the pieces the template promises (favicon, print
   stylesheet, settings panel, reset/export buttons, empty state, MIT
   license line, LLC credit).

2. Logic checks (Python driving Node) — the JS helper block is extracted
   from between the APP-TESTABLE markers in template.html and evaluated
   in Node with a localStorage shim. Each scenario runs against a fresh
   fake storage so tests are order-independent.

Run:  python3 tests/run_tests.py
Exit: 0 = all pass, 1 = failure. Node is required for the logic checks.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template.html"
LICENSE = ROOT / "LICENSE"
README = ROOT / "README.md"

TA_COPYRIGHT = "Copyright (c) 2026 Asdale Dynamics, LLC"


# ---------------------------------------------------------------- structural --

def structural_checks():
    template = TEMPLATE.read_text(encoding="utf-8")
    license_text = LICENSE.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")

    def has(name, ok, detail):
        return {"name": name, "ok": bool(ok), "detail": detail}

    return [
        has("template starts with doctype", template.lstrip().lower().startswith("<!doctype html>"),
            "checks a valid HTML5 doc"),
        has("inline SVG favicon (data URI)", 'data:image/svg+xml' in template and 'rel="icon"' in template,
            "single-file app keeps its favicon inline"),
        has("print stylesheet present", re.search(r"@media\s+print", template) is not None,
            "@media print block should exist"),
        has("storage helpers present",
            all(name in template for name in
                ("function getJSON", "function setJSON", "function removeKey", "function storageAvailable")),
            "getJSON/setJSON/removeKey/storageAvailable"),
        has("schema migration present",
            "migrateSchema(" in template and "SCHEMA_VERSION" in template,
            "migrateSchema + SCHEMA_VERSION"),
        has("settings panel present", 'id="settings-panel"' in template and 'id="storage-status"' in template,
            "settings panel with storage status"),
        has("reset + export buttons present",
            'id="btn-reset"' in template and 'id="btn-export"' in template,
            "reset and export buttons in the header toolbar"),
        has("empty-state guidance present", 'id="empty-state"' in template,
            "first-run guidance element"),
        has("demo module present", 'id="counter-list"' in template and 'id="add-form"' in template,
            "worked counter-list demo"),
        has("responsive viewport meta",
            'name="viewport"' in template,
            "mobile-friendly viewport meta"),
        has("LICENSE copyright line exact", TA_COPYRIGHT in license_text,
            f"expects '{TA_COPYRIGHT}'"),
        has("README credits Asdale Dynamics, LLC", "Asdale Dynamics, LLC" in readme_text,
            "LLC credit in README"),
    ]


# --------------------------------------------------------------------- node --

def extract_testable_js():
    text = TEMPLATE.read_text(encoding="utf-8")
    match = re.search(
        r"/\*\s*APP-TESTABLE-BEGIN\s*\*/(.*?)/\*\s*APP-TESTABLE-END\s*\*/",
        text, re.DOTALL,
    )
    if not match:
        return None
    return match.group(1)


NODE_HARNESS = r"""
const fs = require("fs");

function makeFakeStorage() {
  const map = new Map();
  return {
    getItem: (k) => (map.has(k) ? map.get(k) : null),
    setItem: (k, v) => { map.set(k, String(v)); },
    removeItem: (k) => { map.delete(k); },
    clear: () => { map.clear(); },
    get _map() { return map; },
  };
}

/* APP HELPERS ARE EVALUATED HERE.
 * The leading "use strict" directive would confine the helper functions to
 * this one eval call; strip it so later scenario evals share the same scope. */
const helperSource = fs.readFileSync(process.argv[2], "utf8")
  .replace(/["']use strict["'];(\r?\n)?/, "");
eval(helperSource);

const scenarios = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const results = [];

for (const scenario of scenarios) {
  const fake = makeFakeStorage();
  globalThis.localStorage = fake;
  let outcome;
  try {
    /* The scenario body arrives as a string; build one real function per run
     * so each scenario is isolated from the previous scenario's closures. */
    const fn = eval("(" + scenario.run + ")");
    const detail = fn(fake);
    outcome = { name: scenario.name, ok: true, detail: detail === undefined ? "" : String(detail) };
  } catch (err) {
    outcome = { name: scenario.name, ok: false, detail: err && err.message ? err.message : String(err) };
  }
  results.push(outcome);
}

console.log(JSON.stringify(results, null, 2));
"""

# Each Python entry becomes a node-side scenario (fake = fresh fake storage).
SCENARIOS = [
    {
        "name": "storageAvailable reports fake storage as working",
        "run": "(fake) => storageAvailable() ? 'ok' : (() => { throw new Error('expected true'); })()",
    },
    {
        "name": "getJSON returns fallback when key is missing",
        "run": "() => JSON.stringify(getJSON('nope', {fallback: true})) === '{\"fallback\":true}' ? 'ok' : 'wrong result'",
    },
    {
        "name": "setJSON/getJSON round-trip",
        "run": "(fake) => { setJSON('k.r1', {a: [1, 2, 3], b: 'hi'}); const v = getJSON('k.r1', null); return v && v.a.length === 3 && v.b === 'hi' ? 'ok' : 'wrong result'; }",
    },
    {
        "name": "getJSON falls back on corrupt JSON without throwing",
        "run": "(fake) => { fake.setItem('broken', '{not valid json!!'); return getJSON('broken', 'safe') === 'safe' ? 'ok' : 'did not fall back'; }",
    },
    {
        "name": "migrateSchema maps null/missing state to empty default",
        "run": "() => { const s = migrateSchema(null); return s.schemaVersion === SCHEMA_VERSION && Array.isArray(s.items) && s.items.length === 0 ? 'ok' : 'unexpected shape'; }",
    },
    {
        "name": "migrateSchema lifts legacy v1 string items",
        "run": "() => { const s = migrateSchema({schemaVersion: 1, items: ['Milk', 'Bread']}); return s.schemaVersion === SCHEMA_VERSION && s.items.length === 2 && s.items[0].label === 'Milk' && s.items[0].count === 0 && s.items[0].id ? 'ok' : JSON.stringify(s); }",
    },
    {
        "name": "migrateSchema fills missing ids and clamps negative counts",
        "run": "() => { const s = migrateSchema({schemaVersion: 1, items: [{label: 'X', count: -5}, {id: 'keep', label: 'Y', count: '3'}]}); const i0 = s.items[0]; const i1 = s.items[1]; return (i0.id && i0.id !== 'keep' && i0.count === 0 && i1.id === 'keep' && i1.count === 3) ? 'ok' : JSON.stringify(s); }",
    },
    {
        "name": "migrateSchema is idempotent on current version",
        "run": "() => { const before = {schemaVersion: SCHEMA_VERSION, items: [{id: 'a1', label: 'Y', count: 7}]}; const after = migrateSchema(before); return before.items[0].id === after.items[0].id && before.items[0].label === after.items[0].label && before.items[0].count === after.items[0].count ? 'ok' : 'idempotency broken'; }",
    },
    {
        "name": "loadState reads + migrates from storage",
        "run": "(fake) => { fake.setItem(STORAGE_KEY, JSON.stringify({schemaVersion: 1, items: ['Leg 1']})); const s = loadState(); return s.items.length === 1 && s.items[0].label === 'Leg 1' ? 'ok' : JSON.stringify(s); }",
    },
    {
        "name": "saveState writes JSON and persists",
        "run": "(fake) => { const ok = saveState({schemaVersion: SCHEMA_VERSION, items: [{id: 'z', label: 'Z', count: 1}]}); return ok && JSON.parse(fake.getItem(STORAGE_KEY)).items.length === 1 ? 'ok' : 'saveState failed'; }",
    },
    {
        "name": "resetState clears storage and returns default",
        "run": "(fake) => { fake.setItem(STORAGE_KEY, '{\"schemaVersion\": \"1\", \"items\": [\"gone\"]}'); const s = resetState(); return fake.getItem(STORAGE_KEY) === null && s.items.length === 0 && s.schemaVersion === SCHEMA_VERSION ? 'ok' : 'reset incomplete'; }",
    },
    {
        "name": "buildExportPayload includes metadata, migrated data, no personal info",
        "run": "() => { const p = buildExportPayload({schemaVersion: 1, items: ['One']}); return p.app === APP_NAME && typeof p.exportedAt === 'string' && p.data.items.length === 1 && p.data.items[0].label === 'One' && p.app.indexOf('@') === -1 ? 'ok' : JSON.stringify(p); }",
    },
]


def node_logic_checks(js_source, temp_dir):
    helpers_path = temp_dir / "helpers.js"
    harness_path = temp_dir / "harness.js"
    scenarios_path = temp_dir / "scenarios.json"

    helpers_path.write_text(js_source, encoding="utf-8")
    harness_path.write_text(NODE_HARNESS, encoding="utf-8")

    node_scenarios = [{"name": s["name"], "run": s["run"]} for s in SCENARIOS]
    scenarios_path.write_text(json.dumps(node_scenarios), encoding="utf-8")

    completed = subprocess.run(
        ["node", str(harness_path), str(helpers_path), str(scenarios_path)],
        capture_output=True, text=True, timeout=60,
    )
    if completed.returncode != 0:
        return [{
            "name": "node harness ran",
            "ok": False,
            "detail": completed.stderr.strip() or completed.stdout.strip() or "node exited with error",
        }]
    try:
        results = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return [{
            "name": "node harness output parsed",
            "ok": False,
            "detail": completed.stdout.strip() or "no JSON on stdout",
        }]

    # Isolation guard: the testable block must not touch the DOM or window.
    dom_hits = re.findall(r"\b(document|window)\s*\.", js_source)
    if dom_hits:
        results.append({
            "name": "testable block stays DOM-free",
            "ok": False,
            "detail": "found DOM references in APP-TESTABLE block: " + ", ".join(dom_hits),
        })
    else:
        results.append({
            "name": "testable block stays DOM-free",
            "ok": True,
            "detail": "no document/window references in extracted helpers",
        })
    return results


# --------------------------------------------------------------------- main --

def main():
    missing = [str(p) for p in (TEMPLATE, LICENSE, README) if not p.exists()]
    if missing:
        print(f"FAIL: expected files are missing: {', '.join(missing)}", file=sys.stderr)
        return 1

    results = structural_checks()

    node = shutil.which("node")
    if node is None:
        results.append({
            "name": "node logic checks",
            "ok": False,
            "detail": "Node.js not found on PATH; install Node to run logic checks",
        })
    else:
        js_source = extract_testable_js()
        if js_source is None:
            results.append({
                "name": "APP-TESTABLE markers found",
                "ok": False,
                "detail": "could not find /* APP-TESTABLE-BEGIN */ ... /* APP-TESTABLE-END */ in template.html",
            })
        else:
            with TemporaryDirectory() as tmp:
                results.extend(node_logic_checks(js_source, Path(tmp)))

    failed = [r for r in results if not r["ok"]]
    passed = [r for r in results if r["ok"]]

    print()
    for r in results:
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"  [{mark}] {r['name']}")
        if r["detail"]:
            print(f"          {r['detail']}")
    print()
    print(f"  {len(passed)} passed, {len(failed)} failed, {len(results)} total")

    if failed:
        print("TESTS FAILED", file=sys.stderr)
        return 1
    print("ALL TESTS PASSED")
    return 0



if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
