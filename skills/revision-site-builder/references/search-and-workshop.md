# Search and workshop: default specs and snippets

These are the default specs for every site. The folder adds course-specific material (items, generators, search reference queries in `03`/`04`); a deviation in `00_BRIEF.md` overrides a default. The code is indicative. UI labels are given in English: use the site language.

---

## 1. Global search

### Expected behaviour

- Field in the header of **every** page; on mobile, an icon opens a full-screen panel. Shortcuts `/` and `Ctrl+K` / `⌘K` (ignored when focus is already in a text field).
- Results from 2 characters on, updated while typing (light debounce).
- Groups: Course, Glossary, Exercises, Workshop, Diagrams. At most 5 results per group, then "show more".
- Each result: title, chapter, excerpt with the term highlighted (`<mark>`).
- Keyboard: ↑ ↓ to move, Enter to open, Esc to close. ARIA `combobox` / `listbox` roles, result count announced in an `aria-live` region.
- Opening a result: navigate to the exact anchor, scroll, briefly highlight the section (disabled with `prefers-reduced-motion`). An exercise or workshop item opens in the workshop.
- No results: clear message and 3 suggestions from the glossary (smallest edit distance).

### Index generated at build time

A `scripts/build-search-index.ts` script, run as `prebuild` (and `predev`), walks the files in `src/content/` and writes `src/generated/search-index.json`. Never maintain the index by hand: a newly added section must be findable with no other step.

```ts
export type SearchDoc = {
  id: string;            // unique and stable: "ch03-routing#3.2", "gloss:TTL", "Q3.2", "GEN-3A", "W3.1"
  type: 'course' | 'glossary' | 'exercise' | 'workshop' | 'diagram';
  title: string;
  chapter: string;       // chapter slug
  href: string;          // route + anchor
  text: string;          // plain text, no tags or LaTeX
  keywords?: string;     // keywords, synonyms, acronyms
};
```

### Normalisation and engine

A lightweight library (MiniSearch, FlexSearch) is enough; a custom implementation is fine. Either way, normalisation is a tested pure function.

```ts
export function normalize(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // strip accents
    .toLowerCase()
    .replace(/[’']/g, ' ')
    .trim();
}
```

Example with MiniSearch:

```ts
import MiniSearch from 'minisearch';

export function createIndex(docs: SearchDoc[]) {
  const ms = new MiniSearch<SearchDoc>({
    fields: ['title', 'keywords', 'text'],
    storeFields: ['id', 'type', 'title', 'chapter', 'href', 'text'],
    processTerm: (t) => normalize(t) || null,
    searchOptions: {
      boost: { title: 3, keywords: 2 },
      prefix: true,
      fuzzy: 0.2,
    },
  });
  ms.addAll(docs);
  return ms;
}
```

### Minimum tests

- `normalize('Équation') === 'equation'`.
- Each reference query of the brief: the first result has the expected `id`.
- A query without accents and a query with a typo find the same section as the correct query.
- A glossary acronym returns its glossary entry in the top 3.
- The index script includes every chapter in scope (count `course` documents per slug).

---

## 2. Workshop

### Expected behaviour

- **Access**: main navigation entry, card on the home page, "Practise this chapter" button at the bottom of each chapter (`/workshop?ch=<slug>`).
- **Configuration**: chapters (checkboxes), exercise types, difficulty (1 to 3), length (5, 10, 20, endless). Quick modes:
  - "My weak spots": recently failed items + items linked to the diagnosis misconceptions;
  - "Today's review": items due in spaced repetition;
  - "Mix everything".
