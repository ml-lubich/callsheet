---
name: callsheet-diagrams
description: Author the figure set for a callsheet artifact — 8 to 12 publication-quality inline SVGs that carry the argument of a recorded conversation, so the prose only has to check them. Use after work/content.json validates and before callsheet build.
---

# Diagrams

You are writing `out/diagrams.html`: a fragment of inline `<figure class="dg">`
elements that `callsheet build` injects into the page at `<!--__DIAGRAMS__-->`.
No `<img>`, no raster, no libraries, no external requests — hand-written SVG
paths and one `<style>` block at the top of the fragment.

Read first: `work/content.json` (the analysis), `work/turns.json` (the ground
truth), `work/metrics.json` (the duration your time axes must use).

**The target is 8–12 figures for a one-hour call.** That is not a decoration
budget. It is the claim that most of what the call established is structural —
an order, a fan-out, a comparison, a magnitude — and structure read as a picture
in one pass costs the reader less than the same structure read as a paragraph.
The prose sections exist to be checked against the figures, not the reverse.

## When a diagram earns its place

The test: **does the picture show a structure the prose cannot carry in one
pass?** A reader holding four things in mind at once is being asked to render
the diagram themselves. Draw it for them.

Earns it:

- Something branches, fans out, or rejoins. Prose has to say "meanwhile" and
  hope.
- Two or more quantities are being compared and the *ratio* is the point.
- The thing has a position — in time, in a two-axis space, in a layer stack —
  and the position is what the speaker was arguing about.
- Two states of one object (before/after, theirs/ours) differ in several places
  at once, and the pattern of differences is the finding.
- The same shape recurs across three or four cases, and the reader should see
  the shape is the same.
- Something was described across four scattered stretches of the call and has
  never been seen whole. Assembling it is the contribution.

Does not earn it:

- A bulleted list with boxes drawn around each bullet.
- A single relationship. "A causes B" is a sentence.
- A restatement of the act structure — the page already plots that on its time
  axis; a second copy is noise.
- Anything whose labels do the work while the geometry is arbitrary. If the
  boxes could be shuffled without loss, it is a list.
- A picture of a thing that was mentioned rather than explained. If the
  transcript does not say how the parts connect, you do not know, and inventing
  the connective tissue is fabrication wearing a diagram's clothes.

When in doubt, count the nodes. Under four and it is a sentence; over about
sixteen and the reader stops reading and starts scanning. Split it.

## The catalog

Twelve shapes. Pick by the structure in the conversation, never by variety —
if a call is genuinely four pipelines, draw four pipelines and let the bridges
carry the difference.

Every sketch below is drawn at the scale you should think in: a `viewBox` around
`0 0 880 N`, boxes 156×72, gutters of 32–48, one text baseline every 13–17 units.

### 1. Pipeline with grouped bands

