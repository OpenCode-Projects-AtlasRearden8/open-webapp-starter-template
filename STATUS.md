# STATUS.md — Offline Web App Starter Template

Built 2026-10-26 by Asdale Dynamics, LLC (template by Dylan Asdale).
MIT licensed — see `LICENSE`.

## What was built

- **`template.html`** — a copy-ready, single-file offline web app shell:
  - localStorage helpers (`getJSON` / `setJSON` / `removeKey` / `storageAvailable`)
    guarded against corrupt data with fallbacks
  - schema migration helpers (`SCHEMA_VERSION`, `migrateSchema`, `loadState`,
    `saveState`, `resetState`) so old saved data upgrades transparently
  - an Export button (downloads timestamped JSON, no personal info) and a
    Reset button (confirm-guarded, returns to clean defaults)
  - a Settings panel pattern with `aria-expanded` toggling and storage-health
    status
  - an `@media print` stylesheet that strips chrome and prints clean data
  - an inline SVG data-URI favicon (no external requests — stays offline)
  - a worked demo module (counter list) showing the full state → persist →
    render loop, with first-run empty-state guidance
- **`tests/run_tests.py`** — offline test runner (pure Python stdlib + Node):
  - 12 structural checks on `template.html`, `LICENSE`, `README.md`
  - 12 logic checks that extract the JS helpers from `APP-TESTABLE` markers in
    `template.html` and run them in Node against a fake localStorage — no
    browser, no npm packages
  - 1 isolation check asserting the testable block never touches
    `document`/`window`
- **`docs/tutorial.md`** — step-by-step guide for adapting the template
- **`README.md`**, **`LICENSE`** (MIT, `Copyright (c) 2026 Asdale Dynamics, LLC`)

## How to run

- Use the template: open `template.html` in any browser (double-click, or
  `python3 -m http.server` if you prefer). It works offline.
- Run the tests: `python3 tests/run_tests.py` (needs Python 3 and Node.js).

## Verification results (2026-10-26)

- `python3 tests/run_tests.py` → **25 passed, 0 failed** —
  "ALL TESTS PASSED" (structural + Node logic + isolation checks)
- `node --check` on the full template `<script>` block → **syntax OK**
- `python3 -m py_compile tests/run_tests.py` → **OK**
- DOM smoke simulation (Node harness stubbing the DOM: load app, add item,
  increment, clamp at 0, simulated page reload from storage, settings toggle,
  export payload parse, reset) → **ALL OK**

## Known gaps

- The DOM smoke test is a throwaway harness in `/tmp`, not part of the repo
  tests (no DOM library is bundled to keep the template dependency-free);
  browser behavior was validated through the simulation plus code review.
- The migration story currently handles schema bump 1 → 2 with per-item
  normalisation; deeper multi-step migrations would be added to
  `migrateSchema()` as explicit version cases as the template evolves.
- No automated test covers the print rendering or visual layout; verify in a
  browser when restyling.
- The template is a *shell*: it is intended to be forked per project, so new
  apps should rename `STORAGE_KEY` to their own to avoid key collisions.
