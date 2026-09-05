---
name: callsheet-diagrams
description: Author the figure set for a callsheet artifact — 8 to 12 publication-quality inline SVGs that carry the argument of a recorded conversation, so the prose only has to check them. Use after work/content.json validates and before callsheet build.
---

# Diagrams

## The glyph-first rule

**The node shows the property. The label only names it.**

A box whose entire content is words is a list item wearing a border. What separates
an amateur figure from a professional one is that in the professional one every node
contains a miniature drawing of the thing being claimed, so the claim is visible
before it is read. The same node, twice — label-only:
```html
<svg viewBox="0 0 180 60" role="img"><title>Label-only node</title>
  <rect x="1" y="1" width="178" height="58" fill="var(--paper-2)" stroke="var(--pen-a)"/>
  <text x="12" y="26" font-size="13" fill="var(--ink)">Lexical index</text>
  <text x="12" y="44" font-size="10" fill="var(--ink-soft)">unbounded scores</text>
</svg>
```
Glyph-first:
```html
<svg viewBox="0 0 180 60" role="img"><title>Glyph-first node</title>
  <rect x="1" y="1" width="178" height="58" fill="var(--paper-2)" stroke="var(--pen-a)"/>
  <text x="12" y="19" font-size="13" fill="var(--ink)">Lexical index</text>
  <rect x="12" y="29" width="138" height="9" fill="var(--pen-b)"/>
  <text x="154" y="38" font-size="12" fill="var(--pen-b)">≫</text>
  <text x="12" y="52" font-size="10" fill="var(--ink-soft)">unbounded</text>
</svg>
```
Six more units of ink, and "unbounded" is now something the reader sees before reading
it, and can compare at a glance against the bounded index above it. Before drawing any
node, answer: **what property of this thing is the argument, and what is the smallest
picture of that property?** If the answer is "none, it is just a stage in a sequence",
the node is a plain box and the sequence is the glyph. Four plain boxes in a row is a list.

## What you are writing

`out/diagrams.html`: a fragment of inline `<figure class="dg">` elements that `callsheet
build` injects at the `__DIAGRAMS__` marker. No `<img>`, no raster, no libraries, no
external requests — hand-written paths and one `<style>` block at the top of the fragment.
Read first: `work/content.json` (the analysis), `work/turns.json` (ground truth),
`work/metrics.json` (the duration your time axes must use). **Target 8–12 figures for a
one-hour call.** The prose exists to be checked against the figures, not the reverse.

## When a diagram earns its place

The test: **does the picture show a structure the prose cannot carry in one pass?** A
reader holding four things in mind at once is being asked to render the diagram themselves.

Earns it: something branches, fans out or rejoins; two quantities are compared and the
*ratio* is the point; a thing has a position — in time, in a two-axis space, in a layer
stack — that is what was argued about; two states of one object differ in several places
and the pattern is the finding; one shape recurs across three or four cases; something
described across four scattered stretches has never been seen whole.

Does not earn it: a bulleted list with boxes round each bullet; a single relationship,
which is a sentence; a restatement of the act structure the page already plots; anything
whose labels do the work while the geometry is arbitrary — if the boxes could be shuffled
without loss, it is a list; a thing mentioned rather than explained, where inventing the
connective tissue is fabrication wearing a diagram's clothes. Under four nodes it is a
sentence; over about sixteen the reader starts scanning — split it.

## The glyph vocabulary

Each snippet uses only the page CSS variables. Scale the container, never the decoration.

### 1. Score-scale bar — bounded, unbounded, own scale
Shows that two quantities are **not on the same scale**, before a label says so.
```html
<svg viewBox="0 0 120 62" role="img"><title>Three score scales</title>
  <rect x="0" y="4" width="96" height="8" fill="var(--paper-2)" stroke="var(--grid)"/>
  <rect x="0" y="4" width="62" height="8" fill="var(--pen-a)"/>
  <rect x="0" y="26" width="90" height="8" fill="var(--pen-b)"/>
  <text x="96" y="35" font-size="12" fill="var(--pen-b)">≫</text>
  <rect x="30" y="48" width="66" height="8" fill="var(--paper-2)" stroke="var(--grid)"/>
  <rect x="30" y="48" width="28" height="8" fill="var(--ink-soft)"/>
</svg>
```
Bounded gets a track with both ends fixed; unbounded gets **no** track and runs into a `≫`;
own-scale starts elsewhere. Fails when all three share a track, asserting the opposite.

