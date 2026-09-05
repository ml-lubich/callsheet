import { Reveal, STAGGER } from "../components/Reveal";
import { Skeleton } from "../components/Skeleton";
import { TimeLink } from "../components/TimeLink";
import type { Content, Turn } from "../types";

export function RowsSkeleton({ n = 3 }: { n?: number }) {
  return (
    <div className="sk-grid">
      {Array.from({ length: n }, (_, i) => (
        <div className="sk-row" key={i}>
          <Skeleton h={13} />
          <Skeleton h={13} w={i % 2 ? "78%" : "94%"} />
        </div>
      ))}
    </div>
  );
}

export function Signals({
  rows,
  turns,
}: {
  rows: NonNullable<Content["signals"]>;
  turns: Turn[];
}) {
  return (
    <ul className="rows">
      {rows.map((r, i) => (
        <Reveal as="li" key={`${r.s}-${i}`} delay={i * STAGGER}>
          <TimeLink ts={r.ts} s={r.s} turns={turns} />
          <div>{r.signal}</div>
        </Reveal>
      ))}
    </ul>
  );
}
