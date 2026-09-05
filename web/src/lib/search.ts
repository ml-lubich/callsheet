/**
 * Transcript search that ignores where the spaces fell.
 *
 * Transcribers hear one name as two words, so "deepseek" has to find "deep seek" and
 * "deep seek" has to find "deepseek". Both haystack and needle are collapsed to their
 * non-whitespace characters, matched there, then the hit is mapped back onto the
 * original string so the highlight still lands on real text.
 */

export interface Span {
  text: string;
  hit: boolean;
}

/** The string with whitespace removed, plus original index of each surviving character. */
function squash(text: string): { flat: string; at: number[] } {
  let flat = "";
  const at: number[] = [];
  for (let i = 0; i < text.length; i++) {
    if (!/\s/.test(text[i])) {
      flat += text[i].toLowerCase();
      at.push(i);
    }
  }
  return { flat, at };
}

/** Character ranges of `query` inside `text`, spacing differences ignored. */
export function ranges(text: string, query: string): [number, number][] {
  const needle = squash(query).flat;
  if (!needle) return [];
  const { flat, at } = squash(text);
  const out: [number, number][] = [];
  let from = 0;
  for (;;) {
    const hit = flat.indexOf(needle, from);
    if (hit < 0) return out;
    out.push([at[hit], at[hit + needle.length - 1] + 1]);
    from = hit + needle.length;
  }
}

export function matches(text: string, query: string): boolean {
  return !squash(query).flat || ranges(text, query).length > 0;
}

/** `text` split into plain and matched spans, ready to render. */
export function segments(text: string, query: string): Span[] {
  const hits = ranges(text, query);
  if (!hits.length) return [{ text, hit: false }];
  const out: Span[] = [];
  let at = 0;
  for (const [start, end] of hits) {
    if (start > at) out.push({ text: text.slice(at, start), hit: false });
    out.push({ text: text.slice(start, end), hit: true });
    at = end;
  }
  if (at < text.length) out.push({ text: text.slice(at), hit: false });
  return out;
}
