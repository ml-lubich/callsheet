import type { Content, Deck, Metrics, Turn } from "../types";

/** Resolve the four inputs into the one object the page passes around. */
export function deck(
  content: Content,
  turns: Turn[],
  metrics: Metrics,
  diagrams: string,
): Deck {
  const participants = content.meta?.participants ?? [];
  const keys = participants.length ? participants.map((p) => p.key) : ["A", "B"];
  const names: Record<string, string> = {};
  participants.forEach((p) => (names[p.key] = p.name));
  return {
    content,
    turns,
    metrics,
    diagrams,
    keys,
    names,
    duration: metrics.duration_s || content.meta?.duration_s || 1,
  };
}