### 2. Record field — empty, filled, cited
Shows a record going from unactionable to actionable, as fields not prose.
```html
<svg viewBox="0 0 160 56" role="img"><title>Record fields</title>
  <text x="0" y="12" font-size="10" fill="var(--ink-soft)">source</text>
  <rect x="48" y="4" width="104" height="9" fill="none" stroke="var(--grid)" stroke-dasharray="3 3"/>
  <text x="0" y="32" font-size="10" fill="var(--ink)">source</text>
  <rect x="48" y="24" width="72" height="9" fill="var(--pen-a)"/>
  <text x="0" y="52" font-size="10" fill="var(--ink)">source</text>
  <rect x="48" y="44" width="88" height="9" fill="var(--pen-a)"/>
  <circle cx="146" cy="48" r="2.5" fill="var(--pen-b)"/>
</svg>
```
The dot is provenance. Fails when panels reorder or drop fields, killing the comparison.

### 3. Document with text lines and a badge
Shows an unstructured input and what had to be done to read it.
```html
<svg viewBox="0 0 96 78" role="img"><title>Scanned document</title>
  <path d="M2 2h58l14 14v60H2Z" fill="var(--paper-2)" stroke="var(--ink-soft)"/>
  <path d="M60 2v14h14" fill="none" stroke="var(--ink-soft)"/>
  <path d="M12 32h52M12 42h52M12 52h34" stroke="var(--grid)" stroke-width="3"/>
  <rect x="12" y="60" width="32" height="12" rx="2" fill="none" stroke="var(--pen-b)"/>
  <text x="16" y="69" font-size="8" fill="var(--pen-b)">OCR</text>
</svg>
```
Fails when every document gets the badge: it means "this one needed extra", so on all, nothing.

### 4. Person
Shows that a step is a human step. Never a photograph, never an emoji.
```html
<svg viewBox="0 0 40 44" role="img"><title>Person</title>
  <circle cx="20" cy="12" r="7" fill="none" stroke="var(--pen-b)" stroke-width="1.5"/>
  <path d="M6 40c0-9 6.3-14 14-14s14 5 14 14" fill="none" stroke="var(--pen-b)" stroke-width="1.5"/>
</svg>
```
Fails when used decoratively beside a machine step, erasing its one distinction.

### 5. Gate chain
Shows a deterministic sequence of checks — diamonds, because each can reject.
```html
<svg viewBox="0 0 150 32" role="img"><title>Chain of gates</title>
  <path d="M4 16 20 6 36 16 20 26Z M46 16 62 6 78 16 62 26Z M88 16 104 6 120 16 104 26Z"
        fill="var(--paper-2)" stroke="var(--pen-a)"/>
  <path d="M36 16h10M78 16h10M120 16h20" fill="none" stroke="var(--ink-soft)"/>
  <path d="M134 12l6 4-6 4Z" fill="var(--ink-soft)"/>
</svg>
```
Fails when drawn as rounded boxes: that reads as "steps" and loses the claim of rejection.

### 6. Escalation cascade
Shows cheap-first, expensive-last as a line stepping *down*, so cost is a direction.
```html
<svg viewBox="0 0 150 60" role="img"><title>Escalation cascade</title>
  <path d="M2 10h40v18h40v18h44" fill="none" stroke="var(--pen-b)" stroke-width="1.5"/>
  <circle cx="42" cy="10" r="2.5" fill="var(--pen-b)"/>
  <circle cx="82" cy="28" r="2.5" fill="var(--pen-b)"/>
  <circle cx="126" cy="46" r="2.5" fill="var(--pen-b)"/>
  <text x="2" y="8" font-size="8" fill="var(--ink-soft)">cheap</text>
  <text x="108" y="58" font-size="8" fill="var(--ink-soft)">costly</text>
</svg>
```
Fails when risers are even; uneven risers show which escalation actually hurts.

