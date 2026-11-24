# File formats

Structured data goes in fenced ` ```yaml ` blocks, **one object per block**. Claude Code imports them with a script and `scripts/check_folder.py` validates them, so keep the field names exactly as below. Prose around the blocks is allowed but should stay minimal. Text meant for the site (`prompt`, `solution`, `why`…) is written in the site language; Markdown and `$…$` LaTeX are allowed inside strings (use YAML `|` blocks for multi-line text).

## `01_DIAGNOSIS.md`

```markdown
# Diagnosis
Source: <test of N questions answered without revising | self-description>. Conclusion: <one sentence>.

## Misconceptions
| ID | What the user said (quote) | Correct | Where (section) |
|---|---|---|---|
| F1 | "…" | … | 3.2 |

## Strengths
- …

## Gaps, by priority
1. ch03-routing — <why: weight in past exams, size of the gap>

## Start order
ch03-routing, ch01-…, …

## Learning profile (only if the user gave one)
- …
```

## `02_COURSE_CONTENT.md`

```markdown
# Course content
Sources: <list>. Tags: <set used>. Precedence: <rule>.

## Chapter 3 — Routing {#ch03-routing}

### 3.1 Intuition [Lecture]
…
### 3.2 Longest-prefix match [Handout + Lecture]
Keywords: longest prefix, LPM, routing table lookup
…exact formulas in $…$…
> Watch out (F4): …
### 3.3 Pitfalls
…
### 3.4 Key takeaways
- …
```

Rules: heading `## Chapter N — Title {#slug}` exactly; subsections `### N.k Title [tags]`; one `Keywords:` line per subsection; misconception boxes as `> Watch out (F#): …`.

## `03_EXERCISES.md`

Start with one line: "All numeric values were verified by computation." Then one YAML block per item, grouped by chapter under `## ch03-routing` headings.

### Item (quiz, workshop, exam)

```yaml
id: Q3.2                # Q = quiz/bank item, EX = worked exercise, OR = oral question
kind: mcq               # mcq | number | short | cloze | match | order | card | open | oral
chapter: ch03-routing
section: "3.2"          # for the "see the course" link
difficulty: 1           # 1-3
use: [quiz, workshop]   # any of: quiz, workshop, exam, oral
source: Tutorial 2      # origin tag or document
misconception: F4       # optional
prompt: |
  Which route is chosen for 10.1.2.3?
choices: {A: "10.0.0.0/8", B: "10.1.0.0/16", C: "0.0.0.0/0"}   # mcq
correct: [B]                                                   # mcq
feedback: {A: "Tempting because it matches too, but /16 is longer."}  # per wrong choice, optional
solution: |
  Longest matching prefix wins: /16 beats /8.
```

Fields by kind:

| kind | answer fields |
|---|---|
| `mcq` | `choices`, `correct` (list), `feedback` (optional, per choice) |
| `number` | `answer` (number), `tol` (absolute) or `rel_tol`, `units` (accepted list, optional) |
| `short` | `accepted` (list of accepted answers, compared case/accent-insensitively) |
| `cloze` | `text` with `{{1}}`, `{{2}}` blanks, `blanks: {1: [accepted…], 2: […]}` |
| `match` | `pairs: {left: right}` |
| `order` | `sequence` (list, correct order) |
| `card` | `back` (self-assessed flashcard) |
| `open` | `criteria` (list of marking criteria), `solution` |
| `oral` | `short_answer` (20 s), `key_points` (list), `follow_up` |

Optional on any item: `hint`, `steps` (list, step-by-step solution), `traps` (list of `{answer, misconception, feedback}` for wrong answers that reveal a misconception).

### Generator

```yaml
id: GEN-3A
kind: generator
chapter: ch03-routing
section: "3.2"
title: Pick the route by longest prefix
levels:
  1: two candidate routes
  2: four routes, one default
  3: overlapping prefixes, tie-breaking by metric
params:
  prefix_len: {min: 8, max: 30, int: true}
constraints:
  - at least two routes match the address
answer_format: {kind: short}          # or {kind: number, tol: 0.01, units: [ms]}
method: |
  1. Write the address in binary… 2. …
hint: Compare the number of matching leading bits.
misconception: F4
reference:                            # computed by code; become unit tests
  - params: {address: 10.1.2.3, routes: ["10.0.0.0/8", "10.1.0.0/16"]}
    answer: "10.1.0.0/16"
```

### Exam structure (written assessment)

```yaml
id: EXAM-2025-MIDTERM
kind: exam
source: Midterm 2025
duration_min: 120
documents: none
penalty: "-0.25 per wrong MCQ answer, 0 for no answer"
parts:
  - {title: MCQ, points: 6, items: [Q1.4, Q2.1, Q3.2]}
  - {title: Exercise 1, points: 8, items: [EX3.4]}
```

### Reference values

Every computed value in `03` and `04` lives in an `answer`, `reference` or `expect` field, so the builder turns them into tests directly. No separate table.

## `04_INTERACTIVE_MODULES.md`

Colour code first (one line per notion, hex light/dark), then one YAML block per widget.

```yaml
id: W3.1
kind: widget
chapter: ch03-routing
section: "3.2"
priority: P1                     # P1 essential | P2 important | P3 bonus
title: Route lookup, step by step
inputs:
  address: {type: text, default: "10.1.2.3", validate: ipv4}
  routes:  {type: list, default: ["10.0.0.0/8", "10.1.0.0/16"], max_items: 6}
steps:
  - {id: binary,  shows: address and prefixes in binary, why: comparison is bit by bit}
  - {id: compare, shows: matching bits highlighted,       why: …}
  - {id: choose,  shows: longest match selected,          why: …}
presets: {course_example: {address: "10.1.2.3"}}
misconception: F4
demonstrates: "button 'swap order': the result doesn't depend on table order"
quiz: [Q3.2, Q3.5]               # "Test me" questions, by ID
edge_cases:
  - {input: {routes: []}, expect: "message: no route, packet dropped"}
  - {input: {address: "999.1.1.1"}, expect: "validation message, previous value kept"}
reference:
  - {input: {address: "10.1.2.3"}, step: choose, expect: {chosen: "10.1.0.0/16"}}
notes: |
  Optional prose for anything the fields can't express.
```

Search reference queries (one block):

```yaml
kind: search-queries
queries:
  - {q: "plus long prefixe", expect: "ch03-routing#3.2"}
  - {q: "LPM", expect: "glossary:LPM"}
  - {q: "routage", expect: "ch03-routing"}
```

Training mode: one short block of course-specific choices only (exam IDs to reproduce, or oral settings); defaults come from the builder skill.

```yaml
kind: training
mode: mock-exam            # mock-exam | oral
exams: [EXAM-2025-MIDTERM]
generated_papers: 1
```

## `06_GLOSSARY.md`

```markdown
| Term | Meaning | Definition | Synonyms | Ch. |
|---|---|---|---|---|
| LPM | Longest Prefix Match | … | longest prefix | ch03-routing |
```

## `07_UPDATE.md` (update mode)

```markdown
# Update v1 → v2 (<date>)
New sources: <list>

| Type | ID / slug | File | Detail |
|---|---|---|---|
| add | ch05-qos | 02 | new chapter |
| fix | Q3.2 | 03 | wrong answer B → C (recomputed) |
| remove | GEN-2B | 03 | out of scope now |
| bug | W3.1 | 04 | freezes when the route list is emptied during autoplay (steps: …) |

Must not change: slugs, IDs, progress keys, <approved visual choices>.
Update acceptance criteria:
- [ ] …
```
