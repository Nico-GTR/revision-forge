# Brief: revision site — <COURSE / PROJECT> (<institution>)

Build with the `revision-site-builder` skill. Its defaults (stack, search, workshop, diagram reliability, tests, working method, push to `main`) apply unless a line in "Deviations" says otherwise.

- **Site code**: <CODE> (localStorage prefix)
- **Site language**: <language>, <tone, e.g. informal "tu", direct and kind>
- **Mode**: <creation | update v2>

## Context
<2–4 lines: who revises, real situation, diagnosis in one sentence, deadline, goal (understand mechanisms / answer in-depth oral questions).>

## Files
| File | Content |
|---|---|
| 01_DIAGNOSIS.md | misconceptions, gaps, start order |
| 02_COURSE_CONTENT.md | source of truth |
| 03_EXERCISES.md | items, generators, exams (YAML) |
| 04_INTERACTIVE_MODULES.md | widgets, search queries, training (YAML) |
<add 05/06/07 if present>

## Sources and precedence
<Allowed sources; precedence rule when documents disagree; origin tag set.>

## Confidentiality
<What must never appear, or "nothing sensitive".>

## Scope
| # | Slug | Title | Level | Priority |
|---|---|---|---|---|
| 1 | ch01-… | … | weak | high |
Out of scope: <…>

## Assessment
<Written: date, duration, documents, parts, marks, penalty; see EXAM-… in 03.
Oral: who asks, kind of questions, date.>

## Site specifics
- Home signature element: <…>
- Extra pages: <cheat sheet, timeline, A4 summary… or none>
- Permanent helper: <e.g. decimal ↔ binary converter, or none>
- Imposed / banned vocabulary: <…>

## Visual direction (proposal, refine freely)
<concept; signature motif; colour code with hex light/dark; fonts>

## Decisions already made
- <inconsistency → decision>

## Deviations from the builder defaults
- <none, or e.g. "BrowserRouter instead of HashRouter", "no mock exam: oral mode only">

## Acceptance criteria (course-specific, on top of the builder's)
- [ ] <e.g. the 2025 midterm is playable in mock-exam mode with its real penalty>
