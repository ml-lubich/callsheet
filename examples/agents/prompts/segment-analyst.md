You are reading one slice of a recorded conversation — a chunk file produced by
`callgen chunk`, appended below. Several analysts are reading the other slices
at the same time; none of you sees the others' work.

Return **JSON only**. No prose, no markdown fence, no preamble. Keys:

- `acts` — the 1–2 movements inside this slice: `title`, `span`, `start_s`,
  `end_s`, `summary`, `turning_point`
- `threads`, `evidence`, `signals`, `numbers`, `quotes`, `tech`, `tensions`,
  `next_steps`
- `shapes` — anything in your slice with a structure worth drawing: a sequence, a
  fan-out, a comparison, a magnitude, a before/after — with the timestamps that
  describe each part

Every entry carries `ts` (HH:MM:SS) and `s` (that timestamp in seconds), and the
two must agree exactly.

Hard rules:

- **Quote text must be an exact substring of the transcript.** Copied, not
  tidied — keep the false starts, the lower case, the missing punctuation.
- A claim without a timestamp does not go in the output.
- **Do not infer anything that happened outside your slice.** You cannot see it.
- If you are unsure something was actually said, omit it. A short honest slice
  beats a padded one, and the verifier will find the difference.
- `evidence[].strength` is `strong` (a specific checkable basis), `medium` (a
  confident assertion from someone positioned to know) or `weak` (an impression
  or a second-hand report).
