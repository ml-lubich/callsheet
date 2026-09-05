---
name: callsheet
description: Turn a recording or transcript of a call, meeting or interview into one self-contained HTML document that someone who was not there can read, where the argument is carried by figures and every claim traces to a timestamp. Use when the user has audio, video or a transcript and wants a shareable written artifact, a briefing, a readout, or an "what happened on this call" page — including when they want it checked against someone else's write-up of the same call.
---

# callsheet

Pipeline: **transcribe → check the vocabulary → parse → analyse (agents) → draw →
build → verify → hold out.**
Python owns the mechanical steps. The analysis is yours; the CLI only produces the
files you read and validates what you hand back.

**Pictures first.** The output is not an essay with illustrations. A one-hour call
gets **8–12 figures** that carry the argument, and prose kept short enough that a
reader uses it to check the figures rather than the other way round. Before writing
any paragraph, ask whether the thing it describes has a shape — an order, a
fan-out, a comparison, a magnitude, a position in time. If it does, draw it and
write a caption instead.

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
callsheet transcribe CALL.m4a -m ~/models/ggml-large-v3.bin -o work/transcript -t 8
```

Audio never leaves the machine. If the recording has two or more voices and the
model did not diarize, say so in `meta` and fill the `diarization` section later —
never present unlabelled attribution as certain.

## 2. Check the vocabulary

The recogniser has no prior for the words the call is about, so it substitutes
the nearest ordinary English: FAISS becomes "fate face", BM25 becomes "abeam 25",
SQLite becomes "SQL light". Every claim in this document is supposed to trace to
a timestamp, and a reader searching your spelling finds nothing in a transcript
that says "abeam 25". Worse, the analysts in step 4 will read the garbled form
and explain what they think it means.

```
callsheet lexicon check work/transcript.txt --profile profiles/example-engineer.json \
                       -o work/lexicon.md
```

It exits nonzero when it finds anything, so it gates the rest of the pipeline.
Build a profile from the speaker's own writing when you have it, and use the
shipped one when you do not:

```
callsheet lexicon build --from their/docs --name them -o profiles/them.json
```

**Read `work/lexicon.md` and decide each line yourself.** A phonetic match is a
guess; a guess applied silently is a fabrication that is now spelled correctly.
Then apply the ones you accept, re-parse, and keep the audit:

```
callsheet lexicon apply work/transcript.txt --profile profiles/them.json --write
```

`work/transcript.txt.corrections.json` records every span, offset and score.
Carry it into `meta.extra` — a reader is entitled to know the transcript was
edited and how — and give it to the verifier in step 8.

Full sub-skill: **`skills/lexicon/SKILL.md`**.

## 3. Parse

```
callsheet parse work/transcript.txt -o work     # -> work/turns.json, work/metrics.json
callsheet chunk work/turns.json -n 4 -o work    # -> work/chunk1.txt … work/chunk4.txt
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

**Segment analyst prompt** — one per chunk, self-contained:

> You are reading minutes M1–M2 of a recorded conversation, one slice of N. The
> full transcript of your slice is below. Return JSON only, no prose, with keys:
> `acts` (the 1–2 movements inside this slice: title, span, start_s, end_s,
> summary, turning_point), `threads`, `evidence`, `signals`, `numbers`, `quotes`,
> `tech`, `tensions`, `next_steps`, and `shapes`. Every entry carries `ts`
> (HH:MM:SS) and `s` (that timestamp in seconds). **Quote text must be an exact
> substring of the transcript.** `shapes` is anything in your slice with a
> structure worth drawing — a sequence, a fan-out, a comparison, a magnitude, a
> before/after — with the timestamps that describe each part. Do not infer
> anything that happened outside your slice. If you are unsure a figure was
> actually said, omit it.

**Whole-call reader prompt** — the same JSON keys plus `abstract` (90–120 words)
and `fit`, and one extra instruction: *you are the only reader who sees the whole
call, so your job is the arc — what changed between the first ten minutes and the
last, and what each participant wanted that they did not say directly. In
`shapes`, note anything described in scattered pieces that would only be visible
assembled.*

## Choose a mode — before you synthesize

A mode is a preset over register, shape and emphasis: how the prose is written,
which sections render in what order under what word and figure budgets, and what
the verdict optimises for. It never changes a fact. `professional` is the
default and the right answer unless you have a reason. `callsheet modes` lists
the nine; **`skills/modes/SKILL.md`** defines each and says who each is for.

Put the register into the synthesizer prompt in step 5, and name the same mode
again in step 7:

```
python -c "from callsheet.modes import prompt_guidance; print(prompt_guidance('concise'))"
```

## 5. Synthesize

One agent, strongest model. It reads every `analysis-N.json` and `arc.json` and
writes `work/content.json`. Its rules:

- Acts must **tile the whole call**: `acts[0].start_s == 0`, each act starts where
  the previous ended, the last ends at `metrics.duration_s`. Merge the segment
  analysts' acts across chunk boundaries rather than concatenating them.
- Deduplicate threads by meaning, not by wording. A thread that surfaced in three
  chunks is one thread with three `marks`.
