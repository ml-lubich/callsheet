import { Reveal, STAGGER } from "../components/Reveal";
import { Skeleton } from "../components/Skeleton";
import { TimeAxis } from "../components/TimeAxis";
import { nearestTurn } from "../lib/derive";
import { jump } from "../lib/jump";
import { tickFor } from "./StripChart";
import type { Thread, Turn } from "../types";

export function ThreadsSkeleton() {
  return (
    <div className="threads">
      {[0, 1, 2].map((i) => (
        <div className="thread" key={i}>
          <Skeleton h={22} w="70%" />
          <Skeleton h={13} mt={14} />
          <Skeleton h={13} mt={7} w="84%" />
          <Skeleton h={26} mt={24} />
        </div>
      ))}
    </div>
  );
}

export function Threads({
  threads,
  duration,
  turns,
}: {
  threads: Thread[];
  duration: number;
  turns: Turn[];
}) {
  return (
    <div className="threads">
      {threads.map((t, i) => (
        <Reveal as="article" className="thread" key={t.name} delay={i * STAGGER}>
          <h3>{t.name}</h3>
          <p className="what">{t.what}</p>
          <p className="why">{t.why_it_matters}</p>
          <TimeAxis
            duration={duration}
            marks={t.marks}
            tick={tickFor(duration)}
            onPick={(m) => jump(nearestTurn(turns, m.s))}
          />
          <div className="cap count">{(t.marks ?? []).length} mentions across the call</div>
        </Reveal>
      ))}
    </div>
  );
}
