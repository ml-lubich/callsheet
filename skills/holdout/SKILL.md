---
name: callgen-holdout
description: Seal someone else's write-up of the same call before the analysis starts, refuse to read it during the build, and measure n-gram overlap afterwards to show the two readings were independent. Use whenever a reference answer exists.
---

# Hold out

Someone has already written up this call. That write-up is the most useful thing
in the room and also the most dangerous: read a paragraph of it and you can no
longer tell which of your findings you found.

So the reference is sealed before anything starts, the build is prevented from
opening it, and the resemblance is measured only after the artifact is frozen.
The point is not to score well. The point is that the comparison afterwards
means something, which it cannot if the two readings were ever in contact.

## 1. Seal, before step 3 of the pipeline

Put the reference under `sealed/` and seal it *before the first analyst runs*.
Sealing after the fact proves nothing.

```
callgen seal sealed/
```

This makes every file read-only and records a sha256 of each in
`sealed.sha256`. The hashes are the evidence that the reference did not change
mid-run — a reference edited to match your output would otherwise be
indistinguishable from a good result.

## 2. Refuse to read it, during steps 3–7

Nothing under `sealed/` is opened during analysis, synthesis, diagrams, build or
verification. Not to check a name. Not to resolve an ambiguity. Not "just the
headings".

This is enforced, not promised:

```python
from callgen.holdout import sealed_guard

with sealed_guard("sealed/"):
    ...run the analysis...
```

`sealed_guard` raises if anything under that directory is opened while it is
active. Run the whole build inside it. "We did not read it" then becomes a
property of the run rather than a claim in a report.

If you are dispatching subagents, none of them gets the path either. The most
likely way this breaks is an agent given a broad "read everything in the project
directory" instruction, which is exactly the kind of instruction that sounds
harmless.

## 3. Compare, after the artifact is final

Only once `out/index.html` is built, verified twice and frozen:

```
callgen compare out/index.html sealed/
```

It re-checks every hash — a broken seal invalidates the whole exercise and it
will say so — then prints, for each reference file, the share of that file's
n-grams that also appear in your artifact.

## What the numbers mean

Overlap is reported as a share **of the reference**, at two window sizes.

- **A near-zero 8-gram (or 10-gram) overlap is the evidence.** Eight consecutive
  words in common is not something two independent writers produce by accident;
  it is a sentence, and sentences travel by copying. Near zero means the two
  documents were written from the source, separately. That is the finding.
- **A nonzero 5-gram or 6-gram rate is expected and is not a problem.** Both
  authors quote the same transcript, name the same systems, and use the same
  numbers, so short runs collide constantly — "about eighty per cent of the",
  "before the driver leaves the". Low single digits is normal. A 6-gram share
  that is *zero* is mildly suspicious: it suggests one of the documents is not
  quoting the source much.
- **Read the direction.** The denominator is the reference, so the number answers
  "how much of theirs is in mine", not the reverse. A short reference against a
  long artifact will read higher for purely mechanical reasons.
- **A high 8-gram share means a leak, not a compliment.** Find where the seal
  failed. It has never meant two people wrote the same sentence.

## What this is not

It is not a similarity score to raise, and it is not an accuracy measure. Two
independent readings of the same call can agree on every fact and share almost no
phrasing; they can also disagree completely and share plenty, because both quote
the transcript. Overlap measures contact, nothing else.

**Nothing from this step goes back into the document.** Not a correction, not an
addition, not a "they mentioned something we missed". The comparison happens
after the artifact is frozen precisely so it cannot contaminate it. If the
reference turns out to contain something genuinely important that you missed,
that is a finding about the run — write it in a separate note, outside the
artifact, and leave the artifact alone.