### 7. Magnitude bar at true proportion
Shows the ratio. Shared zero, equal thickness, no truncated axis, ever.
```html
<svg viewBox="0 0 320 54" role="img"><title>Magnitudes at true proportion</title>
  <path d="M60 4v46" stroke="var(--grid)"/>
  <rect x="60" y="6" width="190" height="10" fill="var(--pen-a)"/>
  <text x="256" y="15" font-size="11" fill="var(--pen-a)">119,000</text>
  <rect x="60" y="24" width="1" height="10" fill="var(--pen-b)"/>
  <text x="66" y="33" font-size="11" fill="var(--pen-b)">25</text>
  <rect x="60" y="42" width="7" height="10" fill="var(--ink-soft)"/>
  <text x="73" y="51" font-size="11" fill="var(--ink-soft)">4,000</text>
</svg>
```
A one-unit bar is correct and is the point. Widening it "so it shows" is the lie this prevents.

### 8. Big number with its unit
Shows a figure the speaker wanted heard: large, in a pen, unit small beside it.
```html
<svg viewBox="0 0 200 46" role="img"><title>Headline figure</title>
  <text x="0" y="30" font-size="30" font-weight="600" fill="var(--pen-b)">$237K</text>
  <text x="106" y="30" font-size="10" fill="var(--ink-soft)">/ yr at this volume</text>
  <text x="0" y="43" font-size="10" fill="var(--ink)">saved</text>
</svg>
```
Fails when every number is set large. Two or three per figure set, no more.

### 9. Compare node
Shows two things measured against each other, meeting at a symbol, delta leaving right.
```html
<svg viewBox="0 0 150 60" role="img"><title>Two readings compared</title>
  <path d="M2 12h44l22 16M2 48h44l22-16" fill="none" stroke="var(--ink-soft)"/>
  <circle cx="76" cy="30" r="9" fill="var(--paper)" stroke="var(--ink)"/>
  <path d="M70 30h12M76 24v12" stroke="var(--ink)"/>
  <path d="M85 30h38" fill="none" stroke="var(--pen-a)"/>
  <path d="M117 26l6 4-6 4Z" fill="var(--pen-a)"/>
  <text x="0" y="59" font-size="8" fill="var(--ink-soft)">compare</text>
</svg>
```
Fails when both inputs use one pen. They are the two things being told apart.

### 10. Route fan-out
Shows one thing becoming several real destinations — arrows to boxes that exist.
```html
<svg viewBox="0 0 170 74" role="img"><title>Fan-out to destinations</title>
  <rect x="0" y="26" width="46" height="22" fill="var(--paper-2)" stroke="var(--pen-a)"/>
  <path d="M46 37h22V10h32M68 37h32M68 37v27h32" fill="none" stroke="var(--ink-soft)"/>
  <rect x="104" y="2" width="62" height="16" fill="none" stroke="var(--grid)"/>
  <rect x="104" y="29" width="62" height="16" fill="none" stroke="var(--grid)"/>
  <rect x="104" y="56" width="62" height="16" fill="none" stroke="var(--grid)"/>
</svg>
```
Fails when the fan ends in a label like "3 queues" instead of three shapes.

### 11. Rejected option
Shows the path not taken, still on the page — what was ruled out is half the argument.
```html
<svg viewBox="0 0 150 34" role="img"><title>Rejected option</title>
  <rect x="1" y="1" width="130" height="30" fill="var(--paper-2)" stroke="var(--grid)"/>
  <text x="10" y="20" font-size="11" fill="var(--ink-soft)">vendor quote</text>
  <path d="M10 16h72" stroke="var(--ink-soft)"/>
  <path d="M133 8l13 12M146 8l-13 12" stroke="var(--pen-b)" stroke-width="1.5"/>
</svg>
```
Fails when the node is deleted instead of struck: the reader cannot tell it was considered.

### 12. Timeline tick on a shared axis
Shows *when*. Position is computed from real seconds, never spaced by hand.
```html
<svg viewBox="0 0 300 46" role="img"><title>Events on one shared axis</title>
  <path d="M8 30h284" stroke="var(--ink-soft)" stroke-width="0.5"/>
  <path d="M8 27v6M104 27v6M200 27v6M292 27v6" stroke="var(--grid)" stroke-width="0.5"/>
  <path d="M64 18v12M77 24v6M223 12v18" stroke="var(--pen-a)"/>
  <circle cx="64" cy="18" r="2.5" fill="var(--pen-a)"/>
  <circle cx="77" cy="24" r="2.5" fill="var(--pen-a)"/>
  <circle cx="223" cy="12" r="2.5" fill="var(--pen-a)"/>
  <text x="8" y="44" font-size="9" fill="var(--ink-soft)">00:00</text>
  <text x="266" y="44" font-size="9" fill="var(--ink-soft)">01:07</text>
</svg>
```
`x = pad + (s / duration_s) * (width - 2*pad)`, `duration_s` from `metrics.json`. Colliding
events get staggered leaders, never nudged positions. Even spacing throws the shape away.

