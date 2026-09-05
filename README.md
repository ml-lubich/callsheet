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

Python does the mechanical parts: transcription, vocabulary checking, parsing,
chunking, schema validation, diagram linting, injection, sealing and overlap
measurement. The
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
| `skills/lexicon/` | recovering domain vocabulary the recogniser mangled, before anything reads the transcript |
| `skills/diagrams/` | authoring the figure set: twelve figure kinds, the house style, the self-check |
| `skills/modes/` | the output modes: the register and the shape the same call is rendered in |
| `skills/verify/` | the adversarial fact-check, in a fresh context, grading FABRICATED / WRONG / MISATTRIBUTED / IMPRECISE |
| `skills/holdout/` | sealing a reference answer and measuring independence afterwards |

## Examples

Three complete worked examples live in `examples/`, each an invented transcript
with the intermediate files a real run produces, a `run.sh` that drives the CLI
end to end, and a README saying what it demonstrates.

| | The call | What it shows |
|---|---|---|
| `examples/product-review/` | a three-speaker design review, 52 turns | more than two speakers; a decision reached and then reversed; the two-column comparison figure |
| `examples/incident-postmortem/` | a two-speaker outage retro, 48 turns | the timeline figure on the incident's real wall clock; a causal chain; evidence graded weak where a claim was asserted rather than shown |
| `examples/customer-discovery/` | a two-speaker discovery call, 47 turns | the economics figure; quantities the speaker states loosely and the write-up refuses to sharpen; the hold-out against a second analyst's version |

```
cd examples/product-review && ./run.sh
```

Each `run.sh` runs the real CLI — parse, chunk, lint-diagrams, build, and
seal/compare where a reference answer exists — and exits nonzero if any gate
fails. The agent fan-out is stood in for by the shipped `expected/` files, so the
examples run offline and produce the same page every time.

### The fan-out, made concrete

`examples/agents/` is that fan-out written out as a script. `fanout.sh` drives
the Claude Code CLI directly, one `claude -p` per role, with each role's prompt
in `prompts/` where it can be read and edited without touching the script. Four
segment analysts and one whole-call reader run in parallel as background jobs;
then the synthesizer, the diagram author, the build and the adversarial verifier
run in sequence — eight agent invocations for one call. The model split is five
variables at the top of the script: the analysts are the bulk of the token spend
and most of what they do is careful extraction, so they run on `claude-sonnet-5`,
while the four roles that need judgement across the whole call — the reader, the
synthesizer, the diagram author and the verifier — run on `claude-opus-5`.

## Install

```
pip install -e ".[dev]"
```

## Use

```
callsheet transcribe call.m4a -m ~/models/ggml-large-v3.bin -o work/transcript
callsheet lexicon check work/transcript.txt --profile profiles/example-engineer.json
callsheet parse work/transcript.txt -o work
callsheet chunk work/turns.json -n 4 -o work

# ... agents read work/chunk*.txt and write work/content.json and out/diagrams.html ...

callsheet lint-diagrams out/diagrams.html --turns work/turns.json
callsheet build --content work/content.json --turns work/turns.json \
                --metrics work/metrics.json --diagrams out/diagrams.html \
                --mode professional -o out/index.html
```

`callsheet build` refuses to run on a `content.json` that does not validate, and
names the field that is wrong. It reports the number of external requests in the
finished page, which should be zero.

### Modes

`callsheet modes` lists the nine output modes a build can be rendered in —
`professional` (the default), `concise`, `formal`, `casual`, `interesting`,
`summarized`, `compact`, `creative` and `diagrams-only`. A mode sets the register
the synthesizer writes in, which sections render in what order, the prose and
figure budgets, and the transcript setting. It never changes a fact. A project
can add its own in `.callsheet/modes.json`, merged over the built-ins. See
`skills/modes/`.

The word budgets are hard. `callsheet build` refuses a `content.json` whose
abstract, act summary, thread, list item or any single paragraph runs over the
mode's cap, and names each field with its count and its excess. `callsheet
lint-prose work/content.json --mode concise` reports the same list without the
failure, and additionally flags a wall of text: three consecutive prose sections
with no figure, table or list to break them.

### Linting the figures

`callsheet lint-diagrams` catches the mechanical faults a hand-authored SVG set
falls into: markup that does not nest, a literal hex colour or `fill="white"`
that stops following the theme, a monospace font, a `<marker>` id reused between
two figures so every arrowhead on the page repaints itself, a figure missing
`role="img"`, `<title>`, `<desc>` or its numbered key, text under 10px, and — with
`--turns` — a cited timestamp that starts no real turn. It exits nonzero and
names each fault and the figure it lives in.

### Recovering mangled vocabulary

Local speech recognition has no prior for the words a conversation is about, so
it writes the nearest ordinary English it knows. From one real interview: FAISS
became "fate face", Cognee "cockney", LangGraph "land graph", BM25 "abeam 25",
reciprocal rank fusion "rank reciprocal factor", SQLite "SQL light", ChromaDB
"Chrome IDB". A reader who searches the write-up's spelling finds nothing in the
transcript, and anything summarising it downstream will explain what it thinks
"abeam 25" means.

`callsheet lexicon` profiles how one person writes — their vocabulary and their
phrasing, from documents they wrote — and uses that profile twice: to propose
corrections where the transcript sounds like a term the speaker uses but is not
spelled like one, and to flag sentences whose phrasing is absent from the profile
*and* whose register sits far from it, which is what invented text looks like.

```
callsheet lexicon build --from docs/ notes/*.md --name ada -o profiles/ada.json
callsheet lexicon check work/transcript.txt --profile profiles/ada.json -o work/lexicon.md
callsheet lexicon apply work/transcript.txt --profile profiles/ada.json --write
```

`check` exits nonzero when it finds anything, so it gates a pipeline. Corrections
are never applied on their own: `apply` does nothing without `--write`, and
writes a `.corrections.json` audit of every span, offset and score beside its
output. `profiles/example-engineer.json` ships so the check works before you have
built a profile of your own, and `profiles/README.md` explains why a profile —
frequencies, never message content — is safe to commit.

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
