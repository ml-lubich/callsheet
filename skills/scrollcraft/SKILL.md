---
name: callsheet-scrollcraft
description: Drive a callsheet readout with the reader's scroll position — pinned figures that build in argument order, numbers that count when they arrive, a sticky strip-chart tracker, a chapter rail, and the rests between them. Use when a long readout has an argument whose stages the reader should pass through in order. Do not use for short pages, reference material, appendices, or anything a reader will search with Ctrl-F.
---

# Scrollcraft

Scroll-driving means the reader's position in the page is an input: a figure
assembles as they descend it, a number reaches its value as it arrives, a
transcript tracker follows where they are. It is the same discipline as the
figure set — see `skills/diagrams/SKILL.md` — applied to the axis the reader
already controls.

You do not implement the mechanics. The front end exposes four primitives and
you compose them:

| | |
|---|---|
| `useScrollProgress(ref)` | 0..1 across the referenced element's scroll span |
| `Pinned` | sticks for N viewport heights and passes progress to its children |
| `Scrub` | maps progress to a value with easing |
| `driver="reveal" \| "scroll"` | on a figure: fire once on entry, or track progress |

Everything below is about which of those to reach for, where, and how often.
Do not write components. Do not create files under `web/`.

## 1. When scroll-driving earns its place

The test: **does the reader's position in the argument mean something?** A
figure that reveals in stages because the argument has stages earns a pin. A
figure that fades in because fading in looks expensive does not. The page is
already long; every pinned section makes it longer, and the reader pays that
cost whether or not the motion carried information.

Earns it:

- A pipeline the speaker described one stage at a time, where the point is that
  each stage was added to answer a problem the previous one created. The reader
  descends the same construction.
- A magnitude bar whose whole argument is the ratio. Growing to true size on
  arrival puts the reader's attention on the length at the moment the length is
  the claim.
- A before/after where the finding is the pattern of differences. Crossing from
  one state to the other under the reader's own hand shows which rows moved.
- A long transcript stretch where the reader needs to know where they are on the
  call's time axis, and to scrub back to what they just passed.
- A readout with five or more sections whose order is the argument, where a rail
  of chapter markers tells the reader how much argument is left.

Does not earn it:

- Parallax. Two layers moving at different speeds says nothing about the call.
- Scroll hijacking: intercepting the wheel, snapping to sections, changing the
  scroll rate. The reader's scroll is theirs; you may read it, never steer it.
- A pin added to a figure that reads fine at a glance. If the static figure is
  complete in one pass, driving it only delays it.
- Stages invented for the animation. Splitting a four-box figure into four
  reveals because four reveals feel substantial is a lie about the source.
- Anything that makes the page longer than its content. If half the scroll
  distance is pinned padding, the reader is scrolling through nothing.

The honest default for a callsheet readout is: **most of the page is not
driven.** Three or four driven sections in an hour-long call's readout. Past
that, motion stops being emphasis and becomes the page's texture.

## 2. The grammar — seven moves

Every move below names what it communicates, the primitive it uses, the layout,
the parameters that feel right, and the way it is abused. Six are generic; the
seventh, Stack, is a specific tested device that this repo ports rather than
reinvents.

### Build

**Communicates** that a structure was assembled in an order, and the order is
the argument.

**Primitive.** `Pinned` wrapping a figure with `driver="scroll"`; the figure
reads progress and maps stage boundaries onto it.

**Layout.** The figure fills the pinned viewport, captions and the numbered key
below it, out of the pin. The key is static: the reader must be able to check a
node against its timestamp without hunting for the scroll position that shows it.

**Parameters.** Pin height 2.5–4 viewport heights for three to five stages —
roughly 0.8vh of scroll per stage, never less than 0.6vh or the stage flashes
past. Stage boundaries evenly spaced in progress unless a stage is genuinely
heavier. Within a stage, strokes sweep over 400–700ms of eased progress, then
the fills and labels for that stage fade in on a 50–150ms stagger. Easing:
ease-out for entrances, nothing else.

**Abuse.** A Build whose stages do not correspond to stages in the transcript.
Cite the timestamp that opens each stage in the figure key; if you cannot, the
figure is one stage and wants no pin.

