# Offline Web App Starter Template

A copy-ready, **single-file** HTML/CSS/JS template for small, friendly, offline web apps.
Open it in a browser and it just works — no server, no build step, no accounts, no network.
A friendly template from [Asdale Dynamics, LLC](https://dylanasdale.github.io) (MIT licensed).

## What's in the box

| File | Purpose |
| --- | --- |
| `template.html` | The whole app: page, styles, localStorage helpers, settings panel, print stylesheet, favicon, and a worked demo module (a counter list). |
| `tests/run_tests.py` | Offline test runner. Validates the template HTML, then loads the JS helper code from `template.html` and checks its logic in Node — no browser needed. |
| `docs/tutorial.md` | Step-by-step guide: copy the template, rename it, replace the demo module with your own idea. |
| `LICENSE` | MIT. Copyright (c) 2026 Asdale Dynamics, LLC. |

## Quick start

1. Copy `template.html` into your new project and rename it (e.g. `index.html`).
2. Change the `<title>` and the demo module markup to match your idea.
3. Open the file in any browser. Data saves automatically in localStorage.
4. When you've made changes, run the tests:

   ```bash
   python3 tests/run_tests.py
   ```

   The runner needs only Python 3 and **Node.js** (for the logic tests).

Everything runs offline. The app never sends data anywhere — all content stays in
the browser's localStorage on your own machine.

## How to test

```bash
python3 tests/run_tests.py
```

You should see 25 passing checks: 12 structural checks plus 13 logic checks on the
storage helpers, schema migration, state load/save/reset, and the export payload.

## Credits

Built by [Asdale Dynamics, LLC](https://dylanasdale.github.io) — beginner-friendly AI
education, books, and practical offline-first tools. Plain English, step by step,
never condescending.
