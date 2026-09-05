# Incident postmortem

A two-person retro on an overnight outage. Nadia Brandt (site reliability engineer,
ran the incident) and Colm Ferreira (platform engineer, shipped the config change)
walk through the whole night in order: a connection-pool change lands on the wrong
default, nightly batch volume outruns it, a queue backlog grows unseen for half an
hour, Nadia restarts the ingest fleet on a reasonable-looking hunch, and the restart
— not the original backlog — is what turns it customer-visible, redelivering
unacknowledged messages as duplicate confirmation emails. Colm eventually finds his
own change is the cause, they coordinate a revert, and the backlog drains.

## What this example demonstrates

1. **The timeline figure on the incident's own wall clock, not the call's.**
   `expected/diagrams.html`'s `dg-incident-timeline` (catalog kind 5) plots the
   eight incident events on an axis running 0 to 187 real elapsed minutes, from
   the config change at 0148 UTC to the backlog reading zero at 0455 UTC — not on
   how far into this 46-minute recording each thing was said. Wall-clock incident
   times are written without a colon (`0214 UTC`, `0311 UTC`) throughout the
   transcript and the figures, because the diagram linter treats any `H:MM`-shaped
   string as a cited call timestamp, and these are not call timestamps at all.
2. **A causal chain from the config change to the customer-visible failure.**
   `dg-causal-chain` (catalog kind 2) traces config change → capped connections →
   backlog grows unseen → the restart (drawn off the main row, as the disputed
   step) → reconnect storm → redelivered messages → duplicate confirmation emails.
3. **Evidence graded honestly, including several claims that are asserted rather
   than shown.** `expected/content.json`'s `evidence` section carries 3 `strong`
   rows (a deploy log, a diff with a timestamp, a channel post — each a document
   the speaker has open while talking), 2 `medium` rows (a graph read live, a
   metric watched in the moment, but not saved), and 3 `weak` rows: Nadia's
   memory of the exact queue depth figure at 3am, her secondhand report of when
   duplicate emails started (she heard it from support, not watched it happen),
   and Colm's secondhand, unconfirmed claim about what customers were told. All
   three `weak` rows are exactly the ones where the speaker is going from memory
   or relaying something someone else told them.

## Running it

```
./run.sh
```

or, if `callsheet` isn't on your `PATH`:

```
CALLSHEET=../../.venv/bin/callsheet ./run.sh
```

This parses `transcript.txt`, copies the shipped `expected/content.json` and
`expected/diagrams.html` into place (standing in for the agent fan-out — see
`../agents/` for the real one), lints the figures against the transcript, and
builds `out/index.html`. The build reports the count of external requests; it
must be zero.

## What to look at in the output

- The three figures in `out/index.html`: the incident timeline, the causal chain,
  and a composition bar splitting the 187-minute incident into the four stretches
  the retro names (silent growth, the wrong fix, diagnosis, recovery) — with the
  two human decisions, the restart and the revert, carrying the same two pens
  across all three figures.
- The evidence table's strength column against its `evidence` text — each `weak`
  row names the "from memory" or "heard secondhand" basis that earns the grade.
- **Turns:** 48
