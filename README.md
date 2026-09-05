# callsheet

Turn a recorded conversation into a single self-contained HTML document that
someone who was not on the call can read, where every claim traces to a
timestamp.

One file out. No external requests, no CDN, no fonts to fetch — open it from a
USB stick in five years and it still works. Transcription runs locally through
whisper.cpp; the audio never leaves the machine.

## What it does

```
recording ──▶ transcript ──▶ turns.json ──▶ chunk1..N.txt ──▶ content.json ──▶ index.html
             whisper.cpp     metrics.json   (agents read)     (agents write)   (one file)
```

Python does the mechanical parts: transcription, parsing, chunking, schema
validation, injection, sealing and overlap measurement. The reading and writing
is done by agents, and `SKILL.md` is the Claude Code skill that drives them.

The page itself is a strip chart: every turn is plotted on elapsed time, one
speaker above the baseline and one below, bar height by word count. Acts,
threads, evidence and quotes are all registered to that same axis, so the
structure of the conversation is position in time rather than decoration. The
whole transcript ships inside the page with search and per-speaker filtering,
and every timestamp anywhere on the page jumps to the turn it came from.

## Install

```
pip install -e ".[dev]"
```

## Use

```
callsheet transcribe call.m4a -m ~/models/ggml-large-v3.bin -o work/transcript
callsheet parse work/transcript.txt -o work
callsheet chunk work/turns.json -n 4 -o work

# ... agents read work/chunk*.txt and write work/content.json ...

callsheet build --content work/content.json --turns work/turns.json \
                --metrics work/metrics.json --diagrams out/diagrams.html \
                -o out/index.html
```

`callsheet build` refuses to run on a `content.json` that does not validate, and
names the field that is wrong. It reports the number of external requests in the
finished page, which should be zero.

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

MIT.
