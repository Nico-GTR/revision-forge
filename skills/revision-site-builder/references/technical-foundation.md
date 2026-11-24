# Technical foundation: indicative snippets

Starting points, not rules. Search and workshop: `search-and-workshop.md`. Widgets: `interactive-diagrams.md`.

## Structure

```
CLAUDE.md                 short, for future sessions (template below)
INCONSISTENCY_NOTES.md
netlify.toml
scripts/
  import-brief.ts         folder (02/03/04/06) → src/content/
  build-search-index.ts   src/content → src/generated/search-index.json (prebuild)
src/
  content/                chapters (MDX), items.json, generators/, widgets.json, glossary.json  ← edit here
  generated/              build output, never edited, never read
  lib/                    pure functions + *.test.ts
  components/             rendering only (Widget shell, widgets, Quiz, SearchBar, Workshop…)
  pages/
e2e/                      Playwright: widgets.spec.ts, smoke.spec.ts
```

## Content import (`scripts/import-brief.ts`)

Converting the folder by script instead of retyping it saves the most tokens and removes copy errors.

- **Chapters**: split `02_COURSE_CONTENT.md` on `## Chapter N — Title {#slug}`; write `src/content/chapters/<slug>.mdx`; turn `### N.k Title [tags]` into headings with an anchor `#N.k` and a badge component; `> Watch out (F#): …` into a `<WatchOut id="F#">` component; keep `Keywords:` lines as front-matter for search. After the first import, chapter files belong to the site (widgets get embedded by hand); later runs only write chapters that don't exist yet, unless `--force <slug>`.
- **YAML blocks** in `03`/`04`: extract every ` ```yaml ` block (`js-yaml`), validate with a small schema (zod or hand-written guards), and **upsert by `id`** into `src/content/items.json`, `generators.json`, `exams.json`, `widgets.json`, `search-queries.json`. Never delete on import; removals come from `07_UPDATE.md`.
- **Glossary**: parse the `06` (or end-of-`02`) table into `glossary.json`.
- **Generators**: the YAML is a spec (params, method, reference). Implement each as a pure function in `src/lib/generators/<id>.ts`; its `reference` entries become its tests.
- **Tests for the importer**: a fixture folder with one block of each kind, checking upsert, no deletion, and that every `answer` / `reference` / `expect` value ends up in the content.

```ts
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';

export function yamlBlocks(md: string): Record<string, unknown>[] {
  const out: Record<string, unknown>[] = [];
  for (const m of md.matchAll(/```yaml[^\n]*\n([\s\S]*?)```/g)) {
    const obj = yaml.load(m[1]);
    if (obj && typeof obj === 'object' && !Array.isArray(obj)) out.push(obj as Record<string, unknown>);
  }
  return out;
}

export function upsert<T extends { id: string }>(existing: T[], incoming: T[]): T[] {
  const byId = new Map(existing.map((x) => [x.id, x]));
  for (const x of incoming) byId.set(x.id, { ...byId.get(x.id), ...x });
  return [...byId.values()];
}
```

## Site `CLAUDE.md` template (keep ≤ 60 lines)

```markdown
# <CODE> revision site
Static Vite + React + TS site, deployed by Netlify from `main`. Site language: <language>.

## Commands (quiet)
- install: `npm ci --no-audit --no-fund --silent`
- unit tests: `npx vitest run --reporter=dot` (one file: `npx vitest run src/lib/x.test.ts`)
- interaction tests: `npx playwright test --reporter=line` (one widget: `-g W3.1`)
- build: `npm run build 2>&1 | tail -n 30`
- import a new design folder: `npx tsx scripts/import-brief.ts <folder>`

## Where things are
- content: `src/content/` (chapters MDX, items.json, widgets.json, glossary.json)
- logic: `src/lib/` (pure, tested); widgets: `src/components/widgets/W*.tsx` + `src/lib/widgets/`
- never read: node_modules/, dist/, src/generated/, package-lock.json

## Rules
- IDs (slugs, Q*, GEN-*, W*) are progress keys: never rename.
- Widgets follow the reducer + view + error boundary pattern; every fix starts with a failing test.
- Content comes from the design folder only; log decisions in INCONSISTENCY_NOTES.md.
- Commit messages in English; push to main.

## Compact instructions
When compacting, keep: current task, files changed and why, failing tests, open decisions. Drop: file contents already committed, passing test output, screenshots.
```

## Netlify

```toml
[build]
  command = "npm run build"
  publish = "dist"
```

With `BrowserRouter`, add `public/_redirects` containing `/* /index.html 200`. With `HashRouter`, not needed.

## Quiet `package.json` scripts

```json
{
  "scripts": {
    "predev": "tsx scripts/build-search-index.ts",
    "prebuild": "tsx scripts/build-search-index.ts",
    "build": "tsc -b && vite build --logLevel warn",
    "test": "vitest run --reporter=dot",
    "e2e": "playwright test --reporter=line"
  }
}
```

## localStorage: try/catch, prefixed and versioned

```ts
const PREFIX = 'mysite:v1:';

export function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function save(key: string, value: unknown): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    /* storage unavailable */
  }
}
```

"Reset my progress" removes every key with the prefix. A format change means a new prefix version plus a tested `migrate(v1) → v2`.

## Theme without flash (inline in `<head>`)

```html
<script>
  (function () {
    var t = null;
    try { t = localStorage.getItem('theme'); } catch (e) {}
    if (t !== 'light' && t !== 'dark') {
      t = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.dataset.theme = t;
  })();
</script>
```

## Sharp canvas, redrawn on resize and theme change

```ts
export function setupCanvas(canvas: HTMLCanvasElement) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.max(1, Math.round(canvas.clientWidth * dpr));   // never 0 when mounted hidden
  canvas.height = Math.max(1, Math.round(canvas.clientHeight * dpr));
  const ctx = canvas.getContext('2d')!;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return ctx;
}

const css = (name: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim();

export function useRedraw(target: HTMLElement | null, draw: () => void) {
  useEffect(() => {
    if (!target) return;
    const ro = new ResizeObserver(() => draw());
    ro.observe(target);
    const mo = new MutationObserver(() => draw());
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    draw();
    return () => { ro.disconnect(); mo.disconnect(); };
  }, [target, draw]);
}
```

Useful `Plot` primitives: axes and discreet grid, continuous curve, stems, shaded areas, vertical markers and a draggable cursor, log scales.
