import { Reveal, STAGGER } from "../components/Reveal";
import { ScrollStack } from "../components/ScrollStack";
import { Skeleton } from "../components/Skeleton";
import { TimeLink } from "../components/TimeLink";
import type { Act, Turn } from "../types";

export function ActsSkeleton() {
  return (
    <div className="sk-grid">
      <Skeleton h={34} />
      <Skeleton h={92} />
      <Skeleton h={92} />
    </div>
  );
}

function ActCard({ act, turns }: { act: Act; turns: Turn[] }) {
  return (
    <article className="act">
      <div className="n">{act.n}</div>
      <div>
        <h3 id={`act-${act.n}`}>{act.title}</h3>
        <div className="ts span">{act.span}</div>
        <p className="sum">{act.summary}</p>
        {act.turning_point && (
          <div className="tp">
            <p>{act.turning_point.text}</p>
            <TimeLink
              ts={act.turning_point.ts}
              s={act.turning_point.s ?? act.start_s}
              turns={turns}
            />
          </div>
        )}
      </div>
    </article>
  );
}

/**
 * The acts of the call. On a wide, mouse-driven, motion-ok desktop they pin and stack
 * as the reader scrolls; every other viewport gets the plain column it always had. This
 * is the only section on the page that stacks — five sections behaving identically is
 * one section shown five times.
 */
export function Acts({
  acts,
  duration,
  turns,
}: {
  acts: Act[];
  duration: number;
  turns: Turn[];
}) {
  const go = (n: number) => {
    document.getElementById(`act-${n}`)?.scrollIntoView({ block: "start", behavior: "smooth" });
  };
  return (
    <>
      <div className="timebar">
        {acts.map((a) => (
          <button
            key={a.n}
            type="button"
            className="seg"
            title={a.title}
            onClick={() => go(a.n)}
            style={{
              left: `${((a.start_s / duration) * 100).toFixed(3)}%`,
              width: `${(((a.end_s - a.start_s) / duration) * 100).toFixed(3)}%`,
            }}
          >
            {a.n}
          </button>
        ))}
      </div>
      <ScrollStack
        className="actstack"
        compactClassName="actlist"
        cardClassName="actcard"
        items={acts.map((a, i) => ({
          key: String(a.n),
          node: (
            <Reveal delay={i * STAGGER}>
              <ActCard act={a} turns={turns} />
            </Reveal>
          ),
        }))}
      />
    </>
  );
}
