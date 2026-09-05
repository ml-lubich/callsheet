---
name: callgen
description: Turn a recording or transcript of a call, meeting or interview into one self-contained HTML document that someone who was not there can read, where the argument is carried by figures and every claim traces to a timestamp. Use when the user has audio, video or a transcript and wants a shareable written artifact, a briefing, a readout, or an "what happened on this call" page — including when they want it checked against someone else's write-up of the same call.
---

# callgen

Pipeline: **transcribe → check the vocabulary → parse → analyse (agents) → draw →
build → verify → hold out.**
Python owns the mechanical steps. The analysis is yours; the CLI only produces the
files you read and validates what you hand back.

Doctrine ("pictures first"), rationale and prompt bodies for every step below:
**`skills/prompts.md`**.

Install: `pip install -e .`. Everything runs locally. Sub-skills, each
self-contained and meant to be run in its own context:

| | |
|---|---|
| `skills/lexicon/SKILL.md` | recovering domain vocabulary the recogniser mangled, before anything reads the transcript |
| `skills/diagrams/SKILL.md` | authoring the figure set — the catalog, the house style, the self-check |
| `skills/modes/SKILL.md` | the output modes — the register and the shape the same call is rendered in |
| `skills/verify/SKILL.md` | the adversarial fact-check, in a fresh context |
| `skills/holdout/SKILL.md` | sealing a reference answer and measuring independence |

## 1. Transcribe (skip if a transcript already exists)

```
callgen transcribe CALL.m4a -m ~/models/ggml-large-v3.bin -o work/transcript -t 8
```

## 2. Check the vocabulary

```
callgen lexicon check work/transcript.txt --profile profiles/example-engineer.json \
                       -o work/lexicon.md
```

Gates the rest of the pipeline. Read `work/lexicon.md` and decide each line
yourself, then apply with `callgen lexicon apply ... --write`. Full walkthrough:
**`skills/lexicon/SKILL.md`**; rationale and the apply command: `skills/prompts.md`.

## 3. Parse

```
callgen parse work/transcript.txt -o work     # -> work/turns.json, work/metrics.json
callgen chunk work/turns.json -n 4 -o work    # -> work/chunk1.txt … work/chunk4.txt
```

Read `metrics.json` before dispatching anything: duration, turn count and the
word split tell you how many segment analysts the call actually needs. One
analyst per ~15–20 minutes; four is the usual number.

## 4. Analyse — the fan-out

Dispatch these in one batch. They do not depend on each other.

| Agent | Model | Reads | Returns |
|---|---|---|---|
| Segment analyst ×N | cheaper | one `chunkN.txt` | `work/analysis-N.json` |
| Whole-call reader ×1 | strongest | the entire transcript | `work/arc.json` |

Full prompt bodies for both roles: **`skills/prompts.md`**.

## Choose a mode — before you synthesize

A mode is a preset over register, shape and emphasis: how the prose is written,
which sections render in what order under what word and figure budgets, and what
the verdict optimises for. It never changes a fact. `professional` is the
default and the right answer unless you have a reason. `callgen modes` lists
the nine; **`skills/modes/SKILL.md`** defines each and says who each is for.

Put the register into the synthesizer prompt in step 5, and name the same mode
again in step 7:

```
python -c "from callgen.modes import prompt_guidance; print(prompt_guidance('concise'))"
```

## 5. Synthesize

One agent, strongest model, reads every `analysis-N.json` and `arc.json` and
writes `work/content.json`. Tiling, dedup, timestamp and word-cap rules:
**`skills/prompts.md`**. Validate before continuing — see **Required gates**.

## 6. Draw — the main event

One agent, strongest model, in its own context, following
**`skills/diagrams/SKILL.md`**, writes `out/diagrams.html`: 8–12 inline
`<figure class="dg">` elements, hand-written SVG, no libraries, no raster.
Palette tokens, the figure catalog and the self-check: `skills/prompts.md` and
the sub-skill.

Gate before building:

```
callgen lint-diagrams out/diagrams.html --turns work/turns.json
```

## 7. Build

```
callgen build --content work/content.json --turns work/turns.json \
                --metrics work/metrics.json --diagrams out/diagrams.html \
                --mode professional -o out/index.html
```

`--mode` drops the sections the mode leaves out, reorders the rest, caps the
figure set and sets the transcript. Rendering the same call in a second mode
reruns steps 5 and 7 only. Failure modes and the zero-external-requests
guarantee: `skills/prompts.md`.

## 8. Verify — adversarial, in a fresh context

One agent that has **not** seen the analysis, following
**`skills/verify/SKILL.md`**. Give it `out/index.html` and `work/turns.json` and
nothing else. It grades every defect FABRICATED / WRONG / MISATTRIBUTED /
IMPRECISE and checks quotes, numerals, timestamps, act tiling, thread marks,
evidence strengths, diagram nodes and edges, and speaker attribution. Anything
it cannot find is deleted, not hedged; rebuild and verify again in another
fresh context.

## 9. Hold out (only when a reference answer exists)

If someone else has already written up the same call, follow
**`skills/holdout/SKILL.md`**: seal it *before* the analysis starts, run the build
inside `callgen.holdout.sealed_guard`, and compare only after the artifact is
frozen.

```
callgen seal sealed/                     # read-only + sha256, before step 4
callgen compare out/index.html sealed/   # after the artifact is final
```

Overlap thresholds and what to do with a nonzero rate: `skills/prompts.md`.

## Required gates — none are advisory, each names the fault

```
callgen lexicon check work/transcript.txt --profile PROFILE   # before anything reads it
python -c "import json;from callgen.schema import validate;validate(json.load(open('work/content.json')))"
callgen lint-prose work/content.json --mode MODE               # hard word caps
callgen lint-diagrams out/diagrams.html --turns work/turns.json
callgen build …    # reports external requests; that count must be zero
```

JSON contract and the non-negotiable rules: **`skills/prompts.md`**.