### 13. Small-multiple frame
Shows that the same shape recurs. One cell template, one shared scale.
```html
<svg viewBox="0 0 300 62" role="img"><title>Small multiples on one scale</title>
  <g fill="none" stroke="var(--grid)">
    <rect x="1" y="11" width="92" height="40"/><rect x="103" y="11" width="92" height="40"/>
    <rect x="205" y="11" width="92" height="40"/>
  </g>
  <g fill="none" stroke="var(--pen-a)">
    <path d="M9 45l18-14 18 8 18-22"/><path d="M111 45l18-3 18-2 18-26"/>
    <path d="M213 45l18-26 18 6 18 4"/>
  </g>
  <text x="1" y="8" font-size="9" fill="var(--ink-soft)">A</text>
  <text x="103" y="8" font-size="9" fill="var(--ink-soft)">B</text>
  <text x="205" y="8" font-size="9" fill="var(--ink-soft)">C</text>
</svg>
```
Fails on per-cell scaling: every case then looks identical. Past six cells it is a texture.

### 14. State machine with a return edge
Shows that the loop closes, and what the closing edge costs.
```html
<svg viewBox="0 0 250 70" role="img"><title>Cycle with a costly return edge</title>
  <g fill="var(--paper-2)" stroke="var(--pen-a)">
    <rect x="1" y="8" width="62" height="26"/><rect x="93" y="8" width="62" height="26"/>
    <rect x="185" y="8" width="62" height="26"/>
  </g>
  <path d="M63 21h26M155 21h26" fill="none" stroke="var(--ink-soft)"/>
  <path d="M216 34v24H36v-24" fill="none" stroke="var(--pen-b)" stroke-dasharray="4 3"/>
  <path d="M33 40l3-6 3 6Z" fill="var(--pen-b)"/>
  <text x="96" y="54" font-size="9" fill="var(--pen-b)">6 weeks</text>
</svg>
```
Never a circle: it makes every step look equidistant and hides which edge is expensive. An
unlabelled return edge reduces the figure to "things are connected".

### 15. Composition strip
Shows one whole splitting into named parts, including the part you cannot account for.
```html
<svg viewBox="0 0 300 34" role="img"><title>One whole, named parts</title>
  <rect x="0" y="4" width="186" height="14" fill="var(--pen-a)"/>
  <rect x="186" y="4" width="72" height="14" fill="var(--pen-b)"/>
  <rect x="258" y="4" width="41" height="14" fill="none" stroke="var(--grid)"/>
  <text x="2" y="30" font-size="9" fill="var(--ink-soft)">triage 62%</text>
  <text x="190" y="30" font-size="9" fill="var(--ink-soft)">fixes 24%</text>
</svg>
```
The open segment is the remainder. Fails when parts are inflated to sum, or are not parts.

## Composition: one dense surface, not a gallery

A professional information graphic is **one surface**, read top to bottom, with section
rules between bands of related panels. Adjacency is itself an argument: two glyphs on one
row are compared whether you say so or not.

- **Bands, not figures.** Group panels into horizontal bands, each with a small caps label
  sitting on a 0.5px full-width rule at the band top, left-aligned.
- **One gutter value.** Pick one (32 or 40) and use it between every panel and every band.
  Uneven gutters are the loudest amateur tell there is.
- **Share the axis.** Two panels in a band that both encode magnitude share a zero and a
  scale, labelled once; if they encode time, they share the axis and the pixels-per-second.
- **Reading order is the argument.** Band 1 states the thing, band 2 its cost, band 3 the
  alternative, band 4 the evidence. If you cannot say your band order as four clauses of
  one sentence, reorder until you can.
- **Numbered badges run in reading order** across the whole surface, top-right of each
  panel, feeding one key at the bottom.

