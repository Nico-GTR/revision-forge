# Interactive diagrams: patterns that don't break

Indicative code for the diagram reliability rules. Adapt it to the project; keep the principles. Each widget's spec (inputs with ranges, steps with their "why", edge cases, reference states) comes from its YAML block in `04_INTERACTIVE_MODULES.md`: ranges feed `clamp`, `reference` and `edge_cases` become tests.

## 1. Pure logic: reducer + view

Everything that can go wrong numerically lives here, where it is cheap to test.

```ts
// lib/widgets/w31-routing.ts
export type Params = { hops: number; ttl: number };
export const RANGES = { hops: [1, 12], ttl: [1, 64] } as const; // from the widget's YAML spec
export const STEPS = ['send', 'hop', 'decrement', 'drop-or-forward', 'arrive'] as const;

export type State = { params: Params; step: number; playing: boolean };
export type Action =
  | { type: 'next' } | { type: 'prev' } | { type: 'reset' }
  | { type: 'play' } | { type: 'pause' } | { type: 'tick' }
  | { type: 'set'; key: keyof Params; value: number };

const clamp = (v: number, [min, max]: readonly [number, number]) =>
  Number.isFinite(v) ? Math.min(max, Math.max(min, Math.round(v))) : min;
const last = STEPS.length - 1;

export const initial = (p: Params): State => ({ params: p, step: 0, playing: false });

export function step(s: State, a: Action): State {
  switch (a.type) {
    case 'next':  return { ...s, step: Math.min(s.step + 1, last) };
    case 'prev':  return { ...s, step: Math.max(s.step - 1, 0), playing: false };
    case 'reset': return { ...s, step: 0, playing: false };
    case 'play':  return { ...s, playing: true, step: s.step === last ? 0 : s.step };
    case 'pause': return { ...s, playing: false };
    case 'tick':  return s.step >= last ? { ...s, playing: false } : { ...s, step: s.step + 1 };
    case 'set':   // input change: restart cleanly, never keep a stale animation
      return { params: { ...s.params, [a.key]: clamp(a.value, RANGES[a.key]) }, step: 0, playing: false };
  }
}

export type View = { packetX: number; ttlLeft: number; caption: string };
export function view(p: Params, stepIndex: number): View {
  const i = Math.min(Math.max(stepIndex, 0), last);
  // ... computation from the course, no NaN possible here
  return { packetX: (i / last) * 100, ttlLeft: Math.max(p.ttl - i, 0), caption: STEPS[i] };
}
```

Tests:

```ts
import { describe, it, expect } from 'vitest';
import { step, view, initial, STEPS } from './w31-routing';

describe('W3.1', () => {
  it('reference states from 04', () => {
    expect(view({ hops: 3, ttl: 2 }, 2).ttlLeft).toBe(0);
  });
  it('never leaves bounds, never NaN', () => {
    let s = initial({ hops: 3, ttl: 8 });
    const actions = ['next', 'prev', 'reset', 'play', 'pause', 'tick'] as const;
    for (let k = 0; k < 5000; k++) {
      s = Math.random() < 0.1
        ? step(s, { type: 'set', key: 'ttl', value: (Math.random() - 0.3) * 200 })
        : step(s, { type: actions[Math.floor(Math.random() * actions.length)] });
      expect(s.step).toBeGreaterThanOrEqual(0);
      expect(s.step).toBeLessThan(STEPS.length);
      for (const v of Object.values(view(s.params, s.step)))
        if (typeof v === 'number') expect(Number.isFinite(v)).toBe(true);
    }
  });
  it('clamps garbage input', () => {
    const s = step(initial({ hops: 3, ttl: 8 }), { type: 'set', key: 'ttl', value: NaN });
    expect(s.params.ttl).toBe(1);
  });
});
```

## 2. One animation clock, always cleaned up

```ts
import { useEffect, useRef } from 'react';

export function useAnimationClock(playing: boolean, intervalMs: number, onTick: () => void) {
  const cb = useRef(onTick);
  useEffect(() => { cb.current = onTick; });

  useEffect(() => {
    if (!playing) return;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const every = reduced ? Math.max(intervalMs, 1200) : intervalMs;
    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      if (document.hidden) last = now;          // don't catch up after a hidden tab
      else if (now - last >= every) { last = now; cb.current(); }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);      // pause, unmount, route change
  }, [playing, intervalMs]);
}
```

