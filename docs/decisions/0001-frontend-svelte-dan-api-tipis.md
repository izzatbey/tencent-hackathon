# 0001: Frontend Vite + Svelte + TS, API tipis stdlib, unittest untuk core

- Date: 2026-10-27
- Status: Accepted

## Context

`frontend/` was empty and `POST /api/ask` existed only as a draft contract
(docs/architecture.md §4). Submission is due 1 Nov 2026; the UI is needed for
the demo video, the test screenshots and the 90-second live test. The backend
is pure Python with zero dependencies (owner: Izzat); the UI owner is Farrez.

## Options considered

Frontend: Vite + React + TS; Vite + Svelte + TS; plain HTML/JS without a build.
All three can be tested with Playwright; React and Svelte also get Vitest +
Testing Library component tests.

Data source: thin stdlib API wrapping `process_query()` (chosen); UI on mock
fixtures only; wait for Izzat.

Core test runner: stdlib `unittest` (chosen); pytest.

## Decision (decided by: Farrez)

Vite + Svelte 5 + TypeScript, a thin `http.server` API in `backend/api/`,
and `unittest` for new core tests (`verify_matrix.py` stays).

## Reasoning (Farrez's words)

"Kode paling sedikit dan cepat untuk deadline 1 November, API tipis supaya UI
bisa diuji dengan engine asli."

## Dependency check (2026-10-27)

All versions pinned exactly, installed with `--ignore-scripts`; no package in
the tree declares install scripts. `npm audit`: 0 vulnerabilities. Every
version is at least 3 days old: `svelte` 5.57.3 was 1 day old, so 5.57.2
(2026-10-06) is used. Licenses: MIT (svelte, vite, vitest, testing-library,
jsdom, phosphor), Apache-2.0 (typescript, playwright), MPL-2.0
(@axe-core/playwright, dev only, unmodified), OFL-1.1 (Source Serif 4,
IBM Plex Mono). Runtime bundle: about 25 kB gzip JS + fonts. Body text uses
the system font stack, so no extra font for the UI face.

## Consequences

- Two runtimes in the repo (Python + Node 22) for whoever builds the UI.
- `answer` is `null` for `OK` until an answer composer (S4) exists; the UI
  shows evidence and does not invent a verdict.
- The API trusts `user`/`role` from the request (persona picker for the
  demo). There is no authentication: anyone can claim any persona.

## Revisit when

- Real authentication is needed (replace the persona picker with login).
- The WorkBuddy agent becomes the only demo surface and the web UI is dropped.
