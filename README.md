# callsheet

Turn a recorded conversation into a single self-contained HTML document that
someone who was not on the call can read, where the argument is carried by
figures and every claim traces to a timestamp.

One file out. No external requests, no CDN, no fonts to fetch — open it from a
USB stick in five years and it still works. Transcription runs locally through
whisper.cpp; the audio never leaves the machine.

## What it does

```
recording ──▶ transcript ──▶ turns.json ──▶ chunk1..N.txt ──▶ content.json  ──▶ index.html
             whisper.cpp     metrics.json   (agents read)     diagrams.html    (one file)
                                                              (agents write)
```

Python does the mechanical parts: transcription, parsing, chunking, schema
validation, diagram linting, injection, sealing and overlap measurement. The
reading and drawing is done by agents, and `SKILL.md` is the Claude Code skill
that drives them.

The page itself is a strip chart: every turn is plotted on elapsed time, one
speaker above the baseline and one below, bar height by word count. Acts,
threads, evidence and quotes are all registered to that same axis, so the
structure of the conversation is position in time rather than decoration. The
whole transcript ships inside the page with search and per-speaker filtering,
and every timestamp anywhere on the page jumps to the turn it came from.

The figures sit second on that axis — directly after the abstract, ahead of the
prose that checks them.

## Pictures first

The output is not an essay with illustrations. A one-hour call gets **8–12
figures** — hand-written inline SVG, no libraries, themed through the page's own
CSS variables so they follow light and dark — and prose short enough that a
reader uses it to check the figures rather than the other way round. Anything
with a shape (an order, a fan-out, a comparison, a magnitude, a position in time)
is drawn; prose is for what is left.

The figure set is written to read as one argument: a lead-in names the sequence
and a one-sentence bridge carries the reader between consecutive figures. A set
of individually dense figures that do not compose is a gallery, and a gallery
tells a reader nothing the transcript did not.

## Sub-skills

| | |
|---|---|
| `skills/diagrams/` | authoring the figure set: twelve figure kinds, the house style, the self-check |
| `skills/verify/` | the adversarial fact-check, in a fresh context, grading FABRICATED / WRONG / MISATTRIBUTED / IMPRECISE |
| `skills/holdout/` | sealing a reference answer and measuring independence afterwards |

## Install

```
pip install -e ".[dev]"
```

## Use

```
callsheet transcribe call.m4a -m ~/models/ggml-large-v3.bin -o work/transcript
callsheet parse work/transcript.txt -o work
callsheet chunk work/turns.json -n 4 -o work

# ... agents read work/chunk*.txt and write work/content.json and out/diagrams.html ...

callsheet lint-diagrams out/diagrams.html --turns work/turns.json
callsheet build --content work/content.json --turns work/turns.json \
                --metrics work/metrics.json --diagrams out/diagrams.html \
                -o out/index.html
```

`callsheet build` refuses to run on a `content.json` that does not validate, and
names the field that is wrong. It reports the number of external requests in the
finished page, which should be zero.

### Linting the figures

`callsheet lint-diagrams` catches the mechanical faults a hand-authored SVG set
falls into: markup that does not nest, a literal hex colour or `fill="white"`
that stops following the theme, a monospace font, a `<marker>` id reused between
two figures so every arrowhead on the page repaints itself, a figure missing
`role="img"`, `<title>`, `<desc>` or its numbered key, text under 10px, and — with
`--turns` — a cited timestamp that starts no real turn. It exits nonzero and
names each fault and the figure it lives in.

### Transcript formats

Detected by inspection, no flag needed:

| Shape | Example |
|---|---|
| Bracketed blocks | `[00:12:34] Ada Sterling:` then indented lines |
| Bracketed lines | `[12:34] Ada Sterling: text` — minutes may exceed 59 |
| WebVTT | cues with `<v Name>` or a `Name:` prefix |
| Plain | `Ada Sterling: text` — turn times estimated from word counts |

A line that looks like a timestamp header but is not raises, rather than being
quietly folded into the previous turn where a lost turn would go unnoticed.

### Holding out a reference answer

If someone else has written up the same call, seal their version before you
start, so that the resemblance you measure afterwards means something:

```
callsheet seal sealed/                     # read-only, sha256 recorded
callsheet compare out/index.html sealed/   # verifies the seal, prints n-gram overlap
```

`callsheet.holdout.sealed_guard(path)` raises if anything under the sealed
directory is opened while it is active, so "we did not read it" is a property the
build enforces rather than a claim.

## Development

```
pytest -q
ruff check .
```

The template lives at `src/callsheet/templates/page.html` and takes four markers:
`/*__CONTENT__*/null`, `/*__TURNS__*/null`, `/*__METRICS__*/null` and
`<!--__DIAGRAMS__-->`. Each must appear exactly once. Swap the template for your
own with `callsheet build --template`.

The diagram fragment brings its own `<style>` block for figure internals; the
page owns `.dg-lead` and `.dg-bridge`, the connective prose between figures.
`tests/fixtures/diagrams.html` is a small, lint-clean example of the shape.

MIT.
