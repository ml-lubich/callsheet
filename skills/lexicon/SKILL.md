---
name: callsheet-lexicon
description: Build a profile of how one person writes, then use it to recover domain vocabulary a local speech recogniser mangled and to flag phrasing that speaker never uses. Use after callsheet transcribe and before any agent reads the transcript, whenever the conversation is full of product names, libraries, acronyms or in-house jargon.
---

# Lexicon

Local speech recognition has no prior for the words a conversation is actually
about. It has heard "face" ten thousand times and FAISS never, so it writes what
it knows. From one real interview:

| said | transcribed |
|---|---|
| FAISS | "fate face" |
| Cognee | "cockney", "colony" |
| LangGraph | "land graph" |
| BM25 | "abeam 25" |
| reciprocal rank fusion | "rank reciprocal factor" |
| SQLite | "SQL light" |
| ChromaDB | "Chrome IDB" |

Two things go wrong, and the second is worse. A reader who searches the
write-up's spelling finds nothing in the transcript, so the document's promise —
every claim traces to a timestamp — quietly stops being true. And an agent
reading "abeam 25" downstream will explain what it thinks that means. The
transcript now contains a plausible sentence nobody said, which is the exact
failure `skills/verify/SKILL.md` exists to catch, arriving one step earlier than
the verifier looks.

## When a profile helps

When the call is full of names the recogniser has no prior for: libraries,
products, acronyms, internal systems, people. It does nothing for an ordinary
conversation about ordinary things, and a profile built from a corpus that
shares no vocabulary with the call is worse than none — it will propose the
words it knows.

## Build one from the speaker's own writing

Anything that person wrote in their own words: design docs, README files,
commit messages, published posts, an earlier transcript they have already
corrected. Two thousand words is enough to be useful.

```
callsheet lexicon build --from docs/ notes/*.md --name ada -o profiles/ada.json
```

Files, globs and directories all work; binaries are skipped. Lowercase
vocabulary no extractor can guess — `embeddings`, `reciprocal rank fusion` —
goes in a plain list, one term per line:

```
callsheet lexicon build --from docs/ --name ada --terms vocab.txt -o profiles/ada.json
```

A profile holds counts, not prose: term frequencies, 2- and 3-gram frequencies,
and two register statistics. Email addresses, phone numbers, URLs and street
addresses are stripped before anything is counted. See `profiles/README.md`.

## Check the transcript, before anything reads it

```
callsheet lexicon check work/transcript.txt --profile profiles/ada.json -o work/lexicon.md
```

It prints two lists and exits nonzero if either is non-empty, so it gates a
pipeline:

- **corrections** — spans that sound like the speaker's vocabulary but are not
  spelled like it, with character offsets, a score and a reason.
- **suspicion flags** — sentences whose phrasing is absent from the profile *and*
  whose register sits far from it. That pair is what invented text looks like;
  either signal alone is noise.

## Corrections are proposed, never applied

This is the rule the whole feature turns on. A fuzzy phonetic match is a guess,
and a guess applied silently is indistinguishable from the fabrication the
verifier hunts for — worse, it is now spelled correctly and looks authoritative.

Read the review file. Decide each line. Then, if you accept them:

```
callsheet lexicon apply work/transcript.txt --profile profiles/ada.json --write
```

Without `--write` nothing is written and the command exits nonzero. With it, an
audit lands beside the output as `<transcript>.corrections.json`, recording every
span, offset, suggestion and score. **Re-parse after applying** — offsets move —
and carry the audit through to the artifact, so a reader can see that the
transcript was edited and exactly how.

## What it will get wrong

- **A mangled term with no surviving context is not recovered.** A correction
  only fires near vocabulary that came through intact, because without that
  guard "the colony was cold" becomes Cognee. If every domain word in a stretch
  is mangled, that stretch recovers nothing, and you are back to reading it.
- **A word the speaker really said, that happens to sound like a term.** Rare,
  because a single intact word must be a near-homophone to match at all, but it
  happens. This is why you read the list.
- **A profile of the wrong person.** The guardrail is only as good as the corpus.
  Never build one from the interviewer's writing and run it over the
  interviewee's speech.
