# Product review — bulk-import flow

An invented internal design review: three people on a shift-scheduling tool argue over what a
CSV bulk-import should do when a row in the file is bad, agree on an answer, and then reverse
it once a piloting enterprise account turns out to have an export that will never be clean.

- Priya Raghavan — design lead
- Tomas Halvorsen — engineer
- Wren Okafor — support lead

## What this example demonstrates

1. **More than two speakers.** All three participants argue, concede points, and change their
   minds across the call — this is not a two-person interview.
2. **A decision reached, then reversed.** The group agrees at 00:19:25 to reject an entire
   uploaded file if any row fails validation, reaffirms that spec at 00:45:50 despite evidence
   against it, and reverses it at 00:52:45 once the pilot account's export is shown to be
   permanently unclean. Both the acts and `tensions` in `expected/content.json` carry the
   reversal.
3. **The two-column comparison figure carrying the argument.** `expected/diagrams.html` figure
   `dg-reject-vs-partial` lays reject-the-file against partial import on the four dimensions the
   call actually argued about — one bad row, what the customer sees, the nightly pilot account,
   and support turnaround — with the named dimension down the middle.

- **Turns:** 52

## Running it

```
./run.sh
```

or, if `callsheet` isn't on your `PATH`:

```
CALLSHEET=../../.venv/bin/callsheet ./run.sh
```

This parses `transcript.txt`, chunks it, drops in the shipped `expected/content.json` and
`expected/diagrams.html` in place of the agent fan-out, lints the figures against the real
transcript, and builds `out/index.html`. Everything under `work/` and `out/` is generated.

## What to look at

- `out/index.html` — the finished page. Check that the abstract and acts match the three-figure
  set, and that the reversal reads the same way in the prose and in the timeline figure.
- `expected/diagrams.html` — three figures: a ticket-mix magnitude comparison (the evidence), the
  two-column reject-vs-partial comparison (the argument), and a timeline of when the decision was
  made and reversed. One pen per person throughout: Priya Raghavan and Wren Okafor each hold a
  pen across all three figures; Tomas Halvorsen's framing is unattributed ink-soft structure.
