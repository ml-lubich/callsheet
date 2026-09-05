import { Reveal, STAGGER } from "../components/Reveal";
import { Skeleton } from "../components/Skeleton";
import { TimeLink } from "../components/TimeLink";
import type { Content, Turn } from "../types";

export function LandsSkeleton() {
  return (
    <div className="lands">
      {[0, 1, 2].map((i) => (
        <div className="land" key={i}>
          <Skeleton h={19} w="64%" />
          <Skeleton h={13} mt={12} />
          <Skeleton h={13} mt={7} w="72%" />
        </div>
      ))}
    </div>
  );
}

/** Where the call lands: what it changed, and for whom. Optional in content.json. */
export function Lands({
  lands,
  turns,
}: {
  lands: NonNullable<Content["lands"]>;
  turns: Turn[];
}) {
  return (
    <div className="lands">
      {lands.map((l, i) => (
        <Reveal as="article" className="land" key={l.where + i} delay={i * STAGGER}>
          <h3>{l.where}</h3>
          {l.note && <p>{l.note}</p>}
          {l.ts && <TimeLink ts={l.ts} s={l.s} turns={turns} />}
        </Reveal>
      ))}
    </div>
  );
}