**Fits** a process described as a sequence where some stages belong together
under a name the speaker used ("the retrieval side", "everything before the
gate").

```
  ┌───────┐   ┌ ─ GROUPED BAND ─ ─ ─ ─ ─ ─ ─ ─ ┐
  │ input │──▶  ┌──────┐  ┌──────┐  ┌──────┐     ──▶ ┌────────┐
  └───────┘   │ │ 2    │  │ 3    │  │ 4    │   │     │ output │
              │ └──┬───┘  └──┬───┘  └──┬───┘   │     └────────┘
              └ ─ ─┼─ ─ ─ ─ ─┼─ ─ ─ ─ ─┼─ ─ ─ ─┘
                   └─────────┴─────────┘  join
```

**Coordinates.** Pick a stage pitch (188 = 156 box + 32 gutter) and never
deviate; every box lands on `x = 16 + 188k`. Bands are `<rect class="frame">`
inset 12 outside the boxes they contain, with their label at `y = band.y + 17`.
Edges are `<path>` with only horizontal and vertical segments — one corner per
turn, no diagonals, no curves. A merge is two edges into a shared point, then
one edge onward.

**Failure mode.** Edges routed through boxes, or a band that hugs its contents so
tightly it reads as a border. The tell of an amateur pipeline is diagonal
arrows: they say the author let a layout engine decide and never looked.

### 2. Economics or causal network

**Fits** an argument where cost, risk or delay accumulates, and where *where a
node sits* is the claim: causes left, consequences right, or driver above,
absorber below.

```
   drivers            multiplier          what it costs
   ┌──────┐
   │ vol. │──┐
   └──────┘  ├──▶ ┌──────────┐ ──▶  ┌──────────────┐
   ┌──────┐  │    │ per-unit │      │  annual load  │
   │ rate │──┘    └──────────┘      └──────────────┘
   └──────┘             ▲
                   ┌────┴────┐
                   │ the one │   ← the node the speaker disputed
                   │ number  │
                   └─────────┘
```

**Coordinates.** Three or four columns at fixed x, free y. Vertical order inside
a column must mean something (magnitude, or who raised it) and you must say what
in the `<desc>`. Put the disputed or load-bearing node off the main row so the
eye lands on it.

**Failure mode.** A hub-and-spoke blob where every node touches every other. If
you cannot state the reading direction in one clause, it is not a causal diagram,
it is a word cloud with lines.

### 3. Two-column comparison with the axis of difference between

**Fits** two regimes — before/after, their approach/ours, what was hired for/what
is done — that differ along several named dimensions.

```
      TODAY                 dimension                 PROPOSED
   ┌──────────┐        ─────────────────         ┌──────────┐
   │ manual   │◀─────      who decides      ─────▶│ gated    │
   └──────────┘        ─────────────────         └──────────┘
   ┌──────────┐        ─────────────────         ┌──────────┐
   │ 2 hours  │◀─────      how long         ─────▶│ minutes  │
   └──────────┘        ─────────────────         └──────────┘
```

**Coordinates.** A centre line at `x = width/2`. Left column right-aligned to
`centre - 120`, right column left-aligned to `centre + 120`, the dimension label
centred in the gutter on the same baseline as both. Rows at a fixed pitch.

**Failure mode.** The gutter left empty, or filled with a bare arrow. The gutter
is the whole idea: without a named dimension per row the reader cannot tell what
is being compared and reads two unrelated lists. Second failure: unequal box
widths between the columns, which reads as a verdict you did not earn.

### 4. Layered topology with parallel lanes

**Fits** a system described in tiers where several things happen at the same
level and the level itself has a name.

```
  ═══ interface ══════════════════════════════════════
     │ intake │        │ status page │
  ═══ logic ══════════════════════════════════════════
     │ router │──│ scorer │──│ gate │
  ═══ store ══════════════════════════════════════════
     │ cases │          │ index │        │ audit log │
```

**Coordinates.** Lanes are full-width `<rect class="frame">` of equal height,
stacked at a fixed pitch, labelled at the left edge in the small caps class.
Members sit on the lane's centre line. Cross-lane dependencies are strictly
vertical; same-lane relations strictly horizontal. That single rule is what makes
a layer diagram readable at a glance.

**Failure mode.** A member that spans two lanes because it "sort of does both".
Pick a lane and say the ambiguity in the caption. Also: lanes of different
heights, which implies an importance ranking you did not mean.

### 5. Timeline with events on a real axis

**Fits** anything where *when* is the argument — when a concession appeared, how
long a silence ran, how late the real topic surfaced.

```
  00:00                        00:30                       01:07
  ├────────────┬─────────────────┬──────────┬────────────────┤
               ▲                 ▲          ▲
            first             the turn    the ask
            number             (00:31:40)
  ░░░░░░░░░░░░░░░░  act I  ░░░░░░░  act II  ░░░░░░░░░░░░░░░░░
```

**Coordinates.** `x = pad + (s / duration_s) * (width - 2*pad)` and nothing else,
ever. `duration_s` comes from `metrics.json`. Ticks every five or ten minutes,
labelled, 0.5px. Events above the axis, act bands below it, so the two never
fight. If two events collide, stagger their labels vertically and draw a 1px
leader down to the axis — never nudge the mark off its true position.

**Failure mode.** Even spacing. The moment you space events evenly you have
thrown away the only information the shape carried, and a reader who checks two
timestamps against the axis will catch you.

### 6. Matrix or quadrant

**Fits** items scored on two independent dimensions the speakers actually named.

```
   high │  ·rush         │  ·flagged
        │                │
  effort├────────────────┼────────────────
        │  ·routine      │  ·audit
    low │                │
        └────────────────┴────────────────
           low        value        high
```

**Coordinates.** A square plot area — equal width and height in user units, or
the visual weighting lies. Axis labels at the ends of each axis, not floating.
Place each item at coordinates you can defend from a quote; if the transcript
only supports "more than the other one", use rank order and say so in the
`<desc>`.

**Failure mode.** Inventing precision. A quadrant chart implies you measured
both axes. If you did not, either draw ranks on an unlabelled scale or pick a
different shape. Second failure: an empty quadrant left unremarked — if nothing
is cheap and valuable, that absence is a finding and belongs in the caption.

### 7. Before-and-after of one concrete record

**Fits** a transformation whose value is invisible in the abstract: the same
ticket, row, or form, drawn twice.

```
   ┌ as it arrives ────────┐        ┌ as it leaves ──────────┐
   │ id      4471          │        │ id      4471           │
   │ model   —             │  ──▶   │ model   XR-90   ← new  │
   │ fault   "not working" │        │ fault   seal, thermal   │
   │ route   —             │        │ route   L2      ← new  │
   └───────────────────────┘        └────────────────────────┘
```

**Coordinates.** Two identical panels, same width, same field order, same
baselines, so a changed row is the only thing that moves. Mark changed rows in
the second pen and leave unchanged rows in `--ink-soft`. Field labels in one
column, values in another, both left-aligned on fixed x.

**Failure mode.** A fabricated record. Every field value must be traceable to
something said; if the call named three fields, show three fields and label the
panel honestly rather than padding it to look like a real screen. Second
failure: reordering fields between panels, which destroys the comparison.

### 8. Decision tree or escalation cascade

**Fits** a described set of gates: what happens when a check passes, and what
happens when it does not.

```
              ┌ confidence high? ┐
              └────┬────────┬────┘
                yes│        │no
           ┌───────▼──┐  ┌──▼────────────┐
           │ auto-file│  │ second check  │
           └──────────┘  └───┬───────┬───┘
                          yes│       │no
                    ┌────────▼┐   ┌──▼──────┐
                    │ queue   │   │ human   │
                    └─────────┘   └─────────┘
```

**Coordinates.** Depth is y at a fixed pitch; siblings share a y. Every branch
edge is labelled with its condition at the midpoint of its first segment — an
unlabelled branch is a guess. The failure path goes consistently one way (right,
say) at every level, so the reader learns the direction once.

**Failure mode.** Missing the terminal states. A cascade that stops at the last
gate leaves the reader asking what actually happens; every leaf must be an
outcome, including the boring one. Second failure: branch labels that are not
the speaker's conditions.

### 9. Small multiples of one shape

**Fits** three to six cases that share a structure, where sameness is the point:
each thread's arc, each participant's version of the same week.

```
   case A          case B          case C
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ ▁▃▅▂     │   │ ▁▁▇▇     │   │ ▅▁▁▁     │
  └──────────┘   └──────────┘   └──────────┘
   opens early    late spike     front-loaded
```

**Coordinates.** One cell template, cloned on a strict grid; identical scales in
every cell — this is the entire discipline of small multiples. Label the shared
scale once, at the left, not in every cell. Three or four across, wrapping to a
second row rather than shrinking.

**Failure mode.** Per-cell scaling, which makes every case look identical and
silently deletes the finding. Second failure: too many cells; past six the form
turns into a texture.

### 10. Magnitude comparison where the geometry is the argument

**Fits** a claim of the form "this is much larger than that" — where the ratio,
not the value, is what the speaker wanted heard.

```
  what closes by itself   ████████████████████████████ 4/5
  what needs building     ███████ 1/5
  ──────────────────────────────────────────────────── shared baseline
```

**Coordinates.** Length encodes value, always from a shared zero baseline.
Bars of equal thickness. If you must use area, scale by the square root of the
value and say in the `<desc>` that you did — otherwise a 4× value looks 16×.

**Failure mode.** A truncated axis. Starting bars at anything but zero to "show
the difference better" is the oldest lie in charting and the one a hostile reader
checks first. Second failure: a magnitude figure with no number anywhere — give
the value in the label, since the picture is the emphasis and the label is the
evidence.

### 11. Feedback loop with a return edge

**Fits** a process whose closing edge is the finding: output re-enters as input,
and the speaker's point was the cycle time or the drift.

```
    ┌────────┐     ┌─────────┐     ┌──────────┐
    │ action │ ──▶ │ measure │ ──▶ │ adjust   │
    └───▲────┘     └─────────┘     └────┬─────┘
        └───────────── 6 weeks ─────────┘
```

**Coordinates.** Lay the forward path on one straight line and route the return
edge below it as a single three-segment path, clearly longer than any forward
edge. Label the return edge with its cost — the lag, the loss, the rework —
because that label is the reason the figure exists.

**Failure mode.** Drawing the loop as a circle. A circle makes every step look
equidistant and hides which edge is the expensive one. Second failure: an
unlabelled return edge, which reduces the figure to "things are connected".

### 12. Composition bar

**Fits** one whole that splits into named parts, where the split was disputed or
surprising.

```
  a working day
  ├──────────── triage ─────────────┼── fixes ──┼─ meetings ─┤
  │              62%                │    24%    │    14%     │
```

**Coordinates.** One bar, full width, segments proportional to value, segment
boundaries on exact fractions of the bar width. Label inside the segment when it
fits, on a leader line below when it does not. Order segments largest-first
unless a natural order (time of day, stage) exists — then keep the natural one
and say which in the `<desc>`.

**Failure mode.** Parts that do not sum to the whole. If the transcript accounts
for 80%, draw a `--grid`-hatched remainder labelled "unaccounted" rather than
inflating the parts. Second failure: using this for things that are not parts of
one whole — that is a magnitude comparison, kind 10.

## House style — hard rules

**Colour.** Every colour is a CSS variable, always. The permitted set is
`--ink`, `--ink-soft`, `--grid`, `--pen-a`, `--pen-b`, `--paper`, `--paper-2`.
Never a literal hex, never `fill="white"`, never `fill="black"`, never a named
colour, never `rgb()`. The page ships light and dark palettes and a toggle; a
literal colour is a figure that goes invisible for half your readers.

**Colour means one thing.** Assign one pen per speaker or per actor at the start
and hold it across all twelve figures: `--pen-a` is the same person in figure 1
and figure 11. Structure the reader cannot attribute is structure they cannot
trust. Use `--ink-soft` for anything unattributed or shared. If a figure has no
attribution axis, draw it entirely in one pen and say why in the `<desc>`.

**Type.** No monospace anywhere — not for labels, not for timestamps, not for
identifiers. Timestamps use the condensed face with `font-variant-numeric:
tabular-nums`. Node labels are **five words or fewer**; the note under a node is
**twelve words or fewer**. Anything longer belongs in the caption. Nothing below
10px.

**Line.** Strokes 1–1.5px for structure, 0.5px for the hairline grid and axes.
No shadows. No gradients. No `border-radius` or `rx` above 2. No emoji, no icon
glyphs, no clip art. Fill boxes with `--paper-2` and stroke them with the pen —
never fill a box with a pen colour and put text on top of it.

**Marker ids are per-figure.** Every `<marker>` id is prefixed with the figure's
id: `mk-<figure-id>-a`. All figures land in one document, ids are global, and a
collision silently repaints every arrowhead on the page with the first
definition it finds. This is the most common way a set of individually correct
figures breaks once assembled.

**Every figure carries:**

```html
<figure class="dg" id="dg-short-slug">
  <figcaption>
    <span class="dg-t">A title that states the finding, not the topic</span>
    <span class="dg-w">One or two sentences: what to look at, and what it means.</span>
  </figcaption>
  <div class="dg-scroll">
    <svg viewBox="0 0 880 520" role="img" preserveAspectRatio="xMidYMid meet"
         style="width:100%;height:auto;min-width:880px">
      <title>Short accessible name</title>
      <desc>What the figure shows, read in its reading order, including what
        position and colour encode.</desc>
      <defs><marker id="mk-short-slug-a" …>…</marker></defs>
      …
    </svg>
  </div>
  <ol class="dg-key">
    <li><b>Node label</b> <span>00:14:22</span></li>
    …
  </ol>
</figure>
```

The numbered key is not optional. Each numbered node in the figure gets one
entry giving the timestamp where it was said. That key is what makes a diagram
checkable, and it is the first thing the verifier reads.

## Composition — the set is one argument

Individually dense figures that do not compose is the specific failure this
section exists to prevent. Twelve good diagrams in arbitrary order is a gallery,
and a reader gets nothing from a gallery that they could not get from the
transcript.

- Open the fragment with a **lead-in** (`<div class="dg-lead">`) that names the
  sequence: what the first figure establishes, what each one after it does to
  that. Three or four sentences. If you cannot write it, the set has no order and
  you should reorder it until you can.
- Between consecutive figures, one **bridge** sentence (`<p class="dg-bridge">`)
  that carries the reader from what they just saw to why the next figure follows.
  A bridge states a consequence or a question, never a summary. "Which raises the
  question of what it costs" is a bridge; "the next figure shows costs" is a
  label.
- Sequence by argument, not by chronology. The call wandered; the figures should
  not.
- Each figure must survive being read alone — caption, key and `<desc>` carry it
  — while still sitting in the sequence.

## Responsiveness

Each figure must be legible at 390px wide. Either design it to that width, or
wrap the `<svg>` in `<div class="dg-scroll">` with `overflow-x:auto` and give the
svg `min-width` equal to its viewBox width. The figure scrolls; the page body
must never scroll horizontally. The `dg-key` collapses to one column under
640px.

## The self-check before declaring done

Run every one of these. A failure is a fix, not a note.

```
callsheet lint-diagrams out/diagrams.html --turns work/turns.json
```

That covers well-formedness, literal hex colours, monospace, `fill="white"` and
`fill="black"`, marker ids reused across figures, a figure missing `role="img"`,
`<title>` or `<desc>`, a figure with no numbered key, text below 10px, and every
cited timestamp resolving to a real turn. It exits nonzero and names each fault.

Then check by hand what a linter cannot:

1. **Build and open the page.** `callsheet build … --diagrams out/diagrams.html`
   reports external requests; that number must be zero.
2. **Toggle the theme.** Every stroke, fill and label must remain legible in both.
   A figure that disappears in dark mode has a hard-coded colour the grep missed.
3. **Narrow to 390px.** The page body does not scroll sideways. Each figure
   either fits or scrolls inside its own container.
4. **Read only the captions and bridges, in order.** They must form a coherent
   argument on their own. If they do not, the set is a gallery.
5. **Pick three nodes at random and find them in `work/turns.json`.** Not the
   timestamp — the *claim*. A node whose content is not in the transcript is
   deleted, not softened.
6. **Count words in the longest label.** Over five, rewrite it.
7. **Check one pen means one actor** across the whole set.