Split into separate figures only when panels genuinely do not share an argument —
different subject, time frame, actors. That is rare; the default is one surface.

## Motion

Motion has exactly one job: enforce reading order on the first pass. After the reveal, the
figure is still. **Draw-on follows reading order**, not render order: strokes sweep first,
then fills and text fade in behind them, then numbers count up — stagger with `--d`.
**Nothing moves after the reveal**: no loops, no bounce, no hover motion, no parallax, no
pulsing arrowheads. Whole surface under 1.2s; a reader who scrolls back sees a finished
figure, not a replay. `pathLength="1"` normalises every path to length 1, so one dash
pattern draws any path without measuring it:

```css
.dg [data-draw]{ stroke-dasharray:1; stroke-dashoffset:1;
  animation:dg-draw .45s ease-out var(--d,0s) forwards }
@keyframes dg-draw{ to{ stroke-dashoffset:0 } }
.dg [data-fade]{ opacity:0; animation:dg-fade .3s ease var(--d,0s) forwards }
@keyframes dg-fade{ to{ opacity:1 } }
@media (prefers-reduced-motion:reduce){
  .dg [data-draw],.dg [data-fade]{ animation:none; stroke-dashoffset:0; opacity:1 }
}
```

Usage: `<path pathLength="1" data-draw style="--d:.15s" d="…"/>`. The
reduced-motion block is not optional, and must leave the figure in its final
state rather than hidden.

## Worked example

Copy this one. Three indexes score on scales that cannot be added; rank normalisation is what
makes fusion legal. Every node is a glyph.

