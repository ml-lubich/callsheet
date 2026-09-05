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

/** The one-line finding, when the analysis committed to one. Optional by design. */
export function Verdict({ verdict }: { verdict: NonNullable<Content["verdict"]> }) {
  const text = typeof verdict === "string" ? verdict : verdict.text;
  const note = typeof verdict === "string" ? undefined : verdict.note;
  return (
    <>
      <Reveal as="p" className="verdict">
        {text}
      </Reveal>
      {note && (
        <Reveal as="p" className="verdict-note" delay={STAGGER}>
          {note}
        </Reveal>
      )}
    </>
  );
}
