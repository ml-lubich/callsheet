---
name: callsheet-verify
description: Adversarially fact-check a finished callsheet artifact against the transcript, in a fresh context, grading defects FABRICATED / WRONG / MISATTRIBUTED / IMPRECISE and deleting what cannot be traced. Use after callsheet build and before the artifact is shown to anyone.
---

# Verify

You are checking a document you did not write. That is the whole design: an
author cannot audit their own reading, because the thing they would need to
notice is the thing they already believe.

**Run this in a fresh context.** If you took part in the analysis, the
synthesis, or the diagrams, you are not the verifier. Start a new agent, hand it
only the two files below, and give it nothing else — no summary, no "here is
what we found", no reassurance about which parts are solid.

## Inputs, and the rule about them

```
out/index.html      the finished artifact
work/turns.json     the parsed transcript
```

**`work/turns.json` is the only source of truth.** Not your knowledge of the
domain, not what is obviously true, not what the speakers plainly meant. If a
claim is correct about the world but was not said on this call, it does not
belong in a document whose entire premise is that every claim traces to a
timestamp. Mark it and move on.

You will be tempted to reason from plausibility. A figure like "about 30%" sits
comfortably next to numbers that were said, so it reads as safe. Search for it.
On the run this skill was generalized from, that exact impulse was the test:
a per-case cost figure nobody had spoken had propagated through the analysis into
a finished diagram, keyed to a real timestamp, phrased in the speaker's register.
Everything about it looked right except that it was not in the transcript.

## Grades

Report every defect at one of four levels, worst first. The grade decides the fix.

| Grade | What it means | Fix |
|---|---|---|
| **FABRICATED** | Nothing in the transcript supports it. A number, name, entity or relationship that was never said. | **Delete.** Not soften, not hedge, not "roughly". |
| **WRONG** | It was said, and the document has it wrong — the value, the direction, the sign, the unit. | Correct to what was said, or delete if the correction guts the claim. |
| **MISATTRIBUTED** | Said by someone else, or drawn in the wrong speaker's pen, or credited to the wrong side of a disagreement. | Reattribute. |
| **IMPRECISE** | Supported, but stated more confidently or more specifically than the source warrants. | Weaken to what the transcript supports. |

**A figure the verifier cannot locate in the transcript is deleted, not
softened.** Turning an unsupported "$40 per case" into "a meaningful per-case
cost" does not fix the defect, it hides it — the document now asserts something
unfalsifiable in place of something false, and the next reader has no way to
catch it. Delete the claim and, if the surrounding sentence collapses without it,
delete the sentence.

## The checks

Work through all of them. Report every defect with the grade, the exact text in
the artifact, and either the supporting timestamp or `UNSUPPORTED`.

1. **Quotes are verbatim.** Every string in the quotes section must be an exact
   substring of some turn's text. Not tidied, not de-ummed, not repunctuated. An
   ellipsis is only allowed where material was actually cut, and both sides of it
   must match exactly.
2. **Every numeral is traced.** Walk every digit in the document — abstract,
   acts, evidence, signals, numbers, quotes, diagram labels, diagram keys,
   captions, bridges — and find the turn that says it. Percentages, counts,
   durations, money, versions, dates, model numbers, headcounts. A number derived
   by arithmetic from two spoken numbers is acceptable only if the document shows
   the arithmetic; otherwise it is FABRICATED.
3. **Every timestamp resolves.** Each `ts` must be the start of an actual turn in
   `turns.json`, and the claim attached to it must be in *that* turn or the one or
   two immediately following. A timestamp that resolves to a turn about something
   else is worse than a missing one, because it survives a spot check.
4. **Act spans tile.** `acts[0].start_s == 0`; each act starts exactly where the
   previous ended; the last ends at `metrics.duration_s`. No gap, no overlap. A
   gap means a stretch of the call vanished from the record.
5. **Thread marks land.** Every mark on every thread points at a turn where that
   thread is actually present. A thread with three marks that only really appears
   twice is an inflated thread.
6. **Evidence strengths are honest.** `strong` means the speaker gave a specific,
   checkable basis — a measurement, a document, a named system they operate.
   `medium` is a confident assertion from someone positioned to know. `weak` is
   an impression or a second-hand report. Grade-inflation here is the most common
   defect in an otherwise clean document, and it is IMPRECISE, not cosmetic.
7. **Diagram nodes correspond to something said.** For every node in every
   figure, find the turn. The numbered key gives you the author's claim; verify
   it rather than trusting it. Check the *edges* too: a connection drawn between
   two real nodes that nobody described is FABRICATED, and it is easy to miss
   because both endpoints check out.
8. **Speaker attribution is correct.** Every quote, every commitment, every
   position in a disagreement, and every pen colour in every figure. Confirm the
   pen-to-speaker mapping is the same in all figures — a swap in one figure
   silently reassigns an argument.
9. **The abstract asserts nothing new.** Anything in the abstract must appear,
   supported, further down. Summaries are where unsupported synthesis hides.
10. **Diarization honesty.** If the transcript was not reliably diarized, the
    document must say so, and attributions must not be stated as certain.

## Output

A list. One line per defect:

```
FABRICATED  diagram dg-unit-economics, node 6 "$40 per case"  UNSUPPORTED
WRONG       evidence row 4 "eighty per cent"  transcript says "about eighty" at 00:01:02
IMPRECISE   evidence row 9 strength=strong    basis is one anecdote at 00:44:10
```

Then a one-line verdict: how many of each grade, and whether the document is
publishable after the deletions.

Do not rewrite the document. Do not propose better wording. Do not soften your
own findings because there are a lot of them — a long defect list from a fresh
verifier is the system working.

## After the pass

The author applies every deletion and correction, rebuilds, and runs the
verifier **again, in another fresh context**. The second pass exists because
deletions move text around and rebuilt pages have re-broken things before. Two
consecutive clean passes, or the artifact is not done.
