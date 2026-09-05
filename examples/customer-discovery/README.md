# Customer discovery

A worked example for the callgen pipeline: a two-speaker sales discovery call
between Ines Vartanian, selling a route-planning service, and Hollis Grady, the
operations manager at a regional delivery operation she is trying to sell into.
Everything — both people, the depot, the "northern run," every number — is
invented for this example.

## What this demonstrates

1. **The economics figure.** `expected/diagrams.html`'s second figure,
   `dg-annual-load`, is the catalog's economics/causal-network shape: two of
   Hollis's own driver-side estimates on the left, a fixed weekly multiplier in
   the centre, and the annual figure Ines derives from them on the right. The
   per-hour dollar figure he refuses to give sits off the main row, dashed,
   because it was withheld rather than stated.
2. **Loose quantities, recorded as loose.** Hollis never gives a hard number.
   "Call it thirty-something drivers," "high fifties, maybe sixty stops... give
   or take," "somewhere north of two hours a week, I'd guess" — `numbers` in
   `expected/content.json` preserves each hedge in the `value` string instead
   of quietly rounding it into a clean figure, and `means` says plainly what is
   and is not established. The annual-load figure in the diagram is drawn as an
   open-ended, hatched range rather than a point estimate, for the same reason.
3. **The hold-out.** `other-analyst.html` is a second write-up of the same
   call, sealed with `callgen seal` before the build starts and only opened
   by `callgen compare` after `out/index.html` is final. It agrees with the
   shipped analysis on the process and the headline number's looseness, but
   weighs the turnover admission more heavily and would have pushed harder for
   a named approver before the call ended.

## Run it

```
./run.sh
# or, if callgen isn't on PATH:
CALLGEN=../../.venv/bin/callgen ./run.sh
```

This parses the transcript, chunks it, seals `other-analyst.html`, copies the
shipped `expected/content.json` and `expected/diagrams.html` into place (a real
run would have agents write these — see `../agents/` for that fan-out),
lints the diagrams, builds `out/index.html`, and finally compares the finished
page against the sealed write-up.

- **Turns:** 47
- **Duration:** 2890s (48:10)

## Reading the `compare` output

The run above prints:

```
other-analyst.html: 6-gram 0.0%  10-gram 0.0%
```

A near-zero 10-gram share is the evidence the two write-ups were produced
independently — eight or ten words in a row matching by coincidence basically
does not happen. That gate passes here at 0.0%. The 6-gram share is also 0.0%,
which is lower than the holdout skill's rule of thumb, because `compare` only
looks at the page's static, non-script markup — the analysis prose in
`content.json` (abstract, threads, quotes) is injected at view time from a
`<script>` block that `strip_html` deliberately excludes, so the only visible
text it can compare against `other-analyst.html` is the diagram captions and
the template's own labels. Both files do quote the transcript ("somewhere
north of two hours a week," "let's come back to that"), but never in the same
six-word run, so the short-range share lands at zero too. Nothing here
indicates the write-ups are unrelated — the shared source material is visible
in `work/turns.json` and in both HTML files if you read them side by side.

## What to look at

- `out/index.html` — the finished page. Open it and check the diagrams tab
  against `work/turns.json`.
- `expected/diagrams.html` — three figures: `dg-morning-scramble` (what breaks
  the dispatcher's sheet), `dg-annual-load` (the economics figure), and
  `dg-pilot-scope` (today vs. the pilot Hollis agreed to).
- `expected/content.json` — the `numbers` section for how a hedge gets
  recorded, and `fit.risks` for where the shipped analysis itself might be
  overreaching.
