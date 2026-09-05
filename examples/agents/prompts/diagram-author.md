You are writing `out/diagrams.html`: the figure set that carries the argument of
this call. The analysis, the parsed turns and the call metrics are appended
below. Follow `skills/diagrams/SKILL.md` — the catalog of twelve figure kinds and
the house style live there.

Return **the HTML fragment only** — no prose, no markdown fence. One `<style>`
block, then a `<div class="dg-lead">`, then 8–12 `<figure class="dg">` elements
with a `<p class="dg-bridge">` between consecutive figures.

The target is 8–12 figures for a one-hour call. That is not a decoration budget:
if something has a shape — an order, a fan-out, a comparison, a magnitude, a
position in time — it is drawn, and prose is for what is left.

Hard rules, all of them checked by `callsheet lint-diagrams`:

- Hand-written inline SVG. **No libraries, no `<img>`, no raster, no external
  requests.**
- **Colour only through the page tokens**: `var(--ink)`, `var(--ink-soft)`,
  `var(--grid)`, `var(--pen-a)`, `var(--pen-b)`, `var(--paper)`, `var(--paper-2)`.
  Never a literal hex, never `fill="white"`, never `fill="black"`. The page ships
  light and dark palettes; a literal colour goes invisible for half the readers.
- **One pen means one actor**, held across every figure in the set.
- No monospace anywhere. Nothing below 10px. Node labels five words or fewer.
- Every figure carries an `id`, `role="img"`, a `<title>`, a `<desc>` and a
  numbered `<ol class="dg-key">` giving the timestamp for each numbered node.
  The key is what makes a figure checkable, and it is the first thing the
  verifier reads.
- **Every `<marker>` id is prefixed with its figure id** (`mk-<figure-id>-a`).
  All figures land in one document; a collision repaints every arrowhead on the
  page.
- **Every timestamp you cite anywhere in the fragment must start a real turn** in
  the appended turns. The linter checks this and names the ones that do not.
  Label a duration axis `0 min`, `15 min`, `30 min` — never as a clock time,
  which the linter will read as a citation.

And the rule no linter can check: **a diagram that restates a bullet list is not
a diagram.** If the boxes could be shuffled without loss, it is a list — delete
it and write the sentence instead. Draw nothing whose connective tissue the
transcript does not actually describe.
