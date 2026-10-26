# Tutorial: make your own offline app from this template

This template exists so that starting a small, useful, offline web app takes
five minutes instead of an afternoon of boilerplate. Follow it in order — each
step is short on purpose.

## 0. First, the mindset

Everything you build from this shell has three rules:

- **One file.** HTML, CSS, and JS all live in `template.html`. You can email it,
  put it on a USB stick, or drop it on GitHub Pages. There is no build step.
- **Local only.** All data is saved in your browser's localStorage using the
  helpers in this template. Nothing is ever sent to a server — the file makes
  no network requests at all.
- **Safe by default.** The template's helpers never trust the data they read
  back. If storage is corrupt, the app falls back to clean defaults instead of
  crashing or leaking stale data.

## 1. Copy and rename

1. Copy `template.html` into a new folder and rename it — usually `index.html`.
2. Update `<title>`, the `<h1>`, and the footer text to name your app.
3. Open it in your browser. The demo counter list works immediately: add items,
   increase and decrease counts, close the tab, reopen — everything is still
   there because localStorage saved it.

That's it, you have a working offline app. The rest of this tutorial shows you
what to change and what to leave alone.

## 2. The four parts of the file (and what you may touch)

| Part | Marker | May I edit it? |
| --- | --- | --- |
| `<head>` — meta, favicon, CSS | | Yes — restyle freely; keep `@media print`. |
| Layout — header, settings, main | | Yes — settings panel keeps its IDs. |
| Storage & migration helpers | `APP-TESTABLE-BEGIN` … `APP-TESTABLE-END` | Usually no helpers to change; call them instead. |
| Demo module wiring | everything after the end marker | Replace with your module. |

The test runner extracts the block between the `APP-TESTABLE` markers and runs
its logic under Node, so anything inside must stay pure: no `document`, no
`window`. Buttons, forms, and event listeners belong outside the markers.

## 3. Replace the demo module with your idea

The demo is a counter list — a tiny model + UI + persistence loop:

- **Model**: `state = { schemaVersion, items: [{ id, label, count }] }`
- **Update**: pure-ish changes to `state`, then `saveState(state)`
- **Render**: `render()` rebuilds the list from `state` — always render from
  state, never edit the DOM "alongside" the data.

Common swaps:

- **Checklist**: replace `count` with a `done` boolean, style completed rows.
- **Log/note keeper**: store typed text, render chronologically.
- **Spend/budget tracker**: add a number input for amounts, sum in summary.

Text safety notice: the render code always inserts labels with
`textContent`, never `innerHTML`. Keep it that way so user-typed text can never
inject markup.

## 4. Storage discipline (the part that protects people's data)

Three helpers do all the talking to localStorage:

- `getJSON(key, fallback)` — read JSON with a safe fallback
- `setJSON(key, value)` — write JSON, report success/failure
- `removeKey(key)` — delete a key

And three app-level ones built on those:

- `loadState()` — read, **migrate**, return the state
- `saveState(state)` — persist, exporting failures back to the UI
- `resetState()` — wipe the app's key, return a fresh default

### When your saved-data shape changes, bump the schema

Suppose v2 of your app needs each item to gain a `note` field. Do this:

1. Raise `SCHEMA_VERSION` (e.g. `2` → `3`).
2. In `migrateSchema()`, before mapping items, add a step that fills `note: ""`
   into older items. `normaliseItem()` is the single place per-item shape is
   normalising, so most migrations only touch that function.
3. Add a test in `tests/run_tests.py` to cover the new migration.

Because `migrateSchema()` runs on every load, users who saved data under any
old version get upgraded transparently on their next visit. Never assume the
saved shape matches the current code — offline apps keep old data around far
longer than their versions do.

## 5. The settings panel pattern

The header's **Settings** button toggles the `#settings-panel` and flips its
`aria-expanded`. The current panel shows at-a-glance storage health
(`#storage-status`) plus a human-readable privacy note. The pattern to copy
for options:

1. Add an input (checkbox/sliding thumb/radio group) inside the panel.
2. On change, save into your state via `saveState()`.
3. In `render()`, apply the option — e.g. via a class on `<body>`.
4. Migrate the field exactly like any other schema change (step 4 above).

## 6. Reset and export — always present in an offline app

Offline apps have no cloud backup, so the template bakes in the two buttons
that earn users' trust:

- **Export data** — `buildExportPayload(state)` snaps a timestamped, migrated
  copy of the data and downloads it as `.json`. Restore is trivial: the file
  content is valid state your `migrateSchema()` can consume.
- **Reset** — `resetState()` after a `confirm()`, with text that suggests
  exporting first. Resetting without an escape hatch would be scary; with
  export one click away, it's honest.

If you add more settings, consider exporting *settings and data together* —
that's what users actually want to keep.

## 7. The print stylesheet

`@media print` at the bottom of the CSS drops toolbars, forms, and buttons, and
renders the data as clean paper output. When you design your own module, fold
new controls in there too — a checklist you can print is a genuinely better
checklist.

## 8. Run the offline tests

No browser, no packages:

```bash
python3 tests/run_tests.py
```

- The checks load helper logic using Node (installed with Node.js — if Node is
  missing, the runner tells you and still runs the structural checks).
- Add logic checks by appending to `SCENARIOS` in `tests/run_tests.py`. Each
  scenario runs against a fresh fake localStorage, so scenarios never
  contaminate each other.

## 9. Shipping it

- GitHub Pages works out of the box: rename `template.html` to `index.html`
  and enable Pages (main branch / root). No build system needed.
- One note on publishing: to stay genuinely offline the file must remain
  **request-free** — inline favicon, inline CSS, no CDN scripts. That keeps the
  promise real.

That's the whole loop: copy → rename → rewrite the module → bump the schema
when shapes change → run the tests. Good luck, and keep the file single!
