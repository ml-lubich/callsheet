import type { Deck, Metrics, TimelinePoint, Turn } from "../types";

export function mmss(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

export function median(values: number[]): number {
  const a = [...values].sort((x, y) => x - y);
  if (!a.length) return 0;
  const mid = a.length >> 1;
  return a.length % 2 ? a[mid] : Math.round((a[mid - 1] + a[mid]) / 2);
}

/** The timeline names speakers by display name; the rest of the data uses their key. */
export function keyOf(deck: Pick<Deck, "content" | "keys">, name: string): string {
  const hit = deck.content.meta?.participants?.find((p) => p.name === name);
  if (hit) return hit.key;
  return String(name || "").trim().charAt(0).toUpperCase() || deck.keys[0];
}

export function penIndex(keys: string[], key: string): number {
  return keys.indexOf(key);
}

export function penClass(keys: string[], key: string): "p0" | "p1" | "pn" {
  const i = penIndex(keys, key);
  return i === 0 || i === 1 ? (`p${i}` as "p0" | "p1") : "pn";
}

export function penVar(keys: string[], key: string): string {
  return ["var(--pen-a)", "var(--pen-b)"][penIndex(keys, key)] || "var(--pen-n)";
}

/** Index of the last turn that had started by `sec`. */
export function nearestTurn(turns: Turn[], sec: number): number {
  let lo = 0;
  for (let i = 0; i < turns.length; i++) {
    if (turns[i].s <= sec) lo = i;
    else break;
  }
  return lo;
}

export interface Stats {
  turns: number;
  /** share of all words, per participant key, rounded to whole percent */
  shares: { key: string; name: string; percent: number }[];
  longest: TimelinePoint;
  medianWords: number;
  estimatedTiming: boolean;
}

/** Everything under the strip chart, computed from the timeline rather than stated. */
export function stats(deck: Pick<Deck, "content" | "keys" | "names">, metrics: Metrics): Stats | null {
  const tl = metrics.timeline || [];
  if (!tl.length) return null;
  const words: Record<string, number> = {};
  for (const t of tl) {
    const k = keyOf(deck, t.spk);
    words[k] = (words[k] || 0) + t.words;
  }
  const total = Object.values(words).reduce((a, b) => a + b, 0) || 1;
  return {
    turns: tl.length,
    shares: deck.keys.map((key) => ({
      key,
      name: deck.names[key] || key,
      percent: Math.round(((words[key] || 0) / total) * 100),
    })),
    longest: tl.reduce((m, t) => (t.words > m.words ? t : m), tl[0]),
    medianWords: median(tl.map((t) => t.words)),
    estimatedTiming: Boolean(metrics.estimated_timing),
  };
}
