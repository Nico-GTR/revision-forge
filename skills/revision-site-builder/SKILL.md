---
name: revision-site-builder
description: Builds, tests and pushes to main a static revision site (Vite, React, TS, search, workshop, interactive diagrams) from a design zip dropped into Claude Code, token-efficiently. Also handles updates.
---

# Build a revision site from a design folder

## When to use

The user drops a zip made by the `revision-site-brief` skill (`<CODE>_for_Claude_Code.zip`, or `…_v2.zip` for an update) and asks you to follow it, or asks to fix or extend a site built from one. The repo is, or will be, connected to Netlify, which redeploys on every push to `main`.

Expected: **full autonomy** until the push (no pause for plan approval), **push to `main`**, **brief files never committed**, and a site that always has a **global search bar**, a **workshop**, and **interactive diagrams that don't break**.

**Who owns what.** The folder holds only course-specific content and decisions. This skill and its references hold every default: site architecture, technical constraints, search, workshop, training mode, diagram reliability, tests, working method. A line in the brief's "Deviations" section overrides a default; nothing else does.

**Language**: site content and UI in the site language from the brief. Code, comments, README and commit messages in English unless the brief says otherwise.

## References (load only when needed)

| File | Read it when |
|---|---|
| `references/site-defaults.md` | planning (architecture, pages, training mode, acceptance criteria) |
| `references/technical-foundation.md` | scaffolding (stack, content import, storage, theme, canvas, CLAUDE.md, quiet commands) |
| `references/search-and-workshop.md` | building search or the workshop |
| `references/interactive-diagrams.md` | building or fixing a widget |

## 0. Token budget: work lean

A site build is long; context grows with every file read and every command output, and the whole context is re-sent on each step. Rules:

- **Read each brief file once.** Then write a compact plan to `_brief/PLAN.md` (git-excluded): chapter list, IDs, widget list, decisions. Work from the plan and re-open a brief section only by targeted search (`grep -n 'id: W3.1' -A 30`), never the whole file again.
- **Import, don't retype.** Content in `02` and the YAML blocks in `03`/`04` are converted by a script (`scripts/import-brief.ts`, see `technical-foundation.md`) into `src/content/`. Never copy course text or items by hand: it doubles the tokens and introduces typos.
- **Quiet commands, trimmed output**: `npm ci --no-audit --no-fund --silent`, `npx vitest run --reporter=dot`, `npx playwright test --reporter=line`, `npm run build 2>&1 | tail -n 30`. On failure, re-run only the failing test file. Never `cat` long logs: `grep`/`tail` them.
- **Never read generated or vendor files**: `node_modules/`, `dist/`, `package-lock.json`, `src/generated/`, `.vite/`. Use `rg` with explicit paths.
- **Screenshots are expensive** (each image costs many tokens). Automated checks (console errors, horizontal overflow, reference values) do most of the verification. Look at a small set only: home, one chapter mid-animation, workshop, at desktop width in one theme, plus home and one chapter at 375 px in the other theme. Re-shoot only what you changed.
- **Delegate noisy jobs** when subagents are available: triaging a long failing test run or reviewing screenshots can go to a subagent on a smaller model, which returns a short summary. Don't delegate small jobs.
- **Checkpoint**: commit after each building block; at milestones (after scaffold + import, after P1 widgets, after workshop), if the context is large, compact with the instructions from the site's `CLAUDE.md`. `PLAN.md` and git history carry the state.
- **Write the site's `CLAUDE.md`** early (≤ 60 lines, template in `technical-foundation.md`): commands with quiet flags, where content lives, rules, compact instructions. Future small-tweak sessions then start without exploring the repo.
- Keep replies short between steps; the final report is the one long message.

## 1. Prepare without polluting the repo