```html
<figure class="dg" id="dg-fuse">
  <figcaption>
    <span class="dg-t">Three indexes, three scales, one comparable order</span>
    <span class="dg-w">Read the middle column before the labels: one bar has a
      track with both ends fixed, one has no track and runs off the panel, one
      has a track that starts somewhere else. The right column is the same three
      after rank normalisation — that is all fusion does, and why it works.</span>
  </figcaption>
  <div class="dg-scroll">
    <svg viewBox="0 0 880 268" role="img" preserveAspectRatio="xMidYMid meet"
         style="width:100%;height:auto;min-width:880px">
      <title>Three incompatible score scales normalised to rank before fusion</title>
      <desc>A query fans out to three indexes drawn as score bars: bounded with a
        fixed track, unbounded running past the panel edge, and offset on its own
        track. All three are redrawn on one shared track inside a normalise band,
        then merged at a plus symbol into a single ranked list. Bar length encodes
        score magnitude; the two pens separate the two scoring families.</desc>
      <defs>
        <marker id="mk-fuse-a" viewBox="0 0 8 8" refX="7" refY="4"
                markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0 0 8 4 0 8Z" fill="var(--ink-soft)"/>
        </marker>
      </defs>
      <g fill="none" stroke="var(--ink-soft)" marker-end="url(#mk-fuse-a)">
        <path d="M136 132h20V48h16"/><path d="M136 132h36"/><path d="M136 132h20v84h16"/>
        <path d="M448 48h28"/><path d="M448 132h28"/><path d="M448 216h28"/>
      </g>
      <rect x="16" y="106" width="120" height="52" fill="var(--paper-2)" stroke="var(--ink-soft)"/>
      <text x="28" y="130" font-size="13" fill="var(--ink)">one query</text>
      <text x="28" y="147" font-size="10" fill="var(--ink-soft)">1</text>
      <g fill="var(--paper-2)" stroke="var(--pen-a)">
        <rect x="176" y="16" width="272" height="64"/><rect x="176" y="100" width="272" height="64"/>
        <rect x="176" y="184" width="272" height="64"/>
      </g>
      <text x="188" y="36" font-size="13" fill="var(--ink)">semantic</text>
      <rect x="188" y="44" width="180" height="10" fill="var(--paper)" stroke="var(--grid)"/>
      <rect x="188" y="44" width="112" height="10" fill="var(--pen-a)"/>
      <text x="188" y="70" font-size="10" fill="var(--ink-soft)">bounded 0–1 · 2</text>
      <text x="188" y="120" font-size="13" fill="var(--ink)">lexical</text>
      <rect x="188" y="128" width="196" height="10" fill="var(--pen-b)"/>
      <text x="390" y="139" font-size="13" fill="var(--pen-b)">≫</text>
      <text x="188" y="154" font-size="10" fill="var(--ink-soft)">unbounded · 3</text>
      <text x="188" y="204" font-size="13" fill="var(--ink)">graph</text>
      <rect x="248" y="212" width="120" height="10" fill="var(--paper)" stroke="var(--grid)"/>
      <rect x="248" y="212" width="52" height="10" fill="var(--ink-soft)"/>
      <text x="188" y="238" font-size="10" fill="var(--ink-soft)">own scale · 4</text>
      <rect x="496" y="16" width="204" height="232" fill="none" stroke="var(--grid)" stroke-dasharray="4 4"/>
      <text x="508" y="38" font-size="11" fill="var(--ink-soft)">NORMALISE TO RANK</text>
      <g fill="var(--paper)" stroke="var(--grid)">
        <rect x="512" y="56" width="172" height="10"/><rect x="512" y="88" width="172" height="10"/>
        <rect x="512" y="120" width="172" height="10"/>
      </g>
      <rect x="512" y="56" width="132" height="10" fill="var(--pen-a)"/>
      <rect x="512" y="88" width="104" height="10" fill="var(--pen-b)"/>
      <rect x="512" y="120" width="72" height="10" fill="var(--ink-soft)"/>
      <text x="512" y="152" font-size="10" fill="var(--ink)">one scale, 0–1 · 5</text>
      <path d="M692 61h12v63M692 93h12v31M692 125h12M704 124h3" fill="none" stroke="var(--ink-soft)"/>
      <circle cx="718" cy="124" r="11" fill="var(--paper)" stroke="var(--ink)"/>
      <path d="M712 124h12M718 118v12" stroke="var(--ink)"/>
      <path d="M729 124h11" fill="none" stroke="var(--ink-soft)" marker-end="url(#mk-fuse-a)"/>
      <rect x="750" y="86" width="114" height="88" fill="var(--paper-2)" stroke="var(--pen-a)"/>
      <text x="762" y="108" font-size="13" fill="var(--ink)">fused list</text>
      <rect x="762" y="116" width="90" height="7" fill="var(--pen-a)"/>
      <rect x="762" y="128" width="68" height="7" fill="var(--pen-b)"/>
      <rect x="762" y="140" width="46" height="7" fill="var(--ink-soft)"/>
      <text x="762" y="164" font-size="10" fill="var(--ink-soft)">one order · 6</text>
    </svg>
  </div>
  <ol class="dg-key">
    <li><b>one query</b> <span>00:12:40</span></li>
    <li><b>semantic, bounded</b> <span>00:13:02</span></li>
    <li><b>lexical, unbounded</b> <span>00:13:31</span></li>
    <li><b>graph, own scale</b> <span>00:14:08</span></li>
    <li><b>rank normalisation</b> <span>00:15:22</span></li>
    <li><b>fused ranking</b> <span>00:15:47</span></li>
  </ol>
</figure>
```

## Kind reference

Pick by the structure in the conversation, never by variety. Each kind is an
arrangement of glyphs, not a new drawing:

| Kind | Built from | Layout | Failure mode |
|---|---|---|---|
| Pipeline with bands | any node glyph, gate chain | fixed stage pitch (188 = 156 box + 32 gutter); band rects inset 12 | diagonal arrows; a band hugging its contents |
| Causal / economics net | big number, magnitude bar | 3–4 columns at fixed x, free y; disputed node off the main row | hub-and-spoke blob with no reading direction |
| Two-column comparison | record field, score-scale bar | centre line; named dimension in the gutter on every row | empty gutter; unequal column widths |
| Layered topology | any node glyph, person | full-width lanes of equal height; cross-lane edges strictly vertical | a member spanning two lanes |
| Timeline | timeline tick, composition strip | true position from seconds; events above, act bands below | even spacing |
| Matrix / quadrant | person, big number | square plot area in user units; axis labels at the ends | invented precision; an unremarked empty quadrant |
| Before / after record | record field: empty → filled → cited | two identical panels, same field order and baselines | reordered or fabricated fields |
| Decision tree | gate chain, escalation cascade | depth is y at fixed pitch; failure path always the same side | missing terminal states; unlabelled branches |
| Small multiples | small-multiple frame | one cell template on a strict grid, one shared scale | per-cell scaling; more than six cells |
| Magnitude comparison | magnitude bar, big number | shared zero, equal thickness, length encodes value | truncated axis; no number anywhere |
| Feedback loop | state machine with return edge | forward path straight, return routed below and longer | drawn as a circle; unlabelled return |
| Composition | composition strip | one bar, exact fractional boundaries, largest first unless natural order | parts that do not sum to the whole |

