---
name: callsheet
description: Turn a recording or transcript of a call, meeting or interview into one self-contained HTML document that someone who was not there can read, where every claim traces to a timestamp. Use when the user has audio, video or a transcript and wants a shareable written artifact, a briefing, a readout, or an "what happened on this call" page — including when they want it checked against someone else's write-up of the same call.
---

# callsheet

Pipeline: **transcribe → parse → analyse (agents) → build → verify → hold out.**
Python owns the mechanical steps. The analysis is yours; the CLI only produces the
files you read and validates the JSON you hand back.

Install: `pip install -e .` in the callsheet repo. Everything runs locally.

## 1. Transcribe (skip if a transcript already exists)

```
callsheet transcribe CALL.m4a -m ~/models/ggml-large-v3.bin -o work/transcript -t 8
```

Audio never leaves the machine. If the recording has two or more voices and the
model did not diarize, say so in `meta` and fill the `diarization` section later —
never present unlabelled attribution as certain.

## 2. Parse

```
callsheet parse work/transcript.txt -o work     # -> work/turns.json, work/metrics.json
callsheet chunk work/turns.json -n 4 -o work    # -> work/chunk1.txt … work/chunk4.txt
```

Read `metrics.json` before dispatching anything: duration, turn count and the
word split tell you how many segment analysts the call actually needs. One
analyst per ~15–20 minutes; four is the usual number.

## 3. Analyse — the fan-out

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
> `tech`, `tensions`, `next_steps`. Every entry carries `ts` (HH:MM:SS) and `s`
> (that timestamp in seconds). **Quote text must be an exact substring of the
> transcript.** Do not infer anything that happened outside your slice. If you
> are unsure a figure was actually said, omit it.

**Whole-call reader prompt** — the same JSON keys plus `abstract` (150–200 words)
and `fit`, and one extra instruction: *you are the only reader who sees the whole
call, so your job is the arc — what changed between the first ten minutes and the
last, and what each participant wanted that they did not say directly.*

## 4. Synthesize

One agent, strongest model. It reads every `analysis-N.json` and `arc.json` and
writes `work/content.json`. Its rules:

- Acts must **tile the whole call**: `acts[0].start_s == 0`, each act starts where
  the previous ended, the last ends at `metrics.duration_s`. Merge the segment
  analysts' acts across chunk boundaries rather than concatenating them.
- Deduplicate threads by meaning, not by wording. A thread that surfaced in three
  chunks is one thread with three `marks`.
- Keep the earliest `ts` for any claim that appears more than once.
- `span` strings are derived from `start_s`/`end_s`, never typed by hand.

Validate before going further — the schema names the field that is wrong:

```
python -c "import json,sys;from callsheet.schema import validate;validate(json.load(open('work/content.json')))"
```

## 5. Diagrams

One agent, and only if the call actually described a mechanism worth drawing
(a pipeline, a decision path, a before/after). It writes `out/diagrams.html`:
inline `<figure class="dg">` elements with hand-written SVG, themed through
`var(--ink)`, `var(--pen-a)`, `var(--pen-b)`, `var(--grid)` so they follow the
page's light and dark palettes. No external libraries, no `<img>`, no raster.
Two to four figures. A diagram that only restates a bullet list is not a diagram.

## 6. Build

```
callsheet build --content work/content.json --turns work/turns.json \
                --metrics work/metrics.json --diagrams out/diagrams.html \
                -o out/index.html
```

The build fails loudly on a missing or duplicated template marker, escapes the
injected JSON so it cannot break out of its `<script>`, and reports the number of
external requests in the finished page. That number must be zero.

## 7. Verify — adversarial, in a fresh context

One agent that has **not** seen the analysis. Give it `out/index.html` and
`work/turns.json` and nothing else:

> Every number, name, date and quoted line in this document must appear in the
> transcript. For each one, give the timestamp that supports it, or mark it
> UNSUPPORTED. Do not soften an unsupported figure into a vaguer one — report it
> for deletion.

**Anything it cannot find is deleted, not hedged.** In the run this skill was
generalized from, that pass caught a cost figure that no one had said out loud.
Rebuild after the deletions and run the verifier once more.

## 8. Hold out (only when a reference answer exists)

If someone else has already written up the same call, seal it *before* the
analysis starts:

```
callsheet seal sealed/          # read-only + sha256 in sealed.sha256
```

Nothing reads that directory during steps 3–7. `callsheet.holdout.sealed_guard`
raises if anything tries. After the build is final and frozen:

```
callsheet compare out/index.html sealed/
```

It verifies the seal is intact and prints 6-gram and 10-gram overlap as a share
of the reference. Low single digits is the expected result for two independent
readings of the same call; it is evidence of independence, not a score to
optimize. Nothing from this step goes back into the document.

## JSON contract

`content.json` — see `src/callsheet/schema.py` for the enforced version.

```
meta      {title, subtitle, kind, date, duration_label, duration_s, turns, words,
           extra: [[label, value]], participants: [{key, name, role}]}
abstract  "150-200 words"
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

## Rules that are not negotiable

- A claim without a timestamp does not go in the document.
- Quote text is copied, never tidied.
- The verifier runs in a fresh context, and its deletions are applied.
- Sealed material stays sealed until the artifact is final.
