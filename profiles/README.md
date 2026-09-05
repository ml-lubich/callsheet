# profiles

A profile is a count of how one person writes: which terms they use and how
often, which two- and three-word phrasings they reach for, and two numbers
describing the length of the words in their sentences. `callgen lexicon` uses
it to recover domain vocabulary the recogniser mangled, and to flag phrasing the
speaker demonstrably never uses. See `skills/lexicon/SKILL.md` for when that
helps and how the corrections are reviewed.

## Build your own

Point it at things you wrote in your own words — design docs, READMEs, commit
messages, posts, a transcript you have already corrected by hand:

```
callgen lexicon build --from docs/ notes/*.md --name yourname -o profiles/yourname.local.json
```

Files, globs and directories all work, and binaries are skipped. Lowercase
vocabulary that no extractor can guess from capitalisation — `embeddings`,
`reciprocal rank fusion`, `idempotency` — goes in a plain list, one per line,
passed with `--terms`.

## It is safe to commit, and here is why

A profile is derived statistics, never message content:

- **terms** — a vocabulary with frequencies. `{"FAISS": 3, "reciprocal rank fusion": 2}`.
- **ngrams** — 2- and 3-word phrasings with frequencies. Nothing longer is
  stored, so no sentence can be reconstructed from it.
- **corpus** — how many documents and words went in.
- **register** — the mean and standard deviation of word length per sentence.

Before anything is counted, the text is scrubbed of email addresses, phone
numbers, URLs (credentials included) and street addresses. `tests/test_lexicon.py`
asserts that a corpus seeded with all three produces a profile containing none
of them.

That said, **a profile still reveals what you write about**, and a corpus of
private material yields a vocabulary of private subjects. `.gitignore` excludes
`profiles/*.local.json` and `corpus/`, so name a profile built from anything
private `*.local.json` and keep its source under `corpus/`.

## example-engineer.json

Built from this repository's own documentation plus a list of common
infrastructure and machine-learning vocabulary, so `callgen lexicon` does
something useful before you have written anything of your own. It is a starting
point, not a substitute for a profile of the person actually speaking — see the
last section of `skills/lexicon/SKILL.md`.

```
callgen lexicon check work/transcript.txt --profile profiles/example-engineer.json
```
