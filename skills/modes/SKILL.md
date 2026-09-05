---
name: callgen-modes
description: Choose and apply an output mode for a callgen artifact — the preset that decides the register the synthesizer writes in, which sections render and in what order, the prose and figure budgets, and what the verdict optimises for. Use before step 5 (synthesize) and again at step 7 (build).
---

# Modes

A mode is a named preset over three things:

1. **Register** — how the prose is written. It reaches the synthesizer as text,
   through `callgen.modes.prompt_guidance(name)`.
2. **Shape** — which sections render, in what order, each section's word budget
   and the cap on the figure set. It reaches the page as a `_mode` block inside
   `content.json`, and the template obeys it.
3. **Emphasis** — what the verdict, the evidence and the figures optimise for.

**A mode changes shape and register. It never changes facts.** Dropping a
section removes it from the document, not from the transcript; nothing is
added, softened, reweighted or invented to make a mode fit. If a claim will not
fit the budget it is cut, not hedged. Every mode still runs through the same
schema gate, the same diagram lint and the same adversarial verify.

## The modes

`callgen modes` prints this list with one-line summaries.

**`professional`** *(default)* — the current behaviour. Neutral, unhurried
register; third person where it reads naturally, first person where quoting;
contractions fine. Every section renders in template order and the figure set
runs to 8–12. The verdict states what was decided and then what remains open,
evidence is ranked by strength rather than by order of appearance, and the
figures cover the whole call rather than its most quotable minute. This is the
mode to reach for when you do not have a reason to reach for another.

**`concise`** — the professional register with every sentence paid for: one
clause where two were used, every prose budget halved. Threads and signals stop
being their own sections and fold into the abstract, a sentence each. The figure
set is capped at six, chosen for coverage per square inch, and the transcript
renders collapsed. The verdict comes first and fits in two sentences; evidence
that merely corroborates is dropped.

**`formal`** — third person throughout, no contractions, no quoted slang, no
rhetorical questions, participants named by role on first mention. The verdict
is written as numbered findings rather than as a recommendation. The evidence
table leads the document and the figures follow it, ten at most, each caption
citing the timestamps it was built from. Findings before interpretation.

**`casual`** — second person, contractions, short sentences, the reader
addressed directly. The quotes lead and carry the voice of the call; commentary
between them stays brief. The verdict reads as a note to a friend who asked how
it went. Evidence is mentioned in passing rather than tabulated at length, and
the figure set is the lighter six.

**`interesting`** — opens on the three most surprising moments of the call —
the tensions and the turning points — and says why each was surprising. Every
thread is reframed as the thing nobody said out loud: what the participants were
circling, in the words they avoided. The verdict names what *changed* during the
call rather than what was concluded, and the eight figures are chosen for
surprise rather than for completeness, so a figure that confirms the obvious is
cut. Nothing here licenses manufacturing a tension the transcript does not
support.

**`summarized`** — abstract, verdict, one composite figure and the numbers.
Nothing else, under 400 words of prose in total, no transcript. Threads and
signals collapse into a `highlights` list of at most five: the things that would
change a reader's mind. One reader, two minutes, no scrolling.

**`compact`** — everything, but dense. Every section renders, budgets halved,
one line per item, no bridging sentences, tables wherever a table will do,
figures drawn at half height with one-line captions, transcript collapsed.
Nothing is dropped; everything is shortened. For the reader who wants all of it
on two screens.

**`creative`** — the editorial register turned up. A titled essay paragraph
opens the document and earns the reader's attention without overstating the
call. Figures carry narrative captions that move the argument forward, quotes
are set large and used as beats, and the verdict is a closing paragraph rather
than a box. The abstract, caption and quote budgets are the generous ones.
Evidence supports the essay instead of interrupting it, and nothing is
dramatised past what was said.

**`diagrams-only`** — the figure set with its lead-in and its bridges, the strip
chart, and the numbers. No acts, threads, evidence, quotes or transcript. The
figures *are* the document, so the bridges between consecutive figures have to
carry the argument; every claim lives in a figure or in a number.

## The caps are hard

Budgets are not advice. `callgen build` refuses a `content.json` whose prose
runs over, and names every field with its word count and its excess. Per mode,
scaled from the professional defaults — `summarized` and `compact` at 0.6,
`concise` at 0.75, `creative` at 1.3:

| Cap | Professional | Applies to |
|---|---|---|
| abstract | the mode's abstract budget | `abstract` |
| paragraph | 70 | every paragraph of every prose field |
| act summary | 60 | `acts[].summary` |
| thread | 55 | `threads[].what`, `threads[].why_it_matters` |
| list item | 30 | signals, tensions, numbers, diarization, next steps, evidence claims, fit items, turning points |

Quote text is never capped. Trimming a quote to a word count falsifies it.

Check before you build, and get the same list without the failure:

```
callgen lint-prose work/content.json --mode concise
```

`lint-prose` also fails on a **wall of text**: three consecutive prose sections
— abstract, acts, threads, quotes, fit — with no figure, table or list between
them. Break the run with a figure. Every built-in mode's section order already
satisfies this; a project mode that does not will be told so.

## Register rules, in every mode

`prompt_guidance` ends with the same block for every mode:

- No analogies and no metaphors. Say the thing.
- No scare quotes around ordinary words.
- No "essentially", "basically", "simply".
- No sentence that restates the sentence before it.
- Every paragraph opens with the fact, not the framing.
- Concepts over words: a sentence describing a structure — an order, a fan-out,
  a comparison, a magnitude, a position in time — is a figure you have not drawn
  yet. It goes in a `shapes` entry for the diagram agent, not into the prose.

## Choosing one

| The reader | The mode |
|---|---|
| Was not on the call and will act on it | `professional` |
| Has five minutes and one decision to make | `concise` |
| Is a board, a regulator, or a case file | `formal` |
| Was on the call and wants the feel of it back | `casual` |
| Is deciding whether this call mattered | `interesting` |
| Is forwarding it to someone else | `summarized` |
| Wants all of it and reads fast | `compact` |
| Is being persuaded, not briefed | `creative` |
| Is in the room with the figures on a screen | `diagrams-only` |

When in doubt, `professional`. A mode chosen to flatter the material is a mode
chosen wrong.

## Using it

Before synthesis, put the register and emphasis into the synthesizer prompt:

```
python -c "from callgen.modes import prompt_guidance; print(prompt_guidance('concise'))"
```

At build time, name the same mode:

```
callgen build --content work/content.json --turns work/turns.json \
                --metrics work/metrics.json --diagrams out/diagrams.html \
                --mode concise -o out/index.html
```

`callgen.modes.apply(content, mode)` is what the build calls. It returns a new
content dict with the dropped sections gone and a `_mode` block added carrying
the mode name, the section order, the budgets, the figure cap and the transcript
setting. **Prose over budget is not truncated** — a paragraph cut to a word
count is a mutilated paragraph, so the budget goes to the writer, and the page
records what was asked for. Naming a mode that does not exist fails with the
list of the ones that do.

Rendering the same call twice in two modes is cheap: the analysis does not
change, only steps 5 and 7 rerun.

## A project's own modes

A project may declare its own in `.callgen/modes.json`, merged over the
built-ins. Reusing a built-in's name overrides only the fields you state; a new
name inherits the unstated fields from `professional`:

```json
{
  "concise": { "figures": 4 },
  "board-pack": {
    "register": "Third person, past tense, no jargon a director would have to look up.",
    "emphasis": "Money, dates and owners first. Everything else is context.",
    "sections": ["strip", "abstract", "numbers", "figures", "next"],
    "budgets": { "abstract": 90, "numbers": 20, "figures": 40, "next": 25 },
    "figures": 4,
    "transcript": "omit",
    "summary": "the four numbers, the four figures and who owes what by when"
  }
}
```

The file is validated on load and every failure names the mode and the field:
section ids must be known, budgets must be positive whole numbers of words,
`figures` a whole number, `transcript` one of `open`, `collapsed`, `omit`.

The section ids, in template order:

```
strip  abstract  highlights  figures  acts  threads  evidence  signals
numbers  tech  friction  quotes  fit  next  transcript
```

`strip`, `figures` and `transcript` are drawn from the metrics, the injected
figure fragment and `turns.json` rather than from `content.json`, so they cannot
be emptied by the analysis — only by a mode leaving them out. `transcript` is
kept in step with the `transcript` setting automatically: `omit` removes it,
anything else keeps it last.