### Arrive

**Communicates** that a quantity has a size, at the moment the reader reaches it.

**Primitive.** `driver="reveal"` on the figure, or a `Scrub` bound to a one-shot
entry progress; the count or the bar length is the scrubbed value.

**Layout.** The number sits in normal flow, not pinned. Nothing else on the
screen moves while it counts.

**Parameters.** Fires when the element's top crosses into the middle third of
the viewport. Count or grow over 500–900ms; longer reads as a slot machine.
Counts land on the exact stated value, never a rounded one, and the final digits
must be legible for the last third of the animation. Fires **once** — a number
that recounts every time the reader passes it turns a fact into a toy.

**Abuse.** Counting a number the speaker gave loosely. If the transcript says
"a couple of hundred", the figure says "a couple of hundred" and does not count.
Counting implies precision you must have.

### Cross-fade

**Communicates** that one thing became another, and the differences are the
finding.

**Primitive.** `Pinned` with `Scrub` mapping progress to the opacity pair, or to
a single blend value the figure reads.

**Layout.** Both states occupy the same box, same dimensions, same field order,
same baselines — the before-and-after panel discipline from the diagrams skill,
stacked instead of side by side. Rows that do not change stay in `--ink-soft`
through the whole transition so the eye is not asked to re-read them.

**Parameters.** Pin height 1.5–2 viewport heights. The blend occupies the middle
60% of the pin, with a quarter of the span held at each end state so the reader
can stop and read either. Reversible by nature: scrolling up returns to the
before state.

**Abuse.** Cross-fading two things that are not the same object. If the panels
have different fields, this is a two-column comparison and belongs in the page
statically, side by side, where both are readable at once.

### Track

**Communicates** where the reader currently is on the call's time axis.

**Primitive.** `useScrollProgress` on the transcript container, feeding a sticky
mini strip chart; the marker position is the mapped progress.

**Layout.** A short strip chart — the page's own chart form at reduced height —
stuck to the top or bottom edge, full content width, under 64px tall. A single
hairline marker at the current position. The strip is clickable and draggable:
dragging scrubs the transcript to that time.

**Parameters.** The marker maps to elapsed seconds, not to scroll distance, so
it agrees with every timestamp on the page. Marker moves with no easing — it is
a position readout, and smoothing a position readout makes it lie. Appears when
the transcript section enters, disappears when it leaves; both over 150–200ms.

**Abuse.** A tracker on a section short enough to see whole. If the reader can
see the start and end of the thing being tracked, the tracker is decoration.
Second abuse: a tracker that also animates, pulses, or highlights — it has one
job.

### Chapter

**Communicates** how much argument there is and which part of it the reader is in.

**Primitive.** `useScrollProgress` on the document, or an intersection per
section; the rail marks the active one.

**Layout.** A thin vertical rail at the page margin, one short tick per section,
label on hover or focus, the active tick in `--ink` and the rest in `--grid`.
Under 900px the rail becomes a single hairline progress bar at the top edge with
no labels.

**Parameters.** Active state changes when a section's heading passes the top
third. Click jumps with `scroll-behavior: smooth`, and that smooth jump is the
only place the page is allowed to move the scroll position — because the reader
asked. Transition on the active mark 120–200ms.

**Abuse.** A rail with fifteen entries. Past about eight the rail is a table of
contents pretending to be a progress indicator; give the reader a real contents
list instead.

### Rest

**Communicates** that the previous move is over and can be thought about.

**Primitive.** None. That is the point.

**Layout.** Ordinary flow: prose, a static figure, a quote block, a table. At
least one full viewport height of undriven page.

**Parameters.** Every driven section is followed by a Rest before the next
driven section. Not a shorter rest for a shorter Build — the rest exists for the
reader's attention, not to balance the layout.

**Abuse.** Treating the Rest as leftover space and filling it with a small
decorative animation. A Rest with motion in it is not a Rest.

### Stack

**Communicates** that a sequence of peers is one sequence: each item arrives,
takes the reader's attention, then settles back under the next. Chapters,
case studies, the acts of a call.

