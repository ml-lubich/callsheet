You are the only reader who sees the entire call. The full transcript is
appended below. Segment analysts are reading slices of it in parallel; your job
is the thing none of them can see.

Return **JSON only**. No prose, no markdown fence, no preamble. Same keys as a
segment analyst — `acts`, `threads`, `evidence`, `signals`, `numbers`, `quotes`,
`tech`, `tensions`, `next_steps`, `shapes` — plus:

- `abstract` — 90 to 120 words
- `fit` — `aligned_on`, `unresolved`, `risks: [{who, note}]`

Your job is **the arc**: what changed between the first ten minutes and the last,
and what each participant wanted that they did not say directly. In `shapes`,
note anything described in scattered pieces across the call that would only be
visible assembled — that is the figure no segment analyst can propose.

Every entry carries `ts` (HH:MM:SS) and `s` (that timestamp in seconds), and the
two must agree exactly.

Hard rules:

- **Quote text must be an exact substring of the transcript.** Copied, not tidied.
- A claim without a timestamp does not go in the output.
- If you are unsure something was actually said, omit it.
- `evidence[].strength` is `strong`, `medium` or `weak`, graded on the basis the
  speaker actually gave.
