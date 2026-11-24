# Site defaults

Apply unless the brief's "Deviations" section says otherwise. UI labels are in English here: use the site language.

## Pages

1. **Header (every page)**: site title, global search bar (`/`, `Ctrl+K`), theme toggle, navigation. Mobile: search icon opening a full-screen panel, menu for navigation.
2. **Home / dashboard**: chapter map with a mastery bar per chapter (quiz and workshop results); "Where do I start?" button following the diagnosis start order; workshop card with "Today's review" count; assessment countdown or reminder; the brief's signature element.
3. **Chapter page** (one per chapter, same structure every time): Intuition / Mechanism (at least one interactive diagram when the brief specifies one, every exact formula) / In our project (project sites) / Pitfalls with "Watch out" boxes / Worked example / Check yourself (5–10 quiz items, immediate explained feedback) / In-depth questions (oral sites) / Key takeaways (printable) / "Practise this chapter" button (workshop, pre-filtered). Origin badges on every section.
4. **Workshop**: see `search-and-workshop.md`.
5. **Training mode**:
   - **Mock exam** (written assessment): reproduces each `kind: exam` structure exactly; timed (duration from the exam, adjustable); MCQ marking with the real penalty and the option not to answer; automatic marking of computational items; `open` items with model answer and self-assessment against `criteria`; at least one paper generated on the same model from the generators; per-chapter report linking to pages and workshop sets.
   - **Oral mode** (oral, defence): random draw filterable by chapter; answer aloud or in an optional text box; model answer at 3 levels (`short_answer`, `key_points`, `solution`); self-assessment "I knew / partly / I didn't"; spaced repetition; simulation (10 questions × 2 min, report); two-player examiner view.
6. **Glossary**: one-line definitions, links to sections, searchable.
7. Extra pages listed in the brief.
8. Footer: "Reset my progress", export/import progress (JSON).

## Teaching principles

Manipulate before reading; always the "why"; confront misconceptions (feedback says why the wrong answer was tempting); immediate feedback; real values as defaults; drill until automatic.

## Technical constraints

- Vite + React + TypeScript, CSS modules or Tailwind; no SSR; `HashRouter` (or `BrowserRouter` + `public/_redirects`); `netlify.toml` (`npm run build`, `dist`).
- Content in `src/content/` (MDX/TS/JSON), separate from components, produced by `scripts/import-brief.ts`.
- KaTeX for formulas; SVG + React for diagrams, `<canvas>` for images and dense plots; no heavy library without need; teaching algorithms in readable TypeScript.
- Search index generated at build time, client-side, no external service.
- `localStorage` in try/catch, prefixed and versioned keys, keyed by folder IDs.
- Light/dark theme without flash, plots follow the theme; responsive (controls under the diagram on narrow screens); `prefers-reduced-motion` respected.
- Accessibility: keyboard everywhere (quizzes, workshop, search, widgets), visible focus, WCAG AA contrast, text description of every canvas.
- Vitest for all logic; Playwright for widget interaction tests and smoke tests.

## Default acceptance criteria

- [ ] Every chapter in scope has its page, with tags, exact formulas and its widgets.
- [ ] Every misconception has its "Watch out" box, a quiz item and a workshop item.
- [ ] Every P1 widget passes its interaction test with zero console errors; reference states displayed correctly.
- [ ] Search bar on every page; every reference query lands on the expected section first.
- [ ] Workshop series playable on every chapter, keyboard only, through to the report.
- [ ] Training mode faithful to the assessment (structure, timing, penalty) or to the oral format.
- [ ] Origin badges visible; nothing invented or out of scope; no confidential data.
- [ ] `vitest`, `build` and `playwright` green; Netlify builds from `netlify.toml` and the committed lockfile.
- [ ] Site `README.md` and `CLAUDE.md` present.
