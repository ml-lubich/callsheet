import { Reveal, STAGGER } from "../components/Reveal";
import { Skeleton } from "../components/Skeleton";
import { TimeLink } from "../components/TimeLink";
import { SpeakerChip } from "../components/SpeakerKey";
import { penClass } from "../lib/derive";
import type { Content, Deck, Turn } from "../types";

export function QuotesSkeleton() {
  return (
    <div className="sk-grid" style={{ gap: 34 }}>
      {[0, 1].map((i) => (
        <div className="sk-grid" key={i}>
          <Skeleton h={26} w="86%" />
          <Skeleton h={26} w="64%" />
          <Skeleton h={12} w="30%" mt={8} />
        </div>
      ))}
    </div>
  );
}

export function Quotes({
  quotes,
  deck,
  turns,
}: {
  quotes: NonNullable<Content["quotes"]>;
  deck: Deck;
  turns: Turn[];
}) {
  return (
    <div className="quotes">
      {quotes.map((q, i) => (
        <Reveal key={`${q.s}-${i}`} delay={i * STAGGER} className={`quote q${penClass(deck.keys, q.speaker).slice(1)}`}>
          <blockquote>{q.text}</blockquote>
          <figcaption className="attr">
            <SpeakerChip
              keys={deck.keys}
              spk={q.speaker}
              name={deck.names[q.speaker] || q.speaker}
            />
            <TimeLink ts={q.ts} s={q.s} turns={turns} />
          </figcaption>
        </Reveal>
      ))}
    </div>
  );
}
