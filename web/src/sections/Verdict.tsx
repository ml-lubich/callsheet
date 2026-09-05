import { Reveal, STAGGER } from "../components/Reveal";
import { Skeleton } from "../components/Skeleton";
import type { Content } from "../types";

export function VerdictSkeleton() {
  return (
    <div className="sk-grid">
      <Skeleton h={30} w="70%" />
      <Skeleton h={30} w="52%" />
    </div>
  );
}

/**
 * The stance the analysis committed to. The position is set in the display face so a
 * reader who stops here still leaves with the finding; the case for and against sit
 * under it in the two pens, and the one question that would settle it closes the block.
 */
export function Verdict({ verdict }: { verdict: NonNullable<Content["verdict"]> }) {
  return (
    <div className="verdict">
      <Reveal as="p" className="verdict-position">
        {verdict.position}
      </Reveal>
      <div className="verdict-cols">
        <Reveal as="div" className="verdict-for pen-b" delay={STAGGER}>
          <h4>For</h4>
          <ul>
            {verdict.for.map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        </Reveal>
        <Reveal as="div" className="verdict-against pen-a" delay={STAGGER * 2}>
          <h4>Against</h4>
          <ul>
            {verdict.against.map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        </Reveal>
      </div>
      {verdict.decides_it && (
        <Reveal as="p" className="verdict-decides" delay={STAGGER * 3}>
          <b>What would settle it</b>
          {verdict.decides_it}
        </Reveal>
      )}
    </div>
  );
}