1. Unzip **outside git tracking**: into `_brief/` at the root with `_brief/` added to `.git/info/exclude` (not to `.gitignore`), or a temp folder. The zip itself, if in the repo, is excluded the same way. Check with `git status`.
2. Mode:
   - **creation**: no site in the repo;
   - **update**: site exists and the folder contains `07_UPDATE.md` → section 8;
   - **overhaul**: site exists, no `07` → keep what works and is right (checked against the folder's values), reorganise, keep progress keys where possible.

## 2. Read and plan

1. Read `00_BRIEF.md`, then the other files in its table (`07` first if present).
2. Read `references/site-defaults.md`.
3. Write `_brief/PLAN.md`: tree, components, pure functions and tests, order, deviations applied. Put a short version of the plan in your reply, then **carry on without waiting**.

## 3. Implementation order

Unless the brief deviates:

1. Scaffold (stack, `netlify.toml`, theme tokens, layout, routing, header with search bar, `Widget` shell), site `CLAUDE.md`;
2. `scripts/import-brief.ts` + its tests; run it to fill `src/content/`;
3. pure functions + Vitest tests: computations, generator logic, answer checkers, search, Leitner, widget reducers; every `answer` / `reference` / `expect` value of the folder becomes a test case;
4. P1 widgets, each with its Playwright interaction test;
5. chapter pages, in the diagnosis start order;
6. workshop;
7. training mode (mock exam or oral);
8. glossary, extra pages;
9. P2 then P3 widgets.

Small, frequent commits, one per building block.

## 4. Non-negotiables

- **100 % static**: no backend, serverless function, API key, or AI-model call.
- **Logic in `lib/` as pure, tested functions**; components only render.
- **Search bar on every page**, index generated at build time (`search-and-workshop.md`).
- **Workshop playable on every chapter**; if a chapter has no workshop material in the folder, use its quiz items and report the gap. Never invent items.
- **Diagram reliability rules** (`interactive-diagrams.md`): reducer + view, one animation clock with cleanup, clamped inputs, layout that holds at 375 px, per-widget error boundary, Playwright interaction test per P1 widget failing on any console error.
- **Faithful content**: origin badges visible; each misconception has its "Watch out" box, quiz item and workshop item; folder decisions applied.
- **Progress keyed by folder IDs**, `localStorage` in try/catch with prefixed, versioned keys.

## 5. Decide alone, invent nothing

Nobody answers during the session. If something is missing or ambiguous: look in the brief; otherwise take the most cautious option, the one that adds no content (flag the gap on the site where relevant); record it in `INCONSISTENCY_NOTES.md` at the repo root (committed). Never resolve a content inconsistency silently; never invent a fact, value or result.

## 6. Verify before pushing

1. `npx vitest run --reporter=dot`: all green.
2. `npm run build`: no TypeScript error.
3. `npx playwright test --reporter=line`: widget interaction tests and smoke tests green, zero console errors.
4. Functional checks (automated where possible): search bar on every route; each reference query lands on the right section; a workshop series starts on every chapter and completes with the keyboard; no horizontal overflow at 375 px.
5. The small screenshot set (section 0); fix and re-shoot only what changed.
6. Acceptance criteria: the defaults in `site-defaults.md` plus the brief's own, one by one. Check no out-of-scope content and no confidential data (`rg` for IP patterns and banned names in `src/`).
7. Site README: install, dev, tests, Netlify, where to edit content, how to add an item, generator or widget, how the search index and import work.

A criterion that can't be met goes in the report, undisguised.

## 7. Push

1. `git status`: `package-lock.json`, `netlify.toml`, `CLAUDE.md`, `INCONSISTENCY_NOTES.md` committed; no brief file, no `node_modules/`, no `dist/`.
2. Push to `main`. If refused (protected branch, session limited to a working branch), push to the allowed branch and give the next step in the report (merge, or set the production branch in Netlify). Never `--force` without an explicit request.
3. Netlify deploys; don't deploy yourself.

## 8. Update mode (delta folder)

The v2 folder holds only `00_BRIEF.md`, `07_UPDATE.md` and the new or changed parts. The repo is the source of truth for everything else.

1. Read `07`, then the delta files. Don't explore the whole codebase: `CLAUDE.md` and targeted `rg` on the IDs in `07` locate what to change.
2. Re-run `import-brief` on the delta: it **upserts by ID** into `src/content/` and never deletes; apply removals listed in `07` explicitly. Chapter pages that were hand-enriched after import are edited in place for the changed sections only.
3. Preserve progress: slugs, routes, IDs and `localStorage` keys unchanged; if the stored format changes, bump the key version with a tested migration.
4. Buggy widgets listed in `07`: write the failing test first, then fix (`interactive-diagrams.md`).
5. Search index and workshop pick up the new content automatically; add the new reference queries to the tests.
6. Run section 6 in full, push to `main`.
7. In the report, go through the `07` table row by row: done / partly / not done (why).

## 9. Final report

Plan (or `07` table) vs delivered; acceptance criteria with reasons when unmet; test, build and interaction-test results; screenshots; pushed branch and last commit; `INCONSISTENCY_NOTES.md` contents; what remains (P2/P3 widgets, chapters without workshop material, points to confirm); Netlify settings (build `npm run build`, folder `dist`, branch `main`).
