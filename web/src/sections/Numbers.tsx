import { Reveal, STAGGER } from "../components/Reveal";
import { TimeLink } from "../components/TimeLink";
import type { Content, Turn } from "../types";

export function Numbers({
  rows,
  turns,
}: {
  rows: NonNullable<Content["numbers"]>;
  turns: Turn[];
}) {
  return (
    <ul className="rows">
      {rows.map((r, i) => (
        <Reveal as="li" key={`${r.s}-${i}`} delay={i * STAGGER}>
          <TimeLink ts={r.ts} s={r.s} turns={turns} />
          <div>
            <div className="val">{r.value}</div>
            <div className="means">{r.means}</div>
          </div>
        </Reveal>
      ))}
    </ul>
  );
}