**Primitive.** `ScrollStack` in `web/src/components/` — a port of the
stacking-cards device in the user's `scroll-stack` skill (framer-motion, ~150
lines, with tests). Each card is `position: sticky` at
`stickyTop + i * stackOffset`, with a runway of `scrollPerCard` viewport
heights; the covered card eases to `scale 0.94 / opacity 0.72` over the slice
of progress where the next card travels in. The last card never shrinks.

**Layout.** The cards are the section's existing items. The component takes
the pre-existing layout's classes as `compactClassName`, and that is the whole
safety mechanism: every visitor who does not get the stack gets the old layout
verbatim, so shipping the effect cannot regress a phone.

**Parameters.** `stickyTop 112`, `stackOffset 18`, `scrollPerCard 62` felt
right at 1600×1000 under a fixed nav. Whether a visitor gets the stack at all
is a pure, unit-tested function of viewport signals, not a media query:
`innerWidth <= 1366`, reduced motion, a coarse pointer, touch with no hover,
touch at or under 1920 wide, or four or fewer cores each route to the column.
Port that function and its test verbatim; the thresholds came from real
device complaints. First paint is always the column; the stack is swapped in
after mount, so place the section below the fold.

**Abuse.** More than one Stack on a page — five sections behaving identically
is one section shown five times. Porting a larger drag-physics engine because
it exists. Replacing the routing function with a breakpoint: reduced motion,
coarse pointers and low core counts are not widths.

## 3. Pacing

- **One Build per screen at most.** Two figures assembling in the same viewport
  compete, and the reader watches neither.
- **Never two pinned sections back to back.** A Rest goes between them, always.
- **Total pinned length never exceeds a third of the page.** Sum the pin heights
  in viewport units and compare against the page's total scroll height. Over a
  third, cut the least argumentative pin — not the pin heights, which only makes
  every move feel rushed.
- **A Build's stages map to real stages in the source.** Each stage cites the
  timestamp where the speaker introduced it, in the figure's numbered key.
  Splitting a figure into stages for effect is the same fault as inventing a
  connection between two boxes.
- **Reveal is one-way.** Nothing un-draws when the reader scrolls up. A Build
  that reverses forces the reader to re-earn what they already saw. The two
  exceptions are Cross-fade and Track, which are reversible by nature: a blend
  and a position readout are meaningless if they only run one way.

## 4. Motion discipline

The rules match the figure set, because they are the same figures moving.

- **Strokes sweep, fills and text fade, numbers count.** Those are the three
  motions. There is no fourth.
- **Nothing bounces, loops, or moves after it settles.** No spring easing, no
  attention pulses, no idle drift. A figure that has finished building is a
  static figure.
- **Stagger 50–150ms** between sibling elements in one stage. Under 50ms it
  reads as simultaneous, over 150ms as a queue.
- **Duration budget:** stroke sweeps 400–700ms, fades 200–350ms, counts
  500–900ms. Anything over a second is the page holding the reader up.
- **`prefers-reduced-motion` renders every driven section in its final state,
  with no pin.** Not a faster animation, not a fade — the pin is removed and the
  section becomes an ordinary static figure in flow. Check that the page still
  reads correctly this way, because for some readers this is the only version.
- **Keyboard users get the same content through normal flow.** Pinned sections
  stay in DOM order, every interactive element inside them is focusable and
  reachable in that order, and focusing an element inside a pinned section must
  not require the reader to have scrolled to a particular progress value. If a
  stage's content is only reachable by scrolling, it is not accessible content;
  put it in the key.
- **No content exists only in a driven state.** Every claim visible mid-Build is
  also present in the final state, the caption, or the key.

## 5. Performance floor

- **Transforms and opacity only.** Those are the two properties a compositor can
  animate without touching layout.
- **No layout-triggering property is scroll-linked.** Not `width`, `height`,
  `top`, `left`, `margin`, `font-size`, or anything that reads back a computed
  box. A bar that grows uses `transform: scaleX()` with its origin at the shared
  baseline, never an animated width.
