You are merging the analysts' JSON into one `content.json`, the file the page is
built from. Every analyst's output and the call metrics are appended below.

Return **JSON only** — one object, no prose, no markdown fence.

```
meta      {title, subtitle, kind, date, duration_label, duration_s, turns, words,
           extra: [[label, value]], participants: [{key, name, role}]}
abstract  "90-120 words"
acts      [{n, title, span, start_s, end_s, summary, turning_point:{ts,s,text}}]
threads   [{name, what, why_it_matters, marks:[{ts,s}]}]
evidence  [{ts, s, claim, evidence, strength: strong|medium|weak}]
signals   [{ts, s, signal}]        numbers  [{ts, s, value, means}]
quotes    [{ts, s, speaker, text}] tech     ["names"]
tensions  [{ts, s, note}]          diarization [{ts, s, why}]
next_steps[{ts, s, commitment}]
fit       {aligned_on:[], unresolved:[], risks:[{who, note}]}
```

Rules the schema enforces, each of which fails the build by name:

- Acts must **tile the whole call**: `acts[0].start_s == 0`, each act starts
  exactly where the previous ended, the last ends at `metrics.duration_s`. Merge
  the segment analysts' acts across chunk boundaries rather than concatenating
  them.
- `span` is derived from `start_s`/`end_s` as `HH:MM:SS-HH:MM:SS`, never typed by
  hand.
- Every `ts`/`s` pair must agree, and `s` is an integer.
- `quotes[].speaker` is a participant `key`, not a name.

Rules nothing enforces, which are the ones that matter:

- Deduplicate threads by **meaning**, not by wording. A thread that surfaced in
  three chunks is one thread with three `marks`.
- Keep the earliest `ts` for any claim that appears more than once.
- **Keep the prose short.** `abstract` 90–120 words. Each act `summary` ≤ 60
  words. Each thread's `what` and `why_it_matters` one sentence each. Anything
  longer is a figure nobody has drawn yet — leave it for the diagram author.
- Merge every analyst's `shapes` into one ranked list under `shapes`, and drop
  the ones that are only a single relationship.
- Invent nothing. If two analysts disagree, keep what the transcript supports and
  drop the rest.