## House style — hard rules

**Colour.** Every colour is a CSS variable. The permitted set is `--ink`, `--ink-soft`,
`--grid`, `--pen-a`, `--pen-b`, `--paper`, `--paper-2`. Never a literal hex, never
`fill="white"` or `fill="black"`, never a named colour, never `rgb()`. The page ships light
and dark palettes; a literal colour goes invisible for half your readers.

**Two pens, fixed meaning.** One pen per speaker or actor, held across every figure:
`--pen-a` is the same actor in figure 1 and figure 11. `--ink-soft` for anything
unattributed. A figure with no attribution axis is drawn in one pen, and `<desc>` says why.

**Type.** No fixed-width typewriter faces anywhere — not for labels, not for timestamps,
not for identifiers. Timestamps use the condensed face with `font-variant-numeric:
tabular-nums`. Node labels are **five words or fewer**; the note under a node is **twelve
words or fewer**. Nothing below 10px.

**Line.** Strokes 1–1.5px for structure, 0.5px for hairline grid and axes. No shadows, no
gradients, no `rx` above 2, no emoji, no icon fonts, no clip art. Fill boxes with
`--paper-2` and stroke with a pen — never fill a box with a pen colour and set text on it.

**Marker ids are per-figure**, prefixed with the figure id: `mk-<figure-id>-a`. All figures
land in one document, ids are global, and a collision silently repaints every arrowhead on
the page — the commonest way a set of individually correct figures breaks once assembled.

**Every figure carries** `role="img"`, a `<title>`, a `<desc>` reading the figure in its
reading order and stating what position and colour encode, a `<figcaption>` with `dg-t` (a
title stating the finding, not the topic) and `dg-w` (what to look at and what it means),
and a numbered `dg-key` — one entry per badge with the timestamp where it was said. The key
is what makes a diagram checkable, and the first thing the verifier reads.

## The set is one argument

- Open the fragment with a **lead-in** (`<div class="dg-lead">`) naming the sequence: what
  the first figure establishes, what each one after does to that. If you cannot write it,
  the set has no order — reorder until you can.
- Between consecutive figures, one **bridge** (`<p class="dg-bridge">`) stating a
  consequence or a question, never a summary. "Which raises the question of what it costs"
  is a bridge; "the next figure shows costs" is a label.
- Sequence by argument, not chronology; each figure must survive being read alone.

## Responsiveness

Each figure must be legible at 390px wide. Either design it to that width, or wrap the
`<svg>` in `<div class="dg-scroll">` with `overflow-x:auto` and a `min-width` equal to its
viewBox width. The figure scrolls; the page body never scrolls horizontally. The `dg-key`
collapses to one column under 640px.

## The self-check before declaring done

```
callsheet lint-diagrams out/diagrams.html --turns work/turns.json
```

That covers well-formedness, literal colours, fixed-width faces, marker ids reused across
figures, a missing `role="img"`, `<title>`, `<desc>` or key, text below 10px, and every
cited timestamp resolving to a real turn. Then check by hand what a linter cannot:

1. **Cover the labels.** Read each figure with every text element hidden. If you cannot
   state its claim from the shapes alone, it is not glyph-first — go back.
2. **Build and open the page.** External requests must be zero.
3. **Toggle the theme.** A figure that vanishes in dark mode has a hard-coded
   colour the grep missed.
4. **Narrow to 390px.** The body does not scroll sideways.
5. **Turn on reduced motion.** Every figure renders complete and still.
6. **Read only the captions and bridges, in order.** If they do not form a
   coherent argument alone, the set is a gallery.
7. **Pick three nodes at random and find them in `work/turns.json`** — not the timestamp,
   the *claim*. A node whose content is not in the transcript is deleted, not softened.
8. **Count words in the longest label.** Over five, rewrite it.
9. **Check one pen means one actor** across the whole set.