Usage: `const [s, dispatch] = useReducer(step, preset, initial); useAnimationClock(s.playing, 1000 / speed, () => dispatch({ type: 'tick' }));`. Because `playing` lives in the reducer, spamming Play can't start a second clock.

## 3. The shared `Widget` shell with an error boundary

```tsx
import { Component, type ReactNode } from 'react';

class WidgetBoundary extends Component<
  { fallback: (retry: () => void) => ReactNode; children: ReactNode },
  { failed: boolean; key: number }
> {
  state = { failed: false, key: 0 };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(err: unknown) { console.error('[widget]', err); }
  retry = () => this.setState((s) => ({ failed: false, key: s.key + 1 }));
  render() {
    return this.state.failed
      ? this.props.fallback(this.retry)
      : <div key={this.state.key}>{this.props.children}</div>;
  }
}

export function Widget(props: { id: string; title: string; description: string; children: ReactNode }) {
  return (
    <figure className="widget" data-testid={`widget-${props.id}`} aria-label={props.title}>
      <figcaption>{props.title}</figcaption>
      <WidgetBoundary
        fallback={(retry) => (
          <div role="alert">
            <p>{props.description}</p>
            <button onClick={retry}>Reload diagram</button>
          </div>
        )}
      >
        {props.children}
      </WidgetBoundary>
      <p className="sr-only">{props.description}</p>
    </figure>
  );
}
```

Note: `componentDidCatch` logs to the console on purpose, so a crash still fails the Playwright test even though the page survives.

## 4. Layout that holds

- SVG: `<svg viewBox="0 0 600 300" style="width:100%;height:auto">`, font sizes in viewBox units, `text-anchor` chosen per side so labels near the edges don't clip.
- Long labels: shorten on narrow screens (`useMediaQuery`) or move them to a legend under the diagram.
- Canvas: see `technical-foundation.md` (devicePixelRatio, ResizeObserver, theme MutationObserver).
- Controls: `display:grid` that puts controls below the diagram under ~720 px; range inputs at 100 % width; touch targets ≥ 44 px.

## 5. Playwright interaction test template

Run against `npm run preview` (Playwright `webServer`). One test per P1 widget.

```ts
import { test, expect, type Page } from '@playwright/test';

function trackErrors(page: Page) {
  const errors: string[] = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(e.message));
  return errors;
}

test('W3.1 survives every interaction', async ({ page }) => {
  const errors = trackErrors(page);
  await page.goto('/#/ch03-routing');
  const w = page.getByTestId('widget-W3.1');
  const next = w.getByRole('button', { name: /next/i });      // use the site-language labels
  const prev = w.getByRole('button', { name: /previous/i });
  const play = w.getByRole('button', { name: /play|pause/i });

  for (let i = 0; i < 10; i++) await next.click();             // past the end
  for (let i = 0; i < 10; i++) await prev.click();             // past the start
  for (let i = 0; i < 5; i++) await play.click();              // spam play/pause
  await page.waitForTimeout(1500);

  const slider = w.getByRole('slider').first();
  await slider.focus();
  await page.keyboard.press('Home');
  await page.keyboard.press('End');
  await expect(w.getByTestId('ttl-left')).not.toHaveText(/NaN|undefined|Infinity/);

  await page.setViewportSize({ width: 375, height: 800 });
  expect(await page.evaluate(() =>
    document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  await page.getByRole('button', { name: /theme/i }).click();
  await play.click();
  await page.goto('/#/');                                      // leave mid-autoplay
  await page.goBack();

  // reference state from 04
  await w.getByRole('button', { name: /reset/i }).click();
  await next.click(); await next.click();
  await expect(w.getByTestId('ttl-left')).toHaveText('0');

  expect(errors).toEqual([]);
});
```

## 6. Fixing a reported bug

1. Get the symptom (screenshot, steps) from the user or `07_UPDATE.md`.
2. Write the Playwright or Vitest test that reproduces it, and watch it fail.
3. Fix the root cause in the reducer, the view or the lifecycle, not with a guard in the component.
4. Keep the test: it now protects every future update.
