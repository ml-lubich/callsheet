# Gaps — the React shell against the brief

Taken before the second pass. Everything not listed here is on disk and passing:
the Vite/singlefile build, the build-time data plugin, the strip chart, the R3F
terrain with its WebGL guard, the ten glyphs with their render tests, the
spacing-tolerant search, `registerFigure`, the skeleton boot, the theme toggle,
and the Python `--web` branch with its nine mocked-subprocess tests.

Baseline: pytest 273 passing, vitest 44 passing.

## 1. ScrollStack — absent

Nothing of the skill is ported. `Acts` renders a plain list of `<article>`s.

- `lib/scroll-stack-layout.ts`: `shouldUseCompactScrollStackViewport` and
  `resolveScrollStackVariant`, verbatim from the skill's reference, with the
  three exported thresholds.
- Its test, verbatim, translated from `bun:test` to vitest imports only.
- `components/ScrollStack.tsx`: the ~150-line framer component. Contract:
  `compactClassName` is the old layout verbatim; first paint is compact and the
  stack is swapped in after mount; the stack root owns the `useScroll` ref;
  sticky top is `stickyTop + i * stackOffset`; a covered card goes to scale .94
  / opacity .72; the last card never shrinks; defaults 112 / 18 / 62.
- Its component test: compact on a phone viewport, stack at 1600, compact under
  reduced motion, and `compactClassName` passed through.
- Applied to `Acts` and to nothing else on the page.

## 2. Scroll primitives — absent

- `useScrollProgress(ref)` — 0..1 for an element crossing the viewport.
- `Pinned` — a sticky child inside a runway.
- `Scrub` — maps that progress onto a child's render.
- `driver="reveal" | "scroll"` on figures. Today the draw-on is reveal-only,
  hard-wired to an IntersectionObserver in `sections/Figures.tsx`.

## 3. Transcript is a list, not a reader

`sections/Transcript.tsx` renders every turn flat inside one Collapsible.
Missing:

- A sticky chapter rail built from `CONTENT.acts`, highlighting the current act
  via IntersectionObserver.
- Turns grouped per act, each act its own Collapsible, collapsed by default.
- A pinned miniature strip chart as a scrubber: a viewport window that follows
  scroll, and that scrolls the reader on drag and on click.
- Search hits drawn as ticks on that scrubber.
- The speaker key repeated at the top of the transcript.

Search itself (spaceless-tolerant), the speaker filter and the `#t-12` deep
link are already right and stay as they are.

## 4. Speaker key — absent

`CONTENT.meta.participants` carries name and role; `stats()` already computes
word share. Neither the plate nor the transcript shows a key.

## 5. `_mode` is ignored

`src/callsheet/modes.py` writes `content._mode` with `sections` (the list *and*
the order), `transcript` (`open` / `collapsed` / `omit`) and `figures` (a cap).
`templates/page.html` honours all three. `App.tsx` has a hard-coded section
order, no gating, no transcript mode, no figure cap, and never renders the
`highlights` section that `summarized` mode produces.

## 6. Motion is in one section only

`Reveal` exists and is used by `Acts` alone. The brief asks for elements popping
in across the whole page with a 40–80ms in-section stagger, one-way, no bounce,
nothing moving after it settles, all of it off under reduced motion.

## 7. Too much whitespace

`section{padding:56px 0}` — the brief asks for roughly 35% tighter. Prose does
not sit beside figures at desktop widths: `.dg-wrap` is a single column at every
size.

## 8. Palette is the vanilla template's, unmodernised

Light ground is `#E9EAE3`, a cream, where the brief asks for a cool off-white.
Dark is `#14181B`, near-black rather than a deep blue-black slate. The two pens
are a warm red and a cool blue, which is the right axis, but neither pair has
been checked for AA body / AAA headings.

## 9. Housekeeping

- `.gitignore` has `dist/` (which covers `web/dist`) but not `node_modules`, and
  `web/tsconfig.tsbuildinfo` is an untracked build artefact.
- README says nothing about the web build.
- No screenshots have been taken at any width.

## 10. Tests to add

vitest: the ScrollStack routing table (every row) and the component contract;
`_mode` section gating and ordering; the transcript rail and scrubber; the
speaker key. pytest is already covered.
