# The fan-out, run for real

`fanout.sh` is the orchestration `SKILL.md` describes, written out as a shell
script you can run. It drives the Claude Code CLI directly — one `claude -p`
invocation per role — so nothing about the pipeline is hidden inside an agent
harness you cannot inspect.

```
./fanout.sh ../product-review/transcript.txt
```

It expects `claude` and `callgen` on `PATH`. Everything else is an environment
variable with a sane default: `N` (segment analysts, default 4), `WORK`, `OUT`,
and one model variable per role.

## The stages

| # | Stage | Who | Reads | Writes |
|---|---|---|---|---|
| 1 | parse, chunk | nobody — the CLI | the transcript | `work/turns.json`, `work/metrics.json`, `work/chunkN.txt` |
| 2 | **fan-out** | N analysts **+** 1 whole-call reader, **in parallel** | one chunk each / the whole transcript | `work/analysis-N.json`, `work/arc.json` |
| 3 | synthesize | 1 agent | every analysis + the arc | `work/content.json` |
| 4 | draw | 1 agent | the analysis, the turns, the metrics | `out/diagrams.html` |
| 5 | build | nobody — the CLI | all of the above | `out/index.html` |
| 6 | verify | 1 agent, fresh context | **only** the page and the turns | `out/verification.txt` |

Stage 2 is the only parallel one, and it is parallel because the slices do not
depend on each other. Everything after it is a funnel.

Stages 1 and 5 are marked "nobody" on purpose: parsing, chunking, schema
validation, diagram linting and injection are mechanical, and a model doing them
is a model given the chance to be creative about a `<script>` boundary.

Two gates run inside the script, not after it: `content.json` is validated
against the schema before the diagram author is paid to read it, and
`lint-diagrams` runs before the build. Both fail the whole run.

## What it costs, in agents

With the default `N=4`:

```
4 analysts (cheap, parallel)  +  1 reader (strong, parallel)
1 synthesizer (strong)  +  1 diagram author (strong)  +  1 verifier (strong)
= 8 agent invocations for one call
```

The shape is deliberate. The analysts are the bulk of the token spend — they
each read a slice of the transcript and most of what they do is careful
extraction, which the cheap model does about as well as the expensive one. The
four roles that need judgement across the whole call are the ones on the strong
model, and there is exactly one of each.

Then add one verify pass per round of fixes. The verifier's deletions move text
around, so the loop is: verify, apply, rebuild, verify again in **another** fresh
context. Two consecutive clean passes, or the artifact is not done. Budget two or
three rounds.

## Swapping the models

Top of `fanout.sh`, five lines:

```bash
ANALYST_MODEL=${ANALYST_MODEL:-claude-sonnet-5}    # N of these, one per chunk
READER_MODEL=${READER_MODEL:-claude-opus-5}        # one, and it sees everything
SYNTH_MODEL=${SYNTH_MODEL:-claude-opus-5}
DIAGRAM_MODEL=${DIAGRAM_MODEL:-claude-opus-5}
VERIFIER_MODEL=${VERIFIER_MODEL:-claude-opus-5}
```

Each is overridable from the environment, so a whole run can go cheap without
editing anything:

```
ANALYST_MODEL=claude-haiku-4-5-20251001 N=6 ./fanout.sh ../product-review/transcript.txt
```

One role to leave alone: **the verifier.** It is the only stage whose failure is
silent — a weak verifier returns a short clean list and the document ships with
the fabrication still in it. Everything else fails loudly.

## The prompts

`prompts/` holds the actual text sent for each role, one file per role, read at
run time. Edit them without touching the script.

| File | Role |
|---|---|
| `segment-analyst.md` | one slice, JSON only, no inference beyond the slice |
| `whole-call-reader.md` | the whole call, the arc, the abstract |
| `synthesizer.md` | merge into `content.json`, acts must tile |
| `diagram-author.md` | 8–12 figures, house style, every timestamp real |
| `verifier.md` | adversarial fact-check, FABRICATED / WRONG / MISATTRIBUTED / IMPRECISE |

The hard rules are in every one of them and are not stylistic: quotes are exact
substrings, every claim carries a timestamp, JSON only, invent nothing.

## Failure handling

Every stage is checked for a non-empty output file, and a stage that produced
nothing fails the run naming itself:

```
fanout: stage 'segment analyst 3' produced no work/analysis-3.json — rerun that
stage alone and read what the model said
```

That check exists because the alternative is worse: an empty `analysis-3.json`
flows into the synthesizer, which quietly writes a `content.json` covering three
quarters of the call, and the missing quarter shows up as an act-tiling error
several stages later — or not at all.