- **One item**: statement → input → Enter submits → immediate verdict (correct / wrong / almost, with the reason) → Enter goes to the next one. "Hint" and "Step-by-step solution" buttons; their use is recorded (an item passed with the solution shown doesn't count as mastered).
- **Feedback**: the item's explained solution, the link to the course section and, if the error matches a known misconception (trap answer listed in `03`), the misconception's name and why it was tempting.
- **Series header**: progress (7/10), score, current streak.
- **Report**: score per chapter and per type, list of mistakes with their solution, "Redo the missed ones" and "New series" buttons. The home page's per-chapter mastery is updated.
- **No animation that slows the flow.** Everything is playable with the keyboard.

### Item model

Mirrors the YAML blocks of `03_EXERCISES.md` (format defined by the `revision-site-brief` skill), so the importer copies fields one to one.

```ts
type Base = {
  id: string;                 // "Q3.2", "EX3.4", "OR2.1"; generated: "GEN-3A#seed=1234"
  chapter: string;
  section?: string;           // "3.2" → link to /chapter#3.2
  difficulty?: 1 | 2 | 3;
  use: ('quiz' | 'workshop' | 'exam' | 'oral')[];
  source?: string;
  misconception?: string;     // "F4"
  prompt: string;             // Markdown + KaTeX
  hint?: string;
  steps?: string[];
  solution?: string;
  traps?: { answer: unknown; misconception: string; feedback: string }[];
};

export type Item = Base & (
  | { kind: 'mcq'; choices: Record<string, string>; correct: string[]; feedback?: Record<string, string> }
  | { kind: 'number'; answer: number; tol?: number; rel_tol?: number; units?: string[] }
  | { kind: 'short'; accepted: string[] }                       // compared after normalize()
  | { kind: 'cloze'; text: string; blanks: Record<string, string[]> }
  | { kind: 'match'; pairs: Record<string, string> }
  | { kind: 'order'; sequence: string[] }
  | { kind: 'card'; back: string }                              // self-assessed
  | { kind: 'open'; criteria: string[]; solution: string }
  | { kind: 'oral'; short_answer: string; key_points: string[]; follow_up?: string }
);

export type Generator = {
  id: string;                 // "GEN-3A"
  chapter: string;
  levels: (1 | 2 | 3)[];
  generate: (rng: () => number, level: 1 | 2 | 3) => Item;
};
```

### Seeded randomness (reproducible and testable)

```ts
// mulberry32: small deterministic PRNG
export function rngFromSeed(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const randInt = (rng: () => number, min: number, max: number) =>
  min + Math.floor(rng() * (max - min + 1));
```

The seed is shown under the statement ("Exercise #1234") and lets the user replay the same draw.

### Forgiving marking

```ts
export function parseNumber(input: string): number | null {
  const s = input.trim().replace(/\s/g, '').replace(',', '.');
  if (!/^[-+]?\d*\.?\d+(e[-+]?\d+)?$/i.test(s)) return null;
  return Number(s);
}

export function checkNumber(input: string, a: Extract<Item, { kind: 'number' }>): boolean {
  let raw = input.trim();
  for (const u of a.units ?? []) {
    if (raw.toLowerCase().endsWith(u.toLowerCase())) { raw = raw.slice(0, -u.length); break; }
  }
  const x = parseNumber(raw);
  if (x === null) return false;
  const tol = Math.max(a.tol ?? 0, Math.abs(a.answer) * (a.rel_tol ?? 0));
  return Math.abs(x - a.answer) <= (tol || 1e-9);
}
```

Topic-specific equivalence rules (notations, output formats, accepted units) come from `03`, each with a test.

### Spaced repetition (Leitner boxes)

```ts
export type Card = { id: string; box: 1 | 2 | 3 | 4 | 5; due: number }; // due: timestamp in ms
const DAYS = [0, 1, 2, 4, 8, 16]; // interval per box, in days
const DAY = 86_400_000;

export function review(card: Card, correct: boolean, now: number): Card {
  const box = (correct ? Math.min(card.box + 1, 5) : 1) as Card['box'];
  return { id: card.id, box, due: now + DAYS[box] * DAY };
}

export const isDue = (c: Card, now: number) => c.due <= now;
```

For generators, the card is tracked per generator and level (`GEN-3A@2`), not per draw.

### Minimum tests

- Each generator: for every `reference` entry in its YAML spec, solving with those `params` gives the expected `answer`; a fixed seed always reproduces the same draw.
- 1,000 draws per generator: no degenerate case (division by zero, undefined answer, statement giving away the answer), answers within the expected ranges.
- `checkNumber` accepts a decimal comma, the unit and the allowed rounding; rejects a value outside tolerance and non-numeric input.
- Trap answers trigger the expected misconception feedback.
- `review`: a mistake sends the card back to box 1; a success moves it up one box, capped at 5.
- A series starts for every chapter in scope (at least one item available).