- **The primitives handle passive listeners and rAF batching.** What you must
  still avoid: measuring inside render. No `getBoundingClientRect`,
  `offsetHeight`, or `getComputedStyle` in a component that re-renders on
  progress — measure once on mount and on resize, store it, and read the stored
  value. A single forced reflow per frame is enough to lose the frame budget.
- **Progress is a number, not a state cascade.** Driving a dozen React state
  updates per frame costs more than the animation. Prefer one value threaded
  down, and derive per-element values from it.
- **60fps on a 2020 laptop** is the floor, measured with the theme toggled and
  the transcript section rendered. Test the page with a performance trace, not
  by eye.
- **Degrade, do not break, on a phone.** At narrow widths the honest move is
  usually fewer driven sections, not the same sections compressed. A Build that
  needs three viewport heights on a desktop needs the same three on a phone, and
  a phone reader has less patience for them; drop the weakest one.

## 6. A worked plan for a one-hour readout

Sections in page order. Everything not listed is undriven.

**Chapter rail** — present for the whole document, seven ticks: abstract,
figures, acts, threads, evidence, transcript, next steps. Collapses to a top
hairline under 900px.

**1. The pipeline the call built** (figures section, second figure).
Move: *Build*. Pin height 3.2vh for four stages, each cited to the timestamp
where the speaker introduced it. Strokes sweep between stages, box fills and
labels stagger in at 90ms behind each sweep. The numbered key sits below the
pin, static, with all four timestamps visible from the start.

*Rest:* the bridge sentence and the next two static figures — a comparison and a
layered topology — read normally, roughly one and a half screens.

**2. The ratio the speaker wanted heard** (figures section, fifth figure).
Move: *Arrive*. No pin. Two bars on a shared baseline grow with `scaleX` when
the figure's top reaches the middle third; the values count alongside them over
700ms and stop at the exact stated numbers. Fires once.

*Rest:* the evidence table and the act summaries, static, about two screens.

**3. What the record looked like before and after** (the before/after figure).
Move: *Cross-fade*. Pin height 1.8vh. Both panels in one box, identical field
order; the four unchanged rows stay soft through the whole blend, the two
changed rows carry the second pen. A quarter of the pin holds each end state.
Reversible.

*Rest:* threads and tensions, static, one screen.

**4. The transcript** (the full transcript section).
Move: *Track*. A 56px strip chart sticks to the top edge for the length of the
section, marker mapped to elapsed seconds, draggable to scrub. It appears when
the section enters and leaves with it.

Total pinned: 3.2 + 1.8 = 5 viewport heights against a page that runs well past
fifteen. Comfortably inside the budget, with one Build, one Arrive, one
Cross-fade, one Track, and a Rest after each.

## 7. Self-check before declaring done

Run all of these. A failure is a fix, not a note.

1. **Reduced-motion pass.** Set the OS preference and reload. Every driven
   section renders complete, in flow, with no pin and no leftover blank space
   where a pin used to be. Read the page top to bottom in this state; it must
   make the same argument.
2. **Keyboard pass.** Tab from the top of the document to the bottom. Focus
   order matches reading order, nothing inside a pinned section is skipped or
   trapped, and no focused element is scrolled out of view by a pin.
3. **390px pass.** The body does not scroll sideways. Pinned sections still fit
   their viewport; figures that cannot fit scroll inside their own container.
   Count the driven sections and ask whether a phone reader wants all of them.
4. **Pinned-length budget.** Add up the pin heights in viewport units. Divide by
   the page's total scroll height in the same units. Over a third: cut a move.
5. **Stage-to-source check.** For each Build, open `work/turns.json` and confirm
   every stage boundary has a timestamp behind it. A stage with no source is
   deleted, not softened.
6. **Performance trace.** Record a scroll through each driven section. No frame
   over 16ms, no layout thrash, no scroll-linked style recalculation.
7. **"Would this be better as a static page?"** Answer honestly, in one
   sentence per driven section, saying what the motion communicated that the
   static figure could not. If any answer is about how it feels rather than what
   it shows, remove that move. A readout that survives this question with two
   driven sections instead of four is a better readout.
