import { penClass, penVar, stats } from "../lib/derive";
import type { Deck } from "../types";

/**
 * Who was on the call and how much of it each of them was. The swatch is the pen that
 * speaker is drawn with everywhere else on the page — the chart, the quote rules, the
 * transcript margin — so the key is read once and holds for the whole document.
 *
 * Word share is measured from the timeline, not stated by the analysis.
 */
export function SpeakerKey({ deck, className }: { deck: Deck; className?: string }) {
  const people = deck.content.meta?.participants ?? [];
  if (!people.length) return null;

  const derived = stats(deck, deck.metrics);
  const share = new Map((derived?.shares ?? []).map((s) => [s.key, s.percent]));

  return (
    <ul className={["speakers", className].filter(Boolean).join(" ")}>
      {people.map((p) => {
        const percent = share.get(p.key);
        return (
          <li className="speaker" key={p.key}>
            <i className="swatch" style={{ background: penVar(deck.keys, p.key) }} aria-hidden="true" />
            <span className="who">{p.name}</span>
            {p.role && <span className="role">{p.role}</span>}
            {percent != null && (
              <span className="share num" title="share of all words spoken">
                {percent}%
              </span>
            )}
          </li>
        );
      })}
    </ul>
  );
}

/** "Ada Speaker" -> "AS". One word, one letter; anything unnamed falls back to the key. */
export function initials(name: string): string {
  const words = String(name || "").trim().split(/\s+/).filter(Boolean);
  return words.slice(0, 2).map((w) => w[0].toUpperCase()).join("") || "?";
}

/**
 * A speaker, named and colour-coded, small enough to sit in a transcript turn head or
 * under a quote. The disc carries the initials in that speaker's pen, so a reader
 * scanning the transcript knows who is talking before reading the name.
 */
export function SpeakerChip({
  keys,
  spk,
  name,
}: {
  keys: string[];
  spk: string;
  name: string;
}) {
  return (
    <span className={`chip ${penClass(keys, spk)}`}>
      <i className="chip-i" aria-hidden="true">
        {initials(name)}
      </i>
      <span className="chip-n">{name}</span>
    </span>
  );
}