- Keep the earliest `ts` for any claim that appears more than once.
- `span` strings are derived from `start_s`/`end_s`, never typed by hand.
- **Keep the prose short.** `abstract` 90–120 words. Each act `summary` ≤ 60
  words. Each thread's `what` and `why_it_matters` one sentence each. Anything
  longer is a figure you have not drawn yet — hand it to step 6 instead.
- Merge every analyst's `shapes` into one ranked list for the diagram agent, and
  drop the ones that are only a single relationship.

Validate before going further (see **Required gates**) — the schema names the
field that is wrong.

## 6. Draw — the main event

One agent, strongest model, in its own context, following
**`skills/diagrams/SKILL.md`**. It reads `work/content.json`, `work/turns.json`
and `work/metrics.json` and writes `out/diagrams.html`: 8–12 inline
`<figure class="dg">` elements, hand-written SVG, coloured only through the page
tokens `var(--ink)`, `var(--ink-soft)`, `var(--grid)`, `var(--pen-a)`,
`var(--pen-b)`, `var(--paper)` and `var(--paper-2)`, so every figure follows the
light and dark palettes. No libraries, no `<img>`, no raster.

The sub-skill carries the catalog of twelve figure kinds, the house style, the
composition rules (a lead-in, and a bridge between consecutive figures, so the set
reads as one argument) and the self-check. A diagram that restates a bullet list
is not a diagram.

Gate before building:

```
callsheet lint-diagrams out/diagrams.html --turns work/turns.json
```

## 7. Build

```
callsheet build --content work/content.json --turns work/turns.json \
                --metrics work/metrics.json --diagrams out/diagrams.html \
                --mode professional -o out/index.html
```

`--mode` drops the sections the mode leaves out, reorders the rest, caps the
figure set and sets the transcript. Rendering the same call in a second mode
reruns steps 5 and 7 only.

The build fails loudly on a missing or duplicated template marker, escapes the
injected JSON so it cannot break out of its `<script>`, and reports the number of
external requests in the finished page. That number must be zero.

## 8. Verify — adversarial, in a fresh context

One agent that has **not** seen the analysis, following
**`skills/verify/SKILL.md`**. Give it `out/index.html` and `work/turns.json` and
nothing else. It grades every defect FABRICATED / WRONG / MISATTRIBUTED /
IMPRECISE and checks quotes, numerals, timestamps, act tiling, thread marks,
evidence strengths, diagram nodes and edges, and speaker attribution.

**Anything it cannot find is deleted, not hedged.** In the run this skill was
generalized from, that pass caught a per-case cost figure that no one had said out
loud, sitting in a finished diagram. Rebuild after the deletions and run the
verifier once more, in another fresh context.

## 9. Hold out (only when a reference answer exists)

If someone else has already written up the same call, follow
**`skills/holdout/SKILL.md`**: seal it *before* the analysis starts, run the build
inside `callsheet.holdout.sealed_guard`, and compare only after the artifact is
frozen.

```
callsheet seal sealed/                     # read-only + sha256, before step 4
callsheet compare out/index.html sealed/   # after the artifact is final
```

Near-zero 8-gram overlap is the evidence of independence; a nonzero 5- or 6-gram
rate is expected, because both authors quote the same source. Nothing from this
step goes back into the document.

## JSON contract

`content.json` — see `src/callsheet/schema.py` for the enforced version.

```
meta      {title, subtitle, kind, date, duration_label, duration_s, turns, words,
           extra: [[label, value]], participants: [{key, name, role}]}
abstract  "90-120 words"
acts      [{n, title, span, start_s, end_s, summary, turning_point:{ts,s,text}}]
threads   [{name, what, why_it_matters, marks:[{ts,s}]}]
evidence  [{ts, s, claim, evidence, strength: strong|medium|weak}]
signals   [{ts, s, signal}]        numbers  [{ts, s, value, means}]
quotes    [{ts, s, speaker, text}] tech     ["names"]
tensions  [{ts, s, note}]          diarization [{ts, s, why}]
next_steps[{ts, s, commitment}]
fit       {aligned_on:[], unresolved:[], risks:[{who, note}]}
```

`speaker` is a participant `key`. Any `ts`/`s` pair that disagrees is a hard
error. Every section is optional except `meta`, `abstract` and `acts`; a section
with no data removes itself from the page rather than leaving an empty heading.

## Required gates — none are advisory, each names the fault

```
callsheet lexicon check work/transcript.txt --profile PROFILE   # before anything reads it
python -c "import json;from callsheet.schema import validate;validate(json.load(open('work/content.json')))"
callsheet lint-diagrams out/diagrams.html --turns work/turns.json
callsheet build …    # reports external requests; that count must be zero
```

## Rules that are not negotiable

- If it has a shape, it is a figure. Prose is for what does not.
- A claim without a timestamp does not go in the document.
- Quote text is copied, never tidied.
- A transcript correction is proposed, reviewed by a person, and recorded in the
  artifact. Nothing rewrites a transcript silently.
- The verifier runs in a fresh context, and its deletions are applied.
- Sealed material stays sealed until the artifact is final.
