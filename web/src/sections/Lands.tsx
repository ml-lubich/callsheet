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

/** Where it lands: each practice the speaker demonstrated, and the class of work it transfers to. */
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
        <Reveal as="article" className="land" key={i} delay={i * STAGGER}>
          <h3>{l.observation}</h3>
          <p className="land-to">{l.transfers_to}</p>
          {l.ts && <TimeLink ts={l.ts} s={l.s} turns={turns} />}
        </Reveal>
      ))}
    </div>
  );
}
