# Pipeline detail

Doctrine, rationale and prompt bodies for `SKILL.md`, relocated here to keep
the top-level pipeline outline short. Read the matching numbered section
before running that step for the first time.

## Pictures first

The output is not an essay with illustrations. A one-hour call gets **8–12
figures** that carry the argument, and prose kept short enough that a reader
uses it to check the figures rather than the other way round. Before writing
any paragraph, ask whether the thing it describes has a shape — an order, a
fan-out, a comparison, a magnitude, a position in time. If it does, draw it
and write a caption instead.

## Step 1 — transcribe

Audio never leaves the machine. If the recording has two or more voices and
the model did not diarize, say so in `meta` and fill the `diarization`
section later — never present unlabelled attribution as certain.

## Step 2 — check the vocabulary

The recogniser has no prior for the words the call is about, so it
substitutes the nearest ordinary English: FAISS becomes "fate face", BM25
becomes "abeam 25", SQLite becomes "SQL light". Every claim in this document
is supposed to trace to a timestamp, and a reader searching your spelling
finds nothing in a transcript that says "abeam 25". Worse, the analysts in
step 4 will read the garbled form and explain what they think it means.

`callgen lexicon check` exits nonzero when it finds anything, so it gates the
rest of the pipeline. Build a profile from the speaker's own writing when you
have it, and use the shipped one when you do not:

```
callgen lexicon build --from their/docs --name them -o profiles/them.json
```

**Read `work/lexicon.md` and decide each line yourself.** A phonetic match is
a guess; a guess applied silently is a fabrication that is now spelled
correctly. Then apply the ones you accept, re-parse, and keep the audit:

```
callgen lexicon apply work/transcript.txt --profile profiles/them.json --write
```

`work/transcript.txt.corrections.json` records every span, offset and score.
Carry it into `meta.extra` — a reader is entitled to know the transcript was
edited and how — and give it to the verifier in step 8.

Full sub-skill: **`skills/lexicon/SKILL.md`**.

## Step 3 — parse

Read `metrics.json` before dispatching anything: duration, turn count and the
word split tell you how many segment analysts the call actually needs. One
analyst per ~15–20 minutes; four is the usual number.

## Segment analyst prompt

One per chunk, self-contained:

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

## Whole-call reader prompt

The same JSON keys plus `abstract` (90–120 words) and `fit`, and one extra
instruction: *you are the only reader who sees the whole call, so your job is
the arc — what changed between the first ten minutes and the last, and what
each participant wanted that they did not say directly. In `shapes`, note
anything described in scattered pieces that would only be visible assembled.*

## Step 5 — synthesize

One agent, strongest model. It reads every `analysis-N.json` and `arc.json`
and writes `work/content.json`. Its rules:

- Acts must **tile the whole call**: `acts[0].start_s == 0`, each act starts
  where the previous ended, the last ends at `metrics.duration_s`. Merge the
  segment analysts' acts across chunk boundaries rather than concatenating
  them.
- Deduplicate threads by meaning, not by wording. A thread that surfaced in
  three chunks is one thread with three `marks`.
- Keep the earliest `ts` for any claim that appears more than once.
- `span` strings are derived from `start_s`/`end_s`, never typed by hand.
- **Keep the prose short.** `abstract` 90–120 words. Each act `summary` ≤ 60
  words. Each thread's `what` and `why_it_matters` one sentence each.
  Anything longer is a figure you have not drawn yet — hand it to step 6
  instead.
- Merge every analyst's `shapes` into one ranked list for the diagram agent,
  and drop the ones that are only a single relationship.

Validate before going further (see **Required gates**) — the schema names
the field that is wrong. The word caps are hard: `callgen lint-prose
work/content.json --mode MODE` names every field that is over, and the build
refuses the page rather than shipping it long.

## Step 6 — draw

One agent, strongest model, in its own context, following
**`skills/diagrams/SKILL.md`**. It reads `work/content.json`, `work/turns.json`
and `work/metrics.json` and writes `out/diagrams.html`: 8–12 inline
`<figure class="dg">` elements, hand-written SVG, coloured only through the
page tokens `var(--ink)`, `var(--ink-soft)`, `var(--grid)`, `var(--pen-a)`,
`var(--pen-b)`, `var(--paper)` and `var(--paper-2)`, so every figure follows
the light and dark palettes. No libraries, no `<img>`, no raster.

The sub-skill carries the catalog of twelve figure kinds, the house style,
the composition rules (a lead-in, and a bridge between consecutive figures,
so the set reads as one argument) and the self-check. A diagram that
restates a bullet list is not a diagram.

## Step 7 — build

`--mode` drops the sections the mode leaves out, reorders the rest, caps the
figure set and sets the transcript. Rendering the same call in a second mode
reruns steps 5 and 7 only.

The build fails loudly on a missing or duplicated template marker, escapes
the injected JSON so it cannot break out of its `<script>`, and reports the
number of external requests in the finished page. That number must be zero.

## Step 8 — verify

**Anything it cannot find is deleted, not hedged.** In the run this skill was
generalized from, that pass caught a per-case cost figure that no one had
said out loud, sitting in a finished diagram. Rebuild after the deletions and
run the verifier once more, in another fresh context.

## Step 9 — hold out

Near-zero 8-gram overlap is the evidence of independence; a nonzero 5- or
6-gram rate is expected, because both authors quote the same source. Nothing
from this step goes back into the document.

## JSON contract

`content.json` — see `src/callgen/schema.py` for the enforced version.

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
error. Every section is optional except `meta`, `abstract` and `acts`; a
section with no data removes itself from the page rather than leaving an
empty heading.

## Rules that are not negotiable

- If it has a shape, it is a figure. Prose is for what does not.
- A claim without a timestamp does not go in the document.
- Quote text is copied, never tidied.
- A transcript correction is proposed, reviewed by a person, and recorded in
  the artifact. Nothing rewrites a transcript silently.
- The verifier runs in a fresh context, and its deletions are applied.
- Sealed material stays sealed until the artifact is final.
